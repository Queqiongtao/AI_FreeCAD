# -*- coding: utf-8 -*-
"""离线爆炸图渲染：VTK 离屏出帧 + Pillow 合成 + ffmpeg 编码。

运行环境为 FreeCAD 自带 Python（含 vtk 9.3 / numpy / Pillow），不依赖 GUI。
"""

import os
import shutil
import subprocess
import sys
import time

import numpy as np
import vtk
from PIL import Image, ImageFilter
from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray, vtk_to_numpy

from . import palette
from .scene import assembly_axis, front_direction, load_scene


def find_ffmpeg():
    """按 环境变量 → PATH → 常见安装路径 的顺序查找 ffmpeg。"""
    candidates = [
        os.environ.get("EXPLODE_FFMPEG"),
        shutil.which("ffmpeg"),
        r"D:\Program\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\ffmpeg\bin\ffmpeg.exe",
    ]
    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            return candidate
    raise RuntimeError(
        "找不到 ffmpeg。请安装后加入 PATH，或设置环境变量 EXPLODE_FFMPEG 指向 ffmpeg 可执行文件。"
    )


def find_freecadcmd():
    """优先用当前解释器同目录的 freecadcmd，其次查 PATH。"""
    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    for name in ("freecadcmd.exe", "freecadcmd"):
        candidate = os.path.join(exe_dir, name)
        if os.path.isfile(candidate):
            return candidate
    found = shutil.which("freecadcmd")
    if found:
        return found
    raise RuntimeError(
        "找不到 freecadcmd。请用 FreeCAD 自带的 python.exe 运行，或把 FreeCAD 的 bin 目录加入 PATH。"
    )


