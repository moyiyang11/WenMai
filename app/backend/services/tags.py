"""标签工具：按名称获取或创建 Tag。"""
from __future__ import annotations

from sqlalchemy.orm import Session

from models import Tag

# 说明书固定的市场/题材枚举，用于给标签归类 kind
MARKET = {"男频", "女频", "其他"}
GENRES = {
    "玄幻", "仙侠", "都市", "历史", "科幻", "悬疑", "灵异", "末世", "游戏",
    "无限流", "古言", "现言", "宫斗", "宅斗", "年代", "武道", "修仙", "商战",
}


def classify_kind(name: str) -> str:
    if name in MARKET:
        return "market"
    if name in GENRES:
        return "genre"
    return "style"


def get_or_create_tags(db: Session, names: list[str]) -> list[Tag]:
    result: list[Tag] = []
    for raw in names:
        name = raw.strip()
        if not name:
            continue
        tag = db.query(Tag).filter(Tag.name == name).first()
        if not tag:
            tag = Tag(name=name, kind=classify_kind(name))
            db.add(tag)
            db.flush()
        result.append(tag)
    return result
