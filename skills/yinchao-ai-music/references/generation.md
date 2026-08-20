# 完整歌曲与歌词创作

## 生成完整歌曲

根据用户需求整理提示词后运行：

```bash
python3 scripts/yinchao_music.py song \
  --prompt "整理后的创作提示"
```

用户提供现成歌词时原样传入：

```bash
python3 scripts/yinchao_music.py song \
  --prompt "曲风、节奏、情绪、配器和演唱要求" \
  --lyric "用户提供的完整歌词"
```

提示词和歌词至少提供一项。提示词最多 1000 个字符，歌词最多 3000 个字符。用户明确只要一首时添加 `--n 1`；否则默认生成两个版本。

## 只写歌词

仅在用户明确不要音频时运行：

```bash
python3 scripts/yinchao_music.py lyrics \
  --prompt "整理后的歌词创作提示"
```

歌词可使用 `[INTRO]`、`[VERSE]`、`[CHORUS]`、`[BRIDGE]`、`[BREAK]`、`[OUTRO]` 等结构标签。不要为了生成歌曲而先单独调用歌词接口；完整歌曲结果本身已包含歌词。
