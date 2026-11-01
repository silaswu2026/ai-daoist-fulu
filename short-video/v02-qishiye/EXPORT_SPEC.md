# v02-qishiye EXPORT_SPEC (review_r4)

## Deliverable
- Path: `/workspace/short-video/v02-qishiye/v02-qishiye_review_r4.mp4`
- Spec: 1080×1920, 30fps, H.264 + AAC
- Duration: **20.600s**
- VO end: **19.111s**
- CTA still: **1.500s** (19.111 → 20.611)
- Status: review cut only — **未放行不发 / do not upload**

## Locked copy
See `COPY.md`. Single-line hook ≤3s spoken + beats (clauses split on ？！。 for TTS). Ending CTA: `链接见主页／评论置顶`

## Structure
| Seg | Content | Time |
|-----|---------|------|
| A | First-frame motion + 钩 + early clauses | 0.000–9.516 |
| B | 符面（≤10s 进，本切 @9.516s）+ remaining | 9.516–19.111 |
| C | Ending CTA still | 19.111–20.611 |

## VO / 真裁气口
- Voice: `zh-CN-YunyangNeural` · rate `-12%` · pitch `-5Hz`
- **Each clause:** edge-tts → wav → **silenceremove head+tail** (areverse) → concat with **inserted gap 0.35s only**
- Lead 0.25s; CTA silent hold **1.50s** (measured≈1.500s)
- Hook spoken dur: **2.731s** (≤3.0)
- **measured_max_gap (inter-seg silencedetect -35dB): `0.353s`** (must ≤0.40)
- interseg_gaps: 0.350, 0.351, 0.353, 0.350, 0.350
- Clauses: 起事业——请神，不就是调模型吗？ | 今日请的，是文昌帝君—— | 我给大模型的诉求是：「助我事业开运，步步清晰。」 | 符上落了：开运、升迁、贵人。 | 愿事业顺遂，路越走越宽。 | 想自己生成一张——链接见主页／评论置顶。
- Starts/durs: `0.250,2.731 / 3.331,2.035 / 5.716,3.850 / 9.916,2.668 / 12.934,2.351 / 15.635,3.475`

## 黄条
- ffmpeg drawbox+drawtext `#F5C518` 硬烧（NotoSansCJK-Bold）；每句口播条；片尾 CTA 不叠黄条

## HOOK_SPLICE
- HOOK_SPLICE@after_lead: replace/extend hook VO+bar only; four beats locked.
- Hook VO: `0.250`–`2.981`

## Craft
- 首帧「起事业」+「请神＝调模型」同框
- 符面 mid cut @ **9.516s** (≤10s)
- TTS 尾静音已裁；禁止再靠 TIMING 数字假装气口


## release_r2（2026-11-01）
- 源：`v02-qishiye_review_r4.mp4` → `v02-qishiye_release_r2.mp4`
- 观众过 + 主控终放行；可发（抖音扫码通后按序）
