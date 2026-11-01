"""只读复核生成的 P4 文档：前圈薄壁、架背落床面及参考体。使用 FreeCADCmd。"""
import ast
import hashlib
from pathlib import Path

ROOT_PATH=Path(__file__).resolve().parent
source_path=ROOT_PATH/'enclosure.py'
# 复用唯一建模源中的参数和坐标函数，去掉末尾执行入口，避免重新建模。
tree=ast.parse(source_path.read_text(encoding='utf-8'))
tree.body=[node for node in tree.body if not isinstance(node,ast.Try)]
scope={'__file__':str(source_path)}
exec(compile(tree,str(source_path),'exec'),scope)
globals().update({k:v for k,v in scope.items() if not k.startswith('__')})


def main():
    doc=App.openDocument(os.path.join(OUT,'enclosure.FCStd'))
    rear=doc.getObject('rear_cover').Shape
    frame=doc.getObject('main_shell').Shape
    usb_tool=usb_access_tool()
    assert rear.common(usb_tool).Volume<.001,'Type-C后盖通道堵塞'
    assert doc.getObject('Speaker_Reference').Shape.common(usb_tool).Volume<.001,'Type-C开口碰喇叭'
    usb_rim_checks=[]
    for x,n in ((USB_ACCESS_X-USB_ACCESS_WIDTH/2-.6,12),
                (USB_ACCESS_X+USB_ACCESS_WIDTH/2+.6,12),
                (USB_ACCESS_X-USB_ACCESS_WIDTH/2-.6,19),
                (USB_ACCESS_X+USB_ACCESS_WIDTH/2+.6,19),
                (USB_ACCESS_X,USB_ACCESS_N+USB_ACCESS_HEIGHT/2+.6),
                (USB_ACCESS_X,USB_ACCESS_N+USB_ACCESS_HEIGHT/2+2)):
        line=Part.makeLine(pt(x,60,n),pt(x,48,n))
        segments=rear.common(line).Edges
        assert segments,'Type-C开口旁边壳壁缺失'
        span=max(edge.Length for edge in segments)
        assert span>=1.6,'Type-C开口周围壳壁不足1.6 mm'
        usb_rim_checks.append({'x_n_mm':[x,n],'wall_segment_mm':span})
    assert doc.getObject('Speaker_Pads_Reference') is None,'旧压耳软垫参考体未移除'
    wall_samples=[]
    corner_angle=math.degrees(math.atan2(SPEAKER_H/2+0.5,SPEAKER_W/2+0.5))
    angles=set(range(0,360,10))
    for angle in (45,135,225,315,corner_angle,180-corner_angle,180+corner_angle,360-corner_angle):
        angles.add(angle)
    top_z=FRONT_Z+SIN*OUTER_R-COS*(MOUTH_N+TOP_FLAT_DEPTH)
    for n in (6.6,7.2,7.6,10,15,20,24,35,40):
        for angle in sorted(angles):
            a=math.radians(angle)
            u=X*math.cos(a)+S*math.sin(a)
            line=Part.makeLine(pt(0,0,n)+u*70,pt(0,0,n))
            edges=rear.common(line).Edges
            if not edges:
                continue
            outer=max(edges,key=lambda e:(e.CenterOfMass-pt(0,0,n)).Length)
            ends=[v.Point for v in outer.Vertexes]
            # 入口导角刻意收尖；独立六条孔旁截线验证余壁，不把孔缘当普通壁。
            if any(usb_tool.distToShape(Part.Vertex(p))[0]<USB_ACCESS_CHAMFER+.01 for p in ends):
                wall_samples.append({'kind':'usb_access_edge','n_mm':n,'angle_deg':angle,
                                     'radial_segment_mm':outer.Length})
                continue
            inner=min(ends,key=lambda p:(p-pt(0,0,n)).Length)
            x,s=(inner-P).dot(X),(inner-P).dot(S)
            kind='ordinary'
            if any(abs(p.z-top_z)<0.02 for p in ends):
                kind='cap_edge'
            elif math.hypot(x,s)>INNER_R+0.02 and abs(x)<=SPEAKER_W/2+0.52 and abs(s)<=SPEAKER_H/2+0.52:
                kind='speaker_corner'
            wall_samples.append({'kind':kind,'n_mm':n,'angle_deg':angle,'radial_segment_mm':outer.Length})
    wall_report={}
    for kind,minimum in (('ordinary',1.95),('speaker_corner',1.6),('cap_edge',1.2)):
        values=[v for v in wall_samples if v['kind']==kind]
        assert values,kind+'无壁厚样本'
        lowest=min(v['radial_segment_mm'] for v in values)
        print('径向壁厚',kind,len(values),lowest,flush=True)
        assert lowest>=minimum,kind+'径向实体段不足：'+str(sorted(values,key=lambda v:v['radial_segment_mm'])[:5])
        wall_report[kind]={'sample_count':len(values),'minimum_radial_segment_mm':lowest,
                           'lowest_samples':sorted(values,key=lambda v:v['radial_segment_mm'])[:5]}
    bed_plane=face([pt(-70,-70,FRAME_BACK_N),pt(70,-70,FRAME_BACK_N),
                    pt(70,70,FRAME_BACK_N),pt(-70,70,FRAME_BACK_N)])
    bed_area=frame.common(bed_plane).Area
    assert bed_area>300,'后侧落床面不足'
    # 检查生成实体中的实心截面，避免仅凭参数认定加强区存在。
    boss_spans=[]
    bearing_areas=[]
    head_clearance_checks=[]
    for x,s in SCREWS:
        bearing=frame.common(cyl(MODULE_HEAD_R,MODULE_SEAT_N-0.02,MODULE_SEAT_N,x,s)).Volume/0.02
        assert bearing>=8.0
        bearing_areas.append(bearing)
        probe=cyl(MODULE_BOSS_R-0.1,MODULE_MOUNT_FRONT_N+0.01,MODULE_SEAT_N-0.01,x,s).cut(cyl(MODULE_HOLE_R+0.01,15,18,x,s))
        assert frame.common(probe).Volume>=probe.Volume*0.999
        boss_spans.append(frame.common(probe).Volume)
        for travel in (0,0.5,1,2,4,8,16):
            head=cyl(MODULE_HEAD_R+MODULE_HEAD_CLEARANCE,MODULE_SEAT_N+travel,MODULE_SEAT_N+travel+MODULE_HEAD_H,x,s)
            assert frame.common(head).Volume<0.001
        head_clearance_checks.append(True)
    slot_volumes=[]
    for a in (0,90,180):
        probe=locator(a,52,54,6,14,16.5)
        actual=frame.common(probe).Volume
        assert actual>=probe.Volume*0.999,'前部承力环不连续'
        slot_volumes.append(actual)
    hook_sections=[]
    for a in HOOK_ANGLES:
        x=HOOK_RADIUS*math.cos(math.radians(a))
        pin=Part.makeCylinder(1.85,9.8,pt(x-4.9,HOOK_AXIS_S,HOOK_AXIS_N),X)
        assert frame.common(pin).Volume>=pin.Volume*.999,'一体横销缺失'
        root=box(x-4.8,x+4.8,HOOK_AXIS_S+1,50,26.4,29.2)
        assert rear.common(root).Volume>=root.Volume*.999,'挂钩承力根缺失'
        spans=[]
        for offset in (-1.9,-1.5,-1,-.5,0):
            line=Part.makeLine(pt(x,HOOK_AXIS_S+offset,17.3),pt(x,HOOK_AXIS_S+offset,22))
            span=rear.common(line).Length
            assert span>=2,'挂钩入口承力前翼过薄'
            spans.append(span)
        hook_sections.append({'pin_probe_mm3':pin.Volume,'root_probe_mm3':root.Volume,
                              'retaining_tip_section_spans_mm':spans})
    pad_checks=[]
    for name,x0,x1,s0,s1 in speaker_pad_rectangles():
        probe=box(x0,x1,s0,s1,SPEAKER_PAD_N+.001,SPEAKER_PAD_N+SPEAKER_PAD_MIN_T)
        volume=rear.common(probe).Volume
        assert volume>=probe.Volume*.999,'胶台实体不连续或不足2 mm厚'
        pad_checks.append({'name':name,'probe_volume_mm3':volume,
                           'contact_area_mm2':(x1-x0)*(s1-s0)})
    speaker=doc.getObject('Speaker_Reference').Shape
    assert abs(speaker.Volume-SPEAKER_W*SPEAKER_H*SPEAKER_T)<.001,'喇叭不是完整保守包络'
    assert rear.common(speaker).Volume+frame.common(speaker).Volume<.001,'完整喇叭包络碰壳'
    # 直接复用唯一源码中的外包络构建语句，另验箱体并未被藏到外壳之外。
    main_node=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='main')
    outer_nodes=[node for node in main_node.body if isinstance(node,ast.Assign)
                 and any(isinstance(t,ast.Name) and t.id in ('sections','envelope') for t in node.targets)]
    outer_scope=dict(scope)
    exec(compile(ast.Module(body=outer_nodes,type_ignores=[]),str(source_path),'exec'),outer_scope)
    clearance=box(-SPEAKER_W/2-SPEAKER_CLEARANCE,SPEAKER_W/2+SPEAKER_CLEARANCE,
        -SPEAKER_H/2-SPEAKER_CLEARANCE,SPEAKER_H/2+SPEAKER_CLEARANCE,
        SPEAKER_FRONT_N-SPEAKER_CLEARANCE,SPEAKER_BACK_N+SPEAKER_CLEARANCE)
    assert clearance.cut(outer_scope['envelope']).Volume<.001,'完整箱体及间隙超出外包络'
    assert rear.common(clearance).Volume+frame.common(clearance).Volume<.001,'完整箱体周边0.5 mm间隙不足'
    tape=doc.getObject('Speaker_Tape_Reference').Shape
    expected_tape=sum(c['contact_area_mm2'] for c in pad_checks)*SPEAKER_TAPE_T
    assert abs(tape.Volume-expected_tape)<.001,'胶层参考体厚度或面积错误'
    for name in ('Speaker_Hardware_Reference','Speaker_Washers_Reference','Speaker_Ears_Reference'):
        assert doc.getObject(name) is None,'仍有旧喇叭紧固件参考体'
    insertion=box(-SPEAKER_W/2-SPEAKER_CLEARANCE,SPEAKER_W/2+SPEAKER_CLEARANCE,
        -SPEAKER_H/2-SPEAKER_CLEARANCE,SPEAKER_H/2+SPEAKER_CLEARANCE,-60,SPEAKER_BACK_N+SPEAKER_CLEARANCE)
    assert rear.common(insertion).Volume<.001,'完整喇叭装入路径不通'
    air=box(-40,40,-19.5,19.5,SPEAKER_BACK_N+.001,SPEAKER_BACK_N+SPEAKER_FACE_CLEARANCE)
    assert rear.common(air).Volume<.001,'振膜前方2 mm净空不足'
    data=json.loads(Path(OUT,'validation.json').read_text(encoding='utf-8'))
    alignment=App.Vector(*data['speaker_grille']['axis_world']).dot(-N)
    assert abs(alignment-1)<1e-8,'出音孔轴未对齐发声面'
    for hole in data['speaker_grille']['holes']:
        x,s=hole['center_x_s_mm'];n0,n1=hole['wall_n_mm']
        bore=cyl(GRILLE_HOLE_DIAMETER/2,n0-GRILLE_END_MARGIN,n1+GRILLE_END_MARGIN,x,s)
        assert rear.common(bore).Volume<.001,'斜出音孔道未完整贯通'
        path=cyl(GRILLE_HOLE_DIAMETER/2,SPEAKER_BACK_N+.01,n0-GRILLE_END_MARGIN,x,s)
        assert rear.common(path).Volume<.001,'发声面到孔内端的整条声路被挡住'
    print('胶台实体、完整包络、装入路径及孔轴对齐检查通过',flush=True)
    insert_wall_checks=[]
    for x,s in BOLT_POINTS:
        bore=cyl(LOCK_INSERT_BORE/2,LOCK_INSERT_BACK_N-LOCK_INSERT_DEPTH+.001,
                 LOCK_INSERT_BACK_N-LOCK_INSERT_CHAMFER-.001,x,s)
        assert frame.copy(True).common(bore).Volume<.001,'热熔直孔孔径或深度不足'
        shoulder=cyl(LOCK_INSERT_BORE/2-.01,LOCK_INSERT_BACK_N-LOCK_INSERT_DEPTH-.3,
                     LOCK_INSERT_BACK_N-LOCK_INSERT_DEPTH-.1,x,s).cut(
            cyl(1.71,LOCK_INSERT_BACK_N-LOCK_INSERT_DEPTH-.4,LOCK_INSERT_BACK_N,x,s))
        shoulder_volume=frame.copy(True).common(shoulder).Volume
        assert shoulder_volume>=shoulder.Volume*.999,'热熔孔底部台阶缺失'
        spans=[]
        for n in (LOCK_INSERT_BACK_N-LOCK_INSERT_DEPTH+.1,
                  LOCK_INSERT_BACK_N-2,LOCK_INSERT_BACK_N-1,LOCK_INSERT_BACK_N-.4):
            for angle in range(0,360,30):
                direction=X*math.cos(math.radians(angle))+S*math.sin(math.radians(angle))
                origin=pt(x,s,n)
                line=Part.makeLine(origin+direction*(LOCK_INSERT_BORE/2+.01),
                                   origin+direction*(LOCK_BOSS_R-.01))
                span=frame.copy(True).common(line).Length
                assert span>=line.Length*.999 and span>=1.6,'热熔母座径向壁不连续或过薄'
                spans.append(span)
        for n in (LOCK_INSERT_BACK_N-.15,LOCK_INSERT_BACK_N-.01):
            for angle in range(0,360,30):
                direction=X*math.cos(math.radians(angle))+S*math.sin(math.radians(angle))
                origin=pt(x,s,n)
                line=Part.makeLine(origin+direction*(LOCK_INSERT_BORE/2+LOCK_INSERT_CHAMFER+.01),
                                   origin+direction*(LOCK_BOSS_R-.01))
                span=frame.copy(True).common(line).Length
                assert span>=line.Length*.999 and span>=1.6,'热熔入口导角外围过薄'
                spans.append(span)
        tool=cyl(2,LOCK_INSERT_BACK_N+.01,LOCK_INSERT_BACK_N+12,x,s)
        assert frame.copy(True).common(tool).Volume<.001,'热熔工具轴向入口被挡住'
        insert_wall_checks.append({'center_x_s_mm':[x,s],'radial_section_count':len(spans),
            'minimum_radial_section_mm':min(spans),'bore_clear':True,
            'bottom_shoulder_probe_volume_mm3':shoulder_volume,'heater_access_clear':True})
    tie_open=Part.makeBox(3.8,TIE_CHANNEL_DEPTH-.2,5.8,App.Vector(21.1,TIE_FRONT_Y+0.1,TIE_BASE_Z+.1))
    tie_bridge=Part.makeBox(3.8,1.8,1.8,App.Vector(21.1,TIE_FRONT_Y+0.1,TIE_BASE_Z+6.1))
    assert rear.common(tie_open).Volume<0.001,'扎带穿入口被堵塞'
    assert rear.common(tie_bridge).Volume>=tie_bridge.Volume*0.999,'扎带横桥缺失'
    tie_support_checks=[]
    for x in (18,25):
        for z in (TIE_BASE_Z-8,TIE_BASE_Z-4,TIE_BASE_Z-.5):
            y=TIE_FRONT_Y+TIE_BASE_Z+.1-z+1
            probe=Part.makeBox(2.8,.4,.2,App.Vector(x+.1,y,z))
            actual=rear.common(probe).Volume
            assert actual>=probe.Volume*.999,'扎带桥后下斜撑缺失'
            tie_support_checks.append(actual)
    report={'radial_wall_audit':wall_report,'carrier_rear_bed_contact_area_mm2':bed_area,
            'usb_access':{'rear_cover_channel_clear':True,'rim_wall_checks':usb_rim_checks,
                'minimum_sampled_rim_wall_mm':min(v['wall_segment_mm'] for v in usb_rim_checks),
                'entry_edge_samples_excluded_from_ordinary_wall':sum(v['kind']=='usb_access_edge' for v in wall_samples),
                'carrier_modified':False,'full_plug_path_verified':False,
                'note':'承托架保留，采用用户实物确认；仅证明后盖孔道贯通，不宣称保守插头扫掠全程零干涉。'},
            'stl_sha256':{name:hashlib.sha256(Path(OUT,name+'.stl').read_bytes()).hexdigest() for name in ('main_shell','rear_cover')},
            'reinforcement_sections':{'module_seat_probe_volumes_mm3':boss_spans,'module_head_bearing_areas_mm2':bearing_areas,
                'front_ring_radial_wall_mm':FRAME_R-51.9,
                'front_ring_probe_volumes_mm3':slot_volumes,
                'note':'截面连续性检查，不是有限元、极限载荷或实物强度试验。'},
            'speaker_mount_part':'rear_cover','speaker_pad_checks':pad_checks,
            'speaker_full_envelope_verified':True,'speaker_insertion_path_verified':True,
            'speaker_face_clearance_mm':SPEAKER_FACE_CLEARANCE,'speaker_grille_axis_alignment':alignment,
            'heat_insert_wall_checks':insert_wall_checks,
            'module_head_clearance_checks':head_clearance_checks,'module_engagement_mm':MODULE_THREAD_ENTRY_N-(MODULE_SEAT_N-MODULE_SCREW_L),
            'cable_tie_opening_clear':True,'cable_tie_bridge_probe_mm3':rear.common(tie_bridge).Volume,
            'cable_tie_support_probe_volumes_mm3':tie_support_checks,
            'cable_tie_base_z_mm':TIE_BASE_Z,'cable_tie_clear_opening_mm':[3.8,TIE_CHANNEL_DEPTH-.2,5.8],
            'method':'从外向内求前圈径向实体段；9 个轴向截面、常规及螺丝/音箱角特定方位；顶部收平边缘单独分组。',
            'limitations':'离散径向检查不等于全局法向最薄壁；喇叭采用完整总包络避让；格栅孔缘未纳入此径向壁厚统计；锁盖热熔母座另作孔径、台阶及径向截线检查。',
            'hook_sections':hook_sections,'physical_fit_verified':False}
    with open(os.path.join(OUT,'fit_validation.json'),'w',encoding='utf-8') as f:
        json.dump(report,f,ensure_ascii=False,indent=2)
    print('承托架后侧落床面积',bed_area,flush=True)


main()
