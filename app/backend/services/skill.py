"""Style Skill 导出 v2.0（机制层）。

文件结构：
SKILL.md / style.yaml / rules.md / mechanisms.md /
plot.md / patterns.md / chapter_rules.md /
character.md / dialogue.md / language.md / examples.md
"""
from __future__ import annotations

import io
import zipfile

import yaml

from core.config import BASE_DIR

EXPORT_DIR = BASE_DIR / "data" / "exports"

# ── 参数行为映射表 ────────────────────────────────────────────────────────────

_PACE = {
    "slow": {
        "定义": "缓慢沉浸型步调",
        "行为规则": [
            "可在同一场景停留多章，重视氛围铺垫",
            "人物内心、世界细节描写充分",
            "每章不强制有剧情位置变化",
            "对话与描写比例：约 3:7",
        ],
        "禁止": ["强行跳过重要情感铺垫", "压缩世界设定建构"],
    },
    "medium": {
        "定义": "均衡推进型步调",
        "行为规则": [
            "每章有 1~2 个明确事件推进",
            "铺垫与推进各占约一半篇幅",
            "每章结尾有轻悬念或小爽点",
        ],
        "禁止": ["连续两章无任何剧情推进"],
    },
    "fast": {
        "定义": "快速推进型步调",
        "行为规则": [
            "每章必须有明确事件推进——主角位置 / 关系 / 实力 / 信息至少一项发生变化",
            "开头 200 字内切入主要事件或冲突",
            "冲突节点间隔：不超过 500 字无冲突",
            "同一静态场景不超过 800 字",
            "每章结尾必须有钩子（悬念 / 爽点 / 新问题）",
        ],
        "禁止": [
            "大段景物描写无剧情推进",
            "主角原地踏步超过一章",
            "冗余重复的心理独白（连续出现相同主题超过 300 字）",
        ],
    },
}

_CONFLICT_DENSITY = {
    "low": {
        "定义": "低冲突密度",
        "行为规则": ["以情感 / 信息推进为主", "冲突为辅助节点", "每 2~3 章一个主要冲突"],
    },
    "medium": {
        "定义": "中等冲突密度",
        "行为规则": ["每章有 1 个主要冲突节点", "冲突来源：外部阻力或内部矛盾"],
    },
    "high": {
        "定义": "高冲突密度",
        "行为规则": [
            "每章至少 2 个冲突节点",
            "冲突类型多样：外部对抗 / 利益争夺 / 信息不对等 / 内部挣扎",
            "冲突必须有升级节点（强度递增）",
            "每个主要冲突需有明确结果（胜 / 败 / 僵持 / 新变量）",
        ],
        "禁止": ["同一冲突无进展拖延超过 500 字"],
    },
}

_REVERSAL = {
    "low": {
        "定义": "低反转密度",
        "行为规则": ["信息基本透明，事件线性推进", "无需刻意埋设大量伏笔"],
    },
    "medium": {
        "定义": "中等反转密度",
        "行为规则": ["关键节点有反转（信息差揭示 / 局势逆转）", "重要伏笔在 5~10 章内回收"],
    },
    "medium_high": {
        "定义": "中高反转密度",
        "行为规则": [
            "每 2 章有一次中等反转（信息差 / 局势逆转 / 身份误会揭示）",
            "大章节节点有身份 / 背景 / 动机反转",
            "伏笔链：每埋一个伏笔须在 3~5 章内有中间线索，不超过 10 章回收",
        ],
        "禁止": ["无伏笔的突然反转（'凭空'变化）"],
    },
    "high": {
        "定义": "高反转密度",
        "行为规则": [
            "每章至少一次信息反转或局势逆转",
            "大高潮有多重反转叠加（3 层以上）",
            "每条支线结束前必须有一次认知颠覆",
            "伏笔回收率：主线伏笔 100% 回收，支线 ≥ 80%",
        ],
        "禁止": ["空洞反转（无前期铺垫）", "反转后无情感落地"],
    },
}

_PAYOFF_FREQ = {
    "low": {
        "定义": "爽点稀疏",
        "行为规则": ["积累为主，大爽点间隔 5 章以上", "重视压抑感的积累"],
    },
    "medium": {
        "定义": "中等爽点频率",
        "行为规则": ["每 2~3 章一个明确爽点节奏", "小爽点（打脸 / 升级小节点）穿插"],
    },
    "high": {
        "定义": "高爽点频率",
        "行为规则": [
            "每章必须有至少 1 个明确爽点节奏",
            "爽点结构：压制 → 反差 → 兑现（不可缺省任一环节）",
            "爽点类型多样，不单一重复同类爽点超过 3 章",
            "连续爽点间需有简短喘息（100~200 字情绪落地）",
        ],
        "禁止": ["爽点无前置铺垫直接兑现", "同类爽点连续堆叠超过 3 章"],
    },
}

