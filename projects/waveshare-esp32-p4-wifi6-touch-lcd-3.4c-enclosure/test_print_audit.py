"""验证切片核验器能识别漏打、悬空和正常斜壁搭接。"""
import math
import struct
import tempfile
import unittest
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from print_audit import audit_features, audit_support, read_extrusions, align_extrusions, audit_microphones
from slice_project import write_rear_project


class PrintAuditTests(unittest.TestCase):
    def test_slice_project_preserves_mesh_and_support_blocker(self):
        # 共享顶点的封闭四面体；防止 3MF 退化为互不相连的独立三角面。
        points=[(0,0,0),(2,0,0),(0,2,0),(0,0,2)]
        faces=[(0,2,1),(0,1,3),(1,2,3),(2,0,3)]
        data=b'\0'*80+struct.pack('<I',4)
        for face in faces:
            data+=struct.pack('<12fH',0,0,0,*(v for i in face for v in points[i]),0)
        with tempfile.TemporaryDirectory() as directory:
            stl=Path(directory)/'part.stl';stl.write_bytes(data)
            target=Path(directory)/'part.3mf'
            intake={'diameter_mm':2,'holes':[{'center_x_z_mm':[0,1],'front_y_mm':0,'cavity_y_mm':2}]}
            grille={'diameter_mm':3.2,'holes':[{'center_x_z_mm':[0,1],'wall_y_mm':[3,5],
                    'bounds_world_mm':[-1.6,1.6,2,9,0,2]}],
                    'support_enforcers':[[0,1,0,1,0,1]]}
            write_rear_project(stl,intake,target,grille);first=target.read_bytes()
            write_rear_project(stl,intake,target,grille)
            self.assertEqual(first,target.read_bytes())
            with zipfile.ZipFile(target) as archive:
                model=ET.fromstring(archive.read('3D/3dmodel.model'))
                ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
                mesh=model.find("m:resources/m:object[@id='1']/m:mesh",ns)
                vertices=[tuple(float(v.attrib[k]) for k in ('x','y','z')) for v in mesh.find('m:vertices',ns)]
                triangles=[tuple(vertices[int(t.attrib[k])] for k in ('v1','v2','v3')) for t in mesh.find('m:triangles',ns)]
                self.assertEqual(len(vertices),4)
                self.assertEqual(triangles,[tuple(points[i] for i in face) for face in faces])
                config=ET.fromstring(archive.read('Metadata/model_settings.config'))
                self.assertEqual(len(config.findall("object/part[@subtype='normal_part']")),1)
                self.assertEqual(len(config.findall("object/part[@subtype='support_blocker']")),2)
                self.assertEqual(len(config.findall("object/part[@subtype='support_enforcer']")),1)
                # 出音孔采用窄 XY 投影向上延伸，真实打印体仍只有一个。
                speaker=model.find("m:resources/m:object[@id='3']/m:mesh/m:vertices",ns)
                zs=[float(v.attrib['z']) for v in speaker]
                self.assertAlmostEqual(min(zs),0)
                self.assertAlmostEqual(max(zs),2.6)
                # 斜孔必须按完整孔道投影禁支撑，不能只覆盖孔口或旧水平孔范围。
                ys=[float(v.attrib['y']) for v in speaker]
                self.assertAlmostEqual(min(ys),.4)
                self.assertAlmostEqual(max(ys),10.6)

    def test_microphone_support_cannot_block_air_or_replace_wall(self):
        layers={z:[((x,-1),(x,1),'Outer wall',.4) for x in (-1.4,1.4)] for z in (.2,.4,.6)}
        witnesses=[{'layer_z_mm':z,'point_mm':[x,y,z-.1]}
                   for z in layers for x in (-1.4,1.4) for y in (-.5,.5)]
        intake={'print_witnesses':{'microphone_0':witnesses},
                'air_samples':[{'layer_z_mm':.4,'point_mm':[0,0,.3],'inside_original_wall':True}]}
        self.assertEqual(audit_microphones(layers,intake)['blocked_air_samples'],0)
        blocked={z:list(paths) for z,paths in layers.items()}
        blocked[.4].append(((0,-1),(0,1),'Support',.4))
        with self.assertRaises(AssertionError):audit_microphones(blocked,intake)
        intake['air_samples'].append({'layer_z_mm':.4,'point_mm':[0,3,.3],'inside_original_wall':False})
        external={z:list(paths) for z,paths in layers.items()}
        external[.4].append(((-1,3),(1,3),'Support',.4))
        self.assertEqual(audit_microphones(external,intake)['external_support_sample_count'],1)
        support_only={z:[(a,b,'Support',w) for a,b,_,w in paths] for z,paths in layers.items()}
        with self.assertRaises(AssertionError):audit_microphones(support_only,intake)

    def test_rotated_asymmetric_plate(self):
        corners = [(0, 0), (5, 0), (5, 1), (2, 1), (2, 3), (0, 3)]
        triangles = []
        paths = []
        for (x, y), (xx, yy) in zip(corners, corners[1:] + corners[:1]):
            a, b, c, d = (x, y, 0), (xx, yy, 0), (xx, yy, 1), (x, y, 1)
            triangles.extend([(a, b, c), (a, c, d)])
            paths.append(((30-y, 40+x), (30-yy, 40+xx), 'Outer wall', .4))
        layers = {z: paths for z in (.2, .4, .6)}
        aligned, transform = align_extrusions(triangles, layers,
                                              {'x': 27, 'y': 40, 'width': 3, 'depth': 5})
        self.assertEqual(transform['rotation_deg'], 90)
        self.assertEqual(aligned[.2][0][:2], ((0, 0), (5, 0)))

        # 包围框对称外扩不能改变实际模型尺寸或平移；仍须吻合墙线。
        padded = {'x': 26.9, 'y': 39.9, 'width': 3.2, 'depth': 5.2}
        aligned, transform = align_extrusions(triangles, layers, padded)
        self.assertTrue(transform['bbox_center_alignment'])
        self.assertAlmostEqual(aligned[.2][0][0][0], 0)
        self.assertAlmostEqual(aligned[.2][0][1][0], 5)
        self.assertAlmostEqual(aligned[.2][0][1][1], 0)

        # 报告框中心若与实际路径不符，不能靠放宽包围框误差通过。
        padded['x'] += 1
        with self.assertRaises(AssertionError):
            align_extrusions(triangles, layers, padded)

    def test_support_filament_modes(self):
        text = '''; Z_HEIGHT:0.2
; FEATURE:Support
M83
G1 X10 E1
G1 E-0.8
G1 E0.8
M82
G92 E0
G1 X20 E2
G1 E1.2
G92 E0
G1 X30 E1
'''
        layers, volume = read_extrusions(text, 0, 0)
        self.assertEqual(len(layers[0.2]), 3)
        self.assertAlmostEqual(volume, 4 * math.pi * (1.75 / 2)**2)

    def test_partial_overlap_is_supported(self):
        layers = {0.2: [((0, 0), (20, 0), 'Outer wall', .45)],
                  .4: [((0, .28), (20, .28), 'Outer wall', .45)]}
        self.assertEqual(audit_support(layers), [])

    def test_floating_wall_is_rejected(self):
        layers = {.2: [((0, 0), (20, 0), 'Outer wall', .45)],
                  .4: [((0, 3), (20, 3), 'Outer wall', .45)]}
        self.assertGreater(audit_support(layers)[0]['unsupported_wall_run_mm'], 19)

    def test_missing_feature_is_rejected(self):
        # 封闭方柱存在于 STL，但 G-code 把它整个遗漏，仅在远处打印。
        corners = [(0, 0), (10, 0), (10, 3), (0, 3)]
        triangles = []
        for (x, y), (xx, yy) in zip(corners, corners[1:] + corners[:1]):
            a, b, c, d = (x, y, 0), (xx, yy, 0), (xx, yy, 1), (x, y, 1)
            triangles.extend([(a, b, c), (a, c, d)])
        layers = {z: [((0, 8), (10, 8), 'Outer wall', .45)] for z in (.2, .4)}
        manifest = {'tilt_deg': 40, 'front_z_mm': 61, 'frame_back_n_mm': 26,
                    'frame_print_y_offset_mm': 0, 'features': [
                        {'name': 'missing', 'part': 'rear_cover', 'space': 'world',
                         'bounds': [-1, 11, -1, 4, 0, 1]}]}
        reports, failures = audit_features(triangles, layers, manifest, 'rear_cover')
        self.assertTrue(failures)
        self.assertEqual(reports['missing']['minimum_coverage'], 0)


if __name__ == '__main__':
    unittest.main()
