"""独立回读八件式控制器：装配、完整硬件、电芯净空与托盘维护行程。"""
import argparse
import itertools
import json
import math
from pathlib import Path
import FreeCAD as App
import Mesh
import MeshPart
import Part
from enclosure import ROOT, SCHEMA, PART_LABELS, Design, digest, lc, cy, box

LOCAL_INVERSE=None
LOCAL_BOUNDS={}


def local_bounds(shape):
    key=shape.hashCode()
    if key not in LOCAL_BOUNDS:
        transformed=shape.copy()
        transformed.Placement=LOCAL_INVERSE.multiply(transformed.Placement)
        LOCAL_BOUNDS[key]=transformed.BoundBox
    return LOCAL_BOUNDS[key]


def overlap(a, b):
    if not a.BoundBox.intersect(b.BoundBox):
        return 0.
    # 增加屏幕局部轴向的保守包围盒筛选；候选仍执行精确BRep交集。
    if LOCAL_INVERSE is not None and not local_bounds(a).intersect(local_bounds(b)):
        return 0.
    return a.common(b).Volume


def match_step_bounds(imported,original):
    """体积相同的左右件按位置匹配，不能按浮点体积排序强行配对。"""
    remaining=list(imported);errors=[]
    for shape in original:
        target=shape.optimalBoundingBox(False,False)
        choices=[]
        for i,candidate in enumerate(remaining):
            bounds=candidate.optimalBoundingBox(False,False)
            error=max(abs(getattr(bounds,k)-getattr(target,k)) for k in (
                'XMin','XMax','YMin','YMax','ZMin','ZMax'))
            choices.append((error,i))
        if not choices:
            return [float('inf')]
        error,index=min(choices)
        remaining.pop(index);errors.append(error)
    return errors if not remaining else [float('inf')]


def stable_mesh_volume(shape,deflection):
    """围绕局部中心以双精度补偿求和，避免Mesh.Volume单精度累计与曲面积分漂移。"""
    mesh=MeshPart.meshFromShape(Shape=shape,LinearDeflection=deflection,AngularDeflection=.025,Relative=False)
    vertices,faces=mesh.Topology;center=shape.BoundBox.Center
    points=[v-center for v in vertices]
    return abs(math.fsum(points[i].dot(points[j].cross(points[k]))/6 for i,j,k in faces))