_PROTAGONIST_AGENCY = {
    "low": {
        "定义": "主角被动响应",
        "行为规则": ["主角以响应外部事件为主", "被外力推动，主动决策少"],
    },
    "medium": {
        "定义": "主动与被动均衡",
        "行为规则": ["主角主动行动约占 50%", "有明确个人计划和目标"],
    },
    "high": {
        "定义": "高主动性主角",
        "行为规则": [
            "主角主动调查 / 布局 / 争夺资源",
            "主动利用信息差制造优势",
            "主动创造机会，不等待事件发生",
            "即便处于劣势也有明确主动策略",
            "每 3 章至少一次主角主动发起的行动",
        ],
        "禁止": ["主角连续超过 2 章纯被动响应", "主角在关键节点无任何主观决策"],
    },
}

_PROTAGONIST_GROWTH = {
    "slow": {"定义": "缓慢稳定成长", "行为规则": ["每阶段积累明显", "不强制事件后立刻升级"]},
    "steady": {
        "定义": "稳步成长",
        "行为规则": ["每个重要阶段有明确成长节点", "成长有因果（事件→积累→突破）"],
    },
    "rapid": {
        "定义": "快速成长模型",
        "行为规则": [
            "成长链：事件 → 获取资源/认知 → 实质成长 → 面对新挑战",
            "每个重要事件后主角有实质成长（能力 / 见识 / 地位至少一项）",
            "挑战难度与主角成长速度匹配（成长越快，威胁升级越快）",
            "成长必须可感知（对比变化：对手/同级/环境反应的变化）",
        ],
        "禁止": ["成长无明确原因（无来源的突然变强）", "成长停滞超过 3 章"],
    },
}

_DIALOGUE_DENSITY = {
    "low": {
        "定义": "叙述主导型",
        "行为规则": ["对话辅助叙述，不超过篇幅 30%", "对话用于关键信息传递"],
    },
    "medium": {
        "定义": "均衡对话型",
        "行为规则": ["对话与叙述约各占 40%~50%", "对话推进信息，叙述补充情感"],
    },
    "high": {
        "定义": "高对话密度",
        "行为规则": [
            "对话占比 ≥ 55%",
            "每段对话必须有明确功能：推进剧情 / 制造冲突 / 释放信息 / 区分人物性格",
            "对话不可为纯寒暄（无功能对话须删除或合并）",
            "通过对话节奏控制信息释放（不一次说完）",
            "不同人物对话语气需有明显差异（体现性格）",
        ],
        "禁止": ["无功能的闲聊对话超过 100 字", "所有人物对话风格趋同"],
    },
}

_INFO_DENSITY = {
    "low": {"定义": "低信息密度", "行为规则": ["节奏舒缓，信息逐步释放", "允许留白和感官描写"]},
    "medium": {"定义": "中等信息密度", "行为规则": ["适量信息节点", "重要信息有铺垫"]},
    "high": {
        "定义": "高信息密度",
        "行为规则": [
            "每段文字必须承载有效信息（情节 / 人物 / 世界观）",
            "减少重复和冗余（同一信息不可在 500 字内重述）",
            "建立悬念信息差：读者获得的信息比主角多（或少）以制造张力",
            "信息节奏：重要信息前有铺垫，不突兀出现",
        ],
        "禁止": ["重复叙述已交代信息", "大量无信息量的过渡段落"],
    },
}

# ── 爽点模板库 ───────────────────────────────────────────────────────────────

