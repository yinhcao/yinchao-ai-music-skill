# 音潮涌现 AI 音乐创作 Skill

[![CI](https://github.com/yinhcao/yinchao-ai-music-skill/actions/workflows/test.yml/badge.svg)](https://github.com/yinhcao/yinchao-ai-music-skill/actions/workflows/test.yml)
[![SkillHub](https://img.shields.io/badge/SkillHub-已发布-3957FF)](https://skillhub.cloud.tencent.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

当前限时免费。通过音潮开放平台为 Agent 提供完整的 AI 音乐创作能力：根据想法生成歌曲、把已有歌词唱成歌、参考音频仿写、扩写已有歌曲，以及单独创作歌词。

> 普通歌曲使用音潮 v4.0 音乐创作模型。用户只说“写歌”时，Skill 会默认生成可播放的完整歌曲，而不是只返回歌词。

## 能做什么

- 根据主题、曲风、情绪、乐器和人声要求生成完整歌曲
- 使用用户自己的歌词谱曲并演唱
- 参考 MP3、WAV、公开音频地址或音潮歌曲 ID 仿写
- 从歌曲结尾或指定时间点继续扩写
- 仅在用户明确要求时单独创作歌名和歌词
- 支持长任务恢复，避免等待中断后重复提交

## 安装

### 从 SkillHub 安装

在 [SkillHub](https://skillhub.cloud.tencent.com/) 搜索“音潮涌现 AI 音乐创作”，按照页面提示安装。

### 在 Codex 中从 GitHub 安装

对 Codex 说：

```text
使用 $skill-installer 安装：
https://github.com/yinhcao/yinchao-ai-music-skill/tree/main/skills/yinchaoyongxian-music
```

也可以手动将 `skills/yinchaoyongxian-music` 复制到本地 Skills 目录。

## 配置 API Key

1. 前往[音潮开放平台](https://platform.yinchaoyongxian.com/?register_channel=github)注册并创建 API Key。
2. 在运行 Agent 的环境中设置：

```bash
export YINCHAO_API_KEY="你的 API Key"
```

不要把完整 API Key 发到聊天、Issue、日志或提交记录中。Skill 只从环境变量 `YINCHAO_API_KEY` 读取密钥。

## 使用示例

安装后，可以直接用自然语言创作：

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

只有在明确说“只写歌词”或“不要音频”时，Skill 才只生成歌词。

## 本地开发

仓库中的 Skill 包位于：

```text
skills/yinchaoyongxian-music
```

运行离线校验和测试：

```bash
python3 tools/validate_skill.py
python3 -m unittest discover -s tests -v
```

运行 SkillHub 本地预检：

```bash
skillhub publish skills/yinchaoyongxian-music --dry-run --json
```

本地调用示例：

```bash
python3 skills/yinchaoyongxian-music/scripts/yinchao_music.py song \
  --prompt "温暖的中文民谣，木吉他，轻柔男声"
```

脚本默认输出适合程序和工作流消费的精简 JSON；添加 `--human` 可输出适合人工阅读的歌名、试听地址和歌词。

## 发布

GitHub 是唯一源码，SkillHub 是国内分发渠道。不要在其他仓库同时维护另一份 Skill。

1. 修改 Skill，并更新 `SKILL.md` 中的语义化版本号。
2. 运行离线校验、单元测试和 SkillHub `--dry-run`。
3. 合并到 `main` 后创建与版本一致的 Git Tag，例如 `v1.2.3`。
4. 推送 Tag。GitHub Actions 会测试、发布到 SkillHub，并创建 GitHub Release。

```bash
git tag -a v1.2.3 -m "v1.2.3"
git push origin v1.2.3
```

自动发布前，需要在 GitHub 仓库的 Actions secrets 中配置 `SKILLHUB_TOKEN`。不要将 Token 写入工作流文件。

## 安全

安全问题请参阅 [SECURITY.md](SECURITY.md)。一般功能问题可以提交 GitHub Issue，但请先移除 API Key、任务 ID、私有音频地址及其他敏感信息。

## 许可证

本仓库代码采用 [MIT License](LICENSE)。许可证仅适用于本仓库中的代码与 Skill 文件；音潮开放平台服务、生成内容及品牌标识仍以平台当时展示的服务条款为准。
