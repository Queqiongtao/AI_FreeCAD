"""微雪 ESP32-P4-WIFI6-Touch-LCD-3.4C 桌面外壳，唯一建模源。"""
import os
import math
import json
import traceback
import FreeCAD as App
import Part
import MeshPart

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get('P4_OUTPUT_DIR', os.path.join(ROOT, 'output'))
CACHE = os.environ.get('P4_CACHE_DIR', os.path.join(ROOT, 'archive', 'preview_meshes'))
MODEL = 'ESP32-P4-WIFI6-TOUCH-LCD-3_4C.stp'
DOC_NAME = 'Waveshare_ESP32_P4_WIFI6_Touch_LCD_3_4C_Enclosure'
TILT_DEG = 40.0
MODULE_R = 57.5
FRONT_Z = 61.0
OUTER_R = 57.2
INNER_R = 54.8  # 连续后盖圆柱区普通壁厚 2.4 mm。
MOUTH_N = 6.3
FLOOR_T = 2.6
SPEAKER_W = 100.0
SPEAKER_H = 45.0
SPEAKER_T = 21.0
SPEAKER_FRONT_N = 22.0
SPEAKER_BACK_N = SPEAKER_FRONT_N + SPEAKER_T
PIN_R = 2.8
PIN_H = 1.6
SPEAKER_EAR_T = 2.0  # 用户已确认：安装耳厚 2 mm，位于箱体厚度中部。
SPEAKER_EAR_CENTER_OFFSET = SPEAKER_T/2
SPEAKER_EAR_R = 4.5
SPEAKER_EAR_FRONT_N = SPEAKER_FRONT_N+SPEAKER_EAR_CENTER_OFFSET-SPEAKER_EAR_T/2
SPEAKER_SEAT_N = SPEAKER_EAR_FRONT_N+SPEAKER_EAR_T
SPEAKER_BOSS_R = 6.6
SPEAKER_NUT_FRONT_N = SPEAKER_SEAT_N+2.4
SPEAKER_BOSS_BACK_N = SPEAKER_NUT_FRONT_N+3.2
SPEAKER_WASHER_T = 0.5
SPEAKER_SCREW_L = 8.0
SPEAKER_SERVICE_R = 7.0  # 未知真实箱体在耳根处的形状，此范围是待实物复核的安装操作区。
HOLE_X = 45.0
HOLE_S = 18.0
PRESSURE_R = 4.5
PIN_LEAD_H = 0.4
MODULE_HEAD_R = 2.35
MODULE_HEAD_H = 2.5
MODULE_HEAD_CLEARANCE = 0.3
MODULE_SEAT_N = 17.1
MODULE_MOUNT_FRONT_N = 15.1
MODULE_SCREW_L = 6.0
MODULE_HOLE_R = 1.45
MODULE_BOSS_R = 5.0
MODULE_THREAD_ENTRY_N = 13.1
MODULE_ORIGINAL_TIP_N = 11.1  # 保持原厂螺丝尖端位置，不额外加深入牙。
MODULE_RIB_W = 8.0
FRAME_R = 54.3
LOCATOR_BACK_INNER_R = 51.0
LOCATOR_BACK_WIDTH = 12.5
FIT_SIDE_CLEARANCE = 0.30
FIT_TIP_CLEARANCE = 0.30
FIT_LEAD = 0.6
ELEPHANT_RELIEF = 0.3
NUT_AF = 6.0
NUT_FRONT_N = 20.8
NUT_BACK_N = 23.6
NUT_ENTRY_W = 6.2
NUT_BOSS_R = 5.4
NUT_ROOF_PEAK_N = 17.7
NUT_BOSS_FRONT_N = 16.1
TOP_FLAT_DEPTH = 1.6
TOP_MOUTH_RELIEF = 0.8
TIE_FRONT_Y = 56.0
TIE_BACK_Y = 78.0
FOOT_RX = 48.0
FOOT_RY = 42.0
FOOT_CY = 25.0
ANGLE = math.radians(TILT_DEG)
SIN, COS = math.sin(ANGLE), math.cos(ANGLE)
X, Z = App.Vector(1, 0, 0), App.Vector(0, 0, 1)
N = App.Vector(0, -SIN, COS)
S = App.Vector(0, COS, SIN)
P = App.Vector(0, 0, FRONT_Z)
SCREWS = [(39.25,-10.0),(39.25,17.0),(-39.25,17.0),(-39.25,-17.0)]
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
        if obj.Name=='main_shell':
            obj.Label='内藏承托架（main_shell）'
        elif obj.Name=='rear_cover':
            obj.Label='连续外圈后盖（rear_cover）'
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
        shape.Placement = App.Placement(App.Vector(), App.Rotation(N, Z)).multiply(shape.Placement)
        vertices = shape.tessellate(0.05)[0]
        shape.translate(App.Vector(0, 0, -min(v.z for v in vertices)))
    mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.1,
                                  AngularDeflection=0.35, Relative=False)
    mesh.write(path)
    return mesh



