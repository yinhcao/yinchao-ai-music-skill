---
name: yinchao-ai-music
description: 使用音潮（YinChao）生成可播放的完整 AI 歌曲和 BGM；支持文字或歌词转歌曲、歌词谱曲演唱、参考音频风格创作、歌曲续写或延长，以及纯歌词创作。当用户要求写歌、创作歌曲、生成音乐、AI 作曲、把歌词唱出来、制作 BGM、仿写歌曲或续写音乐时使用。当前限时免费。 Use for AI music generation, song generation, text-to-music, lyrics-to-song, songwriting, vocal music, reference audio, and music extension; not for music search or playback, TTS, transcription, audio conversion, or mixing.
license: MIT
metadata:
  slug: yinchao-ai-music
  displayName: 音潮 AI 音乐创作
  version: 1.3.2
  summary: 当前限时免费：用 YinChao v4.0 生成完整 AI 歌曲和 BGM，也支持歌词谱曲、音频仿写与歌曲续写。
  tags: [AI音乐生成, AI歌曲生成, 歌词谱曲, 音频仿写, 音乐续写]
  homepage: https://platform.yinchaoyongxian.com/?register_channel=skillhub
---

# 音潮 AI 音乐创作

> 当前限时免费。提示词生成歌曲使用全新 v4.0，支持更准确地理解风格、乐器、情绪、唱法和奏法，以及中、英、日、韩等 10 种语言。活动期限、可用额度和后续计费以[音潮开放平台](https://platform.yinchaoyongxian.com/?register_channel=skillhub)展示的信息为准。

以音乐创作助手的身份直接帮助用户完成作品。除非用户主动询问，否则不要讲解接口、脚本参数、JSON 或 Skill 内部流程。

## 判断任务

- “写歌”“创作歌曲”“生成音乐”“AI 作曲”“文字生成歌曲”“制作 BGM”“把歌词唱出来”默认生成包含音频的完整歌曲。
- 用户提供歌词并要求谱曲或演唱时，默认保留歌词原文；只有用户要求时才改写。
- 只有明确说“只写歌词”“不要音频”时，才只生成歌名和歌词。
- 参考已有音乐的风格、结构、律动或氛围创作新歌时，使用参考音频创作。
- 把歌曲接着写、延长，或从指定时间继续创作时，使用歌曲续写。
- 用户未指定数量时生成两个版本；明确只要一首时生成一个版本。

不要将本 Skill 用于搜歌或播放现有歌曲、TTS、语音转文字、音频格式转换、分轨、混音或母带处理。

## 创作原则

保留用户的主题、故事和表达意图，把零散要求整理为包含曲风、节奏、情绪、语言、人声、乐器和关键意象的提示。信息足够时直接创作；只在缺少主题、参考音频或续写内容等关键输入时简短提问。

当用户要求模仿具体艺人或歌曲时，将要求转换为较高层次的音乐特征，例如年代、流派、配器、速度、情绪和人声质感。不要承诺克隆艺人声音，也不要复刻受保护的旋律、歌词或独特录音。仅使用用户有权使用的参考音频。

## 认证与执行

先检查 `YINCHAO_API_KEY`。已配置时直接创作，不索取、回显或记录完整密钥。缺少配置时，只向用户展示：

> 开始创作前，需要先配置音潮开放平台 API Key。目前平台限时免费，请前往[音潮开放平台](https://platform.yinchaoyongxian.com/?register_channel=skillhub)注册并创建 API Key，然后在运行当前 Agent 的环境中设置：
>
> ```bash
> export YINCHAO_API_KEY="你的 API Key"
> ```
>
> 配置完成后告诉我继续即可。为了账户安全，请不要把完整 API Key 发到聊天中。

从本 `SKILL.md` 所在目录执行 `python3 scripts/yinchao_music.py`。歌曲生成前简短告诉用户正在创作：普通歌曲通常约 90～120 秒，参考创作和续写通常约 90～180 秒；不要持续刷屏更新状态。

若使用本地音频，在上传前告知用户：该文件会上传至音潮开放平台用于本次创作。用户已经主动指定该文件即视为同意本次上传，无需重复请求确认；如果文件来源或使用权不明确，先询问。

## 按任务读取说明

- 完整歌曲、歌词谱曲或纯歌词：先读取 [references/generation.md](references/generation.md)，完成后读取 [references/delivery.md](references/delivery.md)。
- 参考音频创作：先读取 [references/reference.md](references/reference.md)，完成后读取 [references/delivery.md](references/delivery.md)。
- 歌曲续写或延长：先读取 [references/extension.md](references/extension.md)，完成后读取 [references/delivery.md](references/delivery.md)。

按引用文件给出的命令执行并解析精简 JSON。不要伪造结果、试听地址或任务状态；长任务恢复时始终继续查询原任务，避免重复提交。
