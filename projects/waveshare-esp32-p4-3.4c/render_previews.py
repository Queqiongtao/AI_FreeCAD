"""渲染八件式桌面控制器的外观、剖面、维护与打印摆放。"""
import argparse
import json
from pathlib import Path
import vtk
from PIL import Image, ImageDraw, ImageFont
from enclosure import COLORS as PART_COLORS, PART_LABELS, SCHEMA, Design

ROOT = Path(__file__).resolve().parent
CACHE = ROOT/'output'/'archive'/'preview_meshes'
COLORS = dict(PART_COLORS, **{
          'Display_Visual': (.04, .05, .06), 'Speaker_Envelope': (.25, .50, .38),
          'Mic_Gasket_Left': (.6, .25, .12), 'Mic_Gasket_Right': (.6, .25, .12),
          'Battery_Envelope':(.28,.48,.67), 'Battery_Keepout':(.3,.6,.8),
          'Power_Envelope':(.2,.5,.3), 'Switch_Envelope':(.15,.17,.19),
          'Feet_Reference':(.12,.14,.15)}
)


def actor_for(name, offset=(0, 0, 0), clip=False, path=None):
    reader = vtk.vtkSTLReader(); reader.SetFileName(str(path or CACHE/(name+'.stl'))); reader.Update()
    normals = vtk.vtkPolyDataNormals(); normals.SetInputConnection(reader.GetOutputPort())
    normals.SetFeatureAngle(45); normals.ConsistencyOn(); normals.AutoOrientNormalsOn(); normals.Update()
    mapper = vtk.vtkPolyDataMapper(); mapper.SetInputConnection(normals.GetOutputPort())
    if clip:
        plane = vtk.vtkPlane(); plane.SetOrigin(0, 0, 0); plane.SetNormal(1, 0, 0)
        mapper.AddClippingPlane(plane)
    actor = vtk.vtkActor(); actor.SetMapper(mapper); actor.SetPosition(*offset)
    prop = actor.GetProperty(); prop.SetColor(*COLORS[name]); prop.SetAmbient(.25)
    prop.SetDiffuse(.7); prop.SetSpecular(.15); prop.SetSpecularPower(35)
    return actor


def render(out, filename, names, camera, caption, offsets=None, clip=False,focus=None,scale=None):
    renderer = vtk.vtkRenderer(); renderer.SetBackground(.965, .96, .95)
    for name in names:
        renderer.AddActor(actor_for(name, (offsets or {}).get(name, (0, 0, 0)), clip))
    window = vtk.vtkRenderWindow(); window.SetOffScreenRendering(1)
    window.SetSize(1400, 1200); window.SetMultiSamples(8); window.AddRenderer(renderer)
    cam = renderer.GetActiveCamera(); cam.SetPosition(*camera); cam.SetFocalPoint(0, 5, 80)
    cam.SetViewUp(0, 0, 1); cam.ParallelProjectionOn(); renderer.ResetCamera(); cam.Zoom(1.02)
    if focus is not None:
        cam.SetPosition(*camera);cam.SetFocalPoint(*focus)
    if scale is not None:
        cam.SetParallelScale(scale)
    renderer.ResetCameraClippingRange()
    window.Render()
    capture = vtk.vtkWindowToImageFilter(); capture.SetInput(window); capture.ReadFrontBufferOff(); capture.Update()
    writer = vtk.vtkPNGWriter(); writer.SetFileName(str(out/filename)); writer.SetInputConnection(capture.GetOutputPort()); writer.Write()
    window.Finalize()
    canvas = Image.open(out/filename).convert('RGB'); draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 25)
    draw.rectangle((0, 1130, 1400, 1200), fill=(246, 245, 242))
    draw.text((28, 1148), caption, font=font, fill=(48, 53, 58)); canvas.save(out/filename)


