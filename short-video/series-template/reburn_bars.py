#!/usr/bin/env python3
"""Re-burn yellow bars with resolvable CJK font onto existing paced cuts."""
from __future__ import annotations
import json, subprocess, textwrap
from pathlib import Path

ROOT = Path('/workspace/short-video')
FONTFILE = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
FONTNAME = 'Noto Sans CJK SC'  # family name libass resolves; Bold via style flag


def run(cmd):
    print('+', ' '.join(map(str, cmd))[:200])
    subprocess.check_call(cmd)


def probe(p):
    return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(p)], text=True))


def ass_time(t: float) -> str:
    h=int(t//3600); m=int((t%3600)//60); s=t%60
    return f"{h}:{m:02d}:{s:05.2f}"


def write_ass(path: Path, events, title: str):
    header = textwrap.dedent(f'''\
    [Script Info]
    Title: {title}
    ScriptType: v4.00+
    PlayResX: 1080
    PlayResY: 1920
    WrapStyle: 2

    [V4+ Styles]
    Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
    Style: YellowBar,{FONTNAME},52,&H00000000,&H000000FF,&H00000000,&H0018C5F5,-1,0,0,0,100,100,0,0,3,16,0,2,55,55,210,1

    [Events]
    Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
    ''')
    lines=[header]
    for start,end,text in events:
        lines.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},YellowBar,,0,0,0,,{text}\n")
    path.write_text(''.join(lines), encoding='utf-8')


JOBS = [
  dict(id='v02-qishiye', review='r3', work='rebuild-r3', out='v02-qishiye_review_r3.mp4',
       bars=[
         '起事业——请神，不就是调模型吗？',
         '今日请的，是文昌帝君——',
         '我给大模型的诉求是：\\N「助我事业开运，步步清晰。」',
         '符上落了：开运、升迁、贵人。',
         '愿事业顺遂，路越走越宽。\\N想自己生成一张——链接见主页／评论置顶。',
       ]),
  dict(id='v03-qifacai', review='r2', work='rebuild-r2', out='v03-qifacai_review_r2.mp4',
       bars=[
         '起发财——付 Token，不就是请福吗？',
         '今日请的，是财神赵公明——',
         '我给大模型的诉求是：\\N「助我财运畅通，进账有路。」',
         '符上落了：进宝、开源、不漏财。',
         '愿财源稳进，不慌不贪。\\N想自己生成一张——链接见主页／评论置顶。',
       ]),
  dict(id='v04-shenti-pingan', review='r2', work='rebuild-r2', out='v04-shenti-pingan_review_r2.mp4',
       bars=[
         '护身——不就是给模型一道护身符吗？',
         '今日请的，是药王孙思邈——',
         '我给大模型的诉求是：\\N「护我身心安泰，少病少忧。」',
         '符上落了：安康、清气、稳眠。',
         '愿身体平安，日日轻安。\\N想自己生成一张——链接见主页／评论置顶。',
       ]),
  dict(id='v05-hufumu', review='r2', work='rebuild-r2', out='v05-hufumu_review_r2.mp4',
       bars=[
         '爸妈不在身边也想护住——\\N一纸符，就是一次调模型。',
         '今日请的，是慈航道人——',
         '我给大模型的诉求是：\\N「护我双亲安康，岁岁平安。」',
         '符上落了：慈安、延年、家宁。',
         '愿父母康健，福报绵长。\\N想自己生成一张——链接见主页／评论置顶。',
       ]),
]

for job in JOBS:
    folder = ROOT/job['id']
    meta = json.loads((folder/job['work']/'meta.json').read_text())
    starts, durs = meta['starts'], meta['durs']
    events = [(s, s+d, bar) for s,d,bar in zip(starts, durs, job['bars'])]
    ass = folder/'subs.ass'
    write_ass(ass, events, job['id'])

    concat = folder/job['work']/'concat_raw.mp4'
    audio = folder/'vo_padded.m4a'
    out = folder/job['out']
    # fontsdir helps libass find TTC
    ass_esc = str(ass).replace('\\','/').replace(':','\\:')
    fontsdir = '/usr/share/fonts/opentype/noto'
    run([
        'ffmpeg','-y','-i',str(concat),'-i',str(audio),
        '-vf', f"ass={ass_esc}:fontsdir={fontsdir}",
        '-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p',
        '-c:a','aac','-b:a','192k','-shortest','-r','30','-movflags','+faststart',
        str(out)
    ])
    dur = probe(out)
    print(job['id'], 'reburned', dur)

    # verify yellow pixels
    rd = folder/f"review-{job['review']}"
    rd.mkdir(exist_ok=True)
    t = starts[0] + min(1.0, durs[0]*0.5)
    frame = rd/'f_hook_barcheck.jpg'
    run(['ffmpeg','-y','-ss',f'{t:.3f}','-i',str(out),'-frames:v','1',str(frame)])

print('done')
