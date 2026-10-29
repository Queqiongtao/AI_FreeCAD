"""从 STL 生成静态预览；只需 Python 与 Pillow，不参与建模。"""

import ast
import math
import struct
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
SOURCE = ast.parse((ROOT / "stand.py").read_text(encoding="utf-8"))
PARAMS = {}
for node in SOURCE.body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        target = node.targets[0]
        if isinstance(target, ast.Name):
            try:
                PARAMS[target.id] = ast.literal_eval(node.value)
            except (ValueError, TypeError):
                pass

ANGLE = math.radians(PARAMS["TILT_DEG"])
SIN, COS = math.sin(ANGLE), math.cos(ANGLE)
MODULE_R = PARAMS["MODULE_R"]
MODULE_DEPTH = PARAMS["MODULE_DEPTH"]
PZ = PARAMS["MODULE_BOTTOM_CLEARANCE"] + MODULE_R * SIN + MODULE_DEPTH * COS
NORMAL = (0.0, -SIN, COS)


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def unit(a):
    length = math.sqrt(dot(a, a))
    return tuple(x / length for x in a)


def module_point(radius, theta, depth):
    return (
        radius * math.cos(theta),
        radius * math.sin(theta) * COS + depth * SIN,
        PZ + radius * math.sin(theta) * SIN - depth * COS,
    )


def module_triangles():
    triangles = []
    front = (0.0, 0.0, PZ)
    back = module_point(0, 0, MODULE_DEPTH)
    for i in range(96):
        a = 2 * math.pi * i / 96
        b = 2 * math.pi * (i + 1) / 96
        f0, f1 = module_point(MODULE_R, a, 0), module_point(MODULE_R, b, 0)
        b0 = module_point(MODULE_R, a, MODULE_DEPTH)
        b1 = module_point(MODULE_R, b, MODULE_DEPTH)
        triangles.extend([
            ((front, f0, f1), (27, 31, 33)),
            ((back, b1, b0), (38, 42, 44)),
            ((f0, b0, b1), (43, 47, 49)),
            ((f0, b1, f1), (43, 47, 49)),
        ])
    return triangles


def carrier_to_assembly(point):
    x, y, z = point
    s = y - PZ * SIN
    n = PARAMS["CARRIER_BACK_N"] - z
    return (x, s * COS + n * SIN, PZ + s * SIN - n * COS)


def read_stl(name, color, transform=None):
    data = (OUT / name).read_bytes()
    count = struct.unpack_from("<I", data, 80)[0]
    assert len(data) == 84 + count * 50, name
    triangles = []
    for i in range(count):
        values = struct.unpack_from("<12f", data, 84 + i * 50)
        vertices = tuple(
            tuple(values[j:j + 3]) for j in (3, 6, 9)
        )
        if transform:
            vertices = tuple(transform(point) for point in vertices)
        triangles.append((vertices, color))
    return triangles


