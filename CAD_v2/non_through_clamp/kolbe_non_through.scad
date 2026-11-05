// Kolbe non-through clamp. mm; plate XY, front -> rear +Z.
// Mechanical concept; physical pressure, chemistry and insulation unverified.
// Public parameters (PLAN.md section 2). All output coordinates derive here.
part = "assembly";
frame_count = 3;
electrode_count = 3;
seal_mode = "flat_gasket";
gasket_material = "EPDM";
electrode_material = "titanium";
explode_gap_mm = 14;
hardware_explode_stagger_mm = 2;
frame_w_mm = 74;
frame_h_mm = 82;
frame_t_mm = 4;
frame_corner_r_mm = 4;
endplate_w_mm = 112;
endplate_h_mm = 120;
endplate_t_mm = 20;
endplate_corner_r_mm = 6;
window_w_mm = 43;
window_h_mm = 63;
window_corner_r_mm = 3;
$fn = 96;
csg_eps_mm = 0.01;
gasket_w_mm = 66;
gasket_h_mm = 74;
gasket_corner_r_mm = 3;
gasket_t_mm = 0.8;
gasket_compression_ratio = gasket_material == "PTFE" ? 0.10 : 0.25;
gasket_pin_d_mm = 4.6;
gasket_slot_extra_mm = 0.6;
oring_cs_mm = 1.2;
oring_compression_ratio = 0.25;
oring_centerline_pad_mm = 2.5;
oring_groove_w_mm = 1.8;
oring_groove_d_mm = 0.3;
electrode_w_mm = 28;
electrode_h_mm = 28;
electrode_t_mm = 1;
electrode_corner_r_mm = 1.5;
electrode_flange_w_mm = 66;
electrode_flange_h_mm = 74;
electrode_flange_r_mm = 3;
electrode_bridge_w_mm = 4;
electrode_bridge_overlap_mm = 0.5;
electrode_pin_d_mm = 6.6;
tab_w_mm = 8;
tab_len_mm = 28;
tab_overlap_mm = 0.5;
tab_x_offsets_mm = [-14,14];
tab_offset_mm = -14;
tab_hole_d_mm = 3.2;
tab_hole_offset_mm = 6;
tab_channel_clearance_mm = 0.3;
tab_gasket_notch_depth_mm = 0.5;
nest_radial_clearance_mm = 0.25;
nest_lip_w_mm = 2;
nest_lip_h_mm = 1.2;
nest_rabbet_d_mm = 1.5;
nest_leadin_mm = 0.3;
nest_side_x_mm = 34.75;
nest_side_len_mm = 60;
nest_end_y_mm = 38.75;
nest_end_len_mm = 54;
nest_segment_r_mm = 0.5;
shoulder_inner_clearance_mm = 0.25;
min_structural_wall_mm = 1;
locator_points = [[-29,20],[29,-17]];
locator_d_mm = 4;
locator_press_d_mm = 3.96;
locator_press_depth_mm = 6;
locator_slip_d_mm = 4.4;
locator_slot_extra_mm = 0.6;
locator_rear_depth_mm = 6;
locator_rear_engagement_mm = 4.8;
locator_tip_chamfer_mm = 0.3;
bolt_points = [[46,50],[0,50],[-46,50],[-46,0],[-46,-50],[0,-50],[46,-50],[46,0]];
bolt_clear_d_mm = 6.6;
bolt_shank_d_mm = 6;
bolt_head_d_mm = 10;
bolt_head_h_mm = 6;
bolt_socket_af_mm = 5;
bolt_socket_depth_mm = 3;
bolt_head_chamfer_mm = 0.3;
bolt_tip_chamfer_mm = 0.5;
bolt_standard_lengths_mm = [40,45,50,55,60,65,70,75,80,85,90];
bolt_min_engagement_mm = 6;
bolt_max_rear_projection_mm = 3.5;
washer_od_mm = 12;
washer_id_mm = 6.4;
washer_t_mm = 1.6;
rear_fastener_mode = "heatset";
heatset_od_mm = 8;
heatset_depth_mm = 8;
heatset_bore_d_mm = 6.2;
heatset_pocket_d_mm = 8;
port_x_mm = 0;
port_y_mm = 27;
port_through_d_mm = 6;
port_counterbore_d_mm = 10.5;
port_counterbore_depth_mm = 3;
port_boss_od_mm = 14;
port_boss_h_mm = 8;
port_boss_flat_mm = 12;

