# v07-huairen EXPORT_SPEC (review_r2)

## Deliverable
- Path: `/workspace/short-video/v07-huairen/v07-huairen_review_r2.mp4`
- Spec: 1080×1920, 30fps, H.264 + AAC
- Duration: **18.000s**
- VO end: **16.525s**
- CTA still: **1.500s** (16.525 → 18.025)
- Status: review cut only — **未放行不发 / do not upload**

## Locked copy
See `COPY.md`. 单句钩（第二句不占钩）. Ending CTA exact: `链接见主页／评论置顶`

## Structure
| Seg | Content | Time |
|-----|---------|------|
| A | First-frame + 单句钩 + ①②（至符面切点） | 0.000–8.282 |
| B | 符中帧（≤10s 进）+ ③④ | 8.282–16.525 |
| C | Ending CTA still | 16.525–18.025 |

## VO / 节奏包
- Voice: `zh-CN-YunyangNeural` · rate `-12%` · pitch `-5Hz`
- Lead 0.25s; **显式 gap 0.25s**（silenceremove 后拼；实测段间 ≤0.35）; CTA **1.50s**
- Starts/durs: `0.250,2.212 / 2.712,1.346 / 4.308,4.124 / 8.682,2.236 / 11.167,5.358`
- 每段 `silenceremove` 裁尾；交前 `silencedetect` 自检通过

## 黄条
- ffmpeg drawbox+drawtext `#F5C518`；1行 y=1540 h=118；2行 y=1480 h=198；x=65 w=950
- 片尾不叠黄条

## HOOK_SPLICE
- HOOK_SPLICE@after_lead: replace/extend hook VO+bar only; four beats locked.
- hook occupies `0.250`–`2.462`

## Craft
- 单句钩 ≤3s（实际 2.21s）；符面 mid_cut=8.282s（≤10）
- ④ 结束立刻接 CTA；未放行不发


## release_r2（2026-11-01）
- 源：`v07-huairen_review_r2.mp4` → `v07-huairen_release_r2.mp4`
- 观众过 + 主控终放行；可发（抖音扫码通后按序）
