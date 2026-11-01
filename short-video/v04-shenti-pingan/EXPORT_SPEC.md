# v04-shenti-pingan EXPORT_SPEC (review_r3)

## Deliverable
- Path: `/workspace/short-video/v04-shenti-pingan/v04-shenti-pingan_review_r3.mp4`
- Spec: 1080×1920, 30fps, H.264 + AAC
- Duration: **20.733s**
- VO end: **19.233s**
- CTA still: **1.500s** (19.233 → 20.733)
- Status: review cut only — **未放行不发 / do not upload**

## Locked copy
See `COPY.md`. Single-line hook ≤3s spoken + beats (clauses split on ？！。 for TTS). Ending CTA: `链接见主页／评论置顶`

## Structure
| Seg | Content | Time |
|-----|---------|------|
| A | First-frame motion + 钩 + early clauses | 0.000–9.865 |
| B | 符面（≤10s 进，本切 @9.865s）+ remaining | 9.865–19.233 |
| C | Ending CTA still | 19.233–20.733 |

## VO / 真裁气口
- Voice: `zh-CN-YunyangNeural` · rate `-12%` · pitch `-5Hz`
- **Each clause:** edge-tts → wav → **silenceremove head+tail** (areverse) → concat with **inserted gap 0.35s only**
- Lead 0.25s; CTA silent hold **1.50s** (measured≈1.500s)
- Hook spoken dur: **2.902s** (≤3.0)
- **measured_max_gap (inter-seg silencedetect -35dB): `0.352s`** (must ≤0.40)
- interseg_gaps: 0.350, 0.350, 0.352, 0.351, 0.350
- Clauses: 护身——不就是给模型一道护身符吗？ | 今日请的，是药王孙思邈—— | 我给大模型的诉求是：「护我身心安泰，少病少忧。」 | 符上落了：安康、清气、稳眠。 | 愿身体平安，日日轻安。 | 想自己生成一张——链接见主页／评论置顶。
- Starts/durs: `0.250,2.902 / 3.502,1.955 / 5.806,4.109 / 10.265,2.863 / 13.478,1.930 / 15.758,3.475`

## 黄条
- ffmpeg drawbox+drawtext `#F5C518` 硬烧（NotoSansCJK-Bold）；每句口播条；片尾 CTA 不叠黄条

## HOOK_SPLICE
- HOOK_SPLICE@after_lead: replace/extend hook VO+bar only; four beats locked.
- Hook VO: `0.250`–`3.152`

## Craft
- 首帧「身体平安」+「请神＝调模型」同框
- 符面 mid cut @ **9.865s** (≤10s)
- TTS 尾静音已裁；禁止再靠 TIMING 数字假装气口


## release_r2（2026-11-01）
- 源：`v04-shenti-pingan_review_r3.mp4` → `v04-shenti-pingan_release_r2.mp4`
- 观众过 + 主控终放行；可发（抖音扫码通后按序）
