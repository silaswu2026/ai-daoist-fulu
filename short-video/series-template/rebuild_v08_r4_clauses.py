#!/usr/bin/env python3
"""v08 review_r4: split every clause (？！。、) → silenceremove → gap≤0.35; whole-file mid-gap gate."""
from __future__ import annotations

import json
import math
import re
import subprocess
from pathlib import Path

ROOT = Path("/workspace/short-video")
FOLDER = ROOT / "v08-hupengyou"
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
REVIEW = "r4"
OUT_NAME = "v08-hupengyou_review_r4.mp4"

# Head+tail only
TRIM_AF = (
    "silenceremove=start_periods=1:start_duration=0.05:start_threshold=-40dB,"
    "areverse,"
    "silenceremove=start_periods=1:start_duration=0.08:start_threshold=-40dB,"
    "areverse"
)

HOOK = "护朋友——请神，不就是调模型吗？"
BEATS = [
    "今日请的，是关圣帝君——",
    "我给大模型的诉求是：「护我挚友义气长存，彼此照应。」",
    "符上落了：义气、互助、长久。",
    "愿好友相护，路远情在。想自己生成一张——链接见主页／评论置顶。",
]
# Yellow bars stay at beat grain (hook + 4)
BAR_LINES = [
    ["护朋友——请神，不就是调模型吗？"],
    ["今日请的，是关圣帝君——"],
    ["我给大模型的诉求是：", "「护我挚友义气长存，彼此照应。」"],
    ["符上落了：义气、互助、长久。"],
    ["愿好友相护，路远情在。", "想自己生成一张——链接见主页／评论置顶。"],
]

SPLIT_CHARS = "？！。、"
CLAUSE_PAT = re.compile(f"([{re.escape(SPLIT_CHARS)}])")


def run(cmd, **kw):
    print("+", " ".join(str(c) for c in cmd)[:240])
    subprocess.check_call(cmd, **kw)


def probe(path: Path) -> float:
    return float(
        subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", str(path)],
            text=True,
        ).strip()
    )


def split_clauses(text: str) -> list[str]:
    """Split on ？！。、 keeping delimiter with left piece; merge orphan closers."""
    parts = CLAUSE_PAT.split(text)
    out = []
    i = 0
    while i < len(parts):
        chunk = parts[i]
        if i + 1 < len(parts) and parts[i + 1] in SPLIT_CHARS:
            chunk = chunk + parts[i + 1]
            i += 2
        else:
            i += 1
        chunk = chunk.strip()
        if not chunk:
            continue
        if out and re.fullmatch(r"[」』》〉）\)]+", chunk):
            out[-1] = out[-1] + chunk
        else:
            out.append(chunk)
    return out or [text.strip()]


def edge_tts(text: str, out: Path, rate: str = RATE):
    run([str(EDGE), "--voice", VOICE, f"--rate={rate}", f"--pitch={PITCH}",
         "--text", text, "--write-media", str(out)])


