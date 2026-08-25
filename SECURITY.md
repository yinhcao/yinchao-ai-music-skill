# 安全策略

## 报告安全问题

如果发现可能泄露 API Key、绕过认证、访问他人任务或造成其他安全影响的问题，请不要创建公开 Issue，也不要提交包含真实密钥或私人音频的复现材料。

请通过[音潮开放平台](https://platform.yinchaoyongxian.com/?register_channel=github)的官方联系渠道私下报告，并提供：

- 受影响的 Skill 版本
- 问题影响与触发条件
- 已去除密钥、个人信息和私人内容的最小复现说明
- 建议的联系方式

我们不会要求你通过聊天或 Issue 提供完整 API Key。

## 使用者注意事项

- 在 SkillHub、ClawHub、skill.sh、Codex、Claude Code 等本地 Agent 中，优先通过环境变量 `YINCHAO_API_KEY` 提供密钥；也可以使用 `YINCHAO_API_KEY_FILE`、显式 `--env-file`、当前目录 `.env` 或 `~/.config/yinchao/.env`。
- 将所有凭据文件权限设为 `0600`，只在 `YINCHAO_API_KEY_FILE` 指向的文件中存放单行原始密钥；dotenv 文件使用 `YINCHAO_API_KEY=...`。不要把密钥本身放进命令行参数。
- Python 脚本只读取目标密钥，不会把 dotenv 的其他字段导入进程环境；已设置的进程环境变量始终覆盖文件来源。
- 在 DeepSeek Harness 中，优先通过 `$DSH_HOME/.credentials.yaml` 的 `refs.YINCHAO_API_KEY` 提供密钥，并将文件权限设为 `0600`；启动环境和 `.env` 仅作为兼容来源。
- DSH Plugin 在进程内解析凭据，只将密钥显式传给音潮 Python 子进程；不要把密钥放进工具参数、命令行或 `cordis.patch.yml`。
- 不要提交 `.env` 文件、终端日志或包含密钥的截图。
- 公开反馈前，移除任务 ID、私人音频地址和未发布歌词。
- 使用本地参考或续写音频会将文件上传至音潮开放平台。只上传有权使用的内容，不要上传不必要的个人信息或机密录音。
- 提交本地音频前，确认当前环境和对话参与者均有权访问该文件。
- 如果怀疑密钥泄露，请立即在音潮开放平台撤销并重新创建。
