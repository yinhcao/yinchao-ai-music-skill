from __future__ import annotations

import importlib.util
import io
import sys
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


class ChannelTests(unittest.TestCase):
    def test_channel_can_be_attributed_by_distributor(self) -> None:
        with patch.dict(
            yinchao_music.os.environ,
            {"YINCHAO_CHANNEL": "github-codex"},
            clear=True,
        ):
            self.assertEqual("github-codex", yinchao_music._channel_header())

    def test_invalid_channel_is_rejected_before_request(self) -> None:
        with (
            patch.dict(
                yinchao_music.os.environ,
                {"YINCHAO_CHANNEL": "bad channel\nvalue"},
                clear=True,
            ),
            self.assertRaisesRegex(ValueError, "YINCHAO_CHANNEL"),
        ):
            yinchao_music._channel_header()


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
            patch.dict(yinchao_music.os.environ, {}, clear=True),
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
