#!/usr/bin/env python3
"""Burn yellow bars via drawbox+drawtext — fixed single-line y (h=frame height bug)."""
from __future__ import annotations
import json, subprocess
from pathlib import Path

ROOT = Path('/workspace/short-video')
FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
BAR_COLOR = '0xF5C518'


def run(cmd):
    print('+', ' '.join(map(str, cmd))[:240])
    subprocess.check_call(cmd)


def probe(p):
    return float(subprocess.check_output(
        ['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(p)], text=True))


def esc_text(s: str) -> str:
    return (s.replace('\\', '\\\\')
             .replace(':', '\\:')
             .replace("'", "\\'")
             .replace('%', '%%'))


JOBS = [
  dict(id='v02-qishiye', review='r3', work='rebuild-r3', out='v02-qishiye_review_r3.mp4',
       lines=[
         ['起事业——请神，不就是调模型吗？'],
         ['今日请的，是文昌帝君——'],
         ['我给大模型的诉求是：', '「助我事业开运，步步清晰。」'],
         ['符上落了：开运、升迁、贵人。'],
         ['愿事业顺遂，路越走越宽。', '想自己生成一张——链接见主页／评论置顶。'],
       ]),
  dict(id='v03-qifacai', review='r2', work='rebuild-r2', out='v03-qifacai_review_r2.mp4',
       lines=[
         ['起发财——付 Token，不就是请福吗？'],
         ['今日请的，是财神赵公明——'],
         ['我给大模型的诉求是：', '「助我财运畅通，进账有路。」'],
         ['符上落了：进宝、开源、不漏财。'],
         ['愿财源稳进，不慌不贪。', '想自己生成一张——链接见主页／评论置顶。'],
       ]),
  dict(id='v04-shenti-pingan', review='r2', work='rebuild-r2', out='v04-shenti-pingan_review_r2.mp4',
       lines=[
         ['护身——不就是给模型一道护身符吗？'],
         ['今日请的，是药王孙思邈——'],
         ['我给大模型的诉求是：', '「护我身心安泰，少病少忧。」'],
         ['符上落了：安康、清气、稳眠。'],
         ['愿身体平安，日日轻安。', '想自己生成一张——链接见主页／评论置顶。'],
       ]),
  dict(id='v05-hufumu', review='r2', work='rebuild-r2', out='v05-hufumu_review_r2.mp4',
       lines=[
         ['爸妈不在身边也想护住——', '一纸符，就是一次调模型。'],
         ['今日请的，是慈航道人——'],
         ['我给大模型的诉求是：', '「护我双亲安康，岁岁平安。」'],
         ['符上落了：慈安、延年、家宁。'],
         ['愿父母康健，福报绵长。', '想自己生成一张——链接见主页／评论置顶。'],
       ]),
]


def build_vf(starts, durs, lines_list) -> str:
    parts = []
    for s, d, lines in zip(starts, durs, lines_list):
        e = s + d
        # commas OK inside single-quoted enable when whole graph is one argv
        enable = f"between(t\\,{s:.3f}\\,{e:.3f})"
        n = len(lines)
        if n == 1:
            y, h = 1540, 118
            parts.append(f"drawbox=x=65:y={y}:w=950:h={h}:color={BAR_COLOR}@1:t=fill:enable='{enable}'")
            # FIXED: do not use h (frame height); pin text inside box
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
    return ','.join(parts)


for job in JOBS:
    folder = ROOT / job['id']
    meta = json.loads((folder / job['work'] / 'meta.json').read_text())
    starts, durs = meta['starts'], meta['durs']
    vf = build_vf(starts, durs, job['lines'])
    (folder / job['work'] / 'bars.vf').write_text(vf)
    concat = folder / job['work'] / 'concat_raw.mp4'
    audio = folder / 'vo_padded.m4a'
    out = folder / job['out']
    tmp = folder / job['work'] / 'review_tmp.mp4'
    # write to tmp then mv — avoid corrupt partial
    run([
        'ffmpeg', '-y',
        '-i', str(concat),
        '-i', str(audio),
        '-filter_complex', f"[0:v]{vf}[v]",
        '-map', '[v]', '-map', '1:a',
        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-b:a', '192k', '-shortest', '-r', '30',
        '-movflags', '+faststart',
        str(tmp),
    ])
    dur = probe(tmp)
    tmp.replace(out)
    print(job['id'], 'OK', dur, '->', out)

    rd = folder / f"review-{job['review']}"
    rd.mkdir(exist_ok=True)
    for label, t in [('hook', starts[0] + min(1.2, durs[0]*0.4)),
                     ('b3', starts[3] + 0.5),
                     ('b1', starts[1] + 0.4)]:
        frame = rd / f'f_{label}_barcheck.jpg'
        run(['ffmpeg', '-y', '-ss', f'{t:.3f}', '-i', str(out), '-update', '1', '-frames:v', '1', str(frame)])

print('ALL DONE')
