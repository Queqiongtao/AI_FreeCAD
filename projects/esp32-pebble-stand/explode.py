# -*- coding: utf-8 -*-
"""S3 鹅卵石底座：爆炸图与视频配置。

用法（FreeCAD 自带 Python）：
    "D:\\Program\\FreeCAD 1.1\\bin\\python.exe" explode.py --mode still --t 0.0
    ... --mode keyframes
    ... --mode video
"""

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(ROOT))
sys.path.insert(0, REPO)

from shared.explode_render import pipeline  # noqa: E402

CONFIG = {
    "scene": {
        "doc": r"output\stand.FCStd",
        "npz": r"archive\explode_render\scene.npz",
        "manifest": r"archive\explode_render\scene.json",
        "deflection": 0.06,
        "angular": 0.25,
        "only": [
            "Mount_Carrier",
            "Rear_Cover",
            "Module_Reference",
            "Battery_Reference",
            "Speaker_Reference",
            "Speaker_Diaphragm_Reference",
            "Speaker_Tape_Reference",
            "Lock_Heads_Reference",
            "Lock_Shafts_Reference",
            "Lock_Inserts_Reference",
            "Original_Heads_Reference",
        ],
        "overrides": {
            "Mount_Carrier": 0.05,
            "Rear_Cover": 0.05,
            "Module_Reference": 0.08,
            "Speaker_Reference": 0.08,
        },
    },
    "frames_dir": r"archive\explode_frames",
    "front_objects": ["Module_Reference"],
    "back_objects": ["Rear_Cover"],
    "video": {
        "width": 1920,
        "height": 1080,
        "fps": 30,
        "seconds": 10,
        "ssaa": 2,
    },
    "camera": {
        "azimuth": [16.0, 54.0],
        "elevation": [7.0, 13.0],
        "fov": 28.0,
        "pingpong": True,
        "max_zoom_out": 2.60,
    },
    "output": {
        "mp4": r"output\exploded_view.mp4",
        "gif": r"output\exploded_view.gif",
        "poster": r"output\preview_exploded.png",
    },
    "poster_frame": 150,
    "groups": {
        "carrier": {
            "objects": ["Mount_Carrier"],
            "direction": "axis",
            "distance": 0.0,
            "expand": [0.0, 0.0],
            "collapse": [1.0, 1.0],
        },
        "battery": {
            "objects": ["Battery_Reference"],
            "direction": "front",
            "distance": 42.0,
            "expand": [1.3, 3.6],
            "collapse": [7.2, 8.8],
        },
        "module": {
            "objects": ["Module_Reference", "Original_Heads_Reference"],
            "direction": "front",
            "distance": 55.0,
            "expand": [1.1, 3.5],
            "collapse": [7.4, 9.1],
        },
        "inserts": {
            "objects": ["Lock_Inserts_Reference"],
            "direction": "axis",
            "distance": 12.0,
            "expand": [1.8, 3.8],
            "collapse": [7.0, 8.6],
        },
        "speaker": {
            "objects": ["Speaker_Reference", "Speaker_Diaphragm_Reference"],
            "direction": "axis",
            "distance": 34.0,
            "expand": [1.7, 4.0],
            "collapse": [7.0, 8.6],
        },
        "tape": {
            "objects": ["Speaker_Tape_Reference"],
            "direction": "axis",
            "distance": 48.0,
            "expand": [1.5, 3.8],
            "collapse": [7.2, 8.8],
        },
        "cover": {
            "objects": ["Rear_Cover"],
            "direction": "axis",
            "distance": 68.0,
            "expand": [1.0, 3.4],
            "collapse": [7.4, 9.2],
        },
        "lock_screws": {
            "objects": ["Lock_Heads_Reference", "Lock_Shafts_Reference"],
            "direction": "axis",
            "distance": 82.0,
            "expand": [0.9, 3.0],
            "collapse": [7.8, 9.4],
        },
    },
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("all", "export", "video", "still", "keyframes"), default="video")
    parser.add_argument("--t", type=float, default=0.45)
    parser.add_argument("--out", default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--start", type=int, default=0)
    args = parser.parse_args()

    result = pipeline.render_project(
        CONFIG,
        ROOT,
        mode=args.mode,
        still_t=args.t,
        still_path=args.out,
        frame_limit=args.limit,
        start_frame=args.start,
    )
    for item in result if isinstance(result, list) else result.values():
        print(item, flush=True)


if __name__ == "__main__":
    main()
