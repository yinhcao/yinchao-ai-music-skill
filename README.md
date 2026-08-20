# YinChao AI Music｜音潮 AI 音乐创作

[![GitHub release](https://img.shields.io/github/v/release/yinhcao/yinchao-ai-music-skill)](https://github.com/yinhcao/yinchao-ai-music-skill/releases/latest)
[![skills.sh](https://skills.sh/b/yinhcao/yinchao-ai-music-skill)](https://skills.sh/yinhcao/yinchao-ai-music-skill)
[![Test](https://github.com/yinhcao/yinchao-ai-music-skill/actions/workflows/test.yml/badge.svg)](https://github.com/yinhcao/yinchao-ai-music-skill/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

当前限时免费。通过[音潮开放平台](https://platform.yinchaoyongxian.com/?register_channel=github)为 Codex、Claude Code 和其他 Agent 提供可播放的完整 AI 歌曲与 BGM：文字生成歌曲、歌词谱曲演唱、参考音频风格创作、歌曲续写与延长，以及纯歌词创作。

YinChao is an AI music generation skill for text-to-music, AI song generation, lyrics-to-song, songwriting, vocal music, reference audio creation, and song extension. It generates playable music instead of stopping at lyrics.

[开放平台](https://platform.yinchaoyongxian.com/?register_channel=github) · [API 文档](https://platform.yinchaoyongxian.com/docs) · [版本记录](https://github.com/yinhcao/yinchao-ai-music-skill/releases)

## 环境要求

- Python 3.10 或更高版本
- 支持 Agent Skills 的 Codex、Claude Code 或其他 Agent
- 音潮开放平台 API Key
- 仅在使用通用 Skills CLI 安装时需要 Node.js 与 `npx`

## 安装

使用 Skills CLI 从 GitHub 安装：

```bash
npx skills add yinhcao/yinchao-ai-music-skill \
  --skill yinchao-ai-music \
  -g -y
```

更新已安装的 Skill：

```bash
npx skills update yinchao-ai-music -g
```

## 能做什么

- 根据主题、曲风、情绪、乐器和人声要求生成完整歌曲或 BGM
- 把已有歌词谱曲并演唱，默认保留原文
- 参考 MP3、WAV、公开音频地址或音潮歌曲 ID 创作新歌
- 从歌曲结尾或指定时间点继续创作和延长音乐
- 仅在用户明确要求时单独创作歌名和歌词
- 在长任务中保留任务 ID，避免中断后重复提交

普通歌曲使用 YinChao v4.0。用户只说“写歌”时，Skill 默认请求生成两个版本，而不是只返回歌词；单个版本仍可能因生成失败而缺失。

## 配置 API Key

1. 前往[音潮开放平台](https://platform.yinchaoyongxian.com/?register_channel=github)注册并创建 API Key。
2. 在运行 Agent 的环境中设置：

```bash
export YINCHAO_API_KEY="你的 API Key"
```

不要把完整 API Key 发到聊天、Issue、日志或提交记录中。Skill 只从环境变量 `YINCHAO_API_KEY` 读取密钥。

使用本地参考音频或续写音频时，文件会上传至音潮开放平台用于本次创作。请只使用你有权使用的音频，并参阅[隐私政策](https://platform.yinchaoyongxian.com/privacy.html)与[服务条款](https://platform.yinchaoyongxian.com/terms.html)。

## 使用示例

```text
写一首温暖的中文民谣，木吉他和轻柔男声，主题是多年未见的朋友。
```

```text
把下面这段歌词谱成一首完整歌曲，保持歌词原文不变：……
```

```text
参考 /path/to/reference.mp3 的律动和氛围创作一首新歌，但不要复刻旋律。
```

```text
把 /path/to/song.mp3 从 60 秒开始继续扩写，接下来唱这段歌词：……
```

只有明确说“只写歌词”或“不要音频”时，Skill 才只生成歌词。

## 本地开发

Skill 包位于 `skills/yinchao-ai-music`，仓库根目录同时提供 Codex Plugin 清单。

运行离线校验和测试：

```bash
python3 tools/validate_skill.py
python3 -m unittest discover -s tests -v
npx skills add . --list
```

本地调用：

```bash
python3 skills/yinchao-ai-music/scripts/yinchao_music.py song \
  --prompt "温暖的中文民谣，木吉他，轻柔男声"
```

脚本默认输出适合 Agent 和工作流消费的精简 JSON；添加 `--human` 可输出歌名、试听地址和歌词。

## 安全与许可

安全问题请参阅 [SECURITY.md](SECURITY.md)。公开反馈前请移除 API Key、任务 ID、私有音频地址和未发布歌词。

仓库代码采用 [MIT License](LICENSE)。许可证只适用于本仓库代码与 Skill 文件；平台服务、生成内容和品牌标识以音潮开放平台当时展示的条款为准。
