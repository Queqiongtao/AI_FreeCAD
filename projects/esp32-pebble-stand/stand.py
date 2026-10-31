"""ESP32-S3-Touch-AMOLED-1.75-B 成品模块的鹅卵石桌面底座。

模块背面的三颗原厂螺丝固定支架；后壳由上侧双刚性旋扣及下侧两颗 M3 锁紧。
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
OUT_DIR = os.environ.get('S3_OUTPUT_DIR', os.path.join(SCRIPT_DIR, "output"))
PREVIEW_DIR = os.environ.get('S3_PREVIEW_DIR', os.path.join(SCRIPT_DIR, 'archive', 'preview_meshes'))
FIT_DIR = os.environ.get('S3_FIT_DIR', os.path.join(SCRIPT_DIR, 'archive', 'fit_samples'))

# 模块是带原厂外壳的成品，不是裸 PCB。
MODULE_R = 25.5
MODULE_DEPTH = 12.1
TILT_DEG = 40.0
MODULE_BOTTOM_CLEARANCE = 5.1
SHELL_DEPTH_EXTENSION = 4.0  # 模块沿前向法线移位，竖直抬高约 3.06 mm
SHELL_REAR_BULGE = 8.0  # 后部曲线扩展量，实际外形仍受正面投影约束
FRONT_TRANSITION_EXTRA = 3.0  # 前口下缘加厚；底环尺寸保持，正面仍受模块轮廓裁切
INNER_FRONT_RETREAT = 1.2  # 下缘内腔小幅后退，保证让位盲端与主内腔之间的实体厚度
SCREWS_2D = [(0.0, 20.50), (13.75, -14.70), (-13.75, -14.70)]
SCREW_CLEARANCE_R = 1.15  # M2 初始值，打印前用原厂螺丝核对

BATTERY_W = 36.0
BATTERY_H = 26.0
BATTERY_T = 8.0
BATTERY_CORNER_R = 3.0
BATTERY_OFFSET_S = 1.0
BATTERY_OFFSET_X = 0.0
BATTERY_FRONT_N = 17.6

# 内部布局试排参数，单位 mm；位置沿模块的 x / s / n 坐标定义。
# 扬声器振膜位于 FRONT_N，朝向后壳；倾角为相对模块背向法线的偏转。
SPEAKER_W = 30.0
SPEAKER_H = 20.0
SPEAKER_THICKNESS = 7.0
SPEAKER_CORNER_R = 0.2  # 未知实物圆角，近似完整矩形包络，不利用圆角挤空间
SPEAKER_OFFSET_X = -1.5
SPEAKER_OFFSET_S = 3.0
SPEAKER_FRONT_N = 33.5
SPEAKER_TILT_DEG = 0.0
SPEAKER_TAPE_T = 0.8
SPEAKER_TAPE_RING_W = 0.8
SPEAKER_TAPE_CORNER_LENGTH = 4.0
SPEAKER_HARD_EDGE = 1.0
SPEAKER_LOCATOR_GAP = 0.3
SPEAKER_LOCATOR_T = 1.6
SPEAKER_LOCATOR_LENGTH = 4.0
SPEAKER_FRONT_GAP = 1.0
SPEAKER_WIRE_GAP = 3.0
SPEAKER_SIDE_GAP = 1.0
SPEAKER_PAD_BORDER = 2.5
SPEAKER_GRILLE_ENABLED = True
SPEAKER_SLOT_COUNT = 5
SPEAKER_SLOT_W = 1.6
SPEAKER_SLOT_H = 6.0
SPEAKER_SLOT_WEB = 1.6
SPEAKER_SLOT_OFFSET_S = -5.8  # 声道投向底环内侧，避开连续接触带
SPEAKER_SLOT_OFFSET_X = 1.5
SPEAKER_CABLE_DIAMETER = 2.0  # 线束暂定包络，实际线径和弯曲半径需实物确认
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
CARRIER_LOCK_WEB_BACK = 17.7
CARRIER_LOCK_WEB_W = 4.4
UPPER_BEAM_W = 3.2
UPPER_BEAM_S = 12.5
UPPER_BEAM_FRONT_N = 13.9
UPPER_BEAM_HALF_SPAN = 17.6
UPPER_NOTCH_R = .8
SHELL_MOUTH_N = MODULE_DEPTH + 0.3
SHELL_PROJECTION_R = 25.2
SHELL_INNER_R = 23.1
MOUNT_CLEARANCE_DEPTH = 5.6  # 让开 n=17.7 mm 的连接筋并留 0.3 mm，避免盲端窄膜
SHELL_FLOOR_T = 2.6
FRONT_WALL_TARGET = 2.4
FOOT_CENTER_Y = 14.0
FOOT_OUTER_RX = 20.5
FOOT_OUTER_RY = 20.0
FOOT_INNER_RX = 15.5
FOOT_INNER_RY = 15.0
FOOT_RECESS = 0.6

GUIDES = ()  # 旧直插键不适用于旋转解锁
GUIDE_CLEARANCE = 0.25
GUIDE_END_N = 20.1
LOCK_POINTS = ((-5.0, -16.0), (5.0, -16.0))  # M3 工具井向中间避让完整底环
LOCK_INSERT_LENGTH = 3.0
LOCK_INSERT_OD = 4.0
LOCK_INSERT_BORE = 3.8
LOCK_INSERT_DEPTH = 3.4
LOCK_SCREW_LENGTH = 6.0
LOCK_CLEARANCE_R = 1.7
LOCK_TOOL_R = 3.1
LOCK_BOSS_BACK = 19.0
LOCK_HEAD_SEAT = 21.5

# 肩部双刚性旋扣；不采用弹性卡扣。沿屏幕法线小角度旋转后，直线取下。
HOOK_ANGLES = (61.0,135.0)
HOOK_RELEASE_DEG = 9.0
HOOK_PULL_MM = 50.0
HOOK_ROOT_T = 3.2
HOOK_CLEARANCE = 0.30
HOOK_FILLET_R = 1.2
HOOK_LUG_FRONT_N = 20.1
HOOK_LUG_BACK_N = HOOK_LUG_FRONT_N+HOOK_ROOT_T
HOOK_LUG_WIDTH = 3.2
HOOK_COVER_WIDTH = 4.0
HOOK_AXIAL_OFFSETS = (3.0,9.3)  # 左侧承压面位于电池后方，避免钩翼被削成薄边
HOOK_RADIAL_INNERS = (19.6,18.8)  # 较高的左立柱加宽径向截面
HOOK_INNER_R = 19.6
HOOK_OUTER_R = HOOK_INNER_R+HOOK_ROOT_T

TILT = math.radians(TILT_DEG)
SIN = math.sin(TILT)
COS = math.cos(TILT)
X = App.Vector(1, 0, 0)
Y = App.Vector(0, 1, 0)
Z = App.Vector(0, 0, 1)
N = App.Vector(0, -SIN, COS)
S = App.Vector(0, COS, SIN)
P = App.Vector(0, 0, MODULE_BOTTOM_CLEARANCE + MODULE_R * SIN + MODULE_DEPTH * COS)
P = P + N*SHELL_DEPTH_EXTENSION


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


def deepen_section(section):
    """底板保持原位，上部平滑升高，为轴向加深后的模块和内腔让位。"""
    z,rx,ry,cy=section
    weight=max(0.0,min(1.0,(z-SHELL_FLOOR_T)/17.4))
    bulge=SHELL_REAR_BULGE*max(0.0,min(1.0,(z-SHELL_FLOOR_T)/9.4))/2
    return z+SHELL_DEPTH_EXTENSION*COS*weight,rx,ry+bulge,cy+bulge


def outer_section(section):
    z,rx,ry,cy=deepen_section(section)
    weight=max(0.0,min(1.0,section[0]/6.0,(28.0-section[0])/16.0))
    delta=FRONT_TRANSITION_EXTRA*weight/2
    return z,rx,ry+delta,cy-delta


def inner_section(section):
    z,rx,ry,cy=deepen_section(section)
    weight=max(0.0,min(1.0,section[0]/6.0,(28.0-section[0])/16.0))
    delta=INNER_FRONT_RETREAT*weight/2
    return z,rx,ry-delta,cy+delta


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


def shoulder_box(angle,r0,r1,t0,t1,n0,n1):
    a=math.radians(angle)
    u=X*math.cos(a)+S*math.sin(a);v=-X*math.sin(a)+S*math.cos(a)
    face=polygon_face([plate_point(0,0,n0)+u*r+v*t for r,t in
                       [(r0,t0),(r1,t0),(r1,t1),(r0,t1)]])
    return face.extrude(-N*(n1-n0))


def hook_pose(shape,angle=0,pull=0):
    moved=shape.copy(True);moved.rotate(P,N,angle);moved.translate(-N*pull)
    return moved


def rotation_sweep(shape,angle):
    """旋转每个边界面，求实体的连续旋转包络；不用离散姿态拼接导槽。"""
    pieces=[shape.copy(True),hook_pose(shape,angle)]
    far=App.Vector(1000,1000,1000)
    for face in shape.Faces:
        swept=face.copy(True).revolve(P,N if angle>0 else -N,abs(angle))
        if swept.isValid() and abs(swept.Volume)>1e-7:
            if swept.isInside(far,1e-7,False):swept.reverse()
            pieces.append(swept)
    independent=[piece.copy(True) for piece in pieces]
    raw=independent[0].multiFuse(independent[1:])
    result=raw.removeSplitter()
    for candidate in (result,raw):
        if candidate.isValid() and len(candidate.Solids)==1:
            try:candidate.check(True)
            except ValueError:continue
            return candidate
    # 多个扫掠体相切时并集整理可能退化；保留每个有效体，逐体相减等价于减去并集。
    result=Part.makeCompound(pieces)
    assert result.isValid(),'连续旋转包络包含无效扫掠体'
    return result


def subtract_sweep(shape,tool):
    if len(tool.Solids)==1:return shape.cut(tool)
    result=shape
    for solid in tool.Solids:result=result.cut(solid)
    return result.removeSplitter()


def add_upper_hooks(frame,cover,envelope):
    hooks=[];lugs=[]
    limit=axial_cylinder(SHELL_INNER_R,12,40)
    g,thick=HOOK_CLEARANCE,HOOK_ROOT_T
    half=HOOK_LUG_WIDTH/2
    stem_hi=-half-2*g;stem_lo=stem_hi-thick
    # 加宽扣头后，钩翼入口必须仍能在 9° 时完全退出，不能沿用旧窄扣头的入口边。
    release=math.radians(HOOK_RELEASE_DEG)
    front,back=HOOK_LUG_FRONT_N,HOOK_LUG_BACK_N
    fillet=HOOK_FILLET_R
    assert 0<fillet<=thick/2
    for index,angle in enumerate(HOOK_ANGLES):
        r0,r1=HOOK_RADIAL_INNERS[index],HOOK_OUTER_R
        offset=HOOK_AXIAL_OFFSETS[index]
        tip_lo=half*math.cos(release)-r0*math.sin(release)+g
        tip_hi=tip_lo+HOOK_COVER_WIDTH
        def b(r0,r1,t0,t1,n0,n1):
            return shoulder_box(angle,r0,r1,t0,t1,n0+offset,n1+offset)
        # 两个支柱均位于局部负切向侧，故同一次旋转可同时退出两个挂接。
        lug=b(r0,r1,stem_lo,half,front,back).common(limit)
        post=shoulder_box(angle,r0,r1,stem_lo,stem_hi,CARRIER_PAD_FRONT_N,front+fillet+offset).common(limit)
        post=post.cut(axial_box(-30,30,-30,14.3,17.3,40))
        lug=lug.cut(axial_box(-30,30,-30,14.3,17.3,40))
        for sx in (-CONNECTOR_X,CONNECTOR_X):
            post=post.cut(axial_box(sx-2.9,sx+2.9,14.45,20.05,12,22.4))
        # 显式圆弧补料构造 R1 内角，避免短边/圆柱裁边导致自动圆角失败。
        a=math.radians(angle)
        u=X*math.cos(a)+S*math.sin(a);v=-X*math.sin(a)+S*math.cos(a)
        gusset=polygon_face([plate_point(0,0,n)+u*r0+v*t for t,n in
            [(stem_hi,CARRIER_BACK_N-.6),(stem_hi+fillet,CARRIER_BACK_N-.6),
             (stem_hi,CARRIER_BACK_N+thick)]]).extrude(u*(r1-r0)).common(limit)
        root=b(r0,r1,stem_hi,stem_hi+fillet,front-fillet,front)
        cutter=Part.makeCylinder(fillet,thick+2*g,
            plate_point(0,0,front-fillet+offset)+u*(r0-g)+v*(stem_hi+fillet),u)
        root=root.cut(cutter).common(limit)
        bracket=post.fuse(lug).fuse(root).fuse(gusset).removeSplitter()
        assert bracket.isValid() and len(bracket.Solids)==1
        frame=frame.fuse(bracket)
        # 两翼、周边壳壁构成刚性扣。内侧和入口均开放，可直接清理支撑。
        hook=b(r0,27,tip_lo,tip_hi,front-g-thick,front-g).fuse(
            b(r0,27,tip_lo,tip_hi,back+g,back+g+thick)).fuse(
            b(r1+g,27,tip_lo,tip_hi,front-g-thick,back+g+thick)).common(envelope)
        for sx in (-CONNECTOR_X,CONNECTOR_X):
            hook=hook.cut(axial_box(sx-2.9,sx+2.9,14.45,20.05,12,front+offset))
        # 与扣头下缘一致地截平钩翼，避免喇叭包络在钩翼上切出薄片。
        hook=hook.cut(axial_box(-30,30,-30,14.3,17.3,40))
        air=b(r0-g,r1+g,stem_lo-g,half+g,front-g,back+g)
        # 根部圆角让位；0.3 mm 间隙不能被清理不到的封闭支撑占用。
        post_air=shoulder_box(angle,r0-g,r1+g,stem_lo-g,stem_hi+g,CARRIER_PAD_FRONT_N-g,back+g+offset)
        root_air=b(r0-g,r1+g,stem_hi+g,stem_hi+fillet+g,front-fillet-g,front+g)
        base_air=shoulder_box(angle,r0-g,r1+g,stem_hi-g,stem_hi+fillet+g,
            CARRIER_BACK_N-.6-g,CARRIER_BACK_N+thick+g)
        air=air.fuse(post_air).fuse(root_air).fuse(base_air).common(axial_cylinder(23.1,13,40))
        sweep=rotation_sweep(air,-HOOK_RELEASE_DEG)
        cover=subtract_sweep(cover,sweep)
        hook=subtract_sweep(hook,sweep)
        cover=cover.fuse(hook)
        hooks.append(hook);lugs.append(lug)
    # 左右短承压垫在环背面滑动；不再使用妨碍旋转的长定位舌。
    stops=[]
    for angle in (0,180):
        pad=shoulder_box(angle,20.4,24.5,-3,3,17.1,19.5).common(envelope)
        cover=cover.fuse(pad);stops.append(pad)
    battery_air=rounded_rectangle_face(BATTERY_W+.6,BATTERY_H+.6,BATTERY_CORNER_R,
        BATTERY_OFFSET_S,BATTERY_FRONT_N-.3).extrude(-N*(BATTERY_T+.6))
    battery_air.translate(X*BATTERY_OFFSET_X)
    cover=subtract_sweep(cover,rotation_sweep(battery_air,-HOOK_RELEASE_DEG))
    for x,s in SCREWS_2D:
        head_air=axial_cylinder(2.4 if x==0 else 2.3,15.5,17.8,x,s)
        cover=subtract_sweep(cover,rotation_sweep(head_air,-HOOK_RELEASE_DEG))
    for sx in (-CONNECTOR_X,CONNECTOR_X):
        # 加粗前翼接近收线区，避让整个解锁行程，而不只检查锁定姿态。
        # 避让贯通前翼厚度，不能在收线区上方留下薄台阶。
        wire_air=axial_box(sx-1.7,sx+1.7,14.7,CONNECTOR_S+1.3,17.7,
            max(21.3,front+min(HOOK_AXIAL_OFFSETS)))
        cover=subtract_sweep(cover,rotation_sweep(wire_air,-HOOK_RELEASE_DEG))
    return frame.removeSplitter(),cover.removeSplitter(),hooks,lugs,stops


def verify_hook_motion(frame,cover,speaker,parts,lugs,shafts,stops):
    """连续旋转/平移扫掠；端面滑动接触用半空间分隔，退化面用净距界证明。"""
    # OCC 布尔可能更新共享曲面的 p-curve/容差；运动验证不得污染交付实体。
    frame,cover,speaker=[shape.copy(True) for shape in (frame,cover,speaker)]
    parts=[shape.copy(True) for shape in parts]
    lugs=[shape.copy(True) for shape in lugs]
    shafts=[shape.copy(True) for shape in shafts]
    stops=[shape.copy(True) for shape in stops]
    moving=Part.makeCompound([cover,speaker])
    fixed=Part.makeCompound([frame]+parts)
    assert moving.common(fixed).Volume<1e-5
    front_space=axial_box(-100,100,-100,100,SHELL_MOUTH_N,100)
    parts=[Part.makeCompound(p.common(front_space).Solids) for p in parts]
    parts=[p for p in parts if p.Solids]
    fixed=Part.makeCompound([Part.makeCompound(frame.common(front_space).Solids)]+parts)
    radial_boundary=23.1
    radial_space=axial_cylinder(radial_boundary,SHELL_MOUTH_N-.01,100)
    assert fixed.cut(radial_space).Volume<1e-6,'固定件超出旋转安全圆柱'
    max_n=max((P-v).dot(N) for v in fixed.tessellate(.1)[0])
    # 绕法线旋转不改变 n，后拉只增加 n；后方部分不可能碰到任何固定件。
    intervals=[];evaluations=0;face_count=0
    far=App.Vector(1000,1000,1000)
    def certify(face,index,lo,hi,rot,obstacles,depth=0):
        nonlocal evaluations
        surface=face.Surface
        if isinstance(surface,Part.Cylinder) and abs(surface.Axis.dot(N))>1-1e-8 and \
            (surface.Center-P).cross(N).Length<1e-6 and surface.Radius>=radial_boundary-1e-7:
            intervals.append((index,'rotate' if rot else 'pull',lo,hi,'invariant_radial_boundary'));return
        middle=(lo+hi)/2
        center=hook_pose(face,middle if rot else HOOK_RELEASE_DEG,0 if rot else middle)
        b=face.BoundBox
        radius=max((App.Vector(x,y,z)-P).Length for x in (b.XMin,b.XMax)
                   for y in (b.YMin,b.YMax) for z in (b.ZMin,b.ZMax))
        bound=2*radius*math.sin(math.radians(hi-lo)/4) if rot else (hi-lo)/2
        distance=center.distToShape(obstacles)[0];evaluations+=1
        if distance>bound+1e-5:
            intervals.append((index,'rotate' if rot else 'pull',lo,hi,'distance_bound'));return
        pose=hook_pose(face,lo if rot else HOOK_RELEASE_DEG,0 if rot else lo)
        # 面在自身平面内旋转，由始末面与边界扫掠覆盖连续区域。
        planar=rot and isinstance(surface,Part.Plane) and abs(surface.Axis.dot(N))>1-1e-8
        if planar:
            pieces=[pose,hook_pose(face,hi)]+[e.copy(True).revolve(P,N,hi-lo) for e in pose.Edges]
            if all(p.isValid() and p.common(obstacles.copy(True)).Area<1e-7 for p in pieces):
                intervals.append((index,'rotate',lo,hi,'planar_boundary_sweep'));return
        else:
            swept=pose.revolve(P,N,hi-lo) if rot else pose.extrude(-N*(hi-lo))
            if swept.isValid() and swept.Faces:
                if swept.Solids and abs(swept.Volume)>1e-8:
                    if swept.isInside(far,1e-7,False):swept.reverse()
                    cross=swept.common(obstacles.copy(True))
                    if cross.Volume<1e-7:
                        intervals.append((index,'rotate' if rot else 'pull',lo,hi,'exact_volume_sweep'));return
                elif not swept.Solids and swept.common(obstacles.copy(True)).Area<1e-7:
                    intervals.append((index,'rotate' if rot else 'pull',lo,hi,'exact_surface_sweep'));return
        if evaluations%100==0:print('连续净距细分',index,lo,hi,distance,flush=True)
        assert depth<18,'连续装拆无法证明净距：'+str((index,lo,hi,distance))
        certify(face,index,lo,middle,rot,obstacles,depth+1)
        certify(face,index,middle,hi,rot,obstacles,depth+1)
    for lower,upper in ((SHELL_MOUTH_N-.001,CARRIER_BACK_N),(CARRIER_BACK_N,max_n+.1)):
        region=axial_box(-100,100,-100,100,lower,upper)
        source=moving
        if lower!=CARRIER_BACK_N:
            # 止挡属于上半空间，先去除它们，避免截平面生成没有厚度的接触翼面。
            source=Part.makeCompound([cover.cut(Part.makeCompound(stops)),speaker])
        bodies=[solid for solid in source.common(region).common(radial_space).Solids if solid.Volume>1e-7]
        band=Part.makeCompound(bodies)
        if lower==CARRIER_BACK_N:
            # 侧止挡 n>=17.1，环背端 n<=17.1；允许端面滑动，禁止体积穿透。
            # 取 Solids 去掉环截面上没有厚度的面，不删任何正体积固定结构。
            fixed_frame=Part.makeCompound(frame.common(region).Solids)
        else:fixed_frame=frame
        obstacles=Part.makeCompound([fixed_frame]+parts)
        for face in band.Faces:
            # 用包含整个行程的保守局部包围盒裁剪固定件，加速精确布尔及净距。
            local=face.copy(True)
            local.translate(-P)
            local.Placement=App.Placement(App.Vector(),App.Rotation(N,Z)).multiply(local.Placement)
            bb=local.BoundBox
            radius=max(math.hypot(x,y) for x in (bb.XMin,bb.XMax) for y in (bb.YMin,bb.YMax))
            margin=2*radius*math.sin(math.radians(HOOK_RELEASE_DEG)/2)+.001
            region=axial_box(bb.XMin-margin,bb.XMax+margin,bb.YMin-margin,bb.YMax+margin,
                             -bb.ZMax-.001,-bb.ZMin+HOOK_PULL_MM+.001)
            nearby=Part.makeCompound(obstacles.common(region).Solids)
            if nearby.Solids:
                certify(face,face_count,0,HOOK_RELEASE_DEG,True,nearby)
                certify(face,face_count,0,HOOK_PULL_MM,False,nearby)
            else:
                intervals.append((face_count,'both',0,HOOK_PULL_MM,'conservative_box_disjoint'))
            face_count+=1
            if face_count%20==0:print('连续装拆已证明面',face_count,flush=True)
    retention=[]
    for lug in lugs:
        volumes=[hook_pose(cover,0,t).common(lug).Volume for t in (1,2)]
        assert min(volumes)>1,'上侧挂接没有形成足够的机械防脱交叠'
        retention.append(volumes)
    locked=hook_pose(cover,1).common(Part.makeCompound(shafts)).Volume
    assert locked>.001,'螺丝未能阻止误旋转'
    return {'continuous_path_certified':True,'release_angle_deg':HOOK_RELEASE_DEG,
            'pull_mm':HOOK_PULL_MM,'certified_faces':face_count,'interval_count':len(intervals),
            'distance_evaluations':evaluations,'intervals':intervals,
            'retention_overlap_at_1_2_mm3':retention,'locked_rotation_overlap_mm3':locked,
            'method':'连续精确旋转/平移扫掠；退化面采用距离和位移界；环背面接触按 n 半空间分隔',
            'physical_fit_verified':False}


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
            App.Vector(), App.Rotation(-N, Z)
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
    # 高度分桶只减少候选三角形，仍执行同一包围框和精确射线判定。
    by_height={}
    for index,triangle in enumerate(triangles):
        for band in range(math.floor((triangle[4][2]-1e-6)/2),math.floor((triangle[5][2]+1e-6)/2)+1):
            by_height.setdefault(band,[]).append(index)
    angle=TILT; N=(0,-SIN,COS); S=(0,COS,SIN); P=(0,-SIN*SHELL_DEPTH_EXTENSION,MODULE_BOTTOM_CLEARANCE+MODULE_R*SIN+MODULE_DEPTH*COS+COS*SHELL_DEPTH_EXTENSION)
    measured=[]
    for i,(norm,a,e1,e2,lo,hi,center) in enumerate(triangles):
        n=dot(sub(P,center),N);s=dot(sub(center,P),S)
        if not (SHELL_MOUTH_N-0.01<=n<=20 or center[2]<14) or abs(dot(norm,N))>.99 or abs(norm[2])>.99:continue
        direction=tuple(-v for v in norm);start=tuple(center[k]+norm[k]*.005 for k in range(3));end=tuple(start[k]+direction[k]*8 for k in range(3))
        raylo=tuple(min(start[k],end[k]) for k in range(3));rayhi=tuple(max(start[k],end[k]) for k in range(3))
        hits=[]
        candidates=set()
        for band in range(math.floor((raylo[2]-1e-6)/2),math.floor((rayhi[2]+1e-6)/2)+1):
            candidates.update(by_height.get(band,[]))
        for candidate in candidates:
            _,b,f1,f2,low,high,_=triangles[candidate]
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
            'excluded':'开放端面、水平底面，以及穿过已单独检查的定位槽、紧固件、喇叭胶框及定位墙包络的射线；0.01 mm 合并同一表面交点',
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
            obj.ViewObject.DiffuseColor = [colors[obj.Name]] * len(obj.Shape.Faces)
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
    # 插头缺口贯通外缘，不留下约 1 mm 的细桥；由下方加强梁承担连接载荷。
    carrier = carrier.cut(rectangle_face(
        sx - CONNECTOR_W / 2, sx + CONNECTOR_W / 2,
        CONNECTOR_S - CONNECTOR_H / 2, 40,
        CARRIER_BACK_N + 0.5
    ).extrude(N * (CARRIER_BACK_N - CARRIER_FRONT_N + 1.0)))
carrier = carrier.removeSplitter()
# 给贯通缺口的竖向棱倒圆；只减料，不侵入插头的矩形安装包络。
notch_edges=[]
for edge in carrier.Edges:
    if len(edge.Vertexes)!=2:continue
    a,b=[v.Point for v in edge.Vertexes]
    d=b-a
    if d.cross(N).Length>1e-6 or abs(d.Length-(CARRIER_BACK_N-CARRIER_PAD_FRONT_N))>1e-5:continue
    center=(a+b)*.5-P
    if center.dot(S)>19.75 and min(abs(abs(center.x)-v) for v in (CONNECTOR_X-CONNECTOR_W/2,CONNECTOR_X+CONNECTOR_W/2))<1e-5:
        notch_edges.append(edge)
if notch_edges:
    carrier=carrier.makeFillet(UPPER_NOTCH_R,notch_edges)
# 加强梁在电池前方，中央短筋从两个插头之间连接顶部原厂螺丝座。
upper_beam=axial_box(-UPPER_BEAM_HALF_SPAN,UPPER_BEAM_HALF_SPAN,
    UPPER_BEAM_S-UPPER_BEAM_W/2,UPPER_BEAM_S+UPPER_BEAM_W/2,
    UPPER_BEAM_FRONT_N,CARRIER_BACK_N)
upper_spine=axial_box(-UPPER_BEAM_W/2,UPPER_BEAM_W/2,
    UPPER_BEAM_S,20.5,UPPER_BEAM_FRONT_N,CARRIER_BACK_N)
carrier=carrier.fuse(upper_beam).fuse(upper_spine).removeSplitter()
# 去掉下方无用圆弧，让出底板上方的空间；两侧下螺丝座仍由上方弧段连接。
carrier = carrier.cut(rectangle_face(-50, 50, -60, -18, 25).extrude(N * 20)).removeSplitter()

# 螺母座连接到原厂下方螺丝座，圆角外形和宽筋分散锁紧力。
for x,s in LOCK_POINTS:
    pad = rounded_rectangle_face(8.5,7.6,1.0,s,13.8).extrude(-N*(LOCK_BOSS_BACK-13.8))
    pad.translate(X*x)
    carrier = carrier.fuse(pad)
    carrier = carrier.fuse(connect_web(x,s,math.copysign(13.75,x),-14.7,CARRIER_LOCK_WEB_W,13.8,CARRIER_LOCK_WEB_BACK))
    # 后侧热熔压入，前方小孔仅供螺丝尾端避空；不再侧开槽削弱母座。
    carrier = carrier.cut(axial_cylinder(1.65,13.5,19.2,x,s))
    carrier = carrier.cut(axial_cylinder(LOCK_INSERT_BORE/2,
        LOCK_BOSS_BACK-LOCK_INSERT_DEPTH,LOCK_BOSS_BACK+.1,x,s))
    carrier = carrier.cut(Part.makeCone(LOCK_INSERT_BORE/2,
        LOCK_INSERT_BORE/2+.3,.3,plate_point(x,s,LOCK_BOSS_BACK-.3),-N))

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
    [ellipse_wire(*outer_section(section)) for section in sections], True, False
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
cavity = Part.makeLoft([ellipse_wire(*inner_section(v)) for v in inner_sections], True, True)
cavity = cavity.common(projection_envelope(SHELL_PROJECTION_R-FRONT_WALL_TARGET)).common(above_floor)
# 安装让位不能越过随外形退让的内腔，否则前口下缘会被圆柱切成薄片。
# 支架下缘为 s=-18；让位只覆盖支架实际存在的上部，保留下方斜壁。
mount_clearance = Part.makeCylinder(SHELL_INNER_R, MOUNT_CLEARANCE_DEPTH, plate_point(0, 0, SHELL_MOUTH_N), -N)
mount_region = rectangle_face(-40, 40, -18.4, 40, SHELL_MOUTH_N).extrude(-N*MOUNT_CLEARANCE_DEPTH)
# 原前口让位保留；旋转增量仅扫过实际环体及螺丝座包络，避免整圆柱误削中央下缘。
ring_air=axial_cylinder(CARRIER_OUTER_R+.3,SHELL_MOUTH_N,CARRIER_BACK_N+.3).cut(
    axial_cylinder(CARRIER_INNER_R-.3,SHELL_MOUTH_N-.1,CARRIER_BACK_N+.4))
lower_cap=axial_box(-40,40,-40,-18.3,SHELL_MOUTH_N-.1,CARRIER_BACK_N+.4)
# 小角度下，底部负 s 半平面的旋转并集由两个端点确定；单个圆柱保留一致的曲面参数。
# f(角度)=s*cos(角度)+x*sin(角度) 为负时二阶导数为正，最大值只能取在端点。
mount_sweep=ring_air.cut(lower_cap.common(hook_pose(lower_cap,-HOOK_RELEASE_DEG)))
for sx,sy in SCREWS_2D:
    if sx==0:continue  # 顶座始终包含在原前口圆柱让位内。
    boss_air=axial_cylinder(CARRIER_BOSS_R,SHELL_MOUTH_N,15.8,sx,sy)
    mount_sweep=mount_sweep.fuse(rotation_sweep(boss_air,-HOOK_RELEASE_DEG))
cavity = cavity.fuse(mount_clearance.common(mount_region)).fuse(mount_sweep.common(above_floor)).removeSplitter()
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
# 两锁座的旋转让位连成一体，消除左右扫掠之间不足打印厚度的中央残筋。
lock_air_width=max(x for x,s in LOCK_POINTS)-min(x for x,s in LOCK_POINTS)+8.9
lock_air=rounded_rectangle_face(lock_air_width,8.0,1.2,LOCK_POINTS[0][1],SHELL_MOUTH_N).extrude(
    -N*(22.0-SHELL_MOUTH_N))
rear=rear.cut(rotation_sweep(lock_air,-HOOK_RELEASE_DEG))
for x,s in LOCK_POINTS:
    # 母座内移后连接筋加长，给筋的整个旋转行程留出 0.3 mm 间隙。
    web_air=connect_web(x,s,math.copysign(13.75,x),-14.7,
        CARRIER_LOCK_WEB_W+.6,13.5,CARRIER_LOCK_WEB_BACK+.3)
    rear=subtract_sweep(rear,rotation_sweep(web_air,-HOOK_RELEASE_DEG))
for x,s in LOCK_POINTS:
    seat=axial_cylinder(3.7,19.25,LOCK_HEAD_SEAT,x,s)
    support=Part.makeBox(8,9,8,App.Vector(x-4,-2,SHELL_FLOOR_T)).common(outer_envelope)
    support=support.common(axial_box(-40,40,-40,-12.5,19.25,70))
    rear=rear.fuse(seat).fuse(support)
    rear=rear.cut(axial_cylinder(LOCK_CLEARANCE_R,18.8,LOCK_HEAD_SEAT+.1,x,s))
    rear=rear.cut(axial_cylinder(LOCK_TOOL_R,LOCK_HEAD_SEAT,80,x,s))
    lock_seats.append(seat)
    wall_audit_zones.append(((x-4.2,x+4.2),(s-4.2,s+4.2),(13.8,80)))
rear=rear.removeSplitter()
carrier,rear,upper_hooks,upper_lugs,hook_stops=add_upper_hooks(carrier,rear,outer_envelope)
guide_sockets=hook_stops
upper_post_sections=[]
for index,angle in enumerate(HOOK_ANGLES):
    a=math.radians(angle)
    u=X*math.cos(a)+S*math.sin(a);v=-X*math.sin(a)+S*math.cos(a)
    hi=-HOOK_LUG_WIDTH/2-2*HOOK_CLEARANCE;lo=hi-HOOK_ROOT_T
    for n in (18.0,20.0,23.0):
        for t in (lo+.05,(lo+hi)/2,hi-.05):
            line=Part.makeLine(plate_point(0,0,n)+u*HOOK_RADIAL_INNERS[index]+v*t,
                plate_point(0,0,n)+u*HOOK_OUTER_R+v*t)
            width=sum(e.Length for e in line.common(carrier.copy(True)).Edges)
            assert width>=2.7,'旋扣立柱径向承力截面不足：'+str((angle,n,t,width))
            upper_post_sections.append(width)
        for r in (HOOK_RADIAL_INNERS[index]+.1,(HOOK_RADIAL_INNERS[index]+HOOK_OUTER_R)/2,HOOK_OUTER_R-.5):
            line=Part.makeLine(plate_point(0,0,n)+u*r+v*lo,
                plate_point(0,0,n)+u*r+v*hi)
            width=sum(e.Length for e in line.common(carrier.copy(True)).Edges)
            assert width>=3.19,'旋扣立柱切向承力截面不足：'+str((angle,n,r,width))
for lo,hi in ((7,22),(-22,-7)):
    wall_audit_zones.append(((lo,hi),(13,23),(14.4,25.3)))
for x,s in SCREWS_2D:
    assert carrier.common(axial_cylinder(2.0,15.5,30,x,s)).Volume<0.01,'原厂螺丝工具路径'

lock_heads=[axial_cylinder(2.75,LOCK_HEAD_SEAT,LOCK_HEAD_SEAT+3,x,s) for x,s in LOCK_POINTS]
lock_shafts=[axial_cylinder(1.5,LOCK_HEAD_SEAT-LOCK_SCREW_LENGTH,LOCK_HEAD_SEAT,x,s) for x,s in LOCK_POINTS]
lock_inserts=[axial_cylinder(LOCK_INSERT_OD/2,LOCK_BOSS_BACK-LOCK_INSERT_LENGTH,LOCK_BOSS_BACK,x,s).cut(
    axial_cylinder(1.5,LOCK_BOSS_BACK-LOCK_INSERT_LENGTH-.1,LOCK_BOSS_BACK+.1,x,s)) for x,s in LOCK_POINTS]
lock_tools=[axial_cylinder(2.0,LOCK_HEAD_SEAT+3,80,x,s) for x,s in LOCK_POINTS]
print('完成止口和锁紧结构',flush=True)
for name,shape in [('carrier',carrier),('rear',rear)]:
    print('快速实体检查',name,shape.isValid(),len(shape.Solids),flush=True)
assert carrier.common(rear).Volume<0.01, '支架与后壳干涉'
for hardware in lock_heads+lock_shafts+lock_tools:
    for name,shape in [('carrier',carrier),('rear',rear)]:
        assert hardware.common(shape).Volume<0.01, name+'挡紧固件或工具'
insert_installation=[]
for x,s in LOCK_POINTS:
    # 滚花与底孔的径向干涉是热熔配合，不作为刚体碰撞错误。
    tool=axial_cylinder(2.0,LOCK_BOSS_BACK+.01,LOCK_BOSS_BACK+12,x,s)
    volume=tool.common(carrier).Volume
    assert volume<.01,'热熔工具轴向入口受阻'
    insert_installation.append(volume)
assert LOCK_HEAD_SEAT-LOCK_SCREW_LENGTH < LOCK_BOSS_BACK-LOCK_INSERT_LENGTH
contact=carrier.distToShape(rear)[0]
assert contact<0.0001,'轴向止挡未接触'
bottom_band=Part.Face(ellipse_wire(0,FOOT_OUTER_RX,FOOT_OUTER_RY,FOOT_CENTER_Y)).extrude(Z*.6)
bottom_band=bottom_band.cut(Part.Face(ellipse_wire(0,FOOT_INNER_RX,FOOT_INNER_RY,FOOT_CENTER_Y)).extrude(Z*.6))
for x,s in LOCK_POINTS:
    assert axial_cylinder(LOCK_TOOL_R,LOCK_HEAD_SEAT,80,x,s).common(bottom_band).Volume<0.001,'工具井切断底环'
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
    BATTERY_OFFSET_S, BATTERY_FRONT_N
).extrude(-N * BATTERY_T)
battery_ref.translate(X * BATTERY_OFFSET_X)
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

# 矩形扬声器试排：粘贴面和格栅随参数生成，间隙失败仍明确记录。
assert min(SPEAKER_W, SPEAKER_H, SPEAKER_THICKNESS, SPEAKER_TAPE_T,
           SPEAKER_TAPE_RING_W, SPEAKER_FRONT_GAP, SPEAKER_WIRE_GAP, SPEAKER_SIDE_GAP)>0
assert 0 < SPEAKER_CORNER_R < min(SPEAKER_W,SPEAKER_H)/2
assert SPEAKER_TAPE_RING_W < min(SPEAKER_W,SPEAKER_H)/2
speaker_axis = -N * math.cos(math.radians(SPEAKER_TILT_DEG)) + S * math.sin(math.radians(SPEAKER_TILT_DEG))
speaker_up = S * math.cos(math.radians(SPEAKER_TILT_DEG)) + N * math.sin(math.radians(SPEAKER_TILT_DEG))
speaker_face = plate_point(SPEAKER_OFFSET_X, SPEAKER_OFFSET_S, SPEAKER_FRONT_N)

def speaker_box(width,height,start,length,radius=None,offset_x=0):
    radius=min(SPEAKER_CORNER_R if radius is None else radius,width/2-.001,height/2-.001)
    local=rounded_rectangle_face(width,height,radius,0,0)
    # 先以模块原点构建，再绕横轴旋转为扬声器朝向。
    local.translate(-P)
    local.rotate(App.Vector(),X,SPEAKER_TILT_DEG)
    local.translate(speaker_face+speaker_axis*start+X*offset_x)
    return local.extrude(speaker_axis*length)

def speaker_rect(x0,x1,y0,y1,start,length):
    points=[speaker_face+X*x+speaker_up*y+speaker_axis*start
            for x,y in [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]]
    return polygon_face(points).extrude(speaker_axis*length)

speaker_open_w=SPEAKER_W-2*SPEAKER_HARD_EDGE
speaker_open_h=SPEAKER_H-2*SPEAKER_HARD_EDGE
speaker_ref = speaker_box(SPEAKER_W,SPEAKER_H,-SPEAKER_THICKNESS,SPEAKER_THICKNESS)
# 仅在四角保留窄 L 形胶层，不把最大角部宽度当成整块方形贴胶面。
tape_ring = speaker_box(SPEAKER_W,SPEAKER_H,0,SPEAKER_TAPE_T).cut(
    speaker_box(SPEAKER_W-2*SPEAKER_TAPE_RING_W,SPEAKER_H-2*SPEAKER_TAPE_RING_W,-.01,SPEAKER_TAPE_T+.02))
speaker_tape_patches=[]
for sx in (-1,1):
    for sy in (-1,1):
        xx=sorted([sx*SPEAKER_W/2,sx*(SPEAKER_W/2-SPEAKER_TAPE_CORNER_LENGTH)])
        yy=sorted([sy*SPEAKER_H/2,sy*(SPEAKER_H/2-SPEAKER_TAPE_CORNER_LENGTH)])
        speaker_tape_patches.append(tape_ring.common(speaker_rect(*xx,*yy,-.01,SPEAKER_TAPE_T+.02)))
speaker_tape=Part.makeCompound(speaker_tape_patches)
speaker_diaphragm = speaker_box(speaker_open_w,speaker_open_h,-.1,.1)
speaker_air = speaker_box(speaker_open_w,speaker_open_h,0,SPEAKER_FRONT_GAP)
speaker_wire_reserve = speaker_rect(SPEAKER_W/2,SPEAKER_W/2+SPEAKER_WIRE_GAP,
    -SPEAKER_H/2,SPEAKER_H/2,-SPEAKER_THICKNESS,SPEAKER_THICKNESS)
# 贴边处允许胶层与粘贴面接触；空气间隙只覆盖实际振膜开口。
speaker_envelope = speaker_box(SPEAKER_W+2*SPEAKER_SIDE_GAP,SPEAKER_H+2*SPEAKER_SIDE_GAP,
    -SPEAKER_THICKNESS,SPEAKER_THICKNESS).fuse(speaker_wire_reserve).fuse(speaker_air).fuse(speaker_tape)
# 旋扣外端避让完整喇叭预留；定位墙和胶框在后续单独添加。
rear=rear.cut(speaker_envelope).removeSplitter()
pad_w=speaker_open_w+2*SPEAKER_PAD_BORDER
pad_h=speaker_open_h+2*SPEAKER_PAD_BORDER
assert SPEAKER_PAD_BORDER>=2.0,'粘贴面框宽至少 2 mm'
speaker_pad=speaker_box(pad_w,pad_h,SPEAKER_TAPE_T,60).cut(
    speaker_box(speaker_open_w,speaker_open_h,SPEAKER_TAPE_T-.01,60.02)).common(outer_envelope).common(above_floor)
assert speaker_pad.Volume>0,'粘贴面未连接到壳体'
rear=rear.fuse(speaker_pad).removeSplitter()
# 四段长边定位和一段非出线端定位；胶带负责保持轴向贴合。
locator_bounds=[]
for sx in (-1,1):
    for sy in (-1,1):
        xx=(sx*8-SPEAKER_LOCATOR_LENGTH/2,sx*8+SPEAKER_LOCATOR_LENGTH/2)
        yy=sorted([sy*(SPEAKER_H/2+SPEAKER_LOCATOR_GAP),
                   sy*(SPEAKER_H/2+SPEAKER_LOCATOR_GAP+SPEAKER_LOCATOR_T)])
        locator_bounds.append((*xx,*yy))
locator_bounds.append((-SPEAKER_W/2-SPEAKER_LOCATOR_GAP-SPEAKER_LOCATOR_T,
    -SPEAKER_W/2-SPEAKER_LOCATOR_GAP,-2,2))
speaker_locators=[speaker_rect(*v,-2,3.6).common(outer_envelope) for v in locator_bounds]
for locator in speaker_locators:
    assert locator.isValid() and len(locator.Solids)==1
    assert locator.distToShape(speaker_ref)[0]>=SPEAKER_LOCATOR_GAP-.001
    rear=rear.fuse(locator)
    local=[(v.x,(v-P).dot(S),(P-v).dot(N)) for v in locator.tessellate(.05)[0]]
    wall_audit_zones.append(tuple((min(v[k] for v in local)-.02,max(v[k] for v in local)+.02) for k in range(3)))
rear=rear.removeSplitter()
# 定位区按 0.3 mm 配合间隙检查，其他周边仍按 1 mm 预留。
for x0,x1,y0,y1 in locator_bounds:
    window=speaker_rect(x0-.01,x1+.01,y0-.01,y1+.01,-SPEAKER_THICKNESS-.01,SPEAKER_THICKNESS+.02)
    speaker_envelope=speaker_envelope.cut(window)
speaker_envelope=speaker_envelope.fuse(speaker_box(SPEAKER_W+2*SPEAKER_LOCATOR_GAP,
    SPEAKER_H+2*SPEAKER_LOCATOR_GAP,-SPEAKER_THICKNESS,SPEAKER_THICKNESS))
# 四块胶层的背面必须全部落在平整承托上。
speaker_glue_support=speaker_tape.copy()
speaker_glue_support.translate(speaker_axis*SPEAKER_TAPE_T)
speaker_glue_support=speaker_glue_support.common(speaker_box(SPEAKER_W,SPEAKER_H,SPEAKER_TAPE_T,.05))
assert speaker_glue_support.cut(rear).Volume<.01,'当前位置无法提供完整平整粘贴面'
speaker_sound_zone = speaker_box(speaker_open_w,speaker_open_h,0,60).common(rear)
speaker_slots=[]
speaker_slot_volumes=[]
if SPEAKER_GRILLE_ENABLED:
    assert isinstance(SPEAKER_SLOT_COUNT,int) and SPEAKER_SLOT_COUNT>0
    assert min(SPEAKER_SLOT_W,SPEAKER_SLOT_H,SPEAKER_SLOT_WEB)>0
    grille_span=SPEAKER_SLOT_COUNT*SPEAKER_SLOT_W+(SPEAKER_SLOT_COUNT-1)*SPEAKER_SLOT_WEB
    assert grille_span<=speaker_open_w-1 and SPEAKER_SLOT_H<=speaker_open_h-1,'出音孔越过振膜区域或胶粘边框'
    assert abs(SPEAKER_SLOT_OFFSET_S)+SPEAKER_SLOT_H/2<=speaker_open_h/2-.1
    assert abs(SPEAKER_SLOT_OFFSET_X)+grille_span/2<=speaker_open_w/2-.1
    for index in range(SPEAKER_SLOT_COUNT):
        offset=SPEAKER_SLOT_OFFSET_X+(index-(SPEAKER_SLOT_COUNT-1)/2)*(SPEAKER_SLOT_W+SPEAKER_SLOT_WEB)
        slot=speaker_box(SPEAKER_SLOT_W,SPEAKER_SLOT_H,0,60,SPEAKER_SLOT_W/2-.001,offset)
        slot.translate(speaker_up*SPEAKER_SLOT_OFFSET_S)
        assert slot.common(speaker_tape).Volume<.001
        assert slot.common(bottom_band).Volume<.001,'出音孔切断底环'
        speaker_slot_volumes.append(slot.common(rear).Volume)
        assert speaker_slot_volumes[-1]>.1,'出音孔没有穿过后壳'
        rear=rear.cut(slot)
        speaker_slots.append(slot)
    rear=rear.removeSplitter()
assert rear.isValid() and len(rear.Solids)==1,'开孔后的后壳必须保持单一有效实体'
assert all(slot.common(rear).Volume<.001 for slot in speaker_slots),'出音孔未贯通'
assert all(speaker_pad.common(v).Volume<.01 for v in [carrier,battery_ref,module_ref]+connector_refs+wire_refs+lock_heads+lock_shafts+lock_inserts+lock_tools),'粘贴面挡住装配或工具'
# 格栅筋和粘贴面独立验证，普通壁厚审计不将孔边缘当成普通壳壁。
pad_points=speaker_box(pad_w,pad_h,SPEAKER_TAPE_T,60).common(outer_envelope).tessellate(.1)[0]
pad_local=[(v.x,(v-P).dot(S),(P-v).dot(N)) for v in pad_points]
wall_audit_zones.append(tuple((min(v[k] for v in pad_local)-.05,max(v[k] for v in pad_local)+.05) for k in range(3)))
speaker_obstacles = [('rear_cover',rear),('battery',battery_ref),('carrier',carrier),('module',module_ref)]
speaker_obstacles += [('connector_%d'%i,v) for i,v in enumerate(connector_refs+connector_sweeps+wire_refs)]
speaker_obstacles += [('fastener_tool_%d'%i,v) for i,v in enumerate(lock_heads+lock_shafts+lock_inserts+lock_tools+original_heads)]
speaker_body_overlaps = {name:round(speaker_ref.common(v).Volume,5) for name,v in speaker_obstacles}
speaker_envelope_overlaps = {name:round(speaker_envelope.common(v).Volume,5) for name,v in speaker_obstacles}
speaker_body_fits = max(speaker_body_overlaps.values()) < .01
speaker_layout_fits = max(speaker_envelope_overlaps.values()) < .01
speaker_conflict_shapes = [speaker_envelope.common(v) for _,v in speaker_obstacles
                           if speaker_envelope.common(v).Volume>=.01]
speaker_conflicts = Part.makeCompound(speaker_conflict_shapes) if speaker_conflict_shapes else None
speaker_clearance = {name:round(speaker_ref.distToShape(v)[0],4) for name,v in speaker_obstacles[:4]}
print('speaker body fits:',speaker_body_fits,'layout clearance fits:',speaker_layout_fits,flush=True)
print('speaker envelope conflicts:',speaker_envelope_overlaps,flush=True)
assert speaker_body_fits and speaker_layout_fits,'喇叭本体或完整安装预留存在冲突'
# 假定 2 mm 线束的连通走线通道；末端接入已有插头收线区。
speaker_route_points=[speaker_face+X*(SPEAKER_W/2+SPEAKER_WIRE_GAP/2)-speaker_axis*(SPEAKER_THICKNESS/2)]
speaker_route_points += [plate_point(*v) for v in [(15,14.3,29),(9,14.3,29),(6.5,16.5,24),(6.5,16.5,20)]]
speaker_route_shapes=[]
for point in speaker_route_points:
    speaker_route_shapes.append(Part.makeSphere(SPEAKER_CABLE_DIAMETER/2,point))
for a,b in zip(speaker_route_points,speaker_route_points[1:]):
    vector=b-a
    speaker_route_shapes.append(Part.makeCylinder(SPEAKER_CABLE_DIAMETER/2,vector.Length,a,vector))
speaker_wire_route=speaker_route_shapes[0].multiFuse(speaker_route_shapes[1:]).removeSplitter()
speaker_route_overlaps={name:round(speaker_wire_route.common(v).Volume,6)
    for name,v in [('rear',rear),('carrier',carrier),('battery',battery_ref),('module',module_ref)]}
assert max(speaker_route_overlaps.values())<.01,'喇叭走线通道干涉：'+str(speaker_route_overlaps)
assert speaker_wire_route.common(speaker_ref).Volume<.01,'线束通道穿过喇叭本体'
assert all(speaker_wire_route.common(v).Volume<.01 for v in lock_heads+lock_shafts+lock_inserts+lock_tools+original_heads)
assert speaker_wire_route.common(speaker_wire_reserve).Volume>.01
assert speaker_wire_route.common(Part.makeCompound(wire_refs)).Volume>.01
speaker_route_length=sum((b-a).Length for a,b in zip(speaker_route_points,speaker_route_points[1:]))
# 实际层中心的实体见证点，用于检查细定位墙、胶面和格栅筋有无被切片省略。
speaker_print_witnesses={}
def add_print_witnesses(name,x,y,n0,n1):
    center=speaker_face+X*x+speaker_up*y
    low,high=sorted([(center+speaker_axis*n0).z,(center+speaker_axis*n1).z])
    points=[]
    for layer in range(max(1,int(low/.2)+1),int(high/.2)+2):
        z=layer*.2-.1
        n=(z-center.z)/speaker_axis.z
        if n0+.05<n<n1-.05:
            point=center+speaker_axis*n
            if rear.isInside(point,.001,False):
                points.append({'layer_z_mm':round(layer*.2,3),'point_mm':[point.x,point.y,point.z]})
    assert len(points)>=3,'打印功能区采样不足：'+name
    speaker_print_witnesses[name]=points
for index,(x0,x1,y0,y1) in enumerate(locator_bounds):
    add_print_witnesses('locator_%d'%index,(x0+x1)/2,(y0+y1)/2,-1.8,1.4)
for sx in (-1,1):
    for sy in (-1,1):
        add_print_witnesses('tape_%s_%s'%(sx,sy),sx*(SPEAKER_W/2-.4),sy*(SPEAKER_H/2-2),1,4)
for index in range(SPEAKER_SLOT_COUNT-1):
    x=SPEAKER_SLOT_OFFSET_X+(index-(SPEAKER_SLOT_COUNT-2)/2)*(SPEAKER_SLOT_W+SPEAKER_SLOT_WEB)
    add_print_witnesses('grille_web_%d'%index,x,SPEAKER_SLOT_OFFSET_S,1,20)

carrier_obj = add_feature(doc, "Mount_Carrier", carrier, (0.83, 0.84, 0.82))
rear_obj = add_feature(doc, "Rear_Cover", rear, (0.66, 0.69, 0.69))
add_feature(doc, "Module_Reference", module_ref, (0.08, 0.09, 0.10))
add_feature(doc, "Battery_Reference", battery_ref, (0.28, 0.65, 0.40), False)
for name,shape,color in (
    ('Speaker_Reference',speaker_ref,(.25,.49,.75)),
    ('Speaker_Diaphragm_Reference',speaker_diaphragm,(.95,.72,.24)),
    ('Speaker_Tape_Reference',speaker_tape,(.65,.38,.76)),
    ('Speaker_Air_Reference',speaker_air,(.3,.75,.8)),
    ('Speaker_Wire_Reserve_Reference',speaker_wire_reserve,(.9,.45,.2)),
    ('Speaker_Wire_Route_Reference',speaker_wire_route,(.9,.45,.2)),
    ('Speaker_Clearance_Reference',speaker_envelope,(.3,.7,.8)),
    ('Speaker_Sound_Zone_Reference',speaker_sound_zone,(.95,.72,.24)),
):
    if shape.Volume>0:
        add_feature(doc,name,shape,color,False)
if speaker_conflicts:
    add_feature(doc,'Speaker_Conflicts_Reference',speaker_conflicts,(.9,.15,.45),False)
for prefix, shapes, color in (
    ("Connector", connector_refs, (0.9, 0.75, 0.3)),
    ("Insertion", connector_sweeps, (0.95, 0.55, 0.2)),
    ("Wire", wire_refs, (0.8, 0.3, 0.2)),
):
    for index, shape in enumerate(shapes):
        add_feature(doc, "%s_%d_Reference" % (prefix, index + 1), shape, color, False)
add_feature(doc, "Adhesive_Area_Reference", adhesive_ref, (0.3, 0.6, 0.9), False)
for name,shapes in [('Lock_Heads',lock_heads),('Lock_Shafts',lock_shafts),
                    ('Lock_Inserts',lock_inserts),('Lock_Tools',lock_tools),('Original_Heads',original_heads)]:
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
carrier.check(True)
rear.check(True)
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
speaker_closing_checks = []
poses=[(a,0) for a in (0,1,2,3,4,6,HOOK_RELEASE_DEG)]
poses += [(HOOK_RELEASE_DEG,t) for t in (.5,1,2,4,8,20,HOOK_PULL_MM)]
for angle,travel in poses:
    moving_cover=hook_pose(rear,angle,travel)
    assert all(moving_cover.common(v).Volume < 0.01 for v in connector_refs + wire_refs)
    rigid_overlap = moving_cover.common(carrier).Volume
    print("closing angle=%.1f travel=%.1f rigid carrier common=%.3f" % (angle,travel,rigid_overlap),flush=True)
    if rigid_overlap>=0.01:
        for solid in moving_cover.common(carrier).Solids:
            c=solid.CenterOfMass-P
            print('合盖干涉位置',solid.Volume,c.x,c.dot(S),-c.dot(N),flush=True)
    assert rigid_overlap < 0.01
    assert moving_cover.common(battery_ref).Volume < 0.01
    closing_checks.append({"angle_deg":angle,"travel_mm":travel,"carrier_overlap_mm3":rigid_overlap})
    # 扬声器随后壳移动，电池占位保持在模块侧；冲突记录而非伪装成通过。
    moving_speaker=hook_pose(speaker_envelope,angle,travel)
    speaker_closing_checks.append({'angle_deg':angle,'travel_mm':travel,'overlap_mm3':round(sum(
        moving_speaker.common(v).Volume for v in [carrier,battery_ref,module_ref]+connector_refs+wire_refs),5)})
assert all(v['overlap_mm3']<.01 for v in speaker_closing_checks),'喇叭随后壳开合时干涉'
print("insertion and closing connector clearance: passed")
hook_motion=verify_hook_motion(carrier,rear,speaker_envelope,
    # 插入包络单独验证；开盖时只保留已经装入的插头实体及线束空间。
    [module_ref,battery_ref]+connector_refs+wire_refs+original_heads+lock_inserts,
    upper_lugs,lock_shafts,hook_stops)
for x,s in LOCK_POINTS:
    bearing=axial_cylinder(2.75,LOCK_HEAD_SEAT-.05,LOCK_HEAD_SEAT,x,s).cut(
        axial_cylinder(LOCK_CLEARANCE_R,LOCK_HEAD_SEAT-.1,LOCK_HEAD_SEAT+.1,x,s))
    assert bearing.cut(rear).Volume<.001,'旋转让位破坏螺丝头承压面'
# 旧通用粘贴区只是参考，新扬声器台可能占用它；单独报告而不当作实体装配失败。
adhesive_zone_clear=adhesive_ref.common(rear).Volume < .01
print('generic adhesive area available:',adhesive_zone_clear,flush=True)

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
    "locking_screws": "2 × M3×6 内六角圆柱头，头部 Ø5.5×3 mm",
    "heat_set_insert":{"thread":"M3","length_mm":LOCK_INSERT_LENGTH,
        "outer_diameter_mm":LOCK_INSERT_OD,"bore_diameter_mm":LOCK_INSERT_BORE,
        "bore_depth_mm":LOCK_INSERT_DEPTH,"entry_chamfer_mm":.3,
        "installation":"承托架背面轴向压入，端面齐平；先热熔再装开发板",
        "thread_engagement_mm":LOCK_INSERT_LENGTH,
        "screw_tip_extension_mm":LOCK_BOSS_BACK-LOCK_INSERT_LENGTH-(LOCK_HEAD_SEAT-LOCK_SCREW_LENGTH),
        "physical_installation_verified":False},
    "guide_engagement_mm":None,
    "guide_clearance_mm":GUIDE_CLEARANCE,
    "guide_widths_mm":[v[1] for v in GUIDES],
    "guide_top_shape":"两处短承压垫和双刚性旋扣",
    "lock_points_mm":LOCK_POINTS,
    "heat_tool_max_overlap_mm3":max(insert_installation),
    "axial_stop_contact_distances_mm":stop_contacts,
    "tool_well_diameter_mm":LOCK_TOOL_R*2,
    "screw_head_seat_n_mm":LOCK_HEAD_SEAT,
    "carrier_ring_width_mm":CARRIER_OUTER_R-CARRIER_INNER_R,
    "closing_checks":closing_checks,
    "upper_hooks":hook_motion,
    "mouth_max_radius_mm": max(mouth_radii),
    "axial_joint_clearance_mm": SHELL_MOUTH_N - MODULE_DEPTH,
    "cavity_volume_cm3": cavity.Volume / 1000,
    "cavity_after_carrier_cm3": outer_envelope.cut(rear).cut(carrier).common(above_floor).Volume / 1000,
    "shell_bbox_mm": [actual_box.XLength, actual_box.YLength, actual_box.ZLength],
    "shell_depth_extension_mm":SHELL_DEPTH_EXTENSION,
    "shell_rear_bulge_parameter_mm":SHELL_REAR_BULGE,
    "module_vertical_raise_mm":SHELL_DEPTH_EXTENSION*COS,
    "module_back_bottom_clearance_mm":MODULE_BOTTOM_CLEARANCE+SHELL_DEPTH_EXTENSION*COS,
    "cavity_bbox_mm": [cavity_box.XLength, cavity_box.YLength, cavity_box.ZLength],
    "sampled_side_wall_min_mm": min(wall_samples),
    "side_wall_sample_count": len(wall_samples),
    "bottom_z_mm": actual_box.ZMin,
    "bottom_contact_samples_passed": sum(ring_samples),
    "bottom_ring_width_samples_passed": ring_width_passed,
    "minimum_tip_angle_without_speaker_deg": min(tip_all_directions),
    "speaker_fitted": False,
    "generic_adhesive_area_available":adhesive_zone_clear,
    "speaker_layout": {
        "status":"矩形扬声器与平整粘贴面试制；完整预留通过" if speaker_layout_fits else "矩形扬声器与格栅试制；完整预留仍有冲突",
        "shape":"rounded_rectangle",
        "body_dimensions_mm":[SPEAKER_W,SPEAKER_H,SPEAKER_THICKNESS],
        "corner_radius_mm":SPEAKER_CORNER_R,
        "front_center_x_s_n_mm":[SPEAKER_OFFSET_X,SPEAKER_OFFSET_S,SPEAKER_FRONT_N],
        "tilt_deg":SPEAKER_TILT_DEG,
        "tape_thickness_mm":SPEAKER_TAPE_T,
        "tape_ring_width_mm":SPEAKER_TAPE_RING_W,
        "tape_pattern":"四角 L 形，各臂 4 mm、宽 0.8 mm；不按整圈贴胶",
        "tape_patch_count":len(speaker_tape_patches),
        "tape_total_area_mm2":speaker_tape.Volume/SPEAKER_TAPE_T,
        "locator_count":len(speaker_locators),
        "locator_gap_mm":SPEAKER_LOCATOR_GAP,
        "locator_wall_mm":SPEAKER_LOCATOR_T,
        "front_gap_mm":SPEAKER_FRONT_GAP,
        "wire_gap_mm":SPEAKER_WIRE_GAP,
        "side_gap_mm":SPEAKER_SIDE_GAP,
        "body_fits":speaker_body_fits,
        "clearance_envelope_fits":speaker_layout_fits,
        "body_clearances_mm":speaker_clearance,
        "body_overlaps_mm3":speaker_body_overlaps,
        "envelope_overlaps_mm3":speaker_envelope_overlaps,
        "closing_checks":speaker_closing_checks,
        "mounting_pad_created":True,
        "mounting_pad_border_mm":SPEAKER_PAD_BORDER,
        "tape_to_shell_distance_mm":round(speaker_tape.distToShape(rear)[0],5),
        "sound_holes_created":SPEAKER_GRILLE_ENABLED,
        "grille":{"slot_count":len(speaker_slots),"slot_width_mm":SPEAKER_SLOT_W,
                  "slot_length_mm":SPEAKER_SLOT_H,"web_width_mm":SPEAKER_SLOT_WEB,
                  "removed_volumes_mm3":[round(v,4) for v in speaker_slot_volumes],
                  "through_holes_verified":all(slot.common(rear).Volume<.001 for slot in speaker_slots)},
        "wire_route_verified":True,
        "wire_route_assumed_diameter_mm":SPEAKER_CABLE_DIAMETER,
        "wire_route_length_mm":speaker_route_length,
        "wire_route_overlaps_mm3":speaker_route_overlaps,
        "print_witnesses":speaker_print_witnesses,
        "maintenance_lead_requires_physical_check":True,
        "note":"30×20×7 mm、短边侧出线；四角窄 L 形胶区，定位处间隙 0.3 mm，其余周边 1 mm。几何走线按 2 mm 线束检查；实际线径、弯曲半径、维护余量和角部胶区仍待实物确认，扬声器未计入倾覆估算。",
    },
    "wire_bend_requires_physical_check": True,
}

# 旋扣切片区域随参数生成；打印坐标直接采用交付 STL 的刚体变换。
flat=carrier.copy(True)
flat.Placement=App.Placement(App.Vector(),App.Rotation(-N,Z)).multiply(flat.Placement)
hook_frame={'origin':list(P),'up':list(S),'normal':list(N),
            'carrier_y_origin':-P.dot(S),'carrier_n_origin':P.dot(N)+flat.BoundBox.ZMin,
            'carrier_s_sign':-1,'carrier_n_sign':1,
            'hook_r0':HOOK_INNER_R,'hook_r1':HOOK_OUTER_R,
            'hook_front_n':HOOK_LUG_FRONT_N+min(HOOK_AXIAL_OFFSETS),
            'hook_back_n':HOOK_LUG_BACK_N+max(HOOK_AXIAL_OFFSETS)}
hook_features={'mount_carrier':[],'rear_cover':[]}
for i,angle in enumerate(HOOK_ANGLES):
    r0,r1=HOOK_RADIAL_INNERS[i],HOOK_OUTER_R
    f,b=HOOK_LUG_FRONT_N+HOOK_AXIAL_OFFSETS[i],HOOK_LUG_BACK_N+HOOK_AXIAL_OFFSETS[i]
    half=HOOK_LUG_WIDTH/2
    stem_hi=-half-2*HOOK_CLEARANCE;stem_lo=stem_hi-HOOK_ROOT_T
    definitions=[('mount_carrier','lug',[r0,r1,stem_lo,half,f,b],0,[r0,r1]),
                 ('mount_carrier','post',[r0,r1,stem_lo,stem_hi,17.5,f],(stem_lo+stem_hi)/2,[r0,r1]),
                 ('rear_cover','front',[r0,r1,-.5,half,f-HOOK_CLEARANCE-HOOK_ROOT_T,f-HOOK_CLEARANCE],.5,[r0,r1]),
                 ('rear_cover','root',[r1+HOOK_CLEARANCE,25.2,-.5,half,f-HOOK_CLEARANCE-HOOK_ROOT_T,b+HOOK_CLEARANCE+HOOK_ROOT_T],.5,[r1+HOOK_CLEARANCE,25.2])]
    for part,kind,bounds,t,probe_r in definitions:
        hook_features[part].append({'name':kind+'_'+str(i),'kind':kind,'angle_deg':angle,
                                    'bounds':bounds,'probe_t':t,'probe_r':probe_r,
                                    'slot_front_n':f-HOOK_CLEARANCE,'slot_back_n':b+HOOK_CLEARANCE})
metrics['hook_print_frame']=hook_frame
metrics['carrier_print_orientation']='模块固定面朝下，三处原厂固定座落床；两根立柱向上打印'
for x in (-8,0,8):
    hook_features['mount_carrier'].append({'name':'beam_'+str(x),'kind':'beam','angle_deg':90,
        'bounds':[UPPER_BEAM_S-UPPER_BEAM_W/2,UPPER_BEAM_S+UPPER_BEAM_W/2,
                  -x-.6,-x+.6,UPPER_BEAM_FRONT_N,CARRIER_BACK_N],
        'probe_t':-x,'probe_r':[UPPER_BEAM_S-UPPER_BEAM_W/2,UPPER_BEAM_S+UPPER_BEAM_W/2]})
hook_features['mount_carrier'].append({'name':'upper_spine','kind':'spine','angle_deg':0,
    'bounds':[-UPPER_BEAM_W/2,UPPER_BEAM_W/2,16.7,17.3,UPPER_BEAM_FRONT_N,CARRIER_BACK_N],
    'probe_t':17,'probe_r':[-UPPER_BEAM_W/2,UPPER_BEAM_W/2]})
metrics['hook_print_features']=hook_features
metrics['upper_hooks'].update({'angles_deg':list(HOOK_ANGLES),'lug_width_mm':HOOK_LUG_WIDTH,
    'hook_width_mm':HOOK_COVER_WIDTH,'root_thickness_mm':HOOK_ROOT_T,'root_fillet_mm':HOOK_FILLET_R,
    'clearance_mm':HOOK_CLEARANCE,'lug_front_n_mm':hook_frame['hook_front_n'],
    'lug_back_n_mm':hook_frame['hook_back_n'],'bearing_faces_preserved':True,
    'axial_offsets_mm':list(HOOK_AXIAL_OFFSETS),'radial_inners_mm':list(HOOK_RADIAL_INNERS)})
metrics['upper_reinforcement']={'beam_width_mm':UPPER_BEAM_W,
    'beam_axial_thickness_mm':CARRIER_BACK_N-UPPER_BEAM_FRONT_N,
    'beam_center_s_mm':UPPER_BEAM_S,'beam_half_span_mm':UPPER_BEAM_HALF_SPAN,
    'notch_corner_radius_mm':UPPER_NOTCH_R,'connector_notches_open':True,
    'post_radial_section_min_mm':min(upper_post_sections),
    'post_radial_section_count':len(upper_post_sections),'post_tangential_section_min_target_mm':3.19,
    'battery_axial_gap_mm':BATTERY_FRONT_N-CARRIER_BACK_N,
    'physical_strength_verified':False}

# 预览辅助网格只存在本地 archive，参考体不混入打印文件。
preview_dir = PREVIEW_DIR
os.makedirs(preview_dir, exist_ok=True)
section_shape = rear.common(Part.makeBox(100, 200, 100, App.Vector(0, -100, 0)))
section_half=Part.makeBox(100,200,100,App.Vector(0,-100,0))
for name, shape in (("section", section_shape), ("battery_reference", battery_ref),
                    ("battery_section",battery_ref.common(section_half)),
                    ("speaker_section",speaker_ref.common(section_half)),
                    ("speaker_tape_section",speaker_tape.common(section_half)),
                    ("speaker_reference",speaker_ref), ("speaker_tape",speaker_tape),
                    ("speaker_diaphragm",speaker_diaphragm), ("speaker_air",speaker_air),
                    ("speaker_wire_reserve",speaker_wire_reserve), ("speaker_envelope",speaker_envelope),
                    ("speaker_wire_route",speaker_wire_route),
                    ("speaker_sound_zone",speaker_sound_zone),
                    ("connector_reference", Part.makeCompound(connector_refs)),
                    ("wire_reference", Part.makeCompound(wire_refs)),
                    ("carrier_reference", carrier), ("adhesive_reference", adhesive_ref),
                    ('upper_hooks',Part.makeCompound(upper_hooks)),('upper_lugs',Part.makeCompound(upper_lugs)),
                    ("fasteners",Part.makeCompound(lock_heads+lock_shafts+lock_inserts))):
    mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.1, AngularDeflection=0.3)
    mesh.write(os.path.join(preview_dir, name + ".stl"))
if speaker_conflicts:
    mesh=MeshPart.meshFromShape(Shape=speaker_conflicts,LinearDeflection=.1,AngularDeflection=.3)
    mesh.write(os.path.join(preview_dir,'speaker_conflicts.stl'))

fit_dir=FIT_DIR
os.makedirs(fit_dir,exist_ok=True)
samples={'upper_hook_carrier':carrier.common(shoulder_box(HOOK_ANGLES[0],HOOK_INNER_R-.05,24,-6,4,12.1,31)),
         'upper_hook_cover':rear.common(shoulder_box(HOOK_ANGLES[0],18,27,-6,5,12.4,33))}
samples['speaker_mount']=rear.common(speaker_rect(-SPEAKER_W/2-3,SPEAKER_W/2+3,
    -SPEAKER_H/2-3,SPEAKER_H/2+3,-2.1,8))
for name,shape in samples.items():
    assert shape.isValid() and len(shape.Solids)==1,'试装件不连通：'+name
    shape=shape.copy()
    if name=='upper_hook_carrier':
        shape.Placement=App.Placement(App.Vector(),App.Rotation(-N,Z)).multiply(shape.Placement)
    elif name!='upper_hook_cover':
        shape.Placement=App.Placement(App.Vector(),App.Rotation(-N,Z)).multiply(shape.Placement)
    shape.translate(App.Vector(0,0,-min(v.z for v in shape.tessellate(.05)[0])))
    mesh=MeshPart.meshFromShape(Shape=shape,LinearDeflection=.05,AngularDeflection=.3,Relative=False)
    assert mesh.isSolid() and len(mesh.getSeparateComponents())==1,'试装网格不闭合：'+name
    mesh.write(os.path.join(fit_dir,name+'.stl'))

carrier.check(True)
rear.check(True)
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
step_warnings=[]
for index,solid in enumerate(step_shape.Solids):
    try:solid.check(True)
    except ValueError as error:
        step_warnings.append({'solid_index':index,'details':str(error)})
metrics['step_export_validation']={'valid':True,'solid_count':2,
    'detailed_bop_passed':not step_warnings,'warnings':step_warnings,
    'editing_master':'stand.FCStd 和 stand.py；STEP 用于装配查看与交换'}
with open(os.path.join(OUT_DIR, "validation.json"), "w", encoding="utf-8") as stream:
    json.dump(metrics, stream, ensure_ascii=False, indent=2)
configure_display(doc)
doc.saveAs(os.path.join(OUT_DIR, "stand.FCStd"))
print("Exported to:", OUT_DIR)