_PAYOFF_TEMPLATES = {
    "打脸": {
        "结构": "他者轻视 → 主角隐忍/承压 → 关键时刻反转局势 → 直接打脸 → 围观者反应收束",
        "铺垫要求": "对方的轻视须有 1~2 章积累，主角隐忍需有情感代价",
        "兑现要求": "打脸须在同一场景完成，不可事后回忆式打脸",
        "强度控制": "重要打脸场景需有围观者作情感放大器",
        "示例节奏": ["对方公开轻视（200字）", "主角承压（100字）", "关键反转触发（50字）", "打脸兑现（300字）", "围观反应（100字）"],
    },
    "升级": {
        "结构": "实力瓶颈/危机触发 → 关键机缘/努力突破 → 突破展示 → 周围认可/震惊",
        "铺垫要求": "瓶颈须在突破前 2~3 章有明确体现",
        "兑现要求": "突破展示需直接对比（前后差距可感知）",
        "强度控制": "大升级节点需配合重要战斗或事件",
        "示例节奏": ["瓶颈压力（150字）", "机缘触发（100字）", "突破过程（200字）", "新实力展示（200字）", "外部认可（100字）"],
    },
    "扮猪吃虎": {
        "结构": "主角示弱/被低估 → 对方盲目自大并施压 → 主角亮出底牌 → 对方错愕 → 优势确立",
        "铺垫要求": "主角隐藏实力须有合理动机，对方的自大需有行为体现",
        "兑现要求": "底牌揭示需一气呵成，不拖泥带水",
        "强度控制": "对方越自大，揭示时落差越大，爽感越强",
        "示例节奏": ["主角示弱/被轻视（300字）", "对方施压自大（200字）", "揭底牌时机（50字）", "力量展示（300字）", "对方错愕崩溃（150字）"],
    },
    "逆袭": {
        "结构": "陷入绝境/极度劣势 → 找到转机/坚持意志 → 发起反击 → 形势逆转 → 胜利确立",
        "铺垫要求": "绝境需充分渲染（身体/心理/外部全面压制）",
        "兑现要求": "反击触发需有明确原因（非奇迹，而是积累爆发）",
        "强度控制": "绝境越深，逆袭越震撼",
        "示例节奏": ["绝境渲染（400字）", "转机出现（100字）", "反击启动（100字）", "逆转过程（400字）", "胜利确立（150字）"],
    },
    "反杀": {
        "结构": "被追杀/打压 → 边逃边积累优势 → 关键反击点出现 → 反杀 → 地位确立",
        "铺垫要求": "积累优势须有具体形式（信息差 / 陷阱 / 关键道具 / 盟友）",
        "兑现要求": "反杀节点需精准把握时机感（不早不晚）",
        "强度控制": "对方死前的震惊反应是爽点的放大器",
        "示例节奏": ["被追/压制（300字）", "暗中积累（200字）", "时机触发（50字）", "反杀（350字）", "地位确立（100字）"],
    },
    "阴谋反转": {
        "结构": "表面局势（误导读者）→ 主角/读者发现异常 → 隐藏布局揭示 → 惊讶落地 → 局势重塑",
        "铺垫要求": "误导伏笔须早于揭示 5 章以上埋设",
        "兑现要求": "揭示须一次性完整，不分散",
        "强度控制": "揭示前的最后一个误导细节越强，反转越震撼",
        "示例节奏": ["表面局势（贯穿数章）", "异常细节暗示（100字）", "揭示触发（50字）", "全面揭示（400字）", "局势重塑（200字）"],
    },
    "伏笔揭晓": {
        "结构": "前期埋设（轻描淡写）→ 线索强化（1~2次提示）→ 揭晓时机到来 → 揭示 → 读者恍然 → 情节升华",
        "铺垫要求": "埋设时必须自然（不可刻意突出），揭晓前需有1次线索强化",
        "兑现要求": "揭晓须与当前情节产生直接联系，非孤立",
        "强度控制": "揭晓后需给读者'回顾反应'空间（主角/配角对应的回忆或联想）",
        "示例节奏": ["埋设（轻描淡写，50字内）", "线索强化（100字）", "揭晓时机（情节触发）", "揭示（300字）", "升华（150字）"],
    },
}

# ── 冲突机制 ─────────────────────────────────────────────────────────────────

