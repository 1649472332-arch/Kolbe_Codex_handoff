"""Self-contained FCStd assemblies with native definitions, App::Link instances,
STEP solids, exact placement/BOM data and BRep interference review.
Run with FreeCAD's bundled Python. No mesh intermediates are used.
"""
import sys,json,math,csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import cad_common as C
import FreeCAD as A,Part,Import
from chinese_names import instance_label, localize_document
P=C.P;V=A.Vector
COLORS={'frame':(.09,.11,.13),'carrier':(.14,.16,.18),'electrode':(.78,.8,.82),
        'anode':(.8,.74,.55),'insulator':(.74,.63,.39),'plate':(.13,.15,.18),
        'seal':(.20,.54,.58),'copper':(.76,.38,.16),'hardware':(.69,.72,.76),'tube':(.86,.87,.85)}

def placement(x=0,y=0,z=0,axis=None,angle=0):
    return A.Placement(V(x,y,z),A.Rotation(V(*axis),angle) if axis else A.Rotation())

def compressed_seal(main=True):
    cs=P['seal_cs'] if main else P['manifold_seal_cs']
    h=P['groove_depth'] if main else P['manifold_groove_depth']
    width=cs*cs/h
    if main:
        size=P['seal_centerline_size'];r=P['seal_corner']
        path=Part.Wire([g.toShape() for g in C.rounded(size,size,r)])
        start=V(-size/2+r,-size/2,0);normal=V(1,0,0)
        edge=Part.Ellipse(V(0,0,0),width/2,h/2).toShape()
        edge.rotate(V(),V(1,1,1),120);edge.translate(start)
    else:
        radius=P['manifold_seal_mean_d']/2
        path=Part.Wire([Part.makeCircle(radius)])
        # At +X the tangent is +Y; the profile is in the XZ plane.
        edge=Part.Ellipse(V(),width/2,h/2).toShape()
        edge.rotate(V(),V(1,0,0),90);edge.translate(V(radius,0,0))
    shape=path.makePipeShell([Part.Wire([edge])],True,True)
    assert shape.isValid() and len(shape.Solids)==1
    return shape

