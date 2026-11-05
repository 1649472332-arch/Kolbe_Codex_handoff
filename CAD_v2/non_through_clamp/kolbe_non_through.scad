// =============================================================================
// Kolbe membrane-free filter-press cell — NON-THROUGH bolt clamp housing
// Units: mm.  XY = plate plane;  Z = stack axis (front → rear = +Z).
//
// vs through-rod stacks (kolbe_stack.scad / CAD_v2 B1 / version2):
//   * Only the two thick endplates carry clamp fasteners.
//   * Short M6 bolts enter from the FRONT outer face and screw into the REAR
//     endplate (heat-set insert pockets by default, or modeled tap drill).
//   * Intermediate flow frames / electrodes have NO bolt holes; bolt shafts
//     pass beside the frame outline between the oversized endplates.
//   * Primary registration = polarized tongue/groove nest on every frame face
//     and both endplate inner faces (print-friendly rectangular keys).
//   * Secondary = optional Ø3 locator pins.
//
// Mechanical concept only — pressure / seal / chemistry NOT validated.
// =============================================================================

// --------------------------- Part selector ----------------------------------
// assembly | exploded | front_endplate | rear_endplate | frame |
// electrode_tab | electrode_plain | locator_pin
part = "assembly";

// --------------------------- Stack composition ------------------------------
frame_count        = 3;
electrode_count    = 3;
use_tabbed_first   = true;
explode_gap_mm     = 14;

// --------------------------- Outer envelopes --------------------------------
frame_w_mm         = 74;
frame_h_mm         = 82;
frame_t_mm         = 4;
frame_corner_r_mm  = 4;

endplate_w_mm      = 96;
endplate_h_mm      = 106;
endplate_t_mm      = 20;
endplate_corner_r_mm = 6;

plate_style        = "rect";   // "rect" | "octagon"
octagon_chamfer_mm = 14;

// --------------------------- Active window / seal ---------------------------
window_w_mm        = 43;
window_h_mm        = 63;
window_corner_r_mm = 3;

seal_cs_mm         = 1.2;
seal_groove_w_mm   = 1.5;
seal_groove_d_mm   = 0.7;
seal_centerline_pad_mm = 2.0;

// --------------------------- Electrodes -------------------------------------
electrode_w_mm     = 28;
electrode_h_mm     = 28;
electrode_t_mm     = 1.0;
electrode_corner_r_mm = 1.5;
tab_w_mm           = 8;
tab_len_mm         = 22;
tab_hole_d_mm      = 3.2;
tab_hole_offset_mm = 6;

// --------------------------- Secondary locators (pins) ----------------------
locator_d_mm       = 3.0;
locator_clear_d_mm = 3.2;
locator_len_mm     = 10;
locator_points     = [[ 28,  35], [-28, -35]];
show_locator_pins  = true;

// --------------------------- Primary nest: tongue / groove ------------------
// Polarized stack registration (print-friendly rectangular keys on land):
//   * Each FRAME: groove pockets on -Z face, raised tongues on +Z face
//     (same XY centers). Frame N tongue seats into frame N+1 groove.
//   * FRONT endplate inner (+Z) face: raised tongues → first frame grooves.
//   * REAR  endplate inner (-Z / local z=0) face: groove pockets → last
//     frame tongues.
// Tongues are undersized vs grooves for FDM clearance.
nest_enable        = true;
nest_count         = 4;          // keys at mid-sides: +X -X +Y -Y
nest_tongue_w_mm   = 3.8;        // radial width of tongue (toward center)
nest_tongue_l_mm   = 11.0;       // length along perimeter
nest_tongue_h_mm   = 0.9;        // raised height
nest_groove_w_mm   = 4.2;        // groove slightly wider
nest_groove_l_mm   = 11.4;
nest_groove_d_mm   = 1.05;       // groove slightly deeper than tongue
nest_inset_mm      = 4.0;        // key center inset from outer edge toward center
nest_fillet_hint_mm = 0.6;       // used as corner radius on key rectangles
// Keep nest keys outside seal groove and inside outer edge.
nest_min_wall_mm   = 1.0;

