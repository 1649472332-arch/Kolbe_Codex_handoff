from pathlib import Path
import json, math, sys
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import FreeCAD as App, Part
V=App.Vector
import cad_common as C
P=C.P

def close_doc(doc):
    if doc and App.getDocument(doc.Name):
        App.closeDocument(doc.Name)

def bb(shape):
    b=shape.BoundBox
    return [round(x,6) for x in (b.XMin,b.XMax,b.YMin,b.YMax,b.ZMin,b.ZMax)]

def audit_component(code,path):
    doc=None
    try:
        doc=App.openDocument(str(path))
        bodies=[o for o in doc.Objects if o.TypeId=='PartDesign::Body']
        if not bodies:
            shapes=[o.Shape for o in doc.Objects if hasattr(o,'Shape') and not o.Shape.isNull()]
            shape=shapes[-1] if shapes else None
        else: shape=bodies[0].Shape
        ok=bool(shape and shape.isValid() and len(shape.Solids)==1 and shape.Volume>0)
        return {'code':code,'source':path.name,'valid':bool(shape and shape.isValid()),'solid_count':len(shape.Solids) if shape else 0,'volume_mm3':round(shape.Volume,6) if shape else None,'bbox_mm':bb(shape) if shape else None,'pass':ok}
    except Exception as e:
        return {'code':code,'source':path.name,'pass':False,'error':str(e)}
    finally:
        close_doc(doc)

def common_volume(shape,probe):
    return shape.common(probe).Volume

def rounded_path_points(size,r,per_segment=5,per_arc=8):
    a=size/2.0;b=a-r;pts=[]
    # Four straight sections.
    for i in range(per_segment+1):
        t=i/per_segment; x=-b+2*b*t
        pts.extend([(x,-a),(a,x),(b-2*b*t,a),(-a,b-2*b*t)])
    # Four corner arcs, sampled including endpoints.
    arcs=[(b,-b,-math.pi/2,0),(b,b,0,math.pi/2),(-b,b,math.pi/2,math.pi),(-b,-b,math.pi,3*math.pi/2)]
    for cx,cy,t0,t1 in arcs:
        for i in range(per_arc+1):
            ang=t0+(t1-t0)*i/per_arc
            pts.append((cx+r*math.cos(ang),cy+r*math.sin(ang)))
    return pts

# Derive the current custom-component inventory from all three generated stack BOM manifests.
assembly_parts={}
for n in (3,5,7):
    data=json.loads((ROOT/'validation'/f'assembly_{n}.json').read_text(encoding='utf-8'))
    for meta in data.get('parts',[]): assembly_parts[meta.get('code')]=meta
custom_codes=sorted(c for c in assembly_parts if not c.startswith('STD-') and not c.endswith('-COMP'))
part_checks=[]
for code in custom_codes:
    part_checks.append(audit_component(code,ROOT/'parts'/(code+'.FCStd')))

# Assembly-generated free-state seal solids are not standalone part documents; inspect their linked BReps.
seal_checks=[]
asm=None
try:
    asm=App.openDocument(str(ROOT/'assemblies'/'Kolbe_5.FCStd'))
    found={}
    for ob in asm.Objects:
        pn=getattr(ob,'PartNumber','')
        if pn in ('KS-101-COMP','KS-102-COMP') and pn not in found:
            shape=ob.Shape
            found[pn]={'code':pn,'source':'assembly generated compressed seal','valid':shape.isValid(),'solid_count':len(shape.Solids),'volume_mm3':round(shape.Volume,6),'pass':shape.isValid() and len(shape.Solids)==1 and shape.Volume>0}
    seal_checks=list(found.values())
finally: close_doc(asm)

# Inspect the latest flow-frame PartDesign body directly.
frame_doc=App.openDocument(str(ROOT/'parts'/'KF-101.FCStd'))
frame_body=next(o for o in frame_doc.Objects if o.TypeId=='PartDesign::Body')
shape=frame_body.Shape

# Fully continuous void probes: window to each plugged manufacturing access, D8 axial bores,
# and local junction volumes where each branch meets its manifold and the wet window.
probe_results=[]
def void_test(name,probe):
    v=common_volume(shape,probe)
    probe_results.append({'name':name,'material_interference_mm3':round(v,10),'pass':v<=1e-5})

# Cross-drilled channels, including their chamber and M4 pilot junctions.
for side,sgn in [('upper',1),('lower',-1)]:
    start_y=25*sgn
    direction=V(0,sgn,0)
    channel=Part.makeCylinder(0.4,50.0,V(0,start_y,3),direction)
    void_test(f'{side}_wet_window_to_M4_access_axis',channel)
    junction_y=62*sgn
    void_test(f'{side}_branch_to_axial_manifold_junction',Part.makeSphere(0.45,V(0,junction_y,3)))
    wet_y=25*sgn
    void_test(f'{side}_branch_to_window_junction',Part.makeSphere(0.45,V(0,wet_y,3)))
    manifold=Part.makeCylinder(2.0,P['gap'],V(0,junction_y,0),V(0,0,1))
    void_test(f'{side}_D8_axial_manifold_axis',manifold)