def render(filename, triangles, camera):
    eye = unit(camera)
    world_up = (0, 0, 1) if abs(eye[2]) < 0.95 else (0, 1, 0)
    right = unit(cross(world_up, eye))
    up = cross(eye, right)
    projected = []
    xs, ys = [], []
    light = unit((0.5, -0.7, 1.0))
    for vertices, base in triangles:
        a, b, c = vertices
        normal = unit(cross(sub(b, a), sub(c, a)))
        intensity = 0.65 + 0.35 * max(0.0, dot(normal, light))
        color = tuple(min(255, int(channel * intensity)) for channel in base)
        points = [
            (dot(vertex, right), dot(vertex, up), dot(vertex, eye))
            for vertex in vertices
        ]
        projected.append((points, color))
        xs.extend(point[0] for point in points)
        ys.extend(point[1] for point in points)

    width = 900
    scale = 740 / max(max(xs) - min(xs), max(ys) - min(ys))
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    canvas = Image.new("RGB", (width, width), (250, 250, 249))
    pixels_out = canvas.load()
    depths = [-float("inf")] * (width * width)
    for points, color in projected:
        pixels = [
            (width / 2 + (x - cx) * scale, width / 2 - (y - cy) * scale, z)
            for x, y, z in points
        ]
        (ax, ay, az), (bx, by, bz), (cx2, cy2, cz) = pixels
        denominator = (by - cy2) * (ax - cx2) + (cx2 - bx) * (ay - cy2)
        if abs(denominator) < 1e-8:
            continue
        left = max(0, int(min(ax, bx, cx2)))
        right_edge = min(width - 1, int(max(ax, bx, cx2)) + 1)
        top = max(0, int(min(ay, by, cy2)))
        bottom = min(width - 1, int(max(ay, by, cy2)) + 1)
        for py in range(top, bottom + 1):
            for px in range(left, right_edge + 1):
                u = ((by - cy2) * (px - cx2) + (cx2 - bx) * (py - cy2)) / denominator
                v = ((cy2 - ay) * (px - cx2) + (ax - cx2) * (py - cy2)) / denominator
                if u < 0 or v < 0 or u + v > 1:
                    continue
                depth = u * az + v * bz + (1 - u - v) * cz
                index = py * width + px
                if depth > depths[index]:
                    depths[index] = depth
                    pixels_out[px, py] = color
    if filename in ("preview_bottom.png", "preview_cover_inside.png", "preview_pocket.png"):
        for py in range(1, width - 1):
            for px in range(1, width - 1):
                index = py * width + px
                if depths[index] == -float("inf"):
                    continue
                if any(
                    depths[neighbor] == -float("inf")
                    or abs(depths[neighbor] - depths[index]) > 0.4
                    for neighbor in (index - 1, index + 1, index - width, index + width)
                ):
                    pixels_out[px, py] = tuple(
                        int(channel * 0.78) for channel in pixels_out[px, py]
                    )
    canvas.save(OUT / filename)
    print(filename)


rear = read_stl("rear_cover.stl", (186, 194, 191))
carrier_print = read_stl("mount_carrier.stl", (140, 153, 152))
carrier = read_stl("mount_carrier.stl", (140, 153, 152), carrier_to_assembly)
module = module_triangles()
assembled = rear + carrier + module
render("preview_iso.png", assembled, (1.0, -1.0, 0.75))
render("preview_front.png", assembled, NORMAL)
render("preview_rear.png", assembled, (0.7, 1.0, 0.5))
render("preview_side.png", assembled, (1.0, 0.0, 0.15))
render("preview_side_left.png", assembled, (-1.0, 0.0, 0.15))
render("preview_bottom.png", rear, (0.0, 0.0, -1.0))
render("preview_cover.png", rear, (0.8, 1.0, 0.8))
render("preview_cover_inside.png", rear, NORMAL)
render("preview_pocket.png", carrier_print, (0.0, 0.0, 1.0))

# 辅助几何由同一参数化建模脚本导出，保持与 CAD 一致。
aux = ROOT / "archive" / "preview_meshes"
battery = read_stl(aux / "battery_reference.stl", (91, 168, 104))
plugs = read_stl(aux / "connector_reference.stl", (235, 182, 65))
wires = read_stl(aux / "wire_reference.stl", (205, 101, 65))
adhesive = read_stl(aux / "adhesive_reference.stl", (77, 140, 210))
section = read_stl(aux / "section.stl", (186, 194, 191))
render("preview_section.png", section + carrier + battery + plugs + wires + adhesive,
       (-1.0, -0.3, 0.3))
render("preview_installation.png", carrier + battery + plugs + wires + adhesive, NORMAL)

def shifted(triangles, delta):
    return [(tuple(tuple(p[i] + delta[i] for i in range(3)) for p in vertices), color)
            for vertices, color in triangles]

render("preview_exploded.png", module + carrier + plugs + wires
       + shifted(rear + battery + adhesive, tuple(-32 * v for v in NORMAL)),
       (1.0, -0.6, 0.45))

font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 20)
for filename, caption in (
    ("preview_section.png", "剖视：绿色为电池尺寸参考，蓝色为通用粘贴区；非实际固定位置"),
    ("preview_installation.png", "接线空间：黄色为两个 2P 插头，橙色为走线预留包络"),
    ("preview_exploded.png", "装配示意：先固定支架并接线，再固定壳内元件、收线、合壳"),
):
    canvas = Image.open(OUT / filename)
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 845, 900, 900), fill=(250, 250, 249))
    draw.text((20, 855), caption, font=font, fill=(40, 45, 45))
    canvas.save(OUT / filename)
