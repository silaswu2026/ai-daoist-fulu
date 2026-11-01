#!/usr/bin/env python3
"""Rebuild EP0 + v02–v05 with REAL silence discipline (silenceremove before concat)."""
from __future__ import annotations

import json
import math
import re
import subprocess
from pathlib import Path

ROOT = Path("/workspace/short-video")
EDGE = ROOT / ".venv/bin/edge-tts"
VOICE = "zh-CN-YunyangNeural"
RATE = "-12%"
PITCH = "-5Hz"
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
BAR_COLOR = "0xF5C518"
LEAD = 0.25
GAP = 0.35
CTA = 1.50
SAMPLE_RATE = 44100
MID_FULU_MAX = 10.0
NOISE_DB = "-35dB"
DETECT_D = 0.18

TRIM_AF = (
    "silenceremove=start_periods=1:start_duration=0.02:start_threshold=0.02:"
    "start_silence=0.025:detection=rms,"
    "areverse,"
    "silenceremove=start_periods=1:start_duration=0.05:start_threshold=0.02:"
    "start_silence=0.025:detection=rms,"
    "areverse"
)

# Each job: hook + beats. Beats may be multi-clause; we auto-split on ？！。 for TTS.
JOBS = [
    {
        "id": "v01-agent-fulu",
        "folder": ROOT / "v01-agent-fulu",
        "out_name": "v01-agent-fulu_review_r5.mp4",
        "review_tag": "r5",
        "title": "神仙＝模型",
        "first": "firstframe-shenxian.jpg",
        "mid": "hero-talisman.jpg",
        "ending": "ending-cta-r4.jpg",
        "segA": "segA.mp4",
        "segB": "segB.mp4",
        "use_still_mid": True,
        "hook": "我突然就悟了——神仙就是模型！",
        "beats": [
            "请大模型不就是请神吗？",
            "付 Token，不就是请福吗？烧多少，花多少。",
            "提示词就是诉求——想求啥，得说清楚。",
            "师承不对口？API 接错人，全跑偏。",
            "念咒调八百遍？那叫瞎调。",
        ],
        # bar text per spoken clause after flatten (hook + split beats)
        # filled at runtime if omitted; optional override list of list[str]
        "fulu_after_clause": 3,  # 0-based among ALL spoken clips after flatten: after Token clause
        "splice_note": "HOOK_SPLICE@after_lead: single-line hook only; mapping beats locked.",
    },
    {
        "id": "v02-qishiye",
        "folder": ROOT / "v02-qishiye",
        "out_name": "v02-qishiye_review_r4.mp4",
        "review_tag": "r4",
        "title": "起事业",
        "first": "firstframe-qishiye.jpg",
        "mid": "mid-fulu-qishiye.jpg",
        "ending": "ending-cta.jpg",
        "segA": "segA.mp4",
        "segB": "segB.mp4",
        "use_still_mid": False,
        "hook": "起事业——请神，不就是调模型吗？",
        "beats": [
            "今日请的，是文昌帝君——",
            "我给大模型的诉求是：「助我事业开运，步步清晰。」",
            "符上落了：开运、升迁、贵人。",
            "愿事业顺遂，路越走越宽。想自己生成一张——链接见主页／评论置顶。",
        ],
        "fulu_after_clause": None,  # auto: first clause containing 符上落了
        "splice_note": "HOOK_SPLICE@after_lead: replace/extend hook VO+bar only; four beats locked.",
    },
    {
        "id": "v03-qifacai",
        "folder": ROOT / "v03-qifacai",
        "out_name": "v03-qifacai_review_r3.mp4",
        "review_tag": "r3",
        "title": "起发财",
        "first": "firstframe-qifacai.jpg",
        "mid": "mid-fulu-qifacai.jpg",
        "ending": "ending-cta.jpg",
        "segA": "segA.mp4",
        "segB": "segB.mp4",
        "use_still_mid": False,
        "hook": "起发财——付 Token，不就是请福吗？",
        "beats": [
            "今日请的，是财神赵公明——",
            "我给大模型的诉求是：「助我财运畅通，进账有路。」",
            "符上落了：进宝、开源、不漏财。",
            "愿财源稳进，不慌不贪。想自己生成一张——链接见主页／评论置顶。",
        ],
        "fulu_after_clause": None,
        "splice_note": "HOOK_SPLICE@after_lead: replace/extend hook VO+bar only; four beats locked.",
    },
    {
        "id": "v04-shenti-pingan",
        "folder": ROOT / "v04-shenti-pingan",
        "out_name": "v04-shenti-pingan_review_r3.mp4",
        "review_tag": "r3",
        "title": "身体平安",
        "first": "firstframe-shenti-pingan.jpg",
        "mid": "mid-fulu-shenti-pingan.jpg",
        "ending": "ending-cta.jpg",
        "segA": "segA.mp4",
        "segB": "segB.mp4",
        "use_still_mid": False,
        "hook": "护身——不就是给模型一道护身符吗？",
        "beats": [
            "今日请的，是药王孙思邈——",
            "我给大模型的诉求是：「护我身心安泰，少病少忧。」",
            "符上落了：安康、清气、稳眠。",
            "愿身体平安，日日轻安。想自己生成一张——链接见主页／评论置顶。",
        ],
        "fulu_after_clause": None,
        "splice_note": "HOOK_SPLICE@after_lead: replace/extend hook VO+bar only; four beats locked.",
    },
    {
        "id": "v05-hufumu",
        "folder": ROOT / "v05-hufumu",
        "out_name": "v05-hufumu_review_r3.mp4",
        "review_tag": "r3",
        "title": "护父母",
        "first": "firstframe-hufumu.jpg",
        "mid": "mid-fulu-hufumu.jpg",
        "ending": "ending-cta.jpg",
        "segA": "segA.mp4",
        "segB": "segB.mp4",
        "use_still_mid": False,
        "hook": "护父母——一纸符，就是一次调模型。",
        "beats": [
            "今日请的，是慈航道人——",
            "我给大模型的诉求是：「护我双亲安康，岁岁平安。」",
            "符上落了：慈安、延年、家宁。",
            "愿父母康健，福报绵长。想自己生成一张——链接见主页／评论置顶。",
        ],
        "fulu_after_clause": None,
        "splice_note": "HOOK_SPLICE@after_lead: replace/extend hook VO+bar only; four beats locked.",
    },
]


