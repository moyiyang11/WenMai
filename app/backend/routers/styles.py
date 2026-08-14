"""风格中心路由（说明书第 14-16 章）：聚类 -> 稳定性 -> Style Profile。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import schemas
from core.database import get_db
from models import Novel, StyleFeature, StyleProfile
from services import style

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
