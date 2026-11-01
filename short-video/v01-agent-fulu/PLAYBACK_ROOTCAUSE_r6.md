# 播放卡第一帧 · 根因（2026-11-01）

## 结论
1. **不是**「第一帧后没有媒体包」：ffprobe 显示 0–10s 连续有 V/A 包。
2. **是**源头生成方式问题，被重封装原样带上：
   - 静帧 JPEG → H.264 后出现大量 **17–50 字节空 P 帧**（画面几乎不变时编码器写 skip）。
   - EP0 r6 还误带 **yuvj420p / color_range=pc**（JPEG full range），部分手机解码器只出首帧后卡住。
3. 旧八条 chat 虽是 yuv420p，但同样是静帧链路时仍可能空 P 帧过多，表现为「停在封面」。

## 正确做法（回源头）
- 生成时强制 `format=yuv420p` + `color_range=tv`（bt709）
- 聊天试看用 **all-intra**（`keyint=1` / 每帧 I 帧）或保证每秒实运动、P 帧体积正常
- `+faststart`；禁止只修 moov 不重编码
- 交付：`_watch_chat/EP0-r6-playable.mp4`