// --------------------------- Clamp fasteners (endplates ONLY) ---------------
bolt_clear_d_mm    = 6.6;
bolt_points        = [
    [ 42,  47], [-42,  47],
    [ 42, -47], [-42, -47],
    [ 42,   0], [-42,   0]
];

// rear_fastener_mode: "heatset" (FDM recommended) | "tap" (machined only)
// heatset → counterbore Ø8 × 8 from outer face for M6 brass heat-set insert
// tap     → blind drill Ø5.0 × 13 (M6×1.0 tap drill model)
rear_fastener_mode = "heatset";
heatset_od_mm      = 8.0;
heatset_depth_mm   = 8.0;
tap_drill_d_mm     = 5.0;
tap_drill_depth_mm = 13.0;

bolt_shank_d_mm    = 6.0;
bolt_head_d_mm     = 10.0;
bolt_head_h_mm     = 6.0;
washer_od_mm       = 12.0;
washer_t_mm        = 1.5;

// --------------------------- Front fluid ports ------------------------------
port_y_mm          = 27;
port_x_mm          = 0;
port_through_d_mm  = 6.0;
port_counterbore_d_mm = 10.5;
port_counterbore_depth_mm = 3.0;
port_boss_od_mm    = 14.0;
port_boss_h_mm     = 8.0;
port_boss_flat_mm  = 12.0;

$fn = 48;

// --------------------------- Derived ----------------------------------------
seal_cl_w = window_w_mm + 2*seal_centerline_pad_mm;
seal_cl_h = window_h_mm + 2*seal_centerline_pad_mm;
seal_outer_w = seal_cl_w + seal_groove_w_mm;
seal_outer_h = seal_cl_h + seal_groove_w_mm;
seal_inner_w = seal_cl_w - seal_groove_w_mm;
seal_inner_h = seal_cl_h - seal_groove_w_mm;
seal_corner_r = window_corner_r_mm + seal_centerline_pad_mm;

// Frames seat land-to-land so tongue/groove nests engage. Electrodes live in the
// window cavities and do NOT add to peripheral stack height (1 mm << 4 mm chamber).
active_stack_t = frame_count * frame_t_mm;
total_stack_t  = 2*endplate_t_mm + active_stack_t;

frame_half_w = frame_w_mm/2;
frame_half_h = frame_h_mm/2;

// Nest key centers: mid-side, inset from frame outer edge
nest_cx = frame_half_w - nest_inset_mm;
nest_cy = frame_half_h - nest_inset_mm;
// 4 mid-side positions: +X, -X, +Y, -Y
nest_centers = [
    [ nest_cx, 0],
    [-nest_cx, 0],
    [0,  nest_cy],
    [0, -nest_cy]
];
// Rotation of each key so length runs along the perimeter
nest_rots = [90, 90, 0, 0];

// --------------------------- Asserts ----------------------------------------
assert(part == "assembly" || part == "exploded" || part == "front_endplate"
    || part == "rear_endplate" || part == "frame" || part == "electrode_tab"
    || part == "electrode_plain" || part == "locator_pin",
    "unknown part= value");
assert(frame_count >= 1 && electrode_count >= 1);
assert(frame_w_mm > window_w_mm + 2*seal_groove_w_mm + 8);
assert(frame_h_mm > window_h_mm + 2*seal_groove_w_mm + 8);
assert(endplate_w_mm > frame_w_mm);
assert(endplate_h_mm > frame_h_mm);
assert(endplate_t_mm >= 12);
assert(seal_groove_d_mm*2 < frame_t_mm);
assert(nest_groove_d_mm + seal_groove_d_mm < frame_t_mm - 0.5,
    "nest groove + seal groove leave too little core thickness");
