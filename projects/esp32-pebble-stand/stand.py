"""ESP32-S3-Touch-AMOLED-1.75-B 成品模块的鹅卵石桌面底座。

模块背面的三颗原厂螺丝固定加宽支架；后壳由止口定位、两颗 M2.5 锁紧。
在 FreeCAD 控制台或 freecadcmd 中运行，输出固定到 ./output/。
"""

import math
import os
import json
import struct

import FreeCAD as App
import MeshPart
import Part


DOC_NAME = "Pebble_Stand"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
OUT_DIR = os.path.join(SCRIPT_DIR, "output")

# 模块是带原厂外壳的成品，不是裸 PCB。
MODULE_R = 25.5
MODULE_DEPTH = 12.1
TILT_DEG = 40.0
MODULE_BOTTOM_CLEARANCE = 5.1
SCREWS_2D = [(0.0, 20.50), (13.75, -14.70), (-13.75, -14.70)]
SCREW_CLEARANCE_R = 1.15  # M2 初始值，打印前用原厂螺丝核对

BATTERY_W = 36.0
BATTERY_H = 26.0
BATTERY_T = 8.0
BATTERY_CORNER_R = 3.0
BATTERY_OFFSET_S = 1.0
CONNECTOR_X = 6.5
CONNECTOR_S = 17.25
CONNECTOR_W = 5.8
CONNECTOR_H = 5.0

CARRIER_FRONT_N = MODULE_DEPTH
CARRIER_BACK_N = 17.1
CARRIER_PAD_FRONT_N = 14.7
CARRIER_INNER_R = 20.4
CARRIER_OUTER_R = 22.8
CARRIER_BOSS_R = 2.6
SHELL_MOUTH_N = MODULE_DEPTH + 0.3
SHELL_PROJECTION_R = 25.2
SHELL_INNER_R = 23.1
SHELL_FLOOR_T = 2.6
FRONT_WALL_TARGET = 2.4
FOOT_CENTER_Y = 14.0
FOOT_OUTER_RX = 20.5
FOOT_OUTER_RY = 20.0
FOOT_INNER_RX = 15.5
FOOT_INNER_RY = 15.0
FOOT_RECESS = 0.6

GUIDES = ((0.0, 8.0), (90.0, 8.0), (180.0, 8.0))
GUIDE_CLEARANCE = 0.25
GUIDE_END_N = 20.1
LOCK_POINTS = ((-7.0, -16.0), (7.0, -16.0))
LOCK_NUT_FRONT = 14.6
LOCK_NUT_BACK = 16.8
LOCK_BOSS_BACK = 19.0
LOCK_HEAD_SEAT = 21.5

TILT = math.radians(TILT_DEG)
SIN = math.sin(TILT)
COS = math.cos(TILT)
X = App.Vector(1, 0, 0)
Y = App.Vector(0, 1, 0)
Z = App.Vector(0, 0, 1)
N = App.Vector(0, -SIN, COS)
S = App.Vector(0, COS, SIN)
P = App.Vector(0, 0, MODULE_BOTTOM_CLEARANCE + MODULE_R * SIN + MODULE_DEPTH * COS)


def plate_point(x, s, n):
    return P + X * x + S * s - N * n


def polygon_face(points):
    return Part.Face(Part.makePolygon(points + [points[0]]))


def rectangle_face(x0, x1, s0, s1, n):
    return polygon_face([
        plate_point(x0, s0, n), plate_point(x1, s0, n),
        plate_point(x1, s1, n), plate_point(x0, s1, n),
    ])


def rounded_rectangle_face(width, height, radius, center_s, n):
    points = []
    for cx, cy, start in (
        (width / 2 - radius, height / 2 - radius, 0),
        (-width / 2 + radius, height / 2 - radius, 90),
        (-width / 2 + radius, -height / 2 + radius, 180),
        (width / 2 - radius, -height / 2 + radius, 270),
    ):
        for i in range(9):
            angle = math.radians(start + i * 90.0 / 8)
            points.append(plate_point(
                cx + radius * math.cos(angle),
                center_s + cy + radius * math.sin(angle), n
            ))
    return polygon_face(points)


def ellipse_wire(z, rx, ry, cy, steps=48):
    points = [
        App.Vector(rx * math.cos(2 * math.pi * i / steps),
                   cy + ry * math.sin(2 * math.pi * i / steps), z)
        for i in range(steps)
    ]
    return Part.makePolygon(points + [points[0]])


def radial_strip(angle, r0, r1, width, n):
    u = X * math.cos(angle) + S * math.sin(angle)
    v = -X * math.sin(angle) + S * math.cos(angle)
    origin = P - N * n
    return polygon_face([
        origin + u * r0 - v * width / 2,
        origin + u * r1 - v * width / 2,
        origin + u * r1 + v * width / 2,
        origin + u * r0 + v * width / 2,
    ])


def axial_cylinder(radius, n0, n1, x=0, s=0):
    return Part.makeCylinder(radius, n1-n0, plate_point(x,s,n0), -N)


def axial_box(x0, x1, s0, s1, n0, n1):
    return rectangle_face(x0,x1,s0,s1,n0).extrude(-N*(n1-n0))


