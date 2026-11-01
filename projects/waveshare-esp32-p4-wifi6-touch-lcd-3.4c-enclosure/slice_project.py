"""从正式 STL 和声孔报告生成带局部禁支撑区域的后壳切片几何。"""
import zipfile
import xml.etree.ElementTree as ET

from print_audit import read_mesh


def write_rear_project(stl, intake, target, grille=None):
    namespace='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
    ET.register_namespace('',namespace)

    def element(parent,name,attrs=None):
        return ET.SubElement(parent,'{'+namespace+'}'+name,attrs or {})

    model=ET.Element('{'+namespace+'}model',{'unit':'millimeter',
        '{http://www.w3.org/XML/1998/namespace}lang':'en-US'})
    resources=element(model,'resources')

    def mesh_object(number,triangles):
        obj=element(resources,'object',{'id':str(number),'type':'model'})
        mesh=element(obj,'mesh');vertices=element(mesh,'vertices');faces=element(mesh,'triangles')
        # 3MF 必须共享顶点，不能照搬 STL 每面三个独立顶点的拓扑。
        lookup={}
        for triangle in triangles:
            indices=[]
            for point in triangle:
                if point not in lookup:
                    lookup[point]=len(lookup)
                    element(vertices,'vertex',dict(zip(('x','y','z'),map(str,point))))
                indices.append(lookup[point])
            element(faces,'triangle',dict(zip(('v1','v2','v3'),map(str,indices))))

    body_triangles=read_mesh(stl.read_bytes())
    mesh_object(1,body_triangles)
    blocker_top=max(point[2] for triangle in body_triangles for point in triangle)+.6
    blocker_ids=[];blocker_names={};enforcer_ids=[]
    holes=[(hole,intake['diameter_mm'],'microphone') for hole in intake['holes']]
    holes += [(hole,grille['diameter_mm'],'speaker') for hole in (grille or {}).get('holes',[])]
    for index,(hole,diameter,kind) in enumerate(holes):
        blockers=[]
        x,z=hole['center_x_z_mm']
        if kind=='microphone':
            front=hole['front_y_mm']-1.6;back=hole['cavity_y_mm']+1.6
            radius=diameter/2+2.4;bottom,top=0,blocker_top
        else:
            b=hole['bounds_world_mm']
            front,back=b[2]-1.6,b[3]+1.6
            radius=diameter/2+1.6;bottom,top=max(0,b[4]-.4),blocker_top
        # Bambu 的禁支撑块抑制接触区，短块不能阻止上方支撑柱穿孔。
        # 沿孔道的窄 XY 投影延伸到整件高度，另由实际墙线承托审计验收。
        points=[(x-radius,front,bottom),(x+radius,front,bottom),
                (x+radius,back,bottom),(x-radius,back,bottom),
                (x-radius,front,top),(x+radius,front,top),
                (x+radius,back,top),(x-radius,back,top)]
        for indices in ((0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),
                        (1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)):
            blockers.append(tuple(points[i] for i in indices))
        mesh_object(index+2,blockers)
        blocker_ids.append(index+2)
        blocker_names[index+2]=('拾音孔' if kind=='microphone' else '出音孔')+'禁支撑区域 '+str(index+1)+'（不打印）'
    for index,bounds in enumerate((grille or {}).get('support_enforcers',[])):
        x0,x1,y0,y1,z0,z1=bounds
        points=[(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),
                (x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
        faces=((0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),
               (1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7))
        number=len(blocker_ids)+2+index
        mesh_object(number,[tuple(points[i] for i in face) for face in faces])
        enforcer_ids.append(number)
        blocker_names[number]='喇叭座强制支撑区域 '+str(index+1)+'（不打印）'
    assembly_id=str(len(blocker_ids)+len(enforcer_ids)+2)
    obj=element(resources,'object',{'id':assembly_id,'type':'model'})
    components=element(obj,'components')
    for number in [1]+blocker_ids+enforcer_ids:element(components,'component',{'objectid':str(number)})
    element(element(model,'build'),'item',{'objectid':assembly_id})
    config=ET.Element('config');obj=ET.SubElement(config,'object',{'id':assembly_id})
    ET.SubElement(obj,'metadata',{'key':'name','value':'rear_cover'})
    for number,subtype in ([(1,'normal_part')]+[(i,'support_blocker') for i in blocker_ids]
                           +[(i,'support_enforcer') for i in enforcer_ids]):
        part=ET.SubElement(obj,'part',{'id':str(number),'subtype':subtype})
        ET.SubElement(part,'metadata',{'key':'name',
            'value':'rear_cover' if number==1 else blocker_names[number]})
        ET.SubElement(part,'metadata',{'key':'matrix','value':'1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1'})
    types='<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>'
    relationships='<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as archive:
        def write(name,data):
            # 固定归档时间，保证 PLA/PETG 两份报告绑定同一个切片几何哈希。
            info=zipfile.ZipInfo(name,(1980,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(info,data)
        write('[Content_Types].xml',types)
        write('_rels/.rels',relationships)
        write('3D/3dmodel.model',ET.tostring(model,encoding='utf-8',xml_declaration=True))
        write('Metadata/model_settings.config',ET.tostring(config,encoding='utf-8',xml_declaration=True))