assert(nest_tongue_h_mm <= nest_groove_d_mm,
    "tongue must be shorter/equal depth than groove");
assert(nest_tongue_w_mm < nest_groove_w_mm && nest_tongue_l_mm < nest_groove_l_mm,
    "tongue must be smaller than groove for clearance");
assert(nest_inset_mm > nest_groove_w_mm/2 + nest_min_wall_mm,
    "nest key too close to outer edge");
assert(rear_fastener_mode == "heatset" || rear_fastener_mode == "tap");
assert(heatset_depth_mm < endplate_t_mm - 2);
assert(tap_drill_depth_mm < endplate_t_mm - 2);
assert(len(bolt_points) == 6);
assert(len(locator_points) == 2);

for (p = bolt_points) {
    assert(abs(p[0]) > frame_half_w || abs(p[1]) > frame_half_h,
        str("bolt at ", p, " intersects frame — move outboard"));
    assert(abs(p[0]) + bolt_clear_d_mm/2 < endplate_w_mm/2 - 1);
    assert(abs(p[1]) + bolt_clear_d_mm/2 < endplate_h_mm/2 - 1);
}
for (p = locator_points) {
    assert(abs(p[0]) + locator_clear_d_mm/2 < frame_half_w - 2);
    assert(abs(p[1]) + locator_clear_d_mm/2 < frame_half_h - 2);
    // Outside window rectangle with ≥2 mm land (OR of axis clearances).
    assert(abs(p[0]) >= window_w_mm/2 + 2 || abs(p[1]) >= window_h_mm/2 + 2,
        str("locator ", p, " too close to / inside window"));
}
// Nest keys must sit outside seal outer and not hit window
for (p = nest_centers) {
    assert(abs(p[0]) + nest_groove_w_mm/2 < frame_half_w - nest_min_wall_mm
        || abs(p[1]) + nest_groove_w_mm/2 < frame_half_h - nest_min_wall_mm
        || true); // mid-side keys: check radial clearance below
}
assert(nest_cx - nest_groove_w_mm/2 > seal_outer_w/2 + nest_min_wall_mm
    || nest_cy - nest_groove_w_mm/2 > seal_outer_h/2 + nest_min_wall_mm,
    "nest keys collide with seal groove — increase nest_inset or shrink seal");
// Stronger: X-side keys clear seal in X; Y-side keys clear seal in Y
assert(nest_cx - nest_groove_w_mm/2 > seal_outer_w/2 + 0.3,
    "±X nest keys overlap seal land");
assert(nest_cy - nest_groove_w_mm/2 > seal_outer_h/2 + 0.3,
    "±Y nest keys overlap seal land");

echo(str("NON-THROUGH Kolbe: frames=", frame_count,
    " electrodes=", electrode_count,
    " active=", active_stack_t, " mm total=", total_stack_t, " mm",
    " rear=", rear_fastener_mode, " nest=", nest_enable));
echo(str("frame ", frame_w_mm, "x", frame_h_mm, "x", frame_t_mm,
    " | endplate ", endplate_w_mm, "x", endplate_h_mm, "x", endplate_t_mm,
    " | window ", window_w_mm, "x", window_h_mm));
echo("bolts OUTSIDE frame; frames have NO bolt holes; tongue/groove nest on all layers");

// --------------------------- 2D helpers -------------------------------------
module rounded_rect_2d(w, h, r) {
    rr = min(r, w/2 - 0.01, h/2 - 0.01);
    offset(r = rr) square([w - 2*rr, h - 2*rr], center = true);
}

module octagon_2d(w, h, chamfer) {
    c = min(chamfer, w/2 - 1, h/2 - 1);
    polygon([
        [ w/2 - c, -h/2 ], [ w/2, -h/2 + c ],
        [ w/2,  h/2 - c ], [ w/2 - c,  h/2 ],
        [-w/2 + c,  h/2 ], [-w/2,  h/2 - c ],
        [-w/2, -h/2 + c ], [-w/2 + c, -h/2 ]
    ]);
}