// Derived: no second set of stack constants in Python.
gasket_count = 2*frame_count+1;
gasket_compressed_t = gasket_t_mm*(1-gasket_compression_ratio);
oring_compressed_h = oring_cs_mm*(1-oring_compression_ratio);
oring_compressed_w = oring_cs_mm*oring_cs_mm/oring_compressed_h;
seal_gap = seal_mode == "flat_gasket" ? gasket_compressed_t : oring_compressed_h-oring_groove_d_mm;
free_gap = seal_mode == "flat_gasket" ? gasket_t_mm : oring_cs_mm-oring_groove_d_mm;
front_stop_h = seal_gap;
frame_stop_h = 2*seal_gap+electrode_t_mm;
nest_axial_gap = nest_rabbet_d_mm-nest_lip_h_mm;
active_stack_t = frame_count*(frame_t_mm+electrode_t_mm)+gasket_count*seal_gap;
total_stack_t = 2*endplate_t_mm+active_stack_t;
free_total_stack_t = 2*endplate_t_mm+frame_count*(frame_t_mm+electrode_t_mm)+gasket_count*free_gap;
rear_z = endplate_t_mm+active_stack_t;
heatset_z = total_stack_t-heatset_depth_mm;
pin_z = endplate_t_mm-locator_press_depth_mm;
locator_len_mm = active_stack_t+locator_press_depth_mm+locator_rear_engagement_mm;
// 1e-9 only absorbs arithmetic roundoff at an exact standard-length boundary.
bolt_candidates = [for (l=bolt_standard_lengths_mm) if (min(heatset_depth_mm,l-washer_t_mm-heatset_z)+1e-9>=bolt_min_engagement_mm && max(0,l-washer_t_mm-total_stack_t)<=bolt_max_rear_projection_mm+1e-9) l];
bolt_length_mm = len(bolt_candidates)>0 ? min(bolt_candidates) : 0;
bolt_engagement_mm = min(heatset_depth_mm,bolt_length_mm-washer_t_mm-heatset_z);
bolt_rear_projection_mm = max(0,bolt_length_mm-washer_t_mm-total_stack_t);
bolt_tip_recess_mm = total_stack_t-(bolt_length_mm-washer_t_mm);
locator_rear_clearance_mm = locator_rear_depth_mm-locator_rear_engagement_mm;
seal_cl_w = window_w_mm+2*oring_centerline_pad_mm;
seal_cl_h = window_h_mm+2*oring_centerline_pad_mm;
seal_cl_r = window_corner_r_mm+oring_centerline_pad_mm;
tab_start_y = electrode_flange_h_mm/2-tab_overlap_mm;
tab_end_y = tab_start_y+tab_len_mm;
slot_angle = atan2(locator_points[1][1]-locator_points[0][1],locator_points[1][0]-locator_points[0][0]);
side_wall_mm = frame_w_mm/2-(nest_side_x_mm+nest_lip_w_mm/2+nest_radial_clearance_mm);
end_wall_mm = frame_h_mm/2-(nest_end_y_mm+nest_lip_w_mm/2+nest_radial_clearance_mm);
front_bbox_max_z = endplate_t_mm+front_stop_h+nest_lip_h_mm;
frame_bbox_h = frame_t_mm+frame_stop_h+nest_lip_h_mm;
seal_free_h = seal_mode == "flat_gasket" ? gasket_t_mm : oring_cs_mm;

// Assertions are active even for manifest-only exports.
assert(frame_count>=1 && frame_count<=6 && frame_count==floor(frame_count), "frame_count must be integer 1..6");
assert(electrode_count==frame_count, "electrode_count must equal frame_count");
assert(seal_mode=="flat_gasket" || seal_mode=="oring", "invalid seal_mode");
assert(gasket_material=="EPDM" || gasket_material=="FKM" || gasket_material=="PTFE", "invalid gasket_material");
assert(electrode_material=="titanium" || electrode_material=="platinum", "invalid electrode_material");
assert(!(gasket_material=="PTFE" && seal_mode=="oring"), "PTFE oring not supported");
assert(rear_fastener_mode=="heatset", "only heatset supported");
assert(len(bolt_points)==8 && len(locator_points)==2);
assert(seal_gap>0 && gasket_compression_ratio>=0 && gasket_compression_ratio<1);
assert(nest_axial_gap>0, "nest axial clearance must be positive");
assert(min(side_wall_mm,end_wall_mm)>=min_structural_wall_mm, "insufficient rabbet outer wall");
assert(min(side_wall_mm,end_wall_mm)-nest_leadin_mm>=0.7-0.000001);
assert(nest_leadin_mm>0 && nest_leadin_mm<nest_lip_h_mm && nest_leadin_mm<nest_rabbet_d_mm);
assert(2*oring_groove_d_mm<frame_t_mm && oring_compressed_w<oring_groove_w_mm);
assert(locator_rear_clearance_mm>0 && locator_press_depth_mm<endplate_t_mm);
assert(bolt_length_mm>0, "no standard bolt satisfies engagement and projection");
assert(heatset_depth_mm<endplate_t_mm && bolt_clear_d_mm>bolt_shank_d_mm);
for (b=bolt_points) {
    assert(norm([max(abs(b[0])-frame_w_mm/2,0),max(abs(b[1])-frame_h_mm/2,0)])-washer_od_mm/2>=2);
    assert(endplate_w_mm/2-abs(b[0])-washer_od_mm/2>=3 && endplate_h_mm/2-abs(b[1])-washer_od_mm/2>=3);
}
// Chunk checkpoint: geometry and dispatch are appended below.

