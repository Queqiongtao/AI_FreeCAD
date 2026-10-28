"""Pebble desk stand for the ESP32-S3-Touch-AMOLED-1.75-B.

Single-file parametric source.  Outputs to ./output/:
  front_shell.stl, rear_cover.stl, stand.step, stand.FCStd

Run with freecadcmd stand.py, or in the FreeCAD GUI console from the
project directory:

    exec(open(r"stand.py", encoding="utf-8").read())

Design:
  * screen 50 deg from horizontal (40 deg from vertical)
  * board/screw pattern rotated 90 deg CCW:
      top screw (0, +20.50), bottom screws (+/-13.75, -14.70)
  * two 5 x 4 mm top openings through the front wall at (+/-6.5, +17.25)
  * 10-pin 2x5 header opening through the front wall at (0, -18.70)
  * 6 o'clock battery slot, ledge notch and internal channel removed
  * no side slots: the two buttons and USB-C are on the side edge
  * helical ramp + compliant lug finger preload
  * no battery support ledge; the battery is held by the rear cover and
    a foam/tape pad, so no rib connects the screw bosses

Board orientation (image = board back, correct):
  * two MX1.25 2P connectors at the top, openings face down/inward
  * 10-pin 2x5 header at the bottom
  * USB-C and the two buttons are on the side edge, no front openings
"""

import math
import os

import FreeCAD as App
import Part
import MeshPart

DOC_NAME = "Pebble_Stand"

# Keep the script portable: use the script's folder when run with
# freecadcmd; fall back to the current directory when exec'd in the GUI.
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
EQ_N = 12.0
BACK_N = 25.0

POCKET_R = 21.3
POCKET_D = 11.5
# Screw access holes at the old ledge plane; no ledge is printed.
ACCESS_N_FRONT = 2.5
ACCESS_N_REAR = 3.0

SCREW_BOSS_R = 3.0
SCREW_BOSS_N = 2.5
SCREW_HEAD_R = 2.2
SCREW_HEAD_DEPTH = 1.5
SCREW_HOLE_R = 1.15
ACCESS_R = 2.3

# Bayonet.  The three-lug pattern is rotated -10 deg (entries
# 320/80/200 instead of 330/90/210) so the bottom lug at 225 deg clears
# the 2 mm bottom plate at the 50 deg recline; the spacing stays 120 deg.
ENTRY_ANGLES = (320.0, 80.0, 200.0)
LOCK_OFFSET = 25.0
ENTRY_HALF = 6.0
LUG_HALF = 5.0
POCKET_START = -6.0
POCKET_END = 30.0
ENTRY_N_FRONT = 6.0
ENTRY_N_REAR = 12.0
POCKET_N_FRONT = 6.0
POCKET_N_REAR = 9.0
LUG_N_FRONT = 6.3
LUG_N_REAR = 8.9
LUG_INNER_R = 22.2
LUG_OUTER_R = 23.5
POCKET_OUTER_R = 23.7
NOTCH_INNER_R = 22.5
NOTCH_OUTER_R = 23.5

# Lower guide / bottom
GUIDE_INNER_R = 21.5
GUIDE_OUTER_R = 22.3
GUIDE_BOTTOM_CUT = 2.1
BOTTOM_PLATE_TOP = 2.0
# Height of the temporary disk that closes the pocket before the final
# 2.0 mm bottom plate is fused.  Define it explicitly for portable runs.
BOTTOM_RING_TOP = 0.5

# Helical bayonet ramp + compliant finger.
# The rigid front block carries the pull-out load; the thin rear finger is the
# axial spring.  The L-slot rear wall ramps from POCKET_N_REAR at the pocket
# start to RAMP_END_N at the locked angle.
LUG_BLOCK_N_REAR = 7.3      # rigid block n=6.3..7.3
FINGER_R_IN = 22.6
FINGER_R_OUT = 23.05
RAMP_END_N = 8.85           # L-slot rear wall at the locked angle
RAMP_STEPS = 24
FINGER_ROOT_FILLET = 0.2