def main():
    global CACHE
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--out', type=Path, default=ROOT/'output')
    args = parser.parse_args(); out = args.out.resolve()
    data = json.loads((out/'validation.json').read_text(encoding='utf-8'))
    if data['schema'] != SCHEMA:
        raise ValueError('仅支持当前八件式候选')
    CACHE = out/'archive'/'preview_meshes'
    names = list(PART_LABELS)+['Display_Visual','Feet_Reference']
    render(out, 'preview_iso.png', names, (260, -330, 230), '一体桌面控制器｜屏面高出0.8mm · 屏周120.4mm · 电池候选样机')
    render(out, 'preview_front.png', names, (0, -400, 170), '正面：原厂圆屏、左右独立麦克风预留口')
    render(out, 'preview_rear.png', names, (260, 330, 230), '背面：深灰维护盖 · 独立出音区 · USB与开关选型预留')
    render(out, 'preview_side.png', names, (400, 0, 100), '侧面：屏周向前包覆，屏面略高；下部机身和软脚位置保留')
    render(out,'preview_top.png',names,(80,160,420),'顶部：连续封闭壳面，取消原板USB外露避让槽')
    design=Design(data['parameters'])
    focus=tuple(design.point(58.8,0,1.5))
    render(out,'preview_screen_seam.png',names,(240,-240,180),
        '屏周近景：0.8mm浅台阶 · 单边0.3mm间隙 · 外缘0.3mm倒角',focus=focus,scale=17)
    internal = names+['Speaker_Envelope', 'Mic_Gasket_Left', 'Mic_Gasket_Right',
        'Battery_Envelope','Power_Envelope','Switch_Envelope']
    render(out, 'preview_section.png', internal, (-330, -210, 180), '剖视：蓝色电池、绿色供电与扬声器；均为待实物确认的硬件占位', clip=True)
    focus=tuple(design.point(0,58,8))
    render(out,'preview_screen_section.png',names,(-230,-150,220),
        '屏周剖面近景：原屏位置保留，包覆侧壁向后过渡；顶部无开槽',clip=True,focus=focus,scale=22)
    offsets = {'rear_cover': (0, 85, 0), 'board_carrier': (0, -35, 25),
               'Display_Visual': (0, -75, 45),
               'mic_left': (-25, -15, 0), 'mic_right': (25, -15, 0),
               'mic_left_lid': (-25, 0, 12), 'mic_right_lid': (25, 0, 12),
               'battery_tray':(0,95,0), 'Battery_Envelope':(0,95,0),'Power_Envelope':(0,95,0),
               'Speaker_Envelope':(0,85,0),'Switch_Envelope':(0,85,0)}
    render(out, 'preview_exploded.png', internal, (270, -360, 240), '八打印件爆炸示意｜电池、扬声器、软垫及原厂屏不打印', offsets)
    render(out,'preview_battery.png',['battery_tray','Battery_Envelope','Power_Envelope'],
        (190,-220,180),'独立电池托盘｜电芯低位软固定，电源平台与电池分层')
    render(out, 'preview_microphones.png', ['board_carrier', 'mic_left', 'mic_left_lid', 'mic_right', 'mic_right_lid', 'Mic_Gasket_Left', 'Mic_Gasket_Right'],
           (60, 250, 70), '导音盖片展开；左右声道独立，声口与密封面待实物校准',
           offsets={'mic_left_lid': (-5, 14, -8), 'mic_right_lid': (5, 14, -8)})
    render_layout(out, data)
    print('已生成八件式装配、内部及逐件打印预览')


def render_layout(out, data):
    width, height = 3000, 1300
    window = vtk.vtkRenderWindow(); window.SetOffScreenRendering(1); window.SetSize(width, height)
    for i, name in enumerate(PART_LABELS):
        renderer = vtk.vtkRenderer(); renderer.SetBackground(.965, .96, .95)
        col, row = i % 4, i // 4
        renderer.SetViewport(col/4, (1-row)/2, (col+1)/4, (2-row)/2)
        actor = actor_for(name, path=out/'trials'/(name+'.stl')); renderer.AddActor(actor)
        bounds = actor.GetBounds(); center = [(bounds[i]+bounds[i+1])/2 for i in (0, 2, 4)]
        cam = renderer.GetActiveCamera(); cam.SetPosition(center[0]+150, center[1]-220, center[2]+180)
        cam.SetFocalPoint(*center); cam.SetViewUp(0, 0, 1); cam.ParallelProjectionOn()
        window.AddRenderer(renderer); renderer.ResetCamera(); cam.Zoom(.83)
        plane = vtk.vtkPlaneSource(); plane.SetOrigin(bounds[0]-3, bounds[2]-3, -.05)
        plane.SetPoint1(bounds[1]+3, bounds[2]-3, -.05); plane.SetPoint2(bounds[0]-3, bounds[3]+3, -.05)
        mapper = vtk.vtkPolyDataMapper(); mapper.SetInputConnection(plane.GetOutputPort())
        bed = vtk.vtkActor(); bed.SetMapper(mapper); bed.GetProperty().SetColor(.73, .78, .80)
        bed.GetProperty().SetOpacity(.4); renderer.AddActor(bed)
    window.Render(); capture = vtk.vtkWindowToImageFilter(); capture.SetInput(window); capture.ReadFrontBufferOff(); capture.Update()
    target = out/'preview_print_layout.png'; writer = vtk.vtkPNGWriter(); writer.SetFileName(str(target))
    writer.SetInputConnection(capture.GetOutputPort()); writer.Write(); window.Finalize()
    canvas = Image.open(target).convert('RGB'); draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 25)
    for i, name in enumerate(PART_LABELS):
        x, y = (i % 4)*750, (i // 4)*650
        draw.text((x+16, y+560), str(i+1)+'. '+PART_LABELS[name], font=font, fill=(35, 40, 45))
        dims = data['parts'][name]['bbox_mm']
        draw.text((x+16, y+600), '%.1f × %.1f × %.1f mm' % tuple(dims), font=font, fill=(65, 70, 75))
    canvas.save(target)


if __name__ == '__main__':
    main()
