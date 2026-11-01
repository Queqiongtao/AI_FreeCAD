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
SPEAKER_FRONT_N = 22.5
SPEAKER_BACK_N = SPEAKER_FRONT_N + SPEAKER_T
SPEAKER_CLEARANCE = 0.5
SPEAKER_TAPE_T = 1.0
SPEAKER_PAD_N = SPEAKER_BACK_N + SPEAKER_TAPE_T
SPEAKER_LONG_TAPE_W = 2.0
SPEAKER_SHORT_TAPE_W = 3.0
SPEAKER_SHORT_INSET = 5.0
SPEAKER_LONG_TAPE_SPAN = 76.0
SPEAKER_SHORT_TAPE_LENGTH = 24.0
SPEAKER_TAPE_RELEASE_GAP = 8.0
SPEAKER_LONG_EDGE_MARGIN = 0.3
SPEAKER_FACE_CLEARANCE = 2.0
SPEAKER_PAD_MIN_T = 2.0
# 原承托架避让位置固定，贴胶姿态微调不改变已打印承托架。
FRAME_SPEAKER_RELIEF_FRONT_N = 21.8
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
LOCK_INSERT_LENGTH = 3.0
LOCK_INSERT_OD = 4.0
LOCK_INSERT_BORE = 3.8  # 用户指定直孔，不增加直径补偿。
LOCK_INSERT_DEPTH = 3.4
LOCK_INSERT_CHAMFER = 0.3
LOCK_INSERT_BACK_N = 26.0
LOCK_BOSS_R = 5.4
LOCK_BOSS_FRONT_N = 16.1
LOCK_TIP_RELIEF_FRONT_N = 18.0
LOCK_HEAD_SEAT_N = 35.0
LOCK_SCREW_LENGTH = 16.0
TOP_FLAT_DEPTH = 1.6
TOP_MOUTH_RELIEF = 0.8
TIE_FRONT_Y = 56.0
TIE_BACK_Y = 78.0
TIE_CHANNEL_DEPTH = 8.0
TIE_BASE_Z = 40.0
# Type-C 直插口：沿板上接口的局部 +s 方向，仅切后盖。
USB_ACCESS_X = -12.4
USB_ACCESS_N = 12.0
USB_ACCESS_START_S = 49.2  # 从挂钩入口外侧开始，只切外壁，不削内部承力翼。
USB_ACCESS_END_S = 124.2
USB_ACCESS_WIDTH = 20.0
USB_ACCESS_HEIGHT = 14.0
USB_ACCESS_RADIUS = 2.0
USB_ACCESS_CHAMFER = 0.5
FOOT_RX = 48.0
FOOT_RY = 42.0
FOOT_CY = 25.0
# P4 前下侧壁拾音孔，位置采用装配世界坐标，z 为离桌高度。
MIC_HOLE_DIAMETER = 2.0
MIC_HOLE_GROUP_X = 30.0
MIC_HOLE_BASE_Z = 6.0
MIC_HOLE_PITCH = 4.0
MIC_HOLE_ROWS = 2
MIC_HOLE_COLUMNS = 3
MIC_HOLE_MIN_WEB = 1.6
MIC_HOLE_END_MARGIN = 0.3
# 后背圆孔出音区；使用世界坐标，避免沿屏幕法线钻向底板。
GRILLE_HOLE_DIAMETER = 3.2
GRILLE_PITCH = 5.6
GRILLE_ROWS = 3
GRILLE_COLUMNS = 15
GRILLE_BASE_S = 7.2
# 左右各9孔，中央不钻孔，避开底板上方的薄壁区域。
GRILLE_ROW_MIN_X = (39.2,33.6,11.2)
GRILLE_END_MARGIN = 0.3
ANGLE = math.radians(TILT_DEG)
SIN, COS = math.sin(ANGLE), math.cos(ANGLE)
X, Z = App.Vector(1, 0, 0), App.Vector(0, 0, 1)
N = App.Vector(0, -SIN, COS)
S = App.Vector(0, COS, SIN)
P = App.Vector(0, 0, FRONT_Z)
SCREWS = [(39.25,-10.0),(39.25,17.0),(-39.25,17.0),(-39.25,-17.0)]


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
        elif obj.Name=='Speaker_Radiating_Faces_Reference':
            obj.ViewObject.ShapeColor=(0.12,0.14,0.15)
        elif obj.Name=='Speaker_Tape_Reference':
            obj.ViewObject.ShapeColor=(0.88,0.66,0.28)
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
HOOK_ANGLES = (70.0,110.0)
HOOK_RADIUS = 49.5
HOOK_AXIS_S = HOOK_RADIUS*math.sin(math.radians(HOOK_ANGLES[0]))
HOOK_AXIS_N = 24.0
HOOK_WIDTH = 10.0
HOOK_ROOT_T = 3.0
HOOK_PIN_R = 2.0
HOOK_CLEARANCE = 0.30
HOOK_OPEN_ANGLE = 18.0


def upper_hook_shape(x):
    """下开口刚性钩，圆弧导槽绕前口上缘退出，不靠弹片变形。"""
    center=pt(x-HOOK_WIDTH/2,HOOK_AXIS_S,HOOK_AXIS_N)
    inner=HOOK_PIN_R+HOOK_CLEARANCE;outer=inner+HOOK_ROOT_T
    tube=Part.makeCylinder(outer,HOOK_WIDTH,center,X).cut(
        Part.makeCylinder(inner,HOOK_WIDTH,center,X))
    bottom=tube.common(box(x-5,x+5,HOOK_AXIS_S,HOOK_AXIS_S+outer+.1,18,31))
    wings=fuse([box(x-5,x+5,HOOK_AXIS_S-2,HOOK_AXIS_S,HOOK_AXIS_N-outer,HOOK_AXIS_N-inner),
                box(x-5,x+5,HOOK_AXIS_S-2,HOOK_AXIS_S,HOOK_AXIS_N+inner,HOOK_AXIS_N+outer)])
    root=box(x-5,x+5,HOOK_AXIS_S,56,HOOK_AXIS_N+inner,HOOK_AXIS_N+outer)
    back=box(x-8.3,x+8.3,HOOK_AXIS_S-5,HOOK_AXIS_S-.5,27,30.3)
    stops=fuse([box(x+sign*6.8-1.5,x+sign*6.8+1.5,
                    HOOK_AXIS_S-5,HOOK_AXIS_S-1,26,29.5) for sign in (-1,1)])
    # 圆弧导槽会削薄入口前翼，向前补一条渐变筋，保留不少于 2 mm 的实体。
    front_rib=face([pt(x-5,HOOK_AXIS_S-2,17.3),pt(x-5,HOOK_AXIS_S+2,18.7),
                    pt(x-5,HOOK_AXIS_S+2,21.7),pt(x-5,HOOK_AXIS_S-2,21.7)]).extrude(X*10)
    hook=fuse([bottom,wings,root,back,stops,front_rib]).common(cyl(OUTER_R,6.3,110))
    # 横销相对后盖沿圆弧退出；用精确圆弧槽保证整个转动过程的间隙。
    ds=HOOK_AXIS_S-OUTER_R;dn=HOOK_AXIS_N-MOUTH_N
    radius=math.hypot(ds,dn);start=math.atan2(dn,ds);end=start+math.radians(HOOK_OPEN_ANGLE)
    def q(r,a):return pt(x-5.1,OUTER_R+r*math.cos(a),MOUTH_N+r*math.sin(a))
    ri=radius-inner;ro=radius+inner;middle=(start+end)/2
    edges=[Part.Arc(q(ro,start),q(ro,middle),q(ro,end)).toShape(),
           Part.makeLine(q(ro,end),q(ri,end)),
           Part.Arc(q(ri,end),q(ri,middle),q(ri,start)).toShape(),
           Part.makeLine(q(ri,start),q(ro,start))]
    slot=Part.Face(Part.Wire(edges)).extrude(X*10.2)
    for a in (start,end):slot=slot.fuse(Part.makeCylinder(inner,10.2,q(radius,a),X))
    return hook.cut(slot)


