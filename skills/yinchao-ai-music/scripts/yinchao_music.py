#!/usr/bin/env python3
"""调用音潮开放平台生成歌词，或生成、仿写、扩写歌曲。"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
from uuid import uuid4


CHANNEL = "github"
CHANNEL_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
DEFAULT_BASE_URL = "https://open.yinchaoyongxian.com"
DEFAULT_LYRIC_SONG_PROMPT = "根据提供的歌词创作并演唱一首完整歌曲，不改写歌词"
TERMINAL_STATUSES = {"done", "fail", "cancelled"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_CREDENTIAL_FILE_BYTES = 1024 * 1024
API_KEY_ENV = "YINCHAO_API_KEY"
API_KEY_FILE_ENV = "YINCHAO_API_KEY_FILE"
ALLOWED_AUDIO_TYPES = {
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
}


@dataclass
class YinchaoAPIError(Exception):
    status: int | None
    detail: str

    def __str__(self) -> str:
        if self.status is None:
            return self.detail
        return f"HTTP {self.status}: {self.detail}"


def _read_credential_file(path: Path, *, label: str) -> str:
    path = path.expanduser()
    try:
        if not path.is_file():
            raise ValueError(f"{label}不是文件：{path}")
        if path.stat().st_size > MAX_CREDENTIAL_FILE_BYTES:
            raise ValueError(f"{label}过大：{path}")
        return path.read_text(encoding="utf-8-sig")
    except ValueError:
        raise
    except OSError as exc:
        raise ValueError(f"无法读取{label}：{path}（{exc}）") from None


def _parse_dotenv_value(raw: str, *, path: Path, line_number: int) -> str:
    value = raw.strip()
    if not value:
        return ""

    if value[0] not in {"'", '"'}:
        comment = re.search(r"\s+#", value)
        return (value[: comment.start()] if comment else value).rstrip()

    quote = value[0]
    escaped = False
    characters: list[str] = []
    closing_index: int | None = None
    for index, character in enumerate(value[1:], start=1):
        if quote == '"' and escaped:
            if character not in {'"', "\\"}:
                characters.append("\\")
            characters.append(character)
            escaped = False
            continue
        if quote == '"' and character == "\\":
            escaped = True
            continue
        if character == quote:
            closing_index = index
            break
        characters.append(character)

    if escaped:
        characters.append("\\")
    if closing_index is None:
        raise ValueError(f"dotenv 引号未闭合：{path}:{line_number}")

    trailing = value[closing_index + 1 :].strip()
    if trailing and not trailing.startswith("#"):
        raise ValueError(f"dotenv 值后存在无效内容：{path}:{line_number}")
    return "".join(characters)


def _read_dotenv_api_key(path: Path) -> str:
    text = _read_credential_file(path, label="dotenv 文件")
    api_key = ""
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        name, separator, raw_value = line.partition("=")
        if name.strip() != API_KEY_ENV:
            continue
        if not separator:
            raise ValueError(f"dotenv 缺少等号：{path}:{line_number}")
        api_key = _parse_dotenv_value(
            raw_value,
            path=path,
            line_number=line_number,
        ).strip()
    return api_key


def _read_raw_api_key(path: Path) -> str:
    api_key = _read_credential_file(path, label="API Key 文件").strip()
    if not api_key:
        raise ValueError(f"API Key 文件为空：{path.expanduser()}")
    if "\n" in api_key or "\r" in api_key:
        raise ValueError(
            f"API Key 文件只能包含一行原始密钥：{path.expanduser()}"
        )
    return api_key


def _resolve_api_key(
    *,
    env_file: str | None = None,
    environ: Mapping[str, str] | None = None,
    cwd: Path | None = None,
    home: Path | None = None,
) -> str:
    environ = os.environ if environ is None else environ

    api_key = environ.get(API_KEY_ENV, "").strip()
    if api_key:
        return api_key

    api_key_file = environ.get(API_KEY_FILE_ENV, "").strip()
    if api_key_file:
        return _read_raw_api_key(Path(api_key_file))

    if env_file:
        path = Path(env_file).expanduser()
        api_key = _read_dotenv_api_key(path)
        if not api_key:
            raise ValueError(f"dotenv 文件中缺少非空 {API_KEY_ENV}：{path}")
        return api_key

    cwd = Path.cwd() if cwd is None else cwd
    home = Path.home() if home is None else home
    candidates = (cwd / ".env", home / ".config" / "yinchao" / ".env")
    visited: set[Path] = set()
    for path in candidates:
        path = path.expanduser()
        try:
            identity = path.resolve()
        except OSError:
            identity = path.absolute()
        if identity in visited or not path.exists():
            continue
        visited.add(identity)
        api_key = _read_dotenv_api_key(path)
        if api_key:
            return api_key
    return ""


def _read_error_detail(raw: bytes) -> str:
    text = raw.decode("utf-8", errors="replace").strip()
    if not text:
        return "请求失败，服务端未返回错误详情"
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return text[:500]
    if isinstance(data, dict):
        detail = data.get("detail") or data.get("message") or data.get("error")
        if detail:
            return str(detail)
    return json.dumps(data, ensure_ascii=False)



def _request_json(
    method: str,
    path: str,
    api_key: str,
    *,
    payload: dict[str, Any] | None = None,
    query: dict[str, str] | None = None,
    base_url: str = DEFAULT_BASE_URL,
    timeout: float = 60,
    retry_get: int = 0,
) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}{path}"
    if query:
        url = f"{url}?{urlencode(query)}"

    body = None
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    attempts = retry_get + 1 if method == "GET" else 1
    for attempt in range(attempts):
        request = Request(
            url,
            data=body,
            method=method,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Channel": CHANNEL,
            },
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                raw = response.read()
        except HTTPError as exc:
            detail = _read_error_detail(exc.read())
            if (
                method == "GET"
                and exc.code in {429, 500, 502, 503, 504}
                and attempt + 1 < attempts
            ):
                time.sleep(2**attempt)
                continue
            raise YinchaoAPIError(exc.code, detail) from None
        except (URLError, TimeoutError) as exc:
            if method == "GET" and attempt + 1 < attempts:
                time.sleep(2**attempt)
                continue
            raise YinchaoAPIError(
                None,
                f"网络请求失败: {exc.reason if isinstance(exc, URLError) else exc}",
            ) from None

        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise YinchaoAPIError(None, "服务端返回了无法解析的响应") from None
        if not isinstance(data, dict):
            raise YinchaoAPIError(None, "服务端返回的数据格式不正确")
        return data

    raise YinchaoAPIError(None, "请求失败")


def _validate_prompt(prompt: str, *, max_length: int) -> str:
    prompt = prompt.strip()
    if not prompt:
        raise ValueError("提示词不能为空")
    if len(prompt) > max_length:
        raise ValueError(f"提示词不能超过 {max_length} 个字符")
    return prompt


def _validate_lyric(lyric: str) -> str:
    lyric = lyric.strip()
    if len(lyric) > 3000:
        raise ValueError("歌词不能超过 3000 个字符")
    return lyric


def _validate_count(count: int) -> None:
    if count not in {1, 2}:
        raise ValueError("歌曲数量只能是 1 或 2")


def _validate_audio_url(audio_url: str) -> str:
    audio_url = audio_url.strip()
    parsed = urlparse(audio_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("音频 URL 必须是可公开访问的 HTTP 或 HTTPS 地址")
    return audio_url


def upload_audio_file(
    file_path: str,
    api_key: str,
    *,
    upload_type: str,
    base_url: str = DEFAULT_BASE_URL,
    progress: bool = True,
) -> str:
    path = Path(file_path).expanduser()
    if not path.is_file():
        raise ValueError(f"找不到音频文件：{path}")

    suffix = path.suffix.lower()
    content_type = ALLOWED_AUDIO_TYPES.get(suffix)
    if not content_type:
        raise ValueError("本地音频仅支持 MP3 或 WAV 格式")
    try:
        file_size = path.stat().st_size
    except OSError as exc:
        raise ValueError(f"无法读取音频文件信息：{exc}") from None
    if file_size > MAX_UPLOAD_BYTES:
        raise ValueError("音频文件大小不能超过 10MB")
    if upload_type not in {"reference", "extend"}:
        raise ValueError("无效的音频上传类型")

    boundary = f"----YinchaoSkill{uuid4().hex}"
    filename = f"audio{suffix}"
    try:
        audio_data = path.read_bytes()
    except OSError as exc:
        raise ValueError(f"无法读取音频文件：{exc}") from None
    body = b"".join(
        [
            f"--{boundary}\r\n".encode(),
            (
                'Content-Disposition: form-data; name="file"; '
                f'filename="{filename}"\r\n'
            ).encode(),
            f"Content-Type: {content_type}\r\n\r\n".encode(),
            audio_data,
            b"\r\n",
            f"--{boundary}\r\n".encode(),
            b'Content-Disposition: form-data; name="upload_type"\r\n\r\n',
            upload_type.encode(),
            b"\r\n",
            f"--{boundary}--\r\n".encode(),
        ]
    )
    request = Request(
        f"{base_url.rstrip('/')}/api/v1/file/upload",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(len(body)),
            "Accept": "application/json",
            "Channel": CHANNEL,
        },
    )

    if progress:
        print("[音潮] 正在上传音频", end="", file=sys.stderr, flush=True)
    try:
        with urlopen(request, timeout=120) as response:
            raw = response.read()
    except HTTPError as exc:
        if progress:
            print(" 失败", file=sys.stderr, flush=True)
        raise YinchaoAPIError(exc.code, _read_error_detail(exc.read())) from None
    except (URLError, TimeoutError) as exc:
        if progress:
            print(" 失败", file=sys.stderr, flush=True)
        detail = exc.reason if isinstance(exc, URLError) else exc
        raise YinchaoAPIError(None, f"音频上传失败: {detail}") from None

    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        if progress:
            print(" 失败", file=sys.stderr, flush=True)
        raise YinchaoAPIError(None, "音频上传接口返回了无法解析的响应") from None
    upload_id = str(data.get("id") or "") if isinstance(data, dict) else ""
    if not upload_id:
        if progress:
            print(" 失败", file=sys.stderr, flush=True)
        raise YinchaoAPIError(None, "音频上传响应中缺少文件 ID")
    if progress:
        print(" 完成", file=sys.stderr, flush=True)
    return upload_id


def prepare_audio_source(
    *,
    audio_file: str | None,
    audio_url: str | None,
    audio_id: str | None,
    api_key: str,
    upload_type: str,
    base_url: str = DEFAULT_BASE_URL,
    progress: bool = True,
) -> dict[str, str]:
    if audio_file:
        upload_id = upload_audio_file(
            audio_file,
            api_key,
            upload_type=upload_type,
            base_url=base_url,
            progress=progress,
        )
        return {"audio_type": "upload_id", "audio_content": upload_id}
    if audio_url:
        return {
            "audio_type": "audio_url",
            "audio_content": _validate_audio_url(audio_url),
        }
    if audio_id:
        audio_id = audio_id.strip()
        if not audio_id:
            raise ValueError("平台歌曲 ID 不能为空")
        return {"audio_type": "audio_id", "audio_content": audio_id}
    raise ValueError("必须提供本地音频、音频 URL 或平台歌曲 ID")


def generate_lyrics(
    prompt: str,
    api_key: str,
    *,
    base_url: str = DEFAULT_BASE_URL,
) -> dict[str, Any]:
    return _request_json(
        "POST",
        "/api/v1/lyric/generate",
        api_key,
        payload={"prompt": _validate_prompt(prompt, max_length=2000)},
        base_url=base_url,
        timeout=120,
    )


def submit_song(
    prompt: str,
    api_key: str,
    *,
    lyric: str = "",
    count: int = 2,
    base_url: str = DEFAULT_BASE_URL,
) -> dict[str, Any]:
    _validate_count(count)
    lyric = _validate_lyric(lyric)
    prompt = prompt.strip()
    if not prompt and not lyric:
        raise ValueError("生成歌曲时提示词和歌词不能同时为空")
    if not prompt:
        prompt = DEFAULT_LYRIC_SONG_PROMPT
    prompt = _validate_prompt(prompt, max_length=1000)
    return _request_json(
        "POST",
        "/api/v1/song/generate",
        api_key,
        payload={
            "model": "v4.0",
            "task_type": "normal",
            "prompt": prompt,
            "lyric": lyric,
            "n": count,
        },
        base_url=base_url,
        timeout=60,
    )


def submit_reference(
    reference_audio: dict[str, str],
    api_key: str,
    *,
    prompt: str,
    lyric: str = "",
    similarity: float = 0.8,
    count: int = 2,
    base_url: str = DEFAULT_BASE_URL,
) -> dict[str, Any]:
    _validate_count(count)
    lyric = _validate_lyric(lyric)
    prompt = prompt.strip()
    if not prompt and not lyric:
        raise ValueError("仿写时提示词和歌词不能同时为空")
    if prompt:
        prompt = _validate_prompt(prompt, max_length=1000)
    if similarity not in {0.2, 0.8, 1.3, 1.5}:
        raise ValueError("相似度只能是 0.2、0.8、1.3 或 1.5")
    return _request_json(
        "POST",
        "/api/v1/song/generate",
        api_key,
        payload={
            "model": "v3.5",
            "task_type": "reference",
            "prompt": prompt,
            "lyric": lyric,
            "reference_audio": reference_audio,
            "similarity": similarity,
            "n": count,
        },
        base_url=base_url,
        timeout=60,
    )


def submit_extend(
    origin_audio: dict[str, str],
    api_key: str,
    *,
    lyric: str = "",
    extend_at: float | None = None,
    count: int = 2,
    base_url: str = DEFAULT_BASE_URL,
) -> dict[str, Any]:
    _validate_count(count)
    lyric = _validate_lyric(lyric)
    if extend_at is not None and extend_at < 0:
        raise ValueError("扩写时间点不能为负数")
    payload: dict[str, Any] = {
        "model": "v3.5",
        "origin_audio": origin_audio,
        "n": count,
    }
    if lyric:
        payload["lyric"] = lyric
    if extend_at is not None:
        payload["extend_at"] = extend_at
    return _request_json(
        "POST",
        "/api/v1/song/extend",
        api_key,
        payload=payload,
        base_url=base_url,
        timeout=60,
    )


def query_task(
    task_id: str,
    api_key: str,
    *,
    base_url: str = DEFAULT_BASE_URL,
) -> dict[str, Any]:
    return _request_json(
        "GET",
        "/api/v1/task/query",
        api_key,
        query={"task_id": task_id},
        base_url=base_url,
        timeout=60,
        retry_get=3,
    )


def _start_progress(label: str, *, enabled: bool) -> None:
    if enabled:
        print(f"[音潮] {label}", end="", file=sys.stderr, flush=True)


def _print_progress_dot(*, enabled: bool) -> None:
    if enabled:
        print(".", end="", file=sys.stderr, flush=True)


def _finish_progress(message: str, *, enabled: bool) -> None:
    if enabled:
        print(f" {message}", file=sys.stderr, flush=True)


def _task_statuses(task: dict[str, Any]) -> tuple[str, ...]:
    choices = task.get("choices")
    if not isinstance(choices, list) or not choices:
        return ()

    return tuple(
        str(choice.get("status") or "unknown")
        for choice in choices
        if isinstance(choice, dict)
    )


def wait_for_task(
    task: dict[str, Any],
    api_key: str,
    *,
    timeout: float,
    interval: float,
    progress: bool = True,
    progress_interval: float = 3,
    progress_label: str = "歌曲生成中",
    base_url: str = DEFAULT_BASE_URL,
    expected_count: int | None = None,
) -> dict[str, Any]:
    task_id = str(task.get("id") or "")
    if not task_id:
        raise YinchaoAPIError(None, "提交响应中缺少任务 ID")

    started_at = time.monotonic()
    deadline = started_at + timeout
    next_progress_at = started_at + progress_interval
    latest = task
    _start_progress(progress_label, enabled=progress)

    try:
        while time.monotonic() < deadline:
            now = time.monotonic()
            statuses = _task_statuses(latest)
            has_all_choices = expected_count is None or len(statuses) >= expected_count
            if statuses and has_all_choices and set(statuses) <= TERMINAL_STATUSES:
                if set(statuses) == {"done"}:
                    _finish_progress("完成", enabled=progress)
                else:
                    _finish_progress("结束", enabled=progress)
                return latest

            if now >= next_progress_at:
                _print_progress_dot(enabled=progress)
                next_progress_at = now + progress_interval

            time.sleep(interval)
            latest = query_task(task_id, api_key, base_url=base_url)
    except YinchaoAPIError as exc:
        latest.setdefault("id", task_id)
        latest["polling_error"] = True
        latest["message"] = (
            f"暂时无法查询任务状态：{exc}。"
            "任务仍可能在生成，请保留任务 ID 稍后继续查询"
        )
        _finish_progress("查询暂时中断", enabled=progress)
        return latest
    except KeyboardInterrupt:
        latest.setdefault("id", task_id)
        latest["polling_interrupted"] = True
        latest["message"] = "已停止等待，任务仍可能在生成，请保留任务 ID 稍后查询"
        _finish_progress("已停止等待", enabled=progress)
        return latest

    latest.setdefault("id", task_id)
    latest["polling_timeout"] = True
    latest["message"] = "轮询超时，任务可能仍在生成，请保留任务 ID 稍后查询"
    _finish_progress("等待超时", enabled=progress)
    return latest


def _format_lyrics(result: dict[str, Any]) -> str:
    title = str(result.get("title") or "未命名歌曲").strip()
    lyric = str(result.get("lyric") or "").strip()
    lines = [f"歌名：《{title}》"]
    if lyric:
        lines.extend(["", "歌词：", lyric])
    return "\n".join(lines)


def _format_song_choice(
    choice: dict[str, Any],
    *,
    index: int,
    total: int,
) -> str:
    status = str(choice.get("status") or "")
    prefix = f"歌曲 {index}\n" if total > 1 else ""

    if status == "done":
        title = str(choice.get("title") or "").strip()
        audio_url = str(choice.get("audio_url") or "").strip()
        lyric = str(choice.get("lyric") or "").strip()
        if not audio_url:
            return f"{prefix}生成结果无效\n原因：服务端未返回可播放的音频地址"
        lines = [f"{prefix}歌名：《{title}》" if title else f"{prefix}歌曲结果"]
        lines.extend(["", "试听/下载：", audio_url])
        if lyric:
            lines.extend(["", "歌词：", lyric])
        return "\n".join(lines)

    if status in {"fail", "cancelled"}:
        label = "生成失败" if status == "fail" else "已取消"
        error = str(choice.get("error") or "").strip()
        lines = [f"{prefix}{label}"]
        if error:
            lines.append(f"原因：{error}")
        return "\n".join(lines)

    label = status or "等待结果"
    return f"{prefix}歌曲仍在生成（{label}）"


def _format_song(result: dict[str, Any]) -> str:
    if result.get("submitted_only"):
        task_id = str(result.get("id") or "未知").strip()
        return (
            "歌曲任务已提交\n"
            f"任务 ID：{task_id}\n\n"
            "请稍后使用 status 命令继续等待，不要重新提交任务。"
        )

    if (
        result.get("polling_timeout")
        or result.get("polling_interrupted")
        or result.get("polling_error")
    ):
        task_id = str(result.get("id") or "未知").strip()
        if result.get("polling_error"):
            headline = "暂时无法查询歌曲状态"
        elif result.get("polling_interrupted"):
            headline = "已停止等待，歌曲可能仍在生成"
        else:
            headline = "歌曲仍在生成"
        return (
            f"{headline}\n"
            f"任务 ID：{task_id}\n\n"
            "请稍后使用 status 命令继续等待，不要重新提交任务。"
        )

    choices = result.get("choices")
    if not isinstance(choices, list) or not choices:
        task_id = str(result.get("id") or "未知").strip()
        return f"暂未取得歌曲结果\n任务 ID：{task_id}"

    valid_choices = [choice for choice in choices if isinstance(choice, dict)]
    if not valid_choices:
        task_id = str(result.get("id") or "未知").strip()
        return f"暂未取得歌曲结果\n任务 ID：{task_id}"

    blocks = [
        _format_song_choice(choice, index=index, total=len(valid_choices))
        for index, choice in enumerate(valid_choices, start=1)
    ]
    return "\n\n----------------------------------------\n\n".join(blocks)


def _normalize_lyrics(result: dict[str, Any]) -> dict[str, Any]:
    title = str(result.get("title") or "").strip()
    lyric = str(result.get("lyric") or "").strip()
    if not lyric:
        return {
            "ok": False,
            "type": "lyrics",
            "error": {"message": "服务端未返回歌词"},
        }
    return {
        "ok": True,
        "type": "lyrics",
        "title": title or "未命名歌曲",
        "lyric": lyric,
    }


def _normalize_song(result: dict[str, Any]) -> dict[str, Any]:
    task_id = str(result.get("id") or "").strip()
    if result.get("submitted_only"):
        return {
            "ok": True,
            "type": "song",
            "status": "submitted",
            "task_id": task_id,
            "message": str(
                result.get("message") or "任务已提交，请稍后使用 status 命令继续查询"
            ).strip(),
        }

    choices = result.get("choices")
    valid_choices = (
        [choice for choice in choices if isinstance(choice, dict)]
        if isinstance(choices, list)
        else []
    )

    songs: list[dict[str, str]] = []
    errors: list[dict[str, Any]] = []
    pending = False

    for index, choice in enumerate(valid_choices, start=1):
        status = str(choice.get("status") or "unknown").strip()
        if status == "done":
            audio_url = str(choice.get("audio_url") or "").strip()
            if not audio_url:
                errors.append(
                    {
                        "index": index,
                        "status": "fail",
                        "message": "服务端未返回可播放的音频地址",
                    }
                )
                continue
            song = {
                "audio_url": audio_url,
                "lyric": str(choice.get("lyric") or "").strip(),
            }
            title = str(choice.get("title") or "").strip()
            if title:
                song["title"] = title
            songs.append(song)
        elif status in {"fail", "cancelled"}:
            errors.append(
                {
                    "index": index,
                    "status": status,
                    "message": str(
                        choice.get("error")
                        or ("歌曲生成失败" if status == "fail" else "歌曲生成已取消")
                    ).strip(),
                }
            )
        else:
            pending = True

    if (
        result.get("polling_timeout")
        or result.get("polling_interrupted")
        or result.get("polling_error")
        or pending
        or not valid_choices
    ):
        status = "interrupted" if result.get("polling_interrupted") else "processing"
        payload: dict[str, Any] = {
            "ok": False,
            "type": "song",
            "status": status,
            "task_id": task_id,
            "message": str(
                result.get("message")
                or "歌曲仍在生成，请稍后使用 status 命令继续查询原任务"
            ).strip(),
        }
        if songs:
            payload["songs"] = songs
        if errors:
            payload["errors"] = errors
        return payload

    if errors:
        return {
            "ok": False,
            "type": "song",
            "status": "partial" if songs else "failed",
            "task_id": task_id,
            "songs": songs,
            "errors": errors,
        }

    return {
        "ok": True,
        "type": "song",
        "songs": songs,
    }


def _error_payload(command: str, message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "type": "lyrics" if command == "lyrics" else "song",
        "error": {"message": message},
    }


def _print_cli_error(args: argparse.Namespace, message: str) -> None:
    if args.human:
        print(f"错误：{message}", file=sys.stderr)
        return
    print(
        json.dumps(
            _error_payload(args.command, message),
            ensure_ascii=False,
        )
    )


def _add_credential_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--env-file",
        metavar="PATH",
        help=(
            "显式读取指定 dotenv 文件中的 YINCHAO_API_KEY；"
            "已设置的进程环境变量始终优先"
        ),
    )


def _add_output_options(parser: argparse.ArgumentParser) -> None:
    output = parser.add_mutually_exclusive_group()
    output.add_argument(
        "--human",
        action="store_true",
        help="输出适合人工阅读的歌名、试听地址和歌词",
    )
    output.add_argument(
        "--json",
        action="store_true",
        help="显式使用默认的精简 JSON 输出",
    )


def _add_audio_source_options(parser: argparse.ArgumentParser) -> None:
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--audio-file",
        help="本地 MP3/WAV 文件路径，最大 10MB",
    )
    source.add_argument(
        "--audio-url",
        help="可公开访问的 HTTP/HTTPS 音频地址",
    )
    source.add_argument(
        "--audio-id",
        help="音潮开放平台已经生成的歌曲 ID",
    )


def _add_wait_options(
    parser: argparse.ArgumentParser,
    *,
    allow_no_wait: bool = False,
) -> None:
    parser.add_argument(
        "--timeout",
        type=float,
        default=600,
        help="最长等待秒数，默认 600",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=3,
        help="轮询间隔秒数，默认 3",
    )
    parser.add_argument(
        "--progress-interval",
        "--dot-interval",
        type=float,
        default=3,
        help="每个进度点的间隔秒数，默认 3",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="不显示上传和等待进度",
    )
    if allow_no_wait:
        parser.add_argument(
            "--no-wait",
            action="store_true",
            help="提交任务后立即返回任务 ID，不等待生成完成",
        )
    _add_output_options(parser)


def _validate_wait_options(args: argparse.Namespace) -> None:
    if args.timeout <= 0:
        raise ValueError("--timeout 必须大于 0")
    if args.poll_interval < 1:
        raise ValueError("--poll-interval 不能小于 1 秒")
    if args.progress_interval < 1:
        raise ValueError("--progress-interval 不能小于 1 秒")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="通过音潮开放平台生成、仿写或扩写歌曲，也可单独生成歌词"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    lyrics = subparsers.add_parser("lyrics", help="根据提示词同步生成歌名与歌词")
    lyrics.add_argument("--prompt", required=True, help="歌曲主题、风格、情绪等描述")
    _add_credential_options(lyrics)
    _add_output_options(lyrics)

    song = subparsers.add_parser("song", help="根据提示词或自定义歌词生成完整歌曲")
    song.add_argument(
        "--prompt",
        default="",
        help="可选的歌曲主题、风格、情绪等描述",
    )
    song.add_argument(
        "--lyric",
        default="",
        help="可选的自定义歌词，最大 3000 字符",
    )
    song.add_argument(
        "--n", type=int, choices=(1, 2), default=2, help="生成数量，默认 2"
    )
    _add_credential_options(song)
    _add_wait_options(song, allow_no_wait=True)

    reference = subparsers.add_parser(
        "reference",
        help="参考已有音频仿写一首新歌并等待结果",
    )
    _add_audio_source_options(reference)
    reference.add_argument(
        "--prompt",
        default="参考这段音频的整体风格和结构，创作一首新歌",
        help="希望保留或改变的风格、律动、情绪等",
    )
    reference.add_argument(
        "--lyric",
        default="",
        help="可选的自定义歌词，最大 3000 字符",
    )
    reference.add_argument(
        "--similarity",
        type=float,
        choices=(0.2, 0.8, 1.3, 1.5),
        default=0.8,
        help="与参考音频的相似度，默认 0.8",
    )
    reference.add_argument(
        "--n",
        type=int,
        choices=(1, 2),
        default=2,
        help="生成数量，默认 2",
    )
    _add_credential_options(reference)
    _add_wait_options(reference, allow_no_wait=True)

    extend = subparsers.add_parser(
        "extend",
        help="从已有音频结尾或指定时间点继续扩写并等待结果",
    )
    _add_audio_source_options(extend)
    extend.add_argument(
        "--lyric",
        default="",
        help="可选的扩写部分歌词，最大 3000 字符",
    )
    extend.add_argument(
        "--extend-at",
        type=float,
        help="从第几秒开始扩写；不传则从音频结尾继续",
    )
    extend.add_argument(
        "--n",
        type=int,
        choices=(1, 2),
        default=2,
        help="生成数量，默认 2",
    )
    _add_credential_options(extend)
    _add_wait_options(extend, allow_no_wait=True)

    status = subparsers.add_parser("status", help="继续查询已经提交的歌曲任务")
    status.add_argument("--task-id", required=True, help="歌曲生成任务 ID")
    _add_credential_options(status)
    _add_wait_options(status)
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    try:
        api_key = _resolve_api_key(env_file=args.env_file)
    except ValueError as exc:
        _print_cli_error(args, str(exc))
        return 1
    if not api_key:
        message = (
            "缺少 YINCHAO_API_KEY。请设置环境变量，或在当前目录 .env、"
            "~/.config/yinchao/.env 中配置，"
            "不要把完整 API Key 发到对话中。"
        )
        _print_cli_error(args, message)
        return 1

    try:
        if args.command == "lyrics":
            result = generate_lyrics(
                args.prompt,
                api_key,
                base_url=DEFAULT_BASE_URL,
            )
        elif args.command in {"song", "reference", "extend"}:
            if args.command == "song":
                submitted = submit_song(
                    args.prompt,
                    api_key,
                    lyric=args.lyric,
                    count=args.n,
                    base_url=DEFAULT_BASE_URL,
                )
                progress_label = "歌曲生成中"
            else:
                audio_source = prepare_audio_source(
                    audio_file=args.audio_file,
                    audio_url=args.audio_url,
                    audio_id=args.audio_id,
                    api_key=api_key,
                    upload_type=args.command,
                    base_url=DEFAULT_BASE_URL,
                    progress=not args.quiet,
                )
                if args.command == "reference":
                    submitted = submit_reference(
                        audio_source,
                        api_key,
                        prompt=args.prompt,
                        lyric=args.lyric,
                        similarity=args.similarity,
                        count=args.n,
                        base_url=DEFAULT_BASE_URL,
                    )
                    progress_label = "歌曲仿写中"
                else:
                    submitted = submit_extend(
                        audio_source,
                        api_key,
                        lyric=args.lyric,
                        extend_at=args.extend_at,
                        count=args.n,
                        base_url=DEFAULT_BASE_URL,
                    )
                    progress_label = "歌曲扩写中"
            if args.no_wait:
                result = dict(submitted)
                result["submitted_only"] = True
                result["message"] = "任务已提交，请稍后使用 status 命令继续查询原任务"
            else:
                _validate_wait_options(args)
                result = wait_for_task(
                    submitted,
                    api_key,
                    timeout=args.timeout,
                    interval=args.poll_interval,
                    progress=not args.quiet,
                    progress_interval=args.progress_interval,
                    progress_label=progress_label,
                    base_url=DEFAULT_BASE_URL,
                    expected_count=args.n,
                )
        else:
            _validate_wait_options(args)
            try:
                current = query_task(
                    args.task_id,
                    api_key,
                    base_url=DEFAULT_BASE_URL,
                )
            except YinchaoAPIError as exc:
                result = {
                    "id": args.task_id,
                    "polling_error": True,
                    "message": (
                        f"暂时无法查询任务状态：{exc}。"
                        "请保留任务 ID 稍后继续查询"
                    ),
                }
            else:
                current.setdefault("id", args.task_id)
                result = wait_for_task(
                    current,
                    api_key,
                    timeout=args.timeout,
                    interval=args.poll_interval,
                    progress=not args.quiet,
                    progress_interval=args.progress_interval,
                    base_url=DEFAULT_BASE_URL,
                )
    except (ValueError, YinchaoAPIError) as exc:
        _print_cli_error(args, str(exc))
        return 1

    if args.human:
        if args.command == "lyrics":
            print(_format_lyrics(result))
        else:
            print(_format_song(result))
    else:
        payload = (
            _normalize_lyrics(result)
            if args.command == "lyrics"
            else _normalize_song(result)
        )
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