// 2D helpers. Slot axis follows the line between the two dowels.
module rr(w,h,r) { offset(r=r) square([w-2*r,h-2*r],center=true); }
module window2d() { rr(window_w_mm,window_h_mm,window_corner_r_mm); }
module slot2d(d,extra) {
    rotate(slot_angle) hull() for (x=[-extra/2,extra/2]) translate([x,0]) circle(d=d);
}
module locator_holes2d(d,extra=0) {
    for (i=[0:1]) translate(locator_points[i]) if (i==0) circle(d=d); else slot2d(d,extra);
}
module tab_channels2d() {
    for (x=tab_x_offsets_mm) translate([x,tab_start_y+frame_h_mm/2])
        square([tab_w_mm+2*tab_channel_clearance_mm,frame_h_mm],center=true);
}
module shoulder2d() {
    difference() {
        rr(frame_w_mm,frame_h_mm,frame_corner_r_mm);
        rr(electrode_flange_w_mm+2*shoulder_inner_clearance_mm,
           electrode_flange_h_mm+2*shoulder_inner_clearance_mm,
           electrode_flange_r_mm+shoulder_inner_clearance_mm);
        tab_channels2d();
    }
}
module rails2d() {
    difference() {
        union() {
            for (x=[-nest_side_x_mm,nest_side_x_mm]) translate([x,0]) rr(nest_lip_w_mm,nest_side_len_mm,nest_segment_r_mm);
            for (y=[-nest_end_y_mm,nest_end_y_mm]) translate([0,y]) rr(nest_end_len_mm,nest_lip_w_mm,nest_segment_r_mm);
        }
        tab_channels2d();
    }
}
// Chamfer each connected rail individually; hulling the entire rail set
// would incorrectly bridge the window and create a disconnected cover sheet.
module rail_piece(i) {
    if (i<2) translate([(i==0 ? -1 : 1)*nest_side_x_mm,0]) rr(nest_lip_w_mm,nest_side_len_mm,nest_segment_r_mm);
    else if (i==2) translate([0,-nest_end_y_mm]) rr(nest_end_len_mm,nest_lip_w_mm,nest_segment_r_mm);
    else let(c=tab_w_mm/2+tab_channel_clearance_mm,
        ranges=[[-nest_end_len_mm/2,tab_x_offsets_mm[0]-c],
                [tab_x_offsets_mm[0]+c,tab_x_offsets_mm[1]-c],
                [tab_x_offsets_mm[1]+c,nest_end_len_mm/2]],r=ranges[i-3])
        intersection() {
            translate([0,nest_end_y_mm]) rr(nest_end_len_mm,nest_lip_w_mm,nest_segment_r_mm);
            translate([(r[0]+r[1])/2,nest_end_y_mm]) square([r[1]-r[0],nest_lip_w_mm+2],center=true);
        }
}
module lip() {
    for (i=[0:5]) {
        translate([0,0,-csg_eps_mm]) linear_extrude(nest_lip_h_mm-nest_leadin_mm+csg_eps_mm) rail_piece(i);
        translate([0,0,nest_lip_h_mm-nest_leadin_mm]) hull() {
            translate([0,0,-csg_eps_mm]) linear_extrude(csg_eps_mm) rail_piece(i);
            translate([0,0,nest_leadin_mm-csg_eps_mm]) linear_extrude(csg_eps_mm)
                offset(delta=-nest_leadin_mm) rail_piece(i);
        }
    }
}
module rabbet_cut() {
    for (i=[0:5]) {
        translate([0,0,-csg_eps_mm]) linear_extrude(nest_rabbet_d_mm+csg_eps_mm)
            offset(r=nest_radial_clearance_mm) rail_piece(i);
        translate([0,0,-csg_eps_mm]) hull() {
            linear_extrude(csg_eps_mm) offset(r=nest_radial_clearance_mm+nest_leadin_mm) rail_piece(i);
            translate([0,0,nest_leadin_mm]) linear_extrude(csg_eps_mm)
                offset(r=nest_radial_clearance_mm) rail_piece(i);
        }
    }
}
module shoulder_lip(z,h) {
    translate([0,0,z-csg_eps_mm]) linear_extrude(h+csg_eps_mm) shoulder2d();
    translate([0,0,z+h]) lip();
}
module seal_band2d(width) {
    difference() {
        rr(seal_cl_w+width,seal_cl_h+width,seal_cl_r+width/2);
        rr(seal_cl_w-width,seal_cl_h-width,seal_cl_r-width/2);
    }
}
module oring_groove(z) {
    translate([0,0,z]) linear_extrude(oring_groove_d_mm+csg_eps_mm) seal_band2d(oring_groove_w_mm);
}
module flat_gasket() {
    linear_extrude(gasket_t_mm) difference() {
        rr(gasket_w_mm,gasket_h_mm,gasket_corner_r_mm);
        window2d();
        locator_holes2d(gasket_pin_d_mm,gasket_slot_extra_mm);
        for (x=tab_x_offsets_mm) translate([x,gasket_h_mm/2])
            square([tab_w_mm+2*tab_channel_clearance_mm,2*tab_gasket_notch_depth_mm],center=true);
    }
}
module electrode(tab=true,x=tab_offset_mm) {
    linear_extrude(electrode_t_mm) difference() {
        union() {
            difference() { rr(electrode_flange_w_mm,electrode_flange_h_mm,electrode_flange_r_mm); window2d(); }
            rr(electrode_w_mm,electrode_h_mm,electrode_corner_r_mm);
            for (s=[-1,1]) translate([0,s*(electrode_h_mm/2+window_h_mm/2)/2])
                square([electrode_bridge_w_mm,(window_h_mm-electrode_h_mm)/2+2*electrode_bridge_overlap_mm],center=true);
            if (tab) translate([x,tab_start_y+tab_len_mm/2]) square([tab_w_mm,tab_len_mm],center=true);
        }
        locator_holes2d(electrode_pin_d_mm);
        if (tab) translate([x,tab_end_y-tab_hole_offset_mm]) circle(d=tab_hole_d_mm);
    }
}
// Explicit sweep: identical vertices/faces in both seal states, fixed centerline.
// The four corner arcs include their endpoints; connecting quads form straights.
ring_steps = $fn/4;
ring_path = [for (q=[0:3],j=[0:ring_steps]) let(a=q*90+j*90/ring_steps,
    cx=(q==0 || q==3 ? 1 : -1)*(seal_cl_w/2-seal_cl_r),
    cy=(q<2 ? 1 : -1)*(seal_cl_h/2-seal_cl_r))
    [cx+seal_cl_r*cos(a),cy+seal_cl_r*sin(a),cos(a),sin(a)]];