def hook_pose(shape,angle=0,release=0,pull=0):
    moved=shape.copy()
    moved.rotate(pt(0,OUTER_R,MOUTH_N),X,angle)
    a=math.radians(angle)
    moved.translate(-(S*math.cos(a)+N*math.sin(a))*release-N*pull)
    return moved


def add_upper_hooks(frame,rear):
    """将框架与后盖改为上缘双钩配合，移除旧直插舌。"""
    # 原直插舌和内侧止挡会妨碍转动，改由两钩下方止挡承压。
    rear=rear.cut(locator(90,51.5,54.7,16.6,22.9,29.6))
    for a in (0,180):
        rear=rear.cut(locator(a,51.5,54.7,16.6,22.9,29.6))
    # 后圈缩短，给整圈前口翻开时让路；模块安装筋和下侧螺母座保留。
    frame=frame.cut(cyl(60,17,27).cut(cyl(51.5,16.9,27.1)))
    hooks=[];pins=[]
    for angle in HOOK_ANGLES:
        x=HOOK_RADIUS*math.cos(math.radians(angle))
        hook=upper_hook_shape(x)
        pocket=box(x-5.3,x+5.3,HOOK_AXIS_S-6.3,60,18.4,31)
        frame=frame.cut(pocket)
        posts=fuse([box(x+sign*6.8-1.5,x+sign*6.8+1.5,
                       HOOK_AXIS_S-5,56,16.8,26) for sign in (-1,1)]+
                   [box(x+sign*6.8-1.5,x+sign*6.8+1.5,49,56,13.2,17)
                    for sign in (-1,1)]).common(cyl(FRAME_R,13,26))
        pin=Part.makeCylinder(HOOK_PIN_R,16.6,pt(x-8.3,HOOK_AXIS_S,HOOK_AXIS_N),X)
        frame=frame.fuse(posts).fuse(pin)
        rear=rear.fuse(hook)
        hooks.append(hook);pins.append(pin)
    return finish_hook_frame(frame),rear.removeSplitter(),hooks,pins


def finish_hook_frame(frame):
    """消除销底与落床面的相切退化；0.1 mm 削平仍能在首层切出销体。"""
    for angle in HOOK_ANGLES:
        x=HOOK_RADIUS*math.cos(math.radians(angle))
        frame=frame.cut(box(x-5.3,x+5.3,HOOK_AXIS_S-2.1,HOOK_AXIS_S+2.1,25.9,26.1))
    result=frame.removeSplitter()
    assert result.isValid() and len(result.Solids)==1,'横销落床面整理失败'
    return result


def radial_wedge(x, s, r0, r1, front_outer, back, width):
    """沿半径向内延伸的 45°承托筋；实际打印姿态由网格导出确定。"""
    a = math.atan2(s, x)
    u, v = X*math.cos(a)+S*math.sin(a), -X*math.sin(a)+S*math.cos(a)
    def q(r,n):
        return pt(0,0,n)+u*r-v*width/2
    front_inner = front_outer+r1-r0
    return face([q(r0,front_inner),q(r1,front_outer),q(r1,back),q(r0,back)]).extrude(v*width)


def verify_hook_motion(frame,rear,speaker,hardware,module,module_heads):
    """精确扫掠覆盖连续行程，退化面以中点距离和最大位移界证明。"""
    pivot=pt(0,OUTER_R,MOUTH_N)
    moving=rear.copy()
    # 四个承压垫闭合时允许接触；其整个运动的 n 下界单独解析验证。
    for a in HOOK_ANGLES:
        x=HOOK_RADIUS*math.cos(math.radians(a))
        for sign in (-1,1):
            moving=moving.cut(box(x+sign*6.8-1.5,x+sign*6.8+1.5,
                                  HOOK_AXIS_S-5,HOOK_AXIS_S-1,26,29.5))
    assert (OUTER_R-(HOOK_AXIS_S-1))*math.cos(math.radians(HOOK_OPEN_ANGLE)) > \
        (29.5-MOUTH_N)*math.sin(math.radians(HOOK_OPEN_ANGLE)), '止挡翻开时未离开承压面'
    moving=Part.makeCompound([moving,speaker,Part.makeCompound(hardware)])
    # 曲面包围盒会过估边界，直接用越界半空间的精确交集证明。
    assert moving.common(box(-150,150,OUTER_R+.001,200,-100,200)).Volume<.00001,'转轴上方有实体'
    assert moving.common(box(-150,150,-200,200,-100,MOUTH_N-.001)).Volume<.00001,'前口前方有实体'
    # n≥28 的部分在 18°时仍有 n≥26.93，整个转动/后拉过程都离开固定件 n≤26。
    assert MOUTH_N+(28-MOUTH_N)*math.cos(math.radians(HOOK_OPEN_ANGLE))>26.9
    moving=moving.common(box(-150,150,-150,150,MOUTH_N-.001,28))
    # 被省略的小元件全部受半径 53 mm 的实心包络保护，绝不按名称屏蔽实体。
    candidates=[];front_count=0;inner_count=0;module_max_n=0
    for solid in module.Solids:
        local=solid.copy();local.translate(-P);local.rotate(App.Vector(),X,-TILT_DEG)
        b=local.BoundBox;module_max_n=max(module_max_n,-b.ZMin)
        if -b.ZMin<MOUTH_N-.0001:
            front_count+=1;continue
        radius=max(math.hypot(x,s) for x in (b.XMin,b.XMax) for s in (b.YMin,b.YMax))
        if radius<53:
            inner_count+=1;continue
        candidates.append(solid.common(box(-100,100,-100,100,MOUTH_N-.001,26)))
    assert module_max_n<26 and all(-(v.Point-P).dot(N)<=26.001 for v in frame.Vertexes)
    fixed=Part.makeCompound([frame]+module_heads+candidates+[cyl(53,MOUTH_N,module_max_n)])
    print('连续装拆检查：精确模块候选',len(candidates),'前方/内部包络',front_count,inner_count,flush=True)
    certified=[];samples=0
    assert moving.common(fixed).Volume<.00001,'连续路径起点重叠'
    far=App.Vector(1000,1000,1000)
    def record(phase,index,lo,hi,method):
        certified.append({'phase':phase,'face':index,'from':lo,'to':hi,'method':method})
        if len(certified)%25==0:print('连续装拆包络已证明',len(certified),flush=True)
    def interval(face,index,lo,hi,rotation,depth=0):
        nonlocal samples
        phase='rotate' if rotation else 'pull'
        beginning=hook_pose(face,lo if rotation else HOOK_OPEN_ANGLE,0,0 if rotation else lo)
        swept=beginning.revolve(pivot,X,hi-lo) if rotation else beginning.extrude(-N*(hi-lo))
        # 面的精确旋转或拉伸扫掠覆盖连续边界；外向须修正，不能误用无限补集。
        if swept.isValid() and abs(swept.Volume)>1e-5:
            if swept.isInside(far,.000001,False):swept.reverse()
            assert not swept.isInside(far,.000001,False),'扫掠体外向异常'
            intersection=swept.common(fixed)
            if intersection.Volume<.000001 and intersection.Area<.000001 and intersection.Length<.000001:
                record(phase,index,lo,hi,'exact_boundary_sweep');return
        # 退化扫掠或布尔未能证明无交集时，再用该面的严格连续距离界证明。
        middle=(lo+hi)/2
        pose=hook_pose(face,middle if rotation else HOOK_OPEN_ANGLE,0,0 if rotation else middle)
        b=face.BoundBox
        radius=max((App.Vector(x,y,z)-pivot).Length for x in (b.XMin,b.XMax)
                   for y in (b.YMin,b.YMax) for z in (b.ZMin,b.ZMax))
        bound=2*radius*math.sin(math.radians(hi-lo)/4) if rotation else (hi-lo)/2
        distance=pose.distToShape(fixed)[0];samples+=1
        if distance>bound+.00001:
            record(phase,index,lo,hi,'face_distance_bound');return
        assert depth<18,'连续装拆包络碰撞或净距不足：'+str((index,lo,hi))
        middle=(lo+hi)/2
        interval(face,index,lo,middle,rotation,depth+1)
        interval(face,index,middle,hi,rotation,depth+1)
    for index,face in enumerate(moving.Faces):
        interval(face,index,0,HOOK_OPEN_ANGLE,True)
        interval(face,index,0,64,False)
    retention=[]
    for a in HOOK_ANGLES:
        x=HOOK_RADIUS*math.cos(math.radians(a))
        pin=Part.makeCylinder(HOOK_PIN_R,16.6,pt(x-8.3,HOOK_AXIS_S,HOOK_AXIS_N),X)
        pin=pin.common(box(x-8.4,x+8.4,HOOK_AXIS_S-2.1,HOOK_AXIS_S+2.1,21.9,25.9))
        volumes=[hook_pose(rear,0,0,t).common(pin).Volume for t in (1,2)]
        assert min(volumes)>1,'上侧未形成刚性防脱'
        retention.append(volumes)
    return {'continuous_path_certified':True,'angle_deg':HOOK_OPEN_ANGLE,'pull_mm':64,
            'intervals':certified,'distance_evaluations':samples,'retention_overlap_at_1_2_mm':retention,
            'module_exact_candidates':len(candidates),'module_front_envelope_count':front_count,
            'module_inner_envelope_count':inner_count,'physical_fit_verified':False,
            'method':'逐面精确旋转/平移扫掠；切向退化面采用中点距离和最大位移界；接触垫单调离开承压面。'}


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


