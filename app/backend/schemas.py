"""Pydantic 请求/响应模型。"""
from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field


# ---------- Tag ----------
class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    kind: str


# ---------- Novel ----------
class NovelCreate(BaseModel):
    title: str
    author: str = ""
    market: str = "其他"
    genre: str = ""
    novel_type: str = ""
    status: str = "连载"
    summary: str = ""
    selling_point: str = ""
    source: str = "用户导入"
    content: str = ""
    tags: list[str] = Field(default_factory=list)


class NovelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    author: str
    market: str
    genre: str
    novel_type: str
    status: str
    word_count: int
    chapter_count: int
    summary: str
    selling_point: str
    source: str
    distill_status: str
    created_at: dt.datetime
    tags: list[TagOut] = Field(default_factory=list)


class DistillationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    novel_id: int
    model: str
    error: str
    result: dict
    updated_at: dt.datetime


# ---------- Style ----------
class ClusterRequest(BaseModel):
    name: str
    novel_ids: list[int]
    description: str = ""


class StyleFeatureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    dimension: str
    feature: str
    stability: float
    level: str


class StyleProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str
    stability: float
    profile_yaml: str
    created_at: dt.datetime
    features: list[StyleFeatureOut] = Field(default_factory=list)
    novels: list[NovelOut] = Field(default_factory=list)


# ---------- Skill ----------
class SkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    profile_id: int
    name: str
    version: str
    stability: float
    source_count: int
    feature_count: int
    export_path: str
    created_at: dt.datetime


class SkillExportRequest(BaseModel):
    name: str = ""       # 缺省用 profile 名转 slug
    version: str = "v1.0"


# ---------- Settings ----------
class LLMConfigOut(BaseModel):
    configured: bool          # 是否已配置有效 key
    source: str               # db / env / none
    model: str
    base_url: str
    masked_key: str           # 脱敏 key，仅回显


class LLMConfigUpdate(BaseModel):
    api_key: str | None = None   # None=不改, ""=清除
    model: str | None = None
    base_url: str | None = None


class LLMTestResult(BaseModel):
    ok: bool
    message: str


# ---------- Dashboard ----------
class DashboardOut(BaseModel):
    total_novels: int
    distilled: int
    pending: int
    failed: int
    profile_count: int
    skill_count: int
    market_dist: dict[str, int]
    genre_dist: dict[str, int]
    style_dist: dict[str, int]
    recent_novels: list[NovelOut]
    recent_skills: list[SkillOut]
