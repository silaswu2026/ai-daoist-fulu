# v08-hupengyou EXPORT_SPEC (review_r4)

## Deliverable
- Path: `/workspace/short-video/v08-hupengyou/v08-hupengyou_review_r4.mp4`
- Spec: 1080×1920, 30fps, H.264 + AAC
- Duration: **19.567s**
- VO end: **18.054s**
- CTA still: **1.500s** (18.054 → 19.554)
- Status: review cut only — **未放行不发 / do not upload**

## Locked copy
See `COPY.md`. Single-line hook「护朋友——请神，不就是调模型吗？」+ four beats. CTA: `链接见主页／评论置顶`

## Structure
| Seg | Content | Time |
|-----|---------|------|
| A | First-frame + 钩 + ①② | 0.000–9.287 |
| B | 符面（≤10s）+ ③④ | 9.287–18.054 |
| C | CTA still | 18.054–19.554 |

## VO / 分句裁尾
- Voice: `zh-CN-YunyangNeural` rate `-12%` pitch `-5Hz`
- **每句按 ？！。、 拆成独立 edge-tts** → silenceremove 头尾 → 显式 gap **0.35s**
- Lead 0.25s; CTA **1.50s**; hook beat dur **2.422s** (≤3)
- mid_cut **9.287s** (符面≤10s)
- Beat starts/durs: `0.250,2.422 / 3.022,1.906 / 5.278,4.059 / 9.687,2.288 / 12.324,5.730`
- Clause count: **8**

## silencedetect 实测（gate: noise=-35dB:d=0.35）
- PASS: no mid silence >0.40s except CTA≈1.5s
- silence_list: `[{"start": 2.67, "end": 3.022, "dur": 0.352}, {"start": 4.927, "end": 5.278, "dur": 0.35}, {"start": 9.336, "end": 9.687, "dur": 0.35}, {"start": 10.733, "end": 11.083, "dur": 0.35}, {"start": 11.263, "end": 11.613, "dur": 0.35}, {"start": 11.974, "end": 12.324, "dur": 0.35}, {"start": 14.247, "end": 14.598, "dur": 0.35}, {"start": 18.054, "end": 19.551, "dur": 1.497}]`

## 黄条
- drawbox+drawtext `#F5C518`；按 beat 粒度（钩+四段）；片尾不叠

## Craft
- 分句消除句内假气口；④「愿…／想自己…」等长句已拆


## release_r2（2026-11-01）
- 源：`v08-hupengyou_review_r4.mp4` → `v08-hupengyou_release_r2.mp4`
- 观众过 + 主控终放行；可发（抖音扫码通后按序 EP0→v02…→v08）