module plate_outline_2d(w, h, r, style = plate_style) {
    if (style == "octagon") octagon_2d(w, h, octagon_chamfer_mm);
    else rounded_rect_2d(w, h, r);
}

module seal_groove_2d() {
    difference() {
        rounded_rect_2d(seal_outer_w, seal_outer_h, seal_corner_r + seal_groove_w_mm/2);
        rounded_rect_2d(seal_inner_w, seal_inner_h, max(0.5, seal_corner_r - seal_groove_w_mm/2));
    }
}

module locator_holes_2d(d = locator_clear_d_mm) {
    for (p = locator_points) translate(p) circle(d = d);
}

module bolt_holes_2d(d = bolt_clear_d_mm) {
    for (p = bolt_points) translate(p) circle(d = d);
}

// Key rectangle in XY; length along local X before rotation
module nest_key_2d(len, wid, r = nest_fillet_hint_mm) {
    rounded_rect_2d(len, wid, min(r, len/2 - 0.05, wid/2 - 0.05));
}

module nest_tongues_solid(h = nest_tongue_h_mm) {
    if (nest_enable) {
        for (i = [0:len(nest_centers) - 1]) {
            translate([nest_centers[i][0], nest_centers[i][1], 0])
                rotate([0, 0, nest_rots[i]])
                    linear_extrude(height = h)
                        nest_key_2d(nest_tongue_l_mm, nest_tongue_w_mm);
        }
    }
}

module nest_grooves_cut(d = nest_groove_d_mm) {
    if (nest_enable) {
        for (i = [0:len(nest_centers) - 1]) {
            translate([nest_centers[i][0], nest_centers[i][1], 0])
                rotate([0, 0, nest_rots[i]])
                    translate([0, 0, -0.02])
                        linear_extrude(height = d + 0.04)
                            nest_key_2d(nest_groove_l_mm, nest_groove_w_mm);
        }
    }
}

// --------------------------- Solid parts ------------------------------------
module frame_solid() {
    // NO bolt holes. -Z face = grooves; +Z face = tongues.
    difference() {
        union() {
            linear_extrude(height = frame_t_mm)
                difference() {
                    rounded_rect_2d(frame_w_mm, frame_h_mm, frame_corner_r_mm);
                    rounded_rect_2d(window_w_mm, window_h_mm, window_corner_r_mm);
                    locator_holes_2d();
                }
            // Tongues overlap 0.2 mm into +Z face for a single CGAL volume
            translate([0, 0, frame_t_mm - 0.2])
                nest_tongues_solid(nest_tongue_h_mm + 0.2);
        }
        // Dual-face seal grooves
        translate([0, 0, -0.01])
            linear_extrude(height = seal_groove_d_mm + 0.01) seal_groove_2d();
        translate([0, 0, frame_t_mm - seal_groove_d_mm])
            linear_extrude(height = seal_groove_d_mm + 0.01) seal_groove_2d();
        // Nest grooves on -Z face
        nest_grooves_cut(nest_groove_d_mm);
    }
}

module electrode_solid(with_tab = true) {
    linear_extrude(height = electrode_t_mm)
        difference() {
            union() {
                rounded_rect_2d(electrode_w_mm, electrode_h_mm, electrode_corner_r_mm);
                if (with_tab)
                    translate([-tab_w_mm/2, electrode_h_mm/2 - 0.5])
                        square([tab_w_mm, tab_len_mm + 0.5], center = false);
            }
            if (with_tab)
                translate([0, electrode_h_mm/2 + tab_len_mm - tab_hole_offset_mm])
                    circle(d = tab_hole_d_mm);
        }
}

module locator_pin_solid() {
    cylinder(d = locator_d_mm, h = locator_len_mm);
}

