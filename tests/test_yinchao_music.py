from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "yinchao-ai-music"
    / "scripts"
    / "yinchao_music.py"
)
SPEC = importlib.util.spec_from_file_location("yinchao_music", MODULE_PATH)
assert SPEC and SPEC.loader
yinchao_music = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = yinchao_music
SPEC.loader.exec_module(yinchao_music)


class CredentialTests(unittest.TestCase):
    def test_process_environment_has_highest_priority(self) -> None:
        result = yinchao_music._resolve_api_key(
            env_file="/path/that/does/not/exist",
            environ={
                "YINCHAO_API_KEY": "  env-secret  ",
                "YINCHAO_API_KEY_FILE": "/also/missing",
            },
        )

        self.assertEqual("env-secret", result)

    def test_raw_api_key_file_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            key_file = Path(temp_dir) / "yinchao.key"
            key_file.write_text("file-secret\n", encoding="utf-8")

            result = yinchao_music._resolve_api_key(
                environ={"YINCHAO_API_KEY_FILE": str(key_file)},
            )

        self.assertEqual("file-secret", result)

    def test_explicit_dotenv_supports_export_quotes_and_comments(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / "custom.env"
            env_file.write_text(
                "# only the target key is read\n"
                "UNRELATED=value\n"
                'export YINCHAO_API_KEY="dotenv-secret" # comment\n',
                encoding="utf-8",
            )

            result = yinchao_music._resolve_api_key(
                env_file=str(env_file),
                environ={},
            )

        self.assertEqual("dotenv-secret", result)

    def test_current_directory_dotenv_precedes_user_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cwd = root / "workspace"
            home = root / "home"
            cwd.mkdir()
            user_config = home / ".config" / "yinchao"
            user_config.mkdir(parents=True)
            (cwd / ".env").write_text(
                "YINCHAO_API_KEY=cwd-secret\n",
                encoding="utf-8",
            )
            (user_config / ".env").write_text(
                "YINCHAO_API_KEY=home-secret\n",
                encoding="utf-8",
            )

            result = yinchao_music._resolve_api_key(
                environ={},
                cwd=cwd,
                home=home,
            )

        self.assertEqual("cwd-secret", result)

    def test_user_config_is_the_final_file_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cwd = root / "workspace"
            home = root / "home"
            cwd.mkdir()
            user_config = home / ".config" / "yinchao"
            user_config.mkdir(parents=True)
            (user_config / ".env").write_text(
                "YINCHAO_API_KEY='home-secret'\n",
                encoding="utf-8",
            )

            result = yinchao_music._resolve_api_key(
                environ={},
                cwd=cwd,
                home=home,
            )

        self.assertEqual("home-secret", result)

    def test_explicit_dotenv_without_key_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / "custom.env"
            env_file.write_text("OTHER_KEY=value\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "缺少非空"):
                yinchao_music._resolve_api_key(
                    env_file=str(env_file),
                    environ={},
                )

    def test_env_file_option_is_available_after_the_subcommand(self) -> None:
        args = yinchao_music._build_parser().parse_args(
            ["song", "--prompt", "测试", "--env-file", "custom.env"]
        )

        self.assertEqual("custom.env", args.env_file)

    def test_main_uses_explicit_dotenv_without_mutating_environment(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / "custom.env"
            env_file.write_text(
                "UNRELATED=value\nYINCHAO_API_KEY=dotenv-secret\n",
                encoding="utf-8",
            )
            environ: dict[str, str] = {}
            stdout = io.StringIO()
            with (
                patch.object(yinchao_music.os, "environ", environ),
                patch.object(
                    yinchao_music.sys,
                    "argv",
                    [
                        "yinchao_music.py",
                        "lyrics",
                        "--prompt",
                        "测试",
                        "--env-file",
                        str(env_file),
                    ],
                ),
                patch.object(
                    yinchao_music,
                    "generate_lyrics",
                    return_value={"title": "测试歌", "lyric": "测试歌词"},
                ) as generate_lyrics,
                redirect_stdout(stdout),
            ):
                exit_code = yinchao_music.main()

        self.assertEqual(0, exit_code)
        self.assertEqual({}, environ)
        generate_lyrics.assert_called_once_with(
            "测试",
            "dotenv-secret",
            base_url=yinchao_music.DEFAULT_BASE_URL,
        )
        self.assertIn('"ok": true', stdout.getvalue())


class SubmitSongTests(unittest.TestCase):
    def test_lyric_only_song_uses_safe_default_prompt_and_default_count(self) -> None:
        with patch.object(
            yinchao_music, "_request_json", return_value={"id": "task-1"}
        ) as request_json:
            result = yinchao_music.submit_song("", "secret", lyric="自定义歌词")

        self.assertEqual({"id": "task-1"}, result)
        payload = request_json.call_args.kwargs["payload"]
        self.assertEqual("v4.0", payload["model"])
        self.assertEqual("normal", payload["task_type"])
        self.assertEqual(yinchao_music.DEFAULT_LYRIC_SONG_PROMPT, payload["prompt"])
        self.assertEqual("自定义歌词", payload["lyric"])
        self.assertEqual(2, payload["n"])

    def test_song_rejects_missing_prompt_and_lyric(self) -> None:
        with self.assertRaisesRegex(ValueError, "不能同时为空"):
            yinchao_music.submit_song("", "secret")

    def test_count_only_accepts_documented_values(self) -> None:
        with self.assertRaisesRegex(ValueError, "只能是 1 或 2"):
            yinchao_music.submit_song("测试", "secret", count=3)

    def test_instrumental_uses_dedicated_v4_endpoint(self) -> None:
        with patch.object(
            yinchao_music, "_request_json", return_value={"id": "task-instrumental"}
        ) as request_json:
            result = yinchao_music.submit_instrumental(
                "轻快的原声吉他 BGM，适合咖啡馆氛围",
                "secret",
                count=1,
            )

        self.assertEqual({"id": "task-instrumental"}, result)
        request_json.assert_called_once_with(
            "POST",
            "/api/v1/song/instrumental",
            "secret",
            payload={
                "model": "v4.0",
                "prompt": "轻快的原声吉他 BGM，适合咖啡馆氛围",
                "n": 1,
            },
            base_url=yinchao_music.DEFAULT_BASE_URL,
            timeout=60,
        )

    def test_instrumental_requires_prompt(self) -> None:
        with self.assertRaisesRegex(ValueError, "提示词不能为空"):
            yinchao_music.submit_instrumental("  ", "secret")

    def test_instrumental_parser_defaults_to_two_results(self) -> None:
        args = yinchao_music._build_parser().parse_args(
            ["instrumental", "--prompt", "宁静的钢琴曲"]
        )

        self.assertEqual("instrumental", args.command)
        self.assertEqual(2, args.n)

    def test_main_submits_and_waits_for_instrumental(self) -> None:
        submitted = {"id": "task-instrumental", "choices": []}
        completed = {
            "id": "task-instrumental",
            "choices": [
                {
                    "status": "done",
                    "audio_url": "https://example.com/instrumental.mp3",
                }
            ],
        }
        stdout = io.StringIO()
        with (
            patch.object(yinchao_music, "_resolve_api_key", return_value="secret"),
            patch.object(
                yinchao_music.sys,
                "argv",
                [
                    "yinchao_music.py",
                    "instrumental",
                    "--prompt",
                    "宁静的钢琴曲",
                    "--n",
                    "1",
                    "--quiet",
                ],
            ),
            patch.object(
                yinchao_music,
                "submit_instrumental",
                return_value=submitted,
            ) as submit_instrumental,
            patch.object(
                yinchao_music,
                "wait_for_task",
                return_value=completed,
            ) as wait_for_task,
            redirect_stdout(stdout),
        ):
            exit_code = yinchao_music.main()

        self.assertEqual(0, exit_code)
        submit_instrumental.assert_called_once_with(
            "宁静的钢琴曲",
            "secret",
            count=1,
            base_url=yinchao_music.DEFAULT_BASE_URL,
        )
        self.assertEqual(1, wait_for_task.call_args.kwargs["expected_count"])
        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["ok"])
        self.assertEqual(
            "https://example.com/instrumental.mp3",
            payload["songs"][0]["audio_url"],
        )

    def test_reference_payload_uses_reference_mode(self) -> None:
        source = {
            "audio_type": "audio_url",
            "audio_content": "https://example.com/reference.mp3",
        }
        with patch.object(
            yinchao_music, "_request_json", return_value={"id": "task-ref"}
        ) as request_json:
            yinchao_music.submit_reference(
                source,
                "secret",
                prompt="温暖的民谣氛围",
                similarity=1.3,
                count=1,
            )

        payload = request_json.call_args.kwargs["payload"]
        self.assertEqual("reference", payload["task_type"])
        self.assertEqual(source, payload["reference_audio"])
        self.assertEqual(1.3, payload["similarity"])
        self.assertEqual(1, payload["n"])

    def test_extend_payload_preserves_origin_and_position(self) -> None:
        source = {"audio_type": "audio_id", "audio_content": "song-1"}
        with patch.object(
            yinchao_music, "_request_json", return_value={"id": "task-ext"}
        ) as request_json:
            yinchao_music.submit_extend(
                source,
                "secret",
                lyric="继续唱下去",
                extend_at=60,
            )

        payload = request_json.call_args.kwargs["payload"]
        self.assertEqual(source, payload["origin_audio"])
        self.assertEqual("继续唱下去", payload["lyric"])
        self.assertEqual(60, payload["extend_at"])


class RecoveryTests(unittest.TestCase):
    def test_polling_error_preserves_task_id_for_resume(self) -> None:
        pending = {"id": "task-resume", "choices": [{"status": "running"}]}
        with (
            patch.object(
                yinchao_music.time,
                "monotonic",
                side_effect=[0.0, 0.0, 0.0],
            ),
            patch.object(yinchao_music.time, "sleep"),
            patch.object(
                yinchao_music,
                "query_task",
                side_effect=yinchao_music.YinchaoAPIError(None, "temporary"),
            ),
        ):
            result = yinchao_music.wait_for_task(
                pending,
                "secret",
                timeout=10,
                interval=1,
                progress=False,
            )

        self.assertEqual("task-resume", result["id"])
        self.assertTrue(result["polling_error"])
        self.assertIn("继续查询", result["message"])

    def test_processing_json_contains_resume_information(self) -> None:
        payload = yinchao_music._normalize_song(
            {
                "id": "task-resume",
                "polling_timeout": True,
                "choices": [{"status": "running"}],
            }
        )
        self.assertFalse(payload["ok"])
        self.assertEqual("processing", payload["status"])
        self.assertEqual("task-resume", payload["task_id"])

    def test_waits_for_all_expected_choices(self) -> None:
        first_choice_only = {
            "id": "task-two",
            "choices": [
                {"status": "done", "audio_url": "https://example.com/one.mp3"}
            ],
        }
        complete = {
            "id": "task-two",
            "choices": [
                {"status": "done", "audio_url": "https://example.com/one.mp3"},
                {"status": "done", "audio_url": "https://example.com/two.mp3"},
            ],
        }
        with (
            patch.object(yinchao_music.time, "monotonic", return_value=0.0),
            patch.object(yinchao_music.time, "sleep"),
            patch.object(yinchao_music, "query_task", return_value=complete) as query,
        ):
            result = yinchao_music.wait_for_task(
                first_choice_only,
                "secret",
                timeout=10,
                interval=1,
                progress=False,
                expected_count=2,
            )

        self.assertEqual(2, len(result["choices"]))
        query.assert_called_once_with(
            "task-two", "secret", base_url=yinchao_music.DEFAULT_BASE_URL
        )


class OutputTests(unittest.TestCase):
    def test_normalized_song_hides_internal_fields(self) -> None:
        payload = yinchao_music._normalize_song(
            {
                "id": "task-1",
                "create_at": 123,
                "choices": [
                    {
                        "status": "done",
                        "title": "测试歌曲",
                        "audio_url": "https://example.com/song.mp3",
                        "lyric": "[VERSE]\n测试",
                        "duration": 120,
                        "size": 1024,
                    }
                ],
            }
        )
        self.assertEqual(
            {
                "ok": True,
                "type": "song",
                "songs": [
                    {
                        "title": "测试歌曲",
                        "audio_url": "https://example.com/song.mp3",
                        "lyric": "[VERSE]\n测试",
                    }
                ],
            },
            payload,
        )

    def test_done_choice_without_audio_is_reported_as_failure(self) -> None:
        payload = yinchao_music._normalize_song(
            {
                "id": "task-missing-audio",
                "choices": [{"status": "done", "title": "没有音频"}],
            }
        )

        self.assertFalse(payload["ok"])
        self.assertEqual("failed", payload["status"])
        self.assertIn("音频地址", payload["errors"][0]["message"])

    def test_empty_lyrics_response_is_reported_as_failure(self) -> None:
        payload = yinchao_music._normalize_lyrics({"title": "只有标题"})

        self.assertFalse(payload["ok"])
        self.assertIn("歌词", payload["error"]["message"])

    def test_missing_api_key_returns_safe_json_error(self) -> None:
        stdout = io.StringIO()
        with (
            patch.object(yinchao_music, "_resolve_api_key", return_value=""),
            patch.object(yinchao_music.sys, "argv", ["yinchao_music.py", "song", "--prompt", "测试"]),
            redirect_stdout(stdout),
        ):
            exit_code = yinchao_music.main()

        self.assertEqual(1, exit_code)
        output = stdout.getvalue()
        self.assertIn("YINCHAO_API_KEY", output)
        self.assertNotIn("secret", output)


if __name__ == "__main__":
    unittest.main()
