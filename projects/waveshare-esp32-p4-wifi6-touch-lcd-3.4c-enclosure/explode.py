# -*- coding: utf-8 -*-
"""P4 两件式外壳：爆炸图与视频配置。

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
        "doc": r"output\enclosure.FCStd",
        "npz": r"archive\explode_render\scene.npz",
        "manifest": r"archive\explode_render\scene.json",
        "deflection": 0.15,
        "angular": 0.25,
        "only": [],
        "overrides": {
            "Module_Reference": 0.45,
            "main_shell": 0.10,
            "rear_cover": 0.10,
            "Speaker_Reference": 0.20,
            "Speaker_Tape_Reference": 0.08,
            "M3_Heat_Inserts_Reference": 0.06,
        },
    },
    "frames_dir": r"archive\explode_frames",
    "front_objects": ["Module_Reference"],
    "back_objects": ["rear_cover"],
    "video": {
        "width": 1920,
        "height": 1080,
        "fps": 30,
        "seconds": 10,
        "ssaa": 2,
    },
    "camera": {
        "azimuth": [18.0, 56.0],
        "elevation": [10.0, 16.0],
        "fov": 28.0,
        "pingpong": True,
        "max_zoom_out": 1.55,
    },
    "output": {
        "mp4": r"output\exploded_view.mp4",
        "gif": r"output\exploded_view.gif",
        "poster": r"output\preview_exploded.png",
    },
    "poster_frame": 150,
    "groups": {
        "carrier": {
            "objects": ["main_shell"],
            "direction": "axis",
            "distance": 0.0,
            "expand": [0.0, 0.0],
            "collapse": [1.0, 1.0],
        },
        "module": {
            "objects": ["Module_Reference", "Internal_USB_Plug_Reference"],
            "direction": "front",
            "distance": 80.0,
            "expand": [1.2, 3.6],
            "collapse": [7.2, 9.0],
        },
        "module_screws": {
            "objects": ["Module_M25_Heads_Reference", "Module_M25_Shafts_Reference"],
            "direction": "front",
            "distance": 64.0,
            "expand": [1.4, 3.6],
            "collapse": [7.4, 9.0],
        },
        "inserts": {
            "objects": ["M3_Heat_Inserts_Reference"],
            "direction": "axis",
            "distance": 14.0,
            "expand": [1.8, 3.8],
            "collapse": [7.0, 8.6],
        },
        "speaker": {
            "objects": ["Speaker_Reference", "Speaker_Radiating_Faces_Reference"],
            "direction": "axis",
            "distance": 46.0,
            "expand": [1.7, 4.0],
            "collapse": [7.0, 8.6],
        },
        "tape": {
            "objects": ["Speaker_Tape_Reference"],
            "direction": "axis",
            "distance": 62.0,
            "expand": [1.5, 3.8],
            "collapse": [7.2, 8.8],
        },
        "cover": {
            "objects": ["rear_cover"],
            "direction": "axis",
            "distance": 96.0,
            "expand": [1.0, 3.4],
            "collapse": [7.4, 9.2],
        },
        "lock_screws": {
            "objects": ["M3_Heads_Reference", "M3_Shafts_Reference"],
            "direction": "axis",
            "distance": 118.0,
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
