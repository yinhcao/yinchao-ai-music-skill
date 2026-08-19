#!/usr/bin/env python3
"""对仓库中的音潮 Skill 做无第三方依赖的离线校验。"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "yinchaoyongxian-music"
SKILL_MD = SKILL_DIR / "SKILL.md"
OPENAI_YAML = SKILL_DIR / "agents" / "openai.yaml"
SCRIPT = SKILL_DIR / "scripts" / "yinchao_music.py"
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?$")


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md 必须以 YAML frontmatter 开头")
    try:
        frontmatter, _ = text[4:].split("\n---\n", 1)
    except ValueError as exc:
        raise ValueError("SKILL.md frontmatter 未正确结束") from exc

    values: dict[str, str] = {}
    for line in frontmatter.splitlines():
        match = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.*?)\s*$", line)
        if match:
            values[match.group(1)] = match.group(2).strip("\"'")
    return values


def validate(expected_version: str | None = None) -> list[str]:
    errors: list[str] = []
    required_files = (SKILL_MD, OPENAI_YAML, SCRIPT)
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

    openai_text = OPENAI_YAML.read_text(encoding="utf-8")
    for field in ("display_name:", "short_description:", "default_prompt:"):
        if field not in openai_text:
            errors.append(f"agents/openai.yaml 缺少 {field.rstrip(':')}")
    if name and f"${name}" not in openai_text:
        errors.append("agents/openai.yaml 的 default_prompt 必须显式引用 Skill 名称")

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