def export_scene(cfg, project_root):
    """调用 freecadcmd 从 FCStd 导出网格缓存（装配位姿）。"""
    scene_cfg = cfg["scene"]
    doc = os.path.join(project_root, scene_cfg["doc"])
    npz = os.path.join(project_root, scene_cfg["npz"])
    manifest = os.path.join(project_root, scene_cfg["manifest"])
    if not os.path.isfile(doc):
        raise RuntimeError("源工程不存在：%s" % doc)

    env = dict(os.environ)
    env.update({
        "EXPLODE_DOC": doc,
        "EXPLODE_OUT": npz,
        "EXPLODE_MANIFEST": manifest,
        "EXPLODE_DEFLECTION": str(scene_cfg.get("deflection", 0.15)),
        "EXPLODE_ANGULAR": str(scene_cfg.get("angular", 0.25)),
        "EXPLODE_ONLY": ",".join(scene_cfg.get("only", [])),
        "EXPLODE_OVERRIDE": ",".join(
            "%s=%s" % (name, value) for name, value in scene_cfg.get("overrides", {}).items()
        ),
        "PYTHONIOENCODING": "utf-8",
    })
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "export_meshes.py")
    os.makedirs(os.path.dirname(npz), exist_ok=True)
    print("导出网格：%s" % doc, flush=True)
    result = subprocess.run(
        [find_freecadcmd(), script],
        env=env, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode != 0 or not os.path.isfile(npz):
        raise RuntimeError(
            "网格导出失败（退出码 %s）。\n%s\n%s"
            % (result.returncode, result.stdout[-1500:], result.stderr[-1500:])
        )
    print("网格已导出：%s" % npz, flush=True)
    return npz


# ---------------------------------------------------------------- 几何与材质

def _polydata(part):
    """三角网格 → 带平滑法线的 vtkPolyData。

    OCC 三角化会产生未焊接的重复顶点且三角形绕序不一致，直接算法线会出现
    条纹。先合并顶点，再由 vtkPolyDataNormals 统一绕序并按 40° 保留硬边。
    """
    verts = part.verts.astype(np.float64)
    faces = part.faces.astype(np.int64)
    points = vtk.vtkPoints()
    points.SetData(numpy_to_vtk(verts, deep=True))
    padded = np.hstack([
        np.full((len(faces), 1), 3, dtype=np.int64),
        faces,
    ]).ravel()
    cells = vtk.vtkCellArray()
    cells.SetCells(len(faces), numpy_to_vtkIdTypeArray(padded, deep=True))
    data = vtk.vtkPolyData()
    data.SetPoints(points)
    data.SetPolys(cells)

    clean = vtk.vtkCleanPolyData()
    clean.SetInputData(data)
    clean.SetPointMerging(1)
    clean.SetToleranceIsAbsolute(True)
    clean.SetAbsoluteTolerance(1e-4)
    clean.Update()

    normals = vtk.vtkPolyDataNormals()
    normals.SetInputConnection(clean.GetOutputPort())
    normals.SetFeatureAngle(40.0)
    normals.SplittingOn()
    normals.ConsistencyOn()
    normals.AutoOrientNormalsOn()
    normals.Update()
    return normals.GetOutput()


def _make_actor(part):
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(_polydata(part))
    mapper.ScalarVisibilityOff()
    mapper.SetResolveCoincidentTopologyToPolygonOffset()
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.SetPickable(0)
    prop = actor.GetProperty()
    prop.SetInterpolationToPhong()
    material = palette.MATERIALS[palette.role_of(part.name)]
    prop.SetColor(*material["color"])
    prop.SetAmbient(material["ambient"])
    prop.SetDiffuse(material["diffuse"])
    prop.SetSpecular(material["specular"])
    prop.SetSpecularPower(material["specular_power"])
    prop.SetOpacity(material.get("opacity", 1.0))
    # 金属件加一点环境色，避免背光面死黑
    prop.SetAmbientColor(*[min(1.0, c * 1.06) for c in material["color"]])
    return actor


# ---------------------------------------------------------------- 渲染器

class Renderer:
    def __init__(self, scene, cfg):
        self.scene = scene
        self.cfg = cfg
        self.width = int(cfg["video"]["width"])
        self.height = int(cfg["video"]["height"])
        self.ssaa = int(cfg["video"].get("ssaa", 2))

        self.ren = vtk.vtkRenderer()
        self.ren.SetBackground(0.965, 0.960, 0.950)
        self.ren.SetBackgroundAlpha(0.0)
        self.ren.SetLightFollowCamera(False)
        self.ren.SetTwoSidedLighting(os.environ.get("EXPLODE_TWO_SIDED") == "1")

        self.window = vtk.vtkRenderWindow()
        self.window.SetOffScreenRendering(1)
        self.window.SetAlphaBitPlanes(1)
        self.window.SetMultiSamples(0)
        self.window.AddRenderer(self.ren)
        self.window.SetSize(self.width * self.ssaa, self.height * self.ssaa)

        self.actors = {}
        grouped = {name for spec in cfg["groups"].values() for name in spec["objects"]}
        missing = grouped - {part.name for part in scene.parts}
        if missing:
            raise KeyError("配置里的对象未在网格缓存中：%s" % sorted(missing))
        self.active = grouped
        for part in scene.parts:
            if part.name not in grouped:
                continue
            actor = _make_actor(part)
            self.ren.AddActor(actor)
            self.actors[part.name] = actor

        self.camera = vtk.vtkCamera()
        self.camera.SetViewAngle(float(cfg["camera"].get("fov", 32)))
        self.camera.SetViewUp(0, 0, 1)
        self.ren.SetActiveCamera(self.camera)

        self.lights = []
        for _ in range(4):
            light = vtk.vtkLight()
            light.SetLightTypeToSceneLight()
            light.SetFocalPoint(0, 0, 0)
            self.ren.AddLight(light)
            self.lights.append(light)

        self.axis = assembly_axis(scene, cfg["front_objects"], cfg["back_objects"])
        self.front = front_direction(scene, cfg["front_objects"], cfg["back_objects"])
        self.offsets = self._group_offsets()
        self.center_asm, self.r_asm = self._bounds(None)
        self.center_exp, self.r_exp = self._bounds(self.offsets)
        self.center, self.radius = self.center_exp, self.r_exp
        self.current_offsets = {}
        self.bounds = self.scene.union_bounds(names=self.active)
        self.distance_asm = self._fit(
            cfg["camera"]["azimuth"][0], cfg["camera"]["elevation"][0]
        )[1]

        self.window.Render()  # 初始化 OpenGL 上下文

    # ------------------------------------------------------------ 布局

    def _vector_for(self, group):
        """爆炸方向：沿装配轴，按组的符号取正反。"""
        spec = self.cfg["groups"][group]
        direction = str(spec.get("direction", "axis"))
        if direction == "axis":
            unit = self.axis
        elif direction == "front":
            unit = -self.axis
        else:
            unit = np.array(spec["direction"], dtype=np.float64)
            unit = unit / np.linalg.norm(unit)
        return unit * float(spec["distance"])

    def _group_offsets(self):
        """每个零件在完全爆炸状态下的偏移。"""
        offsets = {}
        for group, spec in self.cfg["groups"].items():
            vector = self._vector_for(group)
            for name in spec["objects"]:
                offsets[name] = vector
        return offsets

    def _bounds(self, offsets):
        low, high = self.scene.union_bounds(offsets, names=self.active)
        center = (low + high) / 2.0
        radius = float(np.linalg.norm(high - low)) / 2.0
        return center, max(radius, 1.0)

    # ------------------------------------------------------------ 动画量化

    def progress(self, group, t):
        """某组在归一化时刻 t 的爆炸进度 0..1；配置里的窗口单位是秒。"""
        spec = self.cfg["groups"][group]
        seconds = t * float(self.cfg["video"]["seconds"])
        a, b = spec["expand"]
        c, d = spec["collapse"]
        value = _smooth((seconds - a) / max(b - a, 1e-6))
        if seconds > c:
            value = min(value, 1.0 - _smooth((seconds - c) / max(d - c, 1e-6)))
        return value

    def apply_pose(self, t):
        """应用 t 时刻的爆炸位姿，返回总体展开量 0..1。"""
        overall = 0.0
        lows, highs = [], []
        self.current_offsets = {}
        for group, spec in self.cfg["groups"].items():
            value = self.progress(group, t)
            overall = max(overall, value)
            vector = self._vector_for(group) * value
            for name in spec["objects"]:
                self.actors[name].SetPosition(*vector)
                self.current_offsets[name] = vector
                low, high = self.scene[name].offset_bounds(vector)
                lows.append(low)
                highs.append(high)
        self.bounds = (np.min(lows, axis=0), np.max(highs, axis=0))
        return overall

    # ------------------------------------------------------------ 相机与灯光

    def _fit(self, azimuth, elevation):
        """按当前位姿计算相机中心与刚好装下的距离。"""
        cam_cfg = self.cfg["camera"]
        fov = float(cam_cfg.get("fov", 32))
        low, high = self.bounds
        center = (low + high) / 2.0
        eye_dir = _eye_direction(azimuth, elevation, self.front)
        forward = -eye_dir
        right = np.cross(forward, np.array([0.0, 0.0, 1.0]))
        right /= np.linalg.norm(right)
        up = np.cross(right, forward)

        tan_v = np.tan(np.radians(fov) / 2.0)
        tan_h = tan_v * self.width / float(self.height)

        # 用真实顶点做透视精确取景（含每个零件的包围盒角点，避免抽样漏掉极值）
        points = []
        for name in self.actors:
            part = self.scene[name]
            offset = self.current_offsets.get(name, np.zeros(3))
            low_p, high_p = part.offset_bounds(offset)
            points.append(np.array([
                [x, y, z]
                for x in (low_p[0], high_p[0])
                for y in (low_p[1], high_p[1])
                for z in (low_p[2], high_p[2])
            ]))
            step = max(1, len(part.verts) // 20000)
            points.append(part.verts[::step] + offset)
        cloud = np.vstack(points)

        rel = cloud - center
        mid_x = (float((rel @ right).min()) + float((rel @ right).max())) / 2.0
        mid_y = (float((rel @ up).min()) + float((rel @ up).max())) / 2.0
        center = center + right * mid_x + up * mid_y

        rel = cloud - center
        x = rel @ right
        y = rel @ up
        z = rel @ forward
        distance = float(np.max(np.maximum(np.abs(x) / tan_h, np.abs(y) / tan_v) - z)) * 1.03
        return center, max(distance, 1.0), eye_dir, z

    def apply_camera(self, t, amount=1.0):
        cam_cfg = self.cfg["camera"]
        if cam_cfg.get("pingpong"):
            azimuth_lat = _smooth(1.0 - abs(2.0 * t - 1.0))
            elevation_lat = azimuth_lat
        else:
            azimuth_lat = _smooth(t)
            elevation_lat = _smooth(t)
        azimuth = cam_cfg["azimuth"][0] + (cam_cfg["azimuth"][1] - cam_cfg["azimuth"][0]) * azimuth_lat
        elevation = cam_cfg["elevation"][0] + (cam_cfg["elevation"][1] - cam_cfg["elevation"][0]) * elevation_lat

        center, distance, eye_dir, z = self._fit(azimuth, elevation)
        # 限制拉远幅度：爆炸时只轻微退后，避免零件出画过多或主体缩得太小
        limit = self.distance_asm * float(cam_cfg.get("max_zoom_out", 1.7))
        distance = min(distance, limit)

        eye = center + eye_dir * distance
        self.camera.SetFocalPoint(*center)
        self.camera.SetPosition(*eye)
        self.camera.SetClippingRange(max(distance - float(z.max()) - 5.0, 0.1),
                                     distance - float(z.min()) + 5.0)
        if os.environ.get("EXPLODE_DEBUG"):
            print("DEBUG center=%s dist=%.1f az=%.0f el=%.0f"
                  % (np.round(center, 1).tolist(), distance, azimuth, elevation), flush=True)

        # 主光、补光、轮廓光、顶光随相机旋转，保持稳定观感
        key_dir = _eye_direction(azimuth - 38, elevation + 32, self.front)
        fill_dir = _eye_direction(azimuth + 68, max(elevation - 8, 2), self.front)
        rim_dir = _eye_direction(azimuth + 178, elevation + 34, self.front)
        sky_dir = _eye_direction(azimuth + 110, 78, self.front)
        for light, direction, intensity, color in (
            (self.lights[0], key_dir, 1.22, (1.0, 0.985, 0.955)),
            (self.lights[1], fill_dir, 0.75, (0.86, 0.90, 0.99)),
            (self.lights[2], rim_dir, 0.70, (1.0, 0.99, 0.97)),
            (self.lights[3], sky_dir, 0.60, (0.95, 0.97, 1.0)),
        ):
            light.SetPosition(*(center + direction * distance * 1.6))
            light.SetFocalPoint(*center)
            light.SetIntensity(intensity)
            light.SetDiffuseColor(*color)
            light.SetSpecularColor(*color)

    # ------------------------------------------------------------ 出图

    def capture(self):
        """渲染一帧并返回 RGBA 的 PIL 图像（已降采样到成品尺寸）。"""
        self.window.Render()
        grab = vtk.vtkWindowToImageFilter()
        grab.SetInput(self.window)
        grab.SetInputBufferTypeToRGBA()
        grab.ReadFrontBufferOff()
        grab.Update()
        image = grab.GetOutput()
        width, height, _ = image.GetDimensions()
        buffer = vtk_to_numpy(image.GetPointData().GetScalars())
        buffer = buffer.reshape(height, width, -1)[::-1]
        rgba = Image.fromarray(buffer.astype(np.uint8), "RGBA")
        if self.ssaa > 1:
            rgba = rgba.resize((self.width, self.height), Image.LANCZOS)
        return rgba


# ---------------------------------------------------------------- 背景与合成

def _smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3.0 - 2.0 * x)


def _eye_direction(azimuth_deg, elevation_deg, front):
    """方位角以“正面朝向”为 0°，返回从目标指向相机的单位向量。"""
    base = np.arctan2(front[1], front[0])
    angle = base + np.radians(azimuth_deg)
    elevation = np.radians(elevation_deg)
    return np.array([
        np.cos(elevation) * np.cos(angle),
        np.cos(elevation) * np.sin(angle),
        np.sin(elevation),
    ])


def _fit_distance(low, high, center, eye_dir, fov_deg, aspect, margin):
    """按当前包围盒在相机平面上的投影计算刚好装下的距离。"""
    forward = -np.asarray(eye_dir, dtype=np.float64)
    right = np.cross(forward, np.array([0.0, 0.0, 1.0]))
    if np.linalg.norm(right) < 1e-6:
        right = np.array([1.0, 0.0, 0.0])
    right /= np.linalg.norm(right)
    up = np.cross(right, forward)

    corners = np.array([
        [x, y, z]
        for x in (low[0], high[0])
        for y in (low[1], high[1])
        for z in (low[2], high[2])
    ]) - center
    x = np.abs(corners @ right).max()
    y = np.abs(corners @ up).max()
    z = np.abs(corners @ forward).max()

    tan_v = np.tan(np.radians(fov_deg) / 2.0)
    tan_h = tan_v * aspect
    distance = max(y / tan_v, x / tan_h) * margin + z
    return float(distance)


def _background(width, height):
    """垂直渐变 + 暖色柔光 + 轻微暗角。"""
    top = np.array([250, 249, 246], dtype=np.float32)
    bottom = np.array([228, 224, 216], dtype=np.float32)
    ramp = np.linspace(0.0, 1.0, height, dtype=np.float32)[:, None, None]
    canvas = top[None, None, :] * (1 - ramp) + bottom[None, None, :] * ramp
    canvas = np.repeat(canvas, width, axis=1)

    yy, xx = np.mgrid[0:height, 0:width].astype(np.float32)
    cx, cy = width * 0.5, height * 0.46
    dist = np.sqrt(((xx - cx) / (width * 0.62)) ** 2 + ((yy - cy) / (height * 0.62)) ** 2)
    glow = np.clip(1.0 - dist, 0.0, 1.0) ** 2
    canvas += glow[:, :, None] * 10.0

    vignette = np.clip(1.10 - 0.22 * dist ** 2, 0.86, 1.0)
    canvas *= vignette[:, :, None]
    return Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8), "RGB")


