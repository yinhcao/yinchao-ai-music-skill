# YinChao AI Music｜音潮 AI 音乐创作

[![GitHub release](https://img.shields.io/github/v/release/yinhcao/yinchao-ai-music-skill)](https://github.com/yinhcao/yinchao-ai-music-skill/releases/latest)
[![Test](https://github.com/yinhcao/yinchao-ai-music-skill/actions/workflows/test.yml/badge.svg)](https://github.com/yinhcao/yinchao-ai-music-skill/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

当前限时免费。通过[音潮开放平台](https://platform.yinchaoyongxian.com/?register_channel=github)为 Codex、Claude Code 和其他 Agent 提供可播放的完整 AI 歌曲与 BGM：文字生成歌曲、歌词谱曲演唱、参考音频风格创作、歌曲续写与延长，以及纯歌词创作。

YinChao is an AI music generation skill for text-to-music, AI song generation, lyrics-to-song, songwriting, vocal music, reference audio creation, and song extension. It generates playable music instead of stopping at lyrics.

## 环境要求

- Python 3.10 或更高版本
- 支持 Agent Skills 的 Codex、Claude Code 或其他 Agent
- 音潮开放平台 API Key
- 仅在使用通用 Skills CLI 安装时需要 Node.js 与 `npx`

## 安装

从 GitHub 安装最新公开版本：

```bash
npx skills add yinhcao/yinchao-ai-music-skill \
  --skill yinchao-ai-music \
  -g -y
```

当前维护的 Skill 名称是 `yinchao-ai-music`；`yinchaoyongxian-music` 是旧版名称。SkillHub 和 skills.sh 的公开索引可能晚于 GitHub Release 更新；如果暂时搜索不到新名称，请使用上面的 GitHub 安装命令。

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

Skill 包位于 `skills/yinchao-ai-music`，仓库根目录同时提供只包含 Skill 的 Codex Plugin 清单。

运行离线校验和测试：

```bash
python3 tools/validate_skill.py
python3 -m unittest discover -s tests -v
npx skills add . --list
```

运行 SkillHub 本地预检：

SkillHub 发布包只保留运行所需的文本、参考文档和脚本；Codex 专用 UI 元数据与 PNG 图标仍保留在 GitHub 源码中。

```bash
skillhub_stage_root="$(mktemp -d)"
mkdir -p "${skillhub_stage_root}/yinchao-ai-music"
cp skills/yinchao-ai-music/SKILL.md \
  "${skillhub_stage_root}/yinchao-ai-music/"
cp -R \
  skills/yinchao-ai-music/references \
  skills/yinchao-ai-music/scripts \
  "${skillhub_stage_root}/yinchao-ai-music/"
skillhub publish \
  "${skillhub_stage_root}/yinchao-ai-music" \
  --dry-run \
  --json
```

本地调用：

```bash
python3 skills/yinchao-ai-music/scripts/yinchao_music.py song \
  --prompt "温暖的中文民谣，木吉他，轻柔男声"
```

脚本默认输出适合 Agent 和工作流消费的精简 JSON；添加 `--human` 可输出歌名、试听地址和歌词。

分发方可以用 `YINCHAO_CHANNEL` 设置不超过 64 个字符的渠道标识，用于平台归因；未设置时保持 `skillhub`，普通用户无需配置。

## 发布与曝光

GitHub 是唯一源码，SkillHub 是国内分发渠道。发布前请确保 GitHub 仓库为 Public，并在仓库设置中添加以下 Topics：

```text
ai-music  ai-song-generator  text-to-music  lyrics-to-song
songwriting  music-generation  codex-skill  agent-skills  yinchao
```

建议在 GitHub、Skills CLI/skills.sh、SkillHub 与 [OpenAI 通用插件目录](https://developers.openai.com/plugins/build/plugins)使用同一个名称 `yinchao-ai-music`、同一组中英文关键词和相同品牌图标。该插件目录由 ChatGPT 和 Codex 共享；准备好公开资料后，按照[官方提交说明](https://developers.openai.com/plugins/deploy/submission)单独提交，仓库中的 `.codex-plugin/plugin.json` 不等同于已经发布。

README 顶部的标准安装命令应保持可复制；发布后，用典型查询检查 skills.sh 索引：

```bash
npx skills find "AI music"
npx skills find "AI song generator"
npx skills find "lyrics to song"
npx skills find "歌词谱曲"
```

后续版本发布：

1. 更新 `SKILL.md` 的 `metadata.version` 与 `.codex-plugin/plugin.json` 中的同一个语义化版本号。
2. 运行离线校验、单元测试和 SkillHub `--dry-run`。
3. 合并到 `main` 后创建相同版本的 Git Tag。
4. 推送 Tag；GitHub Actions 会测试、发布到 SkillHub，并创建 GitHub Release。
5. 确认 GitHub Release、SkillHub 版本和公开索引状态。

```bash
VERSION="1.3.2"
git tag -a "v${VERSION}" -m "v${VERSION}"
git push origin "v${VERSION}"
```

自动发布前，需要在 GitHub Actions secrets 中配置 `SKILLHUB_TOKEN`。不要将 Token 写入工作流文件。

## 安全与许可

安全问题请参阅 [SECURITY.md](SECURITY.md)。公开反馈前请移除 API Key、任务 ID、私有音频地址和未发布歌词。

仓库代码采用 [MIT License](LICENSE)。许可证只适用于本仓库代码与 Skill 文件；平台服务、生成内容和品牌标识以音潮开放平台当时展示的条款为准。
