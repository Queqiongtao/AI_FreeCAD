# AI FreeCAD

个人 FreeCAD 设计项目集合。一个仓库，一个项目一个文件夹；每个项目自带源文件、输出、参考和旧版本归档。

## 项目

| 项目 | 说明 | 状态 |
| --- | --- | --- |
| [ESP32-S3-Touch-AMOLED-1.75-B 鹅卵石底座](projects/esp32-pebble-stand/) | 40° 屏幕，整面平底，上侧双刚性旋扣＋下侧两螺丝，30×20×7 mm 扬声器四角胶粘、侧向定位及下侧弧面内交错双排 13 个 Ø2 出音孔 | 待实物试印、孔内支撑清理、贴胶和整机装配 |
| [微雪 ESP32-P4-WIFI6-Touch-LCD-3.4C 桌面外壳](projects/waveshare-esp32-p4-wifi6-touch-lcd-3.4c-enclosure/) | 两件式：原板 M2.5 固定承托架，后盖上侧双刚性钩＋下侧两螺丝（M3×3×4 热熔螺母、Ø3.8 底孔）；喇叭边框泡棉胶固定、18 个斜出音孔、左右各六孔拾音、20×14 mm Type-C直插口；40°、正面隐藏 | 待实物试印与声音测试 |

![ESP32 鹅卵石底座](projects/esp32-pebble-stand/output/preview_iso.png)

## 文档

- [AGENT.md](AGENT.md) — AI/协作者工作约定
- [LOG.md](LOG.md) — 工作日志
- [shared/explode_render/README.md](shared/explode_render/README.md) — 爆炸图渲染器与重放方法

## 目录约定

```text
.
├─ README.md                     # 本文件：项目索引 + 通用约定
├─ AGENT.md                      # AI/协作者工作约定
├─ LOG.md                        # 工作日志
├─ .gitignore
├─ .gitattributes
├─ shared/                       # 两个项目共用的代码
│  └─ explode_render/            # 爆炸图渲染器（含 README）
└─ projects/
   └─ <project-slug>/
      ├─ README.md               # 项目自己的说明
      ├─ <name>.py               # 唯一参数化源文件
      ├─ explode.py              # 爆炸图配置（可选）
      ├─ output/                 # STL / STEP / FCStd / 预览
      ├─ reference/              # 项目相关板子图、PDF、DWG
      └─ archive/                # 旧版本，本地保留，Git 忽略
```

- 爆炸视频/动图可重放，不入库；`exploded_view.mp4`、`exploded_view.gif` 已在 `.gitignore` 里按路径排除。

- 项目文件夹用小写短横线：`esp32-pebble-stand`、`desk-organizer`。
- 文件名不带版本号；版本差异用 Git commit / tag。
- `output/` 固定文件名，重跑覆盖，不建版本文件夹。
- 每个项目的参考文件放在自己的 `reference/`，不要放根目录。
- `archive/` 只在本地；`.gitignore` 已忽略所有 `archive/`。
- 两个项目真正共用的代码/资料再放根目录 `shared/`，目前不需要。

## 新增项目

1. 新建 `projects/<project-slug>/`。
2. 放一个 `<name>.py`（或 `design.py`）。
3. 建 `output/`、`reference/`、`archive/`。
4. 写项目 `README.md`。
5. 在上面的项目表里加一行。
6. 跑脚本、展示改动；经用户同意后提交、打 tag。

## Git

提交前需用户明确同意，详见 [AGENT.md](AGENT.md)。

远程：

```text
https://github.com/Queqiongtao/AI_FreeCAD.git
```

沿用普通 Git 存储模型和图纸，不启用 Git LFS。