def hex_nut(x, s, n0, n1, across):
    radius = across/math.sqrt(3)
    return polygon_face([plate_point(x+radius*math.cos(i*math.pi/3),
                                    s+radius*math.sin(i*math.pi/3),n0)
                         for i in range(6)]).extrude(-N*(n1-n0))


def connect_web(x0, s0, x1, s1, width, n0, n1):
    length = math.hypot(x1-x0,s1-s0)
    dx, ds = -(s1-s0)/length*width/2, (x1-x0)/length*width/2
    return polygon_face([plate_point(x0+dx,s0+ds,n0),plate_point(x1+dx,s1+ds,n0),
                         plate_point(x1-dx,s1-ds,n0),plate_point(x0-dx,s0-ds,n0)]).extrude(-N*(n1-n0))


def add_feature(doc, name, shape, color, visible=True):
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    try:
        obj.ViewObject.ShapeColor = color
        obj.ViewObject.Visibility = visible
    except Exception:
        pass
    return obj


def export_stl(shape, filename, lay_flat=False):
    export_shape = shape.copy()
    if lay_flat:
        export_shape.Placement = App.Placement(
            App.Vector(), App.Rotation(N, Z)
        ).multiply(export_shape.Placement)
        export_shape.translate(App.Vector(0, 0, -export_shape.BoundBox.ZMin))
    mesh = MeshPart.meshFromShape(
        Shape=export_shape, LinearDeflection=0.05,
        AngularDeflection=0.30, Relative=False,
    )
    mesh.write(os.path.join(OUT_DIR, filename))
    steep_overhangs = [
        facet for facet in mesh.Facets
        if facet.Normal.z < -0.707
        and min(point[2] for point in facet.Points) > SHELL_FLOOR_T + 1.0
    ]
    steep_area = sum(
        (App.Vector(*facet.Points[1]) - App.Vector(*facet.Points[0])).cross(
            App.Vector(*facet.Points[2]) - App.Vector(*facet.Points[0])
        ).Length / 2.0
        for facet in steep_overhangs
    )
    print("%s: mesh solids=%d, closed=%s, steep overhang=%d facets/%.1f mm2" % (
        filename, len(mesh.getSeparateComponents()), mesh.isSolid(),
        len(steep_overhangs), steep_area,
    ))
    assert len(mesh.getSeparateComponents()) == 1 and mesh.isSolid()


def audit_front_wall(filename):
    """独立于稀疏 BRep 采样，直接检测交付网格的前口和下缘薄片。"""
    data=open(filename,'rb').read(); count=struct.unpack_from('<I',data,80)[0]
    def sub(a,b):return tuple(a[i]-b[i] for i in range(3))
    def dot(a,b):return sum(a[i]*b[i] for i in range(3))
    def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
    triangles=[]
    for i in range(count):
        v=struct.unpack_from('<12f',data,84+i*50)
        normal=v[:3]; a,b,c=v[3:6],v[6:9],v[9:12]
        triangles.append((normal,a,sub(b,a),sub(c,a),tuple(min(a[k],b[k],c[k]) for k in range(3)),tuple(max(a[k],b[k],c[k]) for k in range(3)),tuple((a[k]+b[k]+c[k])/3 for k in range(3))))
    angle=TILT; N=(0,-SIN,COS); S=(0,COS,SIN); P=(0,0,MODULE_BOTTOM_CLEARANCE+MODULE_R*SIN+MODULE_DEPTH*COS)
    measured=[]
    for i,(norm,a,e1,e2,lo,hi,center) in enumerate(triangles):
        n=dot(sub(P,center),N);s=dot(sub(center,P),S)
        if not (SHELL_MOUTH_N-0.01<=n<=20 or center[2]<14) or abs(dot(norm,N))>.99 or abs(norm[2])>.99:continue
        direction=tuple(-v for v in norm);start=tuple(center[k]+norm[k]*.005 for k in range(3));end=tuple(start[k]+direction[k]*8 for k in range(3))
        raylo=tuple(min(start[k],end[k]) for k in range(3));rayhi=tuple(max(start[k],end[k]) for k in range(3))
        hits=[]
        for _,b,f1,f2,low,high,_ in triangles:
            if any(raylo[k]>high[k]+1e-6 or rayhi[k]<low[k]-1e-6 for k in range(3)):continue
            h=cross(direction,f2);det=dot(f1,h)
            if abs(det)<1e-9:continue
            tvec=sub(start,b);u=dot(tvec,h)/det
            if u < -1e-6 or u > 1.000001:continue
            q=cross(tvec,f1);v=dot(direction,q)/det
            if v < -1e-6 or u+v > 1.000001:continue
            distance=dot(f2,q)/det
            if 0<=distance<=8:hits.append(distance)
        hits.sort();unique=[]
        for h in hits:
            if not unique or h-unique[-1]>.01:unique.append(h)
        if len(unique)>=2 and unique[0]<.02:
            width=unique[1]-unique[0]
            # 定位槽、螺丝座及工具井是功能孔，其自身壁厚另作 BRep 检查。
            # 只跳过射线确实进入功能结构包络的样本，不排除整片前口区域。
            finish=tuple(center[k]+direction[k]*width for k in range(3))
            local_a=(center[0],s,n)
            local_b=(finish[0],dot(sub(finish,P),S),dot(sub(P,finish),N))
            def crosses(bounds):
                lo,hi=0.0,1.0
                for k in range(3):
                    delta=local_b[k]-local_a[k]
                    if abs(delta)<1e-9:
                        if not bounds[k][0]-.02<=local_a[k]<=bounds[k][1]+.02:return False
                    else:
                        t0=(bounds[k][0]-.02-local_a[k])/delta
                        t1=(bounds[k][1]+.02-local_a[k])/delta
                        lo=max(lo,min(t0,t1));hi=min(hi,max(t0,t1))
                        if lo>hi:return False
                return True
            if any(crosses(zone) for zone in wall_audit_zones):continue
            measured.append((round(width,5),tuple(round(v,3) for v in center),round(n,3),round(s,3)))
    assert measured, '前口网格壁厚没有有效采样'
    lower=[v for v in measured if v[3]<-18.4]
    assert lower, '前口下缘没有有效采样'
    minimum=min(v[0] for v in measured)
    assert minimum>=2.0, '前口普通壳壁不足 2 mm：'+str(sorted(measured)[:5])
    print('前口密集网格壁厚',len(measured),minimum,'下缘',min(v[0] for v in lower),flush=True)
    return {'sample_count':len(measured),'minimum_mm':minimum,
            'lower_sample_count':len(lower),'lower_minimum_mm':min(v[0] for v in lower),
            'under_2mm_count':sum(v[0]<2 for v in measured),
            'excluded':'开放端面、水平底面，以及穿过已单独验证的定位槽/紧固件包络的射线；0.01 mm 合并同一表面交点',
            'method':'STL 三角面中心沿反法线求实体段；覆盖前口 n<=20 mm 及 z<14 mm 底部过渡',
            'lowest_samples':[{'thickness_mm':v[0],'world_point_mm':v[1],'n_mm':v[2],'s_mm':v[3]} for v in sorted(measured)[:8]]}


