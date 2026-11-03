// Parametric monopolar, membrane-free Kolbe stack concept. Units: mm.
// XY is the plate plane; Z is the stack axis. Mechanical concept only.

// --------------------------- Main parameters ---------------------------
part = "assembly"; // assembly, exploded, one_frame, gasket, anode, cathode,
                   // endplate, insulator, three_layer, five_layer, seven_layer,
                   // flow_section, terminal_detail, tube_adapter, frame_profile, anode_profile,
                   // cathode_profile, endplate_profile, insulator_profile
electrode_count = 3; // odd: 3, 5, or 7; alternating C-A-C...
gap_mm = 4;
electrode_thickness_mm = 0.35;
frame_outer_mm = 120;
frame_corner_r_mm = 4;
active_window_mm = 50;
window_corner_r_mm = 3;
electrode_size_mm = 80;
ear_tip_x_mm = 80;
ear_width_mm = 10;
gasket_cs_mm = gap_mm/4;
gasket_compressed_ratio = 0.75;
gasket_width_ratio = 1.4;
gasket_centerline_mm = 60;
gasket_corner_r_mm = 6;
bolt_d_mm = 7; // clearance for nominal M6 tie rods
bolt_x_mm = 50;
bolt_y_mm = [45, 15];
port_d_mm = gap_mm / 4;
port_axis_z_mm = gap_mm / 2;
endplate_t_mm = 10;
insulator_t_mm = 4;
rod_d_mm = 6;
washer_od_mm = 12;
nut_af_mm = 10;
explode_step_mm = 5;
$fn = 64;

// ------------------------------- Derived -------------------------------
seal_w = gasket_cs_mm * gasket_width_ratio;
seal_h = gasket_cs_mm * gasket_compressed_ratio;
seal_sweep_w = gasket_cs_mm / gasket_compressed_ratio; // area-preserving compressed ellipse
window_r = window_corner_r_mm;
frame_t = gap_mm;
electrode_z_pitch = electrode_thickness_mm + gap_mm;
active_stack_t = electrode_count * electrode_thickness_mm + (electrode_count - 1) * gap_mm;
stack_t = active_stack_t + 2 * (endplate_t_mm + insulator_t_mm);
bolt_points = [for (x=[-bolt_x_mm, bolt_x_mm], y=[-bolt_y_mm[0],-bolt_y_mm[1],bolt_y_mm[1],bolt_y_mm[0]]) [x,y]];
// Eight points in four symmetric pairs, with no hole at the center terminal ears.

assert(electrode_count >= 3 && electrode_count % 2 == 1, "electrode_count must be odd and >= 3");
assert(gap_mm > 0 && electrode_thickness_mm > 0, "gap and electrode thickness must be positive");
assert(seal_w > 0 && seal_w < 2*gasket_centerline_mm, "gasket width must be positive and fit the loop");
assert(seal_sweep_w > 0 && seal_sweep_w <= seal_w, "compressed gasket section must fit within the groove width");
assert(gasket_centerline_mm > active_window_mm + seal_w, "seal loop must surround the active window");
assert(gasket_centerline_mm + seal_w < frame_outer_mm - 2*bolt_d_mm, "seal must clear the frame perimeter and bolt region");
assert(port_d_mm > 0 && port_axis_z_mm > port_d_mm/2 && port_axis_z_mm < frame_t-port_d_mm/2, "port must lie inside the frame thickness");
assert(port_axis_z_mm-port_d_mm/2-seal_h > 0 && frame_t-seal_h-port_axis_z_mm-port_d_mm/2 > 0, "side port bore must remain separated from both face seal grooves");
assert((gasket_centerline_mm-seal_w)/2 > active_window_mm/2, "seal loop must clear the window");
assert(gasket_corner_r_mm > seal_w/2, "rounded seal corner radius is too small");
assert(gasket_cs_mm > 0 && gasket_compressed_ratio > 0 && gasket_compressed_ratio <= 1, "invalid gasket compression");
assert(ear_tip_x_mm > frame_outer_mm/2 && electrode_size_mm > gasket_centerline_mm + seal_w, "terminal ear or electrode plate must extend beyond the seal loop");
assert(ear_tip_x_mm - frame_outer_mm/2 > 0, "electrode ear must clear the frame edge");
assert((gasket_centerline_mm/2 - seal_w/2) > active_window_mm/2 + port_d_mm/2, "side port bore must not break into the seal groove");
assert(bolt_x_mm + bolt_d_mm/2 < frame_outer_mm/2, "bolt holes exceed frame perimeter");
assert((bolt_x_mm - bolt_d_mm/2) > gasket_centerline_mm/2 + seal_w/2, "bolt holes intersect seal loop");
assert(min(bolt_y_mm) > ear_width_mm/2 + washer_od_mm/2, "bolt washers intersect the terminal ear corridor");
assert(electrode_size_mm/2 < bolt_x_mm-bolt_d_mm/2, "electrode body overlaps the bolt hole envelope");
assert(ear_width_mm > 0 && port_axis_z_mm >= 0, "invalid terminal or port geometry");

