"""微雪 ESP32-P4-WIFI6-Touch-LCD-3.4C 桌面外壳，唯一建模源。"""
import os
import math
import json
import traceback
import FreeCAD as App
import Part
import MeshPart

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'output')
CACHE = os.path.join(ROOT, 'archive', 'preview_meshes')
MODEL = 'ESP32-P4-WIFI6-TOUCH-LCD-3_4C.stp'
DOC_NAME = 'Waveshare_ESP32_P4_WIFI6_Touch_LCD_3_4C_Enclosure'
TILT_DEG = 40.0
MODULE_R = 57.5
FRONT_Z = 61.0
OUTER_R = 57.2
INNER_R = 55.2
MOUTH_N = 6.3
FLOOR_T = 2.6
SPEAKER_W = 100.0
SPEAKER_H = 45.0
SPEAKER_T = 21.0
SPEAKER_FRONT_N = 22.0
SPEAKER_BACK_N = 43.0
PIN_R = 2.5
PIN_H = 4.0
SPEAKER_EAR_T = 21.0  # 未单独测量耳厚，先按整箱厚度；后盖压紧面随此参数调整。
HOLE_X = 45.0
HOLE_S = 18.0
STRIP_FRONT_N = SPEAKER_FRONT_N + SPEAKER_EAR_T + 0.2
FOOT_RX = 48.0
FOOT_RY = 42.0
FOOT_CY = 25.0
ANGLE = math.radians(TILT_DEG)
SIN, COS = math.sin(ANGLE), math.cos(ANGLE)
X, Z = App.Vector(1, 0, 0), App.Vector(0, 0, 1)
N = App.Vector(0, -SIN, COS)
S = App.Vector(0, COS, SIN)
P = App.Vector(0, 0, FRONT_Z)
SCREWS = [(x, s) for x in (-37.5, 37.5) for s in (-37.5, 37.5)]
PINS = [(x, s) for x in (-HOLE_X, HOLE_X) for s in (-HOLE_S, HOLE_S)]


def pt(x, s, n):
    return P + X*x + S*s - N*n


def face(points):
    return Part.Face(Part.makePolygon(points + [points[0]]))


def box(x0, x1, s0, s1, n0, n1):
    return face([pt(x0, s0, n0), pt(x1, s0, n0), pt(x1, s1, n0),
                 pt(x0, s1, n0)]).extrude(-N*(n1-n0))


def cyl(r, n0, n1, x=0, s=0):
    return Part.makeCylinder(r, n1-n0, pt(x, s, n0), -N)


def hex_prism(x, s, n0, n1, across=5.65):
    r = across / math.sqrt(3)
    return face([pt(x+r*math.cos(i*math.pi/3+math.pi/6), s+r*math.sin(i*math.pi/3+math.pi/6), n0)
                 for i in range(6)]).extrude(-N*(n1-n0))


def fuse(shapes):
    result = shapes[0]
    for shape in shapes[1:]:
        result = result.fuse(shape)
    return result.removeSplitter()


def center(shape):
    return sum((v.CenterOfMass*v.Volume for v in shape.Solids),App.Vector())/sum(v.Volume for v in shape.Solids)


def rib(x, s, n0=20, n1=22):
    a = math.atan2(s, x)
    u, v = X*math.cos(a)+S*math.sin(a), -X*math.sin(a)+S*math.cos(a)
    origin = pt(0, 0, n0)
    r0 = math.hypot(x, s)-1
    return face([origin+u*r0-v*2, origin+u*54-v*2,
                 origin+u*54+v*2, origin+u*r0+v*2]).extrude(-N*(n1-n0))


def ellipse(z, rx, ry, cy):
    points = [App.Vector(rx*math.cos(i*math.pi/24), cy+ry*math.sin(i*math.pi/24), z)
              for i in range(48)]
    return Part.makePolygon(points+[points[0]])


