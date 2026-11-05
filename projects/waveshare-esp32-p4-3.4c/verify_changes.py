"""对照修复前的磁盘备份，核对七件兼容、模块位置及下部轮廓。"""
import argparse
import json
from pathlib import Path
import FreeCAD as App
from enclosure import ROOT,PART_LABELS,digest,box


def verify(out,baseline):
    before=App.openDocument(str(baseline/'output/enclosure.FCStd'))
    after=App.openDocument(str(out/'enclosure.FCStd'))
    changes={}
    for name in PART_LABELS:
        a=before.getObject(name).Shape;b=after.getObject(name).Shape
        changes[name]={'removed_mm3':a.cut(b).Volume,'added_mm3':b.cut(a).Volume}
        changes[name]['unchanged']=max(changes[name].values())<.001
    references={}
    for name in ('Module_Reference','Display_Visual'):
        a=before.getObject(name).Shape;b=after.getObject(name).Shape
        # 原厂模块1161件重复布尔代价高：比较对应实体的BRep及位置序列。
        references[name]=(len(a.Solids)==len(b.Solids) and a.exportBrepToString()==b.exportBrepToString())
    lower=box(-80,80,-60,60,0,40)
    a=before.main_body.Shape.common(lower);b=after.main_body.Shape.common(lower)
    lower_change=a.cut(b).Volume+b.cut(a).Volume
    passed=(not changes['main_body']['unchanged'] and all(v['unchanged'] for n,v in changes.items() if n!='main_body')
        and all(references.values()) and lower_change<.001)
    result={'passed':passed,'only_reprint':['main_body'] if passed else [],'parts':changes,
        'reference_geometry_and_position_unchanged':references,'lower_body_below_z40_difference_mm3':lower_change,
        'baseline_fcstd_sha256':digest(baseline/'output/enclosure.FCStd'),'fcstd_sha256':digest(out/'enclosure.FCStd'),
        'source_sha256':digest(ROOT/'enclosure.py'),'note':'仅与本次修复前备份比较，不代表实物配合已通过。'}
    (out/'revision_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    App.closeDocument(before.Name);App.closeDocument(after.Name)
    return passed


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=ROOT/'output');parser.add_argument('--baseline',type=Path)
    args=parser.parse_args()
    baseline=args.baseline
    if baseline is None:
        saved=json.loads((ROOT/'archive/screen_flush_work/baseline.json').read_text(encoding='utf-8'))
        baseline=Path(saved['baseline'])
    raise SystemExit(0 if verify(args.out.resolve(),baseline.resolve()) else 1)
