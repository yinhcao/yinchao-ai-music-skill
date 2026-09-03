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
        peers = package["peerDependencies"]

        self.assertTrue(
            {"preinstall", "install", "postinstall", "prepare"}.isdisjoint(scripts)
        )
        self.assertNotIn("skills", packaged_files)
        self.assertIn(
            "skills/yinchao-ai-music/scripts/yinchao_music.py", packaged_files
        )
        for dependency in (
            "@deepseek-ai/dsh-credentials",
            "@deepseek-ai/dsh-skill-filesystem",
            "@deepseek-ai/dsh-subprocess",
            "@deepseek-ai/dsh-tools",
        ):
            with self.subTest(dependency=dependency):
                self.assertEqual(
                    "^0.1.0-rc.6 || ^0.1.1-rc.1",
                    peers[dependency],
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

    def test_adapter_resolves_credentials_and_forwards_only_to_music_child(self) -> None:
        entry = (ROOT / "index.mjs").read_text(encoding="utf-8")

        self.assertIn("credentialRef('YINCHAO_API_KEY')", entry)
        self.assertIn("ctx.credentials.resolve(API_KEY_REF)", entry)
        self.assertIn("ctx.subprocess.spawn", entry)
        self.assertIn(
            "argv: [python, SCRIPT_PATH, action, ...argv, '--json']",
            entry,
        )
        self.assertIn("YINCHAO_API_KEY: resolved.value", entry)
        self.assertNotIn("process.env.YINCHAO_API_KEY", entry)
        self.assertNotIn("...process.env", entry)

    def test_adapter_registers_a_bounded_music_only_tool(self) -> None:
        entry = (ROOT / "index.mjs").read_text(encoding="utf-8")

        self.assertIn("name: 'yinchao_music'", entry)
        self.assertIn(
            "enum: ['song', 'instrumental', 'lyrics', 'reference', 'extend', 'status']",
            entry,
        )
        self.assertIn("timeoutMs: TOOL_TIMEOUT_MS", entry)
        self.assertIn("argv.includes('--human')", entry)
        self.assertIn("argv.includes('--json')", entry)
        self.assertIn("value.startsWith('--env-file=')", entry)
        self.assertIn("value.includes(resolved.value)", entry)

    def test_adapter_uses_streaming_safe_generic_call_presentation(self) -> None:
        entry = (ROOT / "index.mjs").read_text(encoding="utf-8")

        # DSH may project tool/call while streamed JSON is still incomplete.
        # Omitting presentCall avoids parsing partial arguments in api-proxy.
        self.assertNotIn("presentCall:", entry)

    def test_skill_prefers_the_dsh_tool_without_exposing_the_key(self) -> None:
        skill = (
            ROOT / "skills" / "yinchao-ai-music" / "SKILL.md"
        ).read_text(encoding="utf-8")

        self.assertIn("如果当前 Agent 提供 `yinchao_music` 工具", skill)
        self.assertIn("不要再用 bash 直接启动 Python", skill)
        self.assertIn(
            "不要传 `--json`、`--human`、`--env-file` 或 API Key",
            skill,
        )


if __name__ == "__main__":
    unittest.main()