def feature(doc, name, shape, color, visible=True):
    obj = doc.addObject('Part::Feature', name)
    obj.Label = name
    obj.Shape = shape
    if App.GuiUp:
        obj.ViewObject.ShapeColor = color
        obj.ViewObject.Visibility = visible
    return obj


def configure_display(doc):
    """GUI 加载后应用显示设置；仅更改显示，不重建几何。"""
    doc.Label='微雪 ESP32-P4-WIFI6-Touch-LCD-3.4C 两件式外壳'
    if not App.GuiUp:
        return
    visible={'main_shell','rear_cover','Module_Reference'}
    for obj in doc.Objects:
        obj.ViewObject.Visibility=obj.Name in visible
        if obj.Name=='Module_Reference':
            obj.ViewObject.ShapeColor=(0.10,0.12,0.14)
        elif obj.Name=='Speaker_Reference':
            obj.ViewObject.ShapeColor=(0.25,0.45,0.34)
        else:
            obj.ViewObject.ShapeColor=(0.69,0.73,0.72)
    doc.recompute()


def mesh_write(shape, path, printing=False):
    shape = shape.copy()
    if printing:
        shape.Placement = App.Placement(App.Vector(), App.Rotation(-N, Z)).multiply(shape.Placement)
        vertices = shape.tessellate(0.05)[0]
        shape.translate(App.Vector(0, 0, -min(v.z for v in vertices)))
    mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.1,
                                  AngularDeflection=0.35, Relative=False)
    mesh.write(path)
    return mesh



SPLIT_N = 26.0
COVER_START_N = 26.25
BOLT_POINTS = [(-22.0,-38.0),(22.0,-38.0)]
BOLT_SEAT_N = 35.0
SEAM_CLEARANCE = 0.25


def radial_wedge(x, s, r0, r1, front_outer, back, width):
    """沿半径向内延伸的 45°承托筋，模块贴面朝下时逐层长出。"""
    a = math.atan2(s, x)
    u, v = X*math.cos(a)+S*math.sin(a), -X*math.sin(a)+S*math.cos(a)
    def q(r,n):
        return pt(0,0,n)+u*r-v*width/2
    front_inner = front_outer+r1-r0
    return face([q(r0,front_inner),q(r1,front_outer),q(r1,back),q(r0,back)]).extrude(v*width)


def locator(angle, r0, r1, width, n0, n1):
    a=math.radians(angle)
    u,v=X*math.cos(a)+S*math.sin(a),-X*math.sin(a)+S*math.cos(a)
    return face([pt(0,0,n0)+u*r+v*t for r,t in
                 [(r0,-width/2),(r1,-width/2),(r1,width/2),(r0,width/2)]]).extrude(-N*(n1-n0))


def cable_envelope(points, radius=1.75):
    """线径占位，仅验证通路；折线不能替代真实线材弯曲半径。"""
    pieces=[Part.makeSphere(radius,p) for p in points]
    for a,b in zip(points,points[1:]):
        direction=b-a
        pieces.append(Part.makeCylinder(radius,direction.Length,a,direction))
    return fuse(pieces)


