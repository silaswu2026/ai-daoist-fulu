# v03-qifacai EXPORT_SPEC (review_r3)

## Deliverable
- Path: `/workspace/short-video/v03-qifacai/v03-qifacai_review_r3.mp4`
- Spec: 1080×1920, 30fps, H.264 + AAC
- Duration: **21.033s**
- VO end: **19.546s**
- CTA still: **1.500s** (19.546 → 21.046)
- Status: review cut only — **未放行不发 / do not upload**

## Locked copy
See `COPY.md`. Single-line hook ≤3s spoken + beats (clauses split on ？！。 for TTS). Ending CTA: `链接见主页／评论置顶`

## Structure
| Seg | Content | Time |
|-----|---------|------|
| A | First-frame motion + 钩 + early clauses | 0.000–9.840 |
| B | 符面（≤10s 进，本切 @9.840s）+ remaining | 9.840–19.546 |
| C | Ending CTA still | 19.546–21.046 |

## VO / 真裁气口
- Voice: `zh-CN-YunyangNeural` · rate `-12%` · pitch `-5Hz`
- **Each clause:** edge-tts → wav → **silenceremove head+tail** (areverse) → concat with **inserted gap 0.35s only**
- Lead 0.25s; CTA silent hold **1.50s** (measured≈1.500s)
- Hook spoken dur: **2.867s** (≤3.0)
- **measured_max_gap (inter-seg silencedetect -35dB): `0.352s`** (must ≤0.40)
- interseg_gaps: 0.350, 0.350, 0.352, 0.350, 0.350
- Clauses: 起发财——付 Token，不就是请福吗？ | 今日请的，是财神赵公明—— | 我给大模型的诉求是：「助我财运畅通，进账有路。」 | 符上落了：进宝、开源、不漏财。 | 愿财源稳进，不慌不贪。 | 想自己生成一张——链接见主页／评论置顶。
- Starts/durs: `0.250,2.867 / 3.467,2.042 / 5.858,4.031 / 10.240,3.070 / 13.660,2.061 / 16.071,3.475`

## 黄条
- ffmpeg drawbox+drawtext `#F5C518` 硬烧（NotoSansCJK-Bold）；每句口播条；片尾 CTA 不叠黄条

## HOOK_SPLICE
- HOOK_SPLICE@after_lead: replace/extend hook VO+bar only; four beats locked.
- Hook VO: `0.250`–`3.117`

## Craft
- 首帧「起发财」+「请神＝调模型」同框
- 符面 mid cut @ **9.840s** (≤10s)
- TTS 尾静音已裁；禁止再靠 TIMING 数字假装气口


## release_r2（2026-11-01）
- 源：`v03-qifacai_review_r3.mp4` → `v03-qifacai_release_r2.mp4`
- 观众过 + 主控终放行；可发（抖音扫码通后按序）