SCREWS_2D = [
    (0.0, 20.50),
    (13.75, -14.70),
    (-13.75, -14.70),
]

# Board connectors (board back, corrected orientation).
CONN_X = 6.5
CONN_Y = 17.25
CONN_OPENING_W = 5.0
CONN_OPENING_H = 4.0
HEADER_X = 0.0
HEADER_Y = -18.70
HEADER_WINDOW_W = 14.0
HEADER_WINDOW_H = 4.0
SPEAKER_EXIT_W = 5.0
SPEAKER_EXIT_H = 3.0

TILT = math.radians(TILT_DEG)
SIN = math.sin(TILT)
COS = math.cos(TILT)
N = App.Vector(0.0, -SIN, COS)
S = App.Vector(0.0, COS, SIN)
X = App.Vector(1.0, 0.0, 0.0)
Z = App.Vector(0.0, 0.0, 1.0)

P = App.Vector(0.0, 0.0, BOTTOM_GAP + BOARD_R * SIN)
EQ_PLANE = P - N * EQ_N


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
    """Rectangle in the S/N plane, for side-wall cutouts (normal X)."""
    pts = [
        center - S * (width_s / 2.0) - N * (height_n / 2.0),
        center + S * (width_s / 2.0) - N * (height_n / 2.0),
        center + S * (width_s / 2.0) + N * (height_n / 2.0),
        center - S * (width_s / 2.0) + N * (height_n / 2.0),
    ]
    return Part.Face(Part.makePolygon(pts + [pts[0]]))


def top_rect_face(center, width_x, height_n):
    """Rectangle in the X/N plane, for top/bottom outer-wall cutouts (normal S)."""
    pts = [
        center - X * (width_x / 2.0) - N * (height_n / 2.0),
        center + X * (width_x / 2.0) - N * (height_n / 2.0),
        center + X * (width_x / 2.0) + N * (height_n / 2.0),
        center - X * (width_x / 2.0) + N * (height_n / 2.0),
    ]
    return Part.Face(Part.makePolygon(pts + [pts[0]]))


def ann_sector(r_in, r_out, a0, a1, n_front, n_rear, steps=12):
    """Annular sector solid from depth n_front to n_rear.

    The face is built at n_rear and extruded along +N, which decreases n.
    """
    if n_rear <= n_front:
        raise ValueError("n_rear must be greater than n_front")
    pts = []
    for i in range(steps + 1):
        a = math.radians(a0 + (a1 - a0) * i / steps)
        pts.append(
            P - N * n_rear
            + X * (r_out * math.cos(a))
            + S * (r_out * math.sin(a))
        )
    for i in range(steps + 1):
        a = math.radians(a1 + (a0 - a1) * i / steps)
        pts.append(
            P - N * n_rear
            + X * (r_in * math.cos(a))
            + S * (r_in * math.sin(a))
        )
    face = Part.Face(Part.makePolygon(pts + [pts[0]]))
    return face.extrude(N * (n_rear - n_front))


def ramped_ann_sector(r_in, r_out, a0, a1, n_front, n_rear_start, n_rear_end, steps=RAMP_STEPS):
    """Annular sector whose rear wall ramps linearly in n over the arc.

    The pocket is split into ``steps`` narrow sectors.  The rear wall is a
    fine staircase (0.15 mm / 24 = 6 um per step), which the compliant lug
    finger smooths out in use.
    """
    pieces = []
    for i in range(steps):
        t0 = i / float(steps)
        t1 = (i + 1) / float(steps)
        aa0 = a0 + (a1 - a0) * t0
        aa1 = a0 + (a1 - a0) * t1
        tm = 0.5 * (t0 + t1)
        nr = n_rear_start + (n_rear_end - n_rear_start) * tm
        pieces.append(ann_sector(r_in, r_out, aa0, aa1, n_front, nr, steps=4))
    pocket = pieces[0]
    for p in pieces[1:]:
        pocket = pocket.fuse(p)
    return pocket


os.makedirs(OUT_DIR, exist_ok=True)

if DOC_NAME in [d.Name for d in App.listDocuments().values()]:
    App.closeDocument(DOC_NAME)
