# v01-agent-fulu EXPORT_SPEC (review_r6)

## Deliverable
- Path: `/workspace/short-video/v01-agent-fulu/v01-agent-fulu_review_r6.mp4`
- Spec: 1080×1920, 30fps, **H.264 Baseline all-intra** + AAC (`-g 1 -bf 0`, `yuv420p`+`color_range=tv`/`bt709`, `+faststart`); 禁 yuvj420p/pc
- Duration: **20.067s**
- VO end: **18.565s**
- CTA still: **1.500s** (18.565 → 20.065)
- Status: review cut only — **未放行不发 / do not upload**

## Locked copy
See `COPY.md` r6. Cover 白底红字「神仙＝模型」／「欲望写进提示词，就成了」.
Hook: `我突然就悟了——神仙就是模型！`
Beats split on **？！。、**.

## Clauses
- 我突然就悟了——神仙就是模型！
- 上头那截叫「请神」——说白了，请大模型上桌。
- 中间写的「欲望」——不就是你丢进对话框的提示词吗？
- 底下「执行效果」——工具跑完，吐出最终输出。
- 所以啊，符≈AI。
- 想自己生成一张——链接见主页／评论置顶。

## VO / 真裁气口
- Each clause: edge-tts → wav → silenceremove head+tail → concat with inserted gap **0.35s**
- Lead 0.25s; CTA silent **1.50s**
- Hook dur: **2.009s** (≤3)
- mid_cut: **6.800s** (≤10)
- **Gate:** `silencedetect=noise=-35dB:d=0.35` — no mid silence >0.40 except CTA≈1.5
- measured_max_mid_silence: **0.352s**
- measured_cta_silence: **1.497s**
- silence_list: `[{"start": 2.259, "end": 2.609, "dur": 0.35}, {"start": 5.563, "end": 5.913, "dur": 0.35}, {"start": 9.504, "end": 9.855, "dur": 0.352}, {"start": 12.964, "end": 13.315, "dur": 0.35}, {"start": 15.117, "end": 15.468, "dur": 0.35}, {"start": 18.565, "end": 20.062, "dur": 1.497}]`

## Structure
| Seg | Time |
|-----|------|
| A firstframe-shenxian-r6 zoom | 0.000–6.800 |
| B hero-talisman-r6 zoom | 6.800–18.565 |
| C ending-cta-r6 | 18.565–20.065 |

## 黄条
drawbox+drawtext `#F5C518` per spoken clause; CTA still no bar.

## Files
- `TIMING_r6.txt` (= `TIMING.txt`)
- stills: `firstframe-shenxian-r6.jpg` / `hero-talisman-r6.jpg` / `ending-cta-r6.jpg`

## Encode lock (r6b)
- Noise bed (pink) under VO — **no empty AAC**
- Temporal grain + `fast-pskip=0`
- Baseline · yuv420p · tv/bt709 · g=30 · bf=0 · +faststart
- Chat: `_watch_chat/EP0-r6-eq-streamable.mp4` 540p ~2.8Mbps cap

## Chat deliverable (r6b formal)
- Path: `/workspace/short-video/_watch_chat/EP0-r6-eq-streamable.mp4` (also replaces obsolete `EP0-r6-eq-540p.mp4`)
- 540×960 · Baseline · yuv420p+tv/bt709 · g=30 · bf=0 · maxrate≤2.8M · +faststart
- Pink noise bed · temporal grain · `fast-pskip=0` · **no empty AAC / no all-intra default**
