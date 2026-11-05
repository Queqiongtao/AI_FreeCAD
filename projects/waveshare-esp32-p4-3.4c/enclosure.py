"""P4柔和一体桌面控制器：八件式电池候选样机的唯一参数化几何源。"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import FreeCAD as App
import MeshPart
import Part

ROOT = Path(__file__).resolve().parent
DOC_NAME = 'P4_Desktop_Controller'
MODEL = ROOT/'reference'/'ESP32-P4-WIFI6-TOUCH-LCD-3_4C.stp'
SCHEMA = 'p4-desktop-battery-eight-part-1'
DEFAULTS = {
    'tilt_deg': 60., 'head_center': [0, -10, 105.], 'head_radius': 57.,
    'front_n': 9.9, 'rear_y': 44., 'front_y': -48., 'wall': 2.4,
    'floor_t': 2.6, 'fit_clearance': .3, 'carrier_front_n': 18.2,
    'carrier_t': 4., 'cover_t': 3.2, 'boss_radius': 5.,
    'rear_flange_extra': 3., 'seal_groove_depth': .4, 'seal_stock_t': .5,
    'mic_x': 30., 'mic_s': -43., 'mic_interface_n': 12.3, 'mic_outlet_s': -61.,
    'mic_bore_r': 1.5, 'mic_body_w': 14., 'mic_body_depth': 9.,
    'mic_lid_t': 1.6, 'mic_lid_gasket_t': .2, 'mic_pilot_dia': 1.6,
    'gasket_thickness': .8, 'speaker_width': 50., 'speaker_depth': 18.,
    'speaker_height': 25., 'speaker_face_y': 42.2, 'speaker_bottom': 25.,
    'speaker_impedance_ohm': 8, 'speaker_rating_w': 2.,
    'battery_width': 60., 'battery_depth': 50., 'battery_height': 7.3,
    'battery_capacity_mah': 2500., 'battery_bottom': 9.4,
    'power_width': 38., 'power_depth': 33., 'power_height': 14.,
    'power_bottom': 25.4, 'power_center_y': -3.5,
    'tray_bottom': 6., 'tray_t': 2.4, 'waist_reduction': 9.,
    'screen_radius': 57.5, 'screen_radial_gap': .3, 'screen_proud': .8,
    'screen_wrap_end_n': 16.3, 'screen_transition_length': 8., 'screen_edge_break': .3,
}
PART_LABELS = {'main_body':'一体主体壳', 'rear_cover':'六点加强背盖', 'board_carrier':'四点独立承板',
    'mic_left':'左敞口导音槽', 'mic_left_lid':'左导音盖片',
    'mic_right':'右敞口导音槽', 'mic_right_lid':'右导音盖片',
    'battery_tray':'电池及电源可拆托盘'}
COLORS = {name:(.85,.84,.81) for name in PART_LABELS}
COLORS['board_carrier']=(.26,.28,.30)
COLORS['rear_cover']=(.22,.25,.28)
COLORS['battery_tray']=(.26,.28,.30)
COLORS.update({n:(.84,.48,.16) for n in PART_LABELS if n.startswith('mic_')})
PRINT_ORIENTATIONS = {'main_body':'后开口共面加强边贴床，向机身正面生长',
    'rear_cover':'外背面贴床，定位边、加强筋朝上', 'board_carrier':'共面背面贴床，安装柱朝上',
    'mic_left':'入口侧平面贴床，敞口槽朝上', 'mic_right':'同左导音槽',
    'mic_left_lid':'平面贴床', 'mic_right_lid':'平面贴床',
    'battery_tray':'底面贴床，电源平台使用可移除支撑；从两侧清理'}
V = App.Vector

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def box(x0,x1,y0,y1,z0,z1):
    return Part.makeBox(x1-x0,y1-y0,z1-z0,V(x0,y0,z0))

def join(shapes):
    shapes=list(shapes); result=shapes[0]
    for shape in shapes[1:]: result=result.fuse(shape)
    return result.removeSplitter()

def lb(x0,x1,s0,s1,n0,n1):
    return box(x0,x1,s0,s1,-n1,-n0)

def lc(radius,n0,n1,x=0,s=0):
    return Part.makeCylinder(radius,n1-n0,V(x,s,-n0),V(0,0,-1))

def cy(radius,y0,y1,x,z):
    return Part.makeCylinder(radius,y1-y0,V(x,y0,z),V(0,1,0))

def polygon_prism(points,vector):
    return Part.Face(Part.makePolygon(points+[points[0]])).extrude(vector)

class Design:
    def __init__(self,params=None):
        self.p=dict(DEFAULTS)
        if params:
            if set(params)-set(self.p): raise ValueError('未知参数：'+str(set(params)-set(self.p)))
            self.p.update(params)
        p=self.p
        for key,value in p.items():
            if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in (value if isinstance(value,list) else [value])):
                raise ValueError('参数必须为有限数值：'+key)
        if not 55<=p['tilt_deg']<=65: raise ValueError('屏幕试验角度限定55～65°')
        if not 55<=p['head_radius']<=57: raise ValueError('屏幕后壳直径不得大于114mm')
        if p['carrier_t']<4 or p['cover_t']<3.2 or p['wall']<2.4 or p['boss_radius']<4.5:
            raise ValueError('承板、背盖、壳壁或螺柱不得低于加强规格')
        if not .15<=p['fit_clearance']<=.4: raise ValueError('配合间隙需先试片校准')
        if not .2<=p['screen_radial_gap']<=.4 or not .5<=p['screen_proud']<=1.:
            raise ValueError('屏周间隙限定0.2～0.4mm，屏面高差限定0.5～1mm')
        if p['screen_wrap_end_n']<16.3 or p['screen_transition_length']<8:
            raise ValueError('屏周过渡必须避开原厂模块后方15.5mm包络')
        if not 0<=p['screen_edge_break']<=.3: raise ValueError('屏周倒角不得超过0.3mm')
        if not p['mic_outlet_s']<p['mic_s']-12: raise ValueError('麦克风入口和出口间距不足')
        if p['mic_bore_r']*2>p['mic_body_depth']-2: raise ValueError('声槽底部至少保留2mm实体')
        if p['speaker_impedance_ohm']!=8 or p['speaker_rating_w']<2: raise ValueError('扬声器采用8Ω、至少2W')
        self.placement=App.Placement(V(*p['head_center']),App.Rotation(V(1,0,0),p['tilt_deg']))
        self.carrier_bolts=[(x,s) for x in (-43,43) for s in (-24,24)]
        self.cover_bolts=[(x,z) for x,z in [(-35,118),(35,118),(-44,72),(44,72),(-41,18),(41,18)]]
        self.tray_bolts=[(x,y) for x in (-(p['battery_width']/2+6),p['battery_width']/2+6)
            for y in (-(p['battery_depth']/2-2),p['battery_depth']/2-2)]
        self.module_screws=[(39.25,-10),(39.25,17),(-39.25,17),(-39.25,-17)]
        self.parts={}; self.features={}; self.mic_air={}; self.mic_pockets={}; self.gaskets={}
        self._profiles={}

    def point(self,x,s,n): return self.placement.multVec(V(x,s,-n))

    def head(self,shape):
        result=shape.copy(); result.Placement=self.placement.multiply(result.Placement); return result

    def profile(self,inset=0, floor=None):
        """圆屏与大半径腰线相切，采用解析圆弧和前缘圆角保证拓扑稳定。"""
        p=self.p
        wires=[]
        key=(inset,floor)
        if key in self._profiles:
            return self._profiles[key].copy()
        for n,shrink in ((p['front_n']+inset,0),):
            r=p['head_radius']-inset-shrink
            foot=r-p['waist_reduction']
            a=V(r,0,-n); b=V(0,r,-n); c=V(-r,0,-n)
            radius=(10000+p['waist_reduction']**2)/(2*p['waist_reduction'])
            mid=r-radius+math.sqrt(radius**2-2500)
            bottom=foot-80*100/(radius-p['waist_reduction'])
            left=Part.Arc(c,V(-mid,-50,-n),V(-foot,-100,-n)).toShape()
            right=Part.Arc(V(foot,-100,-n),V(mid,-50,-n),a).toShape()
            wires.append(Part.Wire([Part.Arc(a,b,c).toShape(),left,
                Part.makeLine(V(-foot,-100,-n),V(-bottom,-180,-n)),
                Part.makeLine(V(-bottom,-180,-n),V(bottom,-180,-n)),
                Part.makeLine(V(bottom,-180,-n),V(foot,-100,-n)),right]))
        local=Part.Face(wires[0]).extrude(V(0,0,-170))
        front_edges=[e for e in local.Edges if e.BoundBox.ZLength<1e-5
            and abs(e.CenterOfMass.z+p['front_n']+inset)<1e-5 and e.BoundBox.YMax>-.01]
        # 前缘大圆角与内侧对应圆角共心，保持普通壳壁厚度。
        local=local.makeFillet(max(.6,6-inset),front_edges)
        shape=self.head(local)
        result=shape.common(box(-70,70,p['front_y']-2,p['rear_y']+10,
            0 if floor is None else floor,180))
        self._profiles[key]=result
        return result.copy()

    def make_mics(self):
        p=self.p; n=p['mic_interface_n']; depth=p['mic_body_depth']; r=p['mic_bore_r']
        panel=p['front_n']+p['wall']; end=p['mic_outlet_s']; s=p['mic_s']; w=p['mic_body_w']
        self.mic_mounts=[]
        for side,sign in (('left',-1),('right',1)):
            x=sign*p['mic_x']
            stock=lb(x-w/2,x+w/2,end-4,s+4,n,n+depth)
            groove=lb(x-r,x+r,end-r,s+r,n+depth-2*r,n+depth+.01)
            inlet=lc(r,n-1,n+depth,x,s); outlet=lc(r,p['front_n']-1,n+depth,x,end)
            trough=stock.cut(groove).cut(inlet).cut(outlet)
            ln=n+depth+p['mic_lid_gasket_t']
            lid=lb(x-w/2,x+w/2,end-4,s+4,ln,ln+p['mic_lid_t'])
            for dx in (-4.8,4.8):
                trough=trough.cut(lc(p['mic_pilot_dia']/2,n+1.4,n+depth+.1,x+dx,s-4))
                lid=lid.cut(lc(1.1,ln-.1,ln+p['mic_lid_t']+.1,x+dx,s-4))
                trough=trough.cut(lc(1.1,n-.1,n+depth+.1,x+dx,end))
                lid=lid.cut(lc(1.1,ln-.1,ln+p['mic_lid_t']+.1,x+dx,end))
                self.mic_mounts.append((x+dx,end))
            self.parts['mic_'+side]=self.head(trough.removeSplitter())
            self.parts['mic_'+side+'_lid']=self.head(lid.removeSplitter())
            self.mic_air[side]=self.head(join([groove.common(stock),inlet,outlet]))
            # 只切容纳槽体的装配口袋，不把整个包围盒挖成开放共腔。
            self.mic_pockets[side]=self.head(lb(x-w/2-.3,x+w/2+.3,end-4.3,s+4.3,n,ln+p['mic_lid_t']+.3))
            self.gaskets[side]=self.head(lb(x-3.8,x+3.8,s-3.8,s+3.8,n-p['gasket_thickness'],n).cut(lc(r,n-2,n+1,x,s)))
            self.features['mic_'+side]={'interface_x_s_n_mm':[x,s,n],'channel_section_mm':[2*r,2*r],
                'nominal_path_length_mm':s-end+depth-r+(n+depth-r-p['front_n']),
                'actual_port_verified':False,'outlet_x_s_n_mm':[x,end,p['front_n']],
                'closure':'两颗M2×5盖片自攻螺丝，另两颗M2×12夹紧槽体到主体前壁；软垫及浅导孔待试印校准'}

    def make_body(self):
        p=self.p; t=p['wall']; rear=p['rear_y']; cf=p['carrier_front_n']; cb=cf+p['carrier_t']
        self.outer=self.profile()
        front_limit=self.head(lb(-80,80,-180,80,p['front_n']+t,170))
        cavity=self.profile(t,p['floor_t']).common(front_limit)
        cavity=cavity.common(box(-70,70,p['front_y']+t,rear+10,0,180))
        body=self.outer.cut(cavity).common(box(-70,70,p['front_y'],rear,0,180))
        # 内部斜筋从底板连续长出，支承圆屏下方弧形前壁；扬声器前方留空。
        for x in (-42,42):
            rib=polygon_prism([V(x-1.2,16,2.5),V(x-1.2,-48,2.5),V(x-1.2,-48,86.5)],V(2.4,0,0))
            body=body.fuse(rib.common(self.outer).common(box(-70,70,p['front_y'],rear,0,180)))
        # 电池托盘四座连接底板，紧固件位于电芯外侧；不依赖后盖夹紧电池。
        for x,y in self.tray_bolts:
            seat=Part.makeCylinder(4.5,p['tray_bottom'],V(x,y,0))
            a=min(x,math.copysign(60,x))-4.5
            b=max(x,math.copysign(60,x))+4.5
            # 后口朝下打印时先由底板长出45°斜坡，避免螺母座首层悬空。
            root=polygon_prism([V(a,y-4.5,0),V(a,y+8,0),
                V(a,y+8,p['floor_t']-.1),V(a,y+4.5,p['tray_bottom']),
                V(a,y-4.5,p['tray_bottom'])],V(b-a,0,0))
            body=body.fuse(join([seat,root]).common(self.outer))
            body=body.cut(Part.makeCylinder(1.9,3.3,V(x,y,p['tray_bottom']-3.3)))
            body=body.cut(Part.makeCylinder(1.7,4.8,V(x,y,p['tray_bottom']-4.8)))
        # 原主体先按屏幕后缘挖空；前向包覆由下方独立的局部环壁生成。
        body=body.cut(self.head(lc(p['head_radius']-t,0,45)))
        # 共面后缘加强带；密封槽低于硬止挡0.4mm，打印时整个后缘直接落床。
        flange=self.outer.cut(self.profile(t+p['rear_flange_extra'],p['floor_t']+p['rear_flange_extra']))
        body=body.fuse(flange.common(box(-70,70,rear-3,rear,0,180)))
        # 两条渐宽斜梁从侧壁向前口下缘生长，支承圆形开口的打印弧底。
        # 全部高于39.4mm供电包络，最高52.4mm；第二对斜梁承托屏周锥形段弧底。
        for rear_y,front_y,front_z,front_width in ((10,-28,50,22),(15,-18,44,26)):
            for sign in (-1,1):
                sections=[]
                for y,x,z,width in ((rear_y,sign*55,41,4),(front_y,0,front_z,front_width)):
                    points=[V(x-width/2,y,z),V(x+width/2,y,z),
                        V(x+width/2,y,z+2.4),V(x-width/2,y,z+2.4)]
                    sections.append(Part.Wire(Part.makePolygon(points+[points[0]]).Edges))
                support=Part.makeLoft(sections,True,True).common(self.profile(.8))
                body=body.fuse(support)
        # 四处承板支座与侧壁连接；承板前方装螺丝，背盖不参与承板定位。
        anchors=[]
        for x,s in self.carrier_bolts:
            a,b=sorted((x-math.copysign(2,x),math.copysign(65,x)))
            root=join([lc(p['boss_radius'],cb,120,x,s),lb(a,b,s-3.2,s+3.2,cb,120)])
            # 根部终止于外表面内0.8mm，避免与裁剪曲面重合产生退化边。
            root=self.head(root).common(self.profile(.8)).common(box(-70,70,p['front_y'],rear,0,180))
            body=body.fuse(root)
            body=body.cut(self.head(lc(1.7,cb-.1,cb+5.0,x,s)))
            body=body.cut(self.head(lc(1.9,cb+.2,cb+3.3,x,s)))
            anchors.append({'x_s_mm':[x,s],'seat_n_mm':cb,'insert_n_mm':[cb+.2,cb+3.2],
                'screw':'M3×8圆头螺丝＋0.5mm垫片','tip_n_mm':cf-.5+8,'hole_bottom_n_mm':cb+5})
        # 槽体加深后直接贴内前壁，取消悬空凸嘴及支座。
        for x,s in self.mic_mounts:
            body=body.cut(self.head(lc(.8,p['mic_interface_n']-1.8,p['mic_interface_n']+.1,x,s)))
        # 六个背盖螺柱根部直接连至外壁，不使用长悬空柱。
        for x,z in self.cover_bolts:
            a,b=sorted((x-math.copysign(2,x),math.copysign(65,x)))
            root=join([cy(p['boss_radius'],rear-11,rear,x,z),box(a,b,rear-11,rear,z-3.2,z+3.2)])
            body=body.fuse(root.common(self.profile(.8)))
            body=body.cut(cy(1.7,rear-6,rear+.1,x,z)).cut(cy(1.9,rear-3.4,rear-.1,x,z))
        # 屏周局部向前包覆，保持承板、下部壳面和麦克风位置；顶部不再切外露USB槽。
        inner=p['screen_radius']+p['screen_radial_gap']; outer=inner+t
        front=p['screen_proud']; end=p['screen_wrap_end_n']; back=end+p['screen_transition_length']
        edge=p['screen_edge_break']; base=p['head_radius']
        points=[V(inner,0,-front),V(outer-edge,0,-front),V(outer,0,-front-edge),
            V(outer,0,-end),V(base,0,-back),V(base-t,0,-back),V(inner,0,-end)]
        wrap=Part.Face(Part.makePolygon(points+[points[0]])).revolve(V(),V(0,0,1),360)
        body=body.fuse(self.head(wrap))
        self.features['screen_wrap']={'screen_proud_mm':front,'inner_diameter_mm':2*inner,
            'outer_diameter_mm':2*outer,'radial_clearance_mm':p['screen_radial_gap'],
            'wall_mm':t,'edge_break_mm':edge,'wrap_end_n_mm':end,'transition_end_n_mm':back,
            'top_usb_slot':False,'geometry_note':'原屏和承板不移动；仅主壳一体侧壁向前包覆，不遮盖玻璃'}
        self.feet=[]
        for x in (-32,32):
            for y in (-34,33):
                body=body.cut(Part.makeCylinder(5,.8,V(x,y,0)))
                self.feet.append(Part.makeCylinder(4.9,1.6,V(x,y,-.8)))
        for side in ('left','right'):
            body=body.cut(self.mic_pockets[side])
            body=body.cut(self.mic_air[side])
        # 保留有效的解析分面，避免OCCT合并相切面时破坏曲面参数曲线。
        self.parts['main_body']=body
        self.features['structure']={'carrier_t_mm':p['carrier_t'],'cover_t_mm':p['cover_t'],
            'boss_diameter_mm':2*p['boss_radius'],'carrier_mounts':anchors,'cover_mounts_x_z_mm':self.cover_bolts,
            'carrier_independent_of_cover':True,'rear_hard_seat_y_mm':rear,
            'seal_stock_mm':p['seal_stock_t'],'seal_compressed_mm':p['seal_groove_depth'],
            'cover_screw':'M3×8沉头螺丝，3.2mm盖厚，3mm热熔螺母；计入0.2mm头部下沉后孔底余量1.0mm',
            'frame_added_to_display_front':False}

    def make_battery_tray(self):
        p=self.p; z=p['tray_bottom']; top=z+p['tray_t']
        bw=p['battery_width']; bd=p['battery_depth']; gx=bw/2+2
        tray=box(-bw/2-4,bw/2+4,-bd/2-4,bd/2+4,z,top)
        for x,y in self.tray_bolts:
            ear=box(min(x,math.copysign(bw/2,x))-4.3,max(x,math.copysign(bw/2,x))+4.3,
                y-4.3,y+4.3,z,top)
            tray=tray.fuse(ear).cut(Part.makeCylinder(1.7,p['tray_t']+2,V(x,y,z-1)))
        # 低挡边与两侧穿带孔只定位电池，采用软垫和松弛织带保持，不夹压电芯。
        for sign in (-1,1):
            tray=tray.fuse(box(sign*gx-1.2,sign*gx+1.2,-bd/2-1,bd/2+1,top,top+4))
            for y in (-(bd/2-8),bd/2-8):
                tray=tray.cut(box(sign*gx-.7,sign*gx+.7,y-5,y+5,z-.1,top+.1))
        # 电源模块在电池上方独立平台；支柱处于电芯包络以外。
        for x in (-gx,gx):
            tray=tray.fuse(box(x-1.2,x+1.2,-bd/2,-bd/2+5,top,p['power_bottom']))
        tray=tray.fuse(box(-gx-1.2,gx+1.2,-bd/2,-bd/2+5,p['power_bottom']-2.4,p['power_bottom']))
        py=p['power_center_y']; pw=p['power_width']; pd=p['power_depth']
        deck=box(-pw/2-2.4,pw/2+2.4,py-pd/2-2.4,py+pd/2+2.4,
            p['power_bottom']-2.4,p['power_bottom'])
        # 开窗与穿带槽适配未冻结的PCB固定孔，平台保留连续周边，不虚构螺孔。
        deck=deck.cut(box(-pw/2+3,pw/2-3,py-pd/2+3,py+pd/2-3,
            p['power_bottom']-3,p['power_bottom']+.1))
        for x in (-pw/2,pw/2):
            deck=deck.cut(box(x-.7,x+.7,py-4,py+4,p['power_bottom']-3,p['power_bottom']+.1))
        tray=tray.fuse(deck)
        self.parts['battery_tray']=tray.removeSplitter()
        self.battery=box(-p['battery_width']/2,p['battery_width']/2,-p['battery_depth']/2,
            p['battery_depth']/2,p['battery_bottom'],p['battery_bottom']+p['battery_height'])
        self.battery_keepout=box(-p['battery_width']/2-.8,p['battery_width']/2+.8,
            -p['battery_depth']/2-.8,p['battery_depth']/2+.8,
            p['battery_bottom'],p['battery_bottom']+p['battery_height']+1.5)
        self.power=box(-pw/2,pw/2,py-pd/2,py+pd/2,p['power_bottom'],p['power_bottom']+p['power_height'])
        self.features['battery']={'candidate':'Adafruit 328，3.7V 2500mAh，60×50×7.3mm',
            'capacity_mah':p['battery_capacity_mah'],'physical_model_confirmed':False,
            'swelling_clearance_mm':1.5,'mount':'1mm软垫＋两条松弛织带，四颗M3×6独立锁托盘',
            'runtime_target_minutes':60,'measured_power_w':None,'runtime_verified':False,
            'energy_budget':{'nominal_wh':3.7*p['battery_capacity_mah']/1000,
                'assumed_efficiency':.85,'reserved_fraction':.20,
                'one_hour_max_average_load_w':3.7*p['battery_capacity_mah']/1000*.85*.80}}
        self.features['power']={'candidate':'DFRobot DFR0446 / MP2636，PCB 35×30mm',
            'reserved_envelope_mm':[pw,pd,p['power_height']],
            'supply':'USB外接电源→充电/电源路径模块→P4 USB供电口；禁止双源直接并联',
            'charge_current_limit_a':1.0,'charge_current_setting_verified':False,
            'battery_discharge_rating_verified':False,'seamless_transfer_verified':False}

    def make_carrier(self):
        p=self.p; cf=p['carrier_front_n']; cb=cf+p['carrier_t']
        pieces=[lc(54.3,cf,cb).cut(lc(46,cf-1,cb+1)),lb(-53,53,-6,6,cf,cb)]
        for x,s in self.module_screws:
            a,b=sorted((x-math.copysign(5,x),math.copysign(54,x)))
            pieces.extend([lb(a,b,s-5,s+5,cf,cb),lc(5,15.1,cf+.1,x,s)])
        for x,s in self.carrier_bolts: pieces.append(lc(5,cf,cb,x,s))
        carrier=join(pieces).common(lc(54.3,14,cb+1))
        for x,s in self.module_screws:
            carrier=carrier.cut(lc(1.45,14.5,cb+1,x,s)).cut(lc(2.65,18.3,cb+1,x,s))
            carrier=carrier.cut(Part.makeCone(1.45,2.65,1.2,V(x,s,-17.1),V(0,0,-1)))
        for x,s in self.carrier_bolts: carrier=carrier.cut(lc(1.7,cf-.1,cb+.1,x,s))
        carrier=carrier.cut(lb(-60,60,-65,-39,14,cb+1))
        carrier=carrier.cut(lb(-23,-2,29,80,6,cb+1)).cut(lb(-5,5,-3,3,cf-.1,cb+.1))
        self.parts['board_carrier']=self.head(carrier.removeSplitter())

    def make_cover(self):
        p=self.p; rear=p['rear_y']; ct=p['cover_t']; gap=p['fit_clearance']; off=p['wall']+p['rear_flange_extra']+gap
        cover=self.outer.common(box(-70,70,rear,rear+ct,0,180))
        # 密封槽放在盖板内面，槽口朝打印上方；主体后缘整面落床。
        seal=self.profile(.9,.9).cut(self.profile(4.4,4.4)).common(box(-70,70,rear-.1,rear+p['seal_groove_depth'],0,180))
        for x,z in self.cover_bolts: seal=seal.cut(cy(6,rear-1,rear+1,x,z))
        cover=cover.cut(seal)
        # 四个局部定位挡块代替整圈薄定位边，避免切让支座后留下细碎悬片。
        for x in (-46,46):
            for z in (40,90): cover=cover.fuse(box(x-1.6,x+1.6,rear-2,rear+.1,z-3,z+3))
        # 背盖两条纵筋和一条横筋形成框架，避开扬声器完整包络。
        ribs=[box(x-1.6,x+1.6,rear-6,rear+.1,8,111) for x in (-40,40)]
        ribs.append(box(-43,43,rear-6,rear+.1,53,56.2))
        cover=cover.fuse(join(ribs).common(self.outer))
        for x,z in self.cover_bolts:
            # 定位边避让主体螺柱；盖板本身保留平整承压面。
            cover=cover.cut(cy(1.7,rear-.1,rear+ct+.1,x,z))
            cover=cover.cut(Part.makeCone(1.7,3.2,1.5,V(x,rear+ct-1.5,z),V(0,1,0)))
        self.speaker=box(-p['speaker_width']/2,p['speaker_width']/2,p['speaker_face_y']-p['speaker_depth'],
            p['speaker_face_y'],p['speaker_bottom'],p['speaker_bottom']+p['speaker_height'])
        # 轨道仅作可替换独立音腔模块的安装预留，真实固定耳尚待选型。
        for x in (-29,29):
            for z in (28,47):
                cover=cover.fuse(cy(3.5,rear-9,rear+.1,x,z))
                cover=cover.cut(cy(1.4,rear-9.1,rear-5,x,z))
        count=0
        for i in range(-5,6):
            for j in range(-2,3):
                x=i*4.4; z=37.5+j*5.4
                tool=polygon_prism([V(x-1.5,rear-.1,z),V(x,rear-.1,z-2),V(x+1.5,rear-.1,z),V(x,rear-.1,z+2)],V(0,ct+.2,0))
                cover=cover.cut(tool); count+=1
        for x in (-24,-16,-8,0,8,16,24):
            for z in (103,109): cover=cover.cut(cy(1.5,rear-.1,rear+ct+.1,x,z))
        self.power_tool=box(-11,11,rear-.1,rear+ct+.1,62,76)
        cover=cover.cut(self.power_tool)
        self.switch_tool=box(24,36,rear-.1,rear+ct+.1,62,69)
        cover=cover.cut(self.switch_tool)
        self.switch=box(23,37,rear-8,rear-.5,61,70)
        # 后缘定位边与加强筋给主体支座留出0.3mm横向装配余量，硬支承面仍在y=rear。
        plate=cover.common(box(-70,70,rear,rear+ct+.1,0,180))
        inside=cover.common(box(-70,70,rear-12,rear,0,180))
        for dx,dz in ((0,0),(-gap,0),(gap,0),(0,-gap),(0,gap)):
            tool=self.parts['main_body'].copy(); tool.translate(V(dx,0,dz))
            inside=inside.cut(tool)
        attached=[s for s in inside.Solids if s.distToShape(plate)[0]<1e-6]
        self.parts['rear_cover']=join([plate]+attached)
        self.features['speaker']={'envelope_mm':[p['speaker_width'],p['speaker_depth'],p['speaker_height']],
            'face_direction_world':[0,1,0],'impedance_ohm':8,'rating_w':p['speaker_rating_w'],
            'model':None,'mounting':'50×18×25mm独立音腔模块占位，背盖四个安装预留；实际固定耳、隔振垫待选型'}
        self.features['grille']={'count':count,'opening_mm':[3,4],'open_area_mm2':count*6,'minimum_web_mm':1.4}

    def load_module(self):
        source=Part.read(str(MODEL)); source.translate(V(0,0,-3.75)); kept=[]; removed=[]
        for i,solid in enumerate(source.Solids):
            c=solid.CenterOfMass; b=solid.BoundBox
            hit=any(math.hypot(c.x-x,c.y-s)<.1 for x,s in self.module_screws)
            if hit and abs(-b.ZMax-11.1)<.02 and abs(-b.ZMin-15.1)<.02 and solid.Volume<30: removed.append(i)
            else: kept.append(solid)
        if len(removed)!=4: raise RuntimeError('原厂四颗安装螺丝识别失败')
        self.module=self.head(Part.makeCompound(kept))
        self.features['module']={'source_solids':len(source.Solids),'removed_original_screws':removed,
            'retained_solids':len(kept),'source_sha256':digest(MODEL)}
        self.display_case=self.head(source.Solids[0])

    def build(self):
        self.make_mics(); self.make_body(); self.make_carrier(); self.make_cover(); self.make_battery_tray(); self.load_module()
        self.refs={'Module_Reference':self.module,'Speaker_Envelope':self.speaker,
            'Mic_Gasket_Left':self.gaskets['left'],'Mic_Gasket_Right':self.gaskets['right'],
            'Battery_Envelope':self.battery,'Battery_Keepout':self.battery_keepout,
            'Power_Envelope':self.power,'Switch_Envelope':self.switch,
            'Feet_Reference':Part.makeCompound(self.feet)}
        return self

    def print_shape(self,name,shape):
        result=shape.copy()
        if name in ('main_body','rear_cover'):
            result.rotate(V(),V(1,0,0),-90)
        elif name=='board_carrier' or name.startswith('mic_'):
            result.Placement=self.placement.inverse().multiply(result.Placement)
            if name.startswith('mic_'): result.rotate(V(),V(1,0,0),180)
        b=result.BoundBox; result.translate(V(-(b.XMin+b.XMax)/2,-(b.YMin+b.YMax)/2,-b.ZMin))
        return result


def save_mesh(shape, path, ground=False):
    mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=.08, AngularDeflection=.10, Relative=False)
    if ground:
        mesh.translate(0, 0, -mesh.BoundBox.ZMin)
    mesh.write(str(path))
    return {'closed': mesh.isSolid(), 'components': mesh.countComponents(), 'triangles': mesh.CountFacets,
            'sha256': digest(path), 'bbox_mm': [mesh.BoundBox.XLength, mesh.BoundBox.YLength, mesh.BoundBox.ZLength],
            'print_z_min_mm': mesh.BoundBox.ZMin}


def readiness():
    return {'status':'engineering_candidate_not_frozen','production_ready':False,
        'hardware_frozen':False,'physical_tests_executed':False,
        'pending':['电池放电能力及充放电模块限流、电源切换实测',
            '左右声口坐标、朝向及密封校准','实际扬声器、USB延长座、开关及线束确认',
            'PETG试印、配合及五次装拆','60分钟续航、播放唤醒/AEC、3N稳定、运行和充电温升']}


def configure_display(doc):
    # Visibility也是文档数据属性；无GUI生成的工程同样应隐藏参考硬件。
    for obj in doc.Objects:
        if hasattr(obj,'Shape'):
            obj.Visibility=obj.Name in PART_LABELS or obj.Name=='Display_Visual'
    if not App.GuiUp:
        return
    if doc.Design_Status.Schema != SCHEMA:
        raise ValueError('目标文档不是当前八件式候选')
    for obj in doc.Objects:
        if hasattr(obj, 'Shape'):
            obj.ViewObject.Visibility = obj.Name in PART_LABELS or obj.Name == 'Display_Visual'
            obj.ViewObject.ShapeColor = COLORS.get(obj.Name, (.045, .055, .065))
            obj.ViewObject.LineColor = (.18, .19, .20)
            obj.ViewObject.DisplayMode = 'Flat Lines'


def export_design(design, out):
    out.mkdir(parents=True, exist_ok=True); trials = out/'trials'; trials.mkdir(exist_ok=True)
    meshes = out/'archive'/'preview_meshes'; meshes.mkdir(parents=True, exist_ok=True)
    if App.GuiUp and DOC_NAME in App.listDocuments():
        raise RuntimeError('GUI文档已打开，须先检查保存状态，不能直接替换')
    doc = App.newDocument(DOC_NAME); doc.Label = 'P4柔和一体桌面控制器｜电池候选样机'
    meta = doc.addObject('App::FeaturePython', 'Design_Status')
    meta.addProperty('App::PropertyString', 'Schema').Schema = SCHEMA
    meta.addProperty('App::PropertyString', 'Readiness').Readiness = '电池供电及声学待冻结；未完成实物验证'
    meta.addProperty('App::PropertyString', 'ParametersJSON').ParametersJSON = json.dumps(design.p)
    meta.addProperty('App::PropertyBool', 'ProductionReady').ProductionReady = False
    for name, shape in dict(design.parts, **design.refs, Display_Visual=design.display_case).items():
        obj = doc.addObject('Part::Feature', name); obj.Shape = shape; obj.Label = PART_LABELS.get(name, name)
    doc.recompute(); configure_display(doc); doc.saveAs(str(out/'enclosure.FCStd'))
    Part.export([doc.getObject(name) for name in PART_LABELS], str(out/'enclosure.step'))
    report = {'schema': SCHEMA, 'parameters': design.p, 'readiness': readiness(), 'features': design.features,
        'parts': {}, 'samples': {}, 'source_sha256': digest(Path(__file__)), 'fit_verified': False,
        'slicing_verified': False, 'physical_fit_verified': False}
    for name, shape in design.parts.items():
        print(name, shape.isValid(), len(shape.Solids), round(shape.Volume, 2), flush=True)
        info = save_mesh(design.print_shape(name, shape), trials/(name+'.stl'), ground=True)
        save_mesh(shape, meshes/(name+'.stl'))
        info.update({'valid': shape.isValid(), 'solids': len(shape.Solids), 'volume_mm3': shape.Volume,
                     'orientation': PRINT_ORIENTATIONS[name]})
        report['parts'][name] = info
    for name, shape in design.refs.items():
        if name != 'Module_Reference':
            save_mesh(shape, meshes/(name+'.stl'))
    save_mesh(design.display_case, meshes/'Display_Visual.stl')
    sample_dir = trials/'samples'; sample_dir.mkdir(exist_ok=True)
    samples = {'speaker_grille': design.parts['rear_cover'].common(box(-26,26,43.9,47.3,4,46)),
               'carrier_joint': design.parts['main_body'].common(design.head(lb(37,55,17,31,22.2,33)))}
    for name, shape in samples.items():
        if shape.isNull() or shape.Volume < .1:
            raise RuntimeError('局部样件为空：'+name)
        oriented = design.print_shape('main_body' if name == 'carrier_joint' else 'rear_cover', shape)
        report['samples'][name] = save_mesh(oriented, sample_dir/(name+'.stl'), ground=True)
    for gap in (.15, .20, .25, .30, .35, .40):
        hole = box(0, 12, 0, 12, 0, 4).cut(Part.makeCylinder(2+gap, 5, V(6, 6, -.1)))
        pin = box(0, 12, 0, 12, 0, 2).fuse(Part.makeCylinder(2, 4, V(6, 6, 2)))
        for suffix, shape in (('hole', hole), ('pin', pin)):
            name = 'fit_%02d_%s' % (round(gap*100), suffix)
            report['samples'][name] = save_mesh(shape, sample_dir/(name+'.stl'), ground=True)
    report['artifacts'] = {name: digest(out/name) for name in ('enclosure.FCStd', 'enclosure.step')}
    (out/'validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    (out/'design_parameters.json').write_text(json.dumps(design.p, ensure_ascii=False, indent=2), encoding='utf-8')
    measurements = out/'hardware_measurements.json'
    if not measurements.exists():
        measurements.write_text(json.dumps({'schema': SCHEMA, 'mic_coordinates_and_directions': None,
            'speaker_model_and_mounts': None, 'power_cable_and_bend_radius': None,
            'PLA_fit_clearance': None, 'PETG_fit_clearance': None, 'mic_pilot_dia_tested': None,
            'mic_attenuation_db': None, 'added_channel_difference_db': None,
            'wake_quiet_out_of_30': None, 'wake_playing_out_of_30': None,
            'touch_3n_pass': None, 'thermal_2h_pass': None, 'five_assembly_cycles_pass': None},
            ensure_ascii=False, indent=2), encoding='utf-8')
    App.closeDocument(doc.Name)
    print('八件式候选已输出：'+str(out), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=Path(os.environ.get('P4_OUTPUT_DIR', ROOT/'output')))
    parser.add_argument('--params', type=Path)
    parser.add_argument('--release', action='store_true')
    args = parser.parse_args()
    if args.release:
        parser.error('供电、声学及实物测试未完成，当前仅交付工程候选')
    params = json.loads(args.params.read_text(encoding='utf-8')) if args.params else None
    export_design(Design(params).build(), args.out.resolve())


if __name__ == '__main__':
    main()