def run(cmd, **kw):
    print("+", " ".join(str(c) for c in cmd)[:260])
    subprocess.check_call(cmd, **kw)


def probe_dur(path: Path) -> float:
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
                str(path),
            ],
            text=True,
        ).strip()
    )


def split_clauses(text: str) -> list[str]:
    """Split on ？！。 keeping punct (+ optional closing quote) with the left clause."""
    text = text.strip()
    if not text:
        return []
    # delimiter: terminal punct optionally followed by a closing quote
    pieces = re.split(r"([？！。][」』\"]?)", text)
    out: list[str] = []
    buf = ""
    for part in pieces:
        if not part:
            continue
        buf += part
        if re.fullmatch(r"[？！。][」』\"]?", part):
            out.append(buf.strip())
            buf = ""
    if buf.strip():
        out.append(buf.strip())
    cleaned: list[str] = []
    for c in out:
        if re.fullmatch(r"[」』\"'》\s]+", c) and cleaned:
            cleaned[-1] += c
        elif c:
            cleaned.append(c)
    return cleaned or [text]


def bar_lines_for(text: str) -> list[str]:
    """1 or 2 lines for yellow bar from a clause."""
    t = text.strip()
    # Prefer natural break at —— or ： or ， if long
    if len(t) <= 18:
        return [t]
    for sep in ("——", "：", "，"):
        if sep in t:
            a, b = t.split(sep, 1)
            left = (a + sep).strip() if sep != "，" else a.strip() + sep
            right = b.strip()
            if sep == "，":
                left = a.strip() + "，"
            if 4 <= len(left) <= 20 and right:
                return [left, right]
    # hard wrap ~16 chars
    if len(t) > 20:
        return [t[:16], t[16:]]
    return [t]


def edge_tts(text: str, out: Path):
    out.parent.mkdir(parents=True, exist_ok=True)
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