def write_print_features(microphone=None,grille=None):
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
        add('heat_insert_boss_'+str(i),'main_shell',[x-5.5,x+5.5,s-5.5,s+5.5,
            LOCK_BOSS_FRONT_N+.05,LOCK_INSERT_BACK_N-.05])
        add('heat_insert_wall_'+str(i),'main_shell',[x-5.3,x+5.3,s-5.3,s+5.3,
            LOCK_INSERT_BACK_N-LOCK_INSERT_DEPTH+.05,LOCK_INSERT_BACK_N-LOCK_INSERT_CHAMFER-.05])
        # 锁紧承压座止于 n=35；后方大头孔和斜撑的交线另由全局承托检查覆盖。
        add('m3_seat_'+str(i),'rear_cover',[x-5.7,x+5.7,s-5.7,s+5.7,29.55,34.95])
    for name,x0,x1,s0,s1 in speaker_pad_rectangles():
        add(name,'rear_cover',[x0,x1,s0,s1,SPEAKER_PAD_N+.05,SPEAKER_PAD_N+SPEAKER_PAD_MIN_T-.05])
    for i,a in enumerate(HOOK_ANGLES):
        x=HOOK_RADIUS*math.cos(math.radians(a))
        add('upper_hook_'+str(i),'rear_cover',[x-5,x+5,HOOK_AXIS_S-2,HOOK_AXIS_S+5.3,17.3,29.3])
        add('retaining_tip_'+str(i),'rear_cover',[x-4.9,x+4.9,HOOK_AXIS_S-1.9,HOOK_AXIS_S-.1,17.4,21.6])
        add('hook_root_'+str(i),'rear_cover',[x-5,x+5,HOOK_AXIS_S,54,26.3,29.3])
        add('cross_pin_'+str(i),'main_shell',[x-5,x+5,HOOK_AXIS_S-2,HOOK_AXIS_S+2,22,26])
        for sign in (-1,1):
            add('pin_post_'+str(i)+'_'+str(sign),'main_shell',
                [x+sign*6.8-1.5,x+sign*6.8+1.5,HOOK_AXIS_S-5,53,13.2,26])
    for index,hole in enumerate((grille or {}).get('holes',[])):
        b=hole['bounds_world_mm']
        add('grille_hole_'+str(index),'rear_cover',[b[0]-.5,b[1]+.5,b[2]-.5,b[3]+.5,b[4]-.5,b[5]+.5],'world')
    add('bottom_ring','rear_cover',[-49,49,-18,68,0,0.51],'world')
    add('cable_tie_bridge','rear_cover',[17.9,28.1,TIE_FRONT_Y,TIE_BACK_Y,TIE_BASE_Z,TIE_BASE_Z+8.1],'world')
    top_z=FRONT_Z+SIN*OUTER_R-COS*(MOUTH_N+TOP_FLAT_DEPTH)
    add('top_flat','rear_cover',[-20,20,42,60,top_z-1.5,top_z+0.01],'world')
    add('outlet','rear_cover',[-11,11,40,150,17,31],'world')
    add('usb_access_rim','rear_cover',[USB_ACCESS_X-USB_ACCESS_WIDTH/2-2,
        USB_ACCESS_X+USB_ACCESS_WIDTH/2+2,48,60,MOUTH_N,USB_ACCESS_N+USB_ACCESS_HEIGHT/2+2])
    for index,hole in enumerate((microphone or {}).get('holes',[])):
        x,z=hole['center_x_z_mm']
        add('microphone_'+str(index),'rear_cover',[x-2.6,x+2.6,
            hole['front_y_mm']-.1,hole['cavity_y_mm']+.1,z-1.8,z+1.8],'world')
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


def usb_access_tool():
    """圆角矩形插拔通道；宽/厚在接口横截面量取，不按世界水平投影。"""
    x0,x1=USB_ACCESS_X-USB_ACCESS_WIDTH/2,USB_ACCESS_X+USB_ACCESS_WIDTH/2
    n0,n1=USB_ACCESS_N-USB_ACCESS_HEIGHT/2,USB_ACCESS_N+USB_ACCESS_HEIGHT/2
    r=USB_ACCESS_RADIUS
    pieces=[box(x0+r,x1-r,USB_ACCESS_START_S,USB_ACCESS_END_S,n0,n1),
            box(x0,x1,USB_ACCESS_START_S,USB_ACCESS_END_S,n0+r,n1-r)]
    pieces.extend(Part.makeCylinder(r,USB_ACCESS_END_S-USB_ACCESS_START_S,
        pt(x,USB_ACCESS_START_S,n),S) for x in (x0+r,x1-r) for n in (n0+r,n1-r))
    return fuse(pieces)