def configure_display(document):
    """GUI 中只显示当前装配，尺寸参考体默认隐藏。"""
    document.Label = 'ESP32-S3-Touch-AMOLED-1.75-B 桌面底座'
    if not App.GuiUp:
        return
    colors = {'Mount_Carrier': (0.83, 0.84, 0.82), 'Rear_Cover': (0.66, 0.69, 0.69),
              'Module_Reference': (0.08, 0.09, 0.10)}
    for obj in document.Objects:
        obj.ViewObject.Visibility = obj.Name in colors
        if obj.Name in colors:
            obj.ViewObject.ShapeColor = colors[obj.Name]
    document.recompute()


os.makedirs(OUT_DIR, exist_ok=True)
if DOC_NAME in App.listDocuments():
    App.closeDocument(DOC_NAME)
doc = App.newDocument(DOC_NAME)

# 周边开口框连接三个螺丝座，中央不再有电池贴板。
carrier = Part.makeCylinder(
    CARRIER_OUTER_R, CARRIER_BACK_N - CARRIER_PAD_FRONT_N,
    plate_point(0, 0, CARRIER_BACK_N), N,
).cut(Part.makeCylinder(
    CARRIER_INNER_R, CARRIER_BACK_N - CARRIER_PAD_FRONT_N + 1,
    plate_point(0, 0, CARRIER_BACK_N + 0.5), N,
))
for sx, sy in SCREWS_2D:
    boss = Part.makeCylinder(
        CARRIER_BOSS_R, 15.5 - CARRIER_FRONT_N,
        plate_point(sx, sy, 15.5), N,
    )
    carrier = carrier.fuse(boss)
    angle = math.atan2(sy, sx)
    rib = radial_strip(
        angle, math.hypot(sx, sy) - 1.0, CARRIER_OUTER_R,
        4.0, CARRIER_BACK_N
    ).extrude(N * (CARRIER_BACK_N - CARRIER_PAD_FRONT_N))
    carrier = carrier.fuse(rib)

for sx, sy in SCREWS_2D:
    carrier = carrier.cut(Part.makeCylinder(
        SCREW_CLEARANCE_R, CARRIER_BACK_N - CARRIER_FRONT_N + 1.0,
        plate_point(sx, sy, CARRIER_BACK_N + 0.5), N
    ))
for sx in (-CONNECTOR_X, CONNECTOR_X):
    carrier = carrier.cut(rectangle_face(
        sx - CONNECTOR_W / 2, sx + CONNECTOR_W / 2,
        CONNECTOR_S - CONNECTOR_H / 2, CONNECTOR_S + CONNECTOR_H / 2,
        CARRIER_BACK_N + 0.5
    ).extrude(N * (CARRIER_BACK_N - CARRIER_FRONT_N + 1.0)))
carrier = carrier.removeSplitter()
# 去掉下方无用圆弧，让出底板上方的空间；两侧下螺丝座仍由上方弧段连接。
carrier = carrier.cut(rectangle_face(-50, 50, -60, -18, 25).extrude(N * 20)).removeSplitter()

# 螺母座连接到原厂下方螺丝座，圆角外形和宽筋分散锁紧力。
for x,s in LOCK_POINTS:
    pad = rounded_rectangle_face(8.5,7.6,1.0,s,13.8).extrude(-N*(LOCK_BOSS_BACK-13.8))
    pad.translate(X*x)
    carrier = carrier.fuse(pad)
    carrier = carrier.fuse(connect_web(x,s,math.copysign(13.75,x),-14.7,4.0,13.8,19.0))
    carrier = carrier.cut(axial_cylinder(1.45,13.5,19.2,x,s))
    carrier = carrier.cut(hex_nut(x,s,LOCK_NUT_FRONT,LOCK_NUT_BACK,5.2))
    carrier = carrier.cut(axial_box(x-3.05,x+3.05,s,s+9,LOCK_NUT_FRONT,LOCK_NUT_BACK))

