# AGENT.md

本文件是 AI 协作者在本仓库工作的统一约定。所有对话、说明、日志、提交信息、文档一律使用中文。

## 1. 语言

- 与用户对话：中文。
- README、AGENT.md、LOG.md、项目说明、代码注释：中文。
- 提交信息：中文描述；类型前缀用英文（feat / fix / docs / refactor / chore）。
- 文件名、变量名、函数名、分支/tag：英文或简短拼音；不加版本号。

## 2. 仓库结构

- 单仓库、多项目：`projects/<project-slug>/`。
- 每个项目自包含：
  - `README.md`：项目说明
  - `<name>.py`：唯一参数化源文件
  - `output/`：STL / STEP / FCStd / 预览
  - `reference/`：项目相关板子图、PDF、DWG
  - `archive/`：旧版本，本地保留，Git 忽略
- 根目录只放 `README.md`、`AGENT.md`、`LOG.md`、`.gitignore`、`.gitattributes`、`projects/`。
- 每个项目的参考文件放在自己的 `reference/`，不要放根目录。
- 不建版本文件夹；`output/` 固定文件名，重跑覆盖。
- `archive/` 不要删除，除非用户明确要求。
- 两个项目真正共用的代码/资料才放根目录 `shared/`；目前不需要。

## 3. 工作流程

1. 先读根 `README.md`、`AGENT.md`、目标项目 `README.md`。
2. 确认项目目录、当前参数、输出路径。
3. 只改参数化源文件；不要手改 STL / STEP / FCStd。
4. 重跑脚本；验证 solid/1、z=0、common、孔、电池、STEP。
5. 更新项目 `README.md` 和根 `LOG.md`。
6. 展示改动摘要；经用户同意后再提交。
7. 推送 `origin/main`；重要节点打 tag。

### FreeCAD 文档刷新与覆盖

- 默认复用当前工程的同一个 FreeCAD 文档，不得因反复修改、生成或验证而不断新增模型文档或标签。
- 只有用户明确需要对比时，才另开审阅模型；不得通过另开窗口绕过覆盖或未保存状态的确认。
- 每次重新生成模型后，必须同步刷新用户已打开的对应 FreeCAD 文档，核对完整文件路径，并确认窗口显示最新模型。仅更新磁盘文件不算完成。
- 刷新前必须检查未保存修改；发现异常、文档状态不明确，或需要覆盖文件、替换或丢弃未保存内容时，必须先说明问题、影响及处理方案，取得用户明确同意后再操作，不得擅自覆盖、关闭或丢弃文档及未保存内容。
- 更新后必须核对活动文档的完整文件路径，并明确告知用户当前显示的是哪个模型。
- 无法连接或刷新 GUI 时，应明确告知用户，并提供最新文件路径及重新打开方法，不得声称窗口已更新。

## 4. Git 提交

- **不要直接 commit / push。**
- 每次提交前先展示 `git status`、`git diff --stat`，必要时展示关键 diff。
- 必须等用户明确回复“提交 / 可以提交 / 推送”后，才能执行 `git commit` / `git push`。
- 用户说“执行”只代表可以改文件，不代表同意提交。
- 提交前确认当前分支、待提交文件；不要把 `archive/`、临时文件、密钥提交进去。
- 推送前确认远程为 `origin`，分支为 `main`。
- 提交格式：`类型(项目): 中文说明`
  - `feat(esp32-pebble-stand): 屏幕角度改为50°`
  - `fix(esp32-pebble-stand): 删除电池托边`
  - `docs: 增加 AGENT.md 和第一天日志`
  - `refactor(esp32-pebble-stand): 拆分参数`
  - `chore: 更新忽略规则`
- 重要版本打 tag：`<project>-v1`、`<project>-v2`。

## 5. 日志

- 根目录 `LOG.md`，最新记录在最上面。
- 每条记录包含：日期、项目、改动、验证、提交哈希（未提交则写“待提交”）、待办。
- 第一天从 **2026-10-28** 开始记录。
- 每次实质性改动后更新日志；纯问答可不记。

## 6. 文档

- 根 `README.md`：项目索引、目录约定、Git 说明。
- 项目 `README.md`：尺寸、装配、打印、验证、已知取舍。
- 图片用相对路径：`output/preview_*.png`。
- 文档用中文；STL、STEP、FCStd、FreeCAD、Git LFS 等术语可保留英文。
- 不在项目 README 里写 `git init`；Git 由仓库根目录统一管理。

## 7. 安全与边界

- 不删除用户文件或 `archive/`，除非用户明确要求。
- 不提交 token、密钥、密码。
- 二进制文件明显增多时，先问用户是否启用 Git LFS。
- 改模型前确认目标项目和参数；不确定先问。
- 发现文件被占用、删除失败等情况，如实说明，不要强行结束用户进程。

## 8. 当前仓库

- 远程：`https://github.com/Queqiongtao/AI_FreeCAD.git`
- 分支：`main`
- 当前项目：`projects/esp32-pebble-stand/`
- 当前源文件：`projects/esp32-pebble-stand/stand.py`
- 当前输出：`projects/esp32-pebble-stand/output/`
- Git 作者：`queqt <467500670@qq.com>`
- LFS：暂未启用
