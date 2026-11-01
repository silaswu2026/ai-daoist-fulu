#!/usr/bin/env python3
"""Rebuild v02–v05 with audience 节奏包: hook + gaps≤0.4 + CTA≤1.5."""
from __future__ import annotations

import json
import math
import subprocess
import textwrap
from pathlib import Path

ROOT = Path("/workspace/short-video")
EDGE = ROOT / ".venv/bin/edge-tts"
VOICE = "zh-CN-YunyangNeural"
RATE = "-12%"
PITCH = "-5Hz"
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
LEAD = 0.25
GAP = 0.35  # ≤0.40
CTA = 1.50  # ≤1.50
SAMPLE_RATE = 44100
TRIM_AF = (
    "silenceremove=start_periods=1:start_duration=0.02:start_threshold=0.02:"
    "start_silence=0.03:detection=rms,"
    "areverse,"
    "silenceremove=start_periods=1:start_duration=0.05:start_threshold=0.02:"
    "start_silence=0.03:detection=rms,"
    "areverse"
)

# Four-beat spoken lines = locked original (黄条与原交稿一致). Hooks = latest COPY.
JOBS = [
    {
        "id": "v02-qishiye",
        "folder": ROOT / "v02-qishiye",
        "out_name": "v02-qishiye_review_r3.mp4",
        "review_tag": "r3",
        "title": "起事业",
        "first": "firstframe-qishiye.jpg",
        "mid": "mid-fulu-qishiye.jpg",
        "ending": "ending-cta.jpg",
        "hook": "起事业——请神，不就是调模型吗？",
        "beats": [
            "今日请的，是文昌帝君——",
            "我给大模型的诉求是：「助我事业开运，步步清晰。」",
            "符上落了：开运、升迁、贵人。",
            "愿事业顺遂，路越走越宽。想自己生成一张——链接见主页／评论置顶。",
        ],
        "bar": [
            "起事业——请神，不就是调模型吗？",
            "今日请的，是文昌帝君——",
            "我给大模型的诉求是：\\N「助我事业开运，步步清晰。」",
            "符上落了：开运、升迁、贵人。",
            "愿事业顺遂，路越走越宽。\\N想自己生成一张——链接见主页／评论置顶。",
        ],
        "splice_note": "HOOK_SPLICE@after_lead: replace/extend hook VO+bar only; four beats locked.",
    },
    {
        "id": "v03-qifacai",
        "folder": ROOT / "v03-qifacai",
        "out_name": "v03-qifacai_review_r2.mp4",
        "review_tag": "r2",
        "title": "起发财",
        "first": "firstframe-qifacai.jpg",
        "mid": "mid-fulu-qifacai.jpg",
        "ending": "ending-cta.jpg",
        "hook": "起发财——付 Token，不就是请福吗？",
        "beats": [
            "今日请的，是财神赵公明——",
            "我给大模型的诉求是：「助我财运畅通，进账有路。」",
            "符上落了：进宝、开源、不漏财。",
            "愿财源稳进，不慌不贪。想自己生成一张——链接见主页／评论置顶。",
        ],
        "bar": [
            "起发财——付 Token，不就是请福吗？",
            "今日请的，是财神赵公明——",
            "我给大模型的诉求是：\\N「助我财运畅通，进账有路。」",
            "符上落了：进宝、开源、不漏财。",
            "愿财源稳进，不慌不贪。\\N想自己生成一张——链接见主页／评论置顶。",
        ],
        "splice_note": "HOOK_SPLICE@after_lead: replace/extend hook VO+bar only; four beats locked.",
    },
    {
        "id": "v04-shenti-pingan",
        "folder": ROOT / "v04-shenti-pingan",
        "out_name": "v04-shenti-pingan_review_r2.mp4",
        "review_tag": "r2",
        "title": "身体平安",
        "first": "firstframe-shenti-pingan.jpg",
        "mid": "mid-fulu-shenti-pingan.jpg",
        "ending": "ending-cta.jpg",
        "hook": "护身——不就是给模型一道护身符吗？",
        "beats": [
            "今日请的，是药王孙思邈——",
            "我给大模型的诉求是：「护我身心安泰，少病少忧。」",
            "符上落了：安康、清气、稳眠。",
            "愿身体平安，日日轻安。想自己生成一张——链接见主页／评论置顶。",
        ],
        "bar": [
            "护身——不就是给模型一道护身符吗？",
            "今日请的，是药王孙思邈——",
            "我给大模型的诉求是：\\N「护我身心安泰，少病少忧。」",
            "符上落了：安康、清气、稳眠。",
            "愿身体平安，日日轻安。\\N想自己生成一张——链接见主页／评论置顶。",
        ],
        "splice_note": "HOOK_SPLICE@after_lead: replace/extend hook VO+bar only; four beats locked.",
    },
    {
        "id": "v05-hufumu",
        "folder": ROOT / "v05-hufumu",
        "out_name": "v05-hufumu_review_r2.mp4",
        "review_tag": "r2",
        "title": "护父母",
        "first": "firstframe-hufumu.jpg",
        "mid": "mid-fulu-hufumu.jpg",
        "ending": "ending-cta.jpg",
        "hook": "护父母——一纸符，就是一次调模型。",
        "beats": [
            "今日请的，是慈航道人——",
            "我给大模型的诉求是：「护我双亲安康，岁岁平安。」",
            "符上落了：慈安、延年、家宁。",
            "愿父母康健，福报绵长。想自己生成一张——链接见主页／评论置顶。",
        ],
        "bar": [
            "爸妈不在身边也想护住——\\N一纸符，就是一次调模型。",
            "今日请的，是慈航道人——",
            "我给大模型的诉求是：\\N「护我双亲安康，岁岁平安。」",
            "符上落了：慈安、延年、家宁。",
            "愿父母康健，福报绵长。\\N想自己生成一张——链接见主页／评论置顶。",
        ],
        "splice_note": "HOOK_SPLICE@after_lead: replace/extend hook VO+bar only; four beats locked.",
    },
]