module gasket_oring(compressed=false) {
    h=compressed ? oring_compressed_h : oring_cs_mm;
    w=compressed ? oring_compressed_w : oring_cs_mm;
    n=len(ring_path); m=$fn;
    points=[for (p=ring_path,j=[0:m-1]) let(a=j*360/m)
        [p[0]+p[2]*w/2*cos(a),p[1]+p[3]*w/2*cos(a),h/2+h/2*sin(a)]];
    faces=[for (i=[0:n-1],j=[0:m-1]) each let(a=i*m+j,b=((i+1)%n)*m+j,
        c=((i+1)%n)*m+(j+1)%m,d=i*m+(j+1)%m) [[a,c,b],[a,d,c]]];
    polyhedron(points=points,faces=faces,convexity=10);
}
module frame() {
    difference() {
        union() {
            linear_extrude(frame_t_mm) difference() { rr(frame_w_mm,frame_h_mm,frame_corner_r_mm); window2d(); }
            shoulder_lip(frame_t_mm,frame_stop_h);
        }
        rabbet_cut();
        translate([0,0,-csg_eps_mm]) linear_extrude(frame_bbox_h+2*csg_eps_mm) locator_holes2d(locator_slip_d_mm,locator_slot_extra_mm);
        if (seal_mode=="oring") { oring_groove(-csg_eps_mm); oring_groove(frame_t_mm-oring_groove_d_mm); }
    }
}
module front_endplate() {
    difference() {
        union() {
            linear_extrude(endplate_t_mm) rr(endplate_w_mm,endplate_h_mm,endplate_corner_r_mm);
            shoulder_lip(endplate_t_mm,front_stop_h);
            // Outer wrench section plus a true cylindrical base, both united
            // with the plate. The counterbore starts at the exact outer end.
            for (s=[-1,1]) translate([port_x_mm,s*port_y_mm,-port_boss_h_mm]) {
                cylinder(d=port_boss_flat_mm/cos(30),h=port_boss_h_mm/2+csg_eps_mm,$fn=6);
                translate([0,0,port_boss_h_mm/2]) cylinder(d=port_boss_od_mm,h=port_boss_h_mm/2);
            }
        }
        for (p=bolt_points) translate([p[0],p[1],-csg_eps_mm]) cylinder(d=bolt_clear_d_mm,h=endplate_t_mm+2*csg_eps_mm);
        translate([0,0,pin_z]) linear_extrude(locator_press_depth_mm+csg_eps_mm) locator_holes2d(locator_press_d_mm);
        for (s=[-1,1]) {
            translate([port_x_mm,s*port_y_mm,-port_boss_h_mm-csg_eps_mm]) cylinder(d=port_through_d_mm,h=port_boss_h_mm+endplate_t_mm+2*csg_eps_mm);
            translate([port_x_mm,s*port_y_mm,-port_boss_h_mm-csg_eps_mm]) cylinder(d=port_counterbore_d_mm,h=port_counterbore_depth_mm+csg_eps_mm);
        }
    }
}
module rear_endplate() {
    difference() {
        linear_extrude(endplate_t_mm) rr(endplate_w_mm,endplate_h_mm,endplate_corner_r_mm);
        rabbet_cut();
        translate([0,0,-csg_eps_mm]) linear_extrude(locator_rear_depth_mm+csg_eps_mm) locator_holes2d(locator_slip_d_mm,locator_slot_extra_mm);
        for (p=bolt_points) {
            translate([p[0],p[1],-csg_eps_mm]) cylinder(d=bolt_clear_d_mm,h=endplate_t_mm+2*csg_eps_mm);
            translate([p[0],p[1],endplate_t_mm-heatset_depth_mm]) cylinder(d=heatset_pocket_d_mm,h=heatset_depth_mm+csg_eps_mm);
        }
        if (seal_mode=="oring") oring_groove(-csg_eps_mm);
    }
}
module locator_pin() {
    c=locator_tip_chamfer_mm;
    cylinder(d1=locator_d_mm-2*c,d2=locator_d_mm,h=c);
    translate([0,0,c]) cylinder(d=locator_d_mm,h=locator_len_mm-2*c);
    translate([0,0,locator_len_mm-c]) cylinder(d1=locator_d_mm,d2=locator_d_mm-2*c,h=c);
}
module bolt() {
    difference() {
        union() {
            translate([0,0,-bolt_head_h_mm]) cylinder(d1=bolt_head_d_mm-2*bolt_head_chamfer_mm,d2=bolt_head_d_mm,h=bolt_head_chamfer_mm);
            translate([0,0,-bolt_head_h_mm+bolt_head_chamfer_mm]) cylinder(d=bolt_head_d_mm,h=bolt_head_h_mm-bolt_head_chamfer_mm);
            cylinder(d=bolt_shank_d_mm,h=bolt_length_mm-bolt_tip_chamfer_mm);
            translate([0,0,bolt_length_mm-bolt_tip_chamfer_mm]) cylinder(d1=bolt_shank_d_mm,d2=bolt_shank_d_mm-2*bolt_tip_chamfer_mm,h=bolt_tip_chamfer_mm);
        }
        translate([0,0,-bolt_head_h_mm-csg_eps_mm]) cylinder(d=bolt_socket_af_mm/cos(30),h=bolt_socket_depth_mm+csg_eps_mm,$fn=6);
    }
}
module washer() { difference() { cylinder(d=washer_od_mm,h=washer_t_mm); translate([0,0,-csg_eps_mm]) cylinder(d=washer_id_mm,h=washer_t_mm+2*csg_eps_mm); } }
module heatset_nut() { difference() { cylinder(d=heatset_od_mm,h=heatset_depth_mm); translate([0,0,-csg_eps_mm]) cylinder(d=heatset_bore_d_mm,h=heatset_depth_mm+2*csg_eps_mm); } }