def add_usb_access(rear):
    """只给后盖开口；选圆柱外壁上的新孔缘做入口导角。"""
    original=rear.copy(True)
    tool=usb_access_tool()
    removed=rear.common(tool).Volume
    assert removed>1,'Type-C通道未切到后盖'
    rear=rear.cut(tool).removeSplitter()
    edges=[]
    for edge in rear.Edges:
        p=edge.valueAt((edge.FirstParameter+edge.LastParameter)/2)
        q=p-P;x=q.dot(X);s=q.dot(S);n=-q.dot(N)
        if (abs(math.hypot(x,s)-OUTER_R)<.001
            and abs(x-USB_ACCESS_X)<=USB_ACCESS_WIDTH/2+.001
            and abs(n-USB_ACCESS_N)<=USB_ACCESS_HEIGHT/2+.001
            and tool.distToShape(Part.Vertex(p))[0]<.001):
            edges.append(edge)
    assert edges,'未识别Type-C外侧孔缘'
    rear=rear.makeChamfer(USB_ACCESS_CHAMFER,edges).removeSplitter()
    assert rear.isValid() and len(rear.Solids)==1,'Type-C开孔后后盖实体无效'
    assert rear.common(tool).Volume<.001,'Type-C后盖通道未贯通'
    removed_shape=original.cut(rear)
    internal_removed=removed_shape.common(cyl(INNER_R-.01,MOUTH_N-.1,35)).Volume
    assert internal_removed<.001,'Type-C开孔削到壳壁内侧的承力结构'
    return rear,{'clear_width_mm':USB_ACCESS_WIDTH,'clear_height_mm':USB_ACCESS_HEIGHT,
        'corner_radius_mm':USB_ACCESS_RADIUS,'entry_chamfer_mm':USB_ACCESS_CHAMFER,
        'center_x_n_mm':[USB_ACCESS_X,USB_ACCESS_N],'axis_world':list(S),
        'start_s_mm':USB_ACCESS_START_S,'end_s_mm':USB_ACCESS_END_S,
        'removed_before_chamfer_mm3':removed,'chamfer_edge_count':len(edges),
        'internal_structure_removed_mm3':internal_removed,
        'rear_cover_channel_clear':True,'carrier_modified':False,
        'full_plug_path_verified':False,
        'carrier_fit_basis':'用户实物确认承托架不挡USB线；保守插头扫掠与架存在模型交叠，不作为整条插头通道零干涉证明。'}


def acoustic_samples(rear,original_wall,holes,radius,prefix,margin):
    """孔边采样必须在本体内，孔芯按开孔前壳壁分类，供实际切片独立复核。"""
    witnesses={};air=[]
    for index,hole in enumerate(holes):
        x,z=hole['center_x_z_mm'];front,back=hole['wall_y_mm']
        # 所有采样点都严格落在裁剪盒内部，精确交集不改变点的内外归属。
        # 避免每个采样点都对包含全部声孔的完整 BRep 重建分类器。
        clip=Part.makeBox(2*(radius+1),back-front+2*(margin+1),2*(radius+1),
            App.Vector(x-radius-1,front-margin-1,z-radius-1))
        local_rear=rear.common(clip)
        local_original=original_wall.common(clip)
        shoulders=[]
        for layer in range(int((z-radius)/.2)+1,int((z+radius)/.2)+2):
            height=round(layer*.2,3);sample_z=height-.1;delta=sample_z-z
            if abs(delta)>.7*radius:continue
            for fraction in (.25,.5,.75):
                y=front+(back-front)*fraction
                for side in (-1,1):
                    point=App.Vector(x+side*(math.sqrt(radius**2-delta**2)+.4),y,sample_z)
                    if local_rear.isInside(point,.001,False):
                        shoulders.append({'layer_z_mm':height,'point_mm':list(point)})
            if abs(delta)<.3:
                count=int((back-front)/.4)+1
                for i in range(count+1):
                    y=front-margin+i*(back-front+2*margin)/count
                    for offset in (-.4,0,.4):
                        point=App.Vector(x+offset,y,sample_z)
                        air.append({'hole':index,'layer_z_mm':height,'point_mm':list(point),
                            'inside_original_wall':local_original.isInside(point,.001,False)})
        assert len(shoulders)>=12,'孔周边实体采样不足：'+prefix+str(index)
        witnesses[prefix+str(index)]=shoulders
        if (index+1)%13==0 or index+1==len(holes):
            print('声孔实体/孔芯采样',prefix,index+1,'/',len(holes),flush=True)
    return witnesses,air


def speaker_pad_rectangles():
    """长边中间留8 mm拆胶入口；短边从总长端部内退5 mm后向内贴胶。"""
    pads=[]
    for sign in (-1,1):
        outer=SPEAKER_H/2-SPEAKER_LONG_EDGE_MARGIN
        s0,s1=(outer-SPEAKER_LONG_TAPE_W,outer) if sign>0 else (-outer,-outer+SPEAKER_LONG_TAPE_W)
        half=SPEAKER_LONG_TAPE_SPAN/2;gap=SPEAKER_TAPE_RELEASE_GAP/2
        for index,(x0,x1) in enumerate(((-half,-gap),(gap,half))):
            pads.append(('speaker_long_pad_'+str(sign)+'_'+str(index),x0,x1,s0,s1))
        edge=SPEAKER_W/2-SPEAKER_SHORT_INSET
        x0,x1=(edge-SPEAKER_SHORT_TAPE_W,edge) if sign>0 else (-edge,-edge+SPEAKER_SHORT_TAPE_W)
        pads.append(('speaker_short_pad_'+str(sign),x0,x1,-SPEAKER_SHORT_TAPE_LENGTH/2,SPEAKER_SHORT_TAPE_LENGTH/2))
    return pads


def speaker_tape_mount(rear,envelope,above_floor):
    """平面胶台沿后下方向接入壳体，中央留完整出声空间，不占四耳位置。"""
    pads=[box(x0,x1,s0,s1,SPEAKER_PAD_N,115).common(envelope).common(above_floor)
          for _,x0,x1,s0,s1 in speaker_pad_rectangles()]
    rear=rear.fuse(Part.makeCompound(pads)).removeSplitter()
    tapes=[box(x0,x1,s0,s1,SPEAKER_BACK_N,SPEAKER_PAD_N)
           for _,x0,x1,s0,s1 in speaker_pad_rectangles()]
    return rear,tapes


def grille_samples(rear,original,holes):
    """斜孔逐水平层检查孔芯及四侧孔边；按实际轴线求水平椭圆截面。"""
    witnesses={};air=[];radius=GRILLE_HOLE_DIAMETER/2
    for index,hole in enumerate(holes):
        x,s=hole['center_x_s_mm'];n0,n1=hole['wall_n_mm']
        b=hole['bounds_world_mm']
        clip=Part.makeBox(b[1]-b[0]+3,b[3]-b[2]+3,b[5]-b[4]+3,
                          App.Vector(b[0]-1.5,b[2]-1.5,b[4]-1.5))
        wall=original.common(clip);result=rear.common(clip);points=[]
        for layer in range(max(1,math.floor(b[4]/.2)),math.ceil(b[5]/.2)+2):
            z=round(layer*.2,3);height=z-.1;n=(FRONT_Z+s*SIN-height)/COS
            y=s*COS+n*SIN
            for dx,dy in ((-radius-.4,0),(radius+.4,0),(0,-(radius+.4)/COS),(0,(radius+.4)/COS)):
                point=App.Vector(x+dx,y+dy,height)
                if result.isInside(point,.001,False):
                    points.append({'layer_z_mm':z,'point_mm':list(point)})
            for dx,dy in ((0,0),(-.4,0),(.4,0),(0,-.4),(0,.4)):
                point=App.Vector(x+dx,y+dy,height);pn=-(point-P).dot(N)
                if not n0-GRILLE_END_MARGIN+.01<pn<n1+GRILLE_END_MARGIN-.01:continue
                air.append({'hole':index,'layer_z_mm':z,'point_mm':list(point),
                            'inside_original_wall':wall.isInside(point,.001,False)})
        assert len(points)>=12,'斜出音孔孔边样本不足'
        witnesses['grille_'+str(index)]=points
    return witnesses,air