def run(cmd, **kw):
    print("+", " ".join(str(c) for c in cmd)[:240])
    subprocess.check_call(cmd, **kw)


def probe_dur(path: Path) -> float:
    out = subprocess.check_output(
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
    return float(out)


def ass_time(t: float) -> str:
    if t < 0:
        t = 0
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


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


def to_wav(src: Path, dst: Path):
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-ac",
            "1",
            "-ar",
            str(SAMPLE_RATE),
            str(dst),
        ],
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
        [
            "ffmpeg",
            "-y",
            "-i",
            str(wav),
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(m4a),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def make_still_video(img: Path, dur: float, out: Path, fps=30):
    # Ken Burns-ish gentle zoom for motion feel on stills if no motion seg long enough
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
            f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(1.08,1+0.0015*on)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(dur*fps)}:s=1080x1920:fps={fps},format=yuv420p",
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


def fit_segment(src: Path, dur: float, out: Path, fps=30):
    """Loop or trim source motion clip to exact duration, 1080x1920."""
    src_dur = probe_dur(src)
    # scale+pad first via filter; use trim/loop
    if src_dur >= dur - 0.05:
        vf = f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,trim=duration={dur:.3f},setpts=PTS-STARTPTS,fps={fps},format=yuv420p"
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
        # loop input
        loops = int(math.ceil(dur / src_dur)) + 1
        vf = f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setpts=PTS-STARTPTS,fps={fps},format=yuv420p"
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


def write_ass(path: Path, events: list[tuple[float, float, str]], title: str):
    header = textwrap.dedent(
        f"""\
        [Script Info]
        Title: {title}
        ScriptType: v4.00+
        PlayResX: 1080
        PlayResY: 1920
        WrapStyle: 2

        [V4+ Styles]
        Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
        Style: YellowBar,Noto Sans CJK SC Bold,54,&H00000000,&H000000FF,&H00000000,&H0018C5F5,1,0,0,0,100,100,0,0,3,14,0,2,65,65,220,1

        [Events]
        Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
        """
    )
    lines = [header]
    for start, end, text in events:
        lines.append(
            f"Dialogue: 0,{ass_time(start)},{ass_time(end)},YellowBar,,0,0,0,,{text}\n"
        )
    path.write_text("".join(lines), encoding="utf-8")


