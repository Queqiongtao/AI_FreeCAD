# -*- coding: utf-8 -*-
"""网格场景：读取 npz 缓存、计算装配轴与包围盒。"""

import json

import numpy as np


class Part:
    """一个零件的三角网格（世界坐标，mm）。"""

    def __init__(self, name, label, verts, faces):
        self.name = name
        self.label = label
        self.verts = verts.astype(np.float32)
        self.faces = faces.astype(np.int32)
        self.centroid = self._surface_centroid()
        self.bbox = (
            self.verts.min(axis=0).astype(np.float64),
            self.verts.max(axis=0).astype(np.float64),
        )

    def _surface_centroid(self):
        tri = self.verts[self.faces]
        cross = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        area = 0.5 * np.linalg.norm(cross, axis=1)
        total = area.sum()
        if total <= 1e-9:
            return self.verts.mean(axis=0).astype(np.float64)
        centers = tri.mean(axis=1)
        return (centers * area[:, None]).sum(axis=0) / total

    def offset_bounds(self, vector):
        low = self.bbox[0] + np.asarray(vector, dtype=np.float64)
        high = self.bbox[1] + np.asarray(vector, dtype=np.float64)
        return low, high


class Scene:
    """项目场景：零件集合 + 分类与几何统计。"""

    def __init__(self, parts, doc_path, triangles):
        self.parts = parts
        self.doc_path = doc_path
        self.triangles = triangles

    def __getitem__(self, name):
        for part in self.parts:
            if part.name == name:
                return part
        raise KeyError(name)

    def group_parts(self, names):
        return [self[name] for name in names]

    def union_bounds(self, offsets=None, names=None):
        """所有零件（可选带偏移/名称过滤）的并集包围盒。"""
        offsets = offsets or {}
        lows, highs = [], []
        for part in self.parts:
            if names is not None and part.name not in names:
                continue
            vector = offsets.get(part.name, (0.0, 0.0, 0.0))
            low, high = part.offset_bounds(vector)
            lows.append(low)
            highs.append(high)
        return np.min(lows, axis=0), np.max(highs, axis=0)


def load_scene(npz_path, manifest_path):
    """读取 export_meshes.py 生成的缓存。"""
    with open(manifest_path, encoding="utf-8") as handle:
        manifest = json.load(handle)
    data = np.load(npz_path)
    parts = []
    for item in manifest["objects"]:
        index = item["index"]
        parts.append(Part(
            item["name"],
            item.get("label", item["name"]),
            data["v%d" % index],
            data["f%d" % index],
        ))
    return Scene(parts, manifest.get("doc", ""), manifest.get("total_triangles", 0))


def assembly_axis(scene, front_names, back_names):
    """从前部零件质心指向后部零件质心，作为爆炸展开轴。"""
    front = np.mean([scene[name].centroid for name in front_names], axis=0)
    back = np.mean([scene[name].centroid for name in back_names], axis=0)
    vector = back - front
    length = float(np.linalg.norm(vector))
    if length < 1e-9:
        return np.array([0.0, 1.0, 0.0])
    return vector / length


def front_direction(scene, front_names, back_names):
    """装配轴的“向前”水平分量（指向观察者）。"""
    axis = assembly_axis(scene, front_names, back_names)
    flat = np.array([-axis[0], -axis[1], 0.0])
    length = float(np.linalg.norm(flat))
    if length < 1e-6:
        return np.array([0.0, -1.0, 0.0])
    return flat / length
