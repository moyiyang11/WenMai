# AI 小说风格蒸馏与 Skill 导出系统

> 从优秀小说中提取稳定的创作规律，将"看不见的风格"转换成结构化、可比较、可验证、可导出的 AI **Style Skill**。
> 本系统**不生成小说正文**，只负责：收集 → 分析 → 蒸馏 → 风格提取 → 稳定性分析 → Skill 导出。

本目录以《AI小说风格蒸馏与Skill导出系统_产品说明书.md》第 27 章 **MVP 第一阶段** 为基线实现可运行代码骨架，并已按说明书 **§6–§13 深化单本小说蒸馏**（多维度 + 情绪/节奏/冲突曲线）。

## 已实现的 MVP 闭环（说明书 §27）

```
小说导入 → 分类/标签 → 单本 AI 蒸馏 → 蒸馏结果保存
  → 多小说聚类 → 共同特征提取 → 风格稳定性分析
  → Style Profile → Style Skill 导出（zip 包）
```

对应界面：**工作台** / **小说库·蒸馏** / **风格中心（含风格组合）** / **Skill 导出**。

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | React 18 + TypeScript + Tailwind CSS + Vite |
| 后端 | Python + FastAPI + SQLAlchemy |
| 数据库 | SQLite（MVP） |
| AI | DeepSeek（OpenAI 兼容接口），未配置 key 时自动回退本地 mock |

## 目录结构

```
app/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── models.py            # ORM 模型（Novel/Tag/Distillation/StyleProfile/StyleFeature/Skill）
│   ├── schemas.py           # Pydantic 请求/响应
│   ├── core/                # config + database
│   ├── services/            # llm(DeepSeek) / style(聚类稳定性) / skill(导出) / tags
│   ├── routers/             # dashboard / novels / styles / skills
│   └── .env.example
└── frontend/
    └── src/
        ├── api.ts, types.ts
        ├── App.tsx
        └── pages/           # Dashboard / Novels / Styles / Skills
```

## 快速开始

### 方式 A：一键启动（推荐）

首次运行会自动创建 venv、安装前后端依赖，并分别拉起后端(8000)与前端(5173)。

- **Windows**：双击 `app/start.bat`
- **Git Bash / macOS / Linux**：`cd app && ./start.sh`

启动后打开 http://127.0.0.1:5173 。

### 方式 B：手动启动

#### 1. 后端

```bash
cd app/backend
python -m venv .venv
# Windows(Git Bash):
.venv/Scripts/python.exe -m pip install -r requirements.txt
cp .env.example .env          # 可选：填入 DEEPSEEK_API_KEY

.venv/Scripts/python.exe -m uvicorn main:app --reload --port 8000
```

- 打开 http://127.0.0.1:8000/docs 查看 API。
- 健康检查 `GET /api/health` 会显示当前用真实模型还是 mock。

> **DeepSeek 接入**：见下方「AI 接入」一节，推荐用网页配置。
> 留空则蒸馏走本地启发式 mock，可离线跑通整条闭环。

### 2. 前端

```bash
cd app/frontend
npm install
npm run dev      # http://127.0.0.1:5173 （已配置 /api 代理到 8000）
```

## AI 接入（DeepSeek）与防泄露

有两种方式配置 DeepSeek API Key，**都不会把 Key 写入会被提交到 GitHub 的文件**：

1. **网页配置（推荐）**：启动后进入 **系统设置 · AI** 页面，填入 API Key → 保存 → 可点「测试连接」。
   - Key 存储在后端本地数据库 `app/backend/data/app.db`，`data/` 已在 `.gitignore` 中排除。
   - 接口回显一律脱敏（如 `sk-1***abcd`），前端不保存明文；可随时「清除 Key」回退 mock。
2. **`.env` 文件**：在 `app/backend/.env` 设 `DEEPSEEK_API_KEY=sk-xxx`。该文件同样已 gitignore。

优先级：**网页配置 > .env**。两者都为空时，蒸馏走本地启发式 mock，可离线跑通整条闭环。