doc = App.newDocument(DOC_NAME)

# ---------------------------------------------------------------------------
# 1. Front shell body
# ---------------------------------------------------------------------------
profile_pts = [P, P + X * FRONT_R]
steps = 24
for i in range(1, steps + 1):
    u = i / steps
    n = EQ_N * u
    r = FRONT_R - (FRONT_R - SEAM_R) * (u ** 1.2)
    profile_pts.append(P + X * r - N * n)
profile_pts.append(P - N * EQ_N)

front_face = Part.Face(Part.makePolygon(profile_pts + [profile_pts[0]]))
front_body = front_face.revolve(P, N, 360.0)
front_body = solid_of(front_body)
front_shell = front_body.copy()

# Circular battery pocket.
pocket = Part.makeCylinder(POCKET_R, POCKET_D, EQ_PLANE, N)
front_shell = front_shell.cut(pocket)

# Smooth guide bore: Ø45 from n = 12 to n = 6.
bore = Part.makeCylinder(22.5, 6.0, EQ_PLANE, N)
front_shell = front_shell.cut(bore)

# Full bottom floor closes the pocket/bore at the resting plane.
bottom_disk = Part.makeCylinder(POCKET_OUTER_R, POCKET_D, EQ_PLANE, N)
bottom_disk = bottom_disk.common(
    Part.makeBox(80.0, 80.0, BOTTOM_RING_TOP + 1.0, App.Vector(-40.0, -40.0, -1.0))
)
front_shell = front_shell.fuse(bottom_disk)

# No battery support ledge at all.  The three screw
# bosses stay independent, the cable path is fully open, and the battery
# is held by the rear cover / a foam or tape pad.  The screw access holes
# below are the only features left at the old ledge plane.

# Screw bosses.
for sx, sy in SCREWS_2D:
    boss_center = P - N * SCREW_BOSS_N + X * sx + S * sy
    boss = Part.makeCylinder(SCREW_BOSS_R, SCREW_BOSS_N - 0.5, boss_center, N)
    front_shell = front_shell.fuse(boss)

# Counterbores, screw holes, screw access holes.
for sx, sy in SCREWS_2D:
    pt = P - N * SCREW_BOSS_N + X * sx + S * sy
    front_shell = front_shell.cut(
        Part.makeCylinder(SCREW_HEAD_R, SCREW_HEAD_DEPTH, pt, N)
    )
    front_shell = front_shell.cut(
        Part.makeCylinder(SCREW_HOLE_R, SCREW_BOSS_N, pt, N)
    )
    access_pt = P - N * ACCESS_N_REAR + X * sx + S * sy
    front_shell = front_shell.cut(
        Part.makeCylinder(ACCESS_R, ACCESS_N_REAR - ACCESS_N_FRONT, access_pt, N)
    )

# Two top openings for the MX1.25 2P battery/speaker connectors.
# They pass through the front wall directly into the battery pocket; the
# 6 o'clock battery slot, ledge notch and internal channel are removed.
for sx in (-CONN_X, CONN_X):
    opening_face = plate_rect_face(
        P - N * 0.6 + X * sx + S * CONN_Y,
        CONN_OPENING_W, CONN_OPENING_H
    )
    front_shell = front_shell.cut(opening_face.extrude(N * 0.6))

# 10-pin header opening through the front wall into the battery pocket.
header_opening = plate_rect_face(
    P - N * 0.6 + X * HEADER_X + S * HEADER_Y,
    HEADER_WINDOW_W, HEADER_WINDOW_H
).extrude(N * 3.1)
front_shell = front_shell.cut(header_opening)

# Local reinforcement frames on the battery-pocket side.
def reinforcement_frame(center, outer_w, outer_h, inner_w, inner_h, n0=0.6, n1=1.1):
    outer = plate_rect_face(center - N * n1, outer_w, outer_h).extrude(N * (n1 - n0))
    inner = plate_rect_face(center - N * n1, inner_w, inner_h).extrude(N * (n1 - n0))
    return outer.cut(inner)

