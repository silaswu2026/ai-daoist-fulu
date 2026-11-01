#!/usr/bin/env python3
"""Rebuild v08-hupengyou review_r2 with locked 顿悟钩 + audience 节奏包."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path("/workspace/short-video")
MOD = ROOT / "series-template" / "rebuild_pacing_v02_v05.py"

spec = importlib.util.spec_from_file_location("rebuild_pacing", MOD)
mod = importlib.util.module_from_spec(spec)
sys.modules["rebuild_pacing"] = mod
spec.loader.exec_module(mod)

job = {
    "id": "v08-hupengyou",
    "folder": ROOT / "v08-hupengyou",
    "out_name": "v08-hupengyou_review_r2.mp4",
    "review_tag": "r2",
    "title": "护朋友",
    "first": "firstframe-hupengyou.jpg",
    "mid": "mid-fulu-hupengyou.jpg",
    "ending": "ending-cta.jpg",
    "hook": "护朋友——请神，不就是调模型吗？一份义气，就是一次调模型。",
    "beats": [
        "今日请的，是关圣帝君——",
        "我给大模型的诉求是：「护我挚友义气长存，彼此照应。」",
        "符上落了：义气、互助、长久。",
        "愿好友相护，路远情在。想自己生成一张——链接见主页／评论置顶。",
    ],
    "bar": [
        "护朋友——请神，不就是调模型吗？\\N一份义气，就是一次调模型。",
        "今日请的，是关圣帝君——",
        "我给大模型的诉求是：\\N「护我挚友义气长存，彼此照应。」",
        "符上落了：义气、互助、长久。",
        "愿好友相护，路远情在。\\N想自己生成一张——链接见主页／评论置顶。",
    ],
    "splice_note": "HOOK_SPLICE@after_lead: replace/extend hook VO+bar only; four beats locked.",
}

# Prefer punchier mid: if mid still exists as source motion, rebuild uses segB.mp4.
# Ensure segA/segB exist.
folder = job["folder"]
assert (folder / "segA.mp4").exists(), "missing segA.mp4"
assert (folder / "segB.mp4").exists(), "missing segB.mp4"
assert (folder / job["ending"]).exists(), "missing ending"

print("==== rebuilding v08-hupengyou review_r2 ====")
meta = mod.rebuild(job)
(folder / "rebuild-r2" / "meta.json").write_text(
    json.dumps(meta, ensure_ascii=False, indent=2)
)
print("DONE", meta["path"])
