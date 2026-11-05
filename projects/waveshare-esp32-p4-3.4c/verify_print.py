"""八件式控制器PETG参考切片；托盘使用可移除支撑，其余件关闭支撑。"""
import argparse
from datetime import datetime as SliceTimestamp
import json
import subprocess
from pathlib import Path
import FreeCAD
import Mesh
from enclosure import ROOT, SCHEMA, PART_LABELS, digest
from print_audit import read_mesh, read_extrusions, align_extrusions, audit_support, section, grid, covered
import math


def preflight(out, names):
    summary = json.loads((out/'validation.json').read_text(encoding='utf-8'))
    if summary['schema'] != SCHEMA:
        raise ValueError('不能混用其他结构的旧报告')
    if not summary['fit_verified']:
        raise ValueError('请先通过verify_fit.py独立装配验证')
    for name in names:
        stl = out/'trials'/(name+'.stl'); mesh = Mesh.Mesh(str(stl))
        if not (mesh.isSolid() and mesh.countComponents() == 1 and abs(mesh.BoundBox.ZMin) < .001):
            raise ValueError(name+'网格非闭合单组件或未落床')
        if digest(stl) != summary['parts'][name]['sha256']:
            raise ValueError(name+'网格哈希不匹配')
    return summary


def slice_part(out, name, material, slicer):
    cache = ROOT/'archive'/'redesign_slices'/SliceTimestamp.now().strftime('%Y%m%d-%H%M%S-%f')/name
    cache.mkdir(parents=True)
    profiles = slicer.parent/'resources'/'profiles'/'Prusa'

    def load(kind, name):
        data = json.loads((profiles/kind/(name+'.json')).read_text(encoding='utf-8-sig'))
        base = load(kind, data['inherits']) if data.get('inherits') else {}
        base.update(data); base.pop('inherits', None)
        return base

    settings = []
    support_enabled=name=='battery_tray'
    names = [('machine', 'Prusa MK3S 0.4 nozzle'), ('process', '0.20mm Standard @MK3S'),
             ('filament', 'Generic '+material+' @Prusa')]
    for kind, profile in names:
        data = load(kind, profile)
        if kind == 'process':
            data.update({'layer_height': '0.2', 'initial_layer_print_height': '0.2',
                'wall_loops': '6', 'wall_generator': 'classic', 'sparse_infill_density': '30%',
                'enable_support': '1' if support_enabled else '0',
                'support_type': 'normal(auto)', 'support_threshold_angle': '45',
                'support_top_z_distance': '.24' if material == 'PETG' else '.2',
                'brim_type': 'outer_only', 'brim_width': '5'})
        path = cache/(kind+'.json'); path.write_text(json.dumps(data), encoding='utf-8'); settings.append(path)
    stl = out/'trials'/(name+'.stl')
    input_hash=digest(stl)
    source_hashes={p:digest(ROOT/p) for p in ('verify_print.py','print_audit.py')}
    # 固定摆放到参考打印床中心，避免自动排版任意旋转和含外沿的宽松包围框。
    slice_stl = cache/(name+'.stl')
    placed = Mesh.Mesh(str(stl)); placed.translate(125, 105, 0); placed.write(str(slice_stl))
    result = subprocess.run([str(slicer), '--slice', '0', '--orient', '0', '--arrange', '0', '--load-settings',
        str(settings[0])+';'+str(settings[1]), '--load-filaments', str(settings[2]),
        '--outputdir', str(cache), str(slice_stl)], capture_output=True, timeout=180)
    (cache/'stdout.log').write_bytes(result.stdout); (cache/'stderr.log').write_bytes(result.stderr)
    if result.returncode:
        raise RuntimeError(name+'参考切片失败：'+result.stderr.decode(errors='replace')[-1000:])
    sliced = json.loads((cache/'result.json').read_text(encoding='utf-8'))
    if sliced['return_code'] != 0 or len(sliced['sliced_plates']) != 1:
        raise RuntimeError('切片返回异常：'+str(sliced))
    plate = sliced['sliced_plates'][0]
    gcode = cache/'plate_1.gcode'
    layers, support_volume = read_extrusions(gcode.read_text(encoding='utf-8'), 0, 0)
    bounds = placed.BoundBox
    layers, alignment = align_extrusions(read_mesh(stl.read_bytes()), layers,
        {'x': bounds.XMin, 'y': bounds.YMin, 'width': bounds.XLength, 'depth': bounds.YLength})
    if alignment['section_alignment_score'] < .95:
        raise ValueError('固定摆放与实际墙线校准不足95%')
    model_layers = sorted(z for z, segments in layers.items() if any('support' not in s[2].lower() for s in segments))
    mesh = Mesh.Mesh(str(stl)); top = mesh.BoundBox.ZMax
    continuous = bool(model_layers) and model_layers[0] == .2 and all(
        round(i*.2, 3) in model_layers for i in range(1, round(model_layers[-1]/.2)+1))
    unsupported = audit_support(layers)
    contour = audit_contours(read_mesh(stl.read_bytes()), layers)
    if digest(stl)!=input_hash or source_hashes!={p:digest(ROOT/p) for p in source_hashes}:
        raise RuntimeError('切片期间输入或审计源码发生改变，必须重跑，不能绑定混合报告')
    passed = (continuous and -.201 <= top-model_layers[-1] < .4 and not plate['warning_message']
              and (support_enabled or support_volume < .001)
              and (not unsupported or unsupported[0]['unsupported_wall_run_mm'] <= 4.1)
              and contour['minimum_coverage'] >= .95)
    report = {'schema': SCHEMA, 'part': name, 'material': material, 'reference_slice_passed': passed,
        'verification_source_sha256': source_hashes,
        'stl_sha256': input_hash, 'gcode_sha256': digest(gcode), 'cache': str(cache.relative_to(ROOT)),
        'slice_input_sha256': digest(slice_stl), 'slice_input_translation_mm': [125, 105, 0],
        'profile': names, 'nozzle_mm': .4, 'layer_height_mm': .2, 'wall_loops': 6,
        'infill_percent':30,
        'support_enabled': support_enabled,
        'model_layer_count': len(model_layers), 'continuous_model_layers': continuous,
        'top_shortfall_mm': top-model_layers[-1] if model_layers else None,
        'support_volume_mm3': support_volume, 'alignment': alignment,
        'warning': plate['warning_message'], 'physical_print_verified': False,
        'unsupported_wall_runs': unsupported[:20], 'contour_audit': contour,
        'functional_section_coverage_verified': False,
        'note': '托盘允许可移除支撑，其余件关闭支撑；检查连续层、墙线承托与代表截面，仍需实物试印。'}
    (out/(name+'_'+material.lower()+'_print_validation.json')).write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    if not passed:
        raise ValueError(name+'参考切片未通过，详见报告')
    print(name, material, len(model_layers), '层，参考切片通过', flush=True)
    return report


