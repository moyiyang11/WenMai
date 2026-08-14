"""首页工作台数据概览（说明书第 24 章）。"""
from __future__ import annotations

from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import schemas
from core.database import get_db
from models import Novel, Skill, StyleProfile, Tag, novel_tags

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=schemas.DashboardOut)
def dashboard(db: Session = Depends(get_db)):
    novels = db.query(Novel).all()
    market_dist = Counter(n.market for n in novels)
    genre_dist = Counter(n.genre for n in novels if n.genre)

    # 风格标签分布
    style_rows = (
        db.query(Tag.name)
        .join(novel_tags, Tag.id == novel_tags.c.tag_id)
        .filter(Tag.kind == "style")
        .all()
    )
    style_dist = Counter(name for (name,) in style_rows)

    return schemas.DashboardOut(
        total_novels=len(novels),
        distilled=sum(1 for n in novels if n.distill_status == "完成"),
        pending=sum(1 for n in novels if n.distill_status in ("待处理", "处理中")),
        failed=sum(1 for n in novels if n.distill_status == "失败"),
        profile_count=db.query(StyleProfile).count(),
        skill_count=db.query(Skill).count(),
        market_dist=dict(market_dist),
        genre_dist=dict(genre_dist),
        style_dist=dict(style_dist.most_common(12)),
        recent_novels=db.query(Novel).order_by(Novel.created_at.desc()).limit(5).all(),
        recent_skills=db.query(Skill).order_by(Skill.created_at.desc()).limit(5).all(),
    )
