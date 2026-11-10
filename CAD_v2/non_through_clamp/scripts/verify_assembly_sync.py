#!/usr/bin/env python3
"""Compare the synced exports to the pre-sync assembly and independent plate.

Draw verification views directly from actual STL surface triangles. This is a
nominal geometry/demo audit, not a manufacturing or sealing qualification.
"""
import argparse
import io
import json
import os
from pathlib import Path
import re
import subprocess

import numpy as np
import trimesh
from export_manifest import ROOT, SCAD, sha, write_json
from verify_cad import solid, cylinder


def draw(mesh, points, old, out):
    os.environ.setdefault('MPLCONFIGDIR','/tmp/kolbe_assembly_mpl')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    for inner in [False,True]:
        fig,ax=plt.subplots(figsize=(12,9),dpi=160)
        if inner:
            tri=mesh.triangles[mesh.face_normals[:,2]>1e-7]
            z=tri[:,:,2].mean(axis=1)
            order=np.argsort(z)
            colors=['#476b89' if h<15 else '#d6e3ec' if h<20.1 else '#a6bdcd' if h<20.7 else '#6589a3' for h in z[order]]
            ax.add_collection(PolyCollection(tri[order,:,:2],facecolors=colors,edgecolors='none',antialiased=False))
            for i,(p,o) in enumerate(zip(points,old),1):
                ax.add_patch(plt.Circle(o,1.98,fill=False,color='#c6762c',ls='--'))
                ax.plot(*p,'+',color='#132f45')
                ax.annotate(f'P{i} ({p[0]:.9f}, {p[1]:.9f})\nBlind diameter 3.96, depth 6\nFloor Z=14; mouth Z=20',xy=p,xytext=(64,25 if i==1 else -20),
                            arrowprops={'arrowstyle':'-','color':'#132f45'},fontsize=9)
            caption='Actual +Z-facing STL surfaces, painted in depth order. Dark discs: blind floors.\nOrange dashed circles: OLD datum references only. Both locators move 2 mm radially inward.'
        else:
            tri=mesh.triangles[mesh.face_normals[:,2]<-0.999999]
            assert np.all(np.abs(tri[:,:,2])<1e-6)
            ax.add_collection(PolyCollection(tri[:,:,:2],facecolors='#d6e3ec',edgecolors='none',antialiased=False))
            for y in [-27,27]:
                ax.annotate(f'(0, {y:+})\nPlain diameter 9\nThrough Z=0..20',xy=(0,y),xytext=(64,y),arrowprops={'arrowstyle':'-','color':'#132f45'},fontsize=10)
            caption='Actual opaque outer STL triangles at Z=0. Exactly 8 fastener holes + 2 liquid holes.\nFlat exterior: no material at Z<0. Locators are blind from the inside and invisible here.'
        ax.set(xlim=(-64,125),ylim=(-66,68),aspect='equal',xlabel='X (mm)',ylabel='Y (mm)')
        ax.set_title('Assembly front endplate — '+('inner surface' if inner else 'outer plane'),fontsize=16)
        ax.grid(alpha=.15)
        fig.text(.12,.045,caption+'\nNominal CAD/demo verification only; not a manufacturing release.',fontsize=9)
        fig.subplots_adjust(bottom=.17)
        fig.savefig(out/('assembly_sync_front_'+('inner' if inner else 'outer')+'.png'))
        plt.close(fig)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--models',type=Path,default=ROOT,help='export root; use .cad-export-stage to audit blocked exports')
    ap.add_argument('--baseline',default='88acaea3f2abf9c67d6382d8a92a186e5e8f9e81')
    ap.add_argument('--reference',type=Path,default=Path('/workspace/kolbe_tools/frontplate_delivery/front_endplate.stl'))
    ap.add_argument('--out',type=Path,default=ROOT/'renders/assembly_sync_verification.json')
    args=ap.parse_args()
    checks=[]
    def check(name,ok,**details):
        checks.append(dict(check=name,pass_=bool(ok),**details))
        if not ok:
            raise AssertionError(name)
    report={'pass':False,'checks':checks,'baseline_commit':args.baseline,
            'source_sha256':sha(SCAD),'scope':'nominal assembly demo sync; not a manufacturing release'}
    try:
        source=SCAD.read_text()
        old=np.array([[-29,20],[29,-17]],dtype=float)
        points=old*(1-2/np.linalg.norm(old,axis=1))[:,None]
        report['locator_formula']='old * (1 - 2 / norm(old))'
        report['locator_points_exact_mm']=points.tolist()
        check('exact shared vector formula',
              'locator_points_old = [[-29,20],[29,-17]];' in source and
              'locator_shift_mm = 2;' in source and
              'locator_points = [for (old = locator_points_old) old * (1 - locator_shift_mm / norm(old))];' in source)
        check('boss/counterbore/thread parameters removed',not re.search(r'port_(?:boss|counterbore|thread)_|M10',source))
        prefix='CAD_v2/non_through_clamp/'
        def baseline(name):
            data=subprocess.check_output(['git','show',args.baseline+':'+prefix+name],cwd=ROOT)
            return data
        previous=json.loads(baseline('stack_manifest.json'))
        current=json.loads((args.models/'stack_manifest.json').read_text())
        except_parameters={'locator_points','locator_points_old','locator_shift_mm'}
        check('all other retained parameters unchanged',all(current['parameters'][k]==v for k,v in previous['parameters'].items()
              if k not in except_parameters and not re.match(r'port_(?:boss|counterbore|thread)_',k)))
        check('dimension chains unchanged',all(current['derived'][k]==v for k,v in previous['derived'].items() if k!='slot_angle'))
        for r in current['instances']:
            before=next(b for b in previous['instances'] if b['id']==r['id'])
            if r['part']!='locator_pin':
                check('assembled placement unchanged '+r['id'],r['translation']==before['translation'] and r['scale']==before['scale'])
        for mode,folder in [('flat_gasket',args.models/'stls'),('oring',args.models/'stls/oring')]:
            mesh=trimesh.load_mesh(folder/'front_endplate.stl',process=True)
            actual=solid(mesh); reference=solid(trimesh.load_mesh(args.reference,process=True))
            added=max(0.,(actual-reference).volume()); removed=max(0.,(reference-actual).volume())
            check('front matches independent delivery '+mode,added<1e-5 and removed<1e-5,
                  added_mm3=added,removed_mm3=removed,reference_sha256=sha(args.reference))
            report[mode]={'bounds_mm':mesh.bounds.tolist(),'volume_mm3':float(mesh.volume),
                          'triangles':len(mesh.faces),'stl_sha256':sha(folder/'front_endplate.stl'),
                          'liquid_channels':2,'liquid_diameter_mm':9,'liquid_centres_mm':[[0,27],[0,-27]],
                          'liquid_through_z_mm':[0,20],'independent_added_mm3':added,'independent_removed_mm3':removed}
            check('actual front bounds '+mode,np.allclose(mesh.bounds,[[-56,-60,0],[56,60,21.8]],atol=2e-5,rtol=0))
            if mode=='flat_gasket':
                draw(mesh,points,old,args.out.parent)
            for name in ['locator_pin','bolt','washer','heatset_nut']:
                prior=baseline(str((folder/(name+'.stl')).relative_to(args.models)))
                check('hardware bytes unchanged '+mode+'/'+name,(folder/(name+'.stl')).read_bytes()==prior)
            # Fill small old/new locator envelopes in both versions. Any remaining
            # 3D difference would be an unintended change elsewhere in the layer.
            for name in ['rear_endplate','frame','gasket','gasket_tab_left','gasket_tab_right',
                         'electrode_plain','electrode_tab','electrode_tab_right']:
                rel=str((folder/(name+'.stl')).relative_to(args.models))
                a=solid(trimesh.load_mesh(folder/(name+'.stl'),process=True))
                b=solid(trimesh.load_mesh(io.BytesIO(baseline(rel)),file_type='stl',process=True))
                height=max(a.bounding_box()[5],b.bounding_box()[5])
                for xy in np.vstack([old,points]):
                    fill=cylinder(7,height+2,[*xy,-1])
                    a=a+fill; b=b+fill
                added=max(0.,(a-b).volume()); removed=max(0.,(b-a).volume())
                check('only locator regions changed '+mode+'/'+name,added<1e-5 and removed<1e-5,
                      added_outside_locator_envelopes_mm3=added,removed_outside_locator_envelopes_mm3=removed)
        report['pass']=True
    except Exception as exc:
        report['error']=str(exc)
        raise
    finally:
        report['checks']=[{**{k:v for k,v in c.items() if k!='pass_'},'pass':c['pass_']} for c in checks]
        report['check_count']=len(checks)
        write_json(args.out,report)
        print(('PASS' if report['pass'] else 'FAIL')+f': assembly sync; {len(checks)} checks',flush=True)


if __name__=='__main__':
    main()