def rebuild(job: dict) -> dict:
    folder: Path = job["folder"]
    vo_dir = folder / "vo"
    vo_dir.mkdir(exist_ok=True)
    work = folder / f"rebuild-{job['review_tag']}"
    work.mkdir(exist_ok=True)

    # 1) TTS hook + beats (regenerate all for consistent voice)
    texts = [job["hook"], *job["beats"]]
    names = ["hook", "s01", "s02", "s03", "s04"]
    mp3s = []
    wavs = []
    durs = []
    for name, text in zip(names, texts):
        mp3 = vo_dir / f"{name}.mp3"
        wav = vo_dir / f"{name}.wav"
        edge_tts(text, mp3)
        raw = vo_dir / f"{name}_raw.wav"
        to_wav(mp3, raw)
        run(["ffmpeg","-y","-i",str(raw),"-af",TRIM_AF,str(wav)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        d = probe_dur(wav)
        mp3s.append(mp3)
        wavs.append(wav)
        durs.append(d)
        print(f"  {name}: {d:.3f}s — {text[:40]}")

    lead = vo_dir / "lead_p.wav"
    gap = vo_dir / "gap_p.wav"
    make_silence(lead, LEAD)
    make_silence(gap, GAP)

    # 2) concat VO: lead + hook + gap + s01 + gap + s02 + gap + s03 + gap + s04
    parts = [lead, wavs[0]]
    for w in wavs[1:]:
        parts.append(gap)
        parts.append(w)
    vo_wav = work / "vo_full.wav"
    concat_wavs(parts, vo_wav)
    vo_m4a = folder / "vo_full.m4a"
    wav_to_m4a(vo_wav, vo_m4a)

    # timing table
    # starts: hook after lead; then each beat after previous + gap
    starts = []
    t = LEAD
    starts.append(t)  # hook
    t += durs[0]
    for i in range(1, 5):
        t += GAP
        starts.append(t)
        t += durs[i]
    vo_end = t
    assert abs(vo_end - probe_dur(vo_wav)) < 0.05, (vo_end, probe_dur(vo_wav))

    # starts file: hook + 4 beats
    starts_txt = folder / "vo_starts.txt"
    starts_txt.write_text(
        "\n".join(f"{s:.3f},{d:.3f}" for s, d in zip(starts, durs)) + "\n"
    )

    # Cut to mid-fulu 0.40s before ③ (index 3) for punch — clamp after ② start
    beat3_start = starts[3]
    mid_cut = max(starts[2] + durs[2] * 0.85, beat3_start - 0.40)
    # ensure mid_cut after hook+① mostly done: at least after s01 end
    mid_cut = max(mid_cut, starts[1] + durs[1] * 0.5)
    seg_a_dur = mid_cut
    seg_b_dur = vo_end - mid_cut
    total = vo_end + CTA

    # 3) video segments
    segA = work / "segA_fit.mp4"
    segB = work / "segB_fit.mp4"
    segC = work / "segC_cta.mp4"
    # Prefer motion sources; if short, fit_segment loops
    fit_segment(folder / "segA.mp4", seg_a_dur, segA)
    fit_segment(folder / "segB.mp4", seg_b_dur, segB)
    # CTA from ending still
    run(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            str(folder / job["ending"]),
            "-t",
            f"{CTA:.3f}",
            "-vf",
            "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,format=yuv420p",
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            str(segC),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

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

    # 4) ASS yellow bars (hook + 4 beats); no bar on CTA
    events = []
    for i, (s, d, bar) in enumerate(zip(starts, durs, job["bar"])):
        events.append((s, s + d, bar))
    ass_path = folder / "subs.ass"
    write_ass(ass_path, events, job["id"])

    # pad audio to total with trailing silence already via CTA visual; mux
    # vo covers to vo_end; need silent pad CTA
    cta_sil = work / "cta_sil.wav"
    make_silence(cta_sil, CTA)
    vo_pad_wav = work / "vo_padded.wav"
    concat_wavs([vo_wav, cta_sil], vo_pad_wav)
    vo_pad_m4a = folder / "vo_padded.m4a"
    wav_to_m4a(vo_pad_wav, vo_pad_m4a)

    out_path = folder / job["out_name"]
    # burn ASS
    # escape ass path for ffmpeg
    ass_esc = str(ass_path).replace("\\", "/").replace(":", "\\:")
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(concat_raw),
            "-i",
            str(vo_pad_m4a),
            "-vf",
            f"ass={ass_esc}",
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
            str(out_path),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    delivered = probe_dur(out_path)
    meta = {
        "id": job["id"],
        "path": str(out_path),
        "duration": round(delivered, 3),
        "vo_end": round(vo_end, 3),
        "cta": round(CTA, 3),
        "mid_cut": round(mid_cut, 3),
        "gaps": GAP,
        "lead": LEAD,
        "starts": [round(s, 3) for s in starts],
        "durs": [round(d, 3) for d in durs],
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
        f"mid_cut={mid_cut:.3f}\n"
        f"gap={GAP:.3f}\n"
        f"lead={LEAD:.3f}\n"
        f"HOOK_SPLICE={job['splice_note']}\n"
    )

    # EXPORT_SPEC
    spec = f"""# {job['id']} EXPORT_SPEC (review_{job['review_tag']})

## Deliverable
- Path: `{out_path}`
- Spec: 1080×1920, 30fps, H.264 + AAC
- Duration: **{delivered:.3f}s**
- VO end: **{vo_end:.3f}s**
- CTA still: **{CTA:.3f}s** ({vo_end:.3f} → {vo_end+CTA:.3f})
- Status: review cut only — **未放行不发 / do not upload**

## Locked copy
See `COPY.md`. Hook + four beats. Ending CTA exact: `链接见主页／评论置顶`

## Structure
| Seg | Content | Time |
|-----|---------|------|
| A | First-frame motion + 钩 + ①②（至符面切点） | 0.000–{mid_cut:.3f} |
| B | 符中帧更早炸（切点≈③前0.4s）+ ③④ | {mid_cut:.3f}–{vo_end:.3f} |
| C | Ending CTA still | {vo_end:.3f}–{vo_end+CTA:.3f} |

## VO / 节奏包
- Voice: `{VOICE}` via `{EDGE}`
- Rate `{RATE}`, pitch `{PITCH}`
- Lead {LEAD:.2f}s; gaps **{GAP:.2f}s** (≤0.40); CTA silent hold **{CTA:.2f}s** (≤1.50)
- Starts/durs (hook,①,②,③,④): `{' / '.join(f'{s:.3f},{d:.3f}' for s,d in zip(starts,durs))}`
- Files: `vo/hook + s01–s04` → `vo_full.m4a` → `vo_padded.m4a`

## 黄条
- ASS YellowBar `#F5C518` 硬烧；钩 + 四段；片尾 CTA 画面自带文案，不叠黄条
- 四段主干文案与原交稿一致（`txt/b1..b4`）

## HOOK_SPLICE（开场钩插拔点）
- {job['splice_note']}
- Timeline marker: hook VO occupies `{starts[0]:.3f}`–`{starts[0]+durs[0]:.3f}`; replace that span + matching ASS event without shifting四段 if duration matched, else re-gap.

## Craft
- 毛笔字首帧保留主字「{job['title']}」+「请神＝调模型」同框（既有 firstframe，未重绘）
- 符面冲击提前：mid cut @ {mid_cut:.3f}s
- ④ 结束立刻接 CTA，无中段空挂、无长静音尾
"""
    (folder / "EXPORT_SPEC.md").write_text(spec)
    print(json.dumps(meta, ensure_ascii=False))
    return meta


def main():
    results = []
    for job in JOBS:
        print(f"\n==== rebuilding {job['id']} ====")
        results.append(rebuild(job))
    summary = ROOT / "series-template" / "V02_V05_PACING_REPORT.json"
    summary.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print("\nDONE", summary)


if __name__ == "__main__":
    main()
