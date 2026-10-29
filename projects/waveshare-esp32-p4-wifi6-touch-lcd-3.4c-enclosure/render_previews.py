import math
import struct
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
CACHE = ROOT / "archive" / "preview_meshes"
NORMAL = (0, -math.sin(math.radians(40)), math.cos(math.radians(40)))

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


def read_stl(name, color, transform=None):
    data = (CACHE / name).read_bytes()
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


rear = read_stl('rear_cover.stl', (181,194,191))
frame = read_stl('main_shell.stl', (132,151,153))
fasteners = read_stl('fasteners.stl', (192,144,63))
module = read_stl('module.stl', (28,32,34))
speaker = read_stl('speaker.stl', (66,117,86))
section = read_stl('section.stl', (181,194,191))
assembly = rear+frame+module
render('preview_front.png', assembly, NORMAL)
front=Image.open(OUT/'preview_front.png').convert('RGB')
exposed=sum(pixel!=(250,250,249) and max(pixel)>60 for pixel in front.getdata())
assert exposed==0, '正面可见打印件像素：'+str(exposed)
render('preview_iso.png', assembly, (1,-1,0.65))
render('preview_rear.png', assembly, (0.5,1,0.65))
render('preview_side.png', assembly, (1,0,0.1))
render('preview_bottom.png', rear, (0,0,-1))
render('preview_cover_inside.png', rear, NORMAL)
render('preview_section.png', section+frame+speaker+fasteners, (-1,-0.3,0.2))
render('preview_speaker_mount.png', frame+speaker+fasteners, tuple(-v for v in NORMAL))
render('preview_fastening.png', frame+fasteners, tuple(-v for v in NORMAL))

def shifted(triangles, offset):
    return [(tuple(tuple(p[i]+offset[i] for i in range(3)) for p in vertices),color)
            for vertices,color in triangles]

render('preview_exploded.png', module+frame
       +shifted(speaker,tuple(-25*v for v in NORMAL))
       +shifted(rear,tuple(-80*v for v in NORMAL)),(1,-0.6,0.5))
font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
for filename, caption in (
    ('preview_front.png','沿屏幕法线正视：打印结构全部隐藏在原模块轮廓后方'),
    ('preview_section.png','剖视：绿色为音箱占位；一体定位柱与后盖压耳，底板封闭'),
    ('preview_exploded.png','两个打印件：主壳固定模块 → 放入音箱并接线 → 套后盖、锁两颗 M3'),
    ('preview_fastening.png','主壳背面：四处 M4 模块固定座；下方两处捕获螺母和 M3 锁盖'),
    ('preview_speaker_mount.png','音箱安装参考：100×45×21 mm；孔距 90×36 mm；Ø5 mm 定位柱'),
):
    canvas=Image.open(OUT/filename)
    draw=ImageDraw.Draw(canvas)
    draw.rectangle((0,850,900,900),fill=(250,250,249))
    draw.text((15,865),caption,font=font,fill=(40,45,45))
    canvas.save(OUT/filename)