def speaker_grille(rear,cavity):
    """孔轴对齐喇叭发声面法线，只贯通后下弧面，完整底板不切孔。"""
    original=rear.copy();radius=GRILLE_HOLE_DIAMETER/2;holes=[];bores=[]
    assert GRILLE_PITCH-GRILLE_HOLE_DIAMETER>=2.4-.001
    assert len(GRILLE_ROW_MIN_X)==GRILLE_ROWS
    floor_guard=Part.makeBox(300,300,FLOOR_T+1.6,App.Vector(-150,-100,0))
    for row in range(GRILLE_ROWS):
        s=GRILLE_BASE_S+row*GRILLE_PITCH
        for column in range(GRILLE_COLUMNS):
            x=(column-(GRILLE_COLUMNS-1)/2)*GRILLE_PITCH
            if abs(x)<GRILLE_ROW_MIN_X[row]-.001:continue
            probe=cyl(radius,SPEAKER_BACK_N+.01,120,x,s)
            segments=[]
            for solid in original.common(probe).Solids:
                values=[-(v-P).dot(N) for v in solid.tessellate(.01)[0]]
                segments.append((min(values),max(values)))
            assert segments,'出音孔未接触壳壁'
            inner,outer=max(segments,key=lambda span:span[1])
            path=cyl(radius,SPEAKER_BACK_N+.01,inner-GRILLE_END_MARGIN,x,s)
            assert path.common(original).Volume<.001,'发声面至斜孔之间被胶台或其他壳内结构遮挡：'+str((x,s))
            bore=cyl(radius,inner-GRILLE_END_MARGIN,outer+GRILLE_END_MARGIN,x,s)
            assert bore.common(original).common(floor_guard).Volume<.001,'斜出音孔侵入底板保护区：'+str((x,s,bore.BoundBox.ZMin))
            inside=cyl(radius,inner-GRILLE_END_MARGIN,inner-GRILLE_END_MARGIN+.03,x,s)
            outside=cyl(radius,outer+GRILLE_END_MARGIN-.03,outer+GRILLE_END_MARGIN,x,s)
            assert inside.common(cavity).Volume/inside.Volume>.99,'斜孔内端未完整接入内腔'
            assert outside.common(original).Volume<.001,'斜孔外端被遮挡'
            b=bore.BoundBox;center=pt(x,s,outer)
            holes.append({'center_x_s_mm':[x,s],'center_x_z_mm':[x,center.z],
                'wall_n_mm':[inner,outer],'wall_y_mm':[b.YMin,b.YMax],
                'bounds_world_mm':[b.XMin,b.XMax,b.YMin,b.YMax,b.ZMin,b.ZMax],
                'wall_start_mm':list(pt(x,s,inner)),'wall_end_mm':list(center),
                'bore_length_mm':outer-inner+2*GRILLE_END_MARGIN,
                'removed_mm3':bore.common(original).Volume,
                'exit_connects_cavity':True,'exterior_exit_clear':True})
            bores.append(bore)
        print('斜出音孔行',row+1,flush=True)
    rear=rear.cut(Part.makeCompound(bores)).removeSplitter()
    assert rear.isValid() and len(rear.Solids)==1 and rear.common(Part.makeCompound(bores)).Volume<.001
    witnesses,air=grille_samples(rear,original,holes)
    return rear,bores,{'count':len(holes),'rows':GRILLE_ROWS,'columns':GRILLE_COLUMNS,
        'diameter_mm':GRILLE_HOLE_DIAMETER,'pitch_mm':GRILLE_PITCH,
        'minimum_web_mm':GRILLE_PITCH-GRILLE_HOLE_DIAMETER,'axis_world':list(-N),
        'nominal_open_area_mm2':len(holes)*math.pi*radius**2,'support_enforcers':[],
        'holes':holes,'print_witnesses':witnesses,'air_samples':air,
        'physical_audio_verified':False,'speaker_radiating_face_verified':True,
        'note':'按用户确认的双振膜面朝后下方，孔轴与发声面法线一致；实际声音需装机验证'}


