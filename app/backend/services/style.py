"""风格聚类与稳定性分析（说明书第 14-16 章）。

输入多本已蒸馏小说的结构化特征，统计每个特征在样本中的出现率作为“稳定度”，
按阈值分级为 核心/重要/辅助/偶然 特征，并生成 Style Profile YAML。
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict

import yaml

# 参与稳定性统计的“分类型”特征维度：dimension -> (蒸馏字段路径)
CATEGORICAL_FIELDS = {
    "叙事-视角": ("narrative", "perspective"),
    "叙事-驱动": ("narrative", "drive"),
    "叙事-节奏": ("narrative", "pace"),
    "剧情-冲突密度": ("plot", "conflict_density"),
    "剧情-反转密度": ("plot", "reversal_density"),
    "剧情-推进": ("plot", "progression"),
    "情绪-爽点频率": ("emotion", "payoff_frequency"),
    "情绪-高潮频率": ("emotion", "climax_frequency"),
    "人物-主角能动性": ("character", "protagonist_agency"),
    "人物-主角成长": ("character", "protagonist_growth"),
    "语言-句长": ("language", "sentence_length"),
    "语言-对话密度": ("language", "dialogue_density"),
    "语言-描写密度": ("language", "description_density"),
    "语言-信息密度": ("language", "information_density"),
}

# 列表型特征（标签/爽点），按标签出现率统计
LIST_FIELDS = {
    "风格标签": ("style_tags",),
    "情绪-爽点": ("emotion", "main_payoffs"),
}


def _get(d: dict, path: tuple[str, ...]):
    cur = d
    for key in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def _level(stability: float) -> str:
    if stability >= 90:
        return "核心特征"
    if stability >= 70:
        return "重要特征"
    if stability >= 50:
        return "辅助特征"
    return "偶然特征"


def analyze(distillations: list[dict]) -> dict:
    """返回 {features: [...], stability: float, profile: dict}。

    distillations: 每本小说的结构化蒸馏 dict 列表。
    """
    n = len(distillations)
    features: list[dict] = []
    if n == 0:
        return {"features": [], "stability": 0.0, "profile": {}}

    # 分类型：取每个维度的众数作为该风格的取值，稳定度=众数占比
    profile_categorical: dict[str, dict[str, str]] = defaultdict(dict)
    for dim, path in CATEGORICAL_FIELDS.items():
        values = [_get(d, path) for d in distillations]
        values = [v for v in values if v]
        if not values:
            continue
        value, count = Counter(values).most_common(1)[0]
        stability = round(count / n * 100, 1)
        features.append(
            {"dimension": dim, "feature": str(value), "stability": stability, "level": _level(stability)}
        )
        section = path[0]
        profile_categorical[section][path[-1]] = value

    # 列表型：每个标签的出现率
    profile_tags: list[str] = []
    for dim, path in LIST_FIELDS.items():
        tag_counter: Counter = Counter()
        for d in distillations:
            vals = _get(d, path) or []
            if isinstance(vals, list):
                tag_counter.update({str(x) for x in vals})
        for tag, count in tag_counter.most_common():
            stability = round(count / n * 100, 1)
            features.append(
                {"dimension": dim, "feature": tag, "stability": stability, "level": _level(stability)}
            )
            if dim == "风格标签" and stability >= 50:
                profile_tags.append(tag)

    # 综合稳定性：核心+重要特征占全部特征的比例，映射到 0-100
    strong = sum(1 for f in features if f["stability"] >= 70)
    overall = round(strong / len(features) * 100, 1) if features else 0.0

    profile = _build_profile(distillations, profile_categorical, profile_tags)
    return {"features": features, "stability": overall, "profile": profile}


def _build_profile(distillations, categorical, tags) -> dict:
    markets = Counter(_get(d, ("basic", "market")) for d in distillations if _get(d, ("basic", "market")))
    genres = Counter(_get(d, ("basic", "genre")) for d in distillations if _get(d, ("basic", "genre")))
    profile = {
        "market": [m for m, _ in markets.most_common()],
        "genre": [g for g, _ in genres.most_common(3)],
        "narrative": categorical.get("narrative", {}),
        "plot": categorical.get("plot", {}),
        "emotion": categorical.get("emotion", {}),
        "character": categorical.get("character", {}),
        "language": categorical.get("language", {}),
        "style_tags": tags,
    }
    return profile


def to_yaml(name: str, profile: dict) -> str:
    doc = {"name": name, **profile}
    return yaml.safe_dump(doc, allow_unicode=True, sort_keys=False)


def load_distillation(dist_result_json: str) -> dict:
    try:
        return json.loads(dist_result_json)
    except (json.JSONDecodeError, TypeError):
        return {}
