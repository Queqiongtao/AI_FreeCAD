"""Pebble desk stand for the ESP32-S3-Touch-AMOLED-1.75-B.

Front cap + rear body:
  * the thin front cap carries the board, the three through-openings and
    the external thread; it never touches the desk
  * the rear body is the whole pebble shell, the internal thread and the
    entire bottom plate; it is the only desktop contact
  * the battery cradle is attached to the front cap (hidden inside the
    rear body) so the battery does not rotate with the threaded cover

Single-file parametric source.  Outputs to ./output/:
  front_shell.stl, rear_cover.stl, stand.step, stand.FCStd

Run with freecadcmd stand.py, or in the FreeCAD GUI console from the
project directory:

    exec(open(r"stand.py", encoding="utf-8").read())
"""

import math
import os

import FreeCAD as App
import Part
import MeshPart

DOC_NAME = "Pebble_Stand"

try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SCRIPT_DIR = os.getcwd()
OUT_DIR = os.path.join(SCRIPT_DIR, "output")

BOARD_D = 51.0
BOARD_R = BOARD_D / 2.0
TILT_DEG = 50.0
BOTTOM_GAP = 2.0

FRONT_R = 25.5
SEAM_R = 25.1

# Thin front cap: front face + short seam band + thread neck.
CAP_SEAM_N = 2.0
CAP_NECK_N = 8.0
# The front face / outer rim at n<2 is kept complete; only the internal
# part at n>2.01 that would meet the rear-body floor is locally cleared.
# The rear-body floor top is z=2, so this leaves a 0.25 mm gap.
CAP_BOTTOM = 2.25
CAP_CLEAR_N_START = CAP_SEAM_N + 0.01

# Battery cradle: attached to the front cap, hidden inside the rear body.
POCKET_R = 21.3
CRADLE_R_OUT = 22.3
CRADLE_N = 12.0

# Rear body: whole outer shell + counterbore + bottom plate.
REAR_CAVITY_R = 23.2
REAR_CAVITY_N = 15.0
REAR_BACK_N = 28.0
BOTTOM_PLATE_TOP = 2.0

# Single-start right-hand thread near the board.
THREAD_PITCH = 3.0
THREAD_TURNS = 1.6
THREAD_START_N = 3.0
THREAD_ROOT_R = 22.3        # front-cap external minor
THREAD_CREST_R = 23.0       # front-cap external major
THREAD_ROOT_HALF = 1.0
THREAD_CREST_HALF = 0.4
THREAD_STEPS_PER_TURN = 48
THREAD_START_ANGLE_DEG = 10.0  # phase the anti-loosening crest at the stop

REAR_GROOVE_CREST_R = 24.0  # rear-body internal major
REAR_GROOVE_ROOT_HALF = 1.2
REAR_GROOVE_CREST_HALF = 0.6
THREAD_END_CREST_R = 23.3    # last 0.25 turn presses into the 23.2 bore
THREAD_END_TURNS = 0.25

SCREW_BOSS_R = 2.7
SCREW_BOSS_N = 2.5
SCREW_HEAD_R = 2.2
SCREW_HEAD_DEPTH = 1.5
SCREW_HOLE_R = 1.15
ACCESS_R = 2.3
ACCESS_N_FRONT = 2.5
ACCESS_N_REAR = 3.0

SCREWS_2D = [
    (0.0, 20.50),
    (13.75, -14.70),
    (-13.75, -14.70),
]

CONN_X = 6.5
CONN_Y = 17.25
CONN_OPENING_W = 5.0
CONN_OPENING_H = 4.0
HEADER_X = 0.0
HEADER_Y = -18.70
HEADER_WINDOW_W = 14.0
HEADER_WINDOW_H = 4.0

TILT = math.radians(TILT_DEG)
SIN = math.sin(TILT)
COS = math.cos(TILT)
N = App.Vector(0.0, -SIN, COS)
S = App.Vector(0.0, COS, SIN)
X = App.Vector(1.0, 0.0, 0.0)
Z = App.Vector(0.0, 0.0, 1.0)
P = App.Vector(0.0, 0.0, BOTTOM_GAP + BOARD_R * SIN)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def add_feature(name, shape):
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    return obj


