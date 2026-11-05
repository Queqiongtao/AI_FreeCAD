"""验证切片审计拒绝漏打、悬空、支撑冒充实体和坐标错配。"""
import math
import unittest
from print_audit import audit_support, read_extrusions, align_extrusions, audit_microphones
from verify_print import audit_contours


class SlicingTests(unittest.TestCase):
    def test_volume_audit_preserves_translation_and_detects_added_material(self):
        import FreeCAD as App
        import Part
        from verify_fit import stable_mesh_volume
        shape=Part.makeBox(2,3,4)
        moved=shape.copy();moved.translate(App.Vector(100000,100000,100000))
        self.assertAlmostEqual(stable_mesh_volume(shape,.04),24,places=6)
        self.assertAlmostEqual(stable_mesh_volume(moved,.04),24,places=6)
        changed=Part.makeBox(2,3,4.1)
        self.assertGreater(stable_mesh_volume(changed,.04)-stable_mesh_volume(shape,.04),.5)

    def test_step_mirrored_parts_match_by_position(self):
        import FreeCAD as App
        import Part
        from verify_fit import match_step_bounds
        left=Part.makeBox(2,3,4,App.Vector(-30,0,0))
        right=Part.makeBox(2,3,4,App.Vector(30,0,0))
        self.assertEqual(match_step_bounds([right,left],[left,right]),[0,0])
        moved=right.copy();moved.translate(App.Vector(1,0,0))
        self.assertEqual(max(match_step_bounds([moved,left],[left,right])),1)

    def test_missing_contour_and_support_are_not_model(self):
        corners=[(0,0),(10,0),(10,3),(0,3)]; triangles=[]; paths=[]
        for a,b in zip(corners,corners[1:]+corners[:1]):
            p,q,r,s=(*a,0),(*b,0),(*b,1),(*a,1)
            triangles.extend([(p,q,r),(p,r,s)])
            paths.append((a,b,'Outer wall',.45))
        layers={z:paths for z in (.2,.4,.6,.8,1)}
        self.assertEqual(audit_contours(triangles,layers)['minimum_coverage'],1)
        self.assertLess(audit_contours(triangles,{z:v[1:] for z,v in layers.items()})['minimum_coverage'],.95)
        self.assertEqual(audit_contours(triangles,{z:[(a,b,'Support',w) for a,b,_,w in v]
            for z,v in layers.items()})['minimum_coverage'],0)

    def test_wall_overlap_and_floating_wall(self):
        first=[((0,0),(20,0),'Outer wall',.45)]
        self.assertEqual(audit_support({.2:first,.4:[((0,.28),(20,.28),'Outer wall',.45)]}),[])
        self.assertGreater(audit_support({.2:first,.4:[((0,3),(20,3),'Outer wall',.45)]})[0]['unsupported_wall_run_mm'],19)

    def test_support_nearby_can_support_tray_deck(self):
        layers={.2:[((0,0),(20,0),'Support',.45)],
            .6:[((0,0),(20,0),'Outer wall',.45)]}
        self.assertEqual(audit_support(layers),[])

    def test_air_channel_cannot_be_blocked_by_support(self):
        layers={z:[((x,-1),(x,1),'Outer wall',.4) for x in (-1.4,1.4)] for z in (.2,.4,.6)}
        intake={'print_witnesses':{'mic':[{'layer_z_mm':z,'point_mm':[x,y,z-.1]}
            for z in layers for x in (-1.4,1.4) for y in (-.5,.5)]},
            'air_samples':[{'layer_z_mm':.4,'point_mm':[0,0,.3],'inside_original_wall':True}]}
        self.assertEqual(audit_microphones(layers,intake)['blocked_air_samples'],0)
        layers[.4].append(((0,-1),(0,1),'Support',.4))
        with self.assertRaises(AssertionError):
            audit_microphones(layers,intake)

    def test_extrusion_modes_count_deposited_support(self):
        text='; Z_HEIGHT:0.2\n; FEATURE:Support\nM83\nG1 X10 E1\nG1 E-0.8\nG1 E0.8\nM82\nG92 E0\nG1 X20 E2\n'
        layers,volume=read_extrusions(text,0,0)
        self.assertEqual(len(layers[.2]),2)
        self.assertAlmostEqual(volume,3*math.pi*(1.75/2)**2)


if __name__=='__main__':
    unittest.main()
