#!/usr/bin/env python3
"""v05-hufumu review_r4 — split every ？！。、 clause; real silenceremove; silence gate."""
from __future__ import annotations

import json
import math
import re
import subprocess
from pathlib import Path

ROOT = Path("/workspace/short-video")
FOLDER = ROOT / "v05-hufumu"
EDGE = ROOT / ".venv/bin/edge-tts"
VOICE = "zh-CN-YunyangNeural"
RATE = "-12%"
PITCH = "-5Hz"
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
BAR_COLOR = "0xF5C518"
LEAD = 0.25
GAP = 0.35
CTA = 1.50
SR = 44100
MID_MAX = 10.0
OUT = FOLDER / "v05-hufumu_review_r4.mp4"
WORK = FOLDER / "rebuild-r4"
VO = FOLDER / "vo"

TRIM_AF = (
    "silenceremove=start_periods=1:start_duration=0.02:start_threshold=0.02:"
    "start_silence=0.02:detection=rms,"
    "areverse,"
    "silenceremove=start_periods=1:start_duration=0.04:start_threshold=0.02:"
    "start_silence=0.02:detection=rms,"
    "areverse"
)

HOOK = "护父母——一纸符，就是一次调模型。"
BEATS = [
    "今日请的，是慈航道人——",
    "我给大模型的诉求是：「护我双亲安康，岁岁平安。」",
    "符上落了：慈安、延年、家宁。",
    "愿父母康健，福报绵长。想自己生成一张——链接见主页／评论置顶。",
]


def run(cmd, **kw):
    print("+", " ".join(str(c) for c in cmd)[:240])
    subprocess.check_call(cmd, **kw)


def probe(p: Path) -> float:
    return float(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=nw=1:nk=1",
                str(p),
            ],
            text=True,
        ).strip()
    )


def split_clauses(text: str) -> list[str]:
    """Split on ？！。、 — keep delimiter (+ optional closing quote after 。？！)."""
    text = text.strip()
    if not text:
        return []
    # 、 is always a split point; ？！。 optionally eat following 」』"
    pieces = re.split(r"(、|[？！。][」』\"]?)", text)
    out: list[str] = []
    buf = ""
    for part in pieces:
        if not part:
            continue
        buf += part
        if part == "、" or re.fullmatch(r"[？！。][」』\"]?", part):
            out.append(buf.strip())
            buf = ""
    if buf.strip():
        out.append(buf.strip())
    cleaned: list[str] = []
    for c in out:
        if re.fullmatch(r"[」』\"'》\s]+", c) and cleaned:
            cleaned[-1] += c
        elif c and not re.fullmatch(r"[、\s]+", c):
            cleaned.append(c)
    return cleaned or [text]


def flatten() -> list[str]:
    clauses = [HOOK]
    for b in BEATS:
        clauses.extend(split_clauses(b))
    return clauses


def edge_tts(text: str, out: Path):
    run(
        [
            str(EDGE),
            "--voice",
            VOICE,
            f"--rate={RATE}",
            f"--pitch={PITCH}",
            "--text",
            text,
            "--write-media",
            str(out),
        ]
    )