module front_port_boss() {
    difference() {
        union() {
            cylinder(d = port_boss_od_mm, h = port_boss_h_mm);
            translate([0, 0, port_boss_h_mm*0.35])
                cylinder(d = port_boss_flat_mm * 1.1547, h = port_boss_h_mm*0.4, $fn = 6);
        }
        translate([0, 0, -0.1])
            cylinder(d = port_through_d_mm, h = port_boss_h_mm + 0.2);
    }
}

module front_endplate_solid() {
    // Outer face near z=0 (bosses toward -Z); inner face at z=endplate_t_mm.
    // Inner face carries NEST TONGUES that engage the first frame's grooves.
    // Tongues are unioned into the plate before hole cuts so CGAL stays one volume.
    difference() {
        union() {
            linear_extrude(height = endplate_t_mm)
                plate_outline_2d(endplate_w_mm, endplate_h_mm, endplate_corner_r_mm);
            // Tongues on inner face (overlap 0.2 mm into plate for robust union)
            translate([0, 0, endplate_t_mm - 0.2])
                nest_tongues_solid(nest_tongue_h_mm + 0.2);
            // Overlap bosses 0.3 mm into plate so union is watertight
            for (sy = [-1, 1])
                translate([port_x_mm, sy*port_y_mm, 0.3])
                    rotate([180, 0, 0]) front_port_boss();
        }
        // Through features
        translate([0, 0, -0.1])
            linear_extrude(height = endplate_t_mm + 0.2) {
                bolt_holes_2d(bolt_clear_d_mm);
                locator_holes_2d();
                for (sy = [-1, 1])
                    translate([port_x_mm, sy*port_y_mm])
                        circle(d = port_through_d_mm);
            }
        for (sy = [-1, 1])
            translate([port_x_mm, sy*port_y_mm, -port_counterbore_depth_mm])
                cylinder(d = port_counterbore_d_mm, h = port_counterbore_depth_mm + 0.05);
    }
}

module rear_endplate_solid() {
    // Local: inner face at z=0 (toward stack), outer at z=endplate_t_mm.
    // Inner face has NEST GROOVES to accept the last frame's tongues.
    // Outer face has heatset/tap pockets for M6.
    difference() {
        linear_extrude(height = endplate_t_mm)
            plate_outline_2d(endplate_w_mm, endplate_h_mm, endplate_corner_r_mm);
        // Locator through-holes
        translate([0, 0, -0.1])
            linear_extrude(height = endplate_t_mm + 0.2)
                locator_holes_2d();
        // Nest grooves on inner face
        nest_grooves_cut(nest_groove_d_mm);
        // Blind fastener features from OUTER face
        for (p = bolt_points) {
            if (rear_fastener_mode == "heatset") {
                // FDM: M6 brass heat-set insert Ø8 × 8. Do not rely on printed threads.
                translate([p[0], p[1], endplate_t_mm - heatset_depth_mm])
                    cylinder(d = heatset_od_mm, h = heatset_depth_mm + 0.05);
            } else {
                // Machined POM/PEEK/metal only: M6 tap drill Ø5.0 × 13.
                translate([p[0], p[1], endplate_t_mm - tap_drill_depth_mm])
                    cylinder(d = tap_drill_d_mm, h = tap_drill_depth_mm + 0.05);
            }
        }
    }
}

module bolt_visual(shank_len) {
    color([0.72, 0.73, 0.75]) {
        translate([0, 0, -washer_t_mm])
            difference() {
                cylinder(d = washer_od_mm, h = washer_t_mm);
                translate([0, 0, -0.1]) cylinder(d = bolt_shank_d_mm + 0.4, h = washer_t_mm + 0.2);
            }
        translate([0, 0, -washer_t_mm - bolt_head_h_mm])
            cylinder(d = bolt_head_d_mm, h = bolt_head_h_mm, $fn = 6);
        cylinder(d = bolt_shank_d_mm, h = shank_len);
    }
}

