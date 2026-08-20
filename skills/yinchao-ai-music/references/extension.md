# 歌曲续写与延长

音频来源和上传告知要求与参考音频创作相同：支持本地 MP3/WAV、公网音频地址或音潮歌曲 ID；本地文件最大 10MB。

未指定续写位置时从结尾继续：

```bash
python3 scripts/yinchao_music.py extend \
  --audio-file "/绝对路径/origin.mp3" \
  --lyric "接下来演唱的歌词"
```

指定位置时传入秒数：

```bash
python3 scripts/yinchao_music.py extend \
  --audio-url "https://example.com/origin.mp3" \
  --extend-at 60 \
  --lyric "接下来演唱的歌词"
```

优先使用用户提供的续写歌词。只有用户明确希望延长纯音乐时才省略歌词；无法判断续写内容时简短询问。用户明确只要一首时添加 `--n 1`。
