# AI FreeCAD

个人 FreeCAD 设计项目集合。一个仓库，一个项目一个文件夹；每个项目自带源文件、输出、参考和旧版本归档。

## 项目

| 项目 | 说明 | 状态 |
| --- | --- | --- |
| [ESP32 鹅卵石底座](projects/esp32-pebble-stand/) | ESP32-S3-Touch-AMOLED-1.75-B 桌面底座，50° 屏幕，前薄盖 + 后整机身螺纹 | active |

![ESP32 鹅卵石底座](projects/esp32-pebble-stand/output/preview_front.png)

## 文档

- [AGENT.md](AGENT.md) — AI/协作者工作约定
- [LOG.md](LOG.md) — 工作日志

## 目录约定

```text
.
├─ README.md                     # 本文件：项目索引 + 通用约定
├─ AGENT.md                      # AI/协作者工作约定
├─ LOG.md                        # 工作日志
├─ .gitignore
├─ .gitattributes
└─ projects/
   └─ <project-slug>/
      ├─ README.md               # 项目自己的说明
      ├─ <name>.py               # 唯一参数化源文件
      ├─ output/                 # STL / STEP / FCStd / 预览
      ├─ reference/              # 项目相关板子图、PDF、DWG
      └─ archive/                # 旧版本，本地保留，Git 忽略
```

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

当前输出约 4–5 MB，未启用 LFS。以后二进制文件多了再加：

```powershell
git lfs install
git lfs track "*.FCStd" "*.step" "*.stl"
```