echo(str("electrodes=", electrode_count, " | each gap/frame=", gap_mm, " mm | active stack=", active_stack_t, " mm | total stack=", stack_t, " mm"));
echo(str("gasket: cs=", gasket_cs_mm, " mm, groove w=", seal_w, " mm, depth/face=", seal_h, " mm, compressed section height=", seal_h, " mm"));
echo(str("ports: bore=", port_d_mm, " mm, axis Z=", port_axis_z_mm, " mm; pressure rating TBD"));

// Rounded square helper: dimensions are the overall outside dimensions.
module rounded_square_2d(size, r) {
    offset(r=r) square([size-2*r, size-2*r], center=true);
}

module seal_loop_2d(width=seal_w) {
    difference() {
        rounded_square_2d(gasket_centerline_mm+width, gasket_corner_r_mm+width/2);
        rounded_square_2d(gasket_centerline_mm-width, gasket_corner_r_mm-width/2);
    }
}

function seal_arc(cx,cy,a0,a1,n=16) = [for (i=[0:n]) [cx+gasket_corner_r_mm*cos(a0+(a1-a0)*i/n),cy+gasket_corner_r_mm*sin(a0+(a1-a0)*i/n)]];
function seal_line(p1,p2,n=8) = [for (i=[0:n]) [p1[0]+(p2[0]-p1[0])*i/n,p1[1]+(p2[1]-p1[1])*i/n]];
function seal_path_points() = concat(
    seal_arc(gasket_centerline_mm/2-gasket_corner_r_mm,-gasket_centerline_mm/2+gasket_corner_r_mm,-90,0),
    seal_line([gasket_centerline_mm/2,-gasket_centerline_mm/2+gasket_corner_r_mm],[gasket_centerline_mm/2,gasket_centerline_mm/2-gasket_corner_r_mm]),
    seal_arc(gasket_centerline_mm/2-gasket_corner_r_mm,gasket_centerline_mm/2-gasket_corner_r_mm,0,90),
    seal_line([gasket_centerline_mm/2-gasket_corner_r_mm,gasket_centerline_mm/2],[-gasket_centerline_mm/2+gasket_corner_r_mm,gasket_centerline_mm/2]),
    seal_arc(-gasket_centerline_mm/2+gasket_corner_r_mm,gasket_centerline_mm/2-gasket_corner_r_mm,90,180),
    seal_line([-gasket_centerline_mm/2,gasket_centerline_mm/2-gasket_corner_r_mm],[-gasket_centerline_mm/2,-gasket_centerline_mm/2+gasket_corner_r_mm]),
    seal_arc(-gasket_centerline_mm/2+gasket_corner_r_mm,-gasket_centerline_mm/2+gasket_corner_r_mm,180,270),
    seal_line([-gasket_centerline_mm/2+gasket_corner_r_mm,-gasket_centerline_mm/2],[gasket_centerline_mm/2-gasket_corner_r_mm,-gasket_centerline_mm/2]));

module bolt_holes_2d(d=bolt_d_mm) {
    for (p=bolt_points) translate(p) circle(d=d);
}