def microphone_intake(rear,cavity):
    """左右各两排三孔，只切穿第一段前壁并接入原有连通内腔。"""
    original_wall=rear.copy()
    axis=App.Vector(0,1,0)
    radius=MIC_HOLE_DIAMETER/2
    right=[(MIC_HOLE_GROUP_X+(column-(MIC_HOLE_COLUMNS-1)/2)*MIC_HOLE_PITCH,
            MIC_HOLE_BASE_Z+row*MIC_HOLE_PITCH)
           for row in range(MIC_HOLE_ROWS) for column in range(MIC_HOLE_COLUMNS)]
    assert MIC_HOLE_PITCH-MIC_HOLE_DIAMETER>=MIC_HOLE_MIN_WEB
    assert MIC_HOLE_BASE_Z-radius-FLOOR_T>=MIC_HOLE_MIN_WEB
    bores=[];holes=[]
    for side in (-1,1):
        for right_x,z in right:
            x=side*right_x
            segments=[]
            for solid in Part.makeCylinder(radius,200,App.Vector(x,-80,z),axis).common(rear).Solids:
                points=solid.tessellate(.01)[0]
                segments.append((min(v.y for v in points),max(v.y for v in points)))
            assert segments,'拾音孔未碰到 P4 前壁'
            front,back=min(segments)
            bore=Part.makeCylinder(radius,back-front+2*MIC_HOLE_END_MARGIN,
                App.Vector(x,front-MIC_HOLE_END_MARGIN,z),axis)
            exit_disc=Part.makeCylinder(radius,.05,App.Vector(x,back+MIC_HOLE_END_MARGIN-.05,z),axis)
            assert exit_disc.common(cavity).Volume/exit_disc.Volume>.99,'拾音孔出口没有完整进入内腔'
            assert all(bore.distToShape(other)[0]>=MIC_HOLE_MIN_WEB-.001 for other in bores),'孔间筋不足'
            removed=bore.common(rear).Volume
            assert removed>.1,'拾音孔未切除壳壁'
            rear=rear.cut(bore)
            assert bore.common(rear).Volume<.001,'拾音孔未贯通'
            holes.append({'center_x_z_mm':[x,z],'front_y_mm':front,'cavity_y_mm':back,'wall_y_mm':[front,back],
                'bore_length_mm':back-front+2*MIC_HOLE_END_MARGIN,'removed_mm3':removed,
                'exit_connects_cavity':True})
            bores.append(bore)
    rear=rear.removeSplitter()
    assert rear.isValid() and len(rear.Solids)==1,'拾音开孔后后盖实体不连通'
    witnesses,air=acoustic_samples(rear,original_wall,holes,radius,'microphone_',MIC_HOLE_END_MARGIN)
    return rear,bores,{'count':len(holes),'rows_per_side':MIC_HOLE_ROWS,'columns_per_side':MIC_HOLE_COLUMNS,
        'diameter_mm':MIC_HOLE_DIAMETER,'pitch_mm':MIC_HOLE_PITCH,
        'minimum_web_mm':MIC_HOLE_PITCH-MIC_HOLE_DIAMETER,
        'floor_ligament_mm':MIC_HOLE_BASE_Z-radius-FLOOR_T,'axis_world':[0,1,0],
        'holes':holes,'print_witnesses':witnesses,'air_samples':air,
        'independent_acoustic_channels':False,'factory_microphone_coordinates_verified':False,
        'physical_audio_verified':False,'note':'左右共腔拾音，孔道接入内腔；原厂麦克风口位置、原板遮挡及回声须装机检查'}


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
                      -SPEAKER_H/2-0.5,SPEAKER_H/2+0.5,FRAME_SPEAKER_RELIEF_FRONT_N,27))
    ring=ring.cut(box(-60,60,-60,-46,13,27))  # 下端开口，让开连续后盖向底板的曲面过渡。
    main_parts=[ring]
    for x,s in SCREWS:
        r=math.hypot(x,s)
        main_parts.append(cyl(MODULE_BOSS_R,MODULE_MOUNT_FRONT_N,20.5,x,s))
        main_parts.append(local_rectangle(x,s,-1,54.1-r,-MODULE_RIB_W/2,MODULE_RIB_W/2,
                                          MODULE_MOUNT_FRONT_N,20.5))
    for x,s in BOLT_POINTS:
        main_parts.extend([radial_wedge(x,s,40,52.5,13.2,26,8),
                           cyl(LOCK_BOSS_R,LOCK_BOSS_FRONT_N,LOCK_INSERT_BACK_N,x,s)])
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
        # 背面轴向热熔，封实原六角袋、侧入口及避让屋顶，保留原有母座和外筋。
        main_shell=main_shell.cut(cyl(1.7,LOCK_TIP_RELIEF_FRONT_N,LOCK_INSERT_BACK_N+.1,x,s))
        main_shell=main_shell.cut(cyl(LOCK_INSERT_BORE/2,
            LOCK_INSERT_BACK_N-LOCK_INSERT_DEPTH,LOCK_INSERT_BACK_N+.1,x,s))
        main_shell=main_shell.cut(Part.makeCone(LOCK_INSERT_BORE/2,
            LOCK_INSERT_BORE/2+LOCK_INSERT_CHAMFER,LOCK_INSERT_CHAMFER,
            pt(x,s,LOCK_INSERT_BACK_N-LOCK_INSERT_CHAMFER),-N))
    relief=cyl(FRAME_R,MOUTH_N,FRAME_BACK_N-ELEPHANT_RELIEF).fuse(
        Part.makeCone(FRAME_R,FRAME_R-ELEPHANT_RELIEF,ELEPHANT_RELIEF,pt(0,0,FRAME_BACK_N-ELEPHANT_RELIEF),-N))
    main_shell=main_shell.common(relief)
    main_shell=main_shell.removeSplitter()
    # 取消四处耳孔座；整个箱体和四耳都按完整包络避让。
    rear,speaker_tape=speaker_tape_mount(rear,envelope,above_floor)
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
    # 两柱加短横梁组成一体扎带桥，4 mm 跨距可短桥接。
    tie_supports=[]
    for x in (18,25):
        profile=face([App.Vector(x,TIE_FRONT_Y,TIE_BASE_Z+.1),
            App.Vector(x+3,TIE_FRONT_Y,TIE_BASE_Z+.1),
            App.Vector(x+3,TIE_BACK_Y,TIE_BASE_Z+.1),App.Vector(x,TIE_BACK_Y,TIE_BASE_Z+.1)])
        tie_supports.append(down_support(profile,App.Vector(0,1,0),22,envelope,above_floor))
    tie=fuse([Part.makeBox(3,TIE_BACK_Y-TIE_FRONT_Y,8,App.Vector(x,TIE_FRONT_Y,TIE_BASE_Z)) for x in (18,25)]+
             [Part.makeBox(10,TIE_BACK_Y-TIE_FRONT_Y,2,App.Vector(18,TIE_FRONT_Y,TIE_BASE_Z+6))]+tie_supports).common(envelope)
    rear=rear.fuse(tie)
    # 显式打通内侧穿带槽，保证8 mm深度可用，避免形成不可达的小气腔。
    rear=rear.cut(Part.makeBox(4,TIE_CHANNEL_DEPTH+.1,6,App.Vector(21,TIE_FRONT_Y-.1,TIE_BASE_Z)))
    recess=Part.Face(ellipse(-1,43,37,25)).extrude(Z*1.6)
    rear=rear.cut(recess).removeSplitter()
    top_z=FRONT_Z+SIN*OUTER_R-COS*(MOUTH_N+TOP_FLAT_DEPTH)
    rear=rear.common(Part.makeBox(300,300,top_z+1,App.Vector(-150,-100,-1))).removeSplitter()
    # 顶部收平后，把与前口相交的薄楔整个退后，避免留下不足 1.2 mm 的唇边。
    rear=rear.cut(box(-20,20,0,60,MOUTH_N,MOUTH_N+TOP_MOUTH_RELIEF)).removeSplitter()
    main_shell,rear,upper_hooks,upper_pins=add_upper_hooks(main_shell,rear)
    rear,grille_bores,grille_report=speaker_grille(rear,cavity)
    rear,mic_bores,mic_report=microphone_intake(rear,cavity)
    rear,usb_access_report=add_usb_access(rear)
    for hole,bore in zip(mic_report['holes'],mic_bores):
        assert bore.common(main_shell).Volume<.001,'拾音孔碰承托架：'+str(hole['center_x_z_mm'])
    tie_open=Part.makeBox(3.8,TIE_CHANNEL_DEPTH-.2,5.8,App.Vector(21.1,TIE_FRONT_Y+0.1,TIE_BASE_Z+.1))
    assert rear.common(tie_open).Volume<0.001,'扎带穿入口被壳壁堵塞'
    # 完整总外形包络，不再假设耳根存在半径7 mm空位；发声面为背侧n增大方向。
    speaker=box(-SPEAKER_W/2,SPEAKER_W/2,-SPEAKER_H/2,SPEAKER_H/2,SPEAKER_FRONT_N,SPEAKER_BACK_N)
    # 圆面只表达照片中双振膜朝向，不作为实测振膜直径或干涉放行依据。
    speaker_faces=Part.makeCompound([cyl(17,SPEAKER_BACK_N+.01,SPEAKER_BACK_N+.05,x,0) for x in (-24,24)])
    shapes={'main_shell':main_shell,'rear_cover':rear}
    write_print_features(mic_report,grille_report)
    module_heads=[cyl(MODULE_HEAD_R,MODULE_SEAT_N,MODULE_SEAT_N+MODULE_HEAD_H,x,s) for x,s in SCREWS]
    module_shafts=[cyl(1.25,MODULE_SEAT_N-MODULE_SCREW_L,MODULE_SEAT_N,x,s) for x,s in SCREWS]
    module_engagement=MODULE_THREAD_ENTRY_N-(MODULE_SEAT_N-MODULE_SCREW_L)
    assert abs(MODULE_SEAT_N-MODULE_SCREW_L-MODULE_ORIGINAL_TIP_N)<0.001,'M2.5 螺丝尖端位置改变'
    module_bearing=[]
    for x,s in SCREWS:
        area=main_shell.common(cyl(MODULE_HEAD_R,MODULE_SEAT_N-0.02,MODULE_SEAT_N,x,s)).Volume/0.02
        assert area>=8,'M2.5 实际承压面积不足'
        module_bearing.append(area)
    m3_heads=[cyl(2.8,LOCK_HEAD_SEAT_N,LOCK_HEAD_SEAT_N+3,x,s) for x,s in BOLT_POINTS]
    m3_shafts=[cyl(1.5,LOCK_HEAD_SEAT_N-LOCK_SCREW_LENGTH,LOCK_HEAD_SEAT_N,x,s) for x,s in BOLT_POINTS]
    inserts=[cyl(LOCK_INSERT_OD/2,LOCK_INSERT_BACK_N-LOCK_INSERT_LENGTH,LOCK_INSERT_BACK_N,x,s).cut(
        cyl(1.5,LOCK_INSERT_BACK_N-LOCK_INSERT_LENGTH-.1,LOCK_INSERT_BACK_N+.1,x,s)) for x,s in BOLT_POINTS]
    # 滚花外径与底孔之间的 0.1 mm 径向干涉属于热熔配合，不作刚体碰撞错误。
    insert_cores=[cyl(LOCK_INSERT_BORE/2-.001,LOCK_INSERT_BACK_N-LOCK_INSERT_LENGTH,LOCK_INSERT_BACK_N,x,s).cut(
        cyl(1.5,LOCK_INSERT_BACK_N-LOCK_INSERT_LENGTH-.1,LOCK_INSERT_BACK_N+.1,x,s)) for x,s in BOLT_POINTS]
    plug=box(-18.9,-5.9,29.2,44.2,7.5,16.5)
    wire=cable_envelope([pt(-12.4,44.2,12),pt(-12.4,38,18),pt(0,38,22),pt(0,38,45),
                         pt(0,35,50),App.Vector(0,TIE_FRONT_Y-2,TIE_BASE_Z+3),
                         App.Vector(23,TIE_FRONT_Y-2,TIE_BASE_Z+3),
                         App.Vector(23,TIE_FRONT_Y+1,TIE_BASE_Z-3),
                         App.Vector(0,65,24),App.Vector(0,100,24)])
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
    # 用 0.02 mm 虚拟压入测量四处止挡的实际接触面积。
    forward=rear.copy();forward.translate(N*0.02)
    stop_areas=[]
    for a in HOOK_ANGLES:
        x=HOOK_RADIUS*math.cos(math.radians(a))
        for sign in (-1,1):
            pad=box(x+sign*6.8-1.5,x+sign*6.8+1.5,HOOK_AXIS_S-5,HOOK_AXIS_S-1,25.9,26.1)
            area=main_shell.common(forward).common(pad).Volume/0.02
            assert area>10,'挂钩止挡接触不足'
            stop_areas.append(area)
    tape_checks=[]
    for name,x0,x1,s0,s1 in speaker_pad_rectangles():
        probe=box(x0,x1,s0,s1,SPEAKER_PAD_N+.001,SPEAKER_PAD_N+SPEAKER_PAD_MIN_T)
        assert rear.common(probe).Volume>=probe.Volume*.999,'贴胶台前端实体厚度不足'
        tape_checks.append({'name':name,'bounds_x_s_mm':[x0,x1,s0,s1],
                            'contact_area_mm2':(x1-x0)*(s1-s0),'pad_depth_mm':SPEAKER_PAD_MIN_T})
    keepout=box(-SPEAKER_W/2-SPEAKER_CLEARANCE,SPEAKER_W/2+SPEAKER_CLEARANCE,
        -SPEAKER_H/2-SPEAKER_CLEARANCE,SPEAKER_H/2+SPEAKER_CLEARANCE,
        SPEAKER_FRONT_N-SPEAKER_CLEARANCE,SPEAKER_BACK_N+SPEAKER_CLEARANCE)
    assert keepout.cut(envelope).Volume<.001,'完整喇叭及周边间隙超出外壳包络'
    assert rear.common(keepout).Volume<.001,'完整箱体周边0.5 mm间隙不足'
    insertion=box(-SPEAKER_W/2-SPEAKER_CLEARANCE,SPEAKER_W/2+SPEAKER_CLEARANCE,
        -SPEAKER_H/2-SPEAKER_CLEARANCE,SPEAKER_H/2+SPEAKER_CLEARANCE,-60,SPEAKER_BACK_N+SPEAKER_CLEARANCE)
    assert rear.common(insertion).Volume<.001,'贴胶喇叭轴向装入路径受阻'
    face_air=box(-40,40,-19.5,19.5,SPEAKER_BACK_N+.001,SPEAKER_BACK_N+SPEAKER_FACE_CLEARANCE)
    assert rear.common(face_air).Volume<.001,'振膜面前方2 mm净空不足'
    print('贴胶台和完整箱体装入检查通过',tape_checks,flush=True)
    assert speaker.common(wire).Volume<0.02,'线束碰音箱'
    for hardware in module_heads+module_shafts+m3_heads+m3_shafts+insert_cores+speaker_tape:
        for name,shape in shapes.items():
            assert shape.common(hardware).Volume<0.02,name+'碰紧固件'
    assert all(h.common(speaker).Volume<0.02 for h in speaker_tape),'胶层与箱体异常重叠'
    for x,s in SCREWS:
        assert main_shell.common(cyl(MODULE_HEAD_R+MODULE_HEAD_CLEARANCE,MODULE_SEAT_N,110,x,s)).Volume<0.02,'M2.5 头部装入/旋转路径'
    for x,s in BOLT_POINTS:
        tool=cyl(2,38,110,x,s)
        assert tool.common(rear).Volume<0.02,'M3工具路径'
        assert tool.common(main_shell).Volume+tool.common(speaker).Volume<0.02
    insert_installation_checks=[]
    for (x,s),insert in zip(BOLT_POINTS,inserts):
        expected=cyl(LOCK_INSERT_OD/2,LOCK_INSERT_BACK_N-LOCK_INSERT_LENGTH,LOCK_INSERT_BACK_N,x,s).cut(
            cyl(LOCK_INSERT_BORE/2,LOCK_INSERT_BACK_N-LOCK_INSERT_LENGTH-.1,LOCK_INSERT_BACK_N+.1,x,s))
        overlap=insert.copy(True).common(main_shell.copy(True))
        assert overlap.copy(True).cut(expected).Volume<.001,'热熔干涉越过滚花预期区域'
        assert sum(insert.common(v).Volume for v in [rear,speaker,plug,wire])<.02,'热熔螺母碰周边零件'
        tool=cyl(2.0,LOCK_INSERT_BACK_N+.01,LOCK_INSERT_BACK_N+12,x,s)
        tool_overlap=tool.common(main_shell).Volume
        assert tool_overlap<.001,'背面热熔工具入口受阻'
        insert_installation_checks.append({'center_x_s_mm':[x,s],
            'knurl_interference_volume_mm3':overlap.Volume,'heater_tool_overlap_mm3':tool_overlap})
    lock_tip_n=LOCK_HEAD_SEAT_N-LOCK_SCREW_LENGTH
    lock_engagement=min(LOCK_INSERT_BACK_N,LOCK_HEAD_SEAT_N)-max(
        LOCK_INSERT_BACK_N-LOCK_INSERT_LENGTH,lock_tip_n)
    assert lock_engagement>=LOCK_INSERT_LENGTH-.001,'锁盖螺丝未完整啮合热熔螺母'
    assert lock_tip_n-LOCK_TIP_RELIEF_FRONT_N>=.5,'锁盖螺丝尾端顶底'
    travel_checks=[]
    poses=[(a,0) for a in (0,1,2,4,6,8,10,12,15,HOOK_OPEN_ANGLE)]
    poses += [(HOOK_OPEN_ANGLE,t) for t in (1,2,4,8,16,32,64)]
    for angle,travel in poses:
        moved=hook_pose(rear,angle,0,travel)
        moving_speaker=hook_pose(speaker,angle,0,travel)
        moving_hardware=hook_pose(Part.makeCompound(speaker_tape),angle,0,travel)
        fixed=Part.makeCompound([main_shell]+module_heads)
        overlaps={'cover_to_frame':moved.common(fixed).Volume,
                  'speaker_to_frame':moving_speaker.common(fixed).Volume,
                  'speaker_tape_to_frame':moving_hardware.common(fixed).Volume}
        print('合盖',angle,travel,overlaps,flush=True)
        assert max(overlaps.values())<0.02,'合盖行程干涉'
        travel_checks.append({'angle_deg':angle,'travel_mm':travel,'overlaps_mm3':overlaps})
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
    mic_obstacles=[('carrier',main_shell),('module',module),('speaker',speaker),('plug',plug),('wire',wire)]
    mic_obstacles += [('hardware_'+str(i),shape) for i,shape in enumerate(
        module_heads+module_shafts+m3_heads+m3_shafts+inserts+speaker_tape)]
    mic_obstacles += [('cover_tool_'+str(i),cyl(2,38,110,x,s)) for i,(x,s) in enumerate(BOLT_POINTS)]
    acoustic_obstacles=[(name,[(solid,solid.BoundBox) for solid in obstacle.Solids])
        for name,obstacle in mic_obstacles]
    for report,bores in ((mic_report,mic_bores),(grille_report,grille_bores)):
        for hole,bore in zip(report['holes'],bores):
            overlaps={};bore_bounds=bore.BoundBox
            for name,solids in acoustic_obstacles:
                # 包围盒仅排除不可能相交的实体，所有候选仍做精确 BRep 布尔检查。
                candidates=[solid for solid,bounds in solids if bore_bounds.intersect(bounds)]
                overlaps[name]=round(bore.common(Part.makeCompound(candidates)).Volume,6) if candidates else 0.0
            assert max(overlaps.values())<.001,'声孔通道被内部零件挡住：'+str(overlaps)
            hole['obstacles_overlap_mm3']=overlaps
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
    hook_motion=verify_hook_motion(main_shell,rear,speaker,speaker_tape,module,module_heads)
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
                       ('Speaker_Radiating_Faces_Reference',speaker_faces),
                       ('Module_M25_Heads_Reference',Part.makeCompound(module_heads)),
                       ('Module_M25_Shafts_Reference',Part.makeCompound(module_shafts)),('M3_Heads_Reference',Part.makeCompound(m3_heads)),
                       ('M3_Shafts_Reference',Part.makeCompound(m3_shafts)),('M3_Heat_Inserts_Reference',Part.makeCompound(inserts)),
                       ('Speaker_Tape_Reference',Part.makeCompound(speaker_tape)),
                       ('Internal_USB_Plug_Reference',plug),('Cable_Route_Reference',wire)]:
        feature(doc,name,shape,(0.25,0.45,0.34),False)
    doc.recompute();configure_display(doc);doc.saveAs(os.path.join(OUT,'enclosure.FCStd'))
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
    for name,shape in [('module',cyl(MODULE_R,0,6)),('speaker',speaker),('speaker_faces',speaker_faces),
                       ('speaker_tape',Part.makeCompound(speaker_tape)),
                       ('section',rear.common(Part.makeBox(150,250,160,App.Vector(0,-100,0)))),
                       ('fasteners',Part.makeCompound(m3_heads+m3_shafts+inserts+module_heads+module_shafts))]:
        mesh_write(shape,os.path.join(CACHE,name+'.stl'))
    # 止口和安装位局部辅助件只归档，不增加正式打印件；热熔孔不生成试孔件。
    fit_dir=os.environ.get('P4_FIT_DIR',os.path.join(ROOT,'archive','fit_samples'));os.makedirs(fit_dir,exist_ok=True)
    hook_x=HOOK_RADIUS*math.cos(math.radians(HOOK_ANGLES[0]))
    for name,shape in [('upper_hook',rear),('upper_hook_socket',main_shell)]:
        sample=shape.common(box(hook_x-9,hook_x+9,HOOK_AXIS_S-6,57,13,32))
        mesh_write(sample,os.path.join(fit_dir,name+'.stl'),printing=True)
    mesh_write(rear.common(box(35,48,-14,14,SPEAKER_PAD_N-.1,60)),
               os.path.join(fit_dir,'speaker_tape_pad.stl'),printing=True)
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
             'seam_clearance_mm':HOOK_CLEARANCE,'locator_engagement_mm':None,'locator_side_clearance_mm':None,
             'axial_stop_pads':4,
             'axial_stop_contact_areas_mm2':stop_areas,
             'rear_screw':'2 × M3×16 内六角圆柱头，2 × M3×3×4 热熔螺母',
             'heat_set_insert':{'thread':'M3','length_mm':LOCK_INSERT_LENGTH,
                 'outer_diameter_mm':LOCK_INSERT_OD,'bore_diameter_mm':LOCK_INSERT_BORE,
                 'bore_depth_mm':LOCK_INSERT_DEPTH,'entry_chamfer_mm':LOCK_INSERT_CHAMFER,
                 'rear_face_n_mm':LOCK_INSERT_BACK_N,'thread_engagement_mm':lock_engagement,
                 'screw_tip_n_mm':lock_tip_n,'screw_tip_to_relief_floor_mm':lock_tip_n-LOCK_TIP_RELIEF_FRONT_N,
                 'installation':'先热熔再装开发板；从承托架背面轴向压入，端面齐平',
                 'installation_checks':insert_installation_checks},
             'module_screw':'4 × M2.5×6 内六角圆柱头，头径≤4.7 mm、头高≤2.5 mm',
             'module_mount_points_mm':SCREWS,'module_mount_thickness_mm':MODULE_SEAT_N-MODULE_MOUNT_FRONT_N,
             'module_engagement_mm':module_engagement,'module_tip_n_mm':MODULE_SEAT_N-MODULE_SCREW_L,
             'module_original_tip_n_mm':MODULE_ORIGINAL_TIP_N,'removed_original_screw_indices':removed,
             'module_retained_solids':len(retained),'module_head_bearing_areas_mm2':module_bearing,
             'module_head_clearance_diameter_mm':2*(MODULE_HEAD_R+MODULE_HEAD_CLEARANCE),
             'front_hidden_required':True,
             'speaker_corner_clearance_wall_mm':OUTER_R-math.hypot(SPEAKER_W/2+0.5,SPEAKER_H/2+0.5),
             'locator_socket_radial_wall_mm':None,
             'speaker_dimensions_mm':[SPEAKER_W,SPEAKER_H,SPEAKER_T],
             'speaker_mount':{'type':'边框泡棉双面胶','tape_thickness_mm':SPEAKER_TAPE_T,
                 'long_tape_width_mm':SPEAKER_LONG_TAPE_W,'short_tape_width_mm':SPEAKER_SHORT_TAPE_W,
                 'short_edge_inset_mm':SPEAKER_SHORT_INSET,'face_normal_world':list(-N),
                 'body_front_n_mm':SPEAKER_FRONT_N,'radiating_face_n_mm':SPEAKER_BACK_N,
                 'pad_face_n_mm':SPEAKER_PAD_N,'face_clearance_mm':SPEAKER_FACE_CLEARANCE,
                 'body_clearance_mm':SPEAKER_CLEARANCE,'full_body_envelope':True,
                 'insertion_path_verified':True,'tape_pads':tape_checks,
                 'tape_area_mm2':sum(c['contact_area_mm2'] for c in tape_checks),
                 'physical_adhesion_verified':False},
             'frame_radial_clearance_mm':INNER_R-FRAME_R,
             'carrier_print_bed':'后侧框架平面朝下','continuous_cover':True,
             'fdm_design':{'nozzle_mm':0.4,'materials':['PLA','PETG'],'minimum_wall_target_mm':1.2,
                 'minimum_load_wall_target_mm':1.6,'module_mount_closed_holes':True,
                 'heat_insert_bore_mm':LOCK_INSERT_BORE,'heat_insert_bore_depth_mm':LOCK_INSERT_DEPTH,
                 'entry_lead_mm':FIT_LEAD,'bed_edge_relief_mm':ELEPHANT_RELIEF,'rear_flat_top_z_mm':top_z},
             'carrier_reinforcement':{'module_boss_radius_mm':MODULE_BOSS_R,'module_rib_width_mm':MODULE_RIB_W,
                 'locator_back_inner_radius_mm':LOCATOR_BACK_INNER_R,'locator_back_width_mm':LOCATOR_BACK_WIDTH},
             'rear_outlet_mm':[20,12],'outlet_corner_radius_mm':3,
             'usb_access':usb_access_report,
             'cable_reference_diameter_mm':3.5,'cable_bend_radius_verified':False,
             'bottom_ring_width_samples':288,
             'assembly_travel':travel_checks,'upper_hooks':hook_motion,'cavity_cm3':cavity.Volume/1000,
             'estimated_module_mass_g':220,'estimated_speaker_mass_g':100,
             'estimated_total_mass_g':mass,'estimated_tip_angle_deg':tip,
             'speaker_mount_location':'后盖边框胶台，喇叭随盖移动',
             'speaker_body_shape_verified':False,
             'speaker_mount_status':'使用完整100×45×21 mm保守总包络；按用户确认的正面硬边框贴胶，不依赖耳根空位。',
             'microphone_hole_verified':True,'microphone_intake':mic_report,
             'speaker_grille_verified':True,'speaker_grille':grille_report,'physical_fit_verified':False}
    with open(os.path.join(OUT,'validation.json'),'w',encoding='utf-8') as f:
        json.dump(metrics,f,ensure_ascii=False,indent=2)
    print('全部导出完成',OUT,flush=True)


try:
    main()
except Exception:
    traceback.print_exc()
    raise
