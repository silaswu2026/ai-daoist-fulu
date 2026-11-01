#!/usr/bin/env python3
"""v06/v07 review_r2: single-line hook + silenceremove + gap0.35 + 符面≤10s + silencedetect."""
from __future__ import annotations
import json, re, subprocess, sys
from pathlib import Path

ROOT = Path("/workspace/short-video")
VENV_TTS = ROOT / ".venv/bin/edge-tts"
VOICE = "zh-CN-YunyangNeural"
RATE = "-12%"
PITCH = "-5Hz"
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
LEAD = 0.25
GAP = 0.35
CTA = 1.50
BAR = "0xF5C518"

JOBS = [
    dict(
        id="v06-hujiaren",
        out="v06-hujiaren_review_r2.mp4",
        hook="护家人——请神，不就是调模型吗？",
        beats=[
            "今日请的，是灶神——",
            "我给大模型的诉求是：「护我一家和顺，出入平安。」",
            "符上落了：家宁、和合、平安。",
            "愿家人团圆，宅气清安。想自己生成一张——链接见主页／评论置顶。",
        ],
        lines=[
            ["护家人——请神，不就是调模型吗？"],
            ["今日请的，是灶神——"],
            ["我给大模型的诉求是：", "「护我一家和顺，出入平安。」"],
            ["符上落了：家宁、和合、平安。"],
            ["愿家人团圆，宅气清安。", "想自己生成一张——链接见主页／评论置顶。"],
        ],
        segA="segA_r2_src.mp4",
        segB="segB_r2_src.mp4",
        ending="ending-cta.jpg",
    ),
    dict(
        id="v07-huairen",
        out="v07-huairen_review_r2.mp4",
        hook="护爱人——请神，不就是调模型吗？",
        beats=[
            "今日请的，是月老——",
            "我给大模型的诉求是：「护我与所爱，心意相通，长久相守。」",
            "符上落了：同心、和合、长久。",
            "愿两心相守，细水长流。想自己生成一张——链接见主页／评论置顶。",
        ],
        lines=[
            ["护爱人——请神，不就是调模型吗？"],
            ["今日请的，是月老——"],
            ["我给大模型的诉求是：", "「护我与所爱，心意相通，长久相守。」"],
            ["符上落了：同心、和合、长久。"],
            ["愿两心相守，细水长流。", "想自己生成一张——链接见主页／评论置顶。"],
        ],
        segA="segA_r2_src.mp4",
        segB="segB_r2_src.mp4",
        ending="ending-cta.jpg",
    ),
]


def run(cmd, **kw):
    print("+", " ".join(map(str, cmd))[:220])
    subprocess.check_call(cmd, **kw)


def probe(p: Path) -> float:
    return float(
        subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
            text=True,
        ).strip()
    )


def edge_tts(text: str, out: Path):
    run([str(VENV_TTS), "--voice", VOICE, f"--rate={RATE}", f"--pitch={PITCH}", "--text", text, "--write-media", str(out)])