def export_stl(shape, filename):
    mesh = MeshPart.meshFromShape(
        Shape=shape, LinearDeflection=0.05, AngularDeflection=0.30, Relative=False
    )
    components = mesh.getSeparateComponents()
    if len(components) > 1:
        components.sort(key=lambda c: c.Volume, reverse=True)
        mesh = components[0]
    # Small OCC tessellation holes at the cavity floor are filled so the
    # exported STL is a closed solid.
    try:
        mesh.fillupHoles(100, 1000)
    except Exception:
        pass
    mesh.write(os.path.join(OUT_DIR, filename))


def solid_of(shape):
    if len(shape.Solids) == 1:
        return shape.Solids[0]
    if len(shape.Solids) > 1:
        fused = shape.Solids[0]
        for s in shape.Solids[1:]:
            fused = fused.fuse(s)
        if len(fused.Solids) == 1:
            return fused.Solids[0]
        return fused
    return shape


def plate_rect_face(center, width, height):
    pts = [
        center + X * (-width / 2.0) + S * (-height / 2.0),
        center + X * (width / 2.0) + S * (-height / 2.0),
        center + X * (width / 2.0) + S * (height / 2.0),
        center + X * (-width / 2.0) + S * (height / 2.0),
    ]
    return Part.Face(Part.makePolygon(pts + [pts[0]]))


def side_rect_face(center, width_s, height_n):
    pts = [
        center - S * (width_s / 2.0) - N * (height_n / 2.0),
        center + S * (width_s / 2.0) - N * (height_n / 2.0),
        center + S * (width_s / 2.0) + N * (height_n / 2.0),
        center - S * (width_s / 2.0) + N * (height_n / 2.0),
    ]
    return Part.Face(Part.makePolygon(pts + [pts[0]]))


def thread_point(theta, r, n):
    return P - N * n + (X * math.cos(theta) + S * math.sin(theta)) * r


def thread_sector(t0, t1, n0, n1, r_root, r_crest, root_half, crest_half):
    p = [
        thread_point(t0, r_root, n0 - root_half),
        thread_point(t0, r_root, n0 + root_half),
        thread_point(t0, r_crest, n0 + crest_half),
        thread_point(t0, r_crest, n0 - crest_half),
    ]
    q = [
        thread_point(t1, r_root, n1 - root_half),
        thread_point(t1, r_root, n1 + root_half),
        thread_point(t1, r_crest, n1 + crest_half),
        thread_point(t1, r_crest, n1 - crest_half),
    ]
    f0 = Part.Face(Part.makePolygon(p + [p[0]]))
    f1 = Part.Face(Part.makePolygon(q + [q[0]]))
    return Part.makeLoft([f0, f1], True)


def thread_rib(n_start, r_root, r_crest, root_half, crest_half,
               turns=THREAD_TURNS, steps_per_turn=THREAD_STEPS_PER_TURN,
               end_root_r=None, end_crest_r=None,
               start_angle_deg=THREAD_START_ANGLE_DEG):
    total = int(round(turns * steps_per_turn))
    end_steps = int(round(THREAD_END_TURNS * steps_per_turn)) if (end_root_r is not None or end_crest_r is not None) else 0
    start_angle = math.radians(start_angle_deg)
    sectors = []
    for i in range(total):
        t0 = start_angle + 2.0 * math.pi * i / steps_per_turn
        t1 = start_angle + 2.0 * math.pi * (i + 1) / steps_per_turn
        n0 = n_start + THREAD_PITCH * i / steps_per_turn
        n1 = n_start + THREAD_PITCH * (i + 1) / steps_per_turn
        rr = r_root
        cr = r_crest
        if end_steps and i >= total - end_steps:
            f = (i - (total - end_steps) + 0.5) / float(end_steps)
            if end_root_r is not None:
                rr = r_root + (end_root_r - r_root) * f
            if end_crest_r is not None:
                cr = r_crest + (end_crest_r - r_crest) * f
        sectors.append(
            thread_sector(t0, t1, n0, n1, rr, cr, root_half, crest_half)
        )
    rib = sectors[0]
    for s in sectors[1:]:
        rib = rib.fuse(s)
    return solid_of(rib)


