# 观众节奏包（SSOT · 2026-11-01）

观众审 EP0～v05 打回后锁定。生成 / 返工一律按此包；**未过观众不放行、不上传**。

## 硬指标
| 项 | 上限 | 本包取值 |
|----|------|----------|
| 段间气口（钩↔①↔②↔③↔④） | ≤0.40s | **0.35s** |
| 片尾 CTA 静音静帧 | ≤1.50s | **1.50s** |
| 片头 lead | 短 | **0.25s** |
| 中段空挂 / 段间长静音 | **禁止** | — |
| 口播④ 结束后 | **立刻**切 CTA | 无垫静音再挂中帧 |

## 结构（系列符条）
1. **前钩（顿悟）** — COPY「前3秒顿悟钩」；可略超 3s（以定稿句为准）
2. **四段主干** — ①请神 ②诉求 ③符上落了 ④愿 + CTA 口播占位
3. **片尾静帧** — 画面自带「链接见主页／评论置顶」；不叠黄条；≤1.5s

## 画面切点
- **A**：首帧轻动效，覆盖 钩 + ① + 大半②
- **B（符面更早炸）**：在 ③「符上落了」开始前约 **0.40s** 切到符中帧（不得晚于 ③ start）
- **C**：VO 结束帧立刻接 CTA 静帧 1.5s

## 黄条
- 钩 + 四段均烧黄条（`#F5C518` / 深字）
- 实现：ffmpeg **drawbox+drawtext**（`NotoSansCJK-Bold.ttc`）；ASS 字体名在本机不可靠，勿用
- 四段文案与原交稿一致；钩随最新 COPY
- 片尾不叠黄条

## HOOK_SPLICE（开场钩插拔）
各 folder `EXPORT_SPEC.md` / `TIMING.txt` 标了：

`HOOK_SPLICE@after_lead: replace/extend hook VO+bar only; four beats locked.`

- 时间线：`vo_starts.txt` 第 1 行 = hook（start,dur）；其后四行 = ①②③④
- 换钩：只重生成 `vo/hook.*` + 对应 ASS 第一条；若 hook 时长变了，按本包 **gap=0.35** 重拼 `vo_full` 并重算 mid_cut / CTA
- **不要**为了换钩改四段定稿词

## VO 工具
- `edge-tts` · `zh-CN-YunyangNeural` · rate `-12%` · pitch `-5Hz`
- 脚本参考：`series-template/rebuild_pacing_v02_v05.py`

## 验收三问（观众）
1. 首帧 1s 内：符/道×AI 同框，想点？
2. 钩够狠？（顿悟句砸前段）
3. 看完热血 / 想点链接？平铺说明书 + 拖气口 = **不过**

## 本包已应用
- `v02-qishiye_review_r3.mp4`
- `v03-qifacai_review_r2.mp4`
- `v04-shenti-pingan_review_r2.mp4`
- `v05-hufumu_review_r2.mp4`

## 2026-11-01 假气口事故（必修）
TIMING 写 gap=0.35 不够：edge-tts 段尾自带静音，拼接后实测段间~1.3s。
**交核前强制：**
1. 每段 VO `silenceremove` 裁头尾
2. 再插入显式 gap≤0.35
3. `silencedetect` 实测 max gap≤0.40 写入 EXPORT_SPEC
4. 单句钩口播≤3s；第二句不占钩
5. 片尾静音≤1.5；符面≤10s 进
