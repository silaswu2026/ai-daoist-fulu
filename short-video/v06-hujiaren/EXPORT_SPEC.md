# v06-hujiaren EXPORT_SPEC (review_r3)

## Deliverable
- Path: `/workspace/short-video/v06-hujiaren/v06-hujiaren_review_r3.mp4`
- Spec: 1080×1920, 30fps, H.264 + AAC
- Duration: **20.067s**
- VO end: **18.572s**
- CTA still: **1.500s** (18.572 → 20.072)
- Status: review cut only — **未放行不发 / do not upload**

## Locked copy
See `COPY.md`. Single-line hook + four beats. Ending CTA exact: `链接见主页／评论置顶`

## Structure
| Seg | Content | Time |
|-----|---------|------|
| A | First-frame motion + 钩 + ①②（至符面切点） | 0.000–8.705 |
| B | 符中帧（≤10s 进）+ ③④ | 8.705–18.572 |
| C | Ending CTA still | 18.572–20.072 |

## VO / 节奏包（真裁尾）
- Voice: `zh-CN-YunyangNeural` via `/workspace/short-video/.venv/bin/edge-tts`
- Rate `-12%`, pitch `-5Hz`
- **每段 silenceremove 裁头尾**（reverse-trick，-40dB；保留句中停顿）后再拼显式 gap
- Lead 0.25s; planned gaps **0.35s** (≤0.40); CTA silent hold **1.50s** (≤1.50)
- Hook dur **2.526s** (≤3.0)
- Starts/durs (hook,①,②,③,④): `0.250,2.526 / 3.126,1.464 / 4.940,3.815 / 9.105,2.767 / 12.223,6.349`
- mid_cut **8.705s** (符面≤10s)

## silencedetect 实测（交核自检）
- max inter-beat gap: **0.35s** (planned 0.35)
- inter-beat gaps: `[0.35, 0.35, 0.35, 0.35]`
- CTA silence: **1.49s** (planned 1.5)
- all silences ≥0.20s: `[{"start": 0.0, "end": 0.25, "dur": 0.25}, {"start": 0.739, "end": 0.993, "dur": 0.254}, {"start": 1.525, "end": 1.751, "dur": 0.226}, {"start": 2.776, "end": 3.126, "dur": 0.35}, {"start": 3.825, "end": 4.073, "dur": 0.249}, {"start": 4.59, "end": 4.94, "dur": 0.35}, {"start": 6.478, "end": 6.767, "dur": 0.289}, {"start": 7.764, "end": 8.049, "dur": 0.285}, {"start": 8.755, "end": 9.105, "dur": 0.35}, {"start": 10.472, "end": 10.809, "dur": 0.338}, {"start": 11.299, "end": 11.561, "dur": 0.262}, {"start": 11.873, "end": 12.223, "dur": 0.35}, {"start": 13.116, "end": 13.391, "dur": 0.275}, {"start": 14.257, "end": 15.051, "dur": 0.794}, {"start": 16.434, "end": 16.758, "dur": 0.323}, {"start": 17.808, "end": 18.014, "dur": 0.206}, {"start": 18.572, "end": 20.062, "dur": 1.49}]`

## 黄条
- ffmpeg **drawbox+drawtext** 硬烧 `#F5C518`；钩 + 四段；片尾 CTA 不叠黄条
- 1 行：y=1540 h=118；2 行：y=1480 h=198；x=65 w=950

## HOOK_SPLICE
- HOOK_SPLICE@after_lead: replace/extend hook VO+bar only; four beats locked.
- hook VO occupies `0.250`–`2.776`

## Craft
- 毛笔字首帧「护家人」+「请神＝调模型」
- 符面冲击 ≤10s：mid cut @ 8.705s
- ④ 结束立刻接 CTA；假气口已用 silenceremove 消除


## release_r2（2026-11-01）
- 源：`v06-hujiaren_review_r2.mp4` → `v06-hujiaren_release_r2.mp4`
- 观众过 + 主控终放行；可发（抖音扫码通后按序）