_CONFLICT_MODEL = """## 冲突结构模型

```
目标 → 障碍 → 冲突 → 升级 → 结果（胜/败/僵持/新变量）
```

## 冲突来源分类

| 类型 | 说明 | 适用场景 |
|------|------|------|
| 外部对抗冲突 | 人物之间的直接对立 | 战斗/争夺/角逐 |
| 利益争夺冲突 | 资源/地位/信息的竞争 | 权谋/商战/势力争斗 |
| 信息不对等冲突 | 一方掌握对方不知道的信息 | 悬念/反转/布局 |
| 内部矛盾冲突 | 人物自身价值观/能力的限制 | 成长/选择/挣扎 |
| 环境压力冲突 | 外部环境对所有人造成压力 | 末世/危机/灾难 |

## 冲突升级机制

冲突不可单层停留，须按以下方式升级：
1. **量级升级**：对手更强、威胁更大、资源更少
2. **维度升级**：从一种冲突演变为多种冲突叠加
3. **代价升级**：失败的后果越来越严重
4. **关系升级**：普通对手 → 重要对手 → 生死对手

## 冲突解决规则

- 每个冲突必须有明确结果，不允许无结果地淡化消失
- 结果类型：完全胜利 / 惨胜 / 僵持（需新变量打破） / 失败（需积累资本反击）
- 失败后必须给出主角的下一步方向（不可止步于失败本身）
"""

_PROGRESSION_MODEL = """## 剧情推进模型

```
目标 → 行动 → 冲突 → 结果 → 新目标
```

每个推进单元（一章或一个场景单元）必须完成至少一个循环。

## 场景执行机制

```
场景目标 → 关键事件 → 冲突/阻力 → 行动应对 → 结果 → 变化（位置/关系/信息/实力）
```

**场景完成标准：** 场景结束时至少有一项变化——
- 人物位置/处境变化
- 人物关系变化（亲近/疏远/敌对/盟友）
- 信息变化（获得/失去/误解）
- 实力/资源变化

**禁止：** 场景开始和结束时主角和世界完全相同（静态场景）。
"""

_REVERSAL_MODEL = """## 反转类型体系

| 反转类型 | 说明 | 铺垫要求 |
|------|------|------|
| 信息反转 | 读者/主角认知的关键信息被推翻 | 误导信息须至少提前 3 章埋设 |
| 局势反转 | 胜负/强弱关系突然逆转 | 反转契机须有积累基础 |
| 身份反转 | 人物真实身份/立场与表面不同 | 身份线索须在揭示前 5 章有暗示 |
| 伏笔反转 | 前期伏笔在高潮处回收并改变局势 | 伏笔须在设置时自然不突兀 |
| 动机反转 | 人物行为背后的真实动机与表面不同 | 动机线索须贯穿人物出现的全程 |

## 反转铺垫原则

1. **自然埋设**：伏笔不可过于突兀，须融入情节
2. **线索强化**：重要反转前需有 1~2 次轻度暗示
3. **不提前泄底**：铺垫暗示强度不可超过揭示本身
4. **落地反应**：反转后须有人物/读者的情感落地（惊讶/恍然/重新评估）
"""


def _mechanisms_md(profile: dict) -> str:
    """生成参数行为映射文档（机制层 v2.0 核心文件）。"""
    nav = profile.get("narrative", {})
    plt = profile.get("plot", {})
    emo = profile.get("emotion", {})
    cha = profile.get("character", {})
    lang = profile.get("language", {})

    def _block(label: str, mapping: dict, key: str) -> str:
        val = mapping.get(key, {})
        if not val:
            return f"### {label}：`{key}`\n（无映射）\n\n"
        lines = [f"### {label}：`{key}` — {val.get('定义', '')}"]
        lines.append("\n**行为规则：**")
        for r in val.get("行为规则", []):
            lines.append(f"- {r}")
        if val.get("禁止"):
            lines.append("\n**禁止：**")
            for r in val["禁止"]:
                lines.append(f"- ❌ {r}")
        return "\n".join(lines) + "\n"

    sections = ["# 机制层：参数行为映射\n\n> 本文件将 style.yaml 中的抽象参数转化为可执行的创作行为规则。\n"]
    sections.append("## 叙事节奏\n")
    sections.append(_block("节奏（pace）", _PACE, nav.get("pace", "")))
    sections.append("## 剧情机制\n")
    sections.append(_block("冲突密度（conflict_density）", _CONFLICT_DENSITY, plt.get("conflict_density", "")))
    sections.append(_block("反转密度（reversal_density）", _REVERSAL, plt.get("reversal_density", "")))
    sections.append(_block("推进速度（progression）", {
        "slow": {"定义": "慢速推进", "行为规则": ["细腻铺垫，稳步发展"]},
        "steady": {"定义": "稳定推进", "行为规则": ["有节奏的阶段性推进，铺垫与推进均衡"]},
        "rapid": {
            "定义": "快速推进",
            "行为规则": [
                "目标 → 行动 → 冲突 → 结果 → 新目标，每章完成至少一个推进循环",
                "每章必须有剧情位置变化（不允许原地踏步）",
                "推进速度与爽点频率匹配",
            ],
            "禁止": ["连续两章无实质推进", "目标模糊超过一章"],
        },
    }, plt.get("progression", "")))
    sections.append("## 情绪爽点\n")
    sections.append(_block("爽点频率（payoff_frequency）", _PAYOFF_FREQ, emo.get("payoff_frequency", "")))
    sections.append("## 人物机制\n")
    sections.append(_block("主角能动性（protagonist_agency）", _PROTAGONIST_AGENCY, cha.get("protagonist_agency", "")))
    sections.append(_block("主角成长速度（protagonist_growth）", _PROTAGONIST_GROWTH, cha.get("protagonist_growth", "")))
    sections.append("## 语言机制\n")
    sections.append(_block("对话密度（dialogue_density）", _DIALOGUE_DENSITY, lang.get("dialogue_density", "")))
    sections.append(_block("信息密度（information_density）", _INFO_DENSITY, lang.get("information_density", "")))
    return "\n".join(sections)


