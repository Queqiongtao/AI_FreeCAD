# 爆炸图离线渲染器

把项目 `output/*.FCStd` 里的装配体渲染成爆炸演示：一张静帧、一条 MP4、一条循环 GIF。
两个项目（S3 鹅卵石底座、P4 两件式外壳）共用本目录的代码，项目侧只放配置。

- 不启动 FreeCAD 窗口，不需要点任何按钮；全部离屏渲染。
- 不修改 FCStd：材质只在渲染时套用。
- 视频/动图属于可重放产物，**不提交**（见 `.gitignore`），本地保留即可。

## 1. 产物

以 P4 为例（S3 相同，换项目目录）：

| 文件 | 内容 | 是否入库 |
| --- | --- | --- |
| `projects/<slug>/output/preview_exploded.png` | 1920×1080 静帧，README 插图 | 是 |
| `projects/<slug>/output/exploded_view.mp4` | 1920×1080、30 fps、300 帧、10.0 s、H.264 yuv420p | 否 |
| `projects/<slug>/output/exploded_view.gif` | 960×540、15 fps、10 s 循环 | 否 |
| `projects/<slug>/archive/explode_render/scene.npz` | 装配位姿网格缓存 | 否（`archive/` 整体忽略） |
| `projects/<slug>/archive/explode_frames/*.png` | 逐帧图片，可断点续渲 | 否 |

## 2. 依赖

| 组件 | 要求 | 说明 |
| --- | --- | --- |
| FreeCAD | 1.1.x | 提供 `freecadcmd.exe` 和带 `vtk` 的 `python.exe` |
| FreeCAD 自带 Python | 含 `vtk` 9.3、`numpy`、`Pillow` | **不能用系统 Python**，否则 `import vtk` 失败 |
| ffmpeg | 任意近期版本 | 编码 MP4 / GIF |
| Pillow | 随 FreeCAD Python 提供 | 背景合成与降采样 |

查找顺序：

- `ffmpeg`：环境变量 `EXPLODE_FFMPEG` → `PATH` → `D:\Program\ffmpeg\bin\ffmpeg.exe` → `C:\Program Files\ffmpeg\bin\ffmpeg.exe` → `C:\ffmpeg\bin\ffmpeg.exe`
- `freecadcmd`：当前 `python.exe` 同目录 → `PATH`

## 3. 数据流

```text
output/<name>.FCStd
        │  freecadcmd + export_meshes.py（装配位姿、按对象三角化）
        ▼
archive/explode_render/scene.npz + scene.json
        │  VTK 离屏渲染（每个零件一个 Actor，按组平移）
        ▼
archive/explode_frames/0000.png … 0299.png
        │  Pillow 合成渐变背景与接触阴影，2× 超采样后缩放
        ▼
output/exploded_view.mp4 / .gif / preview_exploded.png
```

## 4. 快速开始

在仓库根目录执行（解释器换成自己机器上 FreeCAD 的 `python.exe`）：

```powershell
# 导出网格 + 渲染视频（首次或改了 FCStd 后用 all）
& "D:\Program\FreeCAD 1.1\bin\python.exe" projects\esp32-pebble-stand\explode.py --mode all
& "D:\Program\FreeCAD 1.1\bin\python.exe" projects\waveshare-esp32-p4-wifi6-touch-lcd-3.4c-enclosure\explode.py --mode all
```

单条耗时：S3 约 2 分钟（导出 2 s + 渲染 100 s），P4 约 2.5 分钟（导出 28 s + 渲染 110 s）。

## 5. 分步执行

| 命令 | 作用 |
| --- | --- |
| `--mode all` | 导出网格后渲染完整视频、GIF、静帧 |
| `--mode export` | 只导出 `scene.npz/scene.json` |
| `--mode video` | 只用已有缓存渲染视频（缓存缺失时自动先导出） |
| `--mode still --t 0.5` | 渲染单帧，`--out xxx.png` 可指定路径 |
| `--mode keyframes` | 输出 7 张关键帧到 `archive/explode_frames/key_XX.png` |
| `--mode video --start 120 --limit 10` | 从第 120 帧渲 10 帧，用于调试 |

断点续渲：已存在的 `NNNN.png` 会跳过；改配置后重渲需先清空该目录的 4 位数字帧文件。

## 6. 配置说明

每个项目一个 `explode.py`，核心是 `CONFIG` 字典。

### `scene`

| 键 | 含义 |
| --- | --- |
| `doc` | 源工程，相对项目目录，如 `output\enclosure.FCStd` |
| `npz` / `manifest` | 网格缓存输出路径，默认放 `archive/explode_render/` |
| `deflection` | 默认三角化偏差（mm），越小越精细、越慢 |
| `angular` | 保留字段，当前未使用（`Shape.tessellate` 只接收偏差） |
| `only` | 只导出这些对象；空列表表示全部 |
| `overrides` | 按对象覆写偏差，如 `{"Module_Reference": 0.45}` |

### `groups`

每个组是一个或几个零件，沿同一方向、同一时间窗移动：

```python
"cover": {
    "objects": ["rear_cover"],
    "direction": "axis",      # axis=向后 | front=向前 | [x,y,z]=自定义单位向量
    "distance": 96.0,         # 爆炸距离，mm
    "expand":   [1.0, 3.4],   # 展开起止时间，秒
    "collapse": [7.4, 9.2],   # 回装起止时间，秒
}
```