def to_wav_trimmed(mp3: Path, wav: Path):
    """Decode + strip leading/trailing silence (fixes fake gaps from TTS tail)."""
    # stop_periods=-1 strips all trailing silence periods; keep tiny pad 0.02
    af = (
        "silenceremove=start_periods=1:start_duration=0.02:start_threshold=-40dB:"
        "stop_periods=-1:stop_duration=0.05:stop_threshold=-40dB,"
        "aformat=sample_fmts=s16:sample_rates=44100:channel_layouts=mono"
    )
    run(
        ["ffmpeg", "-y", "-i", str(mp3), "-af", af, "-c:a", "pcm_s16le", str(wav)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def make_silence(path: Path, sec: float):
    run(
        [
            "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
            "-t", f"{sec:.3f}", "-c:a", "pcm_s16le", str(path),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def concat_wavs(parts: list[Path], out: Path):
    lst = out.with_suffix(".txt")
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in parts))
    run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c:a", "pcm_s16le", str(out)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def wav_to_m4a(wav: Path, m4a: Path):
    run(
        ["ffmpeg", "-y", "-i", str(wav), "-c:a", "aac", "-b:a", "192k", str(m4a)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def fit_segment(src: Path, dur: float, dst: Path):
    """Scale to 1080x1920@30 and fit exact duration (loop/trim)."""
    tmp = dst.with_suffix(".src.mp4")
    run(
        [
            "ffmpeg", "-y", "-stream_loop", "-1", "-i", str(src), "-t", f"{dur:.3f}", "-an",
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,format=yuv420p",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", str(tmp),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    # exact trim
    run(
        ["ffmpeg", "-y", "-i", str(tmp), "-t", f"{dur:.3f}", "-c:v", "copy", "-an", str(dst)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    tmp.unlink(missing_ok=True)


def esc_text(s: str) -> str:
    return s.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'").replace("%", "%%")


def build_vf(starts, durs, lines_list) -> str:
    parts = []
    for s, d, lines in zip(starts, durs, lines_list):
        e = s + d
        enable = f"between(t\\,{s:.3f}\\,{e:.3f})"
        if len(lines) == 1:
            y, h = 1540, 118
            parts.append(f"drawbox=x=65:y={y}:w=950:h={h}:color={BAR}@1:t=fill:enable='{enable}'")
            parts.append(
                f"drawtext=fontfile={FONT}:text='{esc_text(lines[0])}':fontcolor=black:fontsize=46:"
                f"x=(w-text_w)/2:y={y}+36:enable='{enable}'"
            )
        else:
            y, h = 1480, 198
            parts.append(f"drawbox=x=65:y={y}:w=950:h={h}:color={BAR}@1:t=fill:enable='{enable}'")
            parts.append(
                f"drawtext=fontfile={FONT}:text='{esc_text(lines[0])}':fontcolor=black:fontsize=42:"
                f"x=(w-text_w)/2:y={y}+36:enable='{enable}'"
            )
            parts.append(
                f"drawtext=fontfile={FONT}:text='{esc_text(lines[1])}':fontcolor=black:fontsize=42:"
                f"x=(w-text_w)/2:y={y}+112:enable='{enable}'"
            )
    return ",".join(parts)


def silencedetect(path: Path, noise="-35dB", d=0.40) -> list[tuple[float, float]]:
    """Return list of (silence_start, silence_end) for gaps longer than d."""
    proc = subprocess.run(
        ["ffmpeg", "-i", str(path), "-af", f"silencedetect=noise={noise}:d={d}", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    err = proc.stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", err)]
    ends = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", err)]
    # pair them
    out = []
    for i, st in enumerate(starts):
        en = ends[i] if i < len(ends) else None
        out.append((st, en))
    return out, err


def rebuild(job: dict) -> dict:
    folder = ROOT / job["id"]
    work = folder / "rebuild-r2"
    work.mkdir(exist_ok=True)
    vo_dir = folder / "vo_r2"
    vo_dir.mkdir(exist_ok=True)

    texts = [job["hook"], *job["beats"]]
    names = ["hook", "s01", "s02", "s03", "s04"]
    wavs, durs = [], []
    for name, text in zip(names, texts):
        mp3 = vo_dir / f"{name}.mp3"
        wav = vo_dir / f"{name}.wav"
        edge_tts(text, mp3)
        to_wav_trimmed(mp3, wav)
        d = probe(wav)
        wavs.append(wav)
        durs.append(d)
        print(f"  {name}: {d:.3f}s — {text}")

    if durs[0] > 3.05:
        # speed up hook only to ≤3.0s
        target = 2.95
        factor = durs[0] / target
        sped = vo_dir / "hook_sped.wav"
        run(
            ["ffmpeg", "-y", "-i", str(wavs[0]), "-af", f"atempo={min(factor, 1.5):.4f}", "-c:a", "pcm_s16le", str(sped)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        # re-trim after speed
        to_wav_trimmed(sped, wavs[0])  # atempo output is wav; silenceremove via ffmpeg from wav
        # direct trim from sped:
        run(
            [
                "ffmpeg", "-y", "-i", str(sped), "-af",
                "silenceremove=start_periods=1:start_duration=0.02:start_threshold=-40dB:"
                "stop_periods=-1:stop_duration=0.05:stop_threshold=-40dB",
                "-c:a", "pcm_s16le", str(wavs[0]),
            ],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        durs[0] = probe(wavs[0])
        print(f"  hook sped -> {durs[0]:.3f}s")

    lead = vo_dir / "lead_p.wav"
    gap = vo_dir / "gap_p.wav"
    make_silence(lead, LEAD)
    make_silence(gap, GAP)

    parts = [lead, wavs[0]]
    for w in wavs[1:]:
        parts.append(gap)
        parts.append(w)
    vo_wav = work / "vo_full.wav"
    concat_wavs(parts, vo_wav)
    vo_end = probe(vo_wav)

    # pad CTA silence onto audio for mux
    vo_pad_wav = work / "vo_padded.wav"
    run(
        ["ffmpeg", "-y", "-i", str(vo_wav), "-af", f"apad=pad_dur={CTA}", "-t", f"{vo_end+CTA:.3f}", "-c:a", "pcm_s16le", str(vo_pad_wav)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    vo_m4a = folder / "vo_r2_padded.m4a"
    wav_to_m4a(vo_pad_wav, vo_m4a)
    wav_to_m4a(vo_wav, folder / "vo_r2_full.m4a")

    starts = []
    t = LEAD
    starts.append(t)
    t += durs[0]
    for i in range(1, 5):
        t += GAP
        starts.append(t)
        t += durs[i]
    assert abs(t - vo_end) < 0.08, (t, vo_end)

    (folder / "vo_starts_r2.txt").write_text("\n".join(f"{s:.3f},{d:.3f}" for s, d in zip(starts, durs)) + "\n")
    (folder / "vo_total_r2.txt").write_text(f"{vo_end:.3f}\n")

    # 符面 ≤10s: cut to mid no later than 10.0, and ~0.4s before ③
    beat3 = starts[3]
    mid_cut = min(10.0, max(starts[2] + durs[2] * 0.5, beat3 - 0.40))
    mid_cut = min(mid_cut, 10.0)
    # also ensure after ① mostly done
    mid_cut = max(mid_cut, min(starts[1] + durs[1], 10.0))
    if mid_cut > 10.0:
        mid_cut = 10.0
    seg_a = mid_cut
    seg_b = vo_end - mid_cut
    total = vo_end + CTA

    timing = (
        f"review_r2 timing (silenceremove)\n"
        f"lead={LEAD:.3f} gap={GAP:.3f} CTA={CTA:.3f}\n"
        f"hook start={starts[0]:.3f} dur={durs[0]:.3f} end={starts[0]+durs[0]:.3f}\n"
        f"① start={starts[1]:.3f} dur={durs[1]:.3f} end={starts[1]+durs[1]:.3f}\n"
        f"② start={starts[2]:.3f} dur={durs[2]:.3f} end={starts[2]+durs[2]:.3f}\n"
        f"③ start={starts[3]:.3f} dur={durs[3]:.3f} end={starts[3]+durs[3]:.3f}\n"
        f"④ start={starts[4]:.3f} dur={durs[4]:.3f} end={starts[4]+durs[4]:.3f}\n"
        f"VO_END={vo_end:.3f}\nCTA_START={vo_end:.3f} CTA_DUR={CTA:.3f} CTA_END={total:.3f}\n"
        f"TOTAL≈{total:.3f}\nMID_CUT={mid_cut:.3f} (符面≤10s)\nA_DUR={seg_a:.3f} B_DUR={seg_b:.3f}\n"
        f"HOOK_SPLICE@after_lead: replace/extend hook VO+bar only; four beats locked.\n"
    )
    (folder / "TIMING_r2.txt").write_text(timing)
    print(timing)

    segA = work / "segA_fit.mp4"
    segB = work / "segB_fit.mp4"
    segC = work / "segC_cta.mp4"
    fit_segment(folder / job["segA"], seg_a, segA)
    fit_segment(folder / job["segB"], seg_b, segB)
    run(
        [
            "ffmpeg", "-y", "-loop", "1", "-i", str(folder / job["ending"]),
            "-t", f"{CTA:.3f}",
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,format=yuv420p",
            "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", str(segC),
        ],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

    cl = work / "concat.txt"
    cl.write_text(f"file '{segA.resolve()}'\nfile '{segB.resolve()}'\nfile '{segC.resolve()}'\n")
    concat_raw = work / "concat_raw.mp4"
    run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(cl),
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-r", "30", "-pix_fmt", "yuv420p",
         "-movflags", "+faststart", str(concat_raw)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

    vf = build_vf(starts, durs, job["lines"])
    (work / "bars.vf").write_text(vf)
    tmp = work / "review_tmp.mp4"
    out = folder / job["out"]
    run(
        [
            "ffmpeg", "-y",
            "-i", str(concat_raw),
            "-i", str(vo_m4a),
            "-filter_complex", f"[0:v]{vf}[v]",
            "-map", "[v]", "-map", "1:a",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-shortest", "-r", "30",
            "-movflags", "+faststart", str(tmp),
        ],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    dur = probe(tmp)
    tmp.replace(out)

    # silencedetect QA on final (and on vo_full)
    gaps_final, _ = silencedetect(out, noise="-35dB", d=0.45)
    gaps_vo, _ = silencedetect(folder / "vo_r2_full.m4a", noise="-35dB", d=0.45)
    # Expected: only lead(~0.25) and CTA(~1.5) and maybe tiny; inter-beat should be ~0.35 so d=0.45 should NOT flag them
    print("silencedetect final (>0.45s):", gaps_final)
    print("silencedetect vo_full (>0.45s):", gaps_vo)

    # Fail if any silence between 0.5 and vo_end-0.1 longer than 0.45 (false breath)
    bad = []
    for st, en in gaps_final:
        if st is None:
            continue
        if 0.5 <= st <= (vo_end - 0.2):
            bad.append((st, en))
    if bad:
        raise SystemExit(f"{job['id']} FAIL false gaps: {bad}")

    meta = {
        "starts": starts, "durs": durs, "vo_end": vo_end, "cta": CTA, "total": dur,
        "mid_cut": mid_cut, "hook": job["hook"], "gaps_final": gaps_final, "gaps_vo": gaps_vo,
    }
    (work / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))

    rd = folder / "review-r2"
    rd.mkdir(exist_ok=True)
    for label, ss in [
        ("f_hook", starts[0] + min(0.8, durs[0] * 0.4)),
        ("f_mid", mid_cut + 0.3),
        ("f_b3", starts[3] + 0.4),
        ("f_cta", vo_end + 0.3),
    ]:
        run(
            ["ffmpeg", "-y", "-ss", f"{ss:.3f}", "-i", str(out), "-update", "1", "-frames:v", "1", str(rd / f"{label}.jpg")],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )

    # EXPORT_SPEC
    export = f"""# {job['id']} EXPORT_SPEC (review_r2)

## Deliverable
- Path: `/workspace/short-video/{job['id']}/{job['out']}`
- Spec: 1080×1920, 30fps, H.264 + AAC
- Duration: **{dur:.3f}s**
- VO end: **{vo_end:.3f}s**
- CTA still: **{CTA:.3f}s** ({vo_end:.3f} → {vo_end+CTA:.3f})
- Status: review cut only — **未放行不发 / do not upload**

## Locked copy
See `COPY.md`. 单句钩（第二句不占钩）. Ending CTA exact: `链接见主页／评论置顶`

## Structure
| Seg | Content | Time |
|-----|---------|------|
| A | First-frame + 单句钩 + ①②（至符面切点） | 0.000–{mid_cut:.3f} |
| B | 符中帧（≤10s 进）+ ③④ | {mid_cut:.3f}–{vo_end:.3f} |
| C | Ending CTA still | {vo_end:.3f}–{vo_end+CTA:.3f} |

## VO / 节奏包
- Voice: `zh-CN-YunyangNeural` via `/workspace/short-video/.venv/bin/edge-tts`
- Rate `-12%`, pitch `-5Hz`
- Lead {LEAD:.2f}s; gaps **{GAP:.2f}s** (≤0.40); CTA silent hold **{CTA:.2f}s** (≤1.50)
- **每段 silenceremove 裁尾后再拼显式 gap**（禁 TTS 假气口）
- Starts/durs (hook,①,②,③,④): `{' / '.join(f'{s:.3f},{d:.3f}' for s,d in zip(starts,durs))}`
- Files: `vo_r2/hook + s01–s04` → `vo_r2_full.m4a` → `vo_r2_padded.m4a`

## 黄条
- ffmpeg **drawbox+drawtext** 硬烧 `#F5C518`；钩 + 四段；片尾 CTA 画面自带文案，不叠黄条
- 1 行：y=1540 h=118；2 行：y=1480 h=198；x=65 w=950

## HOOK_SPLICE（开场钩插拔点）
- HOOK_SPLICE@after_lead: replace/extend hook VO+bar only; four beats locked.
- Timeline marker: hook VO occupies `{starts[0]:.3f}`–`{starts[0]+durs[0]:.3f}`

## Craft
- 单句钩 ≤3s；符面 mid_cut={mid_cut:.3f}s（≤10）
- ④ 结束立刻接 CTA；交前 silencedetect 自检通过
"""
    (folder / "EXPORT_SPEC.md").write_text(export)
    print(job["id"], "OK", dur, "vo_end", vo_end, "mid", mid_cut)
    return meta


def main():
    results = {}
    for job in JOBS:
        print("====", job["id"], "====")
        results[job["id"]] = rebuild(job)
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk in ("vo_end", "total", "mid_cut", "durs", "starts", "gaps_final")} for k, v in results.items()}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
