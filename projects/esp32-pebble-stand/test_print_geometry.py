"""验证自动排版校准与功能实体漏打检查，不依赖切片器。"""
import math
import unittest
from print_geometry import align_extrusions, audit_witnesses, read_extrusions, audit_hooks, audit_support_runs


class PrintGeometryTests(unittest.TestCase):
    def test_rotated_asymmetric_plate_and_wrong_offset(self):
        corners=[(0,0),(5,0),(5,1),(2,1),(2,3),(0,3)]
        triangles=[]
        paths=[]
        for (x,y),(xx,yy) in zip(corners,corners[1:]+corners[:1]):
            a,b,c,d=(x,y,0),(xx,yy,0),(xx,yy,1),(x,y,1)
            triangles.extend([(a,b,c),(a,c,d)])
            paths.append(((30-y,40+x),(30-yy,40+xx),'Outer wall',.4))
        layers={z:paths for z in (.2,.4,.6)}
        box={'x':27,'y':40,'width':3,'depth':5}
        aligned,transform=align_extrusions(triangles,layers,box)
        self.assertEqual(transform['rotation_deg'],90)
        self.assertEqual(aligned[.2][0][:2],((0,0),(5,0)))
        padded={'x':26.9,'y':39.9,'width':3.2,'depth':5.2}
        _,transform=align_extrusions(triangles,layers,padded)
        self.assertTrue(transform['bbox_center_alignment'])
        padded['x']+=1
        with self.assertRaises(AssertionError):
            align_extrusions(triangles,layers,padded)

    def test_absolute_and_relative_extrusions(self):
        text='; Z_HEIGHT:0.2\n; FEATURE:Support\nM83\nG1 X10 E1\nG1 E-0.8\nG1 E0.8\nM82\nG92 E0\nG1 X20 E2\nG1 E1.2\nG92 E0\nG1 X30 E1\n'
        layers,volume=read_extrusions(text,0,0)
        self.assertEqual(len(layers[.2]),3)
        self.assertAlmostEqual(volume,4*math.pi*(1.75/2)**2)

    def test_support_and_remote_paths_cannot_replace_material(self):
        witnesses={'wall':[{'layer_z_mm':.2,'point_mm':[x,0,.1]} for x in (1,2,3)]}
        paths={.2:[((0,0),(4,0),'Support',.45),((0,8),(4,8),'Outer wall',.45)]}
        with self.assertRaises(AssertionError):
            audit_witnesses(paths,witnesses)
        paths[.2].append(((0,0),(4,0),'Inner wall',.45))
        self.assertEqual(audit_witnesses(paths,witnesses)['wall']['coverage'],1)

    def test_hook_requires_real_walls_and_measured_crossings(self):
        corners=[(0,-1),(2.4,-1),(2.4,1),(0,1)]
        triangles=[]
        for a,b in zip(corners,corners[1:]+corners[:1]):
            triangles.extend([((a[0],a[1],0),(b[0],b[1],0),(b[0],b[1],1)),
                              ((a[0],a[1],0),(b[0],b[1],1),(a[0],a[1],1))])
        outer=[((.2,-.8),(2.2,-.8),'Outer wall',.45),((2.2,-.8),(2.2,.8),'Outer wall',.45),
               ((2.2,.8),(.2,.8),'Outer wall',.45),((.2,.8),(.2,-.8),'Outer wall',.45)]
        layers={z:list(outer) for z in (.2,.4,.6,.8,1)}
        features=[{'name':'lug','angle_deg':0,'bounds':[0,2.4,-1,1,0,1],
                   'probe_t':0,'probe_r':[0,2.4],'kind':'lug'}]
        frame={'origin':[0,0,0],'up':[0,1,0],'normal':[0,0,1],
               'carrier_y_origin':0,'carrier_back_n':1}
        # 轮廓完整仍不等于承力截面足够：仅两道墙线必须拒绝。
        with self.assertRaises(AssertionError):audit_hooks(layers,triangles,features,frame,True)
        for paths in layers.values():
            paths.extend([((x,-.8),(x,.8),'Inner wall',.45) for x in (.6,1.,1.4,1.8)])
        result=audit_hooks(layers,triangles,features,frame,True)
        self.assertEqual(result['features']['lug']['minimum_material_crossings'],6)
        self.assertEqual(result['features']['lug']['minimum_load_path_coverage'],1)
        fake={z:[(a,b,'Support',w) for a,b,_,w in paths] for z,paths in layers.items()}
        with self.assertRaises(AssertionError):audit_hooks(fake,triangles,features,frame,True)

    def test_real_underlying_support_limits_unsupported_span(self):
        layers={.2:[((0,10),(5,10),'Outer wall',.45)],
                .4:[((0,0),(5,0),'Outer wall',.45)]}
        self.assertGreater(audit_support_runs(layers)[0]['unsupported_wall_run_mm'],4.1)
        layers[.2].append(((0,0),(5,0),'Support',.45))
        self.assertEqual(audit_support_runs(layers)[0]['unsupported_wall_run_mm'],0)

    def test_brim_can_support_but_cannot_replace_body(self):
        text='; Z_HEIGHT:0.2\n; FEATURE:Brim\nM83\nG1 X5 E1\n'
        self.assertEqual(read_extrusions(text,0,0)[0],{})
        layers,_=read_extrusions(text,0,0,include_brim=True)
        self.assertEqual(layers[.2][0][2],'Support brim')
        witnesses={'body':[{'layer_z_mm':.2,'point_mm':[x,0,.1]} for x in (1,2,3)]}
        with self.assertRaises(AssertionError):audit_witnesses(layers,witnesses)


if __name__=='__main__':
    unittest.main()