// Instance records. Fields are fixed and echoed as JSON-compatible arrays:
// id,part,translation,scale,exploded_translation,exploded_scale,zh,en,
// material,nominal_dims,assembled_dims,group,sequence_index,hardware_index.
function frame_z(i,t=seal_gap)=endplate_t_mm+t+i*(frame_t_mm+electrode_t_mm+2*t);
function electrode_z(i,t=seal_gap)=frame_z(i,t)+frame_t_mm+t;
function central_count()=4*frame_count+3;
function central_kind(s)=s==0 ? "front_endplate" : s==central_count()-1 ? "rear_endplate" :
    s==1 || (s-2)%4==1 || (s-2)%4==3 ? (seal_mode=="flat_gasket" ? "gasket" : "gasket_oring") :
    (s-2)%4==0 ? "frame" : "electrode_tab";
function seal_number(s)=s==1 ? 1 : (s-2)%4==1 ? 2*floor((s-2)/4)+2 : 2*floor((s-2)/4)+3;
function central_z(s,t=seal_gap)=s==0 ? 0 : s==central_count()-1 ? endplate_t_mm+frame_count*(frame_t_mm+electrode_t_mm)+(2*frame_count+1)*t :
    s==1 ? endplate_t_mm : let(i=floor((s-2)/4),k=(s-2)%4)
    k==0 ? frame_z(i,t) : k==1 ? frame_z(i,t)+frame_t_mm : k==2 ? electrode_z(i,t) : electrode_z(i,t)+electrode_t_mm;
function central_h(s)=s==0 ? front_bbox_max_z : s==central_count()-1 ? endplate_t_mm :
    central_kind(s)=="frame" ? frame_bbox_h : central_kind(s)=="electrode_tab" ? electrode_t_mm : seal_free_h;
function pin_exploded_z(i)=front_bbox_max_z+explode_gap_mm+i*(locator_len_mm+explode_gap_mm);
function central_exploded_z(s)=s==0 ? 0 : s==1 ? pin_exploded_z(1)+locator_len_mm+explode_gap_mm : central_exploded_z(s-1)+central_h(s-1)+explode_gap_mm;
function washer_exploded_z(i)=-port_boss_h_mm-explode_gap_mm-washer_t_mm-i*hardware_explode_stagger_mm;
function bolt_exploded_z(i)=washer_exploded_z(0)-explode_gap_mm-bolt_length_mm-i*hardware_explode_stagger_mm;
function heatset_exploded_z(i)=central_exploded_z(central_count()-1)+endplate_t_mm+explode_gap_mm+i*hardware_explode_stagger_mm;
function rec(id,k,pos,sc,ex,esc,zh,en,mat,nom,adim,grp,seq=-1,hw=-1)=[id,k,pos,sc,ex,esc,zh,en,mat,nom,adim,grp,seq,hw];
function central_record(s)=let(k=central_kind(s),i=floor((s-2)/4),
    is_seal=k=="gasket" || k=="gasket_oring",n=is_seal ? seal_number(s) : i+1,
    id=is_seal ? str("gasket_",n) : k=="frame" ? str("frame_",n) : k=="electrode_tab" ? str("electrode_",n) : k,
    kp=k=="electrode_tab" && tab_x_offsets_mm[i%len(tab_x_offsets_mm)]>0 ? "electrode_tab_right" : k,
    nom=k=="front_endplate" || k=="rear_endplate" ? [endplate_w_mm,endplate_h_mm,endplate_t_mm] :
        k=="frame" ? [frame_w_mm,frame_h_mm,frame_t_mm] : k=="electrode_tab" ? [electrode_flange_w_mm,tab_end_y+electrode_flange_h_mm/2,electrode_t_mm] :
        k=="gasket" ? [gasket_w_mm,gasket_h_mm,gasket_t_mm] : [seal_cl_w+oring_cs_mm,seal_cl_h+oring_cs_mm,oring_cs_mm],
    adim=is_seal ? (k=="gasket" ? [gasket_w_mm,gasket_h_mm,gasket_compressed_t] : [seal_cl_w+oring_compressed_w,seal_cl_h+oring_compressed_w,oring_compressed_h]) : nom,
    z=central_z(s)+(k=="gasket_oring" && n%2==0 ? -oring_groove_d_mm : 0),
    zh=is_seal ? str("密封件",n) : k=="frame" ? str("框",n) : k=="electrode_tab" ? str("电极",n) : k=="front_endplate" ? "前端板" : "后端板",
    en=is_seal ? str("Gasket ",n) : k=="frame" ? str("Frame ",n) : k=="electrode_tab" ? str("Electrode ",n) : k,
    mat=is_seal ? gasket_material : k=="electrode_tab" ? electrode_material : "polymer")
    rec(id,kp,[0,0,z],[1,1,k=="gasket" ? gasket_compressed_t/gasket_t_mm : 1],[0,0,central_exploded_z(s)],[1,1,1],zh,en,mat,nom,adim,"stack",s);