os.makedirs(OUT_DIR, exist_ok=True)

if DOC_NAME in [d.Name for d in App.listDocuments().values()]:
    App.closeDocument(DOC_NAME)
doc = App.newDocument(DOC_NAME)


# ---------------------------------------------------------------------------
# 1. Thin front cap
# ---------------------------------------------------------------------------
cap_profile = [P, P + X * FRONT_R]
steps = 16
for i in range(1, steps + 1):
    u = i / float(steps)
    n = CAP_SEAM_N * u
    r = FRONT_R - (FRONT_R - SEAM_R) * (u ** 1.2)
    cap_profile.append(P + X * r - N * n)
cap_profile.append(P + X * THREAD_CREST_R - N * CAP_SEAM_N)
cap_profile.append(P + X * THREAD_CREST_R - N * CAP_NECK_N)
cap_profile.append(P - N * CAP_NECK_N)

cap_face = Part.Face(Part.makePolygon(cap_profile + [cap_profile[0]]))
front_cap = solid_of(cap_face.revolve(P, N, 360.0))

# Hollow the cap; the 0.5 mm front wall stays.
cap_cavity = Part.makeCylinder(
    POCKET_R, CAP_NECK_N - 0.5, P - N * CAP_NECK_N, N
)
front_cap = front_cap.cut(cap_cavity)

# Battery cradle attached to the front cap; hidden inside the rear body.
cradle_outer = Part.makeCylinder(
    CRADLE_R_OUT, CRADLE_N - 0.5, P - N * CRADLE_N, N
)
cradle_inner = Part.makeCylinder(
    POCKET_R, CRADLE_N - 0.5, P - N * CRADLE_N, N
)
front_cap = front_cap.fuse(cradle_outer.cut(cradle_inner))

# Board screw bosses.
for sx, sy in SCREWS_2D:
    boss_center = P - N * SCREW_BOSS_N + X * sx + S * sy
    boss = Part.makeCylinder(SCREW_BOSS_R, SCREW_BOSS_N - 0.5, boss_center, N)
    front_cap = front_cap.fuse(boss)

# Counterbores, screw holes, screw access holes.
for sx, sy in SCREWS_2D:
    pt = P - N * SCREW_BOSS_N + X * sx + S * sy
    front_cap = front_cap.cut(
        Part.makeCylinder(SCREW_HEAD_R, SCREW_HEAD_DEPTH, pt, N)
    )
    front_cap = front_cap.cut(
        Part.makeCylinder(SCREW_HOLE_R, SCREW_BOSS_N, pt, N)
    )
    access_pt = P - N * ACCESS_N_REAR + X * sx + S * sy
    front_cap = front_cap.cut(
        Part.makeCylinder(ACCESS_R, ACCESS_N_REAR - ACCESS_N_FRONT, access_pt, N)
    )

# Two top openings for the MX1.25 2P battery/speaker connectors.
for sx in (-CONN_X, CONN_X):
    opening_face = plate_rect_face(
        P - N * 0.6 + X * sx + S * CONN_Y,
        CONN_OPENING_W, CONN_OPENING_H
    )
    front_cap = front_cap.cut(opening_face.extrude(N * 0.6))

# 10-pin header opening through the front wall into the battery cradle.
header_opening = plate_rect_face(
    P - N * 0.6 + X * HEADER_X + S * HEADER_Y,
    HEADER_WINDOW_W, HEADER_WINDOW_H
).extrude(N * 3.1)
front_cap = front_cap.cut(header_opening)