module electrode_outline_2d(kind="A") {
    union() {
        rounded_square_2d(electrode_size_mm, 2);
        if (kind == "A") translate([electrode_size_mm/2,-ear_width_mm/2]) square([ear_tip_x_mm-electrode_size_mm/2,ear_width_mm], center=false);
        else translate([-ear_tip_x_mm, -ear_width_mm/2]) square([ear_tip_x_mm-electrode_size_mm/2,ear_width_mm], center=false);
    }
}

module electrode_2d(kind="A") {
    difference() {
        electrode_outline_2d(kind);
        // Clamp hole at the dry terminal tip; rod/washer are shown in detail view.
        translate([kind=="A" ? ear_tip_x_mm-5 : -ear_tip_x_mm+5,0]) circle(d=4.2);
    }
}

module frame_profile_2d() {
    difference() {
        rounded_square_2d(frame_outer_mm,frame_corner_r_mm);
        rounded_square_2d(active_window_mm,window_corner_r_mm);
        bolt_holes_2d();
    }
}

module frame_solid() {
    difference() {
        linear_extrude(height=frame_t) frame_profile_2d();
        // Two continuous seal grooves. The through-Y port remains in the mid-plane,
        // separated from both face grooves by solid material.
        translate([0,0,-0.01]) linear_extrude(height=seal_h+0.01) seal_loop_2d();
        translate([0,0,frame_t-seal_h]) linear_extrude(height=seal_h+0.01) seal_loop_2d();
        rotate([90,0,0]) translate([0,port_axis_z_mm,0]) cylinder(d=port_d_mm,h=frame_outer_mm+2,center=true);
    }
}

module gasket_solid(width=seal_sweep_w,height=seal_h) {
    // Sweep an ellipsoidal section around the rounded-square centerline.
    pts=seal_path_points();
    for (i=[0:len(pts)-1]) {
        j=(i+1)%len(pts);
        hull() {
            translate([pts[i][0],pts[i][1],height/2]) scale([width/2,width/2,height/2]) sphere(r=1,$fn=16);
            translate([pts[j][0],pts[j][1],height/2]) scale([width/2,width/2,height/2]) sphere(r=1,$fn=16);
        }
    }
}

module electrode_solid(kind="A") {
    linear_extrude(height=electrode_thickness_mm) electrode_2d(kind);
}

module endplate_2d() {
    difference() {
        rounded_square_2d(frame_outer_mm,frame_corner_r_mm);
        bolt_holes_2d(d=bolt_d_mm);
        // Open terminal notches clear the electrode ears and dry bus bars.
        for (s=[-1,1]) translate([s*75,0]) square([30,ear_width_mm+4],center=true);
    }
}

module insulator_2d() { endplate_2d(); }

module plate_with_washers(thickness, material="endplate") {
    if (material=="endplate") color([0.28,0.31,0.34]) linear_extrude(height=thickness) endplate_2d();
    else color([0.95,0.72,0.22,0.75]) linear_extrude(height=thickness) insulator_2d();
}

module one_frame() {
    color([0.76,0.80,0.84]) frame_solid();
}

module gasket_pair() {
    color([0.86,0.18,0.12]) gasket_solid();
    translate([0,0,frame_t-seal_h]) color([0.86,0.18,0.12]) gasket_solid();
}

module electrode_at(i, z) {
    kind = (i % 2 == 0) ? "C" : "A";
    translate([0,0,z]) color(kind=="A" ? [0.88,0.62,0.20] : [0.56,0.63,0.68]) electrode_solid(kind);
}

module rods_and_hardware(z0=0,z1=stack_t) {
    for (p=bolt_points) {
        translate([p[0],p[1],z0-6.2]) color([0.73,0.74,0.76]) cylinder(d=rod_d_mm,h=z1-z0+12.4);
        for (zz=[z0-1.2,z1]) {
            translate([p[0],p[1],zz]) color([0.75,0.75,0.77]) difference() {
                cylinder(d=washer_od_mm,h=1.2);
                translate([0,0,-0.1]) cylinder(d=rod_d_mm+0.5,h=1.4);
            }
            translate([p[0],p[1],zz+(zz<z0 ? -nut_af_mm/2 : 1.2)]) color([0.65,0.66,0.68]) difference() {
                cylinder(d=nut_af_mm*1.155,h=nut_af_mm/2,$fn=6);
                translate([0,0,-0.1]) cylinder(d=rod_d_mm+0.5,h=nut_af_mm/2+0.2);
            }
        }
    }
}