def composite(rgba, background):
    """模型 RGBA 合成到背景，附一层柔和接触阴影。"""
    alpha = rgba.getchannel("A")
    rgb = rgba.convert("RGB")

    shadow_alpha = alpha.filter(ImageFilter.GaussianBlur(radius=max(6, rgba.width // 90)))
    shadow_alpha = shadow_alpha.point(lambda v: int(v * 0.42))
    offset = (0, max(4, rgba.height // 70))
    shifted = Image.new("L", alpha.size, 0)
    shifted.paste(shadow_alpha, offset)
    shadow_rgb = Image.new("RGB", alpha.size, (96, 92, 84))
    background = Image.composite(shadow_rgb, background, shifted)

    return Image.composite(rgb, background, alpha)


# ---------------------------------------------------------------- 编码

def encode(frames_dir, cfg, project_root):
    video = cfg["video"]
    outputs = cfg["output"]
    ffmpeg = find_ffmpeg()
    mp4 = os.path.join(project_root, outputs["mp4"])
    gif = os.path.join(project_root, outputs["gif"])
    poster = os.path.join(project_root, outputs["poster"])
    os.makedirs(os.path.dirname(mp4), exist_ok=True)

    pattern = os.path.join(frames_dir, "%04d.png")
    _run([
        ffmpeg, "-y", "-loglevel", "error", "-framerate", str(video["fps"]),
        "-i", pattern, "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", mp4,
    ])
    _run([
        ffmpeg, "-y", "-loglevel", "error", "-framerate", str(video["fps"]),
        "-i", pattern, "-vf",
        "fps=15,scale=960:-1:flags=lanczos,split[a][b];"
        "[a]palettegen=max_colors=192:stats_mode=diff[p];"
        "[b][p]paletteuse=dither=sierra2_4a:diff_mode=rectangle",
        gif,
    ])
    poster_source = os.path.join(frames_dir, "%04d.png" % cfg.get("poster_frame", 150))
    if os.path.exists(poster_source):
        Image.open(poster_source).save(poster)
    return {"mp4": mp4, "gif": gif, "poster": poster}


def _run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError("命令失败：%s\n%s" % (" ".join(cmd), result.stderr[-2000:]))
    return result


# ---------------------------------------------------------------- 主流程

def render_project(cfg, project_root, mode="video", still_t=0.45, still_path=None,
                   frame_limit=None, start_frame=0):
    """渲染项目：mode = export / all / video / still / keyframes。"""
    scene_path = os.path.join(project_root, cfg["scene"]["manifest"])
    npz_path = os.path.join(project_root, cfg["scene"]["npz"])
    if mode in ("export", "all") or not os.path.isfile(npz_path):
        export_scene(cfg, project_root)
    if mode == "export":
        return [npz_path]

    scene = load_scene(npz_path, scene_path)
    renderer = Renderer(scene, cfg)

    frames_dir = os.path.join(project_root, cfg["frames_dir"])
    os.makedirs(frames_dir, exist_ok=True)

    video = cfg["video"]
    total = int(round(video["seconds"] * video["fps"]))
    start = time.time()

    if mode == "still":
        amount = renderer.apply_pose(still_t)
        renderer.apply_camera(still_t, amount)
        rgba = renderer.capture()
        image = composite(rgba, _background(renderer.width, renderer.height))
        target = still_path or os.path.join(frames_dir, "still_%03d.png" % int(still_t * 100))
        image.save(target)
        return [target]

    if mode == "keyframes":
        picks = [0.0, 0.18, 0.34, 0.5, 0.66, 0.82, 1.0]
        paths = []
        for index, fraction in enumerate(picks):
            amount = renderer.apply_pose(fraction)
            renderer.apply_camera(fraction, amount)
            rgba = renderer.capture()
            image = composite(rgba, _background(renderer.width, renderer.height))
            path = os.path.join(frames_dir, "key_%02d.png" % index)
            image.save(path)
            paths.append(path)
        return paths

    background = _background(renderer.width, renderer.height)
    for index in range(start_frame, total):
        path = os.path.join(frames_dir, "%04d.png" % index)
        if os.path.exists(path) and os.path.getsize(path) > 0:
            continue
        t = index / max(total - 1, 1)
        amount = renderer.apply_pose(t)
        renderer.apply_camera(t, amount)
        rgba = renderer.capture()
        composite(rgba, background).save(path)
        if index % 30 == 0:
            elapsed = time.time() - start
            print("帧 %4d/%d  %.1fs" % (index, total, elapsed), flush=True)
        if frame_limit is not None and index - start_frame + 1 >= frame_limit:
            break

    elapsed = time.time() - start
    print("出帧完成：%d 帧，%.1f s" % (total, elapsed), flush=True)
    return encode(frames_dir, cfg, project_root)