for sx in (-CONN_X, CONN_X):
    frame = reinforcement_frame(P + X * sx + S * CONN_Y, 8.0, 7.0, 6.0, 5.0)
    # Keep 0.5 mm clear of the top screw boss at (0, 20.5).
    trim = Part.makeCylinder(3.5, 1.2, P - N * 1.2 + S * 20.5, N)
    frame = frame.cut(trim)
    front_shell = front_shell.fuse(frame)

header_frame = reinforcement_frame(P + S * HEADER_Y, 16.0, 6.0, 15.0, 5.0)
front_shell = front_shell.fuse(header_frame)

# No outer-wall or side slots: buttons/USB are on the side edge and do not
# interfere; the rear cover is completely closed.

# Bayonet L-slots: axial entry + ramped circumferential pocket + 0.4 mm notch.
# The rear wall ramps forward over the twist so the compliant finger is pulled
# against the seam at the locked position.
for entry in ENTRY_ANGLES:
    entry_slot = ann_sector(
        22.5, POCKET_OUTER_R, entry - ENTRY_HALF, entry + ENTRY_HALF,
        ENTRY_N_FRONT, ENTRY_N_REAR
    )
    ramp_pocket = ramped_ann_sector(
        22.5, POCKET_OUTER_R,
        entry + POCKET_START, entry + LOCK_OFFSET,
        POCKET_N_FRONT, POCKET_N_REAR, RAMP_END_N,
        steps=RAMP_STEPS
    )
    flat_pocket = ann_sector(
        22.5, POCKET_OUTER_R,
        entry + LOCK_OFFSET, entry + POCKET_END,
        POCKET_N_FRONT, RAMP_END_N
    )
    detent_notch = ann_sector(
        NOTCH_INNER_R, NOTCH_OUTER_R, entry + POCKET_END, entry + POCKET_END + 1.0,
        POCKET_N_FRONT, POCKET_N_REAR
    )
    front_shell = front_shell.cut(
        entry_slot.fuse(ramp_pocket).fuse(flat_pocket).fuse(detent_notch)
    )

# Flat bottom at Z=0.
bottom_cut = Part.makeBox(140.0, 140.0, 50.0, App.Vector(-70.0, -70.0, -50.0))
front_shell = front_shell.cut(bottom_cut)
front_shell = solid_of(front_shell)

# Close the underside with a 2.0 mm plate trimmed to the exact body outline.
# This covers the pocket/bore opening without growing the footprint.
plate_raw = Part.makeBox(
    100.0, 100.0, BOTTOM_PLATE_TOP, App.Vector(-50.0, -50.0, 0.0)
)
plate = plate_raw.common(front_body)
front_shell = front_shell.fuse(plate)
front_shell = solid_of(front_shell)
print("Bottom plate: volume=%.1f" % plate.Volume)
print("Front shell: volume=%.1f bbox=%s" % (front_shell.Volume, front_shell.BoundBox))
print("Front shell valid:", front_shell.isValid(), "solids:", len(front_shell.Solids))

# ---------------------------------------------------------------------------
# 2. Rear cover
# ---------------------------------------------------------------------------
rear_profile = [P + X * SEAM_R - N * EQ_N]
for i in range(1, 25):
    u = i / 24.0
    n = EQ_N + (BACK_N - EQ_N) * u
    r = SEAM_R * math.sqrt(max(0.0, 1.0 - u * u))
    rear_profile.append(P + X * r - N * n)
rear_profile.append(P - N * EQ_N)
rear_face = Part.Face(Part.makePolygon(rear_profile + [rear_profile[0]]))
rear_cover = rear_face.revolve(P, N, 360.0)
rear_cover = solid_of(rear_cover)