def reinforcement_frame(center, outer_w, outer_h, inner_w, inner_h, n0=0.6, n1=1.1):
    outer = plate_rect_face(center - N * n1, outer_w, outer_h).extrude(N * (n1 - n0))
    inner = plate_rect_face(center - N * n1, inner_w, inner_h).extrude(N * (n1 - n0))
    return outer.cut(inner)


for sx in (-CONN_X, CONN_X):
    frame = reinforcement_frame(P + X * sx + S * CONN_Y, 8.0, 7.0, 6.0, 5.0)
    trim = Part.makeCylinder(3.5, 1.2, P - N * 1.2 + S * 20.5, N)
    frame = frame.cut(trim)
    front_cap = front_cap.fuse(frame)

header_frame = reinforcement_frame(P + S * HEADER_Y, 16.0, 6.0, 15.0, 5.0)
front_cap = front_cap.fuse(header_frame)

# External thread near the board.
front_thread = thread_rib(
    THREAD_START_N,
    THREAD_ROOT_R,
    THREAD_CREST_R,
    THREAD_ROOT_HALF,
    THREAD_CREST_HALF,
    end_crest_r=THREAD_END_CREST_R,
)
front_cap = front_cap.fuse(front_thread)

# Keep the visible front face/outer rim at n<2.01 completely.  Only the
# internal part at n>=2.01 that would meet the rear-body floor is cleared
# below z=2.25; the rear-body floor top is z=2, leaving 0.25 mm.
local_half = Part.makeBox(
    80.0, 80.0, 60.0,
    App.Vector(-40.0, -40.0, -(CAP_CLEAR_N_START + 60.0)),
)
tr = App.Matrix()
tr.A11, tr.A12, tr.A13 = X.x, S.x, N.x
tr.A21, tr.A22, tr.A23 = X.y, S.y, N.y
tr.A31, tr.A32, tr.A33 = X.z, S.z, N.z
tr.A14, tr.A24, tr.A34 = P.x, P.y, P.z
local_half.transformShape(tr)
below_cap = Part.makeBox(
    200.0, 200.0, 102.25,
    App.Vector(-100.0, -100.0, -100.0),
)
front_cap = front_cap.cut(local_half.common(below_cap))
front_cap = solid_of(front_cap)

print("Front cap: volume=%.1f bbox=%s" % (front_cap.Volume, front_cap.BoundBox))
print("Front cap valid:", front_cap.isValid(), "solids:", len(front_cap.Solids))


# ---------------------------------------------------------------------------
# 2. Rear body: whole shell, internal thread, bottom plate
# ---------------------------------------------------------------------------
rear_profile = [P + X * SEAM_R - N * CAP_SEAM_N]
rear_profile.append(P + X * SEAM_R - N * CAP_NECK_N)
for i in range(1, 25):
    u = i / 24.0
    n = CAP_NECK_N + (REAR_BACK_N - CAP_NECK_N) * u
    r = SEAM_R * math.sqrt(max(0.0, 1.0 - u * u))
    rear_profile.append(P + X * r - N * n)
rear_profile.append(P - N * CAP_SEAM_N)

rear_face = Part.Face(Part.makePolygon(rear_profile + [rear_profile[0]]))
rear_body = solid_of(rear_face.revolve(P, N, 360.0))

# Counterbore / cavity clears the front-cap thread and cradle.
rear_cavity = Part.makeCylinder(
    REAR_CAVITY_R,
    REAR_CAVITY_N - CAP_SEAM_N,
    P - N * REAR_CAVITY_N,
    N,
)

# Keep the bottom 2 mm of the shell solid: this is the rear-body floor
# that the front cap sits on and the only desktop contact.
above_floor = Part.makeBox(
    140.0, 140.0, 100.0, App.Vector(-70.0, -70.0, BOTTOM_PLATE_TOP)
)
rear_body = rear_body.cut(rear_cavity.common(above_floor))