def _plot_md(profile: dict) -> str:
    """剧情机制文档（冲突 + 推进 + 反转）。"""
    plt = profile.get("plot", {})
    sections = [
        f"# 剧情机制\n\n**冲突密度：** `{plt.get('conflict_density', '—')}`  "
        f"**反转密度：** `{plt.get('reversal_density', '—')}`  "
        f"**推进速度：** `{plt.get('progression', '—')}`\n",
        _CONFLICT_MODEL,
        _PROGRESSION_MODEL,
        _REVERSAL_MODEL,
    ]
    return "\n".join(sections)


def _patterns_md(profile: dict) -> str:
    """爽点 / 冲突 / 反转模板库，根据 style_tags 优先展示相关模板。"""
    tags = set(profile.get("style_tags", []))
    payoffs = list(profile.get("emotion", {}).get("main_payoffs", [])) if isinstance(
        profile.get("emotion"), dict) else []

    # 优先展示 tags/payoffs 匹配的模板，其余追加
    priority = []
    for t in payoffs + list(tags):
        if t in _PAYOFF_TEMPLATES and t not in priority:
            priority.append(t)
    rest = [k for k in _PAYOFF_TEMPLATES if k not in priority]
    order = priority + rest

    lines = ["# Pattern 模板库\n\n## 爽点模板\n\n"]
    lines.append("> 每种爽点都有完整的铺垫-压制-反差-兑现结构，不可跳过任一环节。\n")
    for key in order:
        tpl = _PAYOFF_TEMPLATES[key]
        lines.append(f"### {key}\n")
        lines.append(f"**结构：** {tpl['结构']}\n")
        lines.append(f"**铺垫要求：** {tpl['铺垫要求']}")
        lines.append(f"**兑现要求：** {tpl['兑现要求']}")
        lines.append(f"**强度控制：** {tpl['强度控制']}")
        steps = tpl.get("示例节奏", [])
        if steps:
            lines.append("**示例节奏：**")
            for i, s in enumerate(steps, 1):
                lines.append(f"  {i}. {s}")
        lines.append("")
    return "\n".join(lines)