module external_buses(count=electrode_count, zbase=endplate_t_mm+insulator_t_mm) {
    // Dry-side copper bars. Branch straps touch only tabs of the same polarity.
    local_active=count*electrode_thickness_mm+(count-1)*gap_mm;
    for (s=[-1,1]) color([0.78,0.42,0.14]) translate([s*82,0,zbase+local_active/2])
        cube([3,6,local_active],center=true);
    for (i=[0:count-1]) {
        kind=(i%2==0)?"C":"A";
        z=zbase+i*electrode_z_pitch+electrode_thickness_mm/2;
        x=(kind=="A")?1:-1;
        color([0.82,0.48,0.17]) translate([x*71.5,0,z+electrode_thickness_mm/2+0.6]) cube([21,4,1.2],center=true);
        // Isolated clamp screw is conceptual and remains outside the wet window.
        color([0.27,0.28,0.30]) translate([x*(ear_tip_x_mm-5),0,z+electrode_thickness_mm/2+1.6]) cylinder(d=3.8,h=3,center=true);
    }
}

module tube_adapter() {
    // Removable slip-on concept; no thread form or fitting standard is implied.
    difference() {
        rotate([90,0,0]) cylinder(d=port_d_mm+0.4,h=20,center=true);
        rotate([90,0,0]) cylinder(d=port_d_mm,h=20.2,center=true);
    }
}

module channel_adapters(count=electrode_count,zbase=endplate_t_mm+insulator_t_mm) {
    for (i=[0:count-2], s=[-1,1]) {
        z=zbase+i*electrode_z_pitch+electrode_thickness_mm+gap_mm/2;
        translate([0,s*(frame_outer_mm/2+10),z]) color([0.25,0.48,0.62]) tube_adapter();
    }
}

module assembly(exploded=false, count=electrode_count) {
    local_active=count*electrode_thickness_mm+(count-1)*gap_mm;
    local_total=local_active+2*(endplate_t_mm+insulator_t_mm);
    offset_z=exploded ? explode_step_mm : 0;
    // bottom endplate and insulator
    color([0.28,0.31,0.34]) translate([0,0,0]) linear_extrude(height=endplate_t_mm) endplate_2d();
    color([0.95,0.72,0.22,0.75]) translate([0,0,endplate_t_mm+offset_z]) linear_extrude(height=insulator_t_mm) insulator_2d();
    for (i=[0:count-1]) {
        z=endplate_t_mm+insulator_t_mm+i*(electrode_thickness_mm+gap_mm)+(exploded ? (2*i+2)*offset_z : 0);
        electrode_at(i,z);
        if (i<count-1) {
            fz=z+electrode_thickness_mm+offset_z;
            translate([0,0,fz]) one_frame();
            translate([0,0,fz]) gasket_pair();
        }
    }
    topz=endplate_t_mm+insulator_t_mm+local_active;
    exploded_lift=exploded ? (2*(count-1)+3)*offset_z : 0;
    color([0.95,0.72,0.22,0.75]) translate([0,0,topz+exploded_lift]) linear_extrude(height=insulator_t_mm) insulator_2d();
    color([0.28,0.31,0.34]) translate([0,0,topz+insulator_t_mm+exploded_lift+offset_z]) linear_extrude(height=endplate_t_mm) endplate_2d();
    if (!exploded) {
        rods_and_hardware(0,local_total);
        external_buses(count,endplate_t_mm+insulator_t_mm);
        channel_adapters(count,endplate_t_mm+insulator_t_mm);
    } else {
        // Hardware omitted from exploded preview to keep separated interfaces visible.
        for (p=bolt_points) color([0.73,0.74,0.76]) translate([p[0],p[1],-12]) cylinder(d=rod_d_mm,h=local_total+exploded_lift+24);
    }
}