- 时间轴固定 10 秒，`_smooth`（3t²−2t³）缓动。
- 组之间错峰：外壳先退、胶层与喇叭次之、紧固件最后；回装顺序相反。
- 装配轴由 `front_objects` 与 `back_objects` 的质心连线自动求出，`axis`/`front` 均为该轴的正负方向。

### `camera`

| 键 | 含义 |
| --- | --- |
| `azimuth` | 方位角起止（度），0° = 正对屏幕 |
| `elevation` | 仰角起止（度） |
| `fov` | 垂直视场角 |
| `pingpong` | `true` 时方位角走“去程→回程”，首尾同机位，可无缝循环 |
| `max_zoom_out` | 相对组装态最多拉远倍数，防止爆炸时主体缩太小 |

相机每帧按当前几何自动取景：把真实顶点投影到屏幕，算出刚好装下的距离，再按 `max_zoom_out` 截断。

### `video` / `output`

`width`、`height`、`fps`、`seconds`、`ssaa`（超采样倍数，2 表示 3840×2160 渲染后缩到 1080p）；
`output.mp4/gif/poster` 为相对项目目录的产物路径，`poster_frame` 指定用第几帧做静帧。

## 7. 材质配色

`palette.py` 是唯一的调色入口，`role_of()` 按对象名匹配材质。当前为“风格 A · 工业极简”：

| 角色 | 色值 | 用于 |
| --- | --- | --- |
| `shell_light` | `#DAD7D2` 暖白 | 后盖 / 后壳 |
| `shell_dark` | `#474C52` 石墨 | 承托架 |
| `metal` | `#B9BDC3` 拉丝钢 | M2.5、M3、热熔螺母 |
| `speaker` | `#1F2124` | 喇叭本体与振膜 |
| `pcb` | `#1C2025` | 屏幕/开发板 |
| `battery` | `#2E3238` | 电池参考体 |
| `tape` | `#D19333` 泡棉橙 | 双面胶层 |
| `plug` / `cable` | `#2A2D31` / `#33363A` | USB 插头、线束 |

每个材质还有 `ambient`、`diffuse`、`specular`、`specular_power`、`opacity`。改完直接重跑 `--mode video` 即可，**不会写回 FCStd**。

新增对象若没匹配到规则，会落到 `FALLBACK`（石墨）；在 `_RULES` 里加一行关键字即可。

## 8. 换电脑 / 换安装路径

1. 装 **FreeCAD 1.1** 与 **ffmpeg**；确认 `FreeCAD\bin\python.exe` 能 `import vtk`。
2. 克隆仓库。`archive/` 不在仓库里，所以第一次必须用 `--mode all`（或 `--mode export`）重新导出网格；源 FCStd 已随仓库提交。
3. 用 FreeCAD 的 `python.exe` 运行项目 `explode.py`。
4. ffmpeg 不在 `PATH` 时：

```powershell
$env:EXPLODE_FFMPEG = "C:\tools\ffmpeg\bin\ffmpeg.exe"
```

5. FreeCAD 装在非默认位置时，直接用它的 `python.exe` 运行即可：`freecadcmd` 会在同一 `bin` 目录里自动找到。

## 9. 常见问题

| 现象 | 原因与处理 |
| --- | --- |
| `ModuleNotFoundError: No module named 'vtk'` | 用成了系统 Python；改用 FreeCAD 的 `python.exe` |
| `找不到 ffmpeg` | 未安装或不在 `PATH`；设 `EXPLODE_FFMPEG` |
| `找不到 freecadcmd` | 解释器不是 FreeCAD 的，或 `bin` 不在 `PATH` |
| `配置里的对象未在网格缓存中：['xxx']` | FCStd 里对象被改名/删除；更新 `groups` 或重跑 `--mode export` |
| 渲染很慢 | 降低 `deflection` 精度（增大数值）、把 `ssaa` 改 1、或先用 `--limit` 试跑 |
| 视频没更新 | 旧帧被复用；清空 `archive/explode_frames` 里的 `NNNN.png` |
| 爆炸时零件飞出画面 | 调小 `distance`，或调大 `max_zoom_out` |

## 10. 验证

```powershell
& "D:\Program\ffmpeg\bin\ffprobe.exe" -v error -select_streams v:0 `
  -show_entries stream=width,height,r_frame_rate,nb_frames `
  -show_entries format=duration -of default=noprint_wrappers=1 `
  projects\esp32-pebble-stand\output\exploded_view.mp4
```

期望：`1920×1080`、`30/1`、`300` 帧、`10.0` 秒。

循环检查（首尾帧应完全一致）：

```powershell
& "D:\Program\FreeCAD 1.1\bin\python.exe" -c `
  "from PIL import Image, ImageChops; import numpy as np; a=Image.open(r'...\0000.png').convert('RGB'); b=Image.open(r'...\0299.png').convert('RGB'); print(np.asarray(ImageChops.difference(a,b)).max())"
```

输出 `0` 表示可无缝循环。

## 11. 已知限制

- 材质只用于渲染，交付的 FCStd 仍是 FreeCAD 默认配色。
- 参考体（开发板、电池、螺丝等）只用于说明装配关系，不计入打印件数量。
- 相机自动取景会随爆炸程度轻微推拉；`max_zoom_out` 是硬限制，极端配置下可能贴边。
- GIF 用 192 色调色板，渐变背景会有轻微色带；MP4 无此问题。
- 视频编码依赖 ffmpeg 的 `libx264`，极简版 ffmpeg 可能没有该编码器。