def main(n,exploded=False):
    tag=f'Kolbe_{n}'+('_exploded' if exploded else '')
    doc=C.doc_new(tag)
    defs=doc.addObject('App::DocumentObjectGroup','Definitions');defs.Label='原生零件定义 / Native editable definitions'
    stack=doc.addObject('App::Part','Stack');stack.Label=f'{n} 片紧凑板框电堆 / Internal parallel manifolds'
    stack.Visibility=True
    stack.addProperty('App::PropertyInteger','ElectrodeCount','Design');stack.ElectrodeCount=n
    stack.addProperty('App::PropertyLength','ReviewGap','Design');stack.ReviewGap=P['gap']
    stack.addProperty('App::PropertyString','GapStatus','Design');stack.GapStatus=P['electrode_gap_status']
    stack.addProperty('App::PropertyString','Configuration','Design');stack.Configuration=P['configuration']
    stack.addProperty('App::PropertyString','ConstraintMethod','Design');stack.ConstraintMethod='Deterministic datum placements in build_assemblies.py; not solved Assembly workbench joints'
    masters={};instances=[];source_docs=[]
    def master(code):
        if code in masters:return masters[code]
        src=A.openDocument(str(ROOT/'parts'/(code+'.FCStd')));source_docs.append(src)
        bodies=[o for o in src.Objects if o.TypeId=='PartDesign::Body']
        body=doc.copyObject(bodies[0],True)
        body.Label=code+' | '+bodies[0].Label
        defs.addObject(body);body.Visibility=False
        for o in body.Group:o.Visibility=False
        body.Tip.Visibility=True
        masters[code]=body
        return body
    def shape_master(code,shape,label):
        if code in masters:return masters[code]
        f=doc.addObject('PartDesign::Feature',code.replace('-','_'));f.Shape=shape;f.Label=label
        f.addProperty('App::PropertyString','Representation','Design');f.Representation='Assembly deformation visualization, free-state supplier part is in parts/'
        defs.addObject(f);f.Visibility=False;masters[code]=f
        return f
    def instance(code,pl,role,color='hardware',shape=None,label=None):
        src=shape_master(code,shape,label or code) if shape is not None else master(code)
        ob=doc.addObject('App::Link','I_'+str(len(instances)+1))
        ob.setLink(src);ob.LinkTransform=True;ob.LinkPlacement=pl;ob.Label=instance_label(code,role)
        ob.addProperty('App::PropertyString','PartNumber','BOM');ob.PartNumber=code
        ob.addProperty('App::PropertyString','Function','BOM');ob.Function=role
        ob.addProperty('App::PropertyString','DisplayColor','BOM');ob.DisplayColor=color
        stack.addObject(ob);ob.Visibility=True
        instances.append({'object':ob,'code':code,'role':role,'color':color})
        return ob
    active=n*P['electrode_thickness']+(n-1)*P['gap'];H=44+active;z0=26;pitch=P['gap']+P['electrode_thickness']
    ex=12 if exploded else 0
    def ez(z,layer):return z+layer*ex
    instance('KP-201',placement(z=0),'Front pressure plate','plate')
    instance('KP-202',placement(z=ez(12,1)),'Front insulating fluid adapter','insulator')
    mainseal=compressed_seal(True);maniseal=compressed_seal(False)
    # Two manifold seals on the outer cathode/front insulator interface.
    for x,y in P['manifold_points']:
        instance('KS-102-COMP',placement(x,y,ez(26-P['manifold_groove_depth']/2,1)), 'Front manifold seal','seal',maniseal)
    for i in range(n):
        z=z0+i*pitch;layer=2+2*i
        pol='C' if i%2==0 else 'A';coupon='KP-102' if pol=='C' else 'KP-101';carrier='KP-602' if pol=='C' else 'KP-601'
        instance(carrier,placement(z=ez(z,layer)),f'Precision insulating carrier {i} ({pol})','carrier')
        instance(coupon,placement(z=ez(z,layer)),f'Electrode {i} ({pol}), both faces exposed when internal','anode' if pol=='A' else 'electrode')
        if i<n-1:
            fz=z+P['electrode_thickness'];fl=layer+1
            instance('KF-101',placement(z=ez(fz,fl)),f'Parallel flow channel {i}','frame')
            for center in [fz+P['groove_depth']/2,fz+P['gap']-P['groove_depth']/2]:
                instance('KS-101-COMP',placement(z=ez(center,fl)),f'Channel {i} perimeter seal','seal',mainseal)
            for x,y in P['manifold_points']:
                for center in [fz+P['manifold_groove_depth']/2,fz+P['gap']-P['manifold_groove_depth']/2]:
                    instance('KS-102-COMP',placement(x,y,ez(center,fl)),f'Channel {i} manifold seal','seal',maniseal)
            if not exploded:
                for sign in [-1,1]:
                    instance('KH-901',placement(0,sign*69.3,fz+3,(0,0,1),0 if sign>0 else 180),f'Channel {i} crossdrill plug','hardware')
                    instance('KH-902',placement(0,sign*74.8,fz+3,(0,0,1),0 if sign>0 else 180),f'Channel {i} plug face washer','seal')
    rearz=z0+active;rearlayer=2*n+2
    instance('KP-203',placement(z=ez(rearz,rearlayer)),'Rear insulating manifold closure','insulator')
    for x,y in P['manifold_points']:
        instance('KS-102-COMP',placement(x,y,ez(rearz+P['manifold_groove_depth']/2,rearlayer)), 'Rear manifold seal','seal',maniseal)
    instance('KP-204',placement(z=ez(H-12,rearlayer+1)),'Rear pressure plate','plate')
    # In the exploded document separate the sheet carriers and coupons laterally.
    if exploded:
        for item in instances:
            if item['code'] in ['KP-101','KP-102']:
                item['object'].LinkPlacement.Base.x=190
    else:
        # Copper busbars and dedicated supports/clamps/M4 fasteners removed.
        for x,y in P['bolt_points']:
            foot=0  # Seat directly on pressure plates after support removal.
            rodcode=f'STD-M8-ROD-{n}-'+('SUPPORT' if foot else 'PLATE')
            instance(rodcode,placement(x,y,-foot-10.1),'Stack tie rod')
            instance('STD-M8-WASHER',placement(x,y,-foot-1.6),'Front tie washer')
            instance('STD-M8-NUT',placement(x,y,-foot-8.1),'Front tie nut')
            instance('STD-M8-WASHER',placement(x,y,H+foot),'Rear tie washer')
            instance('STD-M8-NUT',placement(x,y,H+foot+1.6),'Rear tie nut')
        # Continuous insulated pins: 0.1 mm end clearance in each blind hole.
        for x,y in P['locator_points']:
            instance(f'STD-LOCATOR-{n}',placement(x,y,9.1),'Insulating alignment pin','insulator')
        # Front-only tubing ports. Source fitting parts have their physical axis along +Y.
        for x,y in P['manifold_points']:
            rot=(1,0,0)
            instance('KP-501',placement(x,y,20,rot,-90),'Front M6x1 tube compression nut')
            instance('KP-502',placement(x,y,22,rot,-90),'Front compression ferrule','seal')
            instance('KP-503',placement(x,y,22,rot,-90),'Front electrolyte tubing','tube')
    doc.recompute()
    # Native groups remain editable; each instance is linked to an embedded definition.
    for src in masters.values():src.Visibility=False
    for item in instances:item['object'].Visibility=True
    doc.recompute()
    stem=ROOT/'assemblies'/tag
    localize_document(doc)
    doc.saveAs(str(stem.with_suffix('.FCStd')))
    Import.export([stack],str(stem.with_suffix('.step')))
    roundtrip=Part.Shape();roundtrip.read(str(stem.with_suffix('.step')))
    if len(roundtrip.Solids)!=len(instances):raise RuntimeError('STEP round-trip solid count mismatch')
    rows=[]
    for item in instances:
        ob=item['object'];s=ob.Shape
        if not s.isValid() or len(s.Solids)!=1:raise RuntimeError('Invalid instance '+ob.Label)
        rows.append({'name':ob.Name,'code':item['code'],'function':item['role'],'valid':True,'volume_mm3':s.Volume,'bounds':[s.BoundBox.XMin,s.BoundBox.YMin,s.BoundBox.ZMin,s.BoundBox.XMax,s.BoundBox.YMax,s.BoundBox.ZMax]})
    if not exploded:
        # Exact volumetric intersections, excluding designated thread engagement interfaces.
        issues=[];intentional=[]
        for ia in range(len(instances)):
            aa=instances[ia];sa=aa['object'].Shape;ba=sa.BoundBox
            for ib in range(ia+1,len(instances)):
                bb=instances[ib];sb=bb['object'].Shape;bc=sb.BoundBox
                if min(ba.XMax,bc.XMax)-max(ba.XMin,bc.XMin)<1e-5 or min(ba.YMax,bc.YMax)-max(ba.YMin,bc.YMin)<1e-5 or min(ba.ZMax,bc.ZMax)-max(ba.ZMin,bc.ZMin)<1e-5:continue
                vol=sa.common(sb).Volume
                if vol<1e-4:continue
                record={'a':aa['object'].Name,'a_code':aa['code'],'b':bb['object'].Name,'b_code':bb['code'],'volume_mm3':round(vol,6)}
                if set([aa['code'],bb['code']])==set(['KF-101','KH-901']) or ('STD-M4-S12' in [aa['code'],bb['code']] and any(x.startswith('KB-A') or x.startswith('KB-C') for x in [aa['code'],bb['code']])):intentional.append(record)
                else:issues.append(record)
        report={'configuration':n,'body_stack_height_mm':H,'active_stack_height_mm':active,'gap_mm_provisional':6,'instances':len(rows),'all_valid':True,'unresolved_intersections':issues,'cosmetic_thread_engagement_intersections':intentional,'parts':rows}
        (ROOT/'validation'/f'assembly_{n}.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        counts={}
        for item in instances:counts[item['code']]=counts.get(item['code'],0)+1
        with (ROOT/'drawings'/f'BOM_{n}.csv').open('w',newline='',encoding='utf-8-sig') as f:
            w=csv.writer(f);w.writerow(['Part number','Quantity','Note'])
            for code,count in counts.items():w.writerow([code.replace('-COMP',''),count,'Compressed seal shown in assembly' if '-COMP' in code else 'See native component document'])
        print(json.dumps({'n':n,'instances':len(rows),'height':H,'interferences':len(issues),'details':issues},ensure_ascii=False),flush=True)
    for src in source_docs:
        if src.Name in A.listDocuments():A.closeDocument(src.Name)
    A.closeDocument(doc.Name)

def standards():
    def save(code,diameter,length,hole=0,af=0,head=False):
        d=C.doc_new(code.replace('-','_'));b=C.body_new(d,'Body',code)
        if af:
            radius=af/math.sqrt(3)
            points=[(radius*math.cos(i*math.pi/3),radius*math.sin(i*math.pi/3)) for i in range(6)]
            geos=C.poly(points)+[C.circle(0,0,hole/2)]
        else:geos=[C.circle(0,0,diameter/2)]+([C.circle(0,0,hole/2)] if hole else [])
        sk=C.sketch(b,'Section',geos);C.pad(b,'Length',sk,length)
        if head:
            hs=C.sketch(b,'LowHead',[C.circle(0,0,3.5)]);C.pad(b,'Head',hs,2.2,True)
            hx=C.sketch(b,'HexSocket',C.poly([(1.3*math.cos(i*math.pi/3),1.3*math.sin(i*math.pi/3)) for i in range(6)]),C.at_z(-2.2))
            C.pocket(b,'Socket',hx,1.3,True)
        b.addProperty('App::PropertyString','ThreadRepresentation','Specification');b.ThreadRepresentation='Nominal smooth geometry, thread specification in part label; no modeled helix'
        C.finish(d,b,code,'PEEK provisional' if 'LOCATOR' in code else 'Stainless steel, grade and fastener strength class TBD')
        A.closeDocument(d.Name)
    save('STD-M8-WASHER',16,1.6,8.4)
    save('STD-M8-NUT',0,6.5,8.2,13)
    for n in [3,5,7]:
        active=n*.35+(n-1)*6;H=44+active
        for foot,label in [(0,'PLATE')]:save(f'STD-M8-ROD-{n}-{label}',8,H+2*foot+20.2)
        save(f'STD-LOCATOR-{n}',3,H-18.2)

if __name__=='__main__':
    standards()
    for n in [3,5,7]:main(n)
    main(5,True)