module section_view() {
    // One actual channel with both face seals and the through-side ports exposed.
    difference() {
        union() {
            color([0.76,0.80,0.84]) frame_solid();
            color([0.86,0.18,0.12]) gasket_solid();
            translate([0,0,frame_t-seal_h]) color([0.86,0.18,0.12]) gasket_solid();
            translate([0,0,-electrode_thickness_mm]) color([0.88,0.62,0.20]) electrode_solid("A");
            translate([0,0,frame_t]) color([0.56,0.63,0.68]) electrode_solid("C");
            // External adapter stubs: conceptual barbs only, no claimed thread standard.
            for (s=[-1,1]) translate([0,s*(frame_outer_mm/2+10),port_axis_z_mm]) color([0.25,0.48,0.62]) tube_adapter();
        }
        // Cut away half the frame to expose the internal through path and seal cross-section.
        translate([-frame_outer_mm,-frame_outer_mm,-10]) cube([frame_outer_mm,2*frame_outer_mm,frame_t+20]);
    }
}

module terminal_view() {
    color([0.56,0.63,0.68]) translate([0,0,0]) electrode_solid("C");
    color([0.88,0.62,0.20]) translate([0,0,electrode_z_pitch]) electrode_solid("A");
    // Insulating plate notch, dry-side busbar and clamp stack concept.
    color([0.95,0.72,0.22,0.6]) translate([0,0,-insulator_t_mm]) linear_extrude(height=insulator_t_mm) insulator_2d();
    color([0.78,0.42,0.14]) translate([-82,0,0]) cube([3,6,2*electrode_z_pitch],center=true);
    color([0.78,0.42,0.14]) translate([82,0,electrode_z_pitch]) cube([3,6,2*electrode_z_pitch],center=true);
    for (s=[-1,1]) translate([s*71.5,0,(s<0?0:electrode_z_pitch)+electrode_thickness_mm+0.6])
        color([0.78,0.42,0.14]) cube([21,4,1.2],center=true);
    for (x=[-1,1]) translate([x*75,0,x<0?0:electrode_z_pitch]) color([0.30,0.31,0.33]) cylinder(d=4.2,h=7,center=true);
    // Tie rod and terminal ear clearance envelope shown at the nearest dry hardware location.
    translate([-bolt_x_mm,bolt_y_mm[1],-3]) color([0.72,0.73,0.75]) cylinder(d=rod_d_mm,h=2*electrode_z_pitch+8);
}

module profile_view(name) {
    if (name=="frame_profile") frame_profile_2d();
    if (name=="anode_profile") electrode_2d("A");
    if (name=="cathode_profile") electrode_2d("C");
    if (name=="endplate_profile") endplate_2d();
    if (name=="insulator_profile") insulator_2d();
}

// -------------------------------- Views ---------------------------------
if (part=="assembly") assembly(false);
else if (part=="exploded") assembly(true);
else if (part=="three_layer") assembly(false,3);
else if (part=="five_layer") assembly(false,5);
else if (part=="seven_layer") assembly(false,7);
else if (part=="one_frame") one_frame();
else if (part=="gasket") color([0.86,0.18,0.12]) gasket_solid(gasket_cs_mm,gasket_cs_mm);
else if (part=="anode") color([0.88,0.62,0.20]) electrode_solid("A");
else if (part=="cathode") color([0.56,0.63,0.68]) electrode_solid("C");
else if (part=="endplate") plate_with_washers(endplate_t_mm,"endplate");
else if (part=="insulator") plate_with_washers(insulator_t_mm,"insulator");
else if (part=="flow_section") section_view();
else if (part=="terminal_detail") terminal_view();
else if (part=="tube_adapter") color([0.25,0.48,0.62]) tube_adapter();
else if (part=="frame_profile" || part=="anode_profile" || part=="cathode_profile" || part=="endplate_profile" || part=="insulator_profile") profile_view(part);
else assert(false, str("Unknown part/view: ",part));
