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
    / "yinchaoyongxian-music"
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