FRAME_BACK_N = 26.0
BOLT_POINTS = [(-22.0,-38.0),(22.0,-38.0)]
BOLT_SEAT_N = 35.0
SEAM_CLEARANCE = 0.25


def radial_wedge(x, s, r0, r1, front_outer, back, width):
    """沿半径向内延伸的 45°承托筋；实际打印姿态由网格导出确定。"""
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


def local_rectangle(x, s, u0, u1, t0, t1, n0, n1):
    """以安装孔径向为横轴的局部矩形，用于朝外开放的固定座。"""
    a=math.atan2(s,x)
    u,v=X*math.cos(a)+S*math.sin(a),-X*math.sin(a)+S*math.cos(a)
    origin=pt(x,s,n0)
    return face([origin+u*r+v*t for r,t in [(u0,t0),(u1,t0),(u1,t1),(u0,t1)]]).extrude(-N*(n1-n0))


def locator_lead(angle):
    # 使用明确的平面线框放样，避免对布尔运算后的整件施加易失效圆角。
    a=math.radians(angle)
    u,v=X*math.cos(a)+S*math.sin(a),-X*math.sin(a)+S*math.cos(a)
    wires=[]
    lead=0.4  # 缩短收尖段，让侧舌在 0.2 mm 层高下尽早形成完整截面。
    for n,r0,r1,w in [(23,53.1+lead,56.3-lead,8-2*lead),(23+lead,53.1,56.3,8)]:
        points=[pt(0,0,n)+u*r+v*t for r,t in [(r0,-w/2),(r1,-w/2),(r1,w/2),(r0,w/2)]]
        wires.append(Part.makePolygon(points+[points[0]]))
    return Part.makeLoft(wires,True,True).fuse(locator(angle,53.1,56.3,8,23+lead,26.1))


def locator_entry(angle):
    a=math.radians(angle)
    u,v=X*math.cos(a)+S*math.sin(a),-X*math.sin(a)+S*math.cos(a)
    wires=[]
    for n,r0,r1,w in [(25.7,52.8,55.1,8.6),(26.05,52.45,55.45,9.3)]:
        points=[pt(0,0,n)+u*r+v*t for r,t in [(r0,-w/2),(r1,-w/2),(r1,w/2),(r0,w/2)]]
        wires.append(Part.makePolygon(points+[points[0]]))
    return Part.makeLoft(wires,True,True)


def locator_roof(angle):
    a=math.radians(angle)
    u,v=X*math.cos(a)+S*math.sin(a),-X*math.sin(a)+S*math.cos(a)
    def q(t,n):return pt(0,0,n)+u*52.8+v*t
    return face([q(-4.3,22.7),q(0,18.4),q(4.3,22.7)]).extrude(u*2.3)


def down_support(profile, direction, depth, envelope, above_floor):
    """沿世界 Z 向下、水平等距伸向壳壁；每层横向增长不超过层高。"""
    return profile.extrude((direction-Z)*depth).common(envelope).common(above_floor)