guide_tongues = []
for degrees,width in GUIDES:
    angle=math.radians(degrees)
    straight=radial_strip(angle,20.6,22.6,width,16.7).extrude(-N*(19.5-16.7))
    lead=Part.makeLoft([radial_strip(angle,20.6,22.6,width,19.5).OuterWire,
                        radial_strip(angle,21.2,22.0,width-1.2,GUIDE_END_N).OuterWire],True,True)
    tongue=straight.fuse(lead).common(axial_cylinder(CARRIER_OUTER_R,16.7,GUIDE_END_N))
    guide_tongues.append(tongue)
    carrier=carrier.fuse(tongue)
carrier=carrier.removeSplitter()
for x,s in SCREWS_2D:
    carrier=carrier.cut(axial_cylinder(SCREW_CLEARANCE_R,11.9,15.6,x,s))
    carrier=carrier.cut(axial_cylinder(2.4 if x==0 else 2.1,15.5,30,x,s))
carrier=carrier.removeSplitter()

# 底面轮廓保持不变；加宽其上方过渡，避免前口下缘斜壁被内腔切成薄片。
# 外侧仍由投影圆柱裁切，整个过渡必须藏在原模块正面轮廓后方。
sections = [
    (0.0, FOOT_OUTER_RX, FOOT_OUTER_RY, FOOT_CENTER_Y),
    (2.0, 23.0, 24.0, FOOT_CENTER_Y),
    (6.0, 26.0, 25.0, 12.0),
    (12.0, 28.0, 28.0, 11.0),
    (20.0, 27.0, 27.0, 10.0),
    (28.0, 26.5, 24.0, 11.0),
    (35.0, 23.0, 19.0, 12.0),
    (40.0, 16.0, 13.0, 14.0),
    (43.0, 1.0, 1.0, 16.0),
]
rear = Part.makeLoft(
    [ellipse_wire(*section) for section in sections], True, False
)
# 从正面投影约束整个壳体，后方及底面也不能超出屏幕轮廓。
def projection_envelope(radius):
    return Part.makeCylinder(radius, 80, plate_point(0, 0, SHELL_MOUTH_N), -N)


rear = rear.common(projection_envelope(SHELL_PROJECTION_R))
outer_envelope = rear.copy()
above_floor = Part.makeBox(200, 200, 100, App.Vector(-100, -100, SHELL_FLOOR_T))
# 内腔跟随外壳，而非电池形状；截面退让约 3 mm 以补偿倾斜壁面。
inner_sections = [
    (SHELL_FLOOR_T, 17.4, 16.9, FOOT_CENTER_Y),
    (6.0, 20.4, 18.4, 12.0),
    (12.0, 22.4, 21.4, 11.0),
    (20.0, 24.0, 24.0, 10.0),
    (28.0, 23.5, 21.0, 11.0),
    (35.0, 20.0, 16.0, 12.0),
    (39.0, 13.0, 10.0, 14.0),
    (40.0, 1.0, 1.0, 16.0),
]
cavity = Part.makeLoft([ellipse_wire(*v) for v in inner_sections], True, False)
cavity = cavity.common(projection_envelope(SHELL_PROJECTION_R-FRONT_WALL_TARGET)).common(above_floor)
# 安装让位不能越过随外形退让的内腔，否则前口下缘会被圆柱切成薄片。
# 支架下缘为 s=-18；让位只覆盖支架实际存在的上部，保留下方斜壁。
mount_clearance = Part.makeCylinder(SHELL_INNER_R, 6.6, plate_point(0, 0, SHELL_MOUTH_N), -N)
mount_region = rectangle_face(-40, 40, -18.4, 40, SHELL_MOUTH_N).extrude(-N*6.6)
cavity = cavity.fuse(mount_clearance.common(mount_region).common(above_floor)).removeSplitter()
assert cavity.cut(outer_envelope).Volume < 0.01
rear = rear.cut(cavity)
print("connected cavity: solids=%d volume=%.1f mm3 bbox=%s" % (
    len(cavity.Solids), cavity.Volume, cavity.BoundBox))
assert len(cavity.Solids) == 1

# 检查常规侧壁的法向距离；前口开放面和底面不算侧壁。
skin_faces = []
for face in outer_envelope.Faces:
    points = [v.Point for v in face.Vertexes]
    on_mouth = all(abs((P - p).dot(N) - SHELL_MOUTH_N) < 0.01 for p in points)
    on_base = all(abs(p.z) < 0.01 for p in points)
    if not on_mouth and not on_base:
        skin_faces.append(face)
outer_skin = Part.makeCompound(skin_faces)
wall_samples = []
for z, rx, ry, cy in inner_sections[1:-1]:
    for i in range(0, 48, 3):
        a = 2 * math.pi * i / 48
        point = App.Vector(rx * math.cos(a), cy + ry * math.sin(a), z)
        if cavity.isInside(point, 0.01, True):
            wall_samples.append(outer_skin.distToShape(Part.Vertex(point))[0])
