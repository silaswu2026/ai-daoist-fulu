# v05-hufumu EXPORT_SPEC (review_r4)

## Deliverable
- Path: `/workspace/short-video/v05-hufumu/v05-hufumu_review_r4.mp4`
- Spec: 1080×1920, 30fps, H.264 + AAC
- Duration: **20.167s**
- VO end: **18.682s**
- CTA still: **1.500s** (18.682 → 20.182)
- Status: review cut only — **未放行不发 / do not upload**

## Locked copy
See `COPY.md`. Hook: `护父母——一纸符，就是一次调模型。`
Beats split on **？！。、** into separate TTS clauses (r3 fail was unsplit ④ ~6.4s with 0.796s mid silence).

## Clauses
- 护父母——一纸符，就是一次调模型。
- 今日请的，是慈航道人——
- 我给大模型的诉求是：「护我双亲安康，岁岁平安。」
- 符上落了：慈安、
- 延年、
- 家宁。
- 愿父母康健，福报绵长。
- 想自己生成一张——链接见主页／评论置顶。

## VO / 真裁气口
- Each clause: edge-tts → wav → silenceremove head+tail → concat with inserted gap **0.35s**
- Lead 0.25s; CTA silent **1.50s**
- Hook dur: **2.776s**
- **Gate:** `silencedetect=noise=-35dB:d=0.35` whole file — no mid silence >0.40 except CTA≈1.5
- measured_max_mid_silence: **0.357s**
- measured_cta_silence: **1.473s**
- silence_list: `[{"start": 3.026, "end": 3.376, "dur": 0.35}, {"start": 5.221, "end": 5.571, "dur": 0.35}, {"start": 9.529, "end": 9.879, "dur": 0.35}, {"start": 11.186, "end": 11.536, "dur": 0.35}, {"start": 11.876, "end": 12.226, "dur": 0.35}, {"start": 12.489, "end": 12.842, "dur": 0.353}, {"start": 13.818, "end": 14.176, "dur": 0.357}, {"start": 14.856, "end": 15.207, "dur": 0.351}, {"start": 18.682, "end": 20.155, "dur": 1.473}]`

## Structure
| Seg | Time |
|-----|------|
| A firstframe motion | 0.000–9.479 |
| B 符面 | 9.479–18.682 |
| C CTA | 18.682–20.182 |

## 黄条
drawbox+drawtext `#F5C518` per clause; CTA no bar.

## Files
- `TIMING_r4.txt` (= `TIMING.txt`)
- `rebuild-r4/meta.json`


## release_r2（2026-11-01）
- 源：`v05-hufumu_review_r4.mp4` → `v05-hufumu_release_r2.mp4`
- 观众过 + 主控终放行；可发（抖音扫码通后按序 EP0→v02…→v08）