function instance_records()=concat(
    [for (s=[0:central_count()-1]) central_record(s)],
    [for (i=[0:7]) rec(str("bolt_",i+1),"bolt",concat(bolt_points[i],[-washer_t_mm]),[1,1,1],concat(bolt_points[i],[bolt_exploded_z(i)]),[1,1,1],str("螺栓",i+1),str("Bolt ",i+1),"steel",[bolt_shank_d_mm,bolt_length_mm,bolt_head_h_mm],[bolt_shank_d_mm,bolt_length_mm,bolt_head_h_mm],"bolts",-1,i)],
    [for (i=[0:7]) rec(str("washer_",i+1),"washer",concat(bolt_points[i],[-washer_t_mm]),[1,1,1],concat(bolt_points[i],[washer_exploded_z(i)]),[1,1,1],str("垫圈",i+1),str("Washer ",i+1),"steel",[washer_od_mm,washer_id_mm,washer_t_mm],[washer_od_mm,washer_id_mm,washer_t_mm],"washers",-1,i)],
    [for (i=[0:7]) rec(str("heatset_",i+1),"heatset_nut",concat(bolt_points[i],[heatset_z]),[1,1,1],concat(bolt_points[i],[heatset_exploded_z(i)]),[1,1,1],str("热熔螺母",i+1),str("Heatset ",i+1),"brass",[heatset_od_mm,heatset_depth_mm],[heatset_od_mm,heatset_depth_mm],"heatsets",-1,i)],
    [for (i=[0:1]) rec(str("locator_pin_",i+1),"locator_pin",concat(locator_points[i],[pin_z]),[1,1,1],concat(locator_points[i],[pin_exploded_z(i)]),[1,1,1],str("定位销",i+1),str("Locator pin ",i+1),"steel",[locator_d_mm,locator_len_mm],[locator_d_mm,locator_len_mm],"locators",-1,i)]);

module geometry(k,compressed=false) {
    if (k=="front_endplate") front_endplate();
    else if (k=="rear_endplate") rear_endplate();
    else if (k=="frame") frame();
    else if (k=="gasket") { if (seal_mode=="flat_gasket") flat_gasket(); else gasket_oring(compressed); }
    else if (k=="gasket_oring" || k=="gasket_oring_compressed") gasket_oring(compressed || k=="gasket_oring_compressed");
    else if (k=="electrode_tab") electrode();
    else if (k=="electrode_tab_right") electrode(true,abs(tab_x_offsets_mm[1]));
    else if (k=="electrode_plain") electrode(false);
    else if (k=="locator_pin") locator_pin();
    else if (k=="bolt") bolt();
    else if (k=="washer") washer();
    else if (k=="heatset_nut") heatset_nut();
    else if (k=="bolt_with_washer") { bolt(); washer(); }
}
module assembly(exploded=false) {
    for (r=instance_records()) {
        c=r[11]=="stack" ? (r[1]=="frame" ? [0.55,0.72,0.85] : r[8]=="polymer" ? [0.24,0.28,0.34] : r[1]=="gasket" || r[1]=="gasket_oring" ? [0.16,0.16,0.16] : [0.68,0.69,0.72]) : r[11]=="heatsets" ? [0.72,0.52,0.20] : [0.75,0.78,0.81];
        color(c) translate(exploded ? r[4] : r[2]) scale(exploded ? r[5] : r[3]) geometry(r[1],!exploded);
    }
}
// Manifest parameter and derived echo definitions are appended next.
if (part=="assembly" || part=="exploded") assembly(part=="exploded");
else if (part!="manifest") {
    assert(len([for (k=["front_endplate","rear_endplate","frame","gasket","gasket_oring","gasket_oring_compressed","electrode_tab","electrode_plain","locator_pin","bolt","washer","heatset_nut","bolt_with_washer"]) if (k==part) k])>0,"unknown part");
    geometry(part);
}