# Internal thread, also kept above the 2 mm floor.
rear_thread = thread_rib(
    THREAD_START_N,
    REAR_CAVITY_R,
    REAR_GROOVE_CREST_R,
    REAR_GROOVE_ROOT_HALF,
    REAR_GROOVE_CREST_HALF,
    start_angle_deg=0.0,
)
rear_body = rear_body.cut(rear_thread.common(above_floor))

# Flat bottom at z=0.
rear_bottom_cut = Part.makeBox(
    140.0, 140.0, 50.0, App.Vector(-70.0, -70.0, -50.0)
)
rear_body = rear_body.cut(rear_bottom_cut)
rear_body = rear_body.common(
    Part.makeBox(200.0, 200.0, 200.0, App.Vector(-100.0, -100.0, 0.0))
)
rear_body = solid_of(rear_body)

print("Rear body: volume=%.1f bbox=%s" % (rear_body.Volume, rear_body.BoundBox))
print("Rear body valid:", rear_body.isValid(), "solids:", len(rear_body.Solids))


# ---------------------------------------------------------------------------
# 3. Board reference
# ---------------------------------------------------------------------------
board_ref = Part.makeCylinder(BOARD_R, 12.1, P, N)
board_ref_obj = add_feature("Board_Reference", board_ref)


def add_connector_ref(name, sx, sy, width, height, n_front, n_rear, color):
    face = plate_rect_face(P - N * n_front + X * sx + S * sy, width, height)
    shape = face.extrude(-N * (n_rear - n_front))
    obj = add_feature(name, shape)
    try:
        obj.ViewObject.ShapeColor = color
        obj.ViewObject.Visibility = False
    except Exception:
        pass
    return obj


add_connector_ref("Board_Connector_Battery", -CONN_X, CONN_Y, 4.0, 3.0, 0.6, 3.6, (0.95, 0.55, 0.15))
add_connector_ref("Board_Connector_Speaker", CONN_X, CONN_Y, 4.0, 3.0, 0.6, 3.6, (0.15, 0.55, 0.95))
add_connector_ref("Board_Header_10Pin", HEADER_X, HEADER_Y, 12.7, 2.5, 0.6, 3.1, (0.55, 0.85, 0.35))


def add_side_ref(name, sx, sy, width_s, height_n, depth_x, color):
    face = side_rect_face(
        P - N * 0.6 + X * sx + S * sy, width_s, height_n
    )
    shape = face.extrude(X * depth_x)
    obj = add_feature(name, shape)
    try:
        obj.ViewObject.ShapeColor = color
        obj.ViewObject.Visibility = False
    except Exception:
        pass
    return obj


add_side_ref("Board_USB_C", 25.0, 4.0, 9.0, 4.0, 2.0, (0.35, 0.35, 0.35))
add_side_ref("Board_Button_1", -25.0, -8.0, 3.0, 2.0, -2.0, (0.45, 0.45, 0.45))
add_side_ref("Board_Button_2", -25.0, -2.0, 3.0, 2.0, -2.0, (0.45, 0.45, 0.45))
try:
    board_ref_obj.ViewObject.ShapeColor = (0.10, 0.10, 0.12)
    board_ref_obj.ViewObject.Transparency = 10
    board_ref_obj.ViewObject.Visibility = True
except Exception:
    pass

front_obj = add_feature("Front_Shell", front_cap)
rear_obj = add_feature("Rear_Cover", rear_body)

try:
    front_obj.ViewObject.ShapeColor = (0.82, 0.82, 0.82)
    rear_obj.ViewObject.ShapeColor = (0.72, 0.72, 0.72)
except Exception:
    pass

doc.recompute()


# ---------------------------------------------------------------------------
# 4. Export
# ---------------------------------------------------------------------------
export_stl(front_cap, "front_shell.stl")
export_stl(rear_body, "rear_cover.stl")

Part.export([front_obj, rear_obj], os.path.join(OUT_DIR, "stand.step"))
doc.saveAs(os.path.join(OUT_DIR, "stand.FCStd"))

print("Exported to:", OUT_DIR)
print("P=%s" % P)