# Verify each closed perimeter groove is clear at many points on both faces.
main_loop_checks=[]
for face,z0 in [('top',P['gap']-P['groove_depth']+0.15),('bottom',P['groove_depth']-0.25)]:
    vols=[]
    for x,y in rounded_path_points(P['seal_centerline_size'],P['seal_corner']):
        vols.append(common_volume(shape,Part.makeCylinder(0.08,0.1,V(x,y,z0),V(0,0,1))))
    vmax=max(vols) if vols else 0
    main_loop_checks.append({'face':face,'sample_count':len(vols),'max_material_interference_mm3':round(vmax,10),'pass':vmax<=1e-5})

# Verify all annular manifold face-seal grooves at 32 points on each ring/face.
mani_loop_checks=[]
rmean=P['manifold_seal_mean_d']/2
for face,z0 in [('top',P['gap']-P['manifold_groove_depth']+0.15),('bottom',P['manifold_groove_depth']-0.25)]:
    for mx,my in P['manifold_points']:
        vols=[]
        for i in range(32):
            t=2*math.pi*i/32
            x=float(mx)+rmean*math.cos(t); y=float(my)+rmean*math.sin(t)
            vols.append(common_volume(shape,Part.makeCylinder(0.08,0.1,V(x,y,z0),V(0,0,1))))
        vmax=max(vols) if vols else 0
        mani_loop_checks.append({'face':face,'center_xy':[mx,my],'sample_count':len(vols),'max_material_interference_mm3':round(vmax,10),'pass':vmax<=1e-5})

frame_record={'valid':shape.isValid(),'solid_count':len(shape.Solids),'volume_mm3':round(shape.Volume,6),'bbox_mm':bb(shape)}
frame_feature_counts=dict(Counter(o.TypeId for o in frame_body.Group))
# Explicit design arithmetic for squeeze, gland fill and remaining lands.
main_cs=P['seal_cs'];main_w=P['groove_width'];main_d=P['groove_depth']
mani_cs=P['manifold_seal_cs'];mani_w=P['manifold_groove_width'];mani_d=P['manifold_groove_depth']
main_outer=P['seal_centerline_size']+main_w
main_inner=P['seal_centerline_size']-main_w
metrics={
 'chamber_area_mm2':round(P['window']**2-(4-math.pi)*P['window_corner']**2,6),
 'electrode_coupon_area_mm2':round(P['electrode_width']*P['electrode_height']-(4-math.pi)*2.0**2,6),
 'electrode_coupon_corner_radius_mm':2.0,
 'chamber_to_coupon_area_percent':round(100*(P['window']**2-(4-math.pi)*P['window_corner']**2)/(P['electrode_width']*P['electrode_height']-(4-math.pi)*2.0**2),4),
 'main_gland':{'cs_mm':main_cs,'groove_width_mm':main_w,'depth_mm':main_d,'squeeze_percent':round(100*(main_cs-main_d)/main_cs,4),'fill_percent':round(100*(math.pi*(main_cs/2)**2/(main_w*main_d)),4),'outer_envelope_mm':round(main_outer,3),'metal_coupon_outer_land_each_side_mm':round((P['electrode_width']-main_outer)/2,3),'inner_envelope_mm':round(main_inner,3),'window_edge_to_groove_inner_land_mm':round((main_inner-P['window'])/2,3)},
 'manifold_gland':{'cs_mm':mani_cs,'groove_width_mm':mani_w,'depth_mm':mani_d,'squeeze_percent':round(100*(mani_cs-mani_d)/mani_cs,4),'fill_percent':round(100*(math.pi*(mani_cs/2)**2/(mani_w*mani_d)),4)},
 'minimum_branch_cover_to_main_groove_floor_mm':round(P['gap']/2-main_d-P['port_bore']/2,3),
 'minimum_branch_cover_to_manifold_groove_floor_mm':round(P['gap']/2-mani_d-P['port_bore']/2,3)
}

close_doc(frame_doc)
all_checks=part_checks+seal_checks
passed=all(c.get('pass') for c in all_checks) and all(x['pass'] for x in probe_results+main_loop_checks+mani_loop_checks)
result={
 'audit':'FreeCAD BRep geometry audit; not a pressure, fluid-dynamics, materials, or manufacturing qualification',
 'revision':P['revision'],'units':'mm','runtime':'FreeCAD bundled Python / Part BRep',
 'active_stack_configurations':[3,5,7],
 'custom_part_count':len(custom_codes),'custom_parts':part_checks,
 'assembly_generated_seal_solids':seal_checks,
 'kf101':{'file':'parts/KF-101.FCStd',**frame_record,'feature_type_counts':{},'flow_void_probes':probe_results,'main_perimeter_groove_closed_loop_samples':main_loop_checks,'manifold_groove_closed_loop_samples':mani_loop_checks},
 'dimensional_metrics':metrics,
 'overall_pass':passed,
 'unresolved':['Actual electrode/foil and carrier dimensional tolerances require supplier confirmation.','Flow distribution, pressure rating, fluid compatibility, shunt-current effects, and plug/washer sealing are untested.','The 6 mm frame thickness is a provisional mechanical envelope; operating gap remains TBD.']
}
# Native feature inventory and model dimensions for record.
from collections import Counter
result['kf101']['feature_type_counts']=frame_feature_counts
(ROOT/'validation'/'geometry_audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({'overall_pass':passed,'custom_parts':len(custom_codes),'part_failures':[x for x in part_checks if not x['pass']],'seal_checks':seal_checks,'probe_failures':[x for x in probe_results+main_loop_checks+mani_loop_checks if not x['pass']],'metrics':metrics},indent=2))






