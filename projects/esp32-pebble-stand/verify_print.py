"""用本机 Bambu Studio 检查 0.4 mm 喷嘴的下缘挤出路径；G-code 仅作验证。"""
import argparse
import hashlib
import json
import re
import struct
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'output'
CACHE = ROOT / 'archive' / 'print_check'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--slicer', default=r'C:\Program Files\Bambu Studio\bambu-studio.exe')
    parser.add_argument('--part',choices=('rear_cover','mount_carrier'),default='rear_cover')
    args = parser.parse_args()
    slicer = Path(args.slicer)
    profiles = slicer.parent / 'resources' / 'profiles' / 'Prusa'
    assert slicer.is_file() and profiles.is_dir(), '请通过 --slicer 指定带 Prusa 配置的 Bambu Studio'
    cache = CACHE / args.part
    cache.mkdir(parents=True, exist_ok=True)
    is_carrier = args.part == 'mount_carrier'

    def load(kind, name):
        data = json.loads((profiles / kind / (name + '.json')).read_text(encoding='utf-8-sig'))
        base = load(kind, data['inherits']) if data.get('inherits') else {}
        base.update(data)
        base.pop('inherits', None)
        return base

    names = [('machine', 'Prusa MK3S 0.4 nozzle'),
             ('process', '0.20mm Standard @MK3S'), ('filament', 'Generic PETG @Prusa')]
    files = []
    for kind, name in names:
        data = load(kind, name)
        if kind == 'process':
            data.update({'layer_height': '0.2', 'initial_layer_print_height': '0.2',
                         'wall_loops': '4', 'wall_generator': 'classic',
                         'enable_support':'1','support_type':'normal(auto)',
                         'support_threshold_angle':'30','brim_type':'outer_only','brim_width':'5'})
        path = cache / (kind + '.json')
        path.write_text(json.dumps(data), encoding='utf-8')
        files.append(path)
    stl = OUT / (args.part+'.stl')
    result_path = cache / 'result.json'
    # 禁止用上次切片结果冒充本次验证；缓存中的 G-code 也不作用户机型的打印文件。
    if result_path.exists():
        result_path.unlink()
    command = [str(slicer), '--slice', '0', '--load-settings', str(files[0]) + ';' + str(files[1]),
               '--load-filaments', str(files[2]), '--outputdir', str(cache), str(stl)]
    result = subprocess.run(command, capture_output=True, timeout=60)
    assert result.returncode == 0, '切片程序失败：' + str(result.returncode)
    sliced = json.loads(result_path.read_text(encoding='utf-8'))
    assert sliced['return_code'] == 0 and len(sliced['sliced_plates']) == 1
    plate = sliced['sliced_plates'][0]
    assert not plate['warning_message'], plate['warning_message']
    box = plate['objects'][0]['bbox']
    data = stl.read_bytes()
    vertices = []
    for i in range(struct.unpack_from('<I', data, 80)[0]):
        values = struct.unpack_from('<12f', data, 84 + i * 50)
        vertices.extend((values[3:6], values[6:9], values[9:12]))
    dx = box['x'] - min(v[0] for v in vertices)
    dy = box['y'] - min(v[1] for v in vertices)
    x = y = layer = 0
    feature = ''
    paths = {}
    gcode = (cache / 'plate_1.gcode').read_text(encoding='utf-8')
    support_moves=0
    support_layers=set()
    model_layers=set()
    for line in gcode.splitlines():
        if line.startswith('; Z_HEIGHT:'):
            layer = round(float(line.split(':')[1]), 3)
            paths.setdefault(layer, [])
        if line.startswith('; FEATURE:'):
            feature = line.split(':', 1)[1].strip()
        if not line.startswith(('G0 ', 'G1 ')):
            continue
        values = {k: float(v) for k, v in re.findall(r'([XYE])([-+\d.]+)', line.split(';')[0])}
        nx, ny = values.get('X', x), values.get('Y', y)
        if values.get('E',0)>0 and 'support' in feature.lower() and (nx!=x or ny!=y):
            support_moves+=1
            support_layers.add(layer)
        if values.get('E',0)>0 and feature not in ('Custom','Skirt','Brim') and 'support' not in feature.lower() and (nx!=x or ny!=y):
            model_layers.add(layer)
        if values.get('E', 0) > 0 and 'wall' in feature.lower() and (nx != x or ny != y):
            paths.setdefault(layer, []).append(((x-dx, y-dy), (nx-dx, ny-dy), feature))
        x, y = nx, ny
    # 支撑界面可能在本体层之间插入独立层，这些层没有本体壳壁是正常情况。
    assert paths and all(z in model_layers or z in support_layers for z in paths), '存在既无本体也无支撑的空层'
    object_paths={z:segments for z,segments in paths.items() if segments}
    # 曲面顶部小于挤出线宽的尖端可能被切片器省略；允许最多一层＋半线宽。
    top_shortfall=max(v[2] for v in vertices)-max(model_layers)
    assert 0<=top_shortfall<0.4,'本体顶部缺失超过切片分辨率'
    expected_layers=round(max(model_layers)/0.2)
    assert all(round(i*0.2,3) in model_layers for i in range(1,expected_layers+1)), '本体标准层缺少挤出路径'
    assert all(round(i*0.2,3) in object_paths for i in range(1,expected_layers)), '非顶层缺少壳壁路径'
    probes = []
    # 中央前口自然结束后进入屏幕开口，改查左右下缘，避免把正常开口判成漏打。
    test_probes=() if is_carrier else ((0, 2.8, 7.8, 0), (-18, 8, 11.4, 3), (18, 8, 11.4, 3))
    for probe_x, z0, z1, ymax in test_probes:
        for z, segments in sorted(object_paths.items()):
            if not z0 <= z <= z1:
                continue
            crossings = set()
            for (x, y), (nx, ny), _ in segments:
                if min(x, nx) <= probe_x <= max(x, nx) and abs(nx-x) > 0.00001:
                    y_cross = y + (ny-y) * (probe_x-x) / (nx-x)
                    if y_cross < ymax:
                        crossings.add(round(y_cross, 2))
            assert len(crossings) >= 2, '下缘路径缺失：' + str((probe_x, z, crossings))
            probes.append({'x_mm': probe_x, 'z_mm': z, 'wall_crossings': len(crossings)})
    assert len(probes) == (0 if is_carrier else 62), '层高或测试范围发生变化，需重新定义验证截线'
    assert support_moves>0,'打印件需要支撑，但没有生成支撑路径'
    report = {'stl_sha256': hashlib.sha256(data).hexdigest(), 'slicer': 'Bambu Studio',
              'printer_profile': names[0][1], 'filament_profile': names[2][1],
              'nozzle_mm': 0.4, 'layer_height_mm': 0.2, 'wall_loops': 4,
              'wall_generator': 'classic', 'support_enabled': True,'support_extrusion_moves':support_moves,
              'support_type':'normal(auto)','support_threshold_angle_deg':30,'outer_brim_width_mm':5,
              'layer_count': len(paths), 'object_layer_count':len(model_layers),
              'wall_layer_count':len(object_paths),
              'top_shortfall_mm':round(top_shortfall,5),
              'support_only_layer_count':len(support_layers-model_layers),
              'lower_edge_probe_count': len(probes),
              'min_wall_crossings': min((p['wall_crossings'] for p in probes),default=None),
              'warning_message': plate['warning_message'], 'lower_edge_probes': probes,
              'physical_print_verified': False,
              'note': '参考机型切片，非用户实际机型验证；G-code 仅存本地 archive，不作为打印交付。'}
    report_name='carrier_print_validation.json' if is_carrier else 'print_validation.json'
    (OUT / report_name).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    image = Image.new('RGB', (1200, 860), (250, 250, 249))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 19)
    title=('承托架' if is_carrier else '后壳')+'本体路径（普通支撑＋5 mm 外沿，图中隐藏支撑）'
    draw.text((20, 15), title, font=font, fill=(35, 40, 40))
    heights=(0.2,1.0,2.0,3.0,5.0,7.0) if is_carrier else (3.0,5.0,7.0,9.0,11.0,13.0)
    for index, z in enumerate(heights):
        left, top = (index % 3) * 400, 55 + (index // 3) * 385
        draw.text((left + 15, top), 'Z = %.1f mm' % z, font=font, fill=(35, 40, 40))
        for a, b, kind in paths[z]:
            points = [(left+200+p[0]*5.2, top+260-p[1]*5.2) for p in (a, b)]
            color = (210, 110, 35) if kind == 'Outer wall' else (48, 122, 146)
            draw.line(points, fill=color, width=2)
        draw.text((left+15, top+340), '橙：外壁  蓝：内壁/悬垂壁', font=font, fill=(60, 65, 65))
    image.save(OUT / ('preview_carrier_layers.png' if is_carrier else 'preview_print_layers.png'))
    print('切片成功：%d 本体层，%d 支撑专用层，%d 条下缘截线通过' % (len(model_layers),len(support_layers-model_layers),len(probes)))


if __name__ == '__main__':
    main()
