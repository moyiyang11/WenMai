"""ORM 数据模型。

覆盖说明书第 26 章核心实体中 MVP 需要的部分：
Novel / Tag / Distillation / StyleProfile / StyleFeature / Skill。
其余实体（Chapter/Character/Event...）留作第二阶段扩展。
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


# 小说 <-> 标签 多对多
novel_tags = Table(
    "novel_tags",
    Base.metadata,
    Column("novel_id", ForeignKey("novels.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

# 风格 <-> 来源小说 多对多
profile_novels = Table(
    "profile_novels",
    Base.metadata,
    Column("profile_id", ForeignKey("style_profiles.id", ondelete="CASCADE"), primary_key=True),
    Column("novel_id", ForeignKey("novels.id", ondelete="CASCADE"), primary_key=True),
)


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    # kind: market(市场) / genre(题材) / style(风格标签)
    kind: Mapped[str] = mapped_column(String(16), default="style", index=True)

    novels: Mapped[list[Novel]] = relationship(
        secondary=novel_tags, back_populates="tags"
    )


class Novel(Base):
    __tablename__ = "novels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    author: Mapped[str] = mapped_column(String(128), default="")
    market: Mapped[str] = mapped_column(String(16), default="其他")  # 男频/女频/其他
    genre: Mapped[str] = mapped_column(String(64), default="")        # 题材
    novel_type: Mapped[str] = mapped_column(String(64), default="")   # 具体类型
    status: Mapped[str] = mapped_column(String(16), default="连载")   # 连载/完结
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    chapter_count: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[str] = mapped_column(Text, default="")
    selling_point: Mapped[str] = mapped_column(Text, default="")  # 核心卖点
    source: Mapped[str] = mapped_column(String(64), default="用户导入")
    content: Mapped[str] = mapped_column(Text, default="")  # 正文（用于蒸馏采样）

    # 待处理/处理中/完成/失败
    distill_status: Mapped[str] = mapped_column(String(16), default="待处理", index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)

    tags: Mapped[list[Tag]] = relationship(
        secondary=novel_tags, back_populates="novels"
    )
    distillation: Mapped[Distillation | None] = relationship(
        back_populates="novel", uselist=False, cascade="all, delete-orphan"
    )


class Distillation(Base):
    """单本小说的结构化蒸馏结果（JSON 存储在 result 字段）。"""

    __tablename__ = "distillations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    novel_id: Mapped[int] = mapped_column(
        ForeignKey("novels.id", ondelete="CASCADE"), unique=True, index=True
    )
    result: Mapped[str] = mapped_column(Text, default="{}")  # JSON 字符串
    model: Mapped[str] = mapped_column(String(64), default="")
    error: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    novel: Mapped[Novel] = relationship(back_populates="distillation")


class StyleProfile(Base):
    """风格模型 Style Profile：来自多本小说聚类 + 稳定性分析。"""

    __tablename__ = "style_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    stability: Mapped[float] = mapped_column(Float, default=0.0)  # 综合稳定性 0-100
    profile_yaml: Mapped[str] = mapped_column(Text, default="")   # 生成的 Style Profile YAML
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)

    novels: Mapped[list[Novel]] = relationship(secondary=profile_novels)
    features: Mapped[list[StyleFeature]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )
    skills: Mapped[list[Skill]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )


class StyleFeature(Base):
    """风格特征及其稳定度。"""

    __tablename__ = "style_features"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("style_profiles.id", ondelete="CASCADE"), index=True
    )
    dimension: Mapped[str] = mapped_column(String(64), default="")  # 维度：节奏/冲突/文风...
    feature: Mapped[str] = mapped_column(String(128))               # 特征名，如“快节奏”
    stability: Mapped[float] = mapped_column(Float, default=0.0)    # 稳定度 0-100
    # 核心特征/重要特征/辅助特征/偶然特征
    level: Mapped[str] = mapped_column(String(16), default="偶然特征")

    profile: Mapped[StyleProfile] = relationship(back_populates="features")


class Setting(Base):
    """运行时键值配置。用于在网页里保存 DeepSeek API Key 等敏感信息，
    落库在 data/ 目录（已 gitignore），避免写进会被提交到 GitHub 的文件。"""

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class Skill(Base):
    """导出的 Style Skill 记录（含版本管理元数据）。"""

    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("style_profiles.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255), index=True)
    version: Mapped[str] = mapped_column(String(32), default="v1.0")
    stability: Mapped[float] = mapped_column(Float, default=0.0)
    source_count: Mapped[int] = mapped_column(Integer, default=0)  # 来源小说数
    feature_count: Mapped[int] = mapped_column(Integer, default=0)
    export_path: Mapped[str] = mapped_column(String(512), default="")  # zip 路径
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)

    profile: Mapped[StyleProfile] = relationship(back_populates="skills")