module manifest_echo() {
    echo(["KOLBE_V1","parameter",["part",part]]);
    echo(["KOLBE_V1","parameter",["frame_count",frame_count]]);
    echo(["KOLBE_V1","parameter",["electrode_count",electrode_count]]);
    echo(["KOLBE_V1","parameter",["seal_mode",seal_mode]]);
    echo(["KOLBE_V1","parameter",["gasket_material",gasket_material]]);
    echo(["KOLBE_V1","parameter",["electrode_material",electrode_material]]);
    echo(["KOLBE_V1","parameter",["explode_gap_mm",explode_gap_mm]]);
    echo(["KOLBE_V1","parameter",["hardware_explode_stagger_mm",hardware_explode_stagger_mm]]);
    echo(["KOLBE_V1","parameter",["frame_w_mm",frame_w_mm]]);
    echo(["KOLBE_V1","parameter",["frame_h_mm",frame_h_mm]]);
    echo(["KOLBE_V1","parameter",["frame_t_mm",frame_t_mm]]);
    echo(["KOLBE_V1","parameter",["frame_corner_r_mm",frame_corner_r_mm]]);
    echo(["KOLBE_V1","parameter",["endplate_w_mm",endplate_w_mm]]);
    echo(["KOLBE_V1","parameter",["endplate_h_mm",endplate_h_mm]]);
    echo(["KOLBE_V1","parameter",["endplate_t_mm",endplate_t_mm]]);
    echo(["KOLBE_V1","parameter",["endplate_corner_r_mm",endplate_corner_r_mm]]);
    echo(["KOLBE_V1","parameter",["window_w_mm",window_w_mm]]);
    echo(["KOLBE_V1","parameter",["window_h_mm",window_h_mm]]);
    echo(["KOLBE_V1","parameter",["window_corner_r_mm",window_corner_r_mm]]);
    echo(["KOLBE_V1","parameter",["$fn",$fn]]);
    echo(["KOLBE_V1","parameter",["csg_eps_mm",csg_eps_mm]]);
    echo(["KOLBE_V1","parameter",["gasket_w_mm",gasket_w_mm]]);
    echo(["KOLBE_V1","parameter",["gasket_h_mm",gasket_h_mm]]);
    echo(["KOLBE_V1","parameter",["gasket_corner_r_mm",gasket_corner_r_mm]]);
    echo(["KOLBE_V1","parameter",["gasket_t_mm",gasket_t_mm]]);
    echo(["KOLBE_V1","parameter",["gasket_compression_ratio",gasket_compression_ratio]]);
    echo(["KOLBE_V1","parameter",["gasket_pin_d_mm",gasket_pin_d_mm]]);
    echo(["KOLBE_V1","parameter",["gasket_slot_extra_mm",gasket_slot_extra_mm]]);
    echo(["KOLBE_V1","parameter",["oring_cs_mm",oring_cs_mm]]);
    echo(["KOLBE_V1","parameter",["oring_compression_ratio",oring_compression_ratio]]);
    echo(["KOLBE_V1","parameter",["oring_centerline_pad_mm",oring_centerline_pad_mm]]);
    echo(["KOLBE_V1","parameter",["oring_groove_w_mm",oring_groove_w_mm]]);
    echo(["KOLBE_V1","parameter",["oring_groove_d_mm",oring_groove_d_mm]]);
    echo(["KOLBE_V1","parameter",["electrode_w_mm",electrode_w_mm]]);
    echo(["KOLBE_V1","parameter",["electrode_h_mm",electrode_h_mm]]);
    echo(["KOLBE_V1","parameter",["electrode_t_mm",electrode_t_mm]]);
    echo(["KOLBE_V1","parameter",["electrode_corner_r_mm",electrode_corner_r_mm]]);
    echo(["KOLBE_V1","parameter",["electrode_flange_w_mm",electrode_flange_w_mm]]);
    echo(["KOLBE_V1","parameter",["electrode_flange_h_mm",electrode_flange_h_mm]]);
    echo(["KOLBE_V1","parameter",["electrode_flange_r_mm",electrode_flange_r_mm]]);
    echo(["KOLBE_V1","parameter",["electrode_bridge_w_mm",electrode_bridge_w_mm]]);
    echo(["KOLBE_V1","parameter",["electrode_bridge_overlap_mm",electrode_bridge_overlap_mm]]);
    echo(["KOLBE_V1","parameter",["electrode_pin_d_mm",electrode_pin_d_mm]]);
    echo(["KOLBE_V1","parameter",["tab_w_mm",tab_w_mm]]);
    echo(["KOLBE_V1","parameter",["tab_len_mm",tab_len_mm]]);
    echo(["KOLBE_V1","parameter",["tab_overlap_mm",tab_overlap_mm]]);
    echo(["KOLBE_V1","parameter",["tab_x_offsets_mm",tab_x_offsets_mm]]);
    echo(["KOLBE_V1","parameter",["tab_offset_mm",tab_offset_mm]]);
    echo(["KOLBE_V1","parameter",["tab_hole_d_mm",tab_hole_d_mm]]);
    echo(["KOLBE_V1","parameter",["tab_hole_offset_mm",tab_hole_offset_mm]]);
    echo(["KOLBE_V1","parameter",["tab_channel_clearance_mm",tab_channel_clearance_mm]]);
    echo(["KOLBE_V1","parameter",["tab_gasket_notch_depth_mm",tab_gasket_notch_depth_mm]]);
    echo(["KOLBE_V1","parameter",["nest_radial_clearance_mm",nest_radial_clearance_mm]]);
    echo(["KOLBE_V1","parameter",["nest_lip_w_mm",nest_lip_w_mm]]);
    echo(["KOLBE_V1","parameter",["nest_lip_h_mm",nest_lip_h_mm]]);
    echo(["KOLBE_V1","parameter",["nest_rabbet_d_mm",nest_rabbet_d_mm]]);
    echo(["KOLBE_V1","parameter",["nest_leadin_mm",nest_leadin_mm]]);
    echo(["KOLBE_V1","parameter",["nest_side_x_mm",nest_side_x_mm]]);
    echo(["KOLBE_V1","parameter",["nest_side_len_mm",nest_side_len_mm]]);
    echo(["KOLBE_V1","parameter",["nest_end_y_mm",nest_end_y_mm]]);
    echo(["KOLBE_V1","parameter",["nest_end_len_mm",nest_end_len_mm]]);
    echo(["KOLBE_V1","parameter",["nest_segment_r_mm",nest_segment_r_mm]]);
    echo(["KOLBE_V1","parameter",["shoulder_inner_clearance_mm",shoulder_inner_clearance_mm]]);
    echo(["KOLBE_V1","parameter",["min_structural_wall_mm",min_structural_wall_mm]]);
    echo(["KOLBE_V1","parameter",["locator_points",locator_points]]);
    echo(["KOLBE_V1","parameter",["locator_d_mm",locator_d_mm]]);
    echo(["KOLBE_V1","parameter",["locator_press_d_mm",locator_press_d_mm]]);
    echo(["KOLBE_V1","parameter",["locator_press_depth_mm",locator_press_depth_mm]]);
    echo(["KOLBE_V1","parameter",["locator_slip_d_mm",locator_slip_d_mm]]);
    echo(["KOLBE_V1","parameter",["locator_slot_extra_mm",locator_slot_extra_mm]]);
    echo(["KOLBE_V1","parameter",["locator_rear_depth_mm",locator_rear_depth_mm]]);
    echo(["KOLBE_V1","parameter",["locator_rear_engagement_mm",locator_rear_engagement_mm]]);
    echo(["KOLBE_V1","parameter",["locator_tip_chamfer_mm",locator_tip_chamfer_mm]]);
    echo(["KOLBE_V1","parameter",["bolt_points",bolt_points]]);
    echo(["KOLBE_V1","parameter",["bolt_clear_d_mm",bolt_clear_d_mm]]);
    echo(["KOLBE_V1","parameter",["bolt_shank_d_mm",bolt_shank_d_mm]]);
    echo(["KOLBE_V1","parameter",["bolt_head_d_mm",bolt_head_d_mm]]);
    echo(["KOLBE_V1","parameter",["bolt_head_h_mm",bolt_head_h_mm]]);
    echo(["KOLBE_V1","parameter",["bolt_socket_af_mm",bolt_socket_af_mm]]);
    echo(["KOLBE_V1","parameter",["bolt_socket_depth_mm",bolt_socket_depth_mm]]);
    echo(["KOLBE_V1","parameter",["bolt_head_chamfer_mm",bolt_head_chamfer_mm]]);
    echo(["KOLBE_V1","parameter",["bolt_tip_chamfer_mm",bolt_tip_chamfer_mm]]);
    echo(["KOLBE_V1","parameter",["bolt_standard_lengths_mm",bolt_standard_lengths_mm]]);
    echo(["KOLBE_V1","parameter",["bolt_min_engagement_mm",bolt_min_engagement_mm]]);
    echo(["KOLBE_V1","parameter",["bolt_max_rear_projection_mm",bolt_max_rear_projection_mm]]);
    echo(["KOLBE_V1","parameter",["washer_od_mm",washer_od_mm]]);
    echo(["KOLBE_V1","parameter",["washer_id_mm",washer_id_mm]]);
    echo(["KOLBE_V1","parameter",["washer_t_mm",washer_t_mm]]);
    echo(["KOLBE_V1","parameter",["rear_fastener_mode",rear_fastener_mode]]);
    echo(["KOLBE_V1","parameter",["heatset_od_mm",heatset_od_mm]]);
    echo(["KOLBE_V1","parameter",["heatset_depth_mm",heatset_depth_mm]]);
    echo(["KOLBE_V1","parameter",["heatset_bore_d_mm",heatset_bore_d_mm]]);
    echo(["KOLBE_V1","parameter",["heatset_pocket_d_mm",heatset_pocket_d_mm]]);
    echo(["KOLBE_V1","parameter",["port_x_mm",port_x_mm]]);
    echo(["KOLBE_V1","parameter",["port_y_mm",port_y_mm]]);
    echo(["KOLBE_V1","parameter",["port_through_d_mm",port_through_d_mm]]);
    echo(["KOLBE_V1","parameter",["port_counterbore_d_mm",port_counterbore_d_mm]]);
    echo(["KOLBE_V1","parameter",["port_counterbore_depth_mm",port_counterbore_depth_mm]]);
    echo(["KOLBE_V1","parameter",["port_boss_od_mm",port_boss_od_mm]]);
    echo(["KOLBE_V1","parameter",["port_boss_h_mm",port_boss_h_mm]]);
    echo(["KOLBE_V1","parameter",["port_boss_flat_mm",port_boss_flat_mm]]);
    echo(["KOLBE_V1","derived",["gasket_count",gasket_count]]);
    echo(["KOLBE_V1","derived",["gasket_compressed_t",gasket_compressed_t]]);
    echo(["KOLBE_V1","derived",["oring_compressed_h",oring_compressed_h]]);
    echo(["KOLBE_V1","derived",["oring_compressed_w",oring_compressed_w]]);
    echo(["KOLBE_V1","derived",["seal_gap",seal_gap]]);
    echo(["KOLBE_V1","derived",["free_gap",free_gap]]);
    echo(["KOLBE_V1","derived",["front_stop_h",front_stop_h]]);
    echo(["KOLBE_V1","derived",["frame_stop_h",frame_stop_h]]);
    echo(["KOLBE_V1","derived",["nest_axial_gap",nest_axial_gap]]);
    echo(["KOLBE_V1","derived",["active_stack_t",active_stack_t]]);
    echo(["KOLBE_V1","derived",["total_stack_t",total_stack_t]]);
    echo(["KOLBE_V1","derived",["free_total_stack_t",free_total_stack_t]]);
    echo(["KOLBE_V1","derived",["rear_z",rear_z]]);
    echo(["KOLBE_V1","derived",["heatset_z",heatset_z]]);
    echo(["KOLBE_V1","derived",["pin_z",pin_z]]);
    echo(["KOLBE_V1","derived",["locator_len_mm",locator_len_mm]]);
    echo(["KOLBE_V1","derived",["bolt_length_mm",bolt_length_mm]]);
    echo(["KOLBE_V1","derived",["bolt_engagement_mm",bolt_engagement_mm]]);
    echo(["KOLBE_V1","derived",["bolt_rear_projection_mm",bolt_rear_projection_mm]]);
    echo(["KOLBE_V1","derived",["bolt_tip_recess_mm",bolt_tip_recess_mm]]);
    echo(["KOLBE_V1","derived",["locator_rear_clearance_mm",locator_rear_clearance_mm]]);
    echo(["KOLBE_V1","derived",["seal_cl_w",seal_cl_w]]);
    echo(["KOLBE_V1","derived",["seal_cl_h",seal_cl_h]]);
    echo(["KOLBE_V1","derived",["seal_cl_r",seal_cl_r]]);
    echo(["KOLBE_V1","derived",["tab_start_y",tab_start_y]]);
    echo(["KOLBE_V1","derived",["tab_end_y",tab_end_y]]);
    echo(["KOLBE_V1","derived",["slot_angle",slot_angle]]);
    echo(["KOLBE_V1","derived",["side_wall_mm",side_wall_mm]]);
    echo(["KOLBE_V1","derived",["end_wall_mm",end_wall_mm]]);
    echo(["KOLBE_V1","derived",["front_bbox_max_z",front_bbox_max_z]]);
    echo(["KOLBE_V1","derived",["frame_bbox_h",frame_bbox_h]]);
    for (r=instance_records()) echo(["KOLBE_V1","instance",r]);
}
if (part=="manifest") manifest_echo();
