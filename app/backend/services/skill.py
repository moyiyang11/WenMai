"""Style Skill 导出（说明书第 17-21 章）。

将 StyleProfile 打包为符合建议结构的 Skill 目录并压缩成 zip：
SKILL.md / style.yaml / rules.md / plot.md / character.md /
rhythm.md / dialogue.md / language.md / examples.md
"""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

import yaml

from core.config import BASE_DIR

EXPORT_DIR = BASE_DIR / "data" / "exports"


def _rules_md(name: str, profile: dict, features: list[dict]) -> str:
    core = [f for f in features if f["level"] == "核心特征"]
    important = [f for f in features if f["level"] == "重要特征"]
    lines = [f"# {name} — 核心规则\n", "## 核心特征（稳定度 ≥ 90%，必须遵守）\n"]
    lines += [f"- **{f['dimension']}**：{f['feature']}（{f['stability']}%）" for f in core] or ["- （无）"]
    lines.append("\n## 重要特征（70%~89%，强烈建议）\n")
    lines += [f"- **{f['dimension']}**：{f['feature']}（{f['stability']}%）" for f in important] or ["- （无）"]
    lines.append("\n## 禁止事项\n")
    lines += [
        "- 禁止大段复制原文或复述具体剧情。",
        "- 禁止模仿特定作者身份。",
        "- 本 Skill 只描述可迁移的风格规律，不生成正文。",
    ]
    return "\n".join(lines) + "\n"


def _section_md(title: str, data: dict) -> str:
    body = yaml.safe_dump(data or {}, allow_unicode=True, sort_keys=False)
    return f"# {title}\n\n```yaml\n{body}```\n"


def _skill_md(name: str, version: str, profile: dict, features: list[dict], source_count: int) -> str:
    core = [f["feature"] for f in features if f["level"] == "核心特征"]
    tags = "、".join(profile.get("style_tags", [])) or "—"
    return f"""# {name}

**版本：** {version}
**类型：** Style Skill（风格知识与分析结果的可执行封装）
**来源：** {source_count} 本小说蒸馏聚类

## 风格定位

{tags}

## 使用场景

在进行同类网文创作/续写时，作为“风格约束层”加载，指导 AI 保持一致的
叙事节奏、冲突结构、爽点机制与语言特征。**本 Skill 不负责生成正文。**

## 核心规则（摘要）

{chr(10).join(f"- {c}" for c in core) or "- （见 rules.md）"}

## 调用方式

加载本目录，优先读取 `style.yaml` 获取参数，再按 `rules.md` 约束输出。

## 规则文件

- `style.yaml` — 结构化风格参数
- `rules.md` — 核心规则与禁止事项
- `plot.md` / `character.md` / `rhythm.md` / `dialogue.md` / `language.md` — 分维度机制
- `examples.md` — 分析示例
"""


def build_skill_files(
    name: str, version: str, profile: dict, features: list[dict], source_count: int
) -> dict[str, str]:
    """返回 {相对路径: 文件内容}。"""
    style_yaml = yaml.safe_dump({"name": name, **profile}, allow_unicode=True, sort_keys=False)
    examples = "# 分析示例\n\n" + "\n".join(
        f"- **{f['dimension']}** → {f['feature']}（稳定度 {f['stability']}%，{f['level']}）"
        for f in sorted(features, key=lambda x: -x["stability"])
    ) + "\n"
    return {
        "SKILL.md": _skill_md(name, version, profile, features, source_count),
        "style.yaml": style_yaml,
        "rules.md": _rules_md(name, profile, features),
        "plot.md": _section_md("剧情机制", profile.get("plot", {})),
        "character.md": _section_md("人物机制", profile.get("character", {})),
        "rhythm.md": _section_md("节奏机制", {**profile.get("narrative", {}), **profile.get("emotion", {})}),
        "dialogue.md": _section_md("对话特征", {"dialogue_density": profile.get("language", {}).get("dialogue_density")}),
        "language.md": _section_md("语言特征", profile.get("language", {})),
        "examples.md": examples,
    }


def export_zip(slug: str, version: str, files: dict[str, str]) -> str:
    """写出 zip，返回绝对路径。"""
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = EXPORT_DIR / f"{slug}-{version}.zip"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel, content in files.items():
            zf.writestr(f"{slug}/{rel}", content)
    zip_path.write_bytes(buf.getvalue())
    return str(zip_path)