# Smooth lower guide neck.
neck_start = EQ_PLANE - N * 0.5
# Relieve the neck front end 0.3 mm so the seam face, not the
# neck/shoulder pair, is the axial hard stop.
neck_len = 6.2
neck_outer = Part.makeCylinder(GUIDE_OUTER_R, neck_len, neck_start, N)
neck_inner = Part.makeCylinder(GUIDE_INNER_R, neck_len, neck_start, N)
neck = neck_outer.cut(neck_inner)
# Remove the guide below the bottom ring gap.
guide_cut = Part.makeBox(
    80.0, 80.0, 20.0 + GUIDE_BOTTOM_CUT, App.Vector(-40.0, -40.0, -20.0)
)
neck = neck.cut(guide_cut)
rear_cover = rear_cover.fuse(neck)

# 3 locked bayonet lugs: rigid front block + compliant rear finger + detent.
for entry in ENTRY_ANGLES:
    locked = entry + LOCK_OFFSET
    block = ann_sector(
        LUG_INNER_R, LUG_OUTER_R, locked - LUG_HALF, locked + LUG_HALF,
        LUG_N_FRONT, LUG_BLOCK_N_REAR
    )
    finger = ann_sector(
        FINGER_R_IN, FINGER_R_OUT, locked - LUG_HALF, locked + LUG_HALF,
        LUG_BLOCK_N_REAR, LUG_N_REAR
    )
    if FINGER_ROOT_FILLET > 0:
        try:
            # The root is the finger face at n=7.3 (closest to the axis plane
            # P along N).  Fillet its boundary to reduce the root stress.
            root_face = min(
                finger.Faces, key=lambda f: (P - f.CenterOfMass).dot(N)
            )
            finger = finger.makeFillet(FINGER_ROOT_FILLET, root_face.Edges)
        except Exception:
            pass
    bump = ann_sector(
        LUG_INNER_R, LUG_OUTER_R, entry + POCKET_END, entry + POCKET_END + 1.0,
        LUG_N_FRONT, LUG_BLOCK_N_REAR
    )
    rear_cover = rear_cover.fuse(block).fuse(finger).fuse(bump)

# Flat bottom at Z=0.
rear_cover = rear_cover.cut(bottom_cut)

rear_cover = solid_of(rear_cover)
print("Rear cover: volume=%.1f bbox=%s" % (rear_cover.Volume, rear_cover.BoundBox))
print("Rear cover valid:", rear_cover.isValid(), "solids:", len(rear_cover.Solids))

# ---------------------------------------------------------------------------
# 3. Board reference
# ---------------------------------------------------------------------------
board_ref = Part.makeCylinder(BOARD_R, 12.1, P, N)
board_ref_obj = add_feature("Board_Reference", board_ref)

# Connector references (not printed): 2x MX1.25 2P at the top,
# 10-pin 2x5 header at the bottom, and the side USB/buttons.
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

# Side USB-C on the right, two buttons on the left (cylindrical side).
add_side_ref("Board_USB_C", 25.0, 4.0, 9.0, 4.0, 2.0, (0.35, 0.35, 0.35))
add_side_ref("Board_Button_1", -25.0, -8.0, 3.0, 2.0, -2.0, (0.45, 0.45, 0.45))
add_side_ref("Board_Button_2", -25.0, -2.0, 3.0, 2.0, -2.0, (0.45, 0.45, 0.45))
try:
    board_ref_obj.ViewObject.ShapeColor = (0.10, 0.10, 0.12)
    board_ref_obj.ViewObject.Transparency = 10
    board_ref_obj.ViewObject.Visibility = True
except Exception:
    pass

front_obj = add_feature("Front_Shell", front_shell)
rear_obj = add_feature("Rear_Cover", rear_cover)

try:
    front_obj.ViewObject.ShapeColor = (0.82, 0.82, 0.82)
    rear_obj.ViewObject.ShapeColor = (0.72, 0.72, 0.72)
except Exception:
    pass

doc.recompute()

# ---------------------------------------------------------------------------
# 4. Export
# ---------------------------------------------------------------------------
export_stl(front_shell, "front_shell.stl")
export_stl(rear_cover, "rear_cover.stl")

Part.export([front_obj, rear_obj], os.path.join(OUT_DIR, "stand.step"))
doc.saveAs(os.path.join(OUT_DIR, "stand.FCStd"))

print("Exported to:", OUT_DIR)
print("P=%s" % P)