print("regular side wall sampled minimum=%.3f mm (%d points)" % (min(wall_samples), len(wall_samples)))
assert min(wall_samples) >= 1.95

# 中央只浅凹，不打穿；外侧保留 5 mm 宽的 360 度水平接触带。
underside_recess = Part.Face(ellipse_wire(
    -1.0, FOOT_INNER_RX, FOOT_INNER_RY, FOOT_CENTER_Y
)).extrude(Z * (1.0 + FOOT_RECESS))
rear = rear.cut(underside_recess)
rear = rear.removeSplitter()

# 三处定位槽的端面抵住支架，形成确定的轴向承压止挡。
guide_sockets = []
wall_audit_zones = []
for degrees,width in GUIDES:
    angle=math.radians(degrees)
    body=radial_strip(angle,19.1,23.4,width+3.0,CARRIER_BACK_N).extrude(-N*4.5).common(outer_envelope)
    socket=radial_strip(angle,20.35,22.85,width+0.5,16.9).extrude(-N*3.45)
    socket=socket.common(axial_cylinder(23.05,16.9,20.35))
    body=body.cut(socket)
    if degrees==90:
        # 顶部键加宽并分叉，留出原厂顶螺丝和两个插头的直线操作通路。
        body=body.cut(axial_box(-12,12,0,20.35,16.9,22))
        body=body.cut(axial_cylinder(2.4,15.5,30,0,20.5))
    rear=rear.fuse(body).cut(socket)
    guide_sockets.append(body)
    points=[v.Point for v in socket.Vertexes]
    local=[((v-P).dot(X),(v-P).dot(S),(P-v).dot(N)) for v in points]
    wall_audit_zones.append(tuple((min(v[k] for v in local)-.02,max(v[k] for v in local)+.02) for k in range(3)))

lock_seats=[]
for x,s in LOCK_POINTS:
    boss_clearance=rounded_rectangle_face(8.9,8.0,1.2,s,SHELL_MOUTH_N).extrude(-N*(19.25-SHELL_MOUTH_N))
    boss_clearance.translate(X*x)
    rear=rear.cut(boss_clearance)
    seat=axial_cylinder(3.7,19.25,LOCK_HEAD_SEAT,x,s)
    support=Part.makeBox(8,9,8,App.Vector(x-4,-2,SHELL_FLOOR_T)).common(outer_envelope)
    support=support.common(axial_box(-40,40,-40,-12.5,19.25,70))
    rear=rear.fuse(seat).fuse(support)
    rear=rear.cut(axial_cylinder(1.45,18.8,LOCK_HEAD_SEAT+.1,x,s))
    rear=rear.cut(axial_cylinder(2.65,LOCK_HEAD_SEAT,80,x,s))
    lock_seats.append(seat)
    wall_audit_zones.append(((x-4.2,x+4.2),(s-4.2,s+4.2),(13.8,80)))
rear=rear.removeSplitter()
for x,s in SCREWS_2D:
    assert carrier.common(axial_cylinder(2.0,15.5,30,x,s)).Volume<0.01,'原厂螺丝工具路径'

lock_heads=[axial_cylinder(2.25,LOCK_HEAD_SEAT,LOCK_HEAD_SEAT+2.5,x,s) for x,s in LOCK_POINTS]
lock_shafts=[axial_cylinder(1.25,LOCK_HEAD_SEAT-8,LOCK_HEAD_SEAT,x,s) for x,s in LOCK_POINTS]
lock_nuts=[hex_nut(x,s,14.7,16.7,5.0).cut(axial_cylinder(1.25,14.6,16.8,x,s)) for x,s in LOCK_POINTS]
lock_tools=[axial_cylinder(2.0,LOCK_HEAD_SEAT+2.5,80,x,s) for x,s in LOCK_POINTS]
print('完成止口和锁紧结构',flush=True)
for name,shape in [('carrier',carrier),('rear',rear)]:
    print('快速实体检查',name,shape.isValid(),len(shape.Solids),flush=True)
assert carrier.common(rear).Volume<0.01, '支架与后壳干涉'
for hardware in lock_heads+lock_shafts+lock_nuts+lock_tools:
    for name,shape in [('carrier',carrier),('rear',rear)]:
        assert hardware.common(shape).Volume<0.01, name+'挡紧固件或工具'
nut_insertion=[]
for nut in lock_nuts:
    for distance in (0,1,2,4,6,8,10):
        moved=nut.copy();moved.translate(S*distance)
        volume=moved.common(carrier).Volume
        assert volume<0.01,'螺母无法从内侧滑入'
        nut_insertion.append(volume)
contact=carrier.distToShape(rear)[0]
assert contact<0.0001,'轴向止挡未接触'
bottom_band=Part.Face(ellipse_wire(0,FOOT_OUTER_RX,FOOT_OUTER_RY,FOOT_CENTER_Y)).extrude(Z*.6)
bottom_band=bottom_band.cut(Part.Face(ellipse_wire(0,FOOT_INNER_RX,FOOT_INNER_RY,FOOT_CENTER_Y)).extrude(Z*.6))
for x,s in LOCK_POINTS:
    assert axial_cylinder(2.65,LOCK_HEAD_SEAT,80,x,s).common(bottom_band).Volume<0.001,'工具井切断底环'
