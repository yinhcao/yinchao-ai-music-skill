from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "stage_skill.py"
SPEC = importlib.util.spec_from_file_location("stage_skill", MODULE_PATH)
assert SPEC and SPEC.loader
stage_skill = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = stage_skill
SPEC.loader.exec_module(stage_skill)


class StageSkillTests(unittest.TestCase):
    def test_each_distributor_gets_only_its_register_channel(self) -> None:
        for channel in ("skillhub", "clawhub"):
            with self.subTest(channel=channel), tempfile.TemporaryDirectory() as temp:
                output = Path(temp) / "yinchao-ai-music"
                staged = stage_skill.stage_skill(channel, output)

                self.assertEqual(6, len(staged))
                text = "\n".join(
                    path.read_text(encoding="utf-8")
                    for path in staged
                    if path.suffix == ".md"
                )
                self.assertEqual(4, text.count(f"register_channel={channel}"))
                for other in set(stage_skill.SUPPORTED_CHANNELS) - {channel}:
                    self.assertNotIn(f"register_channel={other}", text)

    def test_package_contains_only_the_allowlisted_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "yinchao-ai-music"
            staged = stage_skill.stage_skill("clawhub", output)

            actual = {path.relative_to(output) for path in staged}
            self.assertEqual(set(stage_skill.PACKAGE_FILES), actual)

    def test_non_empty_output_directory_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "yinchao-ai-music"
            output.mkdir()
            (output / "existing.txt").write_text("keep", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "输出目录必须为空"):
                stage_skill.stage_skill("skillhub", output)


if __name__ == "__main__":
    unittest.main()
