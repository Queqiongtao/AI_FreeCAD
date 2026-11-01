# -*- coding: utf-8 -*-
"""从 FCStd 导出三角网格缓存，供爆炸图渲染使用。

freecadcmd 会把命令行参数当成待打开文件，因此改用环境变量传参：
    EXPLODE_DOC        源 FCStd 路径（必需）
    EXPLODE_OUT        输出 npz 路径（必需）
    EXPLODE_MANIFEST   输出清单 json 路径（必需）
    EXPLODE_ONLY       只导出这些对象名，逗号分隔（可选）
    EXPLODE_DEFLECTION 默认三角化偏差，mm（默认 0.2）
    EXPLODE_ANGULAR    默认角度偏差（默认 0.25）
    EXPLODE_OVERRIDE   按对象覆写偏差，如 "Module_Reference=0.45"

打印件与参考体都从 FCStd 取装配位姿，避免 STL 的打印姿态。
"""

import json
import os

import FreeCAD
import numpy as np


def parse_overrides(text):
    result = {}
    if not text:
        return result
    for item in text.split(","):
        if "=" in item:
            name, value = item.split("=", 1)
            result[name.strip()] = float(value)
    return result


def bbox_of(points):
    return [
        float(points[:, 0].min()), float(points[:, 1].min()), float(points[:, 2].min()),
        float(points[:, 0].max()), float(points[:, 1].max()), float(points[:, 2].max()),
    ]


def main():
    doc_path = os.environ.get("EXPLODE_DOC")
    out_path = os.environ.get("EXPLODE_OUT")
    manifest_path = os.environ.get("EXPLODE_MANIFEST")
    missing = [name for name, value in (
        ("EXPLODE_DOC", doc_path),
        ("EXPLODE_OUT", out_path),
        ("EXPLODE_MANIFEST", manifest_path),
    ) if not value]
    if missing:
        raise RuntimeError("缺少环境变量：%s" % ", ".join(missing))
    if not os.path.isfile(doc_path):
        raise RuntimeError("源工程不存在：%s" % doc_path)
    only_text = os.environ.get("EXPLODE_ONLY", "")
    default_deflection = float(os.environ.get("EXPLODE_DEFLECTION", "0.2"))
    angular = float(os.environ.get("EXPLODE_ANGULAR", "0.25"))
    overrides = parse_overrides(os.environ.get("EXPLODE_OVERRIDE", ""))
    wanted = [n.strip() for n in only_text.split(",") if n.strip()]

    doc = FreeCAD.openDocument(doc_path)
    objects = []
    arrays = {}
    for obj in doc.Objects:
        if not hasattr(obj, "Shape") or obj.Shape.isNull():
            continue
        if wanted and obj.Name not in wanted:
            continue
        shape = obj.Shape
        deviation = overrides.get(obj.Name, default_deflection)
        points, facets = shape.tessellate(deviation)
        if not points or not facets:
            continue
        verts = np.array([[p.x, p.y, p.z] for p in points], dtype=np.float32)
        faces = np.array(facets, dtype=np.int32)

        # tessellate 通常已带 Shape 的 placement；仅在包围盒不一致时补变换。
        bb = shape.BoundBox
        shape_min = np.array([bb.XMin, bb.YMin, bb.ZMin], dtype=np.float64)
        if np.abs(verts.min(axis=0) - shape_min).max() > 1e-3:
            matrix = obj.Placement.toMatrix()
            verts = np.array(
                [matrix.multVec(FreeCAD.Vector(*p)) for p in verts], dtype=np.float32
            )

        index = len(objects)
        arrays["v%d" % index] = verts
        arrays["f%d" % index] = faces
        objects.append({
            "index": index,
            "name": obj.Name,
            "label": obj.Label,
            "triangles": int(len(faces)),
            "vertices": int(len(verts)),
            "deflection": deviation,
            "bbox": bbox_of(verts),
            "volume": float(shape.Volume),
        })
        print("导出 %-40s 三角面 %7d 偏差 %.2f" % (obj.Name, len(faces), deviation), flush=True)

    FreeCAD.closeDocument(doc.Name)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    np.savez_compressed(out_path, **arrays)
    manifest = {
        "doc": doc_path,
        "objects": objects,
        "total_triangles": sum(o["triangles"] for o in objects),
    }
    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
    print("总计 %d 个对象，%d 三角面" % (len(objects), manifest["total_triangles"]), flush=True)


if __name__ in ("__main__", "export_meshes"):
    try:
        main()
    except Exception as error:  # noqa: BLE001
        import sys
        import traceback
        traceback.print_exc()
        print("网格导出失败：%s" % error, flush=True)
        sys.exit(1)