// --------------------------- Assembly ---------------------------------------
// Interleave: electrode, frame, electrode, frame, ... then leftover electrodes.
// Z pitch accounts for nest tongue sticking into the next part's groove, so
// mating solid faces still meet: tongue height is absorbed by groove depth.
// Electrodes sit in the window and do not change peripheral land contact;
// for simplicity we still stack thicknesses additively (conservative gap).

module place_one_electrode(idx, z) {
    with_tab = (idx % 2 == 0) ? use_tabbed_first : !use_tabbed_first;
    tab_shift = (idx - (electrode_count - 1)/2) * (tab_w_mm + 2);
    translate([tab_shift, 0, z])
        color(with_tab ? [0.90, 0.70, 0.25] : [0.62, 0.68, 0.72])
            electrode_solid(with_tab = with_tab);
}

module place_one_frame(z) {
    translate([0, 0, z])
        color([0.18, 0.18, 0.20])
            frame_solid();
}

module place_stack_layers(z0, gap = 0) {
    // Frames only set axial pitch (land-to-land). Electrodes are centered in
    // each frame window so nest tongues still reach the next groove.
    n_f = frame_count;
    n_e = electrode_count;
    for (i = [0:n_f - 1]) {
        zf = z0 + i * (frame_t_mm + gap);
        place_one_frame(zf);
        if (i < n_e) {
            // Center electrode in this frame's cavity
            ze = zf + (frame_t_mm - electrode_t_mm) / 2;
            place_one_electrode(i, ze);
        }
    }
    // Extra electrodes beyond frame_count: park after last frame (visual only)
    if (n_e > n_f) {
        for (i = [n_f:n_e - 1]) {
            ze = z0 + n_f * (frame_t_mm + gap) + (i - n_f) * (electrode_t_mm + gap);
            place_one_electrode(i, ze);
        }
    }
}

module locator_pins_in_stack(z_mid) {
    if (show_locator_pins) {
        for (p = locator_points)
            translate([p[0], p[1], z_mid - locator_len_mm/2])
                color([0.55, 0.55, 0.58]) locator_pin_solid();
    }
}

module bolts_in_assembly(z_front_outer, z_rear_outer) {
    engage = (rear_fastener_mode == "heatset") ? heatset_depth_mm*0.85
                                               : tap_drill_depth_mm*0.85;
    shank = (z_rear_outer - z_front_outer) + engage;
    for (p = bolt_points)
        translate([p[0], p[1], z_front_outer])
            bolt_visual(shank);
}

module assembly_view(exploded = false) {
    gap = exploded ? explode_gap_mm : 0;
    color([0.12, 0.12, 0.14]) front_endplate_solid();

    z_stack0 = endplate_t_mm + gap;
    // Explode gaps between frames (+ optional trailing gap before rear plate)
    active_draw_t = active_stack_t + (frame_count - 1)*gap;

    place_stack_layers(z_stack0, gap);

    z_rear_inner = z_stack0 + active_draw_t + gap;
    translate([0, 0, z_rear_inner])
        color([0.12, 0.12, 0.14]) rear_endplate_solid();

    locator_pins_in_stack(z_stack0 + (exploded ? active_draw_t : active_stack_t)/2);
    bolts_in_assembly(0, z_rear_inner + endplate_t_mm);
}

// --------------------------- Part dispatch ----------------------------------
if (part == "front_endplate") {
    front_endplate_solid();
} else if (part == "rear_endplate") {
    rear_endplate_solid();
} else if (part == "frame") {
    frame_solid();
} else if (part == "electrode_tab") {
    electrode_solid(true);
} else if (part == "electrode_plain") {
    electrode_solid(false);
} else if (part == "locator_pin") {
    locator_pin_solid();
} else if (part == "exploded") {
    assembly_view(true);
} else {
    assembly_view(false);
}