def to_wav(src: Path, dst: Path):
    run(
        ["ffmpeg", "-y", "-i", str(src), "-ac", "1", "-ar", str(SR), str(dst)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def trim(src: Path, dst: Path):
    run(
        ["ffmpeg", "-y", "-i", str(src), "-af", TRIM_AF, str(dst)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def silence(path: Path, dur: float):
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"anullsrc=r={SR}:cl=mono",
            "-t",
            f"{dur:.3f}",
            str(path),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def concat_wavs(parts: list[Path], out: Path):
    lst = out.with_suffix(".concat.txt")
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in parts))
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(lst),
            "-c",
            "copy",
            str(out),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def wav_m4a(wav: Path, m4a: Path):
    run(
        ["ffmpeg", "-y", "-i", str(wav), "-c:a", "aac", "-b:a", "192k", str(m4a)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def fit_seg(src: Path, dur: float, out: Path, fps=30):
    src_dur = probe(src)
    if src_dur >= dur - 0.05:
        vf = (
            f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            f"trim=duration={dur:.3f},setpts=PTS-STARTPTS,fps={fps},format=yuv420p"
        )
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-vf",
            vf,
            "-an",
            "-t",
            f"{dur:.3f}",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            str(out),
        ]
    else:
        loops = int(math.ceil(dur / max(src_dur, 0.01))) + 1
        vf = (
            "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            f"setpts=PTS-STARTPTS,fps={fps},format=yuv420p"
        )
        cmd = [
            "ffmpeg",
            "-y",
            "-stream_loop",
            str(loops),
            "-i",
            str(src),
            "-vf",
            vf,
            "-an",
            "-t",
            f"{dur:.3f}",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            str(out),
        ]
    run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def still(img: Path, dur: float, out: Path, zoom=False):
    if zoom:
        vf = (
            f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            f"zoompan=z='min(1.06,1+0.001*on)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={max(int(dur*30),1)}:s=1080x1920:fps=30,format=yuv420p"
        )
    else:
        vf = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,format=yuv420p"
    run(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            str(img),
            "-t",
            f"{dur:.3f}",
            "-vf",
            vf,
            "-an",
            "-r",
            "30",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            str(out),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def esc(s: str) -> str:
    return (
        s.replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
        .replace("%", "%%")
    )


def bar_lines(text: str) -> list[str]:
    t = text.strip()
    if len(t) <= 18:
        return [t]
    for sep in ("——", "：", "，"):
        if sep in t:
            a, b = t.split(sep, 1)
            left = a + sep
            right = b.strip()
            if right:
                return [left, right]
    if len(t) > 20:
        return [t[:16], t[16:]]
    return [t]


def build_vf(starts, durs, lines_list) -> str:
    parts = []
    for s, d, lines in zip(starts, durs, lines_list):
        e = s + d
        en = f"between(t\\,{s:.3f}\\,{e:.3f})"
        if len(lines) == 1:
            y, h = 1540, 118
            parts.append(
                f"drawbox=x=65:y={y}:w=950:h={h}:color={BAR_COLOR}@1:t=fill:enable='{en}'"
            )
            parts.append(
                f"drawtext=fontfile={FONT}:text='{esc(lines[0])}':fontcolor=black:fontsize=46:"
                f"x=(w-text_w)/2:y={y}+36:enable='{en}'"
            )
        else:
            y, h = 1480, 198
            parts.append(
                f"drawbox=x=65:y={y}:w=950:h={h}:color={BAR_COLOR}@1:t=fill:enable='{en}'"
            )
            parts.append(
                f"drawtext=fontfile={FONT}:text='{esc(lines[0])}':fontcolor=black:fontsize=42:"
                f"x=(w-text_w)/2:y={y}+36:enable='{en}'"
            )
            parts.append(
                f"drawtext=fontfile={FONT}:text='{esc(lines[1])}':fontcolor=black:fontsize=42:"
                f"x=(w-text_w)/2:y={y}+112:enable='{en}'"
            )
    return ",".join(parts)


def silencedetect(path: Path, until: float | None = None, d=0.35):
    cmd = ["ffmpeg", "-i", str(path)]
    if until is not None:
        cmd += ["-t", f"{until:.3f}"]
    cmd += ["-af", f"silencedetect=noise=-35dB:d={d}", "-f", "null", "-"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    starts = [float(x) for x in re.findall(r"silence_start:\s*([0-9.]+)", proc.stderr)]
    ends = re.findall(
        r"silence_end:\s*([0-9.]+)\s*\|\s*silence_duration:\s*([0-9.]+)", proc.stderr
    )
    out = []
    ei = 0
    for s in starts:
        if ei < len(ends):
            out.append((s, float(ends[ei][0]), float(ends[ei][1])))
            ei += 1
        else:
            # open to end
            dur = until if until is not None else probe(path)
            out.append((s, dur, max(0.0, dur - s)))
    return out, proc.stderr


def main():
    WORK.mkdir(exist_ok=True)
    VO.mkdir(exist_ok=True)
    clauses = flatten()
    print("CLAUSES:")
    for i, c in enumerate(clauses):
        print(f"  [{i}] {c}")
    (WORK / "clauses.txt").write_text("\n".join(clauses) + "\n")

    wavs = []
    durs = []
    for i, text in enumerate(clauses):
        name = "hook" if i == 0 else f"s{i:02d}"
        mp3 = VO / f"{name}.mp3"
        raw = VO / f"{name}_raw.wav"
        tw = VO / f"{name}.wav"
        edge_tts(text, mp3)
        to_wav(mp3, raw)
        trim(raw, tw)
        d = probe(tw)
        # reject if internal silence >0.40 after trim (should be rare on short clauses)
        sil, _ = silencedetect(tw, d=0.25)
        for s, e, dd in sil:
            if s > 0.05 and e < d - 0.05 and dd > 0.40:
                raise RuntimeError(f"clip {name} still has internal silence {dd:.3f}s: {text}")
        wavs.append(tw)
        durs.append(d)
        print(f"  {name}: {d:.3f}s — {text}")

    if durs[0] > 3.05:
        print(f"WARNING hook {durs[0]:.3f}s > 3s")

    lead = VO / "lead_p.wav"
    gap = VO / "gap_p.wav"
    silence(lead, LEAD)
    silence(gap, GAP)
    parts = [lead, wavs[0]]
    for w in wavs[1:]:
        parts += [gap, w]
    vo_wav = WORK / "vo_full.wav"
    concat_wavs(parts, vo_wav)
    wav_m4a(vo_wav, FOLDER / "vo_full.m4a")

    starts = []
    t = LEAD
    starts.append(t)
    t += durs[0]
    for i in range(1, len(durs)):
        t += GAP
        starts.append(t)
        t += durs[i]
    vo_end = t
    assert abs(vo_end - probe(vo_wav)) < 0.08, (vo_end, probe(vo_wav))

    # 符面: first clause containing 符上落了
    fulu_i = next(i for i, c in enumerate(clauses) if "符上落了" in c)
    mid_cut = min(MID_MAX, max(starts[0] + durs[0], starts[fulu_i] - 0.40))
    mid_cut = min(mid_cut, vo_end - 0.5)

    segA = WORK / "segA_fit.mp4"
    segB = WORK / "segB_fit.mp4"
    segC = WORK / "segC_cta.mp4"
    fit_seg(FOLDER / "segA.mp4", mid_cut, segA)
    fit_seg(FOLDER / "segB.mp4", vo_end - mid_cut, segB)
    still(FOLDER / "ending-cta.jpg", CTA, segC, zoom=False)

    cl = WORK / "concat.txt"
    cl.write_text(
        f"file '{segA.resolve()}'\nfile '{segB.resolve()}'\nfile '{segC.resolve()}'\n"
    )
    concat_raw = WORK / "concat_raw.mp4"
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(cl),
            "-c",
            "copy",
            str(concat_raw),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    cta_sil = WORK / "cta_sil.wav"
    silence(cta_sil, CTA)
    vo_pad = WORK / "vo_padded.wav"
    concat_wavs([vo_wav, cta_sil], vo_pad)
    wav_m4a(vo_pad, FOLDER / "vo_padded.m4a")

    lines_list = [bar_lines(c) for c in clauses]
    vf = build_vf(starts, durs, lines_list)
    (WORK / "bars.vf").write_text(vf)
    tmp = WORK / "review_tmp.mp4"
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(concat_raw),
            "-i",
            str(FOLDER / "vo_padded.m4a"),
            "-filter_complex",
            f"[0:v]{vf}[v]",
            "-map",
            "[v]",
            "-map",
            "1:a",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            "-r",
            "30",
            "-movflags",
            "+faststart",
            str(tmp),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    delivered = probe(tmp)
    tmp.replace(OUT)

    # GATE: whole-file silencedetect -35dB:d=0.35 — no mid silence >0.40 except CTA≈1.5
    silences, raw_log = silencedetect(OUT, d=0.35)
    (WORK / "silencedetect_r4.txt").write_text(raw_log)
    bad = []
    for s, e, d in silences:
        if s >= vo_end - 0.08:
            # CTA hold — must be ≈1.5
            if not (1.2 <= d <= 1.65):
                bad.append((s, e, d, "cta_out_of_range"))
            continue
        if d > 0.40 + 1e-3:
            bad.append((s, e, d, "mid_gap"))
    silence_list = [
        {"start": round(s, 3), "end": round(e, 3), "dur": round(d, 3)}
        for s, e, d in silences
    ]
    print("SILENCE LIST:", json.dumps(silence_list, ensure_ascii=False))
    if bad:
        raise RuntimeError(f"silence gate failed: {bad}")

    max_mid = max((d for s, e, d in silences if s < vo_end - 0.08), default=0.0)
    cta_d = next((d for s, e, d in silences if s >= vo_end - 0.08), CTA)

    (FOLDER / "vo_starts.txt").write_text(
        "\n".join(f"{s:.3f},{d:.3f}" for s, d in zip(starts, durs)) + "\n"
    )
    (FOLDER / "vo_total.txt").write_text(f"{delivered:.3f}\n")

    timing = (
        f"review_r4 silence-pack (split on ？！。、)\n"
        f"lead={LEAD:.3f} gap={GAP:.3f} CTA={CTA:.3f}\n"
        f"clauses={len(clauses)}\n"
        + "\n".join(
            f"c{i:02d} start={starts[i]:.3f} dur={durs[i]:.3f} end={starts[i]+durs[i]:.3f} | {clauses[i]}"
            for i in range(len(clauses))
        )
        + f"\nVO_END={vo_end:.3f}\n"
        f"CTA_START={vo_end:.3f} CTA_DUR={CTA:.3f} CTA_END={vo_end+CTA:.3f}\n"
        f"TOTAL≈{delivered:.3f}\n"
        f"mid_cut={mid_cut:.3f} (符面≤{MID_MAX})\n"
        f"measured_max_mid_silence={max_mid:.3f}\n"
        f"measured_cta_silence={cta_d:.3f}\n"
        f"silenceremove=head+tail_areverse\n"
        f"gate=silencedetect_-35dB_d0.35_no_mid_>0.40_except_CTA\n"
    )
    (FOLDER / "TIMING_r4.txt").write_text(timing)
    (FOLDER / "TIMING.txt").write_text(timing)

    meta = {
        "id": "v05-hufumu",
        "path": str(OUT),
        "duration": round(delivered, 3),
        "vo_end": round(vo_end, 3),
        "cta": CTA,
        "mid_cut": round(mid_cut, 3),
        "measured_max_mid_silence": round(max_mid, 3),
        "measured_cta_silence": round(cta_d, 3),
        "silence_list": silence_list,
        "starts": [round(s, 3) for s in starts],
        "durs": [round(d, 3) for d in durs],
        "clauses": clauses,
        "hook_dur": round(durs[0], 3),
        "review_tag": "r4",
    }
    (WORK / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))

    spec = f"""# v05-hufumu EXPORT_SPEC (review_r4)

## Deliverable
- Path: `{OUT}`
- Spec: 1080×1920, 30fps, H.264 + AAC
- Duration: **{delivered:.3f}s**
- VO end: **{vo_end:.3f}s**
- CTA still: **{CTA:.3f}s** ({vo_end:.3f} → {vo_end+CTA:.3f})
- Status: review cut only — **未放行不发 / do not upload**

## Locked copy
See `COPY.md`. Hook: `{HOOK}`
Beats split on **？！。、** into separate TTS clauses (r3 fail was unsplit ④ ~6.4s with 0.796s mid silence).

## Clauses
{chr(10).join(f'- {c}' for c in clauses)}

## VO / 真裁气口
- Each clause: edge-tts → wav → silenceremove head+tail → concat with inserted gap **{GAP:.2f}s**
- Lead {LEAD:.2f}s; CTA silent **{CTA:.2f}s**
- Hook dur: **{durs[0]:.3f}s**
- **Gate:** `silencedetect=noise=-35dB:d=0.35` whole file — no mid silence >0.40 except CTA≈1.5
- measured_max_mid_silence: **{max_mid:.3f}s**
- measured_cta_silence: **{cta_d:.3f}s**
- silence_list: `{json.dumps(silence_list, ensure_ascii=False)}`

## Structure
| Seg | Time |
|-----|------|
| A firstframe motion | 0.000–{mid_cut:.3f} |
| B 符面 | {mid_cut:.3f}–{vo_end:.3f} |
| C CTA | {vo_end:.3f}–{vo_end+CTA:.3f} |

## 黄条
drawbox+drawtext `#F5C518` per clause; CTA no bar.

## Files
- `TIMING_r4.txt` (= `TIMING.txt`)
- `rebuild-r4/meta.json`
"""
    (FOLDER / "EXPORT_SPEC.md").write_text(spec)
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    print("OK", OUT)


if __name__ == "__main__":
    main()