assert min(v.z for head in lock_heads for v in head.tessellate(.05)[0])>FOOT_RECESS,'螺丝头碰桌面'
original_heads=[axial_cylinder(2.0,15.5,17.5,x,s) for x,s in SCREWS_2D]
for head in original_heads:
    assert head.common(carrier).Volume+head.common(rear).Volume<.01,'原厂螺丝头无空间'
stop_contacts=[carrier.distToShape(stop)[0] for stop in guide_sockets]
assert max(stop_contacts)<.0001,'有轴向止挡没有接触'

module_ref = Part.makeCylinder(
    MODULE_R, MODULE_DEPTH, plate_point(0, 0, MODULE_DEPTH), N
)
battery_ref = rounded_rectangle_face(
    BATTERY_W, BATTERY_H, BATTERY_CORNER_R,
    BATTERY_OFFSET_S, 17.6
).extrude(-N * BATTERY_T)
connector_refs = [
    rectangle_face(
        sx - 2.5, sx + 2.5,
        CONNECTOR_S - 2.0, CONNECTOR_S + 2.0,
        CARRIER_FRONT_N
    ).extrude(-N * 5.0)
    for sx in (-CONNECTOR_X, CONNECTOR_X)
]

# 插头插入包络和朝内收线空间，实际线束弯曲半径须实物确认。
connector_sweeps = [
    rectangle_face(sx - 2.9, sx + 2.9, CONNECTOR_S - 2.5,
                   CONNECTOR_S + 2.5, MODULE_DEPTH).extrude(-N * 10.0)
    for sx in (-CONNECTOR_X, CONNECTOR_X)
]
wire_refs = [
    rectangle_face(sx - 1.4, sx + 1.4, 15.0, CONNECTOR_S + 1.0,
                   18.0).extrude(-N * 3.0)
    for sx in (-CONNECTOR_X, CONNECTOR_X)
]
adhesive_ref = Part.makeBox(24, 16, 0.4, App.Vector(-12, 8, SHELL_FLOOR_T))
carrier_obj = add_feature(doc, "Mount_Carrier", carrier, (0.83, 0.84, 0.82))
rear_obj = add_feature(doc, "Rear_Cover", rear, (0.66, 0.69, 0.69))
add_feature(doc, "Module_Reference", module_ref, (0.08, 0.09, 0.10))
add_feature(doc, "Battery_Reference", battery_ref, (0.28, 0.65, 0.40), False)
for prefix, shapes, color in (
    ("Connector", connector_refs, (0.9, 0.75, 0.3)),
    ("Insertion", connector_sweeps, (0.95, 0.55, 0.2)),
    ("Wire", wire_refs, (0.8, 0.3, 0.2)),
):
    for index, shape in enumerate(shapes):
        add_feature(doc, "%s_%d_Reference" % (prefix, index + 1), shape, color, False)
add_feature(doc, "Adhesive_Area_Reference", adhesive_ref, (0.3, 0.6, 0.9), False)
for name,shapes in [('Lock_Heads',lock_heads),('Lock_Shafts',lock_shafts),
                    ('Lock_Nuts',lock_nuts),('Lock_Tools',lock_tools),('Original_Heads',original_heads)]:
    add_feature(doc,name+'_Reference',Part.makeCompound(shapes),(0.8,0.62,0.24),False)
doc.recompute()

for name, shape in (("carrier", carrier), ("rear", rear)):
    print("%s: valid=%s solids=%d volume=%.1f bbox=%s" % (
        name, shape.isValid(), len(shape.Solids), shape.Volume, shape.BoundBox
    ))
overlap = carrier.common(rear)
print("common: carrier/rear=%.3f module/rear=%.3f battery/rear=%.3f battery/carrier=%.3f" % (
    overlap.Volume, module_ref.common(rear).Volume,
    battery_ref.common(rear).Volume, battery_ref.common(carrier).Volume,
))
print("connector clearance:", [
    round(connector.common(carrier).Volume + connector.common(rear).Volume, 3)
    for connector in connector_refs
])
ring_samples = [
    rear.isInside(
        App.Vector(
            (FOOT_INNER_RX + 2.5) * math.cos(2 * math.pi * i / 72),
            FOOT_CENTER_Y + (FOOT_INNER_RY + 2.5) * math.sin(2 * math.pi * i / 72),
            0.1,
        ), 0.01, False
    )
    for i in range(72)
]
print("bottom: z_min=%.3f ring=%d/72 battery_z_min=%.3f" % (
    rear.BoundBox.ZMin, sum(ring_samples), battery_ref.BoundBox.ZMin
))
ring_width_passed = 0
for inset in (0.3, 1.25, 3.75, 4.7):
    for i in range(72):
        a = 2*math.pi*i/72
        point = App.Vector((FOOT_OUTER_RX-inset)*math.cos(a),
                           FOOT_CENTER_Y+(FOOT_OUTER_RY-inset)*math.sin(a), 0.1)
        ring_width_passed += rear.isInside(point, 0.01, False)
assert ring_width_passed == 288, '底部接触带宽度检查失败'

