#!/usr/bin/env python3
"""对仓库中的音潮 Skill 做无第三方依赖的离线校验。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "yinchao-ai-music"
SKILL_MD = SKILL_DIR / "SKILL.md"
OPENAI_YAML = SKILL_DIR / "agents" / "openai.yaml"
SCRIPT = SKILL_DIR / "scripts" / "yinchao_music.py"
PLUGIN_MANIFEST = ROOT / ".codex-plugin" / "plugin.json"
REFERENCE_FILES = tuple(
    SKILL_DIR / "references" / name
    for name in ("generation.md", "reference.md", "extension.md", "delivery.md")
)
LOGO = SKILL_DIR / "assets" / "yinchao-logo.png"
DISPLAY_NAME = "音潮 AI 音乐创作"
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?$")


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md 必须以 YAML frontmatter 开头")
    try:
        frontmatter, _ = text[4:].split("\n---\n", 1)
    except ValueError as exc:
        raise ValueError("SKILL.md frontmatter 未正确结束") from exc

    values: dict[str, str] = {}
    in_metadata = False
    for line in frontmatter.splitlines():
        if line == "metadata:":
            in_metadata = True
            continue
        if line and not line.startswith((" ", "\t")):
            in_metadata = False
        pattern = (
            r"^\s{2}([A-Za-z][A-Za-z0-9_-]*):\s*(.*?)\s*$"
            if in_metadata
            else r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.*?)\s*$"
        )
        match = re.match(pattern, line)
        if match:
            values[match.group(1)] = match.group(2).strip("\"'")
    return values


def validate(expected_version: str | None = None) -> list[str]:
    errors: list[str] = []
    required_files = (
        SKILL_MD,
        OPENAI_YAML,
        SCRIPT,
        PLUGIN_MANIFEST,
        LOGO,
        *REFERENCE_FILES,
    )
    for path in required_files:
        if not path.is_file():
            errors.append(f"缺少文件：{path.relative_to(ROOT)}")
    if errors:
        return errors

    skill_text = SKILL_MD.read_text(encoding="utf-8")
    try:
        metadata = parse_frontmatter(skill_text)
    except ValueError as exc:
        return [str(exc)]

    for field in (
        "name",
        "description",
        "slug",
        "displayName",
        "version",
        "summary",
        "license",
    ):
        if not metadata.get(field):
            errors.append(f"SKILL.md frontmatter 缺少 {field}")

    name = metadata.get("name", "")
    if name and SKILL_DIR.name != name:
        errors.append(f"Skill 目录名 {SKILL_DIR.name!r} 必须与 name {name!r} 一致")
    if name and metadata.get("slug") != name:
        errors.append("当前仓库约定 slug 与 name 保持一致")
    if metadata.get("displayName") != DISPLAY_NAME:
        errors.append(f"Skill 展示名必须是 {DISPLAY_NAME!r}")

    version = metadata.get("version", "")
    if version and not SEMVER.fullmatch(version):
        errors.append(f"version 不是有效的语义化版本：{version}")
    if expected_version:
        expected_version = expected_version.removeprefix("v")
        if version != expected_version:
            errors.append(f"Git Tag 版本 {expected_version} 与 SKILL.md 版本 {version} 不一致")

    if metadata.get("license") != "MIT":
        errors.append("SKILL.md 的 license 必须与仓库 LICENSE 保持一致")

    homepage = metadata.get("homepage", "")
    if homepage and "register_channel=skillhub" not in homepage:
        errors.append("SkillHub 包内官网链接必须保留 register_channel=skillhub")

    description = metadata.get("description", "")
    for phrase in (
        "AI 歌曲",
        "BGM",
        "歌词谱曲",
        "参考音频",
        "歌曲续写",
        "AI music generation",
        "lyrics-to-song",
    ):
        if phrase not in description:
            errors.append(f"description 缺少检索关键词：{phrase}")

    openai_text = OPENAI_YAML.read_text(encoding="utf-8")
    for field in ("display_name:", "short_description:", "default_prompt:"):
        if field not in openai_text:
            errors.append(f"agents/openai.yaml 缺少 {field.rstrip(':')}")
    if name and f"${name}" not in openai_text:
        errors.append("agents/openai.yaml 的 default_prompt 必须显式引用 Skill 名称")
    if f'display_name: "{DISPLAY_NAME}"' not in openai_text:
        errors.append("agents/openai.yaml 的展示名与 Skill 不一致")
    for field in ("icon_small:", "icon_large:", "brand_color:"):
        if field not in openai_text:
            errors.append(f"agents/openai.yaml 缺少 {field.rstrip(':')}")

    try:
        plugin = json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"无法解析 .codex-plugin/plugin.json：{exc}")
    else:
        if plugin.get("name") != name:
            errors.append("Plugin name 必须与 Skill name 保持一致")
        if plugin.get("version") != version:
            errors.append("Plugin version 必须与 Skill version 保持一致")
        if plugin.get("interface", {}).get("displayName") != DISPLAY_NAME:
            errors.append("Plugin 展示名与 Skill 不一致")
        if plugin.get("skills") != "./skills/":
            errors.append("Plugin skills 必须指向 ./skills/")

    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    if "__pycache__/" not in gitignore or "*.py[cod]" not in gitignore:
        errors.append(".gitignore 必须排除 Python 缓存文件")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-version", help="校验 Git Tag 与 Skill 版本一致")
    args = parser.parse_args()

    errors = validate(args.expected_version)
    if errors:
        for error in errors:
            print(f"[ERROR] {error}", file=sys.stderr)
        return 1
    print("[OK] Skill 结构、元数据和版本校验通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
