from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import cad_common as C
import FreeCAD as App, Part
V=App.Vector
P=C.P

def add_pocket(body,name,geos,place,length,reversed=False):
    s=C.sketch(body,name+'Profile',geos,place)
    return C.pocket(body,name,s,length,reversed)

def check_feature(f,name):
    f.Document.recompute()
    if f.Shape.isNull() or not f.Shape.isValid() or len(f.Shape.Solids)!=1:
        raise ValueError('%s produced invalid/non-single solid geometry'%name)

def axis_plane(y, upper):
    rot=App.Rotation(V(1,0,0),-90 if upper else 90)
    return App.Placement(V(0,y,P['gap']/2),rot)

code='KF-101'
try: App.closeDocument('InternalManifoldFrame')
except Exception: pass
doc=App.newDocument('InternalManifoldFrame')
body=C.body_new(doc,'FlowFrame','Internal-manifold flow frame '+code)
# Explicit editable design metadata, including non-functional plugged drill access.
for name,val in [('NominalGap',P['gap']),('WindowSize',P['window']),('MainSealCenterline',P['seal_centerline_size']),('MainGrooveWidth',P['groove_width']),('MainGrooveDepth',P['groove_depth']),('ActiveElectrodeWidth',P['electrode_width']),('ActiveElectrodeHeight',P['electrode_height']),('ManifoldDiameter',P['manifold_d']),('ManifoldSealMeanDiameter',P['manifold_seal_mean_d']),('ManifoldSealGrooveWidth',P['manifold_groove_width']),('ManifoldSealGrooveDepth',P['manifold_groove_depth']),('BranchDiameter',P['port_bore']),('AccessThreadMajor',4.0),('AccessThreadPitch',0.7),('AccessThreadCoreDiameter',3.3),('AccessThreadDepth',6.0),('AccessSpotfaceDiameter',6.0),('AccessSpotfaceDepth',0.2),('AccessWasherThickness',1.0)]:
    body.addProperty('App::PropertyLength',name,'Design');setattr(body,name,val)
body.addProperty('App::PropertyString','PortArchitecture','Design');body.PortArchitecture='Two axial D8 internal manifolds; no external fluid bosses or outlet ports'
body.addProperty('App::PropertyString','ManufacturingAccess','Design');body.ManufacturingAccess='Two M4x0.7 plugged cross-drill entries at y=+/-75; sealing washer required; not endplate interface'
body.addProperty('App::PropertyString','AccessThreadModel','Design');body.AccessThreadModel='M4x0.7 cosmetic callout; 3.3 mm minor-core bore, 6 mm engagement'
body.addProperty('App::PropertyString','FlowStatus','Design');body.FlowStatus='PROVISIONAL; flow behavior/distribution, actual electrode clearance, gap, chemistry and pressure validation pending; no CFD'
# Frame blank occupies z=0..gap to match the repeat-stack datum.
outer=C.sketch(body,'FrameBlankProfile',C.rounded(P['frame_size'],P['frame_size'],P['frame_corner']),C.at_z(0))
f=C.pad(body,'FrameBlank',outer,P['gap']);check_feature(f,'FrameBlank')
# Single wet window preserves the 56 mm electrode envelope; there are no headers.
f=add_pocket(body,'WetWindow',C.rounded(P['window'],P['window'],P['window_corner']),C.at_z(P['gap']),P['gap']);check_feature(f,'WetWindow')
# Small perimeter gasket groove on both mating faces, sized to the electrode coupon.
sg=P['seal_centerline_size'];gr=P['seal_corner'];gw=P['groove_width'];gd=P['groove_depth']
main_ring=C.rounded(sg+gw,sg+gw,gr+gw/2)+C.rounded(sg-gw,sg-gw,gr-gw/2)
f=add_pocket(body,'TopPerimeterSealGroove',main_ring,C.at_z(P['gap']),gd);check_feature(f,'TopPerimeterSealGroove')
f=add_pocket(body,'BottomPerimeterSealGroove',main_ring,C.at_z(0),gd,True);check_feature(f,'BottomPerimeterSealGroove')
# Two D8 axial through-manifolds, with independent annular seals on each face.
mp=[(float(x),float(y)) for x,y in P['manifold_points']]
f=add_pocket(body,'AxialManifolds',[C.circle(mx,my,P['manifold_d']/2) for mx,my in mp],C.at_z(P['gap']),P['gap']);check_feature(f,'AxialManifolds')
mr=[]
mean_r=P['manifold_seal_mean_d']/2
half_width=P['manifold_groove_width']/2
for mx,my in mp:
    mr.extend([C.circle(mx,my,mean_r+half_width),C.circle(mx,my,mean_r-half_width)])
