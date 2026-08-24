from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DshPluginTests(unittest.TestCase):
    def test_all_distributable_manifests_share_identity_and_version(self) -> None:
        dsh = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        codex = json.loads(
            (ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        skill = (ROOT / "skills" / "yinchao-ai-music" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertEqual("yinchao-ai-music", dsh["name"])
        self.assertEqual(dsh["name"], codex["name"])
        self.assertEqual(dsh["version"], codex["version"])
        self.assertIn(f"  version: {dsh['version']}\n", skill)

    def test_dsh_bundle_has_no_install_time_scripts(self) -> None:
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        scripts = package.get("scripts", {})
        packaged_files = set(package["files"])

        self.assertTrue(
            {"preinstall", "install", "postinstall", "prepare"}.isdisjoint(scripts)
        )
        self.assertNotIn("skills", packaged_files)
        self.assertIn(
            "skills/yinchao-ai-music/scripts/yinchao_music.py", packaged_files
        )
        self.assertEqual(
            "^0.1.0-rc.6 || ^0.1.1-rc.1",
            package["peerDependencies"]["@deepseek-ai/dsh-skill-filesystem"],
        )
        self.assertEqual(
            "./cordis.patch.yml", package["dsh"]["bundle"]["patch"]
        )

    def test_adapter_scans_only_its_bundled_skill_directory(self) -> None:
        entry = (ROOT / "index.mjs").read_text(encoding="utf-8")

        self.assertIn("includeDefaultRoots: false", entry)
        self.assertIn("bundledSkillDir: skillDir", entry)
        self.assertNotIn("customSkillDirs", entry)
        self.assertIn("new URL('./skills', import.meta.url)", entry)
        self.assertIn("providerName: 'yinchao-ai-music'", entry)


if __name__ == "__main__":
    unittest.main()
