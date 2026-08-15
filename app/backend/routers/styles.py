"""风格中心路由（说明书第 14-16 章）：聚类 -> 稳定性 -> Style Profile。"""
from __future__ import annotations

import json as _json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

import schemas
from core.database import get_db
from models import Novel, StyleFeature, StyleProfile
from services import llm, style

router = APIRouter(prefix="/api/styles", tags=["styles"])


@router.get("", response_model=list[schemas.StyleProfileOut])
def list_profiles(db: Session = Depends(get_db)):
    return db.query(StyleProfile).order_by(StyleProfile.created_at.desc()).all()


@router.get("/{profile_id}", response_model=schemas.StyleProfileOut)
def get_profile(profile_id: int, db: Session = Depends(get_db)):
    profile = db.get(StyleProfile, profile_id)
    if not profile:
        raise HTTPException(404, "风格不存在")
    return profile


@router.post("/cluster", response_model=schemas.StyleProfileOut)
def cluster(payload: schemas.ClusterRequest, db: Session = Depends(get_db)):
    """选择多本已蒸馏小说，提取共同特征并生成 Style Profile。"""
    novels = db.query(Novel).filter(Novel.id.in_(payload.novel_ids)).all()
    if len(novels) < 2:
        raise HTTPException(400, "至少选择 2 本小说进行聚类")

    distillations = []
    missing = []
    for n in novels:
        if n.distillation and n.distillation.result:
            distillations.append(style.load_distillation(n.distillation.result))
        else:
            missing.append(n.title)
    if missing:
        raise HTTPException(400, f"以下小说尚未蒸馏：{', '.join(missing)}")

    analysis = style.analyze(distillations)
    profile_yaml = style.to_yaml(payload.name, analysis["profile"])

    profile = StyleProfile(
        name=payload.name,
        description=payload.description,
        stability=analysis["stability"],
        profile_yaml=profile_yaml,
    )
    profile.novels = novels
    profile.features = [
        StyleFeature(
            dimension=f["dimension"],
            feature=f["feature"],
            stability=f["stability"],
            level=f["level"],
        )
        for f in analysis["features"]
    ]
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.delete("/{profile_id}")
def delete_profile(profile_id: int, db: Session = Depends(get_db)):
    profile = db.get(StyleProfile, profile_id)
    if not profile:
        raise HTTPException(404, "风格不存在")
    db.delete(profile)
    db.commit()
    return {"ok": True}


class _SuggestNameReq(BaseModel):
    novel_ids: list[int]


@router.post("/suggest-name")
def suggest_name(payload: _SuggestNameReq, db: Session = Depends(get_db)):
    """根据已蒸馏小说特征，AI 生成 3 个推荐风格名称。"""
    novels = db.query(Novel).filter(Novel.id.in_(payload.novel_ids)).all()

    markets, genres, all_tags, paces, conflicts, payoffs = [], [], [], [], [], []
    for n in novels:
        if n.distillation and n.distillation.result:
            try:
                r = _json.loads(n.distillation.result)
                if r.get("basic", {}).get("market"):
                    markets.append(r["basic"]["market"])
                if r.get("basic", {}).get("genre"):
                    genres.append(r["basic"]["genre"])
                all_tags.extend(r.get("style_tags", []))
                if r.get("narrative", {}).get("pace"):
                    paces.append(r["narrative"]["pace"])
                if r.get("plot", {}).get("conflict_density"):
                    conflicts.append(r["plot"]["conflict_density"])
                payoffs.extend(r.get("emotion", {}).get("main_payoffs", []))
            except Exception:  # noqa: BLE001
                pass

    def most_common(lst: list) -> str:
        return max(set(lst), key=lst.count) if lst else ""

    seen: set[str] = set()
    unique_tags: list[str] = []
    for t in all_tags:
        if t not in seen:
            seen.add(t)
            unique_tags.append(t)

    summary = {
        "market": most_common(markets),
        "genre": most_common(genres),
        "style_tags": unique_tags[:6],
        "pace": most_common(paces),
        "conflict_density": most_common(conflicts),
        "main_payoffs": list(dict.fromkeys(payoffs))[:4],
    }
    suggestions = llm.suggest_profile_name(summary)
    return {"suggestions": suggestions}


@router.post("/combine", response_model=schemas.StyleProfileOut)
def combine(payload: schemas.CombineRequest, db: Session = Depends(get_db)):
    """风格组合（说明书 §20）：把多个已有 Style Profile 组合成新风格。

    重新计算共同规则 / 冲突规则 / 优先级，生成新的 Style Profile。
    """
    import yaml

    ids = list(dict.fromkeys(payload.profile_ids))  # 去重保序
    if len(ids) < 2:
        raise HTTPException(400, "至少选择 2 个风格进行组合")

    profiles = db.query(StyleProfile).filter(StyleProfile.id.in_(ids)).all()
    if len(profiles) < 2:
        raise HTTPException(400, "有效风格不足 2 个")

    sources = [
        {
            "name": p.name,
            "weight": len(p.novels) or 1,
            "features": [
                {"dimension": f.dimension, "feature": f.feature, "stability": f.stability, "level": f.level}
                for f in p.features
            ],
            "profile": yaml.safe_load(p.profile_yaml) or {},
        }
        for p in profiles
    ]

    result = style.combine(sources)
    profile_yaml = style.to_yaml(payload.name, result["profile"])

    source_names = "、".join(p.name for p in profiles)
    desc = payload.description or f"组合自：{source_names}"

    new_profile = StyleProfile(
        name=payload.name,
        description=desc,
        stability=result["stability"],
        profile_yaml=profile_yaml,
    )
    # 来源小说 = 各源风格来源小说的并集（去重）
    novel_union: dict[int, Novel] = {}
    for p in profiles:
        for n in p.novels:
            novel_union[n.id] = n
    new_profile.novels = list(novel_union.values())
    new_profile.features = [
        StyleFeature(
            dimension=f["dimension"],
            feature=f["feature"],
            stability=f["stability"],
            level=f["level"],
            origin=f.get("origin", ""),
        )
        for f in result["features"]
    ]
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    return new_profile
