"""P4 两打印件参考切片；验证连续层并展示本体和支撑路径。"""
import argparse
import hashlib
import json
import math
import os
import re
import struct
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from print_audit import read_mesh, read_extrusions, align_extrusions, audit_features, audit_support

ROOT = Path(__file__).resolve().parent
OUT = Path(os.environ.get('P4_OUTPUT_DIR', ROOT / 'output'))
CACHE = Path(os.environ.get('P4_PRINT_CACHE_DIR', ROOT / 'archive' / 'print_check'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--part', required=True, choices=('main_shell', 'rear_cover'))
    parser.add_argument('--material', choices=('PLA','PETG'), default='PETG')
    parser.add_argument('--baseline',action='store_true',help='只用于旧 STL 同配置对比，不作为新模型验收')
    parser.add_argument('--slicer', default=r'C:\Program Files\Bambu Studio\bambu-studio.exe')
    args = parser.parse_args()
    slicer = Path(args.slicer)
    profiles = slicer.parent / 'resources' / 'profiles' / 'Prusa'
    cache = CACHE / args.material.lower() / args.part
    cache.mkdir(parents=True, exist_ok=True)

    def load(kind, name):
        data = json.loads((profiles / kind / (name + '.json')).read_text(encoding='utf-8-sig'))
        base = load(kind, data['inherits']) if data.get('inherits') else {}
        base.update(data)
        base.pop('inherits', None)
        return base

    names = [('machine', 'Prusa MK3S 0.4 nozzle'), ('process', '0.20mm Standard @MK3S'),
             ('filament', 'Generic '+args.material+' @Prusa')]
    settings = []
    for kind, name in names:
        data = load(kind, name)
        if kind == 'process':
            data.update({'layer_height':'0.2', 'initial_layer_print_height':'0.2',
                         'wall_loops':'4', 'wall_generator':'classic',
                         'enable_support':'1', 'support_type':'normal(auto)',
                         'support_threshold_angle':'45', 'brim_type':'outer_only', 'brim_width':'5',
                         'support_top_z_distance':'0.24' if args.material=='PETG' else '0.2'})
        path = cache / (kind+'.json')
        path.write_text(json.dumps(data), encoding='utf-8')
        settings.append(path)
    stl = OUT / (args.part+'.stl')
    result_path = cache / 'result.json'
    if result_path.exists():
        result_path.unlink()  # 仅清理本脚本产生的临时结果，防止误用旧切片。
    result = subprocess.run([str(slicer), '--slice','0', '--load-settings',
                             str(settings[0])+';'+str(settings[1]), '--load-filaments',
                             str(settings[2]), '--outputdir',str(cache),str(stl)],
                            capture_output=True, timeout=120)
    assert result.returncode == 0, '切片失败：'+result.stderr.decode(errors='replace')[-1500:]
    sliced = json.loads(result_path.read_text(encoding='utf-8'))
    assert sliced['return_code'] == 0 and len(sliced['sliced_plates']) == 1
    plate = sliced['sliced_plates'][0]
    assert not plate['warning_message'], plate['warning_message']
    data = stl.read_bytes()
    vertices = []
    for i in range(struct.unpack_from('<I',data,80)[0]):
        values = struct.unpack_from('<12f',data,84+i*50)
        vertices.extend((values[3:6],values[6:9],values[9:12]))
    assert abs(min(v[2] for v in vertices)) < 0.001, 'STL 未落床'
    triangles=read_mesh(data)
    paths={}
    model_layers=set()
    support_layers=set()
    layers,support_volume=read_extrusions((cache/'plate_1.gcode').read_text(encoding='utf-8'),0,0)
    layers,alignment=align_extrusions(triangles,layers,plate['objects'][0]['bbox'])
    for z,segments in layers.items():
        for a,b,kind,width in segments:
            support='support' in kind.lower()
            (support_layers if support else model_layers).add(z)
            if support or 'wall' in kind.lower():paths.setdefault(z,[]).append((a,b,support))
    assert model_layers and min(model_layers)==0.2, '首层无本体'
    assert all(round(i*0.2,3) in model_layers for i in range(1,round(max(model_layers)/0.2)+1)), '本体层中断'
    shortfall=max(v[2] for v in vertices)-max(model_layers)
    assert -0.201<=shortfall<0.4, '顶部偏差超过切片分辨率'  # 顶层可向上取整一层。
    support_runs=audit_support(layers)
    feature_checks={}
    feature_failures=[]
    if not args.baseline:
        manifest=json.loads((OUT/'print_features.json').read_text(encoding='utf-8'))
        feature_checks,feature_failures=audit_features(triangles,layers,manifest,args.part)
    report={'stl_sha256':hashlib.sha256(data).hexdigest(), 'slicer':'Bambu Studio',
            'printer_profile':names[0][1], 'filament_profile':names[2][1],
            'nozzle_mm':0.4, 'layer_height_mm':0.2, 'wall_loops':4,'wall_generator':'classic',
            'support_type':'normal(auto)', 'support_threshold_angle_deg':45,
            'support_top_gap_mm':0.24 if args.material=='PETG' else 0.2,
            'support_extrusion_volume_mm3':support_volume,'baseline_only':args.baseline,
            'plate_alignment':alignment,
            'brim_width_mm':5, 'object_layer_count':len(model_layers),
            'support_layer_count':len(support_layers), 'top_shortfall_mm':shortfall,
            'warning_message':plate['warning_message'], 'physical_print_verified':False,
            'support_removal_verified':False,
            'feature_checks':feature_checks,'feature_failures':feature_failures,
            'unsupported_wall_runs':support_runs[:15],
            'feature_validation_passed':not args.baseline and not feature_failures,
            'support_audit_method':'当前墙线挤出足迹与前一本体层及下方 0.18～0.50 mm 支撑足迹求搭接，额外 0.02 mm 容差；连续无搭接墙段不得超过 4.1 mm。',
            'feature_audit_method':'STL 功能截面轮廓按长度加权，对照所有本体挤出足迹；收尖边用截面内侧 1.2 mm 探测分类并单列原始覆盖率，其余截面要求覆盖 95%；关键承力区另检查至少两条墙线。',
            'note':'参考切片；支撑仍需实物验证可拆性，G-code 不交付。'}
    (OUT/(args.part+'_'+args.material.lower()+'_print_validation.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    if not args.baseline:
        assert not feature_failures,'关键结构切片缺失：'+str(feature_failures[:8])
        assert not support_runs or support_runs[0]['unsupported_wall_run_mm']<=4.1,'连续悬空墙线超过 4 mm：'+str(support_runs[:5])
    image=Image.new('RGB',(1200,880),(250,250,249))
    draw=ImageDraw.Draw(image)
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
    draw.text((15,10),args.part+' '+args.material+'：蓝色本体墙线／橙色支撑（参考机型）',font=font,fill=(35,40,40))
    zs=sorted(model_layers)
    selected=[zs[round((len(zs)-1)*f)] for f in (0,.05,.15,.3,.5,.8)]
    xmin,xmax=min(v[0] for v in vertices),max(v[0] for v in vertices)
    ymin,ymax=min(v[1] for v in vertices),max(v[1] for v in vertices)
    scale=330/max(xmax-xmin,ymax-ymin)
    for index,height in enumerate(selected):
        left,top=(index%3)*400,50+(index//3)*410
        draw.text((left+15,top),'Z = %.2f mm'%height,font=font,fill=(35,40,40))
        for a,b,support in paths.get(height,[]):
            points=[(left+200+(p[0]-(xmin+xmax)/2)*scale,
                     top+210-(p[1]-(ymin+ymax)/2)*scale) for p in (a,b)]
            draw.line(points,fill=(218,126,47) if support else (48,122,146),width=1)
    image.save(OUT/('preview_'+args.part+'_'+args.material.lower()+'_print.png'))
    print(args.part,args.material,'本体层',len(model_layers),'支撑体积',round(support_volume,2),'特征',len(feature_checks),'顶部偏差',round(shortfall,4))


if __name__=='__main__':
    main()
