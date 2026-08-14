"""LLM service via DeepSeek (OpenAI-compatible); falls back to deterministic mock when no API key is set."""
from __future__ import annotations

import hashlib
import json
import re

import httpx

from core.config import settings
from services import settings_store

# ---------- 多段采样 ----------

def _sample_content(content: str, total_chars: int) -> tuple[str, str]:
    """Sample head/mid/tail thirds of content; returns (sample_text, description)."""
    n = len(content)
    if n <= total_chars:
        return content, f"全文 {n} 字(未超采样上限)"
    each = total_chars // 3
    head = content[:each]
    mid_start = max(each, n // 2 - each // 2)
    mid = content[mid_start: mid_start + each]
    tail_start = max(mid_start + each, n - each)
    tail = content[tail_start:]
    sep = "\n\n[……中略……]\n\n"
    sample = head + sep + mid + sep + tail
    pct_head = round(each / n * 100, 1)
    pct_mid = round(mid_start / n * 100, 1)
    pct_tail = round(tail_start / n * 100, 1)
    desc = (f"多段采样：前{pct_head}%({each}字)+ "
            f"中{pct_mid}%({each}字)+ "
            f"末{pct_tail}%起({len(tail)}字)，全文共 {n} 字")
    return sample, desc


# ---------- 导入预检测 schema ----------

DETECT_SCHEMA_HINT = """
你是网文编辑，快速判断小说读者市场和题材。阅读给定片段，只输出以下 JSON，不要额外文字：
{
  "market": "男频|女频|其他",
  "genre": "题材(如 玄幻/仙侠/都市/历史/科幻/悬疑/灵异/末世/古言/现言/宫斗/宅斗/年代/无限流/游戏)",
  "style_tags": ["爽文","升级","热血"],
  "core_theme": "一句话核心主题"
}
判断依据：
- 男频：升级/修炼/打怪/系统/争霸/商战/热血/无限流等男性向叙事
- 女频：穿越/宫斗/宅斗/甜宠/古言/现言/强强/CP向等女性向叙事
只输出 JSON，不要额外文字。
"""

DISTILL_SCHEMA_HINT = """
你是一名网文风格逆向分析专家。请阅读给定的小说片段，抽象出可迁移的"风格规律"，
不要复述剧情、不要照抄原文。严格输出如下 JSON(值使用中文；枚举尽量落在提示区间；
曲线类字段输出 0-100 的整数数组，长度 8-12，代表故事从开端到结尾的走势)：

{
  "basic": {
    "market": "男频|女频|其他", "genre": "题材", "core_theme": "核心主题",
    "target_reader": "目标读者", "selling_point": "核心卖点", "positioning": "故事定位"
  },
  "narrative": {
    "perspective": "first_person|third_person|omniscient|multi",
    "drive": "event_driven|character_driven|puzzle_driven", "pace": "slow|medium|fast"
  },
  "plot": {
    "conflict_density": "low|medium|high",
    "reversal_density": "low|medium|medium_high|high", "progression": "slow|steady|rapid"
  },
  "emotion": {
    "payoff_frequency": "low|medium|high", "climax_frequency": "low|medium|high",
    "main_payoffs": ["打脸","逆袭","升级"]
  },
  "character": {"protagonist_agency": "low|medium|high", "protagonist_growth": "slow|steady|rapid"},
  "language": {
    "sentence_length": "short|short_medium|medium|long", "dialogue_density": "low|medium|high",
    "description_density": "low|medium|high", "information_density": "low|medium|high"
  },
  "style_tags": ["爽文","快节奏","热血"],

  "story_structure": {
    "start": "故事起点", "core_question": "核心问题", "core_goal": "核心目标",
    "main_line": "主线", "sub_lines": ["支线1","支线2"],
    "stages": ["第一阶段","第二阶段","第三阶段"],
    "key_events": ["关键事件1","关键事件2"],
    "turning_point": "重要转折", "climax": "高潮", "low_point": "低谷", "ending": "结局走向"
  },
  "characters": {
    "protagonist": {"identity":"身份","personality":"性格","desire":"欲望","goal":"目标",
      "fear":"恐惧","flaw":"缺陷","ability":"能力","action_style":"行动方式",
      "growth_path":"成长路线","arc":"人物弧光"},
    "supporting": [{"name":"配角","role":"人物定位","function":"剧情功能","relation":"与主角关系","personality":"性格"}],
    "antagonist": {"identity":"身份","goal":"目标","motive":"动机","ability":"能力",
      "logic":"行动逻辑","conflict":"与主角冲突","ending":"最终结局"}
  },
  "relations": [
    {"from":"人物A","to":"人物B","type":"亲属|朋友|盟友|师徒|上下级|合作|对立|敌对|感情",
     "changes":["敌对","合作","信任"]}
  ],
  "events": [
    {"name":"事件名","chapter":"发生位置","characters":["参与人物"],"type":"事件类型",
     "precondition":"前置条件","conflict":"核心冲突","result":"事件结果",
     "impact_main":"对主线影响","impact_character":"对人物影响"}
  ],
  "conflicts": {
    "types": ["人物冲突","实力冲突","价值观冲突"],
    "curve": [30,45,60,70,55,80,95,70],
    "escalation": "升级方式", "resolution": "解决方式"
  },
  "foreshadows": [
    {"content":"伏笔内容","first_seen":"埋设位置","surface":"表面含义","truth":"真实含义",
     "characters":["相关人物"],"payoff":"回收位置","method":"回收方式","info_gap":"信息差"}
  ],
  "emotion_curve": {
    "process": ["压抑","积累","冲突","爆发","爽点","反馈"],
    "curve": [40,30,50,70,90,60,80,95],
    "payoff_points": [{"position":"位置","type":"爽点类型","intensity":"高|中|低","setup":"前置压抑"}]
  },
  "rhythm": {
    "chapter_words": "章节平均字数",
    "dialogue_ratio": [40,50,45,60,55,50,65,58],
    "info_density": [60,65,70,68,75,72,80,78],
    "payoff_density": [20,35,50,45,70,60,85,90],
    "reversal_freq": [10,20,30,25,40,35,55,50]
  },
  "writing": {
    "language": {"avg_sentence":"平均句长描述","long_short_ratio":"长短句比例","paragraph":"段落长度"},
    "description": {"action":"高|中|低","psychology":"高|中|低","environment":"高|中|低",
      "appearance":"高|中|低","sensory":"高|中|低"},
    "narration": {"person":"第一/第三/全知","viewpoint":"单视角/多视角","driven":"事件/人物/谜题驱动"},
    "tone": {"seriousness":"高|中|低","humor":"高|中|低","oppression":"高|中|低",
      "intensity":"高|中|低","literariness":"高|中|低","popularity":"高|中|低"}
  }
}
只输出 JSON，不要额外文字。
"""


def _extract_json(text: str) -> dict:
    """Strip markdown fences and parse JSON from LLM response text."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            return json.loads(m.group(0))
        raise


def _seeded_curve(seed: int, n: int, base: int, amp: int, rising: bool = True) -> list[int]:
    """Generate a seeded pseudo-random curve of integers in 0-100."""
    vals = []
    x = seed % 2147483647 or 1
    for i in range(n):
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        noise = (x % (2 * amp + 1)) - amp
        trend = int(i / max(n - 1, 1) * 30) if rising else 0
        vals.append(max(5, min(100, base + trend + noise)))
    return vals


def _mock_distill(title: str, content: str) -> dict:
    """Return deterministic mock distillation result when no API key is available."""
    sample, sample_desc = _sample_content(content, settings.distill_sample_chars)
    sample = sample or title
    seed = int(hashlib.md5(title.encode("utf-8")).hexdigest()[:8], 16)

    # 语言特征启发式
    dialogue_ratio = sample.count('“') / max(len(sample) / 100, 1)
    marks = sample.count("。") + sample.count("！") + sample.count("？")
    avg_sent = len(sample) / max(marks, 1)
    sent_len = "short" if avg_sent < 18 else "short_medium" if avg_sent < 30 else "medium"
    dlg = "high" if dialogue_ratio > 1.2 else "medium" if dialogue_ratio > 0.4 else "low"

    tag_hits = [t for t in ["修仙", "武道", "系统", "诡异", "都市", "玄幻", "热血", "升级", "权谋", "复仇"] if t in sample]
    is_xuanhuan = any(k in sample for k in ["修仙", "武道", "玄幻", "灵气", "修炼"])
    genre = "玄幻" if is_xuanhuan else ("都市" if "都市" in sample else "其他")
    n = 10

    return {
        "basic": {
            "market": "男频",
            "genre": genre,
            "core_theme": "成长与逆袭",
            "target_reader": "网文男频读者",
            "selling_point": "、".join(tag_hits[:3]) or "强设定 + 快节奏",
            "positioning": "长篇连载 · 升级流",
        },
        "narrative": {"perspective": "third_person", "drive": "event_driven", "pace": "fast"},
        "plot": {"conflict_density": "high", "reversal_density": "medium_high", "progression": "rapid"},
        "emotion": {
            "payoff_frequency": "high",
            "climax_frequency": "high",
            "main_payoffs": ["升级", "逆袭", "打脸"],
        },
        "character": {"protagonist_agency": "high", "protagonist_growth": "rapid"},
        "language": {
            "sentence_length": sent_len,
            "dialogue_density": dlg,
            "description_density": "medium",
            "information_density": "high",
        },
        "style_tags": ["爽文", "快节奏", "热血"] + tag_hits[:2],

        # ---- §6.2 故事结构 ----
        "story_structure": {
            "start": "主角身处困境或起点弱小",
            "core_question": "主角能否突破限制、达成目标",
            "core_goal": "变强 / 复仇 / 守护",
            "main_line": "主角沿实力/地位阶梯持续攀升",
            "sub_lines": ["感情线", "宿敌线", "身世之谜"],
            "stages": ["开局立势", "中期扩张", "后期决战"],
            "key_events": ["获得关键机缘", "遭遇强敌打压", "反杀翻盘"],
            "turning_point": "关键实力/信息反转",
            "climax": "与最终反派的决战",
            "low_point": "被背叛或重创的至暗时刻",
            "ending": "达成核心目标，开启新格局",
        },
        # ---- §6.3 人物系统 ----
        "characters": {
            "protagonist": {
                "identity": "出身平凡但潜力非凡", "personality": "坚韧果决、爱憎分明",
                "desire": "变强并掌控命运", "goal": "达成核心目标", "fear": "失去所守护之人",
                "flaw": "偶尔冲动 / 执念", "ability": "成长型核心能力", "action_style": "主动出击、以战养战",
                "growth_path": "弱 → 强 → 巅峰", "arc": "从被动求生到主动掌局",
            },
            "supporting": [
                {"name": "引路人", "role": "导师", "function": "推动主角成长", "relation": "师徒/盟友", "personality": "深沉睿智"},
                {"name": "红颜/挚友", "role": "情感支点", "function": "提供动机与情感锚", "relation": "感情/伙伴", "personality": "坚定忠诚"},
            ],
            "antagonist": {
                "identity": "更高层级的压迫者", "goal": "维持秩序或吞噬资源", "motive": "野心/理念冲突",
                "ability": "阶段性碾压主角", "logic": "步步紧逼、层层设局",
                "conflict": "与主角争夺资源与命运主导权", "ending": "被主角超越并击败",
            },
        },
        # ---- §7 人物关系(含变化追踪)----
        "relations": [
            {"from": "主角", "to": "引路人", "type": "师徒", "changes": ["陌生", "师徒", "并肩"]},
            {"from": "主角", "to": "反派", "type": "敌对", "changes": ["对立", "冲突", "决裂", "决战"]},
            {"from": "主角", "to": "红颜/挚友", "type": "感情", "changes": ["相识", "信任", "生死与共"]},
        ],
        # ---- §8 剧情时间线 ----
        "events": [
            {"name": "开局困境", "chapter": "前 5%", "characters": ["主角"], "type": "铺垫",
             "precondition": "主角处于弱势", "conflict": "生存/尊严受威胁", "result": "触发成长动机",
             "impact_main": "开启主线", "impact_character": "确立目标"},
            {"name": "获得机缘", "chapter": "10%", "characters": ["主角", "引路人"], "type": "转折",
             "precondition": "陷入绝境", "conflict": "机遇与风险并存", "result": "实力/认知跃迁",
             "impact_main": "加速推进", "impact_character": "能力升级"},
            {"name": "强敌打压", "chapter": "40%", "characters": ["主角", "反派"], "type": "冲突",
             "precondition": "主角崭露头角", "conflict": "实力代差", "result": "至暗低谷",
             "impact_main": "制造张力", "impact_character": "淬炼心性"},
            {"name": "反杀翻盘", "chapter": "70%", "characters": ["主角", "反派"], "type": "爽点",
             "precondition": "厚积薄发", "conflict": "正面对决", "result": "扬眉吐气",
             "impact_main": "阶段高潮", "impact_character": "地位跃升"},
        ],
        # ---- §9 冲突系统 ----
        "conflicts": {
            "types": ["人物冲突", "利益冲突", "实力冲突", "价值观冲突"],
            "curve": _seeded_curve(seed + 1, n, 45, 20, rising=True),
            "escalation": "由个人恩怨升级为势力/世界级对抗",
            "resolution": "以实力与智谋正面击破",
        },
        # ---- §10 悬念与伏笔 ----
        "foreshadows": [
            {"content": "主角身世的隐秘", "first_seen": "前期", "surface": "普通出身",
             "truth": "隐藏血脉/来历", "characters": ["主角", "引路人"], "payoff": "中后期",
             "method": "关键人物揭示", "info_gap": "读者与主角均被误导"},
            {"content": "反派的真正目的", "first_seen": "中期", "surface": "争夺资源",
             "truth": "更深的布局", "characters": ["反派"], "payoff": "决战前", "method": "反转揭露",
             "info_gap": "读者先于主角察觉"},
        ],
        # ---- §11 情绪曲线 ----
        "emotion_curve": {
            "process": ["压抑", "积累", "冲突", "爆发", "爽点", "反馈", "新目标"],
            "curve": _seeded_curve(seed + 2, n, 40, 25, rising=True),
            "payoff_points": [
                {"position": "20%", "type": "小逆袭", "intensity": "中", "setup": "前期压抑"},
                {"position": "50%", "type": "打脸", "intensity": "高", "setup": "被轻视"},
                {"position": "80%", "type": "反杀", "intensity": "高", "setup": "至暗低谷"},
            ],
        },
        # ---- §12 节奏曲线 ----
        "rhythm": {
            "chapter_words": "2000-2600 字/章",
            "dialogue_ratio": _seeded_curve(seed + 3, n, 45, 12),
            "info_density": _seeded_curve(seed + 4, n, 65, 10),
            "payoff_density": _seeded_curve(seed + 5, n, 40, 20, rising=True),
            "reversal_freq": _seeded_curve(seed + 6, n, 25, 15, rising=True),
        },
        # ---- §13 文风系统 ----
        "writing": {
            "language": {"avg_sentence": f"约 {int(avg_sent)} 字", "long_short_ratio": "短句为主", "paragraph": "短段落、留白多"},
            "description": {"action": "高", "psychology": "中", "environment": "中", "appearance": "低", "sensory": "中"},
            "narration": {"person": "第三人称", "viewpoint": "单主视角", "driven": "事件驱动"},
            "tone": {"seriousness": "中", "humor": "中", "oppression": "中", "intensity": "高", "literariness": "中", "popularity": "高"},
        },
        "_engine": "mock",
        "_sample_desc": sample_desc,
    }


def _mock_detect(title: str, content: str) -> dict:
    """mock detect: no API key fallback for offline demo."""
    sample = content[:6000] or title
    is_female = any(k in sample for k in ["穿越", "宫斗", "宅斗", "甜宠", "古言", "女主", "闺蜜", "嫁", "夫君"])
    is_xuanhuan = any(k in sample for k in ["修仙", "武道", "玄幻", "灵气", "修炼", "丹药"])
    tag_hits = [t for t in ["爽文", "升级", "热血", "悬疑", "智斗", "甜宠", "逆袭", "快节奏"] if t in sample]
    return {
        "market": "女频" if is_female else "男频",
        "genre": "古言" if is_female and not is_xuanhuan else ("玄幻" if is_xuanhuan else "都市"),
        "style_tags": tag_hits[:4] or (["甜宠", "古言"] if is_female else ["爽文", "升级"]),
        "core_theme": "穿越逆袭成长" if is_female else "成长与逆袭",
        "_engine": "mock",
    }


def detect_novel(title: str, content: str) -> dict:
    """Detect novel market/genre from first 6000 chars; falls back to mock when no API key."""
    api_key = settings_store.get_api_key()
    if not api_key.strip():
        return _mock_detect(title, content)

    model = settings_store.get_model()
    base_url = settings_store.get_base_url()
    sample = content[:6000]
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": DETECT_SCHEMA_HINT},
            {"role": "user", "content": f"小说名：{title}\n\n片段：\n{sample}"},
        ],
        "temperature": 0.1,
        "stream": False,
    }
    headers = {"Authorization": f"Bearer {api_key}"}
    with httpx.Client(timeout=60) as client:
        resp = client.post(f"{base_url}/chat/completions", json=payload, headers=headers)
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"]
    result = _extract_json(text)
    result["_engine"] = model
    return result


def distill_novel(title: str, content: str) -> dict:
    """Distill novel into style profile dict; uses multi-segment sampling; falls back to mock."""
    api_key = settings_store.get_api_key()
    if not api_key.strip():
        return _mock_distill(title, content)

    model = settings_store.get_model()
    base_url = settings_store.get_base_url()
    sample, sample_desc = _sample_content(content, settings.distill_sample_chars)
    user_prompt = f"小说名：{title}\n采样说明：{sample_desc}\n\n小说片段：\n{sample}"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": DISTILL_SCHEMA_HINT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "stream": False,
    }
    headers = {"Authorization": f"Bearer {api_key}"}
    with httpx.Client(timeout=180) as client:
        resp = client.post(
            f"{base_url}/chat/completions",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"]
    result = _extract_json(text)
    result["_engine"] = model
    result["_sample_desc"] = sample_desc
    return result

