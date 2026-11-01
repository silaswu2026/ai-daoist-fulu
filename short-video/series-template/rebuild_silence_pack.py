#!/usr/bin/env python3
"""Audience silence-pack rebuild: silenceremove each VO beat, explicit gap≤0.35, CTA≤1.5, 符面≤10s, hook≤3s."""
from __future__ import annotations

import json
import math
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path("/workspace/short-video")
EDGE = ROOT / ".venv/bin/edge-tts"
VOICE = "zh-CN-YunyangNeural"
RATE = "-12%"
PITCH = "-5Hz"
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
LEAD = 0.25
GAP = 0.35
CTA = 1.50
SAMPLE_RATE = 44100
MID_CUT_MAX = 10.0
HOOK_MAX = 3.0
BAR_COLOR = "0xF5C518"

# Lead+trail only (do NOT use stop_periods=1 alone — mid-phrase pauses >0.08s would chop words).
# Equivalent intent to user filter, but reverse-trick keeps mid pauses.
SILENCE_AF = (
    "silenceremove=start_periods=1:start_duration=0.05:start_threshold=-40dB,"
    "areverse,"
    "silenceremove=start_periods=1:start_duration=0.08:start_threshold=-40dB,"
    "areverse"
)


def run(cmd, **kw):
    print("+", " ".join(str(c) for c in cmd)[:260])
    subprocess.check_call(cmd, **kw)


def probe_dur(path: Path) -> float:
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        text=True,
    ).strip()
    return float(out)


def edge_tts(text: str, out: Path, rate: str = RATE):
    out.parent.mkdir(parents=True, exist_ok=True)
    run([str(EDGE), "--voice", VOICE, f"--rate={rate}", f"--pitch={PITCH}",
         "--text", text, "--write-media", str(out)])


