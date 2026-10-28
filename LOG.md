# 工作日志

最新记录在最上面。

## 2026-10-28（第一天）

### 仓库与结构

- 确定单仓库、多项目结构：`projects/<project-slug>/`。
- 当前项目迁移到 `projects/esp32-pebble-stand/`。
- 根目录保留 `README.md`、`AGENT.md`、`LOG.md`、`.gitignore`、`.gitattributes`。
- 旧版本移入项目的 `archive/`，Git 忽略。

### ESP32 鹅卵石底座

- 屏幕 50°（离垂直 40°）。
- 卡口整体转 -10°：320/80/200 → 345/105/225。
- 删除电池托边；前壳三个螺丝座独立。
- 三处前壁通孔（顶部两个 MX1.25、底部 10-pin）贯通电池仓。
- 单文件 `stand.py`，输出固定到 `output/`。
- 验证：前壳 6505.3 mm³、后盖 15443.9 mm³、前/后 common 0.2361 mm³、STEP 有效。
- 输出：`front_shell.stl`、`rear_cover.stl`、`stand.step`、`stand.FCStd`、`preview_*.png`。

### Git

- 初始化 `main`，提交 `c990ed9`，推送 `origin/main`。
- 作者：`queqt <467500670@qq.com>`。
- 未启用 Git LFS。

### 待办

- 打印 50° 前壳，确认屏幕角度。
- 关闭 PDF 阅读器后删除旧参考文件夹。
- 增加 `AGENT.md` / `LOG.md` 并提交（待用户同意）。
