"""独立读取 STL 和实际 G-code，检查功能截面及墙线的下层承托。"""
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
        # 新后盖的报告包围框比网格宽约 0.19 mm；其中心可用于平移初值。
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


def audit_features(triangles,layers,manifest,part):
    angle=math.radians(manifest['tilt_deg'])
    sn,cs=math.sin(angle),math.cos(angle)
    front=manifest['front_z_mm']
    back=manifest['frame_back_n_mm']
    yoffset=manifest['frame_print_y_offset_mm']
    features=[f for f in manifest['features'] if f['part']==part]
    reports={f['name']:{'layer_count':0,'minimum_coverage':1.0,'maximum_missing_edge_run_mm':0.0,
                        'minimum_crossing_count':None,'crossing_probe_count':0,'skipped_short_sections':0,
                        'boundary_transition_layers':0,'tapered_edge_length_mm':0.0,
                        'minimum_full_contour_coverage':1.0} for f in features}
    def local(p):
        x,y,z=p
        return (x,y-yoffset,back-z) if part=='main_shell' else (x,y*cs+(z-front)*sn,y*sn-(z-front)*cs)
    def inside(p,bounds):
        return all(bounds[2*k]-0.001<=p[k]<=bounds[2*k+1]+0.001 for k in range(3))
    z_intervals={}
    for f in features:
        b=f['bounds']
        if f['space']=='world':lo,hi=b[4:6]
        elif part=='main_shell':lo,hi=back-b[5],back-b[4]
        else:lo,hi=front+b[2]*sn-b[5]*cs,front+b[3]*sn-b[4]*cs
        z_intervals[f['name']]=(lo-0.002,hi+0.002)
    def measure(contour,height,f,wall_index):
        total=found=raw_total=raw_found=0
        length=maximum_run=tapered=0.0
        def within(q):
            crossings=0
            for a,b in contour:
                if (a[1]>q[1])!=(b[1]>q[1]):
                    if q[0]<a[0]+(q[1]-a[1])*(b[0]-a[0])/(b[1]-a[1]):crossings+=1
            return crossings%2==1
        for a,b in contour:
            a3,b3=(a[0],a[1],height),(b[0],b[1],height)
            aa,bb=(local(a3),local(b3)) if f['space']=='local' else (a3,b3)
            bounds=f['bounds']
            if any(max(aa[k],bb[k])<bounds[2*k]-0.001 or min(aa[k],bb[k])>bounds[2*k+1]+0.001 for k in range(3)):continue
            count=max(1,math.ceil(math.dist(a,b)/0.35))
            missing_run=0.0
            step=math.dist(a,b)/count
            for i in range(count):
                p=(a[0]+(b[0]-a[0])*(i+0.5)/count,a[1]+(b[1]-a[1])*(i+0.5)/count,height)
                if not inside(local(p) if f['space']=='local' else p,f['bounds']):continue
                annulus=f.get('contact_annulus')
                if annulus:
                    lp=local(p)
                    if not annulus[2]<=math.hypot(lp[0]-annulus[0],lp[1]-annulus[1])<=annulus[3]:continue
                hit=covered(p,wall_index,0.10)
                raw_total+=step
                if hit:raw_found+=step
                if not hit:
                    # 倾斜圆面、斜顶的起止层自然收尖；将截面厚度不足 1.2 mm
                    # 的收尖边单列，不能把它们与完整承力截面混为一谈。
                    size=math.dist(a,b)
                    nx,ny=-(b[1]-a[1])/size,(b[0]-a[0])/size
                    if not any(within((p[0]+sign*nx*1.2,p[1]+sign*ny*1.2)) for sign in (-1,1)):
                        tapered+=step;missing_run=0;continue
                # 按实际轮廓长度加权，不能让微短三角面边与 0.35 mm 长边等权。
                total+=step;length+=step
                if hit:found+=step;missing_run=0
                else:missing_run+=step;maximum_run=max(maximum_run,missing_run)
        return found/(total or 1) if total else 1.0,maximum_run,length,total,tapered,raw_found/(raw_total or 1) if raw_total else 1.0
    failures=[]
    for z,segments in sorted(layers.items()):
        walls=[v for v in segments if 'wall' in v[2].lower()]
        if not walls:continue
        # 仅在台阶恰好与切片中面重合时，允许 ±0.001 mm 的边界归属差异。
        # 这比一层厚度小 200 倍，不用它容忍实际缺失的薄结构。
        sections=[(offset,section(triangles,z-0.1+offset)) for offset in (0,-0.001,0.001)]
        # 实体填充和补缝同样形成实物；墙线道数仍在下方独立核验。
        wall_index=grid([v for v in segments if 'support' not in v[2].lower()])
        for f in features:
            lo,hi=z_intervals[f['name']]
            if not lo<=z-0.1<=hi:continue
            choices=[]
            for offset,contour in sections:
                coverage,maximum_run,length,total,tapered,raw_coverage=measure(contour,z-0.1+offset,f,wall_index)
                choices.append((coverage,-maximum_run,-abs(offset),length,total,offset,tapered,raw_coverage))
            coverage,negative_run,_,length,total,offset,tapered,raw_coverage=max(choices)
            maximum_run=-negative_run
            r=reports[f['name']]
            r['tapered_edge_length_mm']+=tapered
            r['minimum_full_contour_coverage']=min(r['minimum_full_contour_coverage'],raw_coverage)
            if not total and not any(c[4] for c in choices):continue
            if offset:r['boundary_transition_layers']+=1
            if length<0.8:
                r['skipped_short_sections']+=1
                continue  # 导角起止处的短轮廓单列，不作为承力截面。
            r['layer_count']+=1
            r['minimum_coverage']=min(r['minimum_coverage'],coverage)
            r['maximum_missing_edge_run_mm']=max(r['maximum_missing_edge_run_mm'],maximum_run)
            if coverage<0.95 or maximum_run>0.8:
                failures.append({'feature':f['name'],'z_mm':z,'coverage':coverage,'missing_run_mm':maximum_run})
            cross=f.get('cross')
            n=back-(z-0.1)
            line=None
            if cross and cross['kind']=='slot' and 23<=n<=25.5:
                a=math.radians(cross['angle'])
                line=((50.9*math.cos(a),50.9*math.sin(a)+yoffset),(52.95*math.cos(a),52.95*math.sin(a)+yoffset))
            if line:
                a,b=line;ux,uy=b[0]-a[0],b[1]-a[1];hits=set()
                for c,d,_,_ in walls:
                    vx,vy=d[0]-c[0],d[1]-c[1];det=ux*vy-uy*vx
                    if abs(det)<1e-8:continue
                    wx,wy=c[0]-a[0],c[1]-a[1]
                    t=(wx*vy-wy*vx)/det;u=(wx*uy-wy*ux)/det
                    if 0<=t<=1 and 0<=u<=1:hits.add(round(t*math.hypot(ux,uy),2))
                count=len(hits)
                r['crossing_probe_count']+=1
                r['minimum_crossing_count']=min(count,r['minimum_crossing_count'] if r['minimum_crossing_count'] is not None else count)
                if count<2:failures.append({'feature':f['name'],'z_mm':z,'wall_crossings':count})
    for name,r in reports.items():
        if r['layer_count']<2:failures.append({'feature':name,'error':'功能区域没有至少两个有效切片截面'})
    return reports,failures


def audit_support(layers):
    heights=sorted(layers)
    worst=[]
    for z in heights:
        if z<=0.201:continue
        previous=[]
        for h in heights[bisect.bisect_left(heights,z-0.50):bisect.bisect_right(heights,z-0.18)]:
            previous.extend(v for v in layers[h] if 'support' in v[2].lower() or abs(h-(z-0.2))<0.015)
        index=grid(previous)
        run=longest=0.0
        last=None
        for a,b,kind,width in layers[z]:
            if 'wall' not in kind.lower():run=0;last=None;continue
            if last is None or math.dist(last,a)>0.05:run=0
            count=max(1,math.ceil(math.dist(a,b)/0.30))
            step=math.dist(a,b)/count
            for i in range(count):
                p=(a[0]+(b[0]-a[0])*(i+0.5)/count,a[1]+(b[1]-a[1])*(i+0.5)/count)
                # 正常斜壁只需挤出足迹与下层搭接，无须中心落在下层内。
                if covered(p,index,width/2+0.02):run=0
                else:run+=step;longest=max(longest,run)
            last=b
        if longest>0:worst.append({'z_mm':z,'unsupported_wall_run_mm':longest})
    return sorted(worst,key=lambda r:-r['unsupported_wall_run_mm'])