def write_print_features():
    """向独立切片检查器提供坐标和功能区域；以 STL 截面验证实际挤出。"""
    features=[]
    def add(name,part,bounds,space='local',cross=None,contact_annulus=None):
        features.append({'name':name,'part':part,'bounds':bounds,'space':space,'cross':cross,
                         'contact_annulus':contact_annulus})
    for i,(x,s) in enumerate(SCREWS):
        add('module_seat_'+str(i),'main_shell',[x-5.1,x+5.1,s-5.1,s+5.1,
            MODULE_MOUNT_FRONT_N+0.05,MODULE_SEAT_N-0.05],contact_annulus=[x,s,MODULE_HOLE_R,MODULE_BOSS_R])
        r=math.hypot(x,s)
        add('module_arm_'+str(i),'main_shell',[min(x,x/r*54)-4,max(x,x/r*54)+4,
            min(s,s/r*54)-4,max(s,s/r*54)+4,MODULE_MOUNT_FRONT_N+0.05,20.45])
    for i,(x,s) in enumerate(BOLT_POINTS):
        add('nut_pocket_'+str(i),'main_shell',[x-5.6,x+5.6,s-3.7,s+9.1,16.05,26.01])
        # 锁紧承压座止于 n=35；后方大头孔和斜撑的交线另由全局承托检查覆盖。
        add('m3_seat_'+str(i),'rear_cover',[x-5.7,x+5.7,s-5.7,s+5.7,29.55,34.95])
    for i,(x,s) in enumerate(PINS):
        add('speaker_locator_'+str(i),'rear_cover',[x-2.9,x+2.9,s-2.9,s+2.9,
            SPEAKER_SEAT_N-PIN_H+0.05,SPEAKER_SEAT_N-0.05],contact_annulus=[x,s,1.7,2.8])
        add('speaker_seat_'+str(i),'rear_cover',[x-4.6,x+4.6,s-4.6,s+4.6,
            SPEAKER_SEAT_N+0.05,SPEAKER_NUT_FRONT_N-0.05])
        add('speaker_nut_'+str(i),'rear_cover',[x-SPEAKER_BOSS_R-0.1,x+SPEAKER_BOSS_R+0.1,
            s-SPEAKER_BOSS_R-0.1,s+SPEAKER_BOSS_R+0.1,
            SPEAKER_NUT_FRONT_N+0.05,SPEAKER_BOSS_BACK_N-0.05])
    for a in (0,90,180):
        c,s=math.cos(math.radians(a)),math.sin(math.radians(a))
        points=[(r*c-t*s,r*s+t*c) for r,t in [(50.8,-8.2),(57.1,-8.2),(57.1,8.2),(50.8,8.2)]]
        xy=[min(p[0] for p in points),max(p[0] for p in points),min(p[1] for p in points),max(p[1] for p in points)]
        add('locator_socket_'+str(a),'main_shell',xy+[16.7,26.01],cross={'kind':'slot','angle':a})
        tongue_points=[(r*c-t*s,r*s+t*c) for r,t in [(52.1,-4),(56.2,-4),(56.2,4),(52.1,4)]]
        tongue_xy=[min(p[0] for p in tongue_points),max(p[0] for p in tongue_points),
                   min(p[1] for p in tongue_points),max(p[1] for p in tongue_points)]
        add('locator_tongue_'+str(a),'rear_cover',tongue_xy+[23.1,29.4])
    for x in range(-33,34,6):
        add('grille_web_'+str(x),'rear_cover',[x-1.65,x+1.65,-11,11,48,110])
    add('bottom_ring','rear_cover',[-49,49,-18,68,0,0.51],'world')
    add('cable_tie_bridge','rear_cover',[17.9,28.1,TIE_FRONT_Y,TIE_BACK_Y,16,24.1],'world')
    top_z=FRONT_Z+SIN*OUTER_R-COS*(MOUTH_N+TOP_FLAT_DEPTH)
    add('top_flat','rear_cover',[-20,20,42,60,top_z-1.5,top_z+0.01],'world')
    add('outlet','rear_cover',[-11,11,40,150,17,31],'world')
    data={'tilt_deg':TILT_DEG,'front_z_mm':FRONT_Z,'frame_back_n_mm':FRAME_BACK_N,
          'frame_print_y_offset_mm':FRONT_Z*SIN,'features':features,
          'method':'关键区域取 STL 中层截面，与实际线宽扩展后的 G-code 墙线比较；不以整层存在挤出代替局部检查。'}
    with open(os.path.join(OUT,'print_features.json'),'w',encoding='utf-8') as f:
        json.dump(data,f,ensure_ascii=False,indent=2)


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
    # 下部侧后轮廓放缓外扩；保留底面和前侧包覆，减少落床时的过悬支撑。
    sections=[(0,48,42,25),(3,50.4,44.4,25),(10,55.8,49.8,18.8),(25,62,59,15),
              (45,64,65,18),(65,61,58,12),(85,57,51,6),(100,45,41,0),
              (115,23,23,0),(120,1,1,0)]
    envelope=Part.makeLoft([ellipse(*v) for v in sections],True,False).common(cyl(OUTER_R,MOUTH_N,110))
    inner=[(FLOOR_T,46,39.2,25),(10,51.4,45.4,18.8),(25,57.6,54.6,15),
           (45,61,62,18),(65,58,55,12),(85,54,48,6),(100,42,38,0),
           (112,20,20,0),(116,1,1,0)]
    above_floor=Part.makeBox(300,300,160,App.Vector(-150,-100,FLOOR_T))
    cavity=Part.makeLoft([ellipse(*v) for v in inner],True,False).common(cyl(INNER_R,MOUTH_N,110)).common(above_floor)
    cavity=cavity.fuse(box(-SPEAKER_W/2-0.5,SPEAKER_W/2+0.5,
                           -SPEAKER_H/2-0.5,SPEAKER_H/2+0.5,
                           MOUTH_N,SPEAKER_BACK_N+0.5)).removeSplitter()
    skin=envelope.cut(cavity)
    # 外圈全部交给连续后盖；承托架与后盖圆柱内壁留 0.5 mm。
    rear=skin
    ring=cyl(FRAME_R,13.2,FRAME_BACK_N).cut(cyl(51.9,13,27))
    ring=ring.cut(box(-SPEAKER_W/2-0.5,SPEAKER_W/2+0.5,
                      -SPEAKER_H/2-0.5,SPEAKER_H/2+0.5,SPEAKER_FRONT_N-0.2,27))
    ring=ring.cut(box(-60,60,-60,-46,13,27))  # 下端开口，让开连续后盖向底板的曲面过渡。
    main_parts=[ring]
    for x,s in SCREWS:
        r=math.hypot(x,s)
        main_parts.append(cyl(MODULE_BOSS_R,MODULE_MOUNT_FRONT_N,20.5,x,s))
        main_parts.append(local_rectangle(x,s,-1,54.1-r,-MODULE_RIB_W/2,MODULE_RIB_W/2,
                                          MODULE_MOUNT_FRONT_N,20.5))
    for x,s in BOLT_POINTS:
        main_parts.extend([radial_wedge(x,s,40,52.5,13.2,26,8),cyl(NUT_BOSS_R,NUT_BOSS_FRONT_N,26,x,s)])
    for a in (0,90,180):
        main_parts.append(locator(a,LOCATOR_BACK_INNER_R,FRAME_R,LOCATOR_BACK_WIDTH,16.8,FRAME_BACK_N).common(
            cyl(FRAME_R,16.8,FRAME_BACK_N)))
        # 后盖定位舌，台阶两肩与架背面相接，独立承担锁紧力。
        shelf=locator(a,52.0,56.3,16,26,29.5)
        # 从最低的背面开始斜撑，避免倾斜台阶的背缘留一条悬空薄楔。
        shelf_face=min(shelf.Faces,key=lambda f:abs(-(f.CenterOfMass-P).dot(N)-29.5))
        direction=App.Vector(math.cos(math.radians(a)),math.sin(math.radians(a)),0)
        ramp=down_support(shelf_face,direction,32 if a==90 else 7,envelope,above_floor)
        rear=rear.fuse(shelf).fuse(ramp).fuse(locator_lead(a))
    main_shell=fuse(main_parts).common(envelope)
    for x,s in SCREWS:
        main_shell=main_shell.cut(cyl(MODULE_HOLE_R,MODULE_MOUNT_FRONT_N-0.1,27,x,s))
        main_shell=main_shell.cut(cyl(MODULE_HEAD_R+MODULE_HEAD_CLEARANCE,MODULE_SEAT_N,27,x,s))
    for a in (0,90,180):
        main_shell=main_shell.cut(locator(a,53.1-FIT_SIDE_CLEARANCE,55.1,8+2*FIT_SIDE_CLEARANCE,23-FIT_TIP_CLEARANCE,26.1))
        # 落床槽口扩张，容纳首层象脚；承力槽背在导入口以上保持 1.8 mm。
        main_shell=main_shell.cut(locator_entry(a))
        main_shell=main_shell.cut(locator_roof(a))
    for x,s in BOLT_POINTS:
        main_shell=main_shell.cut(cyl(1.7,18,27,x,s))
        main_shell=main_shell.cut(hex_prism(x,s,NUT_FRONT_N,NUT_BACK_N,NUT_AF))
        # 从空腔内侧向下滑入螺母；后方留 2.4 mm 实体承压肩。
        main_shell=main_shell.cut(box(x-NUT_ENTRY_W/2,x+NUT_ENTRY_W/2,s,s+9,NUT_FRONT_N,NUT_BACK_N))
        roof=face([pt(x-NUT_ENTRY_W/2,s-3.6,NUT_FRONT_N),pt(x,s-3.6,NUT_ROOF_PEAK_N),
                   pt(x+NUT_ENTRY_W/2,s-3.6,NUT_FRONT_N)]).extrude(S*12.6)
        main_shell=main_shell.cut(roof)
    relief=cyl(FRAME_R,MOUTH_N,FRAME_BACK_N-ELEPHANT_RELIEF).fuse(
        Part.makeCone(FRAME_R,FRAME_R-ELEPHANT_RELIEF,ELEPHANT_RELIEF,pt(0,0,FRAME_BACK_N-ELEPHANT_RELIEF),-N))
    main_shell=main_shell.common(relief)
    main_shell=main_shell.removeSplitter()
    # 喇叭独立固定到后盖。圆耳承压面后方扩径，保证普通六角螺母袋的壁厚。
    for x,s in PINS:
        target_x=x
        x=-abs(x)  # 对称结构在同一侧完成布尔后镜像，避免相切圆柱的方向性布尔退化。
        seat=cyl(SPEAKER_EAR_R,SPEAKER_SEAT_N,SPEAKER_SEAT_N+0.1,x,s)
        seat=seat.fuse(Part.makeCone(SPEAKER_EAR_R,SPEAKER_BOSS_R,2.1,
                                   pt(x,s,SPEAKER_SEAT_N+0.1),-N))
        seat=seat.fuse(cyl(SPEAKER_BOSS_R,SPEAKER_SEAT_N+2.2,SPEAKER_BOSS_BACK_N,x,s))
        profile=Part.Face(Part.Wire([Part.makeCircle(SPEAKER_BOSS_R,
                              pt(x,s,SPEAKER_SEAT_N+2.2),-N)]))
        support=down_support(profile,App.Vector((1 if x>0 else -1)*COS,SIN,0),22,envelope,above_floor)
        # 筋从耳孔操作区绕出总外形侧边；不侵入未确认的箱体包络。
        keepout=box(-SPEAKER_W/2-0.3,SPEAKER_W/2+0.3,-100,100,
                    SPEAKER_FRONT_N-0.3,SPEAKER_BACK_N+0.3)
        support=support.cut(keepout)
        # 连接筋从座体背段接入，去除前缘与圆座相交产生的窄尖片。
        support=support.common(cyl(150,SPEAKER_BOSS_BACK_N-1.2,140))
        seat=seat.fuse(support)
        # 背面开口防转袋：先从后侧放普通螺母，再装喇叭；锁紧后轴向捕获。
        # 方形防转袋保留对边限位，避免六角尖顶在倾斜打印时形成微小尖孔。
        seat=seat.cut(box(x-3,x+3,s-3.4,s+3.4,SPEAKER_NUT_FRONT_N,SPEAKER_BACK_N+0.3))
        seat=seat.fuse(cyl(PIN_R,SPEAKER_SEAT_N-PIN_H+PIN_LEAD_H-0.05,SPEAKER_SEAT_N+0.1,x,s))
        seat=seat.fuse(Part.makeCone(PIN_R-0.4,PIN_R,PIN_LEAD_H,
                       pt(x,s,SPEAKER_SEAT_N-PIN_H),-N))
        seat=seat.cut(cyl(1.7,SPEAKER_SEAT_N-PIN_H-0.1,SPEAKER_BOSS_BACK_N+1,x,s))
        if target_x>0:
            seat=seat.mirror(App.Vector(),X)
        rear=rear.fuse(seat)
    for x,s in BOLT_POINTS:
        seat=cyl(5.5,29.5,BOLT_SEAT_N,x,s)
        profile=Part.Face(Part.Wire([Part.makeCircle(5.5,pt(x,s,29.5),-N)]))
        support=down_support(profile,App.Vector(0,1,0),20,envelope,above_floor)
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
    tie=fuse([Part.makeBox(3,TIE_BACK_Y-TIE_FRONT_Y,8,App.Vector(x,TIE_FRONT_Y,16)) for x in (18,25)]+
             [Part.makeBox(10,TIE_BACK_Y-TIE_FRONT_Y,2,App.Vector(18,TIE_FRONT_Y,22))]).common(envelope)
    rear=rear.fuse(tie)
    recess=Part.Face(ellipse(-1,43,37,25)).extrude(Z*1.6)
    rear=rear.cut(recess).removeSplitter()
    top_z=FRONT_Z+SIN*OUTER_R-COS*(MOUTH_N+TOP_FLAT_DEPTH)
    rear=rear.common(Part.makeBox(300,300,top_z+1,App.Vector(-150,-100,-1))).removeSplitter()
    # 顶部收平后，把与前口相交的薄楔整个退后，避免留下不足 1.2 mm 的唇边。
    rear=rear.cut(box(-20,20,0,60,MOUTH_N,MOUTH_N+TOP_MOUTH_RELIEF)).removeSplitter()
    tie_open=Part.makeBox(3.8,1.8,5.8,App.Vector(21.1,TIE_FRONT_Y+0.1,16.1))
    assert rear.common(tie_open).Volume<0.001,'扎带穿入口被壳壁堵塞'
    # 总外形参考包络不代表真实箱体。只确认四个中部圆耳；耳周操作区独立标注待试装。
    speaker=box(-SPEAKER_W/2,SPEAKER_W/2,-SPEAKER_H/2,SPEAKER_H/2,SPEAKER_FRONT_N,SPEAKER_BACK_N)
    for x,s in PINS:
        speaker=speaker.cut(cyl(SPEAKER_SERVICE_R,SPEAKER_FRONT_N-1,SPEAKER_BACK_N+1,x,s))
    ears=[]
    for x,s in PINS:
        ears.append(cyl(SPEAKER_EAR_R,SPEAKER_EAR_FRONT_N,SPEAKER_SEAT_N,x,s).cut(
            cyl(3,SPEAKER_EAR_FRONT_N-0.1,SPEAKER_SEAT_N+0.1,x,s)))
    speaker=fuse([speaker]+ears)
    shapes={'main_shell':main_shell,'rear_cover':rear}
    write_print_features()
    module_heads=[cyl(MODULE_HEAD_R,MODULE_SEAT_N,MODULE_SEAT_N+MODULE_HEAD_H,x,s) for x,s in SCREWS]
    module_shafts=[cyl(1.25,MODULE_SEAT_N-MODULE_SCREW_L,MODULE_SEAT_N,x,s) for x,s in SCREWS]
    module_engagement=MODULE_THREAD_ENTRY_N-(MODULE_SEAT_N-MODULE_SCREW_L)
    assert abs(MODULE_SEAT_N-MODULE_SCREW_L-MODULE_ORIGINAL_TIP_N)<0.001,'M2.5 螺丝尖端位置改变'
    module_bearing=[]
    for x,s in SCREWS:
        area=main_shell.common(cyl(MODULE_HEAD_R,MODULE_SEAT_N-0.02,MODULE_SEAT_N,x,s)).Volume/0.02
        assert area>=8,'M2.5 实际承压面积不足'
        module_bearing.append(area)
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
    collision=main_shell.common(rear)
    for solid in collision.Solids:
        c=solid.CenterOfMass-P
        print('两壳局部干涉',solid.Volume,(c.dot(X),c.dot(S),-c.dot(N)),flush=True)
    assert collision.Volume<0.02,'两壳干涉'
    # 用 0.02 mm 虚拟压入测量三处止挡的实际接触面积，不能只统计名义台阶。
    forward=rear.copy();forward.translate(N*0.02)
    stop_areas=[]
    for a in (0,90,180):
        area=main_shell.common(forward).common(locator(a,51.8,56.5,16,25.9,26.1)).Volume/0.02
        assert area>12,'止挡接触不足'
        stop_areas.append(area)
    washers=[]
    speaker_hardware=[]
    ear_contacts=[]
    speaker_nut_checks=[]
    for x,s in PINS:
        front=SPEAKER_EAR_FRONT_N-SPEAKER_WASHER_T
        washer=cyl(4.5,front,SPEAKER_EAR_FRONT_N,x,s).cut(cyl(1.7,front-0.1,SPEAKER_EAR_FRONT_N+0.1,x,s))
        shaft=cyl(1.5,front,front+SPEAKER_SCREW_L,x,s)
        head=cyl(2.85,front-3,front,x,s)
        nut=hex_prism(x,s,SPEAKER_NUT_FRONT_N,SPEAKER_NUT_FRONT_N+2.4,5.5).cut(
            cyl(1.5,SPEAKER_NUT_FRONT_N-0.1,SPEAKER_NUT_FRONT_N+2.5,x,s))
        washers.append(washer)
        speaker_hardware.extend([shaft,head,nut,washer])
        probe=cyl(4.5,SPEAKER_SEAT_N,SPEAKER_SEAT_N+0.02,x,s).cut(
            cyl(3,SPEAKER_SEAT_N-0.1,SPEAKER_SEAT_N+0.1,x,s))
        contact=rear.common(probe).Volume/0.02
        assert contact>=0.99*math.pi*(4.5**2-3**2),'喇叭圆耳承压面不足'
        ear_contacts.append(contact)
        for travel in (0,1,2,3.3,4):
            moved=nut.copy();moved.translate(-N*travel)
            print('喇叭螺母装入',x,s,travel,moved.common(rear).Volume,flush=True)
            assert moved.common(rear).Volume<0.02,'喇叭螺母背面装入路径'
        rotated=nut.copy()
        rotated.rotate(pt(x,s,SPEAKER_NUT_FRONT_N),-N,30)
        assert rotated.common(rear).Volume>0.05,'喇叭普通螺母袋不能防转'
        tool=cyl(2,SPEAKER_EAR_FRONT_N-18,front-3,x,s)
        assert tool.common(rear).Volume+tool.common(speaker).Volume<0.02,'喇叭螺丝工具通道'
        speaker_nut_checks.append(True)
    print('止挡/圆耳承压面积',stop_areas,ear_contacts,flush=True)
    assert speaker.common(wire).Volume<0.02,'线束碰音箱'
    for hardware in module_heads+module_shafts+m3_heads+m3_shafts+nuts+speaker_hardware:
        for name,shape in shapes.items():
            assert shape.common(hardware).Volume<0.02,name+'碰紧固件'
    assert all(h.common(speaker).Volume<0.02 for h in speaker_hardware),'喇叭参考耳碰紧固件'
    for x,s in SCREWS:
        assert main_shell.common(cyl(MODULE_HEAD_R+MODULE_HEAD_CLEARANCE,MODULE_SEAT_N,110,x,s)).Volume<0.02,'M2.5 头部装入/旋转路径'
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
        moving_speaker=speaker.copy();moving_speaker.translate(-N*travel)
        moving_hardware=Part.makeCompound(speaker_hardware);moving_hardware.translate(-N*travel)
        fixed=Part.makeCompound([main_shell]+module_heads)
        overlaps={'cover_to_frame':moved.common(fixed).Volume,
                  'speaker_to_frame':moving_speaker.common(fixed).Volume,
                  'speaker_hardware_to_frame':moving_hardware.common(fixed).Volume}
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
    assert max_radius<=OUTER_R+0.002,'打印件超出正面隐藏轮廓'
    for shape in shapes.values():
        for v in shape.tessellate(0.08)[0]:
            xx,ss=(v-P).dot(X),(v-P).dot(S)
            assert math.hypot(xx,ss)<=OUTER_R+0.002,'正面存在打印件外扩'
    assert rear.common(outlet).Volume<0.02,'出线孔不通'
    print('快速验证通过，导入完整模块',flush=True)
    source=Part.read(os.path.join(ROOT,'reference',MODEL))
    module=source.copy()
    module.Placement=App.Placement(P-N*3.75,App.Rotation(X,TILT_DEG)).multiply(module.Placement)
    # 根据孔位和轴向包络选择四颗被拆下的原螺丝，不能屏蔽支柱或保护板。
    removed=[]
    retained=[]
    for i,solid in enumerate(module.Solids):
        c=solid.CenterOfMass-P
        hit=any(math.hypot(c.dot(X)-x,c.dot(S)-s)<0.1 for x,s in SCREWS)
        ns=[-(v.Point-P).dot(N) for v in solid.Vertexes]
        if hit and abs(min(ns)-11.1)<0.02 and abs(max(ns)-15.1)<0.02 and solid.Volume<30:
            removed.append(i)
        else:retained.append(solid)
    assert len(removed)==4,'原厂待拆 M2.5 螺丝识别失败'
    module=Part.makeCompound(retained)
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
                       ('Module_M25_Heads_Reference',Part.makeCompound(module_heads)),
                       ('Module_M25_Shafts_Reference',Part.makeCompound(module_shafts)),('M3_Heads_Reference',Part.makeCompound(m3_heads)),
                       ('M3_Shafts_Reference',Part.makeCompound(m3_shafts)),('M3_Nuts_Reference',Part.makeCompound(nuts)),
                       ('Speaker_Washers_Reference',Part.makeCompound(washers)),
                       ('Speaker_Ears_Reference',Part.makeCompound(ears)),
                       ('Speaker_Hardware_Reference',Part.makeCompound(speaker_hardware)),
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
    for name,shape in [('module',cyl(MODULE_R,0,6)),('speaker',speaker),('washers',Part.makeCompound(washers)),
                       ('speaker_hardware',Part.makeCompound(speaker_hardware)),
                       ('section',rear.common(Part.makeBox(150,250,160,App.Vector(0,-100,0)))),
                       ('fasteners',Part.makeCompound(m3_heads+m3_shafts+nuts+module_heads+module_shafts))]:
        mesh_write(shape,os.path.join(CACHE,name+'.stl'))
    doc.recompute();configure_display(doc);doc.saveAs(os.path.join(OUT,'enclosure.FCStd'))
    # 同尺寸螺母袋与止口的局部试装件，归档目录不混入正式打印件。
    fit_dir=os.environ.get('P4_FIT_DIR',os.path.join(ROOT,'archive','fit_samples'));os.makedirs(fit_dir,exist_ok=True)
    sample=main_shell.common(box(12,31,-49,-28,19,30))
    mesh_write(sample,os.path.join(fit_dir,'nut_pocket.stl'),printing=True)
    for name,shape in [('locator_tongue',rear),('locator_socket',main_shell)]:
        sample=shape.common(box(51,58,-8,8,22,32))
        mesh_write(sample,os.path.join(fit_dir,name+'.stl'),printing=True)
    mesh_write(rear.common(box(38,58,10,27,SPEAKER_SEAT_N-2,SPEAKER_BOSS_BACK_N+2)),
               os.path.join(fit_dir,'speaker_mount.stl'),printing=True)
    x,s=SCREWS[-1]
    mesh_write(main_shell.common(local_rectangle(x,s,-6,15,-6,6,15,21)),os.path.join(fit_dir,'module_m25_mount.stl'),printing=True)
    gauge=box(-13,13,-6,6,0,2.4)
    for x,diameter in [(-7,3.4),(0,4.4),(7,6.0)]:
        gauge=gauge.cut(cyl(diameter/2,-0.1,2.5,x,0))
    mesh_write(gauge,os.path.join(fit_dir,'hole_clearance.stl'),printing=True)
    metrics={'module_model':MODEL,'module_source_solids':len(source.Solids),'tilt_deg':40,
             'parts':checks,'step_solids':2,'front_projection_radius_mm':max_radius,
             'front_occlusion_margin_mm':MODULE_R-max_radius,'bottom_ring_passed':ring_passed,
             'bottom_ring_width_nominal_mm':5,'bottom_plate_min_mm':2,
             'seam_clearance_mm':FIT_TIP_CLEARANCE,'locator_engagement_mm':3,'locator_side_clearance_mm':FIT_SIDE_CLEARANCE,
             'axial_stop_pads':3,
             'axial_stop_contact_areas_mm2':stop_areas,'speaker_ear_bearing_areas_mm2':ear_contacts,
             'rear_screw':'2 × M3×16 内六角圆柱头，M3 六角螺母对边 5.5、厚 2.4',
             'nut_retaining_shoulder_mm':2.4,
             'module_screw':'4 × M2.5×6 内六角圆柱头，头径≤4.7 mm、头高≤2.5 mm',
             'module_mount_points_mm':SCREWS,'module_mount_thickness_mm':MODULE_SEAT_N-MODULE_MOUNT_FRONT_N,
             'module_engagement_mm':module_engagement,'module_tip_n_mm':MODULE_SEAT_N-MODULE_SCREW_L,
             'module_original_tip_n_mm':MODULE_ORIGINAL_TIP_N,'removed_original_screw_indices':removed,
             'module_retained_solids':len(retained),'module_head_bearing_areas_mm2':module_bearing,
             'module_head_clearance_diameter_mm':2*(MODULE_HEAD_R+MODULE_HEAD_CLEARANCE),
             'front_hidden_required':True,
             'speaker_corner_clearance_wall_mm':OUTER_R-math.hypot(SPEAKER_W/2+0.5,SPEAKER_H/2+0.5),
             'locator_socket_radial_wall_mm':None,
             'speaker_dimensions_mm':[SPEAKER_W,SPEAKER_H,SPEAKER_T],'speaker_hole_pitch_mm':[2*HOLE_X,2*HOLE_S],
             'speaker_pin_diameter_mm':2*PIN_R,'speaker_pin_height_mm':PIN_H,
             'speaker_ear_thickness_mm':SPEAKER_EAR_T,'speaker_ear_outer_diameter_mm':2*SPEAKER_EAR_R,
             'speaker_hole_diameter_mm':6,'speaker_pin_lead_mm':PIN_LEAD_H,
             'speaker_fasteners':'4 × M3×8，垫片外径 9、内径 3.4、厚 0.5；普通螺母对边 5.5、厚 2.4',
             'speaker_nut_insertion_checks':speaker_nut_checks,
             'speaker_nut_pocket_mm':[6.0,6.8],
             'speaker_nut_pocket_wall_min_nominal_mm':SPEAKER_BOSS_R-math.hypot(3,3.4),
             'speaker_screw_thread_engagement_mm':2.4,
             'speaker_service_radius_mm':SPEAKER_SERVICE_R,
             'frame_radial_clearance_mm':INNER_R-FRAME_R,
             'carrier_print_bed':'后侧框架平面朝下','continuous_cover':True,
             'fdm_design':{'nozzle_mm':0.4,'materials':['PLA','PETG'],'minimum_wall_target_mm':1.2,
                 'minimum_load_wall_target_mm':1.6,'module_mount_closed_holes':True,'nut_pocket_across_flats_mm':NUT_AF,
                 'nut_pocket_depth_mm':NUT_BACK_N-NUT_FRONT_N,'nut_entry_width_mm':NUT_ENTRY_W,
                 'entry_lead_mm':FIT_LEAD,'bed_edge_relief_mm':ELEPHANT_RELIEF,'rear_flat_top_z_mm':top_z},
             'carrier_reinforcement':{'module_boss_radius_mm':MODULE_BOSS_R,'module_rib_width_mm':MODULE_RIB_W,
                 'locator_back_inner_radius_mm':LOCATOR_BACK_INNER_R,'locator_back_width_mm':LOCATOR_BACK_WIDTH},
             'rear_outlet_mm':[20,12],'outlet_corner_radius_mm':3,
             'nut_insertion_travel_mm':[0,1,2,4,6,8,10],
             'cable_reference_diameter_mm':3.5,'cable_bend_radius_verified':False,
             'bottom_ring_width_samples':288,
             'assembly_travel':travel_checks,'cavity_cm3':cavity.Volume/1000,
             'estimated_module_mass_g':220,'estimated_speaker_mass_g':100,
             'estimated_total_mass_g':mass,'estimated_tip_angle_deg':tip,
             'speaker_actual_ear_thickness_mm':SPEAKER_EAR_T,
             'speaker_actual_ear_center_offset_mm':SPEAKER_EAR_CENTER_OFFSET,
             'speaker_mount_location':'后盖独立四支座，拆盖时喇叭随盖移动',
             'speaker_body_shape_verified':False,
             'speaker_mount_status':'中部圆耳及紧固件按确认尺寸建模；总外形扣除耳周安装操作区作为条件包络，真实箱体耳根形状及工具空间需局部试装。',
             'microphone_hole_verified':False,'physical_fit_verified':False}
    with open(os.path.join(OUT,'validation.json'),'w',encoding='utf-8') as f:
        json.dump(metrics,f,ensure_ascii=False,indent=2)
    print('全部导出完成',OUT,flush=True)


try:
    main()
except Exception:
    traceback.print_exc()
    raise
