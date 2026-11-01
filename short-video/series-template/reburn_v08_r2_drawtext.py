#!/usr/bin/env python3
"""Reburn v08-hupengyou review_r2 yellow bars via drawbox+drawtext."""
from __future__ import annotations
import json, subprocess
from pathlib import Path
import importlib.util, sys

ROOT = Path('/workspace/short-video')
MOD = ROOT / 'series-template' / 'reburn_drawtext.py'
spec = importlib.util.spec_from_file_location('reburn_dt', MOD)
mod = importlib.util.module_from_spec(spec)
sys.modules['reburn_dt'] = mod
spec.loader.exec_module(mod)

folder = ROOT / 'v08-hupengyou'
work = folder / 'rebuild-r2'
meta = json.loads((work / 'meta.json').read_text())
starts, durs = meta['starts'], meta['durs']
lines = [
    ['护朋友——请神，不就是调模型吗？', '一份义气，就是一次调模型。'],
    ['今日请的，是关圣帝君——'],
    ['我给大模型的诉求是：', '「护我挚友义气长存，彼此照应。」'],
    ['符上落了：义气、互助、长久。'],
    ['愿好友相护，路远情在。', '想自己生成一张——链接见主页／评论置顶。'],
]
vf = mod.build_vf(starts, durs, lines)
vf_path = work / 'bars.vf'
vf_path.write_text(vf)
out = folder / 'v08-hupengyou_review_r2.mp4'
concat = work / 'concat_raw.mp4'
audio = folder / 'vo_padded.m4a'
mod.run([
    'ffmpeg', '-y',
    '-i', str(concat),
    '-i', str(audio),
    '-filter_complex', f'[0:v]{vf}[v]',
    '-map', '[v]', '-map', '1:a',
    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p',
    '-c:a', 'aac', '-b:a', '192k', '-shortest', '-r', '30',
    '-movflags', '+faststart',
    str(out),
])
dur = mod.probe(out)
print('v08 OK', dur)

# update EXPORT_SPEC 黄条 note
spec_path = folder / 'EXPORT_SPEC.md'
txt = spec_path.read_text()
txt = txt.replace(
    '- ASS YellowBar `#F5C518` 硬烧；钩 + 四段；片尾 CTA 画面自带文案，不叠黄条',
    '- ffmpeg **drawbox+drawtext** 硬烧 `#F5C518`（ASS 字体解析失败同系列）；钩 + 四段；片尾 CTA 画面自带文案，不叠黄条\n- 1 行：y=1540 h=118；2 行：y=1480 h=198；x=65 w=950'
)
# refresh duration if slightly changed
import re
txt = re.sub(r'Duration: \*\*[0-9.]+\*\*s', f'Duration: **{dur:.3f}s**', txt)
spec_path.write_text(txt)

rd = folder / 'review-r2'
rd.mkdir(exist_ok=True)
t = starts[0] + min(1.2, durs[0] * 0.4)
mod.run(['ffmpeg', '-y', '-ss', f'{t:.3f}', '-i', str(out), '-update', '1', '-frames:v', '1', str(rd / 'f_hook_barcheck.jpg')])
t3 = starts[3] + 0.5
mod.run(['ffmpeg', '-y', '-ss', f'{t3:.3f}', '-i', str(out), '-update', '1', '-frames:v', '1', str(rd / 'f_b3_barcheck.jpg')])
tcta = meta['vo_end'] + 0.3
mod.run(['ffmpeg', '-y', '-ss', f'{tcta:.3f}', '-i', str(out), '-update', '1', '-frames:v', '1', str(rd / 'f_cta_barcheck.jpg')])
print('frames OK')