def _chapter_rules_md(profile: dict) -> str:
    """章节结构规则（章节节奏 + 场景执行）。"""
    nav = profile.get("narrative", {})
    plt = profile.get("plot", {})
    emo = profile.get("emotion", {})
    pace = nav.get("pace", "medium")
    drive = nav.get("drive", "event_driven")
    conflict_d = plt.get("conflict_density", "medium")
    payoff_f = emo.get("payoff_frequency", "medium")

    open_rules = {
        "fast": ["快速切入主要事件或冲突（200 字内）", "直接建立本章目标", "禁止开篇大段景物描写"],
        "medium": ["简短铺垫后切入主要事件", "建立本章核心矛盾"],
        "slow": ["可用景物/氛围铺垫", "逐步进入场景，不强求快速切入"],
    }.get(pace, ["建立本章目标和核心矛盾"])

    mid_rules = {
        "event_driven": ["事件持续推进", "每个场景单元有明确结果"],
        "character_driven": ["人物关系/内心深化", "通过行为展示性格变化"],
        "puzzle_driven": ["逐步释放信息", "建立/强化悬念"],
    }.get(drive, ["推进核心剧情"])

    if conflict_d == "high":
        mid_rules += ["升级冲突强度", "多冲突节点交织"]
    elif conflict_d == "medium":
        mid_rules += ["维持一个主要冲突线"]

    end_rules = {
        "high": ["必须有悬念钩子（未解决问题）或爽点（情绪释放）", "制造下章期待"],
        "medium": ["有轻悬念或小结"],
        "low": ["场景收束，情绪落地"],
    }.get(payoff_f, ["完成本章目标，建立下章动机"])

    lines = [
        "# 章节结构规则\n",
        "## 章节节奏框架\n",
        f"**节奏类型：** `{pace}` | **驱动模式：** `{drive}` | **冲突密度：** `{conflict_d}` | **爽点频率：** `{payoff_f}`\n",
        "### 开头（前 15%~20%）\n",
    ]
    for r in open_rules:
        lines.append(f"- {r}")
    lines.append("\n### 中段（20%~75%）\n")
    for r in mid_rules:
        lines.append(f"- {r}")
    lines.append("\n### 结尾（最后 25%）\n")
    for r in end_rules:
        lines.append(f"- {r}")

    lines.append("""
## 场景执行检查清单

每个场景结束前确认：
- [ ] 场景开始和结束时至少有一项变化（位置/关系/信息/实力）
- [ ] 本场景目标是否完成或有明确进展
- [ ] 是否有冲突或阻力节点（根据冲突密度要求）
- [ ] 对话是否有明确功能（推进/冲突/信息/人物区分）
- [ ] 是否有下一场景的钩子或动机

## 禁止事项

- ❌ 静态场景（开始和结束完全一样）
- ❌ 无任何冲突/推进的过渡章节（允许最多 1 章喘息，但需有信息价值）
- ❌ 大段重复已交代信息
- ❌ 章节结尾无任何情绪落点
""")
    return "\n".join(lines)


def _character_md(profile: dict) -> str:
    cha = profile.get("character", {})
    agency = cha.get("protagonist_agency", "")
    growth = cha.get("protagonist_growth", "")
    agency_def = _PROTAGONIST_AGENCY.get(agency, {}).get("定义", agency)
    growth_def = _PROTAGONIST_GROWTH.get(growth, {}).get("定义", growth)
    rules_a = _PROTAGONIST_AGENCY.get(agency, {}).get("行为规则", [])
    rules_g = _PROTAGONIST_GROWTH.get(growth, {}).get("行为规则", [])
    lines = [
        f"# 人物机制\n\n**主角能动性：** `{agency}` — {agency_def}\n**主角成长：** `{growth}` — {growth_def}\n",
        "## 主角行为定义\n",
    ]
    for r in rules_a:
        lines.append(f"- {r}")
    lines.append("\n## 成长模型\n")
    for r in rules_g:
        lines.append(f"- {r}")
    lines.append("""
## 人物一致性规则

- 主角行为须与已建立的性格逻辑一致（不可突然 OOC）
- 重要配角需有独立动机，不单纯服务于主角剧情
- 反派须有合理行动逻辑（不可只为了"被打脸"而存在）
- 人物成长须有代价（成长越快，付出越多）
""")
    return "\n".join(lines)


def _dialogue_md(profile: dict) -> str:
    lang = profile.get("language", {})
    dlg = lang.get("dialogue_density", "")
    dlg_def = _DIALOGUE_DENSITY.get(dlg, {}).get("定义", dlg)
    rules = _DIALOGUE_DENSITY.get(dlg, {}).get("行为规则", [])
    bans = _DIALOGUE_DENSITY.get(dlg, {}).get("禁止", [])
    lines = [
        f"# 对话机制\n\n**对话密度：** `{dlg}` — {dlg_def}\n",
        "## 行为规则\n",
    ]
    for r in rules:
        lines.append(f"- {r}")
    if bans:
        lines.append("\n## 禁止\n")
        for b in bans:
            lines.append(f"- ❌ {b}")
    lines.append("""
## 对话功能分类

每段对话至少承担以下功能之一：
1. **推进剧情**：对话导致行动或决策
2. **制造冲突**：对话引发矛盾或对立
3. **释放信息**：对话传递关键情报或世界观
4. **人物区分**：对话体现人物独特性格和说话方式
5. **情感连接**：建立人物关系的情感节点

## 对话节奏规则

- 信息型对话：逐步释放，不一次说完（制造悬念）
- 冲突型对话：节奏紧凑，短句为主
- 情感型对话：节奏舒缓，有停顿和内心描写
""")
    return "\n".join(lines)