def verify(out):
    global LOCAL_INVERSE
    summary = json.loads((out/'validation.json').read_text(encoding='utf-8'))
    if summary['schema'] != SCHEMA:
        raise ValueError('不是当前八件式候选，不能混用旧报告')
    design = Design(summary['parameters']); design.make_mics()
    LOCAL_INVERSE=design.placement.inverse();LOCAL_BOUNDS.clear()
    doc = App.openDocument(str(out/'enclosure.FCStd'))
    parts = {name: doc.getObject(name).Shape for name in PART_LABELS}
    result = {'schema': SCHEMA, 'checks': {}, 'failures': [],
              'production_ready': False, 'physical_tests_executed': False}

    def check(name, passed, detail):
        result['checks'][name] = {'passed': bool(passed), 'detail': detail}
        if not passed:
            result['failures'].append(name)
        print(name, 'PASS' if passed else 'FAIL', str(detail)[:300], flush=True)

    check('source_hash', summary['source_sha256'] == digest(ROOT/'enclosure.py'), '报告绑定建模源码')
    check('prototype_gate', not doc.Design_Status.ProductionReady and not summary['readiness']['production_ready'],
          '原型不得被标记为正式打印通过')
    for filename, expected in summary['artifacts'].items():
        check('hash_'+filename, digest(out/filename) == expected, expected)
    for name, shape in parts.items():
        try:
            shape.check(True)
            strict_error=None
        except ValueError as exc:
            strict_error=str(exc)
        check(name+'_strict_bop',strict_error is None,strict_error or '严格BOP通过')
        check(name+'_solid', shape.isValid() and len(shape.Solids) == 1,
              {'valid': shape.isValid(), 'solids': len(shape.Solids)})
        stl = out/'trials'/(name+'.stl'); mesh = Mesh.Mesh(str(stl))
        check(name+'_mesh', mesh.isSolid() and mesh.countComponents() == 1 and abs(mesh.BoundBox.ZMin) < 1e-4,
              {'closed': mesh.isSolid(), 'components': mesh.countComponents(), 'zmin': mesh.BoundBox.ZMin})
        check(name+'_mesh_hash', digest(stl) == summary['parts'][name]['sha256'], '打印试样绑定本次STL')
        check(name+'_mesh_volume', abs(abs(mesh.Volume)-shape.Volume)/shape.Volume < .01,
              {'brep_mm3': shape.Volume, 'mesh_mm3': abs(mesh.Volume)})
        check(name+'_bed_size', max(mesh.BoundBox.XLength, mesh.BoundBox.YLength) <= 170,
              {'print_xy_mm': [mesh.BoundBox.XLength, mesh.BoundBox.YLength], 'minimum_bed_mm': 180})
    for (a, first), (b, second) in itertools.combinations(parts.items(), 2):
        volume = overlap(first, second)
        check(a+'__'+b, volume < .02, {'overlap_mm3': volume})
    # 在回读实体上检查硬接触环、螺丝通道和真实盲孔底，不以说明字段代替结构。
    p=summary['parameters']; cf=p['carrier_front_n']; cb=cf+p['carrier_t']; rear=p['rear_y']
    body=parts['main_body']; carrier=parts['board_carrier']; cover=parts['rear_cover']
    for i,(x,s) in enumerate(design.carrier_bolts):
        front=design.head(lc(4.2,cb-.05,cb,x,s).cut(lc(2,cb-.1,cb+.1,x,s)))
        back=design.head(lc(4.2,cb,cb+.05,x,s).cut(lc(2,cb-.1,cb+.1,x,s)))
        bearing=[overlap(front,carrier)/front.Volume,overlap(back,body)/back.Volume]
        shaft=design.head(lc(1.5,cf-.5,cf-.5+8,x,s))
        bottom=design.head(lc(1.45,cb+5.05,cb+5.15,x,s))
        check('carrier_joint_'+str(i), min(bearing)>.98 and overlap(shaft,body)<.001
              and overlap(shaft,carrier)<.001 and overlap(bottom,body)/bottom.Volume>.98,
              {'bearing_coverage':bearing,'screw_bottom_clearance_mm':cb+5-(cf-.5+8),
               'insert_engagement_mm':3.,'cover_required':False})
    for i,(x,z) in enumerate(design.cover_bolts):
        front=cy(4.2,rear-.05,rear,x,z).cut(cy(2,rear-.1,rear+.1,x,z))
        back=cy(4.2,rear,rear+.05,x,z).cut(cy(2,rear-.1,rear+.1,x,z))
        bearing=[overlap(front,body)/front.Volume,overlap(back,cover)/back.Volume]
        head_top=rear+p['cover_t']-.2
        tip=head_top-8
        shaft=cy(1.5,tip,rear+p['cover_t'],x,z)
        bottom=cy(1.45,rear-6.15,rear-6.05,x,z)
        head=Part.makeCone(1.5,3.,1.5,App.Vector(x,head_top-1.5,z),App.Vector(0,1,0))
        check('cover_joint_'+str(i), min(bearing)>.98 and overlap(shaft,body)<.001
              and overlap(shaft,cover)<.001 and overlap(head,cover)<.001
              and overlap(bottom,body)/bottom.Volume>.98,
              {'bearing_coverage':bearing,'screw_bottom_clearance_mm':tip-(rear-6),
               'insert_engagement_mm':3.,'hard_stop_y_mm':rear})
    # 原先以最深凸台9.6mm禁止全部前移，会错误地排斥不遮玻璃的侧边包覆。
    front_envelope=design.head(lc(p['screen_radius'],-.1,9.6))
    check('no_added_front_bezel',overlap(body,front_envelope)<.001,
          '原屏投影内不增加压框；周围侧壁可以向前包覆')
    local_body=body.copy();local_body.Placement=LOCAL_INVERSE.multiply(local_body.Placement)
    screen=doc.Display_Visual.Shape.copy();screen.Placement=LOCAL_INVERSE.multiply(screen.Placement)
    gaps=[];walls=[];steps=[]
    for angle in range(0,360,5):
        c,s=math.cos(math.radians(angle)),math.sin(math.radians(angle))
        line=Part.makeLine(App.Vector(55*c,55*s,-1.5),App.Vector(62*c,62*s,-1.5))
        shell_edges=local_body.common(line).Edges;screen_edges=screen.common(line).Edges
        if not shell_edges or not screen_edges:
            gaps.append(float('inf'));walls.append(0);continue
        radii=[v.Point.x*c+v.Point.y*s for e in shell_edges for v in e.Vertexes]
        screen_radii=[v.Point.x*c+v.Point.y*s for e in screen_edges for v in e.Vertexes]
        gaps.append(min(radii)-max(screen_radii));walls.append(sum(e.Length for e in shell_edges))
        # 在接边平面上量前端位置，避开0.3mm外沿倒角。
        face_line=Part.makeLine(App.Vector(59*c,59*s,.1),App.Vector(59*c,59*s,-1.4))
        edges=local_body.common(face_line).Edges
        steps.append(min((-v.Point.z for e in edges for v in e.Vertexes),default=float('inf')))
    check('screen_radial_gap',len(gaps)==72 and all(abs(g-p['screen_radial_gap'])<.01 for g in gaps),
        {'sample_count':len(gaps),'minimum_mm':min(gaps),'maximum_mm':max(gaps),'nominal_mm':p['screen_radial_gap']})
    check('screen_proud',len(steps)==72 and all(abs(s-p['screen_proud'])<.01 for s in steps),
        {'sample_count':len(steps),'minimum_mm':min(steps),'maximum_mm':max(steps),'nominal_mm':p['screen_proud']})
    check('screen_wrap_wall',len(walls)==72 and min(walls)>=2.39,
        {'sample_count':len(walls),'minimum_radial_wall_mm':min(walls)})
    roof=[]
    for angle in (96,102,108):
        c,s=math.cos(math.radians(angle)),math.sin(math.radians(angle))
        line=Part.makeLine(App.Vector(54.8*c,54.8*s,-15),App.Vector(56.6*c,56.6*s,-15))
        roof.append(sum(e.Length for e in local_body.common(line).Edges))
    check('top_old_usb_slot_closed',min(roof)>1.79,{'restored_material_lengths_mm':roof})
    # 包围盒只筛候选，每个候选仍执行精确BRep交集，不按大致包络放行。
    module = doc.Module_Reference.Shape
    check('module_retained', len(module.Solids) == 1161, {'retained_solids': len(module.Solids)})
    for name, shape in parts.items():
        hits = []
        for index, solid in enumerate(module.Solids):
            value = overlap(shape, solid)
            if value > 1e-5:
                hits.append({'solid': index, 'volume_mm3': value})
        check(name+'_module', sum(hit['volume_mm3'] for hit in hits) < .02, hits)
        value = overlap(shape, doc.Speaker_Envelope.Shape)
        check(name+'_speaker', value < .02, {'overlap_mm3': value})
    for side, air in design.mic_air.items():
        blockers = {name: overlap(air, shape) for name, shape in parts.items()}
        check(side+'_mic_path', max(blockers.values()) < .001, blockers)
    envelopes={name:doc.getObject(name).Shape for name in (
        'Battery_Envelope','Battery_Keepout','Power_Envelope','Switch_Envelope')}
    for ref, shape in envelopes.items():
        for name, part in parts.items():
            value=overlap(shape,part)
            check(name+'__'+ref,value<.001,{'overlap_mm3':value})
        values=[overlap(shape,s) for s in module.Solids]
        check(ref+'_module',sum(values)<.001,{'overlap_mm3':sum(values)})
        check(ref+'_speaker',overlap(shape,doc.Speaker_Envelope.Shape)<.001,
            {'overlap_mm3':overlap(shape,doc.Speaker_Envelope.Shape)})
    for a,b in itertools.combinations(['Battery_Keepout','Power_Envelope','Switch_Envelope'],2):
        check(a+'__'+b,overlap(envelopes[a],envelopes[b])<.001,'电池余量、供电模块及开关互不侵入')
    for i,(x,y) in enumerate(design.tray_bolts):
        seat=Part.makeCylinder(3.8,.05,App.Vector(x,y,p['tray_bottom']-.05)).cut(
            Part.makeCylinder(2,.07,App.Vector(x,y,p['tray_bottom']-.06)))
        contact=overlap(seat,body)/seat.Volume
        shaft=Part.makeCylinder(1.5,6,App.Vector(x,y,p['tray_bottom']+p['tray_t']-6))
        check('tray_joint_'+str(i),contact>.98 and overlap(shaft,body)<.001,
            {'seat_coverage':contact,'screw':'M3×6','insert_length_mm':3})
    # 后盖连同扬声器、开关先移开；托盘连电池和电源平台向后抽出。
    moving=Part.makeCompound([parts['battery_tray'],envelopes['Battery_Keepout'],envelopes['Power_Envelope']])
    obstacles={n:s for n,s in parts.items() if n not in ('battery_tray','rear_cover')}
    obstacles['module']=module
    collisions=[]
    for step in range(0,91,3):
        shifted=moving.copy(); shifted.translate(App.Vector(0,step,0))
        for name,shape in obstacles.items():
            value=overlap(shifted,shape)
            if value>.02:
                collisions.append({'travel_mm':step,'obstacle':name,'volume_mm3':value})
    check('tray_rearward_removal',not collisions,collisions[:12])
    # 后盖外口与内部有贯通关系；外部插头与真实线束仍需选型。
    usb=box(-9,9,rear-.1,rear+p['cover_t']+.1,64,74)
    switch=box(25,35,rear-.1,rear+p['cover_t']+.1,63,68)
    check('rear_usb_opening',overlap(usb,cover)<.001,'后部USB预留口贯通')
    check('rear_switch_opening',overlap(switch,cover)<.001,'后下部开关预留口贯通')
    left = summary['features']['mic_left']; right = summary['features']['mic_right']
    check('mic_symmetry', abs(left['nominal_path_length_mm']-right['nominal_path_length_mm']) < 1e-6,
          {'left_mm': left['nominal_path_length_mm'], 'right_mm': right['nominal_path_length_mm']})
    check('mic_separate', overlap(design.mic_air['left'], design.mic_air['right']) < .001,
          '左右预留声道彼此不连通；与实际麦克风的耦合仍待校准')
    imported = Part.read(str(out/'enclosure.step'))
    check('step_count', len(imported.Solids) == len(PART_LABELS), len(imported.Solids))
    # STEP转换改变复杂裁剪面的数值积分分区；原始Volume差异保留，不用放宽门槛掩盖。
    # 逐件空间匹配后，以两个网格精度的补偿体积及双向布尔差共同验证真实几何。
    remaining=list(imported.Solids);step_details={}
    for name,original in parts.items():
        target=original.optimalBoundingBox(False,False)
        def error(shape):
            bounds=shape.optimalBoundingBox(False,False)
            return max(abs(getattr(bounds,k)-getattr(target,k)) for k in ('XMin','XMax','YMin','YMax','ZMin','ZMax'))
        index=min(range(len(remaining)),key=lambda i:error(remaining[i]));copy=remaining.pop(index)
        differences=[];fine=[]
        for deflection in (.04,.02):
            values=[stable_mesh_volume(s,deflection) for s in (original,copy)]
            differences.append(values[1]-values[0]);fine=values
        step_details[name]={'brep_raw_volume_difference_mm3':copy.Volume-original.Volume,
            'compensated_mesh_volume_mm3':fine,'volume_differences_at_004_002_mm3':differences,
            'removed_mm3':original.cut(copy).Volume,'added_mm3':copy.cut(original).Volume}
    total=sum(s.Volume for s in parts.values())
    delta=math.fsum(v['volume_differences_at_004_002_mm3'][-1] for v in step_details.values())
    check('step_volume',abs(delta)<=max(.05,total*1e-6),
        {'brep_raw_absolute_difference_mm3':abs(imported.Volume-total),'compensated_mesh_difference_mm3':delta,
         'tolerance':'max(0.05mm³,1ppm)','method':'逐件双精度补偿网格体积；另核对两个精度和双向布尔差'})
    check('step_individual_volumes',all(
        all(abs(d)<=max(.05,v['compensated_mesh_volume_mm3'][0]*1e-6) for d in v['volume_differences_at_004_002_mm3'])
        and abs(v['volume_differences_at_004_002_mm3'][0]-v['volume_differences_at_004_002_mm3'][1])<.05
        and max(v['removed_mm3'],v['added_mm3'])<.001 for v in step_details.values()),step_details)
    dimensions=match_step_bounds(imported.Solids,list(parts.values()))
    check('step_individual_bounds',len(dimensions)==8 and max(dimensions)<.0001,
        {'maximum_error_mm':max(dimensions),'tolerance_mm':.0001})
    check('step_solids_valid',all(s.isValid() for s in imported.Solids),'八件STEP实体回读有效')
    for name, info in summary['samples'].items():
        path = out/'trials'/'samples'/(name+'.stl'); mesh = Mesh.Mesh(str(path))
        check('sample_'+name, mesh.isSolid() and abs(mesh.BoundBox.ZMin) < 1e-4 and digest(path) == info['sha256'],
              {'closed': mesh.isSolid(), 'components': mesh.countComponents()})
    # 普通BoundBox可能包含曲面未裁剪范围，不能用作实际装配尺寸。
    bounds = Part.makeCompound(list(parts.values())+[module]).optimalBoundingBox(False,False)
    result['assembly_bbox_mm'] = [bounds.XLength, bounds.YLength, bounds.ZLength]
    result['passed'] = not result['failures']
    result['limitations'] = ['本报告只验证几何；真实参考切片另见print_validation.json，打印、声学、重心与温升待实测',
        '麦克风位置为用户授权预留，声口朝向、密封接触和实际电路板声路未确认',
        '扬声器仅完整包络，安装耳、音腔性能和USB线束须选型校准',
        '供电模块高度、实际固定孔、充电限流及电池放电倍率未实物确认；不代表续航已达标',
        '维护行程每3mm采样，不等于连续碰撞数学证明；软线束需拔插或留维护长度',
        '常规实体有效性不等于严格BOP曲面检查或全局最薄壁验证']
    result['hashes'] = {'source': summary['source_sha256'], 'step': digest(out/'enclosure.step'),
                        'fcstd': digest(out/'enclosure.FCStd')}
    (out/'fit_validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    summary['fit_verified'] = result['passed']
    (out/'validation.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    App.closeDocument(doc.Name)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT/'output')
    args = parser.parse_args()
    raise SystemExit(0 if verify(args.out.resolve())['passed'] else 1)
