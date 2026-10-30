"""验证切片核验器能识别漏打、悬空和正常斜壁搭接。"""
import math
import unittest
from print_audit import audit_features, audit_support, read_extrusions, align_extrusions


class PrintAuditTests(unittest.TestCase):
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
