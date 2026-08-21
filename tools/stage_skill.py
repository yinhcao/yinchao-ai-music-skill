#!/usr/bin/env python3
"""生成带指定注册渠道的确定性 Skill 发布包。"""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "skills" / "yinchao-ai-music"
CANONICAL_CHANNEL = "github"
SUPPORTED_CHANNELS = ("github", "skillhub", "clawhub")
REGISTER_CHANNEL = re.compile(r"register_channel=([a-z][a-z0-9_-]*)")
PACKAGE_FILES = (
    Path("SKILL.md"),
    Path("references/delivery.md"),
    Path("references/extension.md"),
    Path("references/generation.md"),
    Path("references/reference.md"),
    Path("scripts/yinchao_music.py"),
)


def _transform_markdown(source: Path, channel: str) -> str:
    text = source.read_text(encoding="utf-8")
    channels = REGISTER_CHANNEL.findall(text)
    unexpected = sorted(set(channels) - {CANONICAL_CHANNEL})
    if unexpected:
        values = ", ".join(unexpected)
        raise ValueError(f"{source} 包含非 canonical register_channel：{values}")
    return REGISTER_CHANNEL.sub(f"register_channel={channel}", text)


def stage_skill(channel: str, output_dir: Path) -> tuple[Path, ...]:
    if channel not in SUPPORTED_CHANNELS:
        raise ValueError(f"不支持的 register_channel：{channel}")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError(f"输出目录必须为空：{output_dir}")

    staged: list[Path] = []
    attribution_count = 0
    for relative_path in PACKAGE_FILES:
        source = SOURCE_DIR / relative_path
        if not source.is_file():
            raise FileNotFoundError(f"缺少发布文件：{source}")

        destination = output_dir / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.suffix.lower() == ".md":
            transformed = _transform_markdown(source, channel)
            attribution_count += len(REGISTER_CHANNEL.findall(transformed))
            destination.write_text(transformed, encoding="utf-8")
        else:
            shutil.copy2(source, destination)
        staged.append(destination)

    if attribution_count == 0:
        raise ValueError("发布包中没有 register_channel 归因链接")

    staged_channels: set[str] = set()
    for path in staged:
        if path.suffix.lower() == ".md":
            staged_channels.update(
                REGISTER_CHANNEL.findall(path.read_text(encoding="utf-8"))
            )
    if staged_channels != {channel}:
        values = ", ".join(sorted(staged_channels)) or "<empty>"
        raise ValueError(f"发布包渠道校验失败，实际为：{values}")

    return tuple(staged)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel", choices=SUPPORTED_CHANNELS, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    staged = stage_skill(args.channel, args.output.resolve())
    print(
        f"[OK] 已生成 {len(staged)} 个文件，"
        f"register_channel={args.channel}，输出：{args.output.resolve()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