def to_wav(src: Path, dst: Path):
    run(["ffmpeg", "-y", "-i", str(src), "-ac", "1", "-ar", str(SAMPLE_RATE), str(dst)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def trim(src: Path, dst: Path):
    run(["ffmpeg", "-y", "-i", str(src), "-af", TRIM_AF, str(dst)],
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
    src_dur = probe(src)
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
    return s.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'").replace("%", "%%")


def build_vf(beat_spans: list[tuple[float, float]], lines_list) -> str:
    parts = []
    for (s, e), lines in zip(beat_spans, lines_list):
        enable = f"between(t\\,{s:.3f}\\,{e:.3f})"
        if len(lines) == 1:
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


def silencedetect(media: Path, noise="-35dB", d=0.35) -> list[dict]:
    proc = subprocess.run(
        ["ffmpeg", "-i", str(media), "-af", f"silencedetect=noise={noise}:d={d}", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    err = proc.stderr
    starts = [float(x) for x in re.findall(r"silence_start:\s*([\d.]+)", err)]
    ends = re.findall(r"silence_end:\s*([\d.]+)\s*\|\s*silence_duration:\s*([\d.]+)", err)
    out = []
    for i, (e, dur) in enumerate(ends):
        s = starts[i] if i < len(starts) else max(0.0, float(e) - float(dur))
        out.append({"start": round(s, 3), "end": round(float(e), 3), "dur": round(float(dur), 3)})
    if len(starts) > len(ends):
        total = probe(media)
        s = starts[len(ends)]
        out.append({"start": round(s, 3), "end": round(total, 3), "dur": round(total - s, 3)})
    return out


def tts_trim(text: str, stem: Path, rate: str) -> float:
    mp3 = stem.with_suffix(".mp3")
    raw = Path(str(stem) + "_raw.wav")
    wav = stem.with_suffix(".wav")
    edge_tts(text, mp3, rate=rate)
    to_wav(mp3, raw)
    trim(raw, wav)
    return probe(wav)


def main():
    vo = FOLDER / f"vo_{REVIEW}"
    work = FOLDER / f"rebuild-{REVIEW}"
    vo.mkdir(exist_ok=True)
    work.mkdir(exist_ok=True)

    # Build clause list with beat tags
    units: list[dict] = []  # {beat_idx, text, path, dur}
    groups = [HOOK, *BEATS]
    for bi, text in enumerate(groups):
        clauses = split_clauses(text)
        print(f"beat{bi} clauses: {clauses}")
        for ci, clause in enumerate(clauses):
            units.append({"beat_idx": bi, "ci": ci, "text": clause})

    # TTS each clause; speed up hook clauses if total hook > HOOK_MAX
    rate = RATE
    for u in units:
        stem = vo / f"b{u['beat_idx']:02d}_c{u['ci']:02d}"
        d = tts_trim(u["text"], stem, rate)
        u["path"] = stem.with_suffix(".wav")
        u["dur"] = d
        print(f"  b{u['beat_idx']}c{u['ci']}: {d:.3f}s — {u['text']}")

    # If hook (beat 0) total > HOOK_MAX, re-TTS hook clauses faster
    hook_total = sum(u["dur"] for u in units if u["beat_idx"] == 0)
    if hook_total > HOOK_MAX:
        for faster in ("+0%", "+8%", "+15%", "+25%"):
            for u in units:
                if u["beat_idx"] != 0:
                    continue
                stem = vo / f"b{u['beat_idx']:02d}_c{u['ci']:02d}"
                d = tts_trim(u["text"], stem, faster)
                u["path"] = stem.with_suffix(".wav")
                u["dur"] = d
            hook_total = sum(u["dur"] for u in units if u["beat_idx"] == 0)
            rate = faster
            print(f"  hook retime rate={faster} total={hook_total:.3f}")
            if hook_total <= HOOK_MAX:
                break
        if hook_total > HOOK_MAX:
            raise RuntimeError(f"hook still {hook_total:.3f}s > {HOOK_MAX}")

    lead = vo / "lead.wav"
    gapf = vo / "gap.wav"
    make_silence(lead, LEAD)
    make_silence(gapf, GAP)

    parts = [lead]
    for i, u in enumerate(units):
        if i > 0:
            parts.append(gapf)
        parts.append(u["path"])

    vo_wav = work / "vo_full.wav"
    concat_wavs(parts, vo_wav)

    # Timeline
    t = LEAD
    for i, u in enumerate(units):
        if i > 0:
            t += GAP
        u["start"] = t
        u["end"] = t + u["dur"]
        t = u["end"]
    vo_end = t
    assert abs(vo_end - probe(vo_wav)) < 0.08, (vo_end, probe(vo_wav))

    # Beat spans for bars + mid_cut
    beat_spans = []
    beat_durs = []
    beat_starts = []
    for bi in range(5):
        us = [u for u in units if u["beat_idx"] == bi]
        s0 = us[0]["start"]
        e0 = us[-1]["end"]
        beat_spans.append((s0, e0))
        beat_starts.append(s0)
        beat_durs.append(e0 - s0)

    # mid_cut: before ③ (beat 3), ≤10s
    beat3_start = beat_starts[3]
    mid_cut = min(beat3_start - 0.40, MID_CUT_MAX)
    mid_cut = max(mid_cut, min(beat_starts[2] + 0.2, MID_CUT_MAX))
    mid_cut = min(mid_cut, MID_CUT_MAX)
    if beat3_start > MID_CUT_MAX:
        mid_cut = MID_CUT_MAX
        print(f"WARN ③@{beat3_start:.3f}>10 → mid_cut={mid_cut}")

    segA = work / "segA_fit.mp4"
    segB = work / "segB_fit.mp4"
    segC = work / "segC_cta.mp4"
    fit_segment(FOLDER / "segA.mp4", mid_cut, segA)
    fit_segment(FOLDER / "segB.mp4", vo_end - mid_cut, segB)
    run(["ffmpeg", "-y", "-loop", "1", "-i", str(FOLDER / "ending-cta.jpg"),
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
    vo_pad = work / "vo_padded.wav"
    concat_wavs([vo_wav, cta_sil], vo_pad)
    vo_pad_m4a = FOLDER / f"vo_{REVIEW}_padded.m4a"
    wav_to_m4a(vo_pad, vo_pad_m4a)
    wav_to_m4a(vo_wav, FOLDER / f"vo_{REVIEW}_full.m4a")

    vf = build_vf(beat_spans, BAR_LINES)
    (work / "bars.vf").write_text(vf)

    out = FOLDER / OUT_NAME
    tmp = work / "review_tmp.mp4"
    run(["ffmpeg", "-y", "-i", str(concat_raw), "-i", str(vo_pad_m4a),
         "-filter_complex", f"[0:v]{vf}[v]",
         "-map", "[v]", "-map", "1:a",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-shortest", "-r", "30",
         "-movflags", "+faststart", str(tmp)])
    delivered = probe(tmp)
    tmp.replace(out)

    # GATE: whole-file silencedetect noise=-35dB:d=0.35
    sil = silencedetect(out, noise="-35dB", d=0.35)
    print("SILENCE_LIST:")
    for g in sil:
        print(f"  {g['start']:.3f} → {g['end']:.3f}  dur={g['dur']:.3f}")

    bad = []
    for g in sil:
        # allow CTA: silence starting near vo_end with dur≈1.5
        if g["start"] >= vo_end - 0.12 and abs(g["dur"] - CTA) < 0.25:
            continue
        # allow planned gaps ≈0.35 (≤0.40)
        if g["dur"] <= 0.40 + 1e-3:
            continue
        bad.append(g)

    if bad:
        print("GATE FAIL mid silence >0.40:")
        for g in bad:
            print(f"  FAIL {g}")
        raise RuntimeError(f"mid-gap gate failed: {bad}")

    print("GATE PASS")

    meta = {
        "id": "v08-hupengyou",
        "path": str(out),
        "duration": round(delivered, 3),
        "vo_end": round(vo_end, 3),
        "cta": CTA,
        "mid_cut": round(mid_cut, 3),
        "hook_dur": round(beat_durs[0], 3),
        "beat_starts": [round(s, 3) for s in beat_starts],
        "beat_durs": [round(d, 3) for d in beat_durs],
        "clauses": [
            {"beat": u["beat_idx"], "ci": u["ci"], "text": u["text"],
             "start": round(u["start"], 3), "dur": round(u["dur"], 3)}
            for u in units
        ],
        "silence_list": sil,
        "gap_planned": GAP,
        "lead": LEAD,
        "rate": rate,
        "review_tag": REVIEW,
    }
    (work / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))

    timing = (
        f"review_r4 clause-split silence pack\n"
        f"lead={LEAD:.3f} gap={GAP:.3f} CTA={CTA:.3f}\n"
        f"hook start={beat_starts[0]:.3f} dur={beat_durs[0]:.3f} end={beat_starts[0]+beat_durs[0]:.3f}\n"
        f"① start={beat_starts[1]:.3f} dur={beat_durs[1]:.3f}\n"
        f"② start={beat_starts[2]:.3f} dur={beat_durs[2]:.3f}\n"
        f"③ start={beat_starts[3]:.3f} dur={beat_durs[3]:.3f}\n"
        f"④ start={beat_starts[4]:.3f} dur={beat_durs[4]:.3f}\n"
        f"VO_END={vo_end:.3f}\n"
        f"CTA_START={vo_end:.3f} CTA_DUR={CTA:.3f} CTA_END={vo_end+CTA:.3f}\n"
        f"TOTAL≈{delivered:.3f}\n"
        f"mid_cut={mid_cut:.3f}\n"
        f"clauses={len(units)}\n"
        f"gate=silencedetect noise=-35dB:d=0.35 → no mid >0.40 except CTA\n"
        f"silence_list={json.dumps(sil, ensure_ascii=False)}\n"
    )
    (FOLDER / "TIMING.txt").write_text(timing)
    (FOLDER / "TIMING_r4.txt").write_text(timing)

    spec = f"""# v08-hupengyou EXPORT_SPEC (review_r4)

## Deliverable
- Path: `{out}`
- Spec: 1080×1920, 30fps, H.264 + AAC
- Duration: **{delivered:.3f}s**
- VO end: **{vo_end:.3f}s**
- CTA still: **{CTA:.3f}s** ({vo_end:.3f} → {vo_end+CTA:.3f})
- Status: review cut only — **未放行不发 / do not upload**

## Locked copy
See `COPY.md`. Single-line hook「{HOOK}」+ four beats. CTA: `链接见主页／评论置顶`

## Structure
| Seg | Content | Time |
|-----|---------|------|
| A | First-frame + 钩 + ①② | 0.000–{mid_cut:.3f} |
| B | 符面（≤10s）+ ③④ | {mid_cut:.3f}–{vo_end:.3f} |
| C | CTA still | {vo_end:.3f}–{vo_end+CTA:.3f} |

## VO / 分句裁尾
- Voice: `{VOICE}` rate `{rate}` pitch `{PITCH}`
- **每句按 ？！。、 拆成独立 edge-tts** → silenceremove 头尾 → 显式 gap **{GAP:.2f}s**
- Lead {LEAD:.2f}s; CTA **{CTA:.2f}s**; hook beat dur **{beat_durs[0]:.3f}s** (≤3)
- mid_cut **{mid_cut:.3f}s** (符面≤10s)
- Beat starts/durs: `{' / '.join(f'{s:.3f},{d:.3f}' for s,d in zip(beat_starts, beat_durs))}`
- Clause count: **{len(units)}**

## silencedetect 实测（gate: noise=-35dB:d=0.35）
- PASS: no mid silence >0.40s except CTA≈1.5s
- silence_list: `{json.dumps(sil, ensure_ascii=False)}`

## 黄条
- drawbox+drawtext `#F5C518`；按 beat 粒度（钩+四段）；片尾不叠

## Craft
- 分句消除句内假气口；④「愿…／想自己…」等长句已拆
"""
    (FOLDER / "EXPORT_SPEC.md").write_text(spec)

    rd = FOLDER / f"review-{REVIEW}"
    rd.mkdir(exist_ok=True)
    for label, tt in [
        ("hook", beat_starts[0] + 0.6),
        ("b3", beat_starts[3] + 0.3),
        ("cta", vo_end + 0.3),
        ("mid", mid_cut + 0.15),
    ]:
        run(["ffmpeg", "-y", "-ss", f"{tt:.3f}", "-i", str(out),
             "-update", "1", "-frames:v", "1", str(rd / f"f_{label}.jpg")],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print(json.dumps({
        "path": str(out),
        "duration": round(delivered, 3),
        "vo_end": round(vo_end, 3),
        "cta": CTA,
        "mid_cut": round(mid_cut, 3),
        "hook_dur": round(beat_durs[0], 3),
        "max_inter_planned_gap": GAP,
        "silence_list": sil,
        "gate": "PASS",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