def main():
    os.makedirs(OUT,exist_ok=True)
    os.makedirs(CACHE,exist_ok=True)
    sections=[(0,48,42,25),(3,51,45,25),(10,61,56,25),(25,64,64,20),
              (45,64,65,18),(65,61,58,12),(85,57,51,6),(100,45,41,0),
              (115,23,23,0),(120,1,1,0)]
    envelope=Part.makeLoft([ellipse(*v) for v in sections],True,False).common(cyl(OUTER_R,MOUTH_N,110))
    inner=[(FLOOR_T,46,39.2,25),(10,55.5,50,25),(25,61,61,20),
           (45,61,62,18),(65,58,55,12),(85,54,48,6),(100,42,38,0),
           (112,20,20,0),(116,1,1,0)]
    above_floor=Part.makeBox(300,300,160,App.Vector(-150,-100,FLOOR_T))
    cavity=Part.makeLoft([ellipse(*v) for v in inner],True,False).common(cyl(INNER_R,MOUTH_N,110)).common(above_floor)
    for x,s in SCREWS:
        cavity=cavity.fuse(cyl(3.65,MOUTH_N,24.5,x,s).common(above_floor))
    cavity=cavity.fuse(box(-50.5,50.5,-23,23,MOUTH_N,43.5)).removeSplitter()
    skin=envelope.cut(cavity)
    main_parts=[skin.common(cyl(OUTER_R,MOUTH_N,SPLIT_N))]
    rear=skin.common(cyl(OUTER_R,COVER_START_N,110))
    # 环形斜托先从外壁逐层收向螺丝座，避免旧安装框悬空。
    ring=cyl(55.5,13.2,20).cut(Part.makeCone(55.5,52.2,3.3,pt(0,0,13.2),-N))
    ring=ring.cut(cyl(52.2,16.5,21))
    main_parts.append(ring)
    for x,s in SCREWS:
        main_parts.append(cyl(3.1,MOUTH_N,20,x,s))
    for x,s in PINS:
        main_parts.extend([radial_wedge(x,s,47,55.8,11,22,6),
                           cyl(3.7,20.8,22,x,s),cyl(PIN_R,22,26,x,s)])
    for x,s in BOLT_POINTS:
        main_parts.extend([radial_wedge(x,s,40,55.8,7,26,8),cyl(5,20,26,x,s)])
    for a in (0,90,180):
        main_parts.extend([locator(a,54.1,55.7,10,25.5,29.25),
                           locator(a,56.05,57.2,8,25.5,COVER_START_N),
                           radial_wedge(math.cos(math.radians(a)),math.sin(math.radians(a)),
                                        54.1,56.8,23,26,10)])
        rear=rear.cut(locator(a,53.85,55.95,10.5,26.25,29.5))
    main_shell=fuse(main_parts).common(envelope)
    for x,s in SCREWS:
        main_shell=main_shell.cut(cyl(2.2,5.9,21,x,s)).cut(cyl(3.65,20,27,x,s))
    for x,s in BOLT_POINTS:
        main_shell=main_shell.cut(cyl(1.7,18,27,x,s))
        main_shell=main_shell.cut(hex_prism(x,s,21,23.6,5.7))
        # 从空腔内侧向下滑入螺母；后方留 2.4 mm 实体承压肩。
        main_shell=main_shell.cut(box(x-2.9,x+2.9,s,s+9,21,23.6))
    main_shell=main_shell.removeSplitter()
    # 后盖一体压紧耳部，0.5 mm 软垫压缩到 0.2 mm；耳厚须实测后调参。
    for x,s in PINS:
        pressure=cyl(4.5,STRIP_FRONT_N,110,x,s).common(envelope)
        pressure=pressure.cut(cyl(2.8,STRIP_FRONT_N-0.1,STRIP_FRONT_N+5,x,s))
        rear=rear.fuse(pressure)
    for x,s in BOLT_POINTS:
        seat=cyl(5.5,29.5,BOLT_SEAT_N,x,s)
        support=Part.makeBox(8,17,14,App.Vector(x-4,-12,FLOOR_T)).common(envelope)
        rear=rear.fuse(seat).fuse(support)
        rear=rear.cut(cyl(1.7,26,36,x,s)).cut(cyl(3.3,BOLT_SEAT_N,110,x,s))
    # 背部唯一线束出口：20×12、R3，沿世界 Y 方向贯穿。
    outlet=fuse([Part.makeBox(14,110,12,App.Vector(-7,40,18)),
                 Part.makeBox(20,110,6,App.Vector(-10,40,21))]+
                [Part.makeCylinder(3,110,App.Vector(x,40,z),App.Vector(0,1,0))
                 for x in (-7,7) for z in (21,27)])
    rear=rear.cut(outlet)
    for x in range(-36,37,6):
        rear=rear.cut(box(x-1.4,x+1.4,-12,12,48,110).common(above_floor))
    # 两柱加短横梁组成一体扎带桥，4 mm 跨距可短桥接。
    tie=fuse([Part.makeBox(3,12,8,App.Vector(x,73,16)) for x in (18,25)]+
             [Part.makeBox(10,12,2,App.Vector(18,73,22))]).common(envelope)
    rear=rear.fuse(tie)
    recess=Part.Face(ellipse(-1,43,37,25)).extrude(Z*1.6)
    rear=rear.cut(recess).removeSplitter()
    speaker=box(-50,50,-22.5,22.5,22,43)
    for x,s in PINS:
        speaker=speaker.cut(cyl(3,21,44,x,s))
    shapes={'main_shell':main_shell,'rear_cover':rear}
    m4_heads=[cyl(3.5,20,24,x,s) for x,s in SCREWS]
    m3_heads=[cyl(2.8,35,38,x,s) for x,s in BOLT_POINTS]
    m3_shafts=[cyl(1.5,19,35,x,s) for x,s in BOLT_POINTS]
    nuts=[hex_prism(x,s,21.1,23.5,5.5).cut(cyl(1.5,21,24,x,s)) for x,s in BOLT_POINTS]
    plug=box(-18.9,-5.9,29.2,44.2,7.5,16.5)
    wire=cable_envelope([pt(-12.4,44.2,12),pt(-12.4,48,18),pt(-12.4,48,45),
                         pt(-12.4,35,50),App.Vector(0,65,24),App.Vector(0,100,24)])
    print('完成两件几何，开始快速验证',flush=True)
    checks={}
    for name,shape in shapes.items():
        print(name,shape.isValid(),len(shape.Solids),shape.Volume,flush=True)
        assert shape.isValid() and len(shape.Solids)==1,name
        overlap=shape.common(speaker).Volume
        print('音箱干涉',name,overlap,flush=True)
        assert overlap<0.02,name+'碰音箱'
        assert shape.common(plug).Volume<0.02,name+'挡内部插头'
        wire_overlap=shape.common(wire).Volume
        print('线束干涉',name,wire_overlap,flush=True)
        assert wire_overlap<0.02,name+'挡内部走线'
        checks[name]={'valid':True,'solids':1,'volume_mm3':shape.Volume,'speaker_overlap_mm3':overlap}
    assert main_shell.common(rear).Volume<0.02,'两壳干涉'
    assert speaker.common(wire).Volume<0.02,'线束碰音箱'
    for hardware in m4_heads+m3_heads+m3_shafts+nuts:
        for name,shape in shapes.items():
            assert shape.common(hardware).Volume<0.02,name+'碰紧固件'
    for x,s in SCREWS:
        assert main_shell.common(cyl(3.5,20,110,x,s)).Volume<0.02,'M4工具路径'
    for x,s in BOLT_POINTS:
        tool=cyl(2,38,110,x,s)
        assert tool.common(rear).Volume<0.02,'M3工具路径'
        assert tool.common(main_shell).Volume+tool.common(speaker).Volume<0.02
    for nut in nuts:
        for distance in (0,1,2,4,6,8,10):
            moved=nut.copy();moved.translate(S*distance)
            assert main_shell.common(moved).Volume<0.02,'螺母装入路径'
    travel_checks=[]
    for travel in (0,0.5,1,2,4,8,16,24,32,48,64):
        moved=rear.copy();moved.translate(-N*travel)
        overlaps={name:moved.common(shape).Volume for name,shape in
                  [('main_shell',main_shell),('speaker',speaker),('M4_heads',Part.makeCompound(m4_heads))]}
        print('合盖',travel,overlaps,flush=True)
        assert max(overlaps.values())<0.02,'合盖行程干涉'
        travel_checks.append({'travel_mm':travel,'overlaps_mm3':overlaps})
    ring_passed=sum(rear.isInside(App.Vector(45.5*math.cos(i*math.pi/36),
                  25+39.5*math.sin(i*math.pi/36),0.1),0.01,False) for i in range(72))
    assert ring_passed==72,'完整底环'
    for inset in (0.3,1.25,3.75,4.7):
        assert all(rear.isInside(App.Vector((48-inset)*math.cos(i*math.pi/36),
                   25+(42-inset)*math.sin(i*math.pi/36),0.1),0.01,False) for i in range(72)),'底环宽度采样'
    max_radius=max(math.hypot((v-P).dot(X),(v-P).dot(S)) for shape in shapes.values() for v in shape.tessellate(0.08)[0])
    assert max_radius<=OUTER_R+0.002,'正面外露'
    assert rear.common(outlet).Volume<0.02,'出线孔不通'
    print('快速验证通过，导入完整模块',flush=True)
    source=Part.read(os.path.join(ROOT,'reference',MODEL))
    module=source.copy()
    module.Placement=App.Placement(P-N*3.75,App.Rotation(X,TILT_DEG)).multiply(module.Placement)
    groups={}
    for i,solid in enumerate(module.Solids):
        b=solid.BoundBox
        key=('large',i) if max(b.XLength,b.YLength,b.ZLength)>15 else tuple(int(math.floor(c/12)) for c in (b.Center.x,b.Center.y,b.Center.z))
        groups.setdefault(key,[]).append((i,solid))
    for name,shape in shapes.items():
        total=0
        for group in groups.values():
            b=App.BoundBox()
            for _,solid in group:b.add(solid.BoundBox)
            if not shape.BoundBox.intersect(b):continue
            bounds=Part.makeBox(max(b.XLength,0.001),max(b.YLength,0.001),max(b.ZLength,0.001),App.Vector(b.XMin,b.YMin,b.ZMin))
            if shape.common(bounds).Volume<0.00001:continue
            for i,solid in group:
                overlap=shape.common(solid).Volume
                if overlap>0.001:print('实际模块干涉',name,i,overlap,flush=True)
                total+=overlap
        print('完整模块干涉',name,total,flush=True)
        assert total<0.02,name+'碰模块'
        checks[name]['module_overlap_mm3']=total
    masses=[(center(module),220),(center(speaker),100)]+[(center(v),v.Volume*0.00127) for v in shapes.values()]
    mass=sum(m for _,m in masses)
    com=sum((c*m for c,m in masses),App.Vector())/mass
    # 椭圆支撑函数减质心投影，取各倾覆边界法向的最小角度。
    tip=min(math.degrees(math.atan2(math.hypot(48*math.cos(i*math.pi/36),42*math.sin(i*math.pi/36))-
            com.x*math.cos(i*math.pi/36)-(com.y-25)*math.sin(i*math.pi/36),com.z)) for i in range(72))
    doc=App.newDocument(DOC_NAME)
    doc.Label='微雪 ESP32-P4-WIFI6-Touch-LCD-3.4C 两件式外壳'
    objects=[feature(doc,name,shape,(0.69,0.73,0.72)) for name,shape in shapes.items()]
    for name,shape in [('Module_Reference',module),('Speaker_Reference',speaker),
                       ('M4_Heads_Reference',Part.makeCompound(m4_heads)),('M3_Heads_Reference',Part.makeCompound(m3_heads)),
                       ('M3_Shafts_Reference',Part.makeCompound(m3_shafts)),('M3_Nuts_Reference',Part.makeCompound(nuts)),
                       ('Internal_USB_Plug_Reference',plug),('Cable_Route_Reference',wire)]:
        feature(doc,name,shape,(0.25,0.45,0.34),False)
    for name,shape in shapes.items():
        mesh=mesh_write(shape,os.path.join(OUT,name+'.stl'),printing=name=='main_shell')
        assert mesh.isSolid() and len(mesh.getSeparateComponents())==1,name+'网格不封闭'
        mesh_write(shape,os.path.join(CACHE,name+'.stl'))
        checks[name]['mesh_closed']=True
        steep=0
        for facet in mesh.Facets:
            if facet.Normal.z < -0.707 and min(p[2] for p in facet.Points)>4:
                a,b,c=[App.Vector(*p) for p in facet.Points]
                steep+=(b-a).cross(c-a).Length/2
        checks[name]['steep_overhang_mm2']=steep
    Part.export(objects,os.path.join(OUT,'enclosure.step'))
    imported=Part.read(os.path.join(OUT,'enclosure.step'))
    assert imported.isValid() and len(imported.Solids)==2
    for name,shape in [('module',cyl(MODULE_R,0,6)),('speaker',speaker),
                       ('section',rear.common(Part.makeBox(150,250,160,App.Vector(0,-100,0)))),
                       ('fasteners',Part.makeCompound(m3_heads+m3_shafts+nuts))]:
        mesh_write(shape,os.path.join(CACHE,name+'.stl'))
    doc.recompute();configure_display(doc);doc.saveAs(os.path.join(OUT,'enclosure.FCStd'))
    # 同尺寸螺母袋与止口的局部试装件，归档目录不混入正式打印件。
    fit_dir=os.path.join(ROOT,'archive','fit_samples');os.makedirs(fit_dir,exist_ok=True)
    sample=main_shell.common(box(12,31,-49,-28,19,30))
    mesh_write(sample,os.path.join(fit_dir,'nut_pocket.stl'),printing=True)
    for name,shape in [('locator_tongue',main_shell),('locator_socket',rear)]:
        sample=shape.common(box(51,58,-8,8,22,32))
        mesh_write(sample,os.path.join(fit_dir,name+'.stl'),printing=True)
    metrics={'module_model':MODEL,'module_source_solids':len(source.Solids),'tilt_deg':40,
             'parts':checks,'step_solids':2,'front_projection_radius_mm':max_radius,
             'front_occlusion_margin_mm':MODULE_R-max_radius,'bottom_ring_passed':ring_passed,
             'bottom_ring_width_nominal_mm':5,'bottom_plate_min_mm':2,
             'seam_clearance_mm':0.25,'locator_engagement_mm':3,'locator_side_clearance_mm':0.25,
             'axial_stop_pads':3,
             'rear_screw':'2 × M3×16 内六角圆柱头，M3 六角螺母对边 5.5、厚 2.4',
             'nut_retaining_shoulder_mm':2.4,
             'module_screw':'4 × M4×16，预计入牙约 2 mm，须实测有效深度',
             'm4_head_pocket_radial_wall_mm':OUTER_R-math.hypot(37.5,37.5)-3.65,
             'speaker_corner_clearance_wall_mm':OUTER_R-math.hypot(50.5,23),
             'locator_socket_radial_wall_mm':OUTER_R-55.95,
             'speaker_dimensions_mm':[100,45,21],'speaker_hole_pitch_mm':[90,36],
             'speaker_pin_diameter_mm':5,'speaker_ear_thickness_assumed_mm':SPEAKER_EAR_T,
             'speaker_pad_compressed_mm':0.2,'rear_outlet_mm':[20,12],'outlet_corner_radius_mm':3,
             'nut_insertion_travel_mm':[0,1,2,4,6,8,10],
             'cable_reference_diameter_mm':3.5,'cable_bend_radius_verified':False,
             'bottom_ring_width_samples':288,
             'assembly_travel':travel_checks,'cavity_cm3':cavity.Volume/1000,
             'estimated_module_mass_g':220,'estimated_speaker_mass_g':100,
             'estimated_total_mass_g':mass,'estimated_tip_angle_deg':tip,
             'microphone_hole_verified':False,'physical_fit_verified':False}
    with open(os.path.join(OUT,'validation.json'),'w',encoding='utf-8') as f:
        json.dump(metrics,f,ensure_ascii=False,indent=2)
    print('全部导出完成',OUT,flush=True)


try:
    main()
except Exception:
    traceback.print_exc()