def _language_md(profile: dict) -> str:
    lang = profile.get("language", {})
    sent = lang.get("sentence_length", "")
    desc = lang.get("description_density", "")
    info = lang.get("information_density", "")
    info_def = _INFO_DENSITY.get(info, {}).get("定义", info)
    info_rules = _INFO_DENSITY.get(info, {}).get("行为规则", [])
    info_bans = _INFO_DENSITY.get(info, {}).get("禁止", [])

    sent_map = {
        "short": "短句为主（≤15字/句）：强烈紧张感，多用于战斗/冲突场景",
        "short_medium": "短中句混合（15~25字/句）：节奏感强，适合快节奏叙事",
        "medium": "中等句式（25~40字/句）：叙述均衡，标准网文节奏",
        "long": "长句为主（>40字/句）：文学性强，适合沉浸型叙事",
    }
    desc_map = {
        "low": "描写克制，以推进为主；环境/外貌描写不超过 3 句",
        "medium": "描写适中，关键场景充分描写；非关键场景简写",
        "high": "描写丰富，沉浸感强；需确保描写服务于氛围或人物，不做无关堆砌",
    }
    lines = [
        "# 语言机制\n",
        f"**句长风格：** `{sent}` — {sent_map.get(sent, sent)}\n",
        f"**描写密度：** `{desc}` — {desc_map.get(desc, desc)}\n",
        f"**信息密度：** `{info}` — {info_def}\n",
        "\n## 信息密度规则\n",
    ]
    for r in info_rules:
        lines.append(f"- {r}")
    if info_bans:
        lines.append("\n## 禁止\n")
        for b in info_bans:
            lines.append(f"- ❌ {b}")
    lines.append("""
## 描写类型与优先级

| 描写类型 | 用途 | 优先级 |
|------|------|------|
| 动作描写 | 战斗/冲突/紧张场景 | 按冲突密度调整 |
| 心理描写 | 人物决策/情感节点 | 关键决策必须有 |
| 环境描写 | 场景建立/氛围渲染 | 非快节奏场景使用 |
| 外貌描写 | 人物初次出场/关键转变 | 简洁，不超过 5 行 |
| 感官描写 | 沉浸感/特殊场景 | 按节奏需要使用 |

## 段落节奏规则

- 快节奏段落：每段 2~4 句，频繁换段
- 慢节奏段落：每段 5~8 句，情感积累
- 对话段落：一句对话一段或两段，清晰易读
""")
    return "\n".join(lines)


def _rules_md(name: str, profile: dict, features: list[dict]) -> str:
    core = [f for f in features if f["level"] == "核心特征"]
    important = [f for f in features if f["level"] == "重要特征"]
    nav = profile.get("narrative", {})
    plt = profile.get("plot", {})
    emo = profile.get("emotion", {})
    cha = profile.get("character", {})

    # 生成可执行的核心规则摘要
    exec_rules = []
    if nav.get("pace") == "fast":
        exec_rules.append("每章必须有明确事件推进，开头 200 字内切入冲突，结尾必须有钩子")
    if plt.get("conflict_density") == "high":
        exec_rules.append("每章至少 2 个冲突节点，冲突须有升级，不允许无结果冲突")
    if emo.get("payoff_frequency") == "high":
        exec_rules.append("每章至少 1 个爽点，结构：压制 → 反差 → 兑现，缺一不可")
    if plt.get("reversal_density") in ("high", "medium_high"):
        exec_rules.append("每 2 章需有一次信息反转或局势逆转，伏笔必须回收")
    if cha.get("protagonist_agency") == "high":
        exec_rules.append("主角必须主动布局/争夺/利用信息差，不允许连续 2 章纯被动")
    if cha.get("protagonist_growth") == "rapid":
        exec_rules.append("每个重要事件后主角有实质成长，成长需可感知（对比前后差距）")

    lines = [f"# {name} — 核心规则（v2.0 机制层）\n"]
    if exec_rules:
        lines.append("## 可执行核心约束\n")
        lines += [f"- {r}" for r in exec_rules]
        lines.append("")
    lines.append("## 核心特征（稳定度 ≥ 90%，必须遵守）\n")
    lines += [f"- **{f['dimension']}**：{f['feature']}（{f['stability']}%）" for f in core] or ["- （无）"]
    lines.append("\n## 重要特征（70%~89%，强烈建议）\n")
    lines += [f"- **{f['dimension']}**：{f['feature']}（{f['stability']}%）" for f in important] or ["- （无）"]
    lines.append("\n## 验证清单（每章自检）\n")
    lines += [
        "- [ ] 本章是否有明确事件推进（主角位置/关系/信息/实力变化）",
        "- [ ] 冲突节点数量是否符合冲突密度要求",
        "- [ ] 爽点是否有完整的铺垫-反差-兑现结构",
        "- [ ] 对话是否有明确功能（非纯闲聊）",
        "- [ ] 章节结尾是否有悬念/爽点/新问题",
        "- [ ] 主角行为是否符合既定的能动性定义",
    ]
    lines.append("\n## 禁止事项\n")
    lines += [
        "- 禁止大段复制原文或复述具体剧情。",
        "- 禁止模仿特定作者身份。",
        "- 本 Skill 只描述可迁移的风格规律，不生成正文。",
        "- 禁止静态场景（场景前后无任何变化）。",
        "- 禁止无来源的突然反转（伏笔必须前置）。",
    ]
    return "\n".join(lines) + "\n"