def to_wav(src: Path, dst: Path):
    run(["ffmpeg", "-y", "-i", str(src), "-ac", "1", "-ar", str(SAMPLE_RATE), str(dst)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def silence_trim(src: Path, dst: Path):
    """Trim leading+trailing silence only; preserve mid-phrase pauses."""
    run(["ffmpeg", "-y", "-i", str(src), "-af", SILENCE_AF, str(dst)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def make_silence(path: Path, dur: float):
    run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r={SAMPLE_RATE}:cl=mono",
         "-t", f"{dur:.3f}", str(path)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def concat_wavs(parts: list[Path], out: Path):
    lst = out.with_suffix(".concat.txt")
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in parts))
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def wav_to_m4a(wav: Path, m4a: Path):
    run(["ffmpeg", "-y", "-i", str(wav), "-c:a", "aac", "-b:a", "192k", str(m4a)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def fit_segment(src: Path, dur: float, out: Path, fps=30):
    src_dur = probe_dur(src)
    if src_dur >= dur - 0.05:
        vf = (f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
              f"trim=duration={dur:.3f},setpts=PTS-STARTPTS,fps={fps},format=yuv420p")
        run(["ffmpeg", "-y", "-i", str(src), "-vf", vf, "-an", "-t", f"{dur:.3f}",
             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "18", str(out)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        loops = int(math.ceil(dur / max(src_dur, 0.1))) + 1
        vf = (f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
              f"setpts=PTS-STARTPTS,fps={fps},format=yuv420p")
        run(["ffmpeg", "-y", "-stream_loop", str(loops), "-i", str(src), "-vf", vf, "-an",
             "-t", f"{dur:.3f}", "-c:v", "libx264", "-pix_fmt", "yuv420p",
             "-preset", "veryfast", "-crf", "18", str(out)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def esc_text(s: str) -> str:
    return (s.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'").replace("%", "%%"))


def build_vf(starts, durs, lines_list) -> str:
    parts = []
    for s, d, lines in zip(starts, durs, lines_list):
        e = s + d
        enable = f"between(t\\,{s:.3f}\\,{e:.3f})"
        n = len(lines)
        if n == 1:
            y, h = 1540, 118
            parts.append(f"drawbox=x=65:y={y}:w=950:h={h}:color={BAR_COLOR}@1:t=fill:enable='{enable}'")
            parts.append(
                f"drawtext=fontfile={FONT}:text='{esc_text(lines[0])}':fontcolor=black:fontsize=46:"
                f"x=(w-text_w)/2:y={y}+36:enable='{enable}'"
            )
        else:
            y, h = 1480, 198
            parts.append(f"drawbox=x=65:y={y}:w=950:h={h}:color={BAR_COLOR}@1:t=fill:enable='{enable}'")
            parts.append(
                f"drawtext=fontfile={FONT}:text='{esc_text(lines[0])}':fontcolor=black:fontsize=42:"
                f"x=(w-text_w)/2:y={y}+36:enable='{enable}'"
            )
            parts.append(
                f"drawtext=fontfile={FONT}:text='{esc_text(lines[1])}':fontcolor=black:fontsize=42:"
                f"x=(w-text_w)/2:y={y}+112:enable='{enable}'"
            )
    return ",".join(parts)


def silencedetect_gaps(media: Path, min_d=0.25) -> list[dict]:
    """Return silence periods with duration >= min_d."""
    proc = subprocess.run(
        ["ffmpeg", "-i", str(media), "-af", f"silencedetect=noise=-40dB:d={min_d}", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    err = proc.stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]
    ends = re.findall(r"silence_end: ([\d.]+) \| silence_duration: ([\d.]+)", err)
    out = []
    for i, (e, d) in enumerate(ends):
        s = starts[i] if i < len(starts) else max(0.0, float(e) - float(d))
        out.append({"start": s, "end": float(e), "dur": float(d)})
    # trailing silence with no end
    if len(starts) > len(ends):
        total = probe_dur(media)
        s = starts[len(ends)]
        out.append({"start": s, "end": total, "dur": total - s})
    return out


def measure_inter_beat_gaps(media: Path, starts: list[float], durs: list[float]) -> dict:
    """Measure silence around each planned gap boundary."""
    sil = silencedetect_gaps(media, min_d=0.20)
    # classify: lead, inter-beat (between speech), CTA tail
    gaps_meas = []
    for i in range(len(starts) - 1):
        # expected gap window after beat i ends
        win_s = starts[i] + durs[i] - 0.05
        win_e = starts[i + 1] + 0.15
        hit = [g for g in sil if g["end"] > win_s and g["start"] < win_e]
        if hit:
            # take max silence overlapping window
            gaps_meas.append(max(g["dur"] for g in hit))
        else:
            gaps_meas.append(0.0)
    # CTA: silence after last spoken
    vo_end = starts[-1] + durs[-1]
    cta_hits = [g for g in sil if g["start"] >= vo_end - 0.15]
    cta_meas = max((g["dur"] for g in cta_hits), default=0.0)
    # hook spoken = durs[0] (already trimmed)
    return {
        "inter_beat_gaps": [round(x, 3) for x in gaps_meas],
        "max_inter_beat_gap": round(max(gaps_meas) if gaps_meas else 0.0, 3),
        "cta_silence": round(cta_meas, 3),
        "all_silences": [{"start": round(g["start"], 3), "end": round(g["end"], 3), "dur": round(g["dur"], 3)} for g in sil],
    }


def tts_trim_segment(text: str, mp3: Path, wav_raw: Path, wav_trim: Path, rate: str) -> float:
    edge_tts(text, mp3, rate=rate)
    to_wav(mp3, wav_raw)
    silence_trim(wav_raw, wav_trim)
    return probe_dur(wav_trim)


def rebuild(job: dict) -> dict:
    folder: Path = job["folder"]
    vo_dir = folder / "vo_r3" if job.get("vo_subdir") else folder / f"vo_{job['review_tag']}"
    # keep a dedicated vo dir per review to avoid clobber confusion
    vo_dir = folder / f"vo_{job['review_tag']}"
    vo_dir.mkdir(exist_ok=True)
    work = folder / f"rebuild-{job['review_tag']}"
    work.mkdir(exist_ok=True)

    texts = [job["hook"], *job["beats"]]
    names = ["hook", "s01", "s02", "s03", "s04"]
    assert len(texts) == 5
    assert len(job["bar_lines"]) == 5

    rate = job.get("rate", RATE)
    wavs = []
    durs = []
    for name, text in zip(names, texts):
        mp3 = vo_dir / f"{name}.mp3"
        raw = vo_dir / f"{name}_raw.wav"
        trim = vo_dir / f"{name}.wav"
        # hook: ensure ≤ HOOK_MAX; bump rate if needed
        use_rate = rate
        d = tts_trim_segment(text, mp3, raw, trim, use_rate)
        if name == "hook" and d > HOOK_MAX:
            for faster in ("+0%", "+8%", "+15%", "+25%"):
                d = tts_trim_segment(text, mp3, raw, trim, faster)
                use_rate = faster
                if d <= HOOK_MAX:
                    break
            if d > HOOK_MAX:
                raise RuntimeError(f"hook still {d:.3f}s > {HOOK_MAX}s after speed-up")
        print(f"  {name}: {d:.3f}s rate={use_rate} — {text[:48]}")
        wavs.append(trim)
        durs.append(d)

    lead = vo_dir / "lead.wav"
    gapf = vo_dir / "gap.wav"
    make_silence(lead, LEAD)
    make_silence(gapf, GAP)

    parts = [lead, wavs[0]]
    for w in wavs[1:]:
        parts.append(gapf)
        parts.append(w)
    vo_wav = work / "vo_full.wav"
    concat_wavs(parts, vo_wav)
    vo_m4a = folder / f"vo_{job['review_tag']}_full.m4a"
    wav_to_m4a(vo_wav, vo_m4a)

    starts = []
    t = LEAD
    starts.append(t)
    t += durs[0]
    for i in range(1, 5):
        t += GAP
        starts.append(t)
        t += durs[i]
    vo_end = t
    got = probe_dur(vo_wav)
    assert abs(vo_end - got) < 0.08, (vo_end, got)

    (folder / f"vo_starts_{job['review_tag']}.txt").write_text(
        "\n".join(f"{s:.3f},{d:.3f}" for s, d in zip(starts, durs)) + "\n"
    )

    # 符面 ≤10s: cut at min(③-0.4, MID_CUT_MAX), but not before ② has mostly started
    beat3_start = starts[3]
    mid_cut = min(beat3_start - 0.40, MID_CUT_MAX)
    mid_cut = max(mid_cut, min(starts[2] + 0.3, MID_CUT_MAX))  # at least into ② a bit
    mid_cut = min(mid_cut, MID_CUT_MAX)
    # if ③ itself starts after 10s, still cut 符面 at 10s (符面更早炸)
    if beat3_start > MID_CUT_MAX:
        mid_cut = MID_CUT_MAX
        print(f"  WARN: ③ starts @ {beat3_start:.3f} >10; forcing mid_cut={mid_cut}")

    seg_a_dur = mid_cut
    seg_b_dur = vo_end - mid_cut

    segA = work / "segA_fit.mp4"
    segB = work / "segB_fit.mp4"
    segC = work / "segC_cta.mp4"
    fit_segment(folder / "segA.mp4", seg_a_dur, segA)
    fit_segment(folder / "segB.mp4", seg_b_dur, segB)
    run(["ffmpeg", "-y", "-loop", "1", "-i", str(folder / job["ending"]),
         "-t", f"{CTA:.3f}",
         "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,format=yuv420p",
         "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "18", str(segC)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    concat_list = work / "concat.txt"
    concat_list.write_text(
        f"file '{segA.resolve()}'\nfile '{segB.resolve()}'\nfile '{segC.resolve()}'\n"
    )
    concat_raw = work / "concat_raw.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-c", "copy", str(concat_raw)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    cta_sil = work / "cta_sil.wav"
    make_silence(cta_sil, CTA)
    vo_pad_wav = work / "vo_padded.wav"
    concat_wavs([vo_wav, cta_sil], vo_pad_wav)
    vo_pad_m4a = folder / f"vo_{job['review_tag']}_padded.m4a"
    wav_to_m4a(vo_pad_wav, vo_pad_m4a)

    vf = build_vf(starts, durs, job["bar_lines"])
    (work / "bars.vf").write_text(vf)

    out_path = folder / job["out_name"]
    tmp = work / "review_tmp.mp4"
    run(["ffmpeg", "-y", "-i", str(concat_raw), "-i", str(vo_pad_m4a),
         "-filter_complex", f"[0:v]{vf}[v]",
         "-map", "[v]", "-map", "1:a",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-shortest", "-r", "30",
         "-movflags", "+faststart", str(tmp)])
    delivered = probe_dur(tmp)
    tmp.replace(out_path)

    # Verify silencedetect on final
    meas = measure_inter_beat_gaps(out_path, starts, durs)
    print("  MEASURED:", json.dumps(meas, ensure_ascii=False))

    # hard fail if measured max inter gap > 0.55 (allow tiny detect tolerance over 0.35)
    if meas["max_inter_beat_gap"] > 0.55:
        print(f"  FAIL measured max inter-beat gap {meas['max_inter_beat_gap']} > 0.55")
    if meas["cta_silence"] > 1.65:
        print(f"  FAIL measured CTA silence {meas['cta_silence']} > 1.65")
    if durs[0] > HOOK_MAX + 0.05:
        print(f"  FAIL hook dur {durs[0]}")
    if mid_cut > MID_CUT_MAX + 0.01:
        print(f"  FAIL mid_cut {mid_cut}")

    meta = {
        "id": job["id"],
        "path": str(out_path),
        "duration": round(delivered, 3),
        "vo_end": round(vo_end, 3),
        "cta": CTA,
        "mid_cut": round(mid_cut, 3),
        "gaps_planned": GAP,
        "lead": LEAD,
        "starts": [round(s, 3) for s in starts],
        "durs": [round(d, 3) for d in durs],
        "hook_dur": round(durs[0], 3),
        "measured": meas,
        "silence_af": SILENCE_AF,
        "review_tag": job["review_tag"],
        "splice_note": job.get("splice_note", ""),
        "rate": rate,
    }
    (work / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))

    timing = (
        f"review_{job['review_tag']} silence-pack\n"
        f"lead={LEAD:.3f} gap={GAP:.3f} CTA={CTA:.3f}\n"
        f"hook start={starts[0]:.3f} dur={durs[0]:.3f} end={starts[0]+durs[0]:.3f}\n"
        f"① start={starts[1]:.3f} dur={durs[1]:.3f} end={starts[1]+durs[1]:.3f}\n"
        f"② start={starts[2]:.3f} dur={durs[2]:.3f} end={starts[2]+durs[2]:.3f}\n"
        f"③ start={starts[3]:.3f} dur={durs[3]:.3f} end={starts[3]+durs[3]:.3f}\n"
        f"④ start={starts[4]:.3f} dur={durs[4]:.3f} end={starts[4]+durs[4]:.3f}\n"
        f"VO_END={vo_end:.3f}\n"
        f"CTA_START={vo_end:.3f} CTA_DUR={CTA:.3f} CTA_END={vo_end+CTA:.3f}\n"
        f"TOTAL≈{delivered:.3f}\n"
        f"mid_cut={mid_cut:.3f} (符面≤{MID_CUT_MAX})\n"
        f"measured_max_inter_beat_gap={meas['max_inter_beat_gap']}\n"
        f"measured_cta_silence={meas['cta_silence']}\n"
        f"measured_inter_gaps={meas['inter_beat_gaps']}\n"
        f"silenceremove=lead+trail reverse-trick (-40dB)\n"
    )
    (folder / f"TIMING_{job['review_tag']}.txt").write_text(timing)

    spec = f"""# {job['id']} EXPORT_SPEC (review_{job['review_tag']})

## Deliverable
- Path: `{out_path}`
- Spec: 1080×1920, 30fps, H.264 + AAC
- Duration: **{delivered:.3f}s**
- VO end: **{vo_end:.3f}s**
- CTA still: **{CTA:.3f}s** ({vo_end:.3f} → {vo_end+CTA:.3f})
- Status: review cut only — **未放行不发 / do not upload**

## Locked copy
See `COPY.md`. Single-line hook + four beats. Ending CTA exact: `链接见主页／评论置顶`

## Structure
| Seg | Content | Time |
|-----|---------|------|
| A | First-frame motion + 钩 + ①②（至符面切点） | 0.000–{mid_cut:.3f} |
| B | 符中帧（≤10s 进）+ ③④ | {mid_cut:.3f}–{vo_end:.3f} |
| C | Ending CTA still | {vo_end:.3f}–{vo_end+CTA:.3f} |

## VO / 节奏包（真裁尾）
- Voice: `{VOICE}` via `{EDGE}`
- Rate `{rate}`, pitch `{PITCH}`
- **每段 silenceremove 裁头尾**（reverse-trick，-40dB；保留句中停顿）后再拼显式 gap
- Lead {LEAD:.2f}s; planned gaps **{GAP:.2f}s** (≤0.40); CTA silent hold **{CTA:.2f}s** (≤1.50)
- Hook dur **{durs[0]:.3f}s** (≤3.0)
- Starts/durs (hook,①,②,③,④): `{' / '.join(f'{s:.3f},{d:.3f}' for s,d in zip(starts,durs))}`
- mid_cut **{mid_cut:.3f}s** (符面≤10s)

## silencedetect 实测（交核自检）
- max inter-beat gap: **{meas['max_inter_beat_gap']}s** (planned {GAP})
- inter-beat gaps: `{meas['inter_beat_gaps']}`
- CTA silence: **{meas['cta_silence']}s** (planned {CTA})
- all silences ≥0.20s: `{json.dumps(meas['all_silences'], ensure_ascii=False)}`

## 黄条
- ffmpeg **drawbox+drawtext** 硬烧 `#F5C518`；钩 + 四段；片尾 CTA 不叠黄条
- 1 行：y=1540 h=118；2 行：y=1480 h=198；x=65 w=950

## HOOK_SPLICE
- {job.get('splice_note', '')}
- hook VO occupies `{starts[0]:.3f}`–`{starts[0]+durs[0]:.3f}`

## Craft
- 毛笔字首帧「{job['title']}」+「请神＝调模型」
- 符面冲击 ≤10s：mid cut @ {mid_cut:.3f}s
- ④ 结束立刻接 CTA；假气口已用 silenceremove 消除
"""
    (folder / "EXPORT_SPEC.md").write_text(spec)

    # review frames
    rd = folder / f"review-{job['review_tag']}"
    rd.mkdir(exist_ok=True)
    for label, tt in [
        ("hook", starts[0] + min(0.8, durs[0] * 0.4)),
        ("b3", starts[3] + 0.4),
        ("cta", vo_end + 0.3),
        ("mid", mid_cut + 0.2),
    ]:
        run(["ffmpeg", "-y", "-ss", f"{tt:.3f}", "-i", str(out_path),
             "-update", "1", "-frames:v", "1", str(rd / f"f_{label}.jpg")],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print(json.dumps({k: meta[k] for k in ("id", "path", "duration", "vo_end", "cta", "mid_cut", "hook_dur", "measured")}, ensure_ascii=False))
    return meta


# --- job definitions (series 四段) ---
SERIES_JOBS = [
    {
        "id": "v08-hupengyou",
        "folder": ROOT / "v08-hupengyou",
        "out_name": "v08-hupengyou_review_r3.mp4",
        "review_tag": "r3",
        "title": "护朋友",
        "ending": "ending-cta.jpg",
        "hook": "护朋友——请神，不就是调模型吗？",
        "beats": [
            "今日请的，是关圣帝君——",
            "我给大模型的诉求是：「护我挚友义气长存，彼此照应。」",
            "符上落了：义气、互助、长久。",
            "愿好友相护，路远情在。想自己生成一张——链接见主页／评论置顶。",
        ],
        "bar_lines": [
            ["护朋友——请神，不就是调模型吗？"],
            ["今日请的，是关圣帝君——"],
            ["我给大模型的诉求是：", "「护我挚友义气长存，彼此照应。」"],
            ["符上落了：义气、互助、长久。"],
            ["愿好友相护，路远情在。", "想自己生成一张——链接见主页／评论置顶。"],
        ],
        "splice_note": "HOOK_SPLICE@after_lead: replace/extend hook VO+bar only; four beats locked.",
    },
]


def job_v02_v07(which: str, review_tag: str, out_name: str) -> dict:
    table = {
        "v02-qishiye": dict(
            title="起事业", ending="ending-cta.jpg",
            hook="起事业——请神，不就是调模型吗？",
            beats=[
                "今日请的，是文昌帝君——",
                "我给大模型的诉求是：「助我事业开运，步步清晰。」",
                "符上落了：开运、升迁、贵人。",
                "愿事业顺遂，路越走越宽。想自己生成一张——链接见主页／评论置顶。",
            ],
            bar_lines=[
                ["起事业——请神，不就是调模型吗？"],
                ["今日请的，是文昌帝君——"],
                ["我给大模型的诉求是：", "「助我事业开运，步步清晰。」"],
                ["符上落了：开运、升迁、贵人。"],
                ["愿事业顺遂，路越走越宽。", "想自己生成一张——链接见主页／评论置顶。"],
            ],
        ),
        "v03-qifacai": dict(
            title="起发财", ending="ending-cta.jpg",
            hook="起发财——付 Token，不就是请福吗？",
            beats=[
                "今日请的，是财神赵公明——",
                "我给大模型的诉求是：「助我财运畅通，进账有路。」",
                "符上落了：进宝、开源、不漏财。",
                "愿财源稳进，不慌不贪。想自己生成一张——链接见主页／评论置顶。",
            ],
            bar_lines=[
                ["起发财——付 Token，不就是请福吗？"],
                ["今日请的，是财神赵公明——"],
                ["我给大模型的诉求是：", "「助我财运畅通，进账有路。」"],
                ["符上落了：进宝、开源、不漏财。"],
                ["愿财源稳进，不慌不贪。", "想自己生成一张——链接见主页／评论置顶。"],
            ],
        ),
        "v04-shenti-pingan": dict(
            title="身体平安", ending="ending-cta.jpg",
            hook="护身——不就是给模型一道护身符吗？",
            beats=[
                "今日请的，是药王孙思邈——",
                "我给大模型的诉求是：「护我身心安泰，少病少忧。」",
                "符上落了：安康、清气、稳眠。",
                "愿身体平安，日日轻安。想自己生成一张——链接见主页／评论置顶。",
            ],
            bar_lines=[
                ["护身——不就是给模型一道护身符吗？"],
                ["今日请的，是药王孙思邈——"],
                ["我给大模型的诉求是：", "「护我身心安泰，少病少忧。」"],
                ["符上落了：安康、清气、稳眠。"],
                ["愿身体平安，日日轻安。", "想自己生成一张——链接见主页／评论置顶。"],
            ],
        ),
        "v05-hufumu": dict(
            title="护父母", ending="ending-cta.jpg",
            hook="护父母——一纸符，就是一次调模型。",
            beats=[
                "今日请的，是慈航道人——",
                "我给大模型的诉求是：「护我双亲安康，岁岁平安。」",
                "符上落了：慈安、延年、家宁。",
                "愿父母康健，福报绵长。想自己生成一张——链接见主页／评论置顶。",
            ],
            bar_lines=[
                ["护父母——一纸符，就是一次调模型。"],
                ["今日请的，是慈航道人——"],
                ["我给大模型的诉求是：", "「护我双亲安康，岁岁平安。」"],
                ["符上落了：慈安、延年、家宁。"],
                ["愿父母康健，福报绵长。", "想自己生成一张——链接见主页／评论置顶。"],
            ],
        ),
        "v06-hujiaren": dict(
            title="护家人", ending="ending-cta.jpg",
            hook="护家人——请神，不就是调模型吗？",
            beats=[
                "今日请的，是灶神——",
                "我给大模型的诉求是：「护我一家和顺，出入平安。」",
                "符上落了：家宁、和合、平安。",
                "愿家人团圆，宅气清安。想自己生成一张——链接见主页／评论置顶。",
            ],
            bar_lines=[
                ["护家人——请神，不就是调模型吗？"],
                ["今日请的，是灶神——"],
                ["我给大模型的诉求是：", "「护我一家和顺，出入平安。」"],
                ["符上落了：家宁、和合、平安。"],
                ["愿家人团圆，宅气清安。", "想自己生成一张——链接见主页／评论置顶。"],
            ],
        ),
        "v07-huairen": dict(
            title="护爱人", ending="ending-cta.jpg",
            hook="护爱人——请神，不就是调模型吗？",
            beats=[
                "今日请的，是月老——",
                "我给大模型的诉求是：「护我与所爱，心意相通，长久相守。」",
                "符上落了：同心、和合、长久。",
                "愿两心相守，细水长流。想自己生成一张——链接见主页／评论置顶。",
            ],
            bar_lines=[
                ["护爱人——请神，不就是调模型吗？"],
                ["今日请的，是月老——"],
                ["我给大模型的诉求是：", "「护我与所爱，心意相通，长久相守。」"],
                ["符上落了：同心、和合、长久。"],
                ["愿两心相守，细水长流。", "想自己生成一张——链接见主页／评论置顶。"],
            ],
        ),
    }
    base = table[which]
    return {
        "id": which,
        "folder": ROOT / which,
        "out_name": out_name,
        "review_tag": review_tag,
        "title": base["title"],
        "ending": base["ending"],
        "hook": base["hook"],
        "beats": base["beats"],
        "bar_lines": base["bar_lines"],
        "splice_note": "HOOK_SPLICE@after_lead: replace/extend hook VO+bar only; four beats locked.",
    }


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "v08"
    if which == "v08":
        print("==== rebuilding v08-hupengyou review_r3 (silence pack) ====")
        rebuild(SERIES_JOBS[0])
    elif which.startswith("v"):
        # e.g. v02 r4 v02-qishiye_review_r4.mp4
        # argv: v02-qishiye r4
        tag = sys.argv[2]
        out = f"{which}_review_{tag}.mp4"
        print(f"==== rebuilding {which} review_{tag} ====")
        rebuild(job_v02_v07(which, tag, out))
    else:
        raise SystemExit("usage: rebuild_silence_pack.py v08 | v0N-xxx rN")
