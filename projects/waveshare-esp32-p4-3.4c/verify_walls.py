"""用最终实体与解析外表面法向截线核对普通侧壁，不冒充全局最薄壁证明。"""
import json
import math
import FreeCAD as App
import Part
from enclosure import ROOT,Design,digest


def main():
    out=ROOT/'output'
    info=json.loads((out/'validation.json').read_text(encoding='utf-8'))
    design=Design(info['parameters']);p=design.p
    doc=App.openDocument(str(out/'enclosure.FCStd'));body=doc.main_body.Shape
    samples=[];r=p['head_radius'];drop=p['waist_reduction']
    radius=(10000+drop**2)/(2*drop)
    for s in (-95,-80,-60,-30,0,25,45):
        if s>=0:
            x=math.sqrt(r*r-s*s);nx,ns=x/r,s/r
        else:
            dx=math.sqrt(radius*radius-s*s);x=r-radius+dx;nx,ns=dx/radius,s/radius
        for n in (20,35,50,65,80):
            for sign in (-1,1):
                point=design.point(sign*x,s,n)
                if point.z<5 or point.y<p['front_y']+4 or point.y>p['rear_y']-4:
                    continue
                normal=design.placement.Rotation.multVec(App.Vector(sign*nx,ns,0))
                line=Part.makeLine(point+normal*1,point-normal*8)
                section=body.common(line)
                length=sum(e.Length for e in section.Edges)
                samples.append({'local_x_s_n_mm':[sign*x,s,n],
                    'normal_material_length_mm':length,'passed':length>=2.0})
    transition=[];functional=[];design.make_mics()
    # 屏周锥形段的2.4mm径向差不等于法向壁厚，单独沿真实法线检查。
    outer=p['screen_radius']+p['screen_radial_gap']+p['wall'];end=p['screen_wrap_end_n']
    slope=(outer-p['head_radius'])/p['screen_transition_length']
    for n in (end+2,end+4,end+6):
        radius=outer-slope*(n-end)
        for angle in range(0,360,30):
            c,s=math.cos(math.radians(angle)),math.sin(math.radians(angle))
            point=design.point(radius*c,radius*s,n)
            normal=design.placement.Rotation.multVec(App.Vector(c,s,-slope).normalize())
            if any(pocket.isInside(point,.001,True) for pocket in design.mic_pockets.values()):
                # 下半圆过渡位于原下前面板之后，六条射线穿过内部导音件口袋。
                # 改核对真正朝外的前面板，不能把内腔误报漏壳，也不能直接跳过。
                line=Part.makeLine(design.point(radius*c,radius*s,p['front_n']-.1),
                    design.point(radius*c,radius*s,p['front_n']+p['wall']+.1))
                length=sum(e.Length for e in body.common(line).Edges)
                functional.append({'angle_deg':angle,'n_mm':n,'front_panel_material_length_mm':length,
                    'passed':length>=2.39,'classification':'内部麦克风装配口袋，核对其前方真实外面板'})
                continue
            line=Part.makeLine(point+normal,point-normal*8)
            edges=[e for e in body.common(line).Edges if e.distToShape(Part.Vertex(point))[0]<.001]
            length=sum(e.Length for e in edges)
            transition.append({'angle_deg':angle,'n_mm':n,'normal_material_length_mm':length,'passed':length>=2.15})
    result={'source_sha256':digest(ROOT/'enclosure.py'),'fcstd_sha256':digest(out/'enclosure.FCStd'),
        'sample_count':len(samples),'minimum_sampled_material_length_mm':min(s['normal_material_length_mm'] for s in samples),
        'minimum_required_mm':2.0,'passed':len(samples)>=20 and all(s['passed'] for s in samples)
            and len(transition)+len(functional)==36 and all(s['passed'] for s in transition+functional),
        'screen_transition_sample_count':len(transition),'screen_transition_minimum_required_mm':2.15,
        'screen_transition_minimum_normal_wall_mm':min(s['normal_material_length_mm'] for s in transition),
        'screen_transition_samples':transition,
        'internal_mic_pocket_front_panel_samples':functional,
        'samples':samples,'limitations':['仅普通侧壁有限法向截线；不包含前缘、底板、孔、槽及所有曲面极值',
            '筋和支座可增加截线材料长度；不将结果解释为全局最小壁厚']}
    (out/'wall_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('普通侧壁',result['sample_count'],'条截线，最低',result['minimum_sampled_material_length_mm'],'mm，',result['passed'])
    print('屏周过渡',len(transition),'条法向截线，最低',result['screen_transition_minimum_normal_wall_mm'],'mm')
    App.closeDocument(doc.Name)
    return result['passed']


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
