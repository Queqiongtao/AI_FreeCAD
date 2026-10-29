"""ESP32-S3-Touch-AMOLED-1.75-B 成品模块的鹅卵石桌面底座。

模块背面的三颗原厂螺丝固定薄支架；封闭后壳从背面卡到支架上。
在 FreeCAD 控制台或 freecadcmd 中运行，输出固定到 ./output/。
"""

import math
import os
import json

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
CARRIER_INNER_R = 21.5
CARRIER_OUTER_R = 22.8
CARRIER_BOSS_R = 2.6
SHELL_MOUTH_N = MODULE_DEPTH + 0.3
SHELL_PROJECTION_R = 25.2
SHELL_INNER_R = 23.2
SHELL_FLOOR_T = 2.6
FOOT_CENTER_Y = 14.0
FOOT_OUTER_RX = 20.5
FOOT_OUTER_RY = 20.0
FOOT_INNER_RX = 15.5
FOOT_INNER_RY = 15.0
FOOT_RECESS = 0.6

SNAP_ANGLES_DEG = (30.0, 150.0, 225.0)
SNAP_N = 16.2
SNAP_TIP_R = 23.0
SNAP_BUMP_R = 0.8
SNAP_POCKET_R = 1.0

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

for angle_deg in SNAP_ANGLES_DEG:
    angle = math.radians(angle_deg)
    beam = radial_strip(
        angle, 21.0, 23.0, 2.8, CARRIER_BACK_N
    ).extrude(N * (CARRIER_BACK_N - CARRIER_PAD_FRONT_N))
    carrier = carrier.fuse(beam)
    bump = Part.makeSphere(
        SNAP_BUMP_R,
        plate_point(SNAP_TIP_R * math.cos(angle),
                    SNAP_TIP_R * math.sin(angle), SNAP_N)
    )
    carrier = carrier.fuse(bump)

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

# 单一水平截面放样成壳，底层本身就是完整实体，避免斜壳与补环仅相切。
sections = [
    (0.0, FOOT_OUTER_RX, FOOT_OUTER_RY, FOOT_CENTER_Y),
    (2.0, FOOT_OUTER_RX + 0.5, FOOT_OUTER_RY + 0.5, FOOT_CENTER_Y),
    (6.0, 24.0, 22.0, 12.0),
    (12.0, 26.0, 25.0, 11.0),
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
    (SHELL_FLOOR_T, 18.0, 17.5, FOOT_CENTER_Y),
    (6.0, 21.0, 19.0, 12.0),
    (12.0, 23.0, 22.0, 11.0),
    (20.0, 24.0, 24.0, 10.0),
    (28.0, 23.5, 21.0, 11.0),
    (35.0, 20.0, 16.0, 12.0),
    (39.0, 13.0, 10.0, 14.0),
    (40.0, 1.0, 1.0, 16.0),
]
cavity = Part.makeLoft([ellipse_wire(*v) for v in inner_sections], True, False)
cavity = cavity.common(projection_envelope(SHELL_INNER_R)).common(above_floor)
mount_clearance = Part.makeCylinder(23.2, 6.6, plate_point(0, 0, SHELL_MOUTH_N), -N)
cavity = cavity.fuse(mount_clearance.common(above_floor)).removeSplitter()
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

# 卡扣凹位是内侧盲槽，外观面没有解锁孔。
pocket_wall_samples = []
for angle_deg in SNAP_ANGLES_DEG:
    angle = math.radians(angle_deg)
    pocket = Part.makeSphere(
        SNAP_POCKET_R,
        plate_point(SNAP_TIP_R * math.cos(angle),
                    SNAP_TIP_R * math.sin(angle), SNAP_N)
    )
    assert pocket.cut(outer_envelope).Volume < 0.01
    pocket_center = plate_point(SNAP_TIP_R * math.cos(angle),
                                SNAP_TIP_R * math.sin(angle), SNAP_N)
    pocket_wall_samples.append(outer_skin.distToShape(Part.Vertex(pocket_center))[0] - SNAP_POCKET_R)
    rear = rear.cut(pocket)
print("snap pocket wall minimum=%.3f mm" % min(pocket_wall_samples))
assert min(pocket_wall_samples) >= 1.19

# 中央只浅凹，不打穿；外侧保留 5 mm 宽的 360 度水平接触带。
underside_recess = Part.Face(ellipse_wire(
    -1.0, FOOT_INNER_RX, FOOT_INNER_RY, FOOT_CENTER_Y
)).extrude(Z * (1.0 + FOOT_RECESS))
rear = rear.cut(underside_recess)
rear = rear.removeSplitter()

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
adhesive_ref = Part.makeBox(24, 16, 0.4, App.Vector(-12, 2, SHELL_FLOOR_T))
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
# 壳从背后沿轴线压合；弹性卡扣碰到壳壁属于必要的弹性变形，单独检查。
elastic_zones = Part.makeCompound([
    radial_strip(math.radians(a), 20.8, 25.0, 4.0, 18.0).extrude(N * 4.5)
    for a in SNAP_ANGLES_DEG
])
rigid_carrier = carrier.cut(elastic_zones)
for travel in (0.5, 1.0, 2.0, 4.0, 8.0, 12.0):
    moving_cover = rear.copy()
    moving_cover.translate(-N * travel)
    assert all(moving_cover.common(v).Volume < 0.01 for v in connector_refs + wire_refs)
    rigid_overlap = moving_cover.common(rigid_carrier).Volume
    print("closing travel=%.1f rigid carrier common=%.3f" % (travel, rigid_overlap))
    assert rigid_overlap < 0.01
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
    "snap_pocket_min_wall_mm": min(pocket_wall_samples),
    "mouth_max_radius_mm": max(mouth_radii),
    "axial_joint_clearance_mm": SHELL_MOUTH_N - MODULE_DEPTH,
    "cavity_volume_cm3": cavity.Volume / 1000,
    "cavity_after_carrier_cm3": cavity.cut(carrier).Volume / 1000,
    "shell_bbox_mm": [actual_box.XLength, actual_box.YLength, actual_box.ZLength],
    "cavity_bbox_mm": [cavity_box.XLength, cavity_box.YLength, cavity_box.ZLength],
    "sampled_side_wall_min_mm": min(wall_samples),
    "side_wall_sample_count": len(wall_samples),
    "bottom_z_mm": actual_box.ZMin,
    "bottom_contact_samples_passed": sum(ring_samples),
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
                    ("carrier_reference", carrier), ("adhesive_reference", adhesive_ref)):
    mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.1, AngularDeflection=0.3)
    mesh.write(os.path.join(preview_dir, name + ".stl"))

export_stl(carrier, "mount_carrier.stl", lay_flat=True)
export_stl(rear, "rear_cover.stl")
Part.export([carrier_obj, rear_obj], os.path.join(OUT_DIR, "stand.step"))
step_shape = Part.read(os.path.join(OUT_DIR, "stand.step"))
print("STEP: valid=%s solids=%d" % (
    step_shape.isValid(), len(step_shape.Solids)
))
assert step_shape.isValid() and len(step_shape.Solids) == 2
with open(os.path.join(OUT_DIR, "validation.json"), "w", encoding="utf-8") as stream:
    json.dump(metrics, stream, ensure_ascii=False, indent=2)
doc.saveAs(os.path.join(OUT_DIR, "stand.FCStd"))
print("Exported to:", OUT_DIR)
