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


def read_extrusions(text,dx,dy,include_brim=False):
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
        if de>0 and (nx!=x or ny!=y) and feature not in ('Custom','Skirt','') and (feature!='Brim' or include_brim):
            kind='Support brim' if feature=='Brim' else feature
            layers.setdefault(z,[]).append(((x-dx,y-dy),(nx-dx,ny-dy),kind,width))
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


def audit_hooks(layers,triangles,features,frame,is_carrier):
    """以最终 STL 的完整承力截面核对轮廓和实际挤出，排除支撑和稀疏填充。"""
    origin,up,normal=frame['origin'],frame['up'],frame['normal']
    def local(p):
        if is_carrier:return p[0],p[1]-frame['carrier_y_origin'],frame['carrier_back_n']-p[2]
        delta=[p[i]-origin[i] for i in range(3)]
        return p[0],sum(delta[i]*up[i] for i in range(3)),-sum(delta[i]*normal[i] for i in range(3))
    def shoulder(p,f):
        x,s,n=local(p);a=math.radians(f['angle_deg'])
        return x*math.cos(a)+s*math.sin(a),-x*math.sin(a)+s*math.cos(a),n
    def inside(p,b):return all(b[2*i]-.001<=p[i]<=b[2*i+1]+.001 for i in range(3))
    def probe(f,z):
        a=math.radians(f['angle_deg']);t=f['probe_t'];r0,r1=f['probe_r']
        points=[]
        for r in (r0,r1):
            x=r*math.cos(a)-t*math.sin(a);s=r*math.sin(a)+t*math.cos(a)
            if is_carrier:
                n=frame['carrier_back_n']-(z-.1)
                point=(x,s+frame['carrier_y_origin'])
            else:
                n=(origin[2]+up[2]*s-(z-.1))/normal[2]
                point=(x,origin[1]+up[1]*s-normal[1]*n)
            if not f['bounds'][4]+.15<n<f['bounds'][5]-.15:return None
            points.append(point)
        return points
    reports={f['name']:{'layer_count':0,'minimum_coverage':1.0,'minimum_material_crossings':None,
                       'minimum_load_path_coverage':1.0,
                       'minimum_load_path_width_mm':None,
                       'crossing_probe_count':0,'short_section_count':0} for f in features}
    for z,segments in sorted(layers.items()):
        # 台阶交界层可能用实心填充替代内墙；这些真实承力挤出同样计入，排除支撑和稀疏填充。
        walls=[v for v in segments if any(k in v[2].lower() for k in ('wall','solid infill','surface'))]
        if not walls:continue
        paths=grid([v for v in segments if 'support' not in v[2].lower()])
        contour=section(triangles,z-.1)
        for f in features:
            # 只评价整条承力探针均进入特征轴向厚度的层；斜面尖端不是完整承力截面。
            line=probe(f,z)
            if not line:continue
            # 功能让位会裁去名义矩形的一角；先按真实 STL 截线裁剪探针，不能把空气当漏料。
            a,b=line;ux,uy=b[0]-a[0],b[1]-a[1];cuts=[0.,1.]
            for c,d in contour:
                vx,vy=d[0]-c[0],d[1]-c[1];det=ux*vy-uy*vx
                if abs(det)<1e-9:continue
                wx,wy=c[0]-a[0],c[1]-a[1]
                tt=(wx*vy-wy*vx)/det;u=(wx*uy-wy*ux)/det
                if 0<tt<1 and 0<=u<=1:cuts.append(tt)
            cuts=sorted(set(round(t,8) for t in cuts))
            spans=[]
            for lo,hi in zip(cuts,cuts[1:]):
                x,y=a[0]+ux*(lo+hi)/2,a[1]+uy*(lo+hi)/2
                crossings=sum((c[1]>y)!=(d[1]>y) and x<(d[0]-c[0])*(y-c[1])/(d[1]-c[1])+c[0]
                              for c,d in contour)
                if crossings%2:spans.append((hi-lo,lo,hi))
            if not spans:continue
            span,lo,hi=max(spans)
            width=span*math.hypot(ux,uy)
            if width<1.6:
                reports[f['name']]['short_section_count']+=1
                continue
            line=[(a[0]+ux*t,a[1]+uy*t) for t in (lo,hi)]
            r=reports[f['name']]
            r['minimum_load_path_width_mm']=min(width,r['minimum_load_path_width_mm'] or width)
            total=found=0.0
            for a,b in contour:
                count=max(1,math.ceil(math.dist(a,b)/.3));step=math.dist(a,b)/count
                for i in range(count):
                    p=(a[0]+(b[0]-a[0])*(i+.5)/count,a[1]+(b[1]-a[1])*(i+.5)/count,z-.1)
                    if not inside(shoulder(p,f),f['bounds']):continue
                    total+=step
                    if covered(p,paths,.12):found+=step
            r=reports[f['name']]
            if total<.8:
                if total:r['short_section_count']+=1
                continue
            coverage=found/total
            r['minimum_coverage']=min(r['minimum_coverage'],coverage);r['layer_count']+=1
            assert coverage>=.95,'旋扣截面挤出缺失：'+str((f['name'],z,coverage))
            a,b=line;ux,uy=b[0]-a[0],b[1]-a[1];hits=set()
            for c,d,_,_ in walls:
                vx,vy=d[0]-c[0],d[1]-c[1];det=ux*vy-uy*vx
                if abs(det)<1e-8:continue
                wx,wy=c[0]-a[0],c[1]-a[1]
                t=(wx*vy-wy*vx)/det;u=(wx*uy-wy*ux)/det
                if 0<=t<=1 and 0<=u<=1:hits.add(round(t*math.hypot(ux,uy),2))
            count=len(hits)
            r['minimum_material_crossings']=min(count,r['minimum_material_crossings'] if r['minimum_material_crossings'] is not None else count)
            r['crossing_probe_count']+=1
            # 实心填充可能平行探针，交叉道数不能代表材料量；直接检查整条承力路径的实际覆盖。
            solid_index=grid(walls)
            sample_count=max(20,math.ceil(math.dist(a,b)/.05))
            filled=sum(covered((a[0]+ux*(i+.5)/sample_count,a[1]+uy*(i+.5)/sample_count),solid_index,.02)
                       for i in range(sample_count))/sample_count
            r['minimum_load_path_coverage']=min(r['minimum_load_path_coverage'],filled)
            assert count>=4 or filled>=.95,'承力截面挤出不足：'+str((f['name'],z,count,filled))
    for name,r in reports.items():
        assert r['layer_count']>=2 and r['crossing_probe_count']>=2,'旋扣缺少有效截面：'+name
    # 记录槽内实际支撑，明确需要清理；这些路径不能算作承力本体。
    support={}
    if not is_carrier:
        for f in features:
            if f['kind']!='front':continue
            moves=0;heights=set()
            for z,segments in layers.items():
                for a,b,kind,width in segments:
                    if 'support' not in kind.lower():continue
                    p=((a[0]+b[0])/2,(a[1]+b[1])/2,z-.1)
                    r,t,n=shoulder(p,f)
                    if frame['hook_r0']<r<frame['hook_r1'] and -.5<t<1.2 and frame['hook_front_n']-.3<n<frame['hook_back_n']+.3:
                        moves+=1;heights.add(z)
            support[f['name']]={'support_segment_midpoints':moves,'support_layers':len(heights),'removal_physically_verified':False}
    return {'features':reports,'slot_support':support}


def audit_support_runs(layers):
    """真实墙线须与前一本体层或下方支撑搭接，记录连续悬空长度。"""
    heights=sorted(layers);worst=[]
    for z in heights:
        if z<=.201:continue
        below=[]
        for h in heights[bisect.bisect_left(heights,z-.50):bisect.bisect_right(heights,z-.18)]:
            below.extend(v for v in layers[h] if 'support' in v[2].lower() or abs(h-(z-.2))<.015)
        index=grid(below);run=longest=0.0;last=None
        for a,b,kind,width in layers[z]:
            if 'wall' not in kind.lower():run=0;last=None;continue
            if last is None or math.dist(last,a)>.05:run=0
            count=max(1,math.ceil(math.dist(a,b)/.3));step=math.dist(a,b)/count
            for i in range(count):
                p=(a[0]+(b[0]-a[0])*(i+.5)/count,a[1]+(b[1]-a[1])*(i+.5)/count)
                if covered(p,index,width/2+.02):run=0
                else:run+=step;longest=max(longest,run)
            last=b
        worst.append({'z_mm':z,'unsupported_wall_run_mm':longest})
    return sorted(worst,key=lambda r:-r['unsupported_wall_run_mm'])