# 以模块 50 g、电池 15 g、PETG 1.27 g/cm3 估算重心和接触椭圆切线倾覆角。
petg_g_per_mm3 = 0.00127
parts = (
    (module_ref.Solids[0].CenterOfMass, 50.0),
    (battery_ref.Solids[0].CenterOfMass, 15.0),
    (carrier.Solids[0].CenterOfMass, carrier.Volume * petg_g_per_mm3),
    (rear.Solids[0].CenterOfMass, rear.Volume * petg_g_per_mm3),
)
total_mass = sum(mass for _, mass in parts)
center_of_mass = sum(
    (center * mass for center, mass in parts), App.Vector()
) / total_mass
tip_degrees = [
    math.degrees(math.atan2(margin, center_of_mass.z))
    for margin in (
        FOOT_OUTER_RY + center_of_mass.y - FOOT_CENTER_Y,
        FOOT_OUTER_RY - center_of_mass.y + FOOT_CENTER_Y,
        FOOT_OUTER_RX - abs(center_of_mass.x),
    )
]
tip_all_directions = [
    math.degrees(math.atan2(
        math.hypot(
            FOOT_OUTER_RX * math.cos(2 * math.pi * i / 72),
            FOOT_OUTER_RY * math.sin(2 * math.pi * i / 72),
        )
        - center_of_mass.x * math.cos(2 * math.pi * i / 72)
        - (center_of_mass.y - FOOT_CENTER_Y) * math.sin(2 * math.pi * i / 72),
        center_of_mass.z,
    ))
    for i in range(72)
]
print("mass=%.1f g center=%s tip(front/rear/side)=%s" % (
    total_mass, center_of_mass,
    "/".join("%.1f" % angle for angle in tip_degrees)
))
print("minimum tip angle (72 directions)=%.1f" % min(tip_all_directions))

assert carrier.isValid() and len(carrier.Solids) == 1
assert rear.isValid() and len(rear.Solids) == 1
print("actual bottom", min(v.z for v in rear.tessellate(0.05)[0]))
assert abs(min(v.z for v in rear.tessellate(0.05)[0])) < 0.01 and all(ring_samples)
assert rear.isInside(App.Vector(0, FOOT_CENTER_Y, 1.0), 0.01, False)
assert overlap.Volume < 0.01
assert module_ref.common(rear).Volume < 0.01
assert battery_ref.common(rear).Volume < 0.01
assert battery_ref.common(carrier).Volume < 0.01
assert all(
    connector.common(carrier).Volume + connector.common(rear).Volume < 0.01
    for connector in connector_refs
)
assert min(tip_all_directions) >= 30.0

for shape in connector_sweeps + wire_refs:
    print("insertion/wire common", shape.common(carrier).Volume, shape.common(rear).Volume)
    assert shape.common(carrier).Volume + shape.common(rear).Volume < 0.01
    assert shape.common(battery_ref).Volume < 0.01
closing_checks = []
for travel in (0, 0.25, 0.5, 1.0, 2.0, 3.0, 4.0, 8.0, 12.0, 20.0):
    moving_cover = rear.copy()
    moving_cover.translate(-N * travel)
    assert all(moving_cover.common(v).Volume < 0.01 for v in connector_refs + wire_refs)
    rigid_overlap = moving_cover.common(carrier).Volume
    print("closing travel=%.1f rigid carrier common=%.3f" % (travel, rigid_overlap))
    if rigid_overlap>=0.01:
        for solid in moving_cover.common(carrier).Solids:
            c=solid.CenterOfMass-P
            print('合盖干涉位置',solid.Volume,c.x,c.dot(S),-c.dot(N),flush=True)
    assert rigid_overlap < 0.01
    assert moving_cover.common(battery_ref).Volume < 0.01
    closing_checks.append({"travel_mm":travel,"carrier_overlap_mm3":rigid_overlap})
print("insertion and closing connector clearance: passed")
assert adhesive_ref.common(rear).Volume < 0.01

# 检查前口真实截线；BRep 的控制点包围盒会偏大，尺寸用离散表面计算。
mouth_section = outer_envelope.section(rectangle_face(-80, 80, -80, 80, SHELL_MOUTH_N))
mouth_radii = []
for edge in mouth_section.Edges:
    for point in edge.discretize(60):
        delta = point - plate_point(0, 0, SHELL_MOUTH_N)
        mouth_radii.append(math.hypot(delta.dot(X), delta.dot(S)))
assert mouth_radii and max(mouth_radii) <= MODULE_R + 0.01
rear_points = rear.tessellate(0.02)[0]
cavity_points = cavity.tessellate(0.02)[0]
projection_radii = [
    math.hypot((point - P).dot(X), (point - P).dot(S))
    for point in rear_points + carrier.tessellate(0.02)[0]
]
assert max(projection_radii) <= SHELL_PROJECTION_R + 0.001
assert rear.cut(projection_envelope(SHELL_PROJECTION_R)).Volume < 0.01
print("entire stand front projection maximum radius=%.4f mm" % max(projection_radii))
actual_box = App.BoundBox()
cavity_box = App.BoundBox()
for point in rear_points:
    actual_box.add(point)
for point in cavity_points:
    cavity_box.add(point)