f=add_pocket(body,'TopManifoldSealGrooves',mr,C.at_z(P['gap']),P['manifold_groove_depth']);check_feature(f,'TopManifoldSealGrooves')
f=add_pocket(body,'BottomManifoldSealGrooves',mr,C.at_z(0),P['manifold_groove_depth'],True);check_feature(f,'BottomManifoldSealGrooves')
# Dry clamp clearances and locator holes/slot remain outside the wet sealing geometry.
bg=[C.circle(bx,by,P['bolt_clearance']/2) for bx,by in P['bolt_points']]
f=add_pocket(body,'ClampClearances',bg,C.at_z(P['gap']),P['gap']);check_feature(f,'ClampClearances')
lx,ly=P['locator_points'][0];ld=P['locator_clearance']
f=add_pocket(body,'RoundLocator',[C.circle(lx,ly,ld/2)],C.at_z(P['gap']),P['gap']);check_feature(f,'RoundLocator')
lx,ly=P['locator_points'][1]
f=add_pocket(body,'LocatorSlot',C.rounded(ld,ld+1.0,ld/2-0.01,lx,ly),C.at_z(P['gap']),P['gap']);check_feature(f,'LocatorSlot')
# Buried branches connect each axial manifold directly to the 50 mm wet window.
branch_r=P['port_bore']/2
for side,upper in [('Upper',True),('Lower',False)]:
    y_entry=75.0 if upper else -75.0
    y_core_end=69.0 if upper else -69.0
    y_window=P['window']/2 if upper else -P['window']/2
    # A shallow washer spotface at the outside edge, followed by the M4 thread-minor pilot.
    f=add_pocket(body,side+'AccessSpotface',[C.circle(0,0,3.0)],axis_plane(y_entry,upper),0.2);check_feature(f,side+'AccessSpotface')
    f=add_pocket(body,side+'M4PlugCore',[C.circle(0,0,1.65)],axis_plane(y_entry,upper),6.0);check_feature(f,side+'M4PlugCore')
    # The blind feed bore passes through the matching axial manifold and opens into the window.
    f=add_pocket(body,side+'BuriedFeedBranch',[C.circle(0,0,branch_r)],axis_plane(y_core_end,upper),abs(y_core_end-y_window));check_feature(f,side+'BuriedFeedBranch')
rec=C.finish(doc,body,code,'PVDF provisional; chemistry and pressure rating pending')
rec.update({
 'configuration':'internal parallel inlet/outlet manifolds; no external bosses or fluid ports',
 'frame_envelope_mm':{'x':P['frame_size'],'y':P['frame_size'],'z':P['gap'],'z_origin':'0'},
 'gap_status':'6 mm provisional mechanical envelope only; actual gap awaits measured electrodes and flow requirements',
 'wet_geometry_mm':{'window':P['window'],'corner_radius':P['window_corner'],'headers':False},
 'electrode_envelope_mm':{'width':P['electrode_width'],'height':P['electrode_height'],'main_seal_outer_size':P['seal_centerline_size']+P['groove_width'],'main_seal_outer_corner_radius':P['seal_corner']+P['groove_width']/2,'active_foil_manifold_holes':False},
 'main_face_seal':{'centerline_size':P['seal_centerline_size'],'corner_radius':P['seal_corner'],'groove_width':P['groove_width'],'groove_depth_each_face':P['groove_depth'],'nominal_cs':P['seal_cs']},
 'axial_manifolds':{'centers_xy':mp,'diameter':P['manifold_d'],'through_z':True,'seal_grooves_each_face':2,'groove_mean_diameter':P['manifold_seal_mean_d'],'groove_width':P['manifold_groove_width'],'groove_depth':P['manifold_groove_depth'],'nominal_cs':P['manifold_seal_cs']},
 'buried_branches':{'diameter':P['port_bore'],'center_z':P['gap']/2,'upper_path':'y=+69 to +25, intersects manifold at (0,+62) and opens into window','lower_path':'y=-69 to -25, intersects manifold at (0,-62) and opens into window'},
 'plugged_manufacturing_access':{'count':2,'locations_xyz':[[0,75,3],[0,-75,3]],'thread':'M4x0.7','thread_minor_core_diameter':3.3,'engagement':6.0,'washer_spotface_diameter':6.0,'spotface_depth':0.2,'required_seal':'D6 x 1 mm sealing washer; thread and washer compatibility require qualification','functional_interface':False},
 'dry_features':{'bolt_clearance_diameter':P['bolt_clearance'],'bolt_points':P['bolt_points'],'locators':['round 3.2 mm at (-51,46)','3.2 x 4.2 mm slot at (51,-46)']},
 'native_feature_count':len(body.Group),
 'status':'PROVISIONAL - flow behavior/distribution and pressure testing TBD (no CFD); verify electrode/gap fit, chemistry, plug sealing and manufacturing access before release'
})
out={'revision':P['revision'],'units':'mm','active_part':rec,'superseded_legacy_files':[f'KF-{i:02d}.FCStd / KF-{i:02d}.step (front-boss configuration; exclude from current design)' for i in range(1,7)]}
(ROOT/'validation'/'flow_parts.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(rec,indent=2))
App.closeDocument(doc.Name)

