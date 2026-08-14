"""小说库 + 单本蒸馏路由（说明书第 5、6、27 章）。"""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

import schemas
from core.database import get_db
from models import Distillation, Novel
from services import llm
from services.tags import get_or_create_tags

router = APIRouter(prefix="/api/novels", tags=["novels"])


@router.get("", response_model=list[schemas.NovelOut])
def list_novels(db: Session = Depends(get_db)):
    return db.query(Novel).order_by(Novel.created_at.desc()).all()


@router.post("", response_model=schemas.NovelOut)
def create_novel(payload: schemas.NovelCreate, db: Session = Depends(get_db)):
    novel = Novel(
        **payload.model_dump(exclude={"tags"}),
        word_count=len(payload.content),
    )
    novel.tags = get_or_create_tags(db, payload.tags)
    db.add(novel)
    db.commit()
    db.refresh(novel)
    return novel


@router.post("/upload", response_model=schemas.NovelOut)
async def upload_novel(
    file: UploadFile = File(...),
    title: str = Form(""),
    author: str = Form(""),
    market: str = Form("其他"),
    genre: str = Form(""),
    tags: str = Form(""),
    db: Session = Depends(get_db),
):
    """上传 txt 小说文件导入。tags 为逗号分隔字符串。"""
    raw = await file.read()
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        content = raw.decode("gbk", errors="ignore")

    novel = Novel(
        title=title or (file.filename or "未命名").rsplit(".", 1)[0],
        author=author,
        market=market,
        genre=genre,
        content=content,
        word_count=len(content),
        chapter_count=content.count("第") // 2,  # 粗略估计
        source="用户导入",
    )
    novel.tags = get_or_create_tags(db, [t for t in tags.split(",") if t.strip()])
    db.add(novel)
    db.commit()
    db.refresh(novel)
    return novel


@router.get("/{novel_id}", response_model=schemas.NovelOut)
def get_novel(novel_id: int, db: Session = Depends(get_db)):
    novel = db.get(Novel, novel_id)
    if not novel:
        raise HTTPException(404, "小说不存在")
    return novel


@router.delete("/{novel_id}")
def delete_novel(novel_id: int, db: Session = Depends(get_db)):
    novel = db.get(Novel, novel_id)
    if not novel:
        raise HTTPException(404, "小说不存在")
    db.delete(novel)
    db.commit()
    return {"ok": True}


@router.post("/{novel_id}/distill", response_model=schemas.DistillationOut)
def distill(novel_id: int, db: Session = Depends(get_db)):
    """对单本小说执行 AI 蒸馏，保存结构化结果。"""
    novel = db.get(Novel, novel_id)
    if not novel:
        raise HTTPException(404, "小说不存在")

    novel.distill_status = "处理中"
    db.commit()
    try:
        result = llm.distill_novel(novel.title, novel.content)
        engine = result.get("_engine", "")
        dist = novel.distillation or Distillation(novel_id=novel.id)
        dist.result = json.dumps(result, ensure_ascii=False)
        dist.model = engine
        dist.error = ""
        novel.distillation = dist
        novel.distill_status = "完成"
        db.add(dist)
        db.commit()
        db.refresh(dist)
    except Exception as exc:  # noqa: BLE001
        novel.distill_status = "失败"
        dist = novel.distillation or Distillation(novel_id=novel.id)
        dist.error = str(exc)
        novel.distillation = dist
        db.add(dist)
        db.commit()
        raise HTTPException(500, f"蒸馏失败: {exc}") from exc

    return schemas.DistillationOut(
        id=dist.id,
        novel_id=dist.novel_id,
        model=dist.model,
        error=dist.error,
        result=result,
        updated_at=dist.updated_at,
    )


@router.get("/{novel_id}/distillation", response_model=schemas.DistillationOut)
def get_distillation(novel_id: int, db: Session = Depends(get_db)):
    novel = db.get(Novel, novel_id)
    if not novel or not novel.distillation:
        raise HTTPException(404, "尚未蒸馏")
    dist = novel.distillation
    return schemas.DistillationOut(
        id=dist.id,
        novel_id=dist.novel_id,
        model=dist.model,
        error=dist.error,
        result=json.loads(dist.result or "{}"),
        updated_at=dist.updated_at,
    )
