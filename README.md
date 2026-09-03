# YinChao AI Music｜音潮 AI 音乐创作

[![GitHub release](https://img.shields.io/github/v/release/yinhcao/yinchao-ai-music-skill)](https://github.com/yinhcao/yinchao-ai-music-skill/releases/latest)
[![skills.sh](https://skills.sh/b/yinhcao/yinchao-ai-music-skill)](https://www.skills.sh/yinhcao/yinchao-ai-music-skill/yinchao-ai-music)
[![Test](https://github.com/yinhcao/yinchao-ai-music-skill/actions/workflows/test.yml/badge.svg)](https://github.com/yinhcao/yinchao-ai-music-skill/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

通过[音潮开放平台](https://platform.yinchaoyongxian.com/?register_channel=github)，让 Codex、Claude Code 和其他 Agent 生成可播放的完整歌曲、纯音乐与 BGM，支持文字生成音乐、歌词谱曲、参考音频创作、歌曲续写和纯歌词创作。

YinChao is an AI music Agent Skill and DeepSeek Harness plugin that generates playable songs, instrumentals, and BGM from prompts, lyrics, or reference audio.

[开放平台](https://platform.yinchaoyongxian.com/?register_channel=github) · [API 文档](https://platform.yinchaoyongxian.com/docs?register_channel=github) · [SkillHub](https://skillhub.cloud.tencent.com/skills/user_025493eb/yinchao-ai-music) · [ClawHub](https://clawhub.ai/joeydqyuan/skills/yinchao-ai-music) · [skills.sh](https://www.skills.sh/yinhcao/yinchao-ai-music-skill/yinchao-ai-music) · [Awesome DSH Plugins](https://awesome-dsh-plugin.com/p/yinhcao/yinchao-ai-music-skill/) · [版本记录](https://github.com/yinhcao/yinchao-ai-music-skill/releases)

## 生成效果试听

无需安装即可先听[音潮开放平台](https://platform.yinchaoyongxian.com/?register_channel=github)首页展示的生成效果：

- [▶ 自然稳定的情绪表达](https://platform.yinchaoyongxian.com/musics/try_listen_01.mp3) — 听人声咬字、情绪表达与角色感
- [▶ 贴合主题的旋律记忆点](https://platform.yinchaoyongxian.com/musics/try_listen_02.mp3) — 听主题旋律、副歌记忆点与情绪推进
- [▶ 层次丰富的风格化编曲](https://platform.yinchaoyongxian.com/musics/try_listen_03.mp3) — 听人声、弦乐、鼓与笛等元素的编曲层次

## 安装

### 通用 Agent Skill

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

### DeepSeek Harness Plugin

该插件已收录于 [Awesome DSH Plugins](https://awesome-dsh-plugin.com/p/yinhcao/yinchao-ai-music-skill/)；可在详情页查看条目，也可以直接运行下面的命令安装。

直接从 GitHub 安装到所使用的 DSH profile：

```bash
dsh plugin --profile web add github:yinhcao/yinchao-ai-music-skill
```

将 `web` 换成实际的 profile 名称。然后按下文配置 Harness credentials，并重启对应的 DSH 进程。

卸载：

```bash
dsh plugin --profile web remove yinchao-ai-music
```

如果 DSH 已通过其他方式安装过同名 Skill，请先移除旧副本，避免重复加载。

## 能做什么

- 根据主题、曲风、情绪、乐器和人声要求生成完整歌曲
- 根据风格、情绪、主题或使用场景生成无人声的纯音乐或 BGM
- 把已有歌词谱曲并演唱，默认保留原文
- 参考 MP3、WAV、公开音频地址或音潮歌曲 ID 创作新歌
- 从歌曲结尾或指定时间点继续创作和延长音乐
- 仅在用户明确要求时单独创作歌名和歌词
- 在长任务中保留任务 ID，避免中断后重复提交

普通歌曲和纯音乐使用 YinChao v4.0。用户只说“写歌”时，Skill 默认生成两个完整歌曲版本；要求“纯音乐”“BGM”“无人声”或“伴奏”时改用纯音乐生成；只有明确要求“只写歌词”时才不生成音频。

## 配置 API Key

先前往[音潮开放平台](https://platform.yinchaoyongxian.com/?register_channel=github)创建 API Key。请勿把密钥发到聊天、Issue、日志或提交记录中。

### 通用 Skill

SkillHub、ClawHub、skills.sh、Codex、Claude Code 和本地脚本优先使用环境变量：

```bash
export YINCHAO_API_KEY="你的 API Key"
```

需要持久化配置时，推荐使用用户级配置文件 `~/.config/yinchao/.env`；需要按项目隔离时，也可以使用当前目录的 `.env`：

```bash
# ~/.config/yinchao/.env
YINCHAO_API_KEY="你的 API Key"
```

其他可选方式：用 `--env-file /path/to/.env` 指定 dotenv 文件，或用 `YINCHAO_API_KEY_FILE` 指向仅含一行原始密钥的文件。读取优先级为：环境变量 → 密钥文件 → `--env-file` → 当前目录 `.env` → 用户级 `.env`。

请为密钥文件设置仅当前用户可读权限（如 `chmod 600`）；使用项目级 `.env` 时确认它已加入 `.gitignore`，不要把任何凭据文件提交到仓库。

### DeepSeek Harness Plugin

DSH Plugin 推荐使用 Harness credentials。编辑 `~/.dsh/.credentials.yaml`（设置了 `DSH_HOME` 时使用 `$DSH_HOME/.credentials.yaml`）：

```yaml
version: 1

refs:
  YINCHAO_API_KEY: "你的 API Key"
```

如果文件已存在，只需把 `YINCHAO_API_KEY` 加到现有的 `refs` 下。然后运行：

```bash
chmod 600 "${DSH_HOME:-$HOME/.dsh}/.credentials.yaml"
```

密钥由 Harness 读取并仅传给音潮子进程，修改后会在下一次操作时生效。

使用本地参考音频或续写音频时，文件会上传至音潮开放平台用于本次创作。请只使用你有权使用的音频，并参阅[隐私政策](https://platform.yinchaoyongxian.com/privacy.html)与[服务条款](https://platform.yinchaoyongxian.com/terms.html)。

## 使用示例

```text
写一首温暖的中文民谣，木吉他和轻柔男声，主题是多年未见的朋友。
```

```text
把下面这段歌词谱成一首完整歌曲，保持歌词原文不变：……
```

```text
做一段轻快的原声吉他 BGM，温暖、松弛，适合咖啡馆使用，不要人声。
```

```text
参考 /path/to/reference.mp3 的律动和氛围创作一首新歌，但不要复刻旋律。
```

```text
把 /path/to/song.mp3 从 60 秒开始继续扩写，接下来唱这段歌词：……
```

## 本地开发

Skill 位于 `skills/yinchao-ai-music`。仓库根目录同时包含 Codex 和 DSH Plugin 配置，两者共用该 Skill。

运行离线校验和测试：

```bash
python3 tools/validate_skill.py
python3 -m unittest discover -s tests -v
npm pack --dry-run
npx skills add . --list
```

在 DSH Web 中测试本地 Plugin：

```bash
pack_dir="$(mktemp -d)"
package_file="$(npm pack --pack-destination "$pack_dir" --silent)"
dsh plugin --profile web add "$pack_dir/$package_file"
dsh --profile web --dump-config
dsh web
```

本地调用：

```bash
python3 skills/yinchao-ai-music/scripts/yinchao_music.py song \
  --prompt "温暖的中文民谣，木吉他，轻柔男声"
```

生成纯音乐：

```bash
python3 skills/yinchao-ai-music/scripts/yinchao_music.py instrumental \
  --prompt "轻快的原声吉他 BGM，适合咖啡馆氛围"
```

脚本默认输出适合 Agent 和工作流消费的精简 JSON；添加 `--human` 可输出歌名、试听地址和可用的歌词。

## 安全与许可

安全问题请参阅 [SECURITY.md](SECURITY.md)。公开反馈前请移除 API Key、任务 ID、私有音频地址和未发布歌词。

仓库代码采用 [MIT License](LICENSE)。许可证只适用于本仓库代码与 Skill 文件；平台服务、生成内容和品牌标识以音潮开放平台当时展示的条款为准。