> 申请 Key：https://platform.deepseek.com ；`GET /api/health` 会显示当前用真实模型还是 mock。

## 使用流程

1. **小说库·蒸馏**：上传 txt 小说（`素材库/` 下有两本样例），填市场/题材/标签 → 点「蒸馏」。
2. **风格中心**：勾选 ≥2 本已蒸馏小说 → 填风格名 → 「生成 Style Profile」，查看每个特征的稳定度与分级（核心/重要/辅助/偶然，阈值见 §16）。
   - **风格组合（§20）**：勾选 ≥2 个已有风格 → 填组合名 → 「生成组合风格」。系统重新计算**共同规则 / 冲突规则 / 优先级**：同维取值一致→共同；取值冲突→按加权稳定度取舍（采纳/弃用带标记），生成新的可再导出 Skill 的组合 Profile。
3. **Skill 导出**：选择风格 → 「导出为 Skill」→ 预览各文件 → 下载 zip。

导出的 Skill 包结构（说明书 §17）：
```
style-skill/
├── SKILL.md  ├── style.yaml ├── rules.md   ├── plot.md
├── character.md ├── rhythm.md ├── dialogue.md ├── language.md └── examples.md
```

## 与说明书的对应 & 边界

- 已实现（MVP §27）：§5 小说档案、§14 聚类、§15 Style Profile、§16 稳定性分级、§17–19 Skill 导出、**§20 风格组合**、§24 首页概览、§26 核心数据模型（MVP 子集）。
- **已深化的单本蒸馏（§6–§13）**：单本蒸馏结果现覆盖全维度，在「小说库·蒸馏 → 查看」中分页展示：
  - §6.1 基础信息、§6.2 故事结构、§6.3 人物系统（主角/配角/反派）
  - §7 人物关系（含关系变化追踪）、§8 剧情时间线
  - §9 冲突系统（含**冲突曲线**）、§10 悬念伏笔档案
  - §11 情绪曲线（过程 + 爽点分布）、§12 节奏曲线（对话/信息/爽点/反转四条曲线）
  - §13 文风系统（语言/描写/叙事/情绪基调）
  - 曲线以内置轻量 SVG 折线图渲染，无第三方图表库依赖。
- 仍留待后续（§21/§23/§28/§29）：Skill 版本迭代、分析中心（小说vs小说 / 风格vs风格）、章节自动解析、知识库/素材库等。数据模型与蒸馏 JSON 已为其预留扩展点。

## 说明

- 数据库与导出文件在 `app/backend/data/`（首次启动自动建表）。
- mock 蒸馏是确定性启发式（按标题作种子生成稳定的多维度数据与曲线），仅用于跑通流程与演示；接入 DeepSeek 后由模型按同一 JSON schema 输出真实的结构化蒸馏。

## 更新记录

### 2026-08-14 · AI 导入预检测 + 多段采样

**AI 自动识别男/女频**

- 导入小说时增加「AI 自动识别」按钮：选择 txt 文件后点击，系统用小说前 6000 字调用 AI（或 mock），自动识别**市场（男频/女频）、题材、风格标签、核心主题**，结果直接预填到表单；可在提交前手动调整。
- 未配置 API Key 时走本地 mock（关键词匹配启发式），离线可用。

**多段采样覆盖完整故事弧**

- 以前蒸馏只截取文件前 24 000 字，仅分析开头部分。现在改为**头/中/尾三段均等采样**（默认每段 8 000 字），确保开头、中段、结局都被 AI 看到。
- 采样描述随蒸馏结果一起返回，「查看蒸馏结果」面板标题会显示采样范围（如"多段采样：前9.1%(8000字) + 中46.4%(8000字) + 末91.4%(8000字)起，全文共 88 000 字"）。

**改动**

- 后端：`services/llm.py` 新增 `_sample_content()` / `_mock_detect()` / `detect_novel()`；`routers/novels.py` 新增 `POST /api/novels/detect`。
- 前端：`api.ts` 新增 `detectNovel()`；`NovelsPage.tsx` 新增 AI 识别按钮与识别结果预填逻辑；蒸馏结果标题显示采样说明。

