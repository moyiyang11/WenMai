# AI 小说风格蒸馏与 Skill 导出系统

> 从优秀网络小说中提取稳定的创作规律，将"看不见的风格"转换成结构化、可比较、可验证、可导出的 AI **Style Skill**。

本系统**不生成小说正文**，只负责：收集 → AI 蒸馏 → 风格提取 → 稳定性分析 → Skill 导出。

---

## 功能概览

```
小说导入（批量 / 单本） → AI 识别市场·题材·标签 → 单本蒸馏（多段采样）
  → 多小说聚类 → 共同特征提取 → 风格稳定性分析
  → Style Profile → 风格组合（冲突取舍）→ Style Skill 导出（zip）
```

| 模块 | 功能 |
|------|------|
| 小说库·蒸馏 | 批量/单本导入 txt，AI 自动识别市场/题材/标签，批量蒸馏，重复检测 |
| 风格中心 | 多小说聚类生成 Style Profile，风格组合（共同/冲突规则），AI 生成风格名称 |
| Skill 导出 | 从 Profile 生成 11 个机制文件，预览后下载 zip |
| 工作台 | 数据概览（小说数/蒸馏率/风格数/Skill 数）|
| 系统设置 | 网页配置 DeepSeek API Key，测试连接，一键清除 |

---

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | React 18 · TypeScript · Tailwind CSS · Vite |
| 后端 | Python · FastAPI · SQLAlchemy · Pydantic |
| 数据库 | SQLite（MVP） |
| AI | DeepSeek（OpenAI 兼容接口），无 Key 时自动降级本地启发式 mock |

---

## 快速开始

### 方式 A — 一键启动（推荐）

首次运行自动创建 venv、安装前后端依赖，并分别拉起后端（`:8000`）与前端（`:5173`）。

```bash
# Windows（双击或在 Git Bash 中）
app/start.bat

# macOS / Linux / Git Bash
cd app && ./start.sh
```

启动后访问 **http://127.0.0.1:5173**

### 方式 B — 手动启动

**后端**

```bash
cd app/backend
python -m venv .venv

# Windows (Git Bash)
.venv/Scripts/python.exe -m pip install -r requirements.txt
cp .env.example .env          # 可选：填入 DEEPSEEK_API_KEY

.venv/Scripts/python.exe -m uvicorn main:app --reload --port 8000
```

API 文档：http://127.0.0.1:8000/docs  
健康检查（显示当前是真实模型还是 mock）：`GET /api/health`

**前端**

```bash
cd app/frontend
npm install
npm run dev      # http://127.0.0.1:5173（已配置 /api 代理到 8000）
```

---

## AI 接入（DeepSeek）

两种方式均**不会把 Key 写入受 git 追踪的文件**：

**1. 网页配置（推荐）**  
启动后进入 **系统设置 · AI**，填入 Key → 保存 → 点「测试连接」。  
Key 落库于 `app/backend/data/app.db`（已 gitignore），接口回显一律脱敏，可随时「清除 Key」回退 mock。

**2. `.env` 文件**  
在 `app/backend/.env` 写入 `DEEPSEEK_API_KEY=sk-xxx`（文件已 gitignore）。

> 优先级：**网页配置 > .env > mock**  
> 申请 Key：https://platform.deepseek.com

---

## 使用流程

### 1. 导入小说

- **单本**：上传 txt → 点「AI 自动识别」预填市场/题材/标签 → 「导入」
- **批量**：切换到「批量导入」卡片，多选 txt → 「AI 批量识别」（每本单独识别）→ 「批量导入」
- 重复上传时前端立即警告、后端返回 409，已存在的文件自动跳过

### 2. 蒸馏

- 单本点「蒸馏」；或在小说列表右上角点「批量蒸馏（N 个未蒸馏）」
- 蒸馏采用**自适应多段均匀采样**（按小说长度自动选 5–16 段，均匀分布全文）
- AI 返回空内容时自动重试一次，仍失败则降级 mock 并标注原因，不阻塞批量流程

### 3. 风格聚类

- 勾选 ≥ 2 本已蒸馏小说 → （可选）点「AI 生成名称」获取 3 个建议 → 填风格名 → 「生成 Style Profile」
- 特征稳定度分级：核心（≥85%）/ 重要（≥65%）/ 辅助（≥45%）/ 偶然（<45%）

### 4. 风格组合

- 勾选 ≥ 2 个已有 Profile → 填组合名 → 「生成组合风格」
- 同维度取值一致 → **共同**特征；取值冲突 → 按加权稳定度**采纳/弃用**，带 origin 标记

### 5. Skill 导出

- 选择 Profile → 「导出为 Skill」→ 预览各文件 → 下载 zip

导出包包含 11 个文件：

```
style-skill/
├── SKILL.md          # 导航与使用说明
├── style.yaml        # 核心参数
├── rules.md          # 可执行约束 + 验证清单
├── mechanisms.md     # 参数行为映射表
├── plot.md           # 冲突/推进/反转机制模型
├── patterns.md       # 爽点模板（7 种）
├── chapter_rules.md  # 章节结构规则
├── character.md      # 主角行为 + 成长模型
├── dialogue.md       # 对话功能分类 + 节奏规则
├── language.md       # 句段规则 + 描写类型表
└── examples.md       # 示例节奏
```

---

## 目录结构

```
app/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── models.py            # ORM 模型
│   ├── schemas.py           # Pydantic 请求/响应
│   ├── core/                # config · database（含自动补列迁移）
│   ├── services/
│   │   ├── llm.py           # DeepSeek / mock 蒸馏·检测·命名
│   │   ├── style.py         # 聚类 · 稳定性分析 · 风格组合
│   │   ├── skill.py         # Skill 11 文件生成 · zip 导出
│   │   └── tags.py          # 标签 get-or-create
│   └── routers/             # dashboard · novels · styles · skills · settings
└── frontend/
    └── src/
        ├── api.ts · types.ts
        ├── App.tsx
        ├── components/      # ui · DistillDetail · CurveChart
        └── pages/           # Dashboard · Novels · Styles · Skills · Settings
```

---

## 说明

- 数据库与导出文件在 `app/backend/data/`（首次启动自动建表，`data/` 已 gitignore）
- mock 蒸馏是**确定性启发式**（以标题为种子），可离线跑通完整闭环，仅用于演示
- 接入 DeepSeek 后，蒸馏、检测、风格命名均走真实模型，按同一 JSON schema 输出

---