print("actual shell bbox", actual_box)
print("actual cavity bbox", cavity_box)
print("mouth maximum radius=%.4f mm" % max(mouth_radii))
metrics = {
    "stand_front_projection_max_radius_mm": max(projection_radii),
    "front_occlusion_margin_mm": MODULE_R - max(projection_radii),
    "locking_screws": "2 × M2.5×8 内六角圆柱头",
    "nut_across_flats_mm":5.0,
    "nut_pocket_across_flats_mm":5.2,
    "nut_shoulder_mm":LOCK_BOSS_BACK-LOCK_NUT_BACK,
    "guide_engagement_mm":3.0,
    "guide_clearance_mm":GUIDE_CLEARANCE,
    "guide_widths_mm":[v[1] for v in GUIDES],
    "guide_top_shape":"分叉式宽键，让开顶螺丝轴线",
    "lock_points_mm":LOCK_POINTS,
    "nut_slot_entry_width_mm":6.1,
    "nut_slot_side_wall_mm":1.2,
    "nut_insertion_max_overlap_mm3":max(nut_insertion),
    "axial_stop_contact_distances_mm":stop_contacts,
    "tool_well_diameter_mm":5.3,
    "screw_head_seat_n_mm":LOCK_HEAD_SEAT,
    "carrier_ring_width_mm":CARRIER_OUTER_R-CARRIER_INNER_R,
    "closing_checks":closing_checks,
    "mouth_max_radius_mm": max(mouth_radii),
    "axial_joint_clearance_mm": SHELL_MOUTH_N - MODULE_DEPTH,
    "cavity_volume_cm3": cavity.Volume / 1000,
    "cavity_after_carrier_cm3": outer_envelope.cut(rear).cut(carrier).common(above_floor).Volume / 1000,
    "shell_bbox_mm": [actual_box.XLength, actual_box.YLength, actual_box.ZLength],
    "cavity_bbox_mm": [cavity_box.XLength, cavity_box.YLength, cavity_box.ZLength],
    "sampled_side_wall_min_mm": min(wall_samples),
    "side_wall_sample_count": len(wall_samples),
    "bottom_z_mm": actual_box.ZMin,
    "bottom_contact_samples_passed": sum(ring_samples),
    "bottom_ring_width_samples_passed": ring_width_passed,
    "minimum_tip_angle_without_speaker_deg": min(tip_all_directions),
    "speaker_fitted": False,
    "wire_bend_requires_physical_check": True,
}

# 预览辅助网格只存在本地 archive，参考体不混入打印文件。
preview_dir = os.path.join(SCRIPT_DIR, "archive", "preview_meshes")
os.makedirs(preview_dir, exist_ok=True)
section_shape = rear.common(Part.makeBox(100, 200, 100, App.Vector(0, -100, 0)))
for name, shape in (("section", section_shape), ("battery_reference", battery_ref),
                    ("connector_reference", Part.makeCompound(connector_refs)),
                    ("wire_reference", Part.makeCompound(wire_refs)),
                    ("carrier_reference", carrier), ("adhesive_reference", adhesive_ref),
                    ("fasteners",Part.makeCompound(lock_heads+lock_shafts+lock_nuts))):
    mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.1, AngularDeflection=0.3)
    mesh.write(os.path.join(preview_dir, name + ".stl"))

fit_dir=os.path.join(SCRIPT_DIR,'archive','fit_samples')
os.makedirs(fit_dir,exist_ok=True)
samples={'nut_pocket':carrier.common(axial_box(-12,-2,-21,-7,13.8,19)),
         'guide_tongue':carrier.common(axial_box(19,24,-6,6,12.1,20.1)),
         'guide_socket':rear.common(axial_box(19,25.2,-6,6,16.5,22))}
for name,shape in samples.items():
    assert shape.isValid() and len(shape.Solids)==1,'试装件不连通：'+name
    shape=shape.copy()
    shape.Placement=App.Placement(App.Vector(),App.Rotation(-N,Z)).multiply(shape.Placement)
    shape.translate(App.Vector(0,0,-min(v.z for v in shape.tessellate(.05)[0])))
    mesh=MeshPart.meshFromShape(Shape=shape,LinearDeflection=.05,AngularDeflection=.3,Relative=False)
    assert mesh.isSolid() and len(mesh.getSeparateComponents())==1,'试装网格不闭合：'+name
    mesh.write(os.path.join(fit_dir,name+'.stl'))

export_stl(carrier, "mount_carrier.stl", lay_flat=True)
export_stl(rear, "rear_cover.stl")
metrics['front_wall_mesh_audit'] = audit_front_wall(os.path.join(OUT_DIR,'rear_cover.stl'))
metrics['front_wall_target_mm'] = FRONT_WALL_TARGET
metrics['mounting_clearance_radial_mm'] = SHELL_INNER_R-CARRIER_OUTER_R
Part.export([carrier_obj, rear_obj], os.path.join(OUT_DIR, "stand.step"))
step_shape = Part.read(os.path.join(OUT_DIR, "stand.step"))
print("STEP: valid=%s solids=%d" % (
    step_shape.isValid(), len(step_shape.Solids)
))
assert step_shape.isValid() and len(step_shape.Solids) == 2
with open(os.path.join(OUT_DIR, "validation.json"), "w", encoding="utf-8") as stream:
    json.dump(metrics, stream, ensure_ascii=False, indent=2)
configure_display(doc)
doc.saveAs(os.path.join(OUT_DIR, "stand.FCStd"))
print("Exported to:", OUT_DIR)