**验证**

- `tsc --noEmit` 零错误；`npm run build` 成功（43 模块，gzip 64 KB）。
- `POST /api/novels/detect` mock 路径已验证，返回 `{market, genre, style_tags, core_theme}`。
- 多段采样头/中/尾覆盖单元测试通过。

### 2026-08-14 · 新增 §20 风格组合

按说明书第 20 章实现「风格组合」，把多个已有 Style Profile 重新计算成一个新风格。

**能力**

- **共同规则**：多个风格在同一维度取值一致时合并为「共同」特征，稳定度按来源小说数加权平均。
- **冲突规则 + 优先级**：同一维度出现不同取值时判定为冲突，按加权稳定度排序，最高者「冲突-采纳」（优先级最高）、其余「冲突-弃用」并保留取舍记录；采纳项的稳定度按冲突程度下调，如实反映不确定性。
- **标签/市场/题材并集**：`style_tags / market / genre` 跨风格取并集；组合结果可继续导出 Skill。
- 每个特征带 `origin` 标记（共同 / 独有 / 冲突-采纳 / 冲突-弃用），前端以彩色徽标区分，弃用项弱化展示。

**改动**

- 后端：`services/style.py` 新增 `combine()` / `_combine_profile()`；`routers/styles.py` 新增 `POST /api/styles/combine`；`schemas.py` 新增 `CombineRequest` 并给 `StyleFeatureOut` 增加 `origin`；`models.py` 的 `StyleFeature` 新增 `origin` 列。
- 迁移：`core/database.py` 增加轻量自动补列（`_automigrate`），使既有 `app.db` 平滑新增 `origin` 列，无需重建库。
- 前端：`StylesPage` 新增「② 风格组合」卡片（多选风格 + 组合），详情页展示 `origin` 徽标；`ui.tsx` 新增 `OriginBadge`；`api.ts` / `types.ts` 同步。

**验证**

- 后端：`combine()` 单元测试覆盖共同/冲突/加权/并集路径；`POST /api/styles/combine` HTTP 端到端跑通（含冲突取舍、来源并集、自动描述），边界校验（<2 个风格返回 400）通过；测试数据已清理。
- 前端：`tsc --noEmit` 零错误；`npm run build` 成功（43 模块，gzip 64 KB）。

### 2026-08-14 · 端到端验证 & 上传安全核查

本次不新增功能，对现有实现做了完整的可运行性验证，并完成 GitHub 上传前的敏感信息核查。结论：**系统可运行、可交付，可安全上传。**

**后端验证（FastAPI + SQLite）**

- 模块导入正常，全部 API 端点齐备：小说管理/上传/蒸馏、风格聚类、Skill 导出/预览/下载、Dashboard、设置。
- 真实 HTTP 闭环测试全部通过：健康检查 → 2 本小说（均已蒸馏完成）→ 1 个风格 Profile（稳定性 82.6，23 个特征）→ 导出 Skill → 预览 9 个文件 → 下载 3.7 KB zip 包。
- 导出的 Skill 包结构符合 §17（`SKILL.md / style.yaml / rules.md / plot.md / character.md / rhythm.md / dialogue.md / language.md / examples.md`），内容遵循 §19 原则（不复制原文、不模仿作者、不生成正文）。
- 验证中产生的临时 Skill 记录已清理，数据库恢复干净状态。

**前端验证（React + TS + Tailwind）**

- `tsc --noEmit` 类型检查零错误。
- `npm run build` 生产构建成功（43 模块，gzip 63 KB）；`dist/` 已被 gitignore，不入库。

**上传安全核查**

- git 仅跟踪 45 个源码/配置文件；`.venv/`、`node_modules/`、`app/backend/data/`（含 `app.db`）、`.env`、素材库 txt 均已被正确忽略。
- 全量扫描跟踪文件，未发现真实 API Key、token、密码、邮箱、手机号、真实姓名或本机绝对路径。
- API Key 仅落库于已忽略的 `data/app.db`，接口回显一律脱敏，符合设计预期。