def _skill_md(name: str, version: str, profile: dict, features: list[dict], source_count: int) -> str:
    core = [f["feature"] for f in features if f["level"] == "核心特征"]
    tags = "、".join(profile.get("style_tags", [])) or "—"
    market = "、".join(profile.get("market", [])) if isinstance(profile.get("market"), list) else str(profile.get("market", ""))
    genre = "、".join(profile.get("genre", [])) if isinstance(profile.get("genre"), list) else str(profile.get("genre", ""))
    return f"""# {name}

**版本：** {version}（机制层 v2.0）
**类型：** Style Skill — 风格知识与创作行为规则的可执行封装
**来源：** {source_count} 本小说蒸馏聚类
**市场：** {market}  **题材：** {genre}

## 风格定位

{tags}

## 使用场景

在进行同类网文创作/续写时，作为「风格约束层」加载，指导 AI 保持一致的
叙事节奏、冲突结构、爽点机制与语言特征。**本 Skill 不负责生成正文。**

## 核心规则（摘要）

{chr(10).join(f"- {c}" for c in core) or "- （见 rules.md）"}

## 文件说明

| 文件 | 内容 |
|------|------|
| `style.yaml` | 结构化风格参数（参数层） |
| `rules.md` | 核心规则、验证清单、禁止事项 |
| `mechanisms.md` | **参数行为映射**（每个参数的具体执行定义）|
| `plot.md` | 冲突机制 / 推进模型 / 反转体系 |
| `patterns.md` | **爽点/冲突/反转模板库**（含铺垫-兑现结构）|
| `chapter_rules.md` | 章节结构规则 / 场景执行检查清单 |
| `character.md` | 人物行为机制 / 成长模型 |
| `dialogue.md` | 对话功能分类 / 节奏规则 |
| `language.md` | 语言特征 / 描写规则 / 信息密度 |
| `examples.md` | 特征稳定度分析示例 |
"""


def build_skill_files(
    name: str, version: str, profile: dict, features: list[dict], source_count: int
) -> dict[str, str]:
    """返回 {{相对路径: 文件内容}}。v2.0 新增机制层文件。"""
    style_yaml = yaml.safe_dump({"name": name, **profile}, allow_unicode=True, sort_keys=False)
    examples = "# 特征稳定度分析\n\n" + "\n".join(
        f"- **{f['dimension']}** → {f['feature']}（稳定度 {f['stability']}%，{f['level']}）"
        for f in sorted(features, key=lambda x: -x["stability"])
    ) + "\n"
    return {
        "SKILL.md": _skill_md(name, version, profile, features, source_count),
        "style.yaml": style_yaml,
        "rules.md": _rules_md(name, profile, features),
        "mechanisms.md": _mechanisms_md(profile),
        "plot.md": _plot_md(profile),
        "patterns.md": _patterns_md(profile),
        "chapter_rules.md": _chapter_rules_md(profile),
        "character.md": _character_md(profile),
        "dialogue.md": _dialogue_md(profile),
        "language.md": _language_md(profile),
        "examples.md": examples,
    }


def export_zip(slug: str, version: str, files: dict[str, str]) -> str:
    """写出 zip，返回绝对路径。"""
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = EXPORT_DIR / f"{slug}-{version}.zip"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel, content in files.items():
            zf.writestr(f"{slug}/{rel}", content)
    zip_path.write_bytes(buf.getvalue())
    return str(zip_path)