def audit_contours(triangles, layers):
    """对代表高度的STL截面逐段采样，与实际本体挤出对照。"""
    heights = sorted(layers)
    selected = sorted(set(heights[round((len(heights)-1)*f)] for f in (.02, .08, .2, .4, .6, .8, .95)))
    results = []
    for z in selected:
        index = grid([seg for seg in layers[z] if 'support' not in seg[2].lower()])
        total = found = 0.
        for a, b in section(triangles, z-.1):
            length = math.dist(a, b); count = max(1, math.ceil(length/.3)); step = length/count
            for i in range(count):
                t = (i+.5)/count; point = (a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t)
                total += step
                if covered(point, index, .15):
                    found += step
        if total:
            results.append({'z_mm': z, 'coverage': found/total, 'contour_length_mm': total})
    return {'minimum_coverage': min((r['coverage'] for r in results), default=0), 'sections': results,
            'method': '7个代表层，按截面轮廓长度加权，0.3mm采样，对照全部本体挤出足迹'}


def summarize(out):
    """只汇总匹配当前网格和审计脚本的全部材料报告。"""
    reports = {}; missing = []
    sources = {p: digest(ROOT/p) for p in ('verify_print.py', 'print_audit.py')}
    for name in PART_LABELS:
        for material in ('PETG',):
            filename = name+'_'+material.lower()+'_print_validation.json'
            path = out/filename
            if not path.exists():
                missing.append(filename); continue
            r = json.loads(path.read_text(encoding='utf-8'))
            ok = (r.get('schema') == SCHEMA and r['reference_slice_passed']
                  and r['stl_sha256'] == digest(out/'trials'/(name+'.stl'))
                  and r.get('verification_source_sha256') == sources)
            reports[filename] = {'passed': ok, 'sha256': digest(path)}
    passed = not missing and len(reports) == len(PART_LABELS) and all(r['passed'] for r in reports.values())
    result = {'schema': SCHEMA, 'reference_slicing_verified': passed,
              'reports': reports, 'missing': missing, 'supports_disabled_for_all': False,
              'support_parts':['battery_tray'],'required_materials':['PETG'],
              'physical_print_verified': False, 'functional_section_coverage_verified': False,
              'production_ready': False}
    (out/'print_validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    summary = json.loads((out/'validation.json').read_text(encoding='utf-8'))
    summary['reference_slicing_verified'] = passed
    summary['slicing_verified'] = passed
    (out/'validation.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT/'output')
    parser.add_argument('--part', choices=['all']+list(PART_LABELS), default='all')
    parser.add_argument('--material', choices=['PLA', 'PETG'], default='PETG')
    parser.add_argument('--slice', action='store_true', help='执行真实参考切片')
    parser.add_argument('--slicer', type=Path, default=Path('C:/Program Files/Bambu Studio/bambu-studio.exe'))
    args = parser.parse_args(); out = args.out.resolve()
    names = list(PART_LABELS) if args.part == 'all' else [args.part]
    preflight(out, names)
    if args.slice:
        for name in names:
            slice_part(out, name, args.material, args.slicer)
        summarize(out)
    else:
        print('八件式控制器网格打印预检通过；未执行切片或实物验证')


if __name__ == '__main__':
    main()
