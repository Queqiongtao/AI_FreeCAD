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
    mesh_write(doc.getObject('Speaker_Pads_Reference').Shape,os.path.join(CACHE,'pads.stl'))
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
            inner=min(ends,key=lambda p:(p-pt(0,0,n)).Length)
            x,s=(inner-P).dot(X),(inner-P).dot(S)
            kind='ordinary'
            if any(abs(p.z-top_z)<0.02 for p in ends):
                kind='cap_edge'
            elif n<=24.5 and any(math.hypot(x-hx,s-hs)<M4_HEAD_R+M4_HEAD_CLEARANCE+0.02 for hx,hs in SCREWS):
                kind='m4_head'
            elif math.hypot(x,s)>INNER_R+0.02 and abs(x)<=SPEAKER_W/2+0.52 and abs(s)<=SPEAKER_H/2+0.52:
                kind='speaker_corner'
            wall_samples.append({'kind':kind,'n_mm':n,'angle_deg':angle,'radial_segment_mm':outer.Length})
    wall_report={}
    for kind,minimum in (('ordinary',1.95),('m4_head',1.2),('speaker_corner',1.6),('cap_edge',1.2)):
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
    for x,s in SCREWS:
        angle=math.atan2(s,x)
        inward=-X*math.cos(angle)-S*math.sin(angle)
        tangent=-X*math.sin(angle)+S*math.cos(angle)
        for n in (7,12,16,19.9):
            for label,direction,end in (('inward',inward,4.899),
                                         ('side_positive',tangent,3.7),('side_negative',-tangent,3.7)):
                start=2.201
                origin=pt(x,s,n)+(inward*0.1 if label!='inward' else App.Vector())
                probe=Part.makeLine(origin+direction*start,origin+direction*end)
                length=frame.common(probe).Length
                assert length>=(end-start)*0.999,'M4 加强座截面不连续'
                boss_spans.append({'x_mm':x,'s_mm':s,'n_mm':n,'direction':label,'solid_span_mm':length})
        opening=local_rectangle(x,s,0.05,3.2,-2,2,7,19.9)
        assert frame.common(opening).Volume<0.001,'M4 外侧开口残留薄皮'
        bearing=frame.common(cyl(M4_HEAD_R,19.98,20,x,s)).Volume/0.02
        assert bearing>=4.0,'M4 螺丝头承压面积不足'
        bearing_areas.append(bearing)
    slot_volumes=[]
    for a in (0,90,180):
        probe=locator(a,LOCATOR_BACK_INNER_R,53.1-FIT_SIDE_CLEARANCE,8+2*FIT_SIDE_CLEARANCE,23.5,25.5)
        actual=frame.common(probe).Volume
        assert actual>=probe.Volume*0.999,'定位槽背部加强区不足'
        slot_volumes.append(actual)
    seat_volumes=[]
    for x,s in PINS:
        probe=cyl(PRESSURE_R-0.1,SPEAKER_FRONT_N-SPEAKER_BASE_T+0.01,SPEAKER_FRONT_N-0.01,x,s)
        actual=frame.common(probe).Volume
        assert actual>=probe.Volume*0.999,'喇叭承托底座不足'
        seat_volumes.append(actual)
    print('加固截面通过',len(boss_spans),'固定座截线',len(slot_volumes),'槽背',len(seat_volumes),'承托面',flush=True)
    pressure_floors=[]
    for x,s in PINS:
        probe=cyl(2.6,STRIP_FRONT_N+0.61,STRIP_FRONT_N+1.79,x,s)
        volume=rear.common(probe).Volume
        assert volume>=probe.Volume*0.999,'压耳中心盲孔后方实心顶不足'
        pressure_floors.append(volume)
    tie_open=Part.makeBox(3.8,1.8,5.8,App.Vector(21.1,TIE_FRONT_Y+0.1,16.1))
    tie_bridge=Part.makeBox(3.8,1.8,1.8,App.Vector(21.1,TIE_FRONT_Y+0.1,22.1))
    assert rear.common(tie_open).Volume<0.001,'扎带穿入口被堵塞'
    assert rear.common(tie_bridge).Volume>=tie_bridge.Volume*0.999,'扎带横桥缺失'
    report={'radial_wall_audit':wall_report,'carrier_rear_bed_contact_area_mm2':bed_area,
            'stl_sha256':{name:hashlib.sha256(Path(OUT,name+'.stl').read_bytes()).hexdigest() for name in ('main_shell','rear_cover')},
            'reinforcement_sections':{'m4_solid_spans':boss_spans,
                'm4_inward_wall_nominal_mm':M4_REINFORCE_R+M4_REINFORCE_OFFSET-2.2,
                'm4_side_wall_nominal_mm':math.sqrt(M4_REINFORCE_R**2-M4_REINFORCE_OFFSET**2)-2.2,
                'm4_outward_side_open':True,'m4_head_bearing_areas_mm2':bearing_areas,
                'locator_back_thickness_mm':53.1-FIT_SIDE_CLEARANCE-LOCATOR_BACK_INNER_R,
                'locator_back_probe_volumes_mm3':slot_volumes,'speaker_base_probe_volumes_mm3':seat_volumes,
                'speaker_base_thickness_mm':SPEAKER_BASE_T,
                'note':'截面连续性检查，不是有限元、极限载荷或实物强度试验。'},
            'pressure_blind_floor_nominal_mm':1.2,'pressure_floor_probe_volumes_mm3':pressure_floors,
            'cable_tie_opening_clear':True,'cable_tie_bridge_probe_mm3':rear.common(tie_bridge).Volume,
            'method':'从外向内求前圈径向实体段；9 个轴向截面、常规及螺丝/音箱角特定方位；顶部收平边缘单独分组。',
            'limitations':'离散径向检查不等于全局法向最薄壁；格栅、压耳、定位舌和锁盖座未纳入此壁厚统计。',
            'physical_fit_verified':False}
    with open(os.path.join(OUT,'fit_validation.json'),'w',encoding='utf-8') as f:
        json.dump(report,f,ensure_ascii=False,indent=2)
    print('承托架后侧落床面积',bed_area,flush=True)


main()