def to_wav_raw(src: Path, dst: Path):
    run(
        ["ffmpeg", "-y", "-i", str(src), "-ac", "1", "-ar", str(SAMPLE_RATE), str(dst)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def trim_silence(src: Path, dst: Path):
    run(
        ["ffmpeg", "-y", "-i", str(src), "-af", TRIM_AF, str(dst)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def make_silence(path: Path, dur: float):
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"anullsrc=r={SAMPLE_RATE}:cl=mono",
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


def wav_to_m4a(wav: Path, m4a: Path):
    run(
        ["ffmpeg", "-y", "-i", str(wav), "-c:a", "aac", "-b:a", "192k", str(m4a)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def fit_segment(src: Path, dur: float, out: Path, fps=30):
    src_dur = probe_dur(src)
    if src_dur >= dur - 0.05:
        vf = (
            f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            f"trim=duration={dur:.3f},setpts=PTS-STARTPTS,fps={fps},format=yuv420p"
        )
        run(
            [
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
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        loops = int(math.ceil(dur / max(src_dur, 0.01))) + 1
        vf = (
            "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            f"setpts=PTS-STARTPTS,fps={fps},format=yuv420p"
        )
        run(
            [
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
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def still_video(img: Path, dur: float, out: Path, fps=30, zoom=True):
    if zoom:
        vf = (
            f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            f"zoompan=z='min(1.08,1+0.0015*on)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={max(int(dur * fps), 1)}:s=1080x1920:fps={fps},format=yuv420p"
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
            str(fps),
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


def esc_text(s: str) -> str:
    return (
        s.replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
        .replace("%", "%%")
    )


def build_vf(starts, durs, lines_list) -> str:
    parts = []
    for s, d, lines in zip(starts, durs, lines_list):
        e = s + d
        enable = f"between(t\\,{s:.3f}\\,{e:.3f})"
        if len(lines) == 1:
            y, h = 1540, 118
            parts.append(
                f"drawbox=x=65:y={y}:w=950:h={h}:color={BAR_COLOR}@1:t=fill:enable='{enable}'"
            )
            parts.append(
                f"drawtext=fontfile={FONT}:text='{esc_text(lines[0])}':fontcolor=black:fontsize=46:"
                f"x=(w-text_w)/2:y={y}+36:enable='{enable}'"
            )
        else:
            y, h = 1480, 198
            parts.append(
                f"drawbox=x=65:y={y}:w=950:h={h}:color={BAR_COLOR}@1:t=fill:enable='{enable}'"
            )
            parts.append(
                f"drawtext=fontfile={FONT}:text='{esc_text(lines[0])}':fontcolor=black:fontsize=42:"
                f"x=(w-text_w)/2:y={y}+36:enable='{enable}'"
            )
            parts.append(
                f"drawtext=fontfile={FONT}:text='{esc_text(lines[1])}':fontcolor=black:fontsize=42:"
                f"x=(w-text_w)/2:y={y}+112:enable='{enable}'"
            )
    return ",".join(parts)


def measure_silences(audio_path: Path, until: float | None = None):
    cmd = ["ffmpeg", "-i", str(audio_path)]
    if until is not None:
        cmd += ["-t", f"{until:.3f}"]
    cmd += ["-af", f"silencedetect=noise={NOISE_DB}:d={DETECT_D}", "-f", "null", "-"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    text = proc.stderr
    starts = [float(x) for x in re.findall(r"silence_start:\s*([0-9.]+)", text)]
    ends = re.findall(
        r"silence_end:\s*([0-9.]+)\s*\|\s*silence_duration:\s*([0-9.]+)", text
    )
    out = []
    ei = 0
    for s in starts:
        if ei < len(ends):
            e, d = float(ends[ei][0]), float(ends[ei][1])
            out.append((s, e, d))
            ei += 1
        else:
            end_t = until if until is not None else probe_dur(audio_path)
            out.append((s, end_t, max(0.0, end_t - s)))
    return out


def measured_interseg_gaps(silences, starts, durs, vo_end) -> list[float]:
    """For each planned gap between clip i and i+1, measure silence overlapping that window."""
    gaps = []
    for i in range(len(starts) - 1):
        gap_start = starts[i] + durs[i]
        gap_end = starts[i + 1]
        # expected ~GAP; measure max silence fully covering this window
        # Find silence region that overlaps [gap_start, gap_end]
        best = 0.0
        for s, e, d in silences:
            cs = max(s, gap_start - 0.05)
            ce = min(e, gap_end + 0.05)
            if ce > cs:
                best = max(best, ce - cs)
        # also direct planned length
        planned = gap_end - gap_start
        gaps.append(max(best, planned * 0))  # prefer measured overlap
        # If no silence detected overlapping, use planned (speech bled) — count planned
        if best < 0.05:
            gaps[-1] = planned
        else:
            gaps[-1] = best
    return gaps


def flatten_spoken(job):
    clauses = [job["hook"]]
    for b in job["beats"]:
        clauses.extend(split_clauses(b))
    return clauses


def rebuild(job: dict) -> dict:
    folder: Path = job["folder"]
    vo_dir = folder / "vo"
    vo_dir.mkdir(exist_ok=True)
    work = folder / f"rebuild-{job['review_tag']}"
    work.mkdir(exist_ok=True)

    clauses = flatten_spoken(job)
    bar_lines = [bar_lines_for(c) for c in clauses]
    names = ["hook"] + [f"c{i:02d}" for i in range(1, len(clauses))]

    trim_wavs = []
    durs = []
    for idx, (name, text) in enumerate(zip(names, clauses)):
        # keep hook filename stable
        fname = "hook" if idx == 0 else f"s{idx:02d}"
        mp3 = vo_dir / f"{fname}.mp3"
        raw = vo_dir / f"{fname}_raw.wav"
        trim = vo_dir / f"{fname}.wav"
        edge_tts(text, mp3)
        to_wav_raw(mp3, raw)
        trim_silence(raw, trim)
        d = probe_dur(trim)
        trim_wavs.append(trim)
        durs.append(d)
        print(f"  {fname}: raw={probe_dur(raw):.3f} trim={d:.3f} — {text}")

    if durs[0] > 3.05:
        print(f"WARNING: hook trim dur {durs[0]:.3f} > 3.0s")

    lead = vo_dir / "lead_p.wav"
    gap = vo_dir / "gap_p.wav"
    make_silence(lead, LEAD)
    make_silence(gap, GAP)

    parts = [lead, trim_wavs[0]]
    for w in trim_wavs[1:]:
        parts.append(gap)
        parts.append(w)
    vo_wav = work / "vo_full.wav"
    concat_wavs(parts, vo_wav)
    wav_to_m4a(vo_wav, folder / "vo_full.m4a")

    starts = []
    t = LEAD
    starts.append(t)
    t += durs[0]
    for i in range(1, len(durs)):
        t += GAP
        starts.append(t)
        t += durs[i]
    vo_end = t
    got = probe_dur(vo_wav)
    assert abs(vo_end - got) < 0.08, (vo_end, got)

    (folder / "vo_starts.txt").write_text(
        "\n".join(f"{s:.3f},{d:.3f}" for s, d in zip(starts, durs)) + "\n"
    )
    (work / "clauses.txt").write_text("\n".join(clauses) + "\n")

    # fulu cut index
    fulu_idx = job.get("fulu_after_clause")
    if fulu_idx is None:
        fulu_idx = next(
            (i for i, c in enumerate(clauses) if "符上落了" in c),
            min(3, len(clauses) - 1),
        )
    beat_fulu_start = starts[fulu_idx]
    mid_cut = beat_fulu_start - 0.40
    if fulu_idx >= 1:
        mid_cut = max(mid_cut, starts[fulu_idx - 1] + durs[fulu_idx - 1] * 0.45)
    mid_cut = max(mid_cut, starts[0] + durs[0])
    mid_cut = min(mid_cut, MID_FULU_MAX, vo_end - 0.5)
    mid_cut = max(0.8, mid_cut)

    segA = work / "segA_fit.mp4"
    segB = work / "segB_fit.mp4"
    segC = work / "segC_cta.mp4"
    fit_segment(folder / job["segA"], mid_cut, segA)
    if job.get("use_still_mid"):
        still_video(folder / job["mid"], vo_end - mid_cut, segB, zoom=True)
    else:
        fit_segment(folder / job["segB"], vo_end - mid_cut, segB)
    still_video(folder / job["ending"], CTA, segC, zoom=False)

    concat_list = work / "concat.txt"
    concat_list.write_text(
        f"file '{segA.resolve()}'\nfile '{segB.resolve()}'\nfile '{segC.resolve()}'\n"
    )
    concat_raw = work / "concat_raw.mp4"
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_list),
            "-c",
            "copy",
            str(concat_raw),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    cta_sil = work / "cta_sil.wav"
    make_silence(cta_sil, CTA)
    vo_pad_wav = work / "vo_padded.wav"
    concat_wavs([vo_wav, cta_sil], vo_pad_wav)
    wav_to_m4a(vo_pad_wav, folder / "vo_padded.m4a")

    sil_vo = measure_silences(vo_wav, until=vo_end + 0.05)
    inter = measured_interseg_gaps(sil_vo, starts, durs, vo_end)
    measured_max_gap = max(inter) if inter else 0.0
    print(
        f"  interseg_gaps={[round(x,3) for x in inter]} max={measured_max_gap:.3f} mid_cut={mid_cut:.3f} hook={durs[0]:.3f}"
    )
    if measured_max_gap > 0.40 + 0.02:
        raise RuntimeError(
            f"{job['id']}: measured_max_gap {measured_max_gap:.3f} > 0.40 — abort"
        )

    # Also ensure no runaway mid-clause silence >0.55 inside any single trimmed wav
    for i, w in enumerate(trim_wavs):
        internal = measure_silences(w)
        for s, e, d in internal:
            # ignore tiny edge pads ≤0.06
            if 0.05 < s and e < probe_dur(w) - 0.05 and d > 0.55:
                print(f"  WARN internal silence {d:.3f}s in clip {i}: {clauses[i][:24]}")

    vf = build_vf(starts, durs, bar_lines)
    (work / "bars.vf").write_text(vf)
    out_path = folder / job["out_name"]
    tmp = work / "review_tmp.mp4"
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(concat_raw),
            "-i",
            str(folder / "vo_padded.m4a"),
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
    delivered = probe_dur(tmp)
    tmp.replace(out_path)

    # re-measure on final
    sil_final = measure_silences(out_path, until=vo_end + 0.05)
    inter = measured_interseg_gaps(sil_final, starts, durs, vo_end)
    measured_max_gap = max(inter) if inter else 0.0
    if measured_max_gap > 0.42:
        raise RuntimeError(
            f"{job['id']}: FINAL measured_max_gap {measured_max_gap:.3f} > 0.40"
        )

    # CTA silence check on padded audio
    sil_pad = measure_silences(vo_pad_wav)
    cta_sil_dur = 0.0
    for s, e, d in sil_pad:
        if s >= vo_end - 0.08:
            cta_sil_dur = max(cta_sil_dur, e - vo_end)
    cta_sil_dur = min(cta_sil_dur, CTA)

    meta = {
        "id": job["id"],
        "path": str(out_path),
        "duration": round(delivered, 3),
        "vo_end": round(vo_end, 3),
        "cta": round(CTA, 3),
        "cta_silence_measured": round(cta_sil_dur, 3),
        "mid_cut": round(mid_cut, 3),
        "gaps_planned": GAP,
        "lead": LEAD,
        "measured_max_gap": round(measured_max_gap, 3),
        "interseg_gaps": [round(x, 3) for x in inter],
        "hook_dur": round(durs[0], 3),
        "starts": [round(s, 3) for s in starts],
        "durs": [round(d, 3) for d in durs],
        "clauses": clauses,
        "trim_af": TRIM_AF,
        "splice_note": job["splice_note"],
        "review_tag": job["review_tag"],
    }
    (work / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    (folder / "vo_total.txt").write_text(f"{delivered:.3f}\n")
    (folder / "TIMING.txt").write_text(
        f"planned_total_vo_plus_cta={vo_end+CTA:.3f}\n"
        f"delivered_duration={delivered:.3f}\n"
        f"vo_end={vo_end:.3f}\n"
        f"cta={CTA:.3f}\n"
        f"cta_silence_measured={cta_sil_dur:.3f}\n"
        f"mid_cut={mid_cut:.3f}\n"
        f"gap_planned={GAP:.3f}\n"
        f"measured_max_gap={measured_max_gap:.3f}\n"
        f"interseg_gaps={','.join(f'{x:.3f}' for x in inter)}\n"
        f"lead={LEAD:.3f}\n"
        f"hook_dur={durs[0]:.3f}\n"
        f"silenceremove=head+tail_via_areverse_then_insert_gap\n"
        f"HOOK_SPLICE={job['splice_note']}\n"
    )

    spec = f"""# {job['id']} EXPORT_SPEC (review_{job['review_tag']})

## Deliverable
- Path: `{out_path}`
- Spec: 1080×1920, 30fps, H.264 + AAC
- Duration: **{delivered:.3f}s**
- VO end: **{vo_end:.3f}s**
- CTA still: **{CTA:.3f}s** ({vo_end:.3f} → {vo_end+CTA:.3f})
- Status: review cut only — **未放行不发 / do not upload**

## Locked copy
See `COPY.md`. Single-line hook ≤3s spoken + beats (clauses split on ？！。 for TTS). Ending CTA: `链接见主页／评论置顶`

## Structure
| Seg | Content | Time |
|-----|---------|------|
| A | First-frame motion + 钩 + early clauses | 0.000–{mid_cut:.3f} |
| B | 符面（≤10s 进，本切 @{mid_cut:.3f}s）+ remaining | {mid_cut:.3f}–{vo_end:.3f} |
| C | Ending CTA still | {vo_end:.3f}–{vo_end+CTA:.3f} |

## VO / 真裁气口
- Voice: `{VOICE}` · rate `{RATE}` · pitch `{PITCH}`
- **Each clause:** edge-tts → wav → **silenceremove head+tail** (areverse) → concat with **inserted gap {GAP:.2f}s only**
- Lead {LEAD:.2f}s; CTA silent hold **{CTA:.2f}s** (measured≈{cta_sil_dur:.3f}s)
- Hook spoken dur: **{durs[0]:.3f}s** (≤3.0)
- **measured_max_gap (inter-seg silencedetect {NOISE_DB}): `{measured_max_gap:.3f}s`** (must ≤0.40)
- interseg_gaps: {', '.join(f'{x:.3f}' for x in inter)}
- Clauses: {' | '.join(clauses)}
- Starts/durs: `{' / '.join(f'{s:.3f},{d:.3f}' for s,d in zip(starts,durs))}`

## 黄条
- ffmpeg drawbox+drawtext `#F5C518` 硬烧（NotoSansCJK-Bold）；每句口播条；片尾 CTA 不叠黄条

## HOOK_SPLICE
- {job['splice_note']}
- Hook VO: `{starts[0]:.3f}`–`{starts[0]+durs[0]:.3f}`

## Craft
- 首帧「{job['title']}」+「请神＝调模型」同框
- 符面 mid cut @ **{mid_cut:.3f}s** (≤10s)
- TTS 尾静音已裁；禁止再靠 TIMING 数字假装气口
"""
    (folder / "EXPORT_SPEC.md").write_text(spec)
    print(
        json.dumps(
            {
                k: meta[k]
                for k in (
                    "id",
                    "path",
                    "duration",
                    "vo_end",
                    "cta",
                    "measured_max_gap",
                    "mid_cut",
                    "hook_dur",
                )
            },
            ensure_ascii=False,
        )
    )
    return meta


def main():
    import sys
    only = set(sys.argv[1:]) if len(sys.argv) > 1 else None
    results = []
    # load prior report if partial
    summary = ROOT / "series-template" / "EP0_V05_SILENCE_REPORT.json"
    prior = []
    if only and summary.exists():
        try:
            prior = json.loads(summary.read_text())
        except Exception:
            prior = []
    for job in JOBS:
        if only and job["id"] not in only:
            continue
        print(f"\n==== rebuilding {job['id']} review_{job['review_tag']} ====")
        results.append(rebuild(job))
    if only and prior:
        by = {m["id"]: m for m in prior}
        for m in results:
            by[m["id"]] = m
        # keep job order
        results = [by[j["id"]] for j in JOBS if j["id"] in by]
    summary = ROOT / "series-template" / "EP0_V05_SILENCE_REPORT.json"
    summary.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print("\nDONE", summary)
    print("\nTABLE")
    print(
        f"{'path':<56} {'dur':>7} {'vo_end':>7} {'cta':>5} {'max_gap':>8}"
    )
    for m in results:
        print(
            f"{m['path']:<56} {m['duration']:7.3f} {m['vo_end']:7.3f} {m['cta']:5.2f} {m['measured_max_gap']:8.3f}"
        )


if __name__ == "__main__":
    main()
