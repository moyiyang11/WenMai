"""Skill 导出路由（说明书第 17-21 章）。"""
from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

import schemas
from core.database import get_db
from models import Skill, StyleProfile
from services import skill as skill_svc
from services import style as style_svc


router = APIRouter(prefix="/api/skills", tags=["skills"])


def _slug(name: str) -> str:
    s = re.sub(r"[^\w一-鿿-]+", "-", name).strip("-")
    return s or "style-skill"


@router.get("", response_model=list[schemas.SkillOut])
def list_skills(db: Session = Depends(get_db)):
    return db.query(Skill).order_by(Skill.created_at.desc()).all()


@router.post("/from-profile/{profile_id}", response_model=schemas.SkillOut)
def export_skill(
    profile_id: int, payload: schemas.SkillExportRequest, db: Session = Depends(get_db)
):
    profile = db.get(StyleProfile, profile_id)
    if not profile:
        raise HTTPException(404, "风格不存在")

    import yaml

    profile_dict = yaml.safe_load(profile.profile_yaml) or {}
    profile_dict.pop("name", None)
    features = [
        {"dimension": f.dimension, "feature": f.feature, "stability": f.stability, "level": f.level}
        for f in profile.features
    ]
    name = payload.name or profile.name
    slug = _slug(name)

    files = skill_svc.build_skill_files(
        name=name,
        version=payload.version,
        profile=profile_dict,
        features=features,
        source_count=len(profile.novels),
    )
    zip_path = skill_svc.export_zip(slug, payload.version, files)

    skill = Skill(
        profile_id=profile.id,
        name=name,
        version=payload.version,
        stability=profile.stability,
        source_count=len(profile.novels),
        feature_count=len(features),
        export_path=zip_path,
    )
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


@router.get("/{skill_id}/preview")
def preview_skill(skill_id: int, db: Session = Depends(get_db)):
    """返回 SKILL.md 与 style.yaml 文本，供前端预览（说明书 Skill 预览）。"""
    skill = db.get(Skill, skill_id)
    if not skill:
        raise HTTPException(404, "Skill 不存在")
    profile = skill.profile
    import yaml

    profile_dict = yaml.safe_load(profile.profile_yaml) or {}
    profile_dict.pop("name", None)
    features = [
        {"dimension": f.dimension, "feature": f.feature, "stability": f.stability, "level": f.level}
        for f in profile.features
    ]
    files = skill_svc.build_skill_files(
        skill.name, skill.version, profile_dict, features, skill.source_count
    )
    return {"files": files}


@router.get("/{skill_id}/download")
def download_skill(skill_id: int, db: Session = Depends(get_db)):
    skill = db.get(Skill, skill_id)
    if not skill or not skill.export_path:
        raise HTTPException(404, "Skill 包不存在")
    from pathlib import Path

    path = Path(skill.export_path)
    if not path.exists():
        raise HTTPException(404, "Skill 文件已丢失，请重新导出")
    return FileResponse(path, filename=path.name, media_type="application/zip")


@router.delete("/{skill_id}")
def delete_skill(skill_id: int, db: Session = Depends(get_db)):
    skill = db.get(Skill, skill_id)
    if not skill:
        raise HTTPException(404, "Skill 不存在")
    db.delete(skill)
    db.commit()
    return {"ok": True}
