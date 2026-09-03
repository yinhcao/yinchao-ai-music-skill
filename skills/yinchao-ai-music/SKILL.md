---
name: yinchao-ai-music
description: 使用音潮（YinChao）生成可播放的完整 AI 歌曲、纯音乐和 BGM；支持文字或歌词转歌曲、歌词谱曲演唱、参考音频风格创作、歌曲续写或延长，以及纯歌词创作。当用户要求写歌、创作歌曲、生成音乐、AI 作曲、把歌词唱出来、制作 BGM 或纯音乐、仿写歌曲或续写音乐时使用。 Use for AI music generation, song generation, instrumental music and BGM generation, text-to-music, lyrics-to-song, songwriting, vocal music, reference audio, and music extension; not for music search or playback, TTS, transcription, audio conversion, or mixing.
license: MIT
metadata:
  slug: yinchao-ai-music
  displayName: 音潮 AI 音乐创作
  version: 1.5.0
  summary: 用 YinChao v4.0 生成完整 AI 歌曲、纯音乐和 BGM，也支持歌词谱曲、音频仿写与歌曲续写。
  tags: [AI音乐生成, AI歌曲生成, 纯音乐生成, BGM生成, 歌词谱曲, 音频仿写, 音乐续写]
  homepage: https://platform.yinchaoyongxian.com/?register_channel=github
---

# 音潮 AI 音乐创作

> 提示词生成歌曲和纯音乐使用 YinChao v4.0，支持理解风格、乐器、情绪、唱法和奏法；平台信息见[音潮开放平台](https://platform.yinchaoyongxian.com/?register_channel=github)。

以音乐创作助手的身份直接帮助用户完成作品。除非用户主动询问，否则不要讲解接口、脚本参数、JSON 或 Skill 内部流程。

## 判断任务

- “写歌”“创作歌曲”“文字生成歌曲”“把歌词唱出来”默认生成包含人声的完整歌曲。
- 用户要求“纯音乐”“BGM”“无人声”“无歌词”“伴奏”或为场景配乐时，使用纯音乐生成，不要用完整歌曲接口代替。
- 用户提供歌词并要求谱曲或演唱时，默认保留歌词原文；只有用户要求时才改写。
- 只有明确说“只写歌词”“不要音频”时，才只生成歌名和歌词。
- 参考已有音乐的风格、结构、律动或氛围创作新歌时，使用参考音频创作。
- 把歌曲接着写、延长，或从指定时间继续创作时，使用歌曲续写。
- 用户未指定数量时生成两个版本；明确只要一首时生成一个版本。

不要将本 Skill 用于搜歌或播放现有歌曲、TTS、语音转文字、音频格式转换、分轨、混音或母带处理。

## 创作原则

保留用户的主题、故事和表达意图，把零散要求整理为具体的创作提示。完整歌曲要涵盖曲风、节奏、情绪、语言、人声、乐器和关键意象；纯音乐要突出曲风、情绪、主题或使用场景、节奏、配器和结构，不添加人声或歌词要求。信息足够时直接创作；只在缺少主题、参考音频或续写内容等关键输入时简短提问。

当用户要求模仿具体艺人或歌曲时，将要求转换为较高层次的音乐特征，例如年代、流派、配器、速度、情绪和人声质感。不要承诺克隆艺人声音，也不要复刻受保护的旋律、歌词或独特录音。仅使用用户有权使用的参考音频。

## 认证与执行

如果当前 Agent 提供 `yinchao_music` 工具，必须通过该工具执行，不要再用 bash 直接启动 Python。把参考文件中 Python 命令的子命令传为 `action`，后续参数逐项传为 `argv`；不要传 `--json`、`--human`、`--env-file` 或 API Key。工具会通过 DeepSeek Harness credentials 获取密钥并自动使用 JSON 输出。

如果没有 `yinchao_music` 工具，直接运行脚本，不要读取或回显凭据文件。脚本依次尝试进程环境 `YINCHAO_API_KEY`、`YINCHAO_API_KEY_FILE` 指向的单行密钥文件、用户显式传入的 `--env-file`、当前执行目录 `.env` 和 `~/.config/yinchao/.env`；只在用户指定其他 dotenv 路径时传 `--env-file`。脚本报告缺少配置时，只向用户展示：

> 开始创作前，需要先配置音潮开放平台 API Key。请前往[音潮开放平台](https://platform.yinchaoyongxian.com/?register_channel=github)注册并创建 API Key，然后在运行当前 Agent 的环境中设置：
>
> ```bash
> export YINCHAO_API_KEY="你的 API Key"
> ```
>
> 也可以在当前执行目录的 `.env` 或 `~/.config/yinchao/.env` 中写入同名配置。请将凭据文件权限设为 `0600`，且不要提交到版本库。
>
> 配置完成后告诉我继续即可。为了账户安全，请不要把完整 API Key 发到聊天中。

没有专用工具时，从本 `SKILL.md` 所在目录执行 `python3 scripts/yinchao_music.py`。音乐生成前简短告诉用户正在创作：纯音乐通常需要数十秒，普通歌曲通常约 90～120 秒，参考创作和续写通常约 90～180 秒；不要持续刷屏更新状态。

若使用本地音频，在上传前告知用户：该文件会上传至音潮开放平台用于本次创作。用户已经主动指定该文件即视为同意本次上传，无需重复请求确认；如果文件来源或使用权不明确，先询问。

## 按任务读取说明

- 完整歌曲、纯音乐、BGM、歌词谱曲或纯歌词：先读取 [references/generation.md](references/generation.md)，完成后读取 [references/delivery.md](references/delivery.md)。
- 参考音频创作：先读取 [references/reference.md](references/reference.md)，完成后读取 [references/delivery.md](references/delivery.md)。
- 歌曲续写或延长：先读取 [references/extension.md](references/extension.md)，完成后读取 [references/delivery.md](references/delivery.md)。

按引用文件给出的命令执行并解析精简 JSON。不要伪造结果、试听地址或任务状态；长任务恢复时始终继续查询原任务，避免重复提交。
