"""读取挤出路径，并用 STL 截面校准切片器自动旋转和平移。"""
import bisect
import math
import struct


def read_mesh(data):
    triangles=[]
    for i in range(struct.unpack_from('<I',data,80)[0]):
        v=struct.unpack_from('<12f',data,84+i*50)
        triangles.append(tuple(v[j:j+3] for j in (3,6,9)))
    return triangles


def read_extrusions(text,dx,dy):
    import re
    layers={}
    x=y=e=z=0.0
    relative=False
    feature=''
    width=0.45
    support_filament=0.0
    for line in text.splitlines():
        if line.startswith('; Z_HEIGHT:'):
            z=round(float(line.split(':')[1]),3)
        elif line.startswith('; FEATURE:'):
            feature=line.split(':',1)[1].strip()
        elif line.startswith('; LINE_WIDTH:'):
            width=float(line.split(':')[1])
        command=line.split(';')[0].strip()
        if command=='M83':
            relative=True
        elif command=='M82':
            relative=False
        if command.startswith('G92 '):
            values=dict(re.findall(r'([XYE])([-+\d.]+)',command))
            if 'E' in values:e=float(values['E'])
            continue
        if not command.startswith(('G0 ','G1 ')):
            continue
        values={k:float(v) for k,v in re.findall(r'([XYE])([-+\d.]+)',command)}
        nx,ny=values.get('X',x),values.get('Y',y)
        de=(values.get('E',0) if relative else values.get('E',e)-e)
        if 'E' in values:e=(e+values['E'] if relative else values['E'])
        if de>0 and (nx!=x or ny!=y) and feature not in ('Custom','Skirt','Brim',''):
            layers.setdefault(z,[]).append(((x-dx,y-dy),(nx-dx,ny-dy),feature,width))
            if 'support' in feature.lower():support_filament+=de
        x,y=nx,ny
    return layers,support_filament*math.pi*(1.75/2)**2


def distance2(p,a,b):
    ux,uy=b[0]-a[0],b[1]-a[1]
    t=max(0,min(1,((p[0]-a[0])*ux+(p[1]-a[1])*uy)/(ux*ux+uy*uy or 1)))
    return (p[0]-a[0]-t*ux)**2+(p[1]-a[1]-t*uy)**2


def grid(segments):
    cells={}
    for index,(a,b,_,width) in enumerate(segments):
        for x in range(math.floor((min(a[0],b[0])-width)/2),math.floor((max(a[0],b[0])+width)/2)+1):
            for y in range(math.floor((min(a[1],b[1])-width)/2),math.floor((max(a[1],b[1])+width)/2)+1):
                cells.setdefault((x,y),[]).append(index)
    return segments,cells


def covered(p,index,extra):
    segments,cells=index
    for i in cells.get((math.floor(p[0]/2),math.floor(p[1]/2)),[]):
        a,b,_,width=segments[i]
        if distance2(p,a,b)<=(width/2+extra)**2:return True
    return False


def section(triangles,height):
    segments=[]
    for vertices in triangles:
        if not min(v[2] for v in vertices)<height<max(v[2] for v in vertices):continue
        points=[]
        for a,b in zip(vertices,vertices[1:]+vertices[:1]):
            if (a[2]-height)*(b[2]-height)<0:
                t=(height-a[2])/(b[2]-a[2])
                points.append((a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])))
        if len(points)==2 and math.dist(*points)>0.0001:segments.append(points)
    return segments


def align_extrusions(triangles,layers,box):
    """切片器自动排版会旋转 STL；用包围尺寸及实际截面确定刚体变换。"""
    vertices=[v for t in triangles for v in t]
    zs=sorted(z for z,segments in layers.items() if any('wall' in s[2].lower() for s in segments))
    selected=sorted(set(zs[round((len(zs)-1)*f)] for f in (0.08,0.30,0.65)))
    candidates=[]
    for angle in (0,90,180,270):
        c=round(math.cos(math.radians(angle)));s=round(math.sin(math.radians(angle)))
        points=[(c*v[0]-s*v[1],s*v[0]+c*v[1]) for v in vertices]
        xmin,xmax=min(p[0] for p in points),max(p[0] for p in points)
        ymin,ymax=min(p[1] for p in points),max(p[1] for p in points)
        error=max(abs(xmax-xmin-box['width']),abs(ymax-ymin-box['depth']))
        if error>0.25:continue
        # 报告包围框可能略微外扩；只将其中心作为平移初值。
        # 不缩放网格；此分支必须通过三高度实际墙线的更严格校准。
        centered=error>0.05
        dx,dy=box['x']-xmin,box['y']-ymin
        if centered:
            dx+=(box['width']-(xmax-xmin))/2
            dy+=(box['depth']-(ymax-ymin))/2
        total=found=0
        for z in selected:
            wall_index=grid([v for v in layers[z] if 'wall' in v[2].lower()])
            contour=section(triangles,z-0.1)
            for a,b in contour[::max(1,len(contour)//400)]:
                x,y=(a[0]+b[0])/2,(a[1]+b[1])/2
                total+=1
                if covered((c*x-s*y+dx,s*x+c*y+dy),wall_index,0.10):found+=1
        score=found/(total or 1)
        if centered and score<=0.95:continue
        candidates.append((score,angle,c,s,dx,dy,centered,error))
    assert candidates,'自动排版姿态无法与 STL 包围尺寸匹配'
    score,angle,c,s,dx,dy,centered,error=max(candidates)
    assert score>0.75,'自动排版截面校准失败：'+str([(r[0],r[1]) for r in candidates])
    def inverse(p):
        x,y=p[0]-dx,p[1]-dy
        return (c*x+s*y,-s*x+c*y)
    aligned={z:[(inverse(a),inverse(b),kind,width) for a,b,kind,width in segments] for z,segments in layers.items()}
    return aligned,{'rotation_deg':angle,'translation_mm':[dx,dy],'section_alignment_score':score,
                    'bbox_center_alignment':centered,'bbox_dimension_error_mm':error}


def audit_witnesses(layers,witnesses):
    """见证点必须由实际本体挤出覆盖，不能拿支撑或远处路径冒充。"""
    indexes={z:grid([v for v in segments if 'support' not in v[2].lower()])
             for z,segments in layers.items()}
    checks={}
    for name,points in witnesses.items():
        assert len(points)>=3,'功能区采样不足：'+name
        count=sum(covered(p['point_mm'],indexes.get(p['layer_z_mm'],([],{})),.15) for p in points)
        coverage=count/len(points)
        checks[name]={'sample_count':len(points),'coverage':coverage}
        assert coverage>=.95,'功能实体未完整切出：'+name+' '+str(checks[name])
    return checks
