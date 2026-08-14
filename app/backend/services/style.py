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


# ---------- 风格组合（说明书第 20 章）----------
# 多个 Style Profile 组合为新风格：重新计算共同规则、冲突规则、优先级。

def combine(sources: list[dict]) -> dict:
    """组合多个已有风格。

    sources: 每个元素为 {"name": str, "weight": int(来源小说数，作权重),
                         "features": [{dimension, feature, stability, level}, ...],
                         "profile": dict(该风格的 profile YAML 解析结果)}。

    返回 {features, stability, profile, conflicts}：
      - features：合并后的特征列表，含 origin 字段（共同/独有/冲突-采纳/冲突-弃用）
      - conflicts：同一维度取值不一致的冲突记录（保留胜出与被弃用取值）
    """
    k = len(sources)
    if k < 2:
        return {"features": [], "stability": 0.0, "profile": {}, "conflicts": []}

    # 按维度归集各来源的取值（分类型维度：一个来源在一个维度上只有一个取值）
    by_dim: dict[str, list[dict]] = defaultdict(list)
    list_dims = set(LIST_FIELDS)  # 列表型维度（风格标签/爽点）走并集，不算冲突
    for src in sources:
        weight = max(int(src.get("weight") or 1), 1)
        for f in src.get("features", []):
            by_dim[f["dimension"]].append({**f, "_src": src.get("name", ""), "_w": weight})

    features: list[dict] = []
    conflicts: list[dict] = []

    for dim, items in by_dim.items():
        if dim in list_dims:
            # 列表型：同一 feature 跨来源出现率越高越稳定
            groups: dict[str, list[dict]] = defaultdict(list)
            for it in items:
                groups[it["feature"]].append(it)
            for feat, grp in groups.items():
                cover = len({g["_src"] for g in grp})
                stability = round(_wavg([g["stability"] for g in grp], [g["_w"] for g in grp]), 1)
                origin = "共同" if cover >= 2 else "独有"
                features.append(
                    {"dimension": dim, "feature": feat, "stability": stability,
                     "level": _level(stability), "origin": origin}
                )
            continue

        # 分类型：同一维度可能出现不同取值 -> 冲突
        groups = defaultdict(list)
        for it in items:
            groups[it["feature"]].append(it)

        if len(groups) == 1:
            # 所有来源取值一致 = 共同规则
            feat, grp = next(iter(groups.items()))
            cover = len({g["_src"] for g in grp})
            stability = round(_wavg([g["stability"] for g in grp], [g["_w"] for g in grp]), 1)
            features.append(
                {"dimension": dim, "feature": feat, "stability": stability,
                 "level": _level(stability), "origin": "共同" if cover >= 2 else "独有"}
            )
        else:
            # 冲突：按加权稳定度排序，最高者胜出（优先级最高）
            ranked = sorted(
                (
                    {
                        "feature": feat,
                        "stability": round(_wavg([g["stability"] for g in grp], [g["_w"] for g in grp]), 1),
                        "srcs": sorted({g["_src"] for g in grp}),
                    }
                    for feat, grp in groups.items()
                ),
                key=lambda x: -x["stability"],
            )
            winner = ranked[0]
            losers = ranked[1:]
            # 冲突会拉低胜出特征的可信度：乘以其在候选中的稳定度占比
            total = sum(r["stability"] for r in ranked) or 1
            adj = round(winner["stability"] * winner["stability"] / total, 1)
            features.append(
                {"dimension": dim, "feature": winner["feature"], "stability": adj,
                 "level": _level(adj), "origin": "冲突-采纳"}
            )
            for lo in losers:
                features.append(
                    {"dimension": dim, "feature": lo["feature"], "stability": lo["stability"],
                     "level": _level(lo["stability"]), "origin": "冲突-弃用"}
                )
            conflicts.append(
                {
                    "dimension": dim,
                    "adopted": winner["feature"],
                    "adopted_srcs": winner["srcs"],
                    "dropped": [{"feature": lo["feature"], "srcs": lo["srcs"]} for lo in losers],
                }
            )

    # 综合稳定性：被采纳（共同/独有/冲突-采纳）特征中强特征占比
    adopted = [f for f in features if f["origin"] != "冲突-弃用"]
    strong = sum(1 for f in adopted if f["stability"] >= 70)
    overall = round(strong / len(adopted) * 100, 1) if adopted else 0.0

    profile = _combine_profile(sources, features)
    return {"features": features, "stability": overall, "profile": profile, "conflicts": conflicts}


def _wavg(values: list[float], weights: list[int]) -> float:
    tw = sum(weights) or 1
    return sum(v * w for v, w in zip(values, weights)) / tw


def _combine_profile(sources: list[dict], features: list[dict]) -> dict:
    """从被采纳的特征反推组合后的 profile dict（结构与单风格 profile 一致）。"""
    # 维度名 -> (profile section, key)，与 CATEGORICAL_FIELDS 对应
    dim_to_path = {dim: path for dim, path in CATEGORICAL_FIELDS.items()}

    sections: dict[str, dict] = defaultdict(dict)
    for f in features:
        if f["origin"] == "冲突-弃用":
            continue
        path = dim_to_path.get(f["dimension"])
        if path:
            sections[path[0]][path[-1]] = f["feature"]

    # market / genre / style_tags 取各来源并集
    markets, genres, tags = [], [], []
    for src in sources:
        p = src.get("profile", {})
        for m in p.get("market", []) or []:
            if m not in markets:
                markets.append(m)
        for g in p.get("genre", []) or []:
            if g not in genres:
                genres.append(g)
        for t in p.get("style_tags", []) or []:
            if t not in tags:
                tags.append(t)

    return {
        "market": markets,
        "genre": genres,
        "narrative": sections.get("narrative", {}),
        "plot": sections.get("plot", {}),
        "emotion": sections.get("emotion", {}),
        "character": sections.get("character", {}),
        "language": sections.get("language", {}),
        "style_tags": tags,
        "combined_from": [s.get("name", "") for s in sources],
    }


def load_distillation(dist_result_json: str) -> dict:
    try:
        return json.loads(dist_result_json)
    except (json.JSONDecodeError, TypeError):
        return {}
