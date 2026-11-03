"""Generate editable FreeCAD mechanical part documents for the Kolbe stack.

Run with FreeCAD's bundled Python. Parts are built from native Body, Sketch,
Pad and Pocket features; STEP files are neutral exports of each final body.
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import cad_common as C
import FreeCAD as App
import Part
import Sketcher

P = C.P
V = C.V
OUT = ROOT / 'parts'
OUT.mkdir(exist_ok=True)


def body_doc(code, label):
    name = code.replace('-', '_')
    try:
        App.closeDocument(name)
    except Exception:
        pass
    d = App.newDocument(name)
    b = C.body_new(d, 'Body', label)
    return d, b


def round_slot(cx, cy, width, length):
    """Closed horizontal slot, overall length along X."""
    r = width / 2.0
    straight = length / 2.0 - r
    return [
        Part.LineSegment(V(cx - straight, cy - r, 0), V(cx + straight, cy - r, 0)),
        Part.ArcOfCircle(Part.Circle(V(cx + straight, cy, 0), V(0, 0, 1), r), -math.pi/2, math.pi/2),
        Part.LineSegment(V(cx + straight, cy + r, 0), V(cx - straight, cy + r, 0)),
        Part.ArcOfCircle(Part.Circle(V(cx - straight, cy, 0), V(0, 0, 1), r), math.pi/2, 3*math.pi/2),
    ]


def hole_sketch(body, name, circles, z, extras=None):
    geos = [C.circle(x, y, d/2) for x, y, d in circles]
    if extras:
        geos.extend(extras)
    return C.sketch(body, name, geos, C.at_z(z))


def make_electrode(code, label, material, color, tab_side):
    d, b = body_doc(code, label)
    width = P['electrode_width']
    height = P['electrode_height']
    thickness = P['electrode_thickness']
    base = C.sketch(b, 'ElectrodeCouponOutline', C.rounded(width, height, 2))
    f = C.pad(b, 'ElectrodeFoil', base, thickness)
    if tab_side == 'A+x':
        tab_profile = C.rect(24, -8, 100, 8)
        tab_hole_x = 90
    else:
        tab_profile = C.rect(-100, -8, -24, 8)
        tab_hole_x = -90
    tabs = C.sketch(b, 'IntegralTabOutline', tab_profile)
    f = C.pad(b, 'IntegralTab', tabs, thickness)
    hs = hole_sketch(b, 'TerminalHole', [(tab_hole_x, 0, 4.5)], thickness)
    f = C.pocket(b, 'PiercedHoles', hs, thickness)
    b.addProperty('App::PropertyString', 'TerminalTabSide', 'Design')
    b.TerminalTabSide = tab_side
    return C.finish(d, b, code, material, color)


def make_carrier(code, label, tab_side):
    d, b = body_doc(code, label)
    t = P['carrier_thickness']
    outer = P['carrier_size']
    sk = C.sketch(b, 'CarrierOutline', C.rounded(outer, outer, 5))
    f = C.pad(b, 'CarrierFilm', sk, t)
    aperture = P['electrode_width'] + P['carrier_clearance']
    window = C.sketch(b, 'CouponWindow', C.rounded(aperture, aperture, 2.05), C.at_z(t))
    f = C.pocket(b, 'CouponWindowCut', window, t)
    slot_width = P['tab_width'] + P['carrier_clearance']
    halfslot = slot_width / 2
    if tab_side == 'A+x':
        slot_profile = C.rect(aperture/2-1, -halfslot, outer/2+1, halfslot)
        terminal = 'A-side opening toward +X'
    else:
        slot_profile = C.rect(-outer/2-1, -halfslot, -aperture/2+1, halfslot)
        terminal = 'C-side opening toward -X'
    # Separate pocket keeps the carrier window and open tab slot as simple profiles.
    slot = C.sketch(b, 'TerminalSlot', slot_profile, C.at_z(t))
    f = C.pocket(b, 'TerminalSlotCut', slot, t)
    bolts = [(x, y, 9) for x, y in P['bolt_points']]
    bh = hole_sketch(b, 'ThroughFastenerPattern', bolts, t)
    f = C.pocket(b, 'ThroughFastenerClearance', bh, t)
    loc = [(x, y, 3.2) for x, y in P['locator_points']]
    lh = hole_sketch(b, 'ThroughLocatorPattern', loc, t)
    f = C.pocket(b, 'ThroughLocatorHoles', lh, t)
    manifolds = port_holes(P['manifold_points'], P['manifold_d'])
    mh = hole_sketch(b, 'ManifoldBores', manifolds, t)
    f = C.pocket(b, 'ManifoldThroughBores', mh, t)
    b.addProperty('App::PropertyString', 'TerminalSlotSide', 'Design')
    b.TerminalSlotSide = terminal
    b.addProperty('App::PropertyString', 'ThicknessToleranceStatus', 'Specification')
    b.ThicknessToleranceStatus = '0.35 ±0.01 mm provisional; confirm with precision-film supplier'
    b.addProperty('App::PropertyString', 'SupplierStatus', 'Specification')
    b.SupplierStatus = 'Precision PEEK film supplier and grade TBD'
    return C.finish(d, b, code, 'PEEK precision film; supplier and grade TBD', (.08, .08, .09))


def make_plate(code, label, material, thickness, color, locator_depth, tool_access=False):
    d, b = body_doc(code, label)
    sk = C.sketch(b, 'PlateOutline', C.rounded(150, 150, 5))
    f = C.pad(b, 'PlateBlank', sk, thickness)
    points = P['bolt_points']
    bolts = [(x, y, 9.0) for x, y in points]
    hs = hole_sketch(b, 'ThroughFastenerPattern', bolts, thickness)
    f = C.pocket(b, 'ThroughFastenerClearance', hs, thickness)
    if tool_access:
        access = [(x, y, 12) for x, y in P['manifold_points']]
        ps = hole_sketch(b, 'ManifoldToolAccess', access, thickness)
        f = C.pocket(b, 'ToolAccessThroughHoles', ps, thickness)
    loc = [(x, y, 3.2) for x, y in P['locator_points']]
    inner_z = 0 if code == 'KP-204' else thickness
    ls = hole_sketch(b, 'InnerFaceLocatorHoles', loc, inner_z)
    f = C.pocket(b, 'LocatorHoles', ls, locator_depth, reversed=(code == 'KP-204'))
    return C.finish(d, b, code, material, color)


def ring_geometries(points, mean_d, width):
    ri = mean_d/2-width/2
    ro = mean_d/2+width/2
    gs = []
    for x, y in points:
        gs.extend([C.circle(x, y, ro), C.circle(x, y, ri)])
    return gs


def port_holes(points, diameter):
    return [(x, y, diameter) for x, y in points]


def make_front_insulator():
    code = 'KP-202'
    d, b = body_doc(code, 'Front manifold insulator')
    t = P['front_insulator_t']
    sk = C.sketch(b, 'InsulatorOutline', C.rounded(150, 150, 5))
    f = C.pad(b, 'InsulatorBlank', sk, t)
    bolts = [(x, y, 9) for x, y in P['bolt_points']]
    hs = hole_sketch(b, 'ThroughFastenerPattern', bolts, t)
    f = C.pocket(b, 'ThroughFastenerClearance', hs, t)
    loc = [(x, y, 3.2) for x, y in P['locator_points']]
    ls = hole_sketch(b, 'ThroughLocatorPattern', loc, t)
    f = C.pocket(b, 'ThroughLocatorHoles', ls, t)
    manifold = P['manifold_points']
    ms = hole_sketch(b, 'ManifoldBores', port_holes(manifold, 8), t)
    f = C.pocket(b, 'ManifoldThroughBores', ms, 3)
    pilot = hole_sketch(b, 'PortPilotBores', port_holes(manifold, 2.2), 11)
    f = C.pocket(b, 'PortPilotDepth', pilot, 1)
    seat = hole_sketch(b, 'FerruleSeats', port_holes(manifold, 3.4), 10)
    f = C.pocket(b, 'FerruleSeatDepth', seat, 2)
    # A smooth Ø6 clearance envelope occupies the nominal M6x1 receiving zone.
    # The thread is documented as metadata; no helical thread is implied.
    thread = hole_sketch(b, 'ConnectorThreadClearance', port_holes(manifold, 6), 8)
    f = C.pocket(b, 'ConnectorClearanceDepth', thread, 8)
    rings = C.sketch(b, 'InnerManifoldSealGrooves', ring_geometries(manifold, P['manifold_seal_mean_d'], P['manifold_groove_width']), C.at_z(t))
    f = C.pocket(b, 'SealGrooveDepth', rings, P['manifold_groove_depth'])
    b.addProperty('App::PropertyLength', 'PortThreadMajorDiameter', 'Port specification')
    b.PortThreadMajorDiameter = 6
    b.addProperty('App::PropertyLength', 'PortThreadMinorDiameter', 'Port specification')
    b.PortThreadMinorDiameter = 5
    b.addProperty('App::PropertyLength', 'PortThreadPitch', 'Port specification')
    b.PortThreadPitch = 1
    b.addProperty('App::PropertyLength', 'PortThreadLength', 'Port specification')
    b.PortThreadLength = 8
    b.addProperty('App::PropertyString', 'PortThreadGeometry', 'Port specification')
    b.PortThreadGeometry = 'M6x1 nominal designation; actual feature is smooth Ø6 clearance'
    b.addProperty('App::PropertyString', 'SealGrooveFace', 'Design')
    b.SealGrooveFace = 'inner face, z=14'
    return C.finish(d, b, code, 'PEEK, unfilled; material grade TBD', (.85, .72, .38))


def make_rear_insulator():
    code = 'KP-203'
    d, b = body_doc(code, 'Rear manifold insulator')
    t = P['rear_insulator_t']
    sk = C.sketch(b, 'InsulatorOutline', C.rounded(150, 150, 5))
    f = C.pad(b, 'InsulatorBlank', sk, t)
    bolts = [(x, y, 9) for x, y in P['bolt_points']]
    hs = hole_sketch(b, 'ThroughFastenerPattern', bolts, t)
    f = C.pocket(b, 'ThroughFastenerClearance', hs, t)
    loc = hole_sketch(b, 'ThroughLocatorPattern', [(x,y,3.2) for x,y in P['locator_points']], t)
    f = C.pocket(b, 'ThroughLocatorClearance', loc, t)
    manifold = P['manifold_points']
    # The rear panel is presented with its manifold-closing face at z=0.
    # Pocket sketches at z=depth cut back toward that face.
    ms = hole_sketch(b, 'BlindManifoldRecesses', port_holes(manifold, 8), 2)
    f = C.pocket(b, 'ManifoldClosureDepth', ms, 2)
    rings = C.sketch(b, 'InnerManifoldSealGrooves', ring_geometries(manifold, P['manifold_seal_mean_d'], P['manifold_groove_width']), C.at_z(P['manifold_groove_depth']))
    f = C.pocket(b, 'SealGrooveDepth', rings, P['manifold_groove_depth'])
    b.addProperty('App::PropertyString', 'SealGrooveFace', 'Design')
    b.SealGrooveFace = 'inner face, z=0; rear panel is flipped in assembly as required'
    b.addProperty('App::PropertyString', 'ManifoldRecessFace', 'Design')
    b.ManifoldRecessFace = 'inner face, z=0; blind recesses close the rear manifold ends'
    return C.finish(d, b, code, 'PEEK, unfilled; material grade TBD', (.85, .72, .38))


def make_jaw():
    d, b = body_doc('KP-301', 'Electrode tab clamp jaw')
    sk = C.sketch(b, 'JawOutline', C.rounded(16, 16, 1))
    f = C.pad(b, 'JawBlank', sk, 3)
    hs = hole_sketch(b, 'ClampBoltHole', [(0, 0, 4.5)], 3)
    f = C.pocket(b, 'ClampBoltClearance', hs, 3)
    return C.finish(d, b, 'KP-301', 'PEEK, unfilled; material grade TBD', (.85, .72, .38))


def make_busbar():
    d, b = body_doc('KP-302', 'Copper polarity busbar')
    # Axial length is 60 mm; cross-section is 6 X 20 mm.
    sk = C.sketch(b, 'BusbarSection', C.rect(-3, -10, 3, 10))
    f = C.pad(b, 'BusbarLength', sk, 60)
    # Axial mounting holes are drilled from the broad Y-facing side at both ends.
    rot = App.Rotation(V(1, 0, 0), -90)
    hs = C.sketch(b, 'EndFixingHoles', [C.circle(0, -4, 2.25), C.circle(0, -56, 2.25)],
                  App.Placement(V(0, 10, 0), rot))
    f = C.pocket(b, 'EndFixingClearance', hs, 20)
    return C.finish(d, b, 'KP-302', 'Copper, grade TBD', (.78, .38, .16))


def make_strap():
    d, b = body_doc('KP-303', 'Flexible polarity bridge strap')
    sk = C.sketch(b, 'StrapOutline', C.rect(-14, -4, 14, 4))
    f = C.pad(b, 'StrapFoil', sk, 1)
    hs = hole_sketch(b, 'TerminalHoles', [(-9, 0, 4.5), (9, 0, 4.5)], 1)
    f = C.pocket(b, 'TerminalPiercings', hs, 1)
    return C.finish(d, b, 'KP-303', 'Copper foil, temper TBD', (.72, .34, .13))


def make_dowel():
    d, b = body_doc('KP-401', 'Electrode stack locating dowel')
    sk = C.sketch(b, 'DowelSection', [C.circle(0, 0, 1.5)])
    f = C.pad(b, 'DowelLength', sk, 60)
    return C.finish(d, b, 'KP-401', 'PEEK, unfilled; material grade TBD', (.85, .72, .38))


def axial_body(code, label, material):
    d, b = body_doc(code, label)
    # Model along local +Z and orient body so its documented axis is global +Y.
    b.Placement = App.Placement(V(0, 0, 0), App.Rotation(V(1, 0, 0), -90))
    return d, b


def make_nut():
    d, b = axial_body('KP-501', 'M6x1 bulkhead connector nut', '316L stainless steel; thread simplified')
    nose = C.sketch(b, 'ThreadedNoseSection', [C.circle(0, 0, 3)])
    f = C.pad(b, 'ThreadedNoseEnvelope', nose, 8)
    head = C.sketch(b, 'HeadSection', [C.circle(0, 0, 4.5)], App.Placement(V(0, 0, 8), App.Rotation()))
    f = C.pad(b, 'FlangelessHead', head, 7)
    bore = C.sketch(b, 'TubePassage', [C.circle(0, 0, 1.55)], App.Placement(V(0, 0, 15), App.Rotation()))
    f = C.pocket(b, 'ThroughPassage', bore, 15)
    return C.finish(d, b, 'KP-501', '316L stainless steel; M6x1 thread represented by nominal envelope', (.7, .7, .73))


def make_ferrule():
    d, b = axial_body('KP-502', 'Tube compression ferrule', 'PTFE; material grade TBD')
    sk = C.sketch(b, 'FerruleAnnulus', [C.circle(0, 0, 1.7), C.circle(0, 0, 1.5)])
    f = C.pad(b, 'FerruleLength', sk, 2)
    b.addProperty('App::PropertyLength', 'FreeStateBoreDiameter', 'Specification')
    b.FreeStateBoreDiameter = 2.95
    b.addProperty('App::PropertyString', 'SupplierStatus', 'Specification')
    b.SupplierStatus = 'Supplier and product standard TBD; no standard is claimed'
    return C.finish(d, b, 'KP-502', 'PTFE, unfilled; supplier TBD', (.88, .88, .83))


def make_tube():
    d, b = axial_body('KP-503', 'Electrolyte tube stub', 'PTFE; material grade TBD')
    sk = C.sketch(b, 'TubeAnnulus', [C.circle(0, 0, 1.5), C.circle(0, 0, .8)])
    f = C.pad(b, 'TubeLength', sk, 35)
    return C.finish(d, b, 'KP-503', 'PTFE, unfilled; pressure and chemical suitability TBD', (.88, .88, .83))


def main():
    rows = []
    rows.append(make_electrode('KP-101', 'Anode electrode', 'Platinum or Pt-Ti; final specification TBD', (.78, .78, .8), 'A+x'))
    rows.append(make_electrode('KP-102', 'Cathode electrode', 'Material TBD', (.68, .72, .75), 'C-x'))
    rows.append(make_carrier('KP-601', 'Anode precision-film carrier', 'A+x'))
    rows.append(make_carrier('KP-602', 'Cathode precision-film carrier', 'C-x'))
    rows.append(make_plate('KP-201', 'Front dry endplate with manifold tool access', 'Aluminum alloy TBD; coating and compatibility TBD', 12, (.68, .7, .73), 3, True))
    rows.append(make_front_insulator())
    rows.append(make_rear_insulator())
    rows.append(make_plate('KP-204', 'Rear dry endplate', 'Aluminum alloy TBD; coating and compatibility TBD', 12, (.68, .7, .73), 3))
    rows.append(make_jaw())
    rows.append(make_busbar())
    rows.append(make_strap())
    rows.append(make_dowel())
    rows.append(make_nut())
    rows.append(make_ferrule())
    rows.append(make_tube())
    dims = {
        'KP-101': {'coupon': '56 x 56 x 0.35', 'outline_corner_radius': 2, 'tab': 'anode A+x only; root x=24, tip x=100, width_y=16', 'tab_hole': 'only Ø4.5 at (90,0)', 'metal_perforations': 'no manifold or locating holes', 'coupon_area_utilization': 79.56},
        'KP-102': {'coupon': '56 x 56 x 0.35', 'outline_corner_radius': 2, 'tab': 'cathode C-x only; root x=-24, tip x=-100, width_y=16', 'tab_hole': 'only Ø4.5 at (-90,0)', 'metal_perforations': 'no manifold or locating holes', 'coupon_area_utilization': 79.56},
        'KP-601': {'outer': '150 x 150 x 0.35', 'material': 'PEEK precision film; black appearance is visual only', 'coupon_aperture': '56.10 square R2.05', 'terminal_slot': 'width 16.10, open to +X outer edge, separate pocket', 'manifolds': '2 x Ø8 at (0,±62)', 'fasteners': '8 x Ø9; locators 2 x Ø3.2 through', 'thickness_tolerance': '0.35 ±0.01 mm provisional; supplier confirmation required'},
        'KP-602': {'outer': '150 x 150 x 0.35', 'material': 'PEEK precision film; black appearance is visual only', 'coupon_aperture': '56.10 square R2.05', 'terminal_slot': 'width 16.10, open to -X outer edge, separate pocket', 'manifolds': '2 x Ø8 at (0,±62)', 'fasteners': '8 x Ø9; locators 2 x Ø3.2 through', 'thickness_tolerance': '0.35 ±0.01 mm provisional; supplier confirmation required'},
        'KP-201': {'outer': '150 x 150 x 12', 'corner_radius': 5, 'through_holes': '8 x Ø9 at design_basis bolt_points', 'inner_locator_blind_holes': '2 x Ø3.2, depth 3 at design_basis locator_points', 'tool_access': '2 x Ø12 through at (0,±62); dry, no fluid ports'},
        'KP-202': {'outer': '150 x 150 x 14', 'corner_radius': 5, 'through_holes': '8 x Ø9 bolts and 2 x Ø3.2 locators', 'front_ports_from_outer_z0': 'M6x1 nominal properties; smooth Ø6 clearance to z8, Ø3.4 seat z8-10, Ø2.2 pilot z10-11, Ø8 manifold z11-14', 'inner_seal_grooves': '2 x annular, mean Ø14, width 2.2, depth 1.1 on z14 face; uses manifold-specific parameters'},
        'KP-203': {'outer': '150 x 150 x 6', 'corner_radius': 5, 'through_holes': '8 x Ø9 at design_basis bolt_points', 'manifold_closures': '2 x blind Ø8 x 2 at (0,±62) from inner z0 face', 'inner_seal_grooves': '2 x annular, mean Ø14, width 2.2, depth 1.1 on z0 face; uses manifold-specific parameters'},
        'KP-204': {'outer': '150 x 150 x 12', 'corner_radius': 5, 'through_holes': '8 x Ø9 at design_basis bolt_points', 'inner_locator_blind_holes': '2 x Ø3.2, depth 3 at design_basis locator_points', 'fluid_ports': 'none'},
        'KP-301': {'size': '16 x 16 x 3', 'corner_radius': 1, 'hole': 'Ø4.5 through'},
        'KP-302': {'section': '6 x 20', 'axial_length': 60, 'fixings': '2 x Ø4.5 through thickness, 52 mm center spacing'},
        'KP-303': {'size': '28 x 8 x 1', 'holes': '2 x Ø4.5, centers at x=±9; 2.75 end margin'},
        'KP-401': {'diameter': 3, 'length': 60},
        'KP-501': {'axis': 'global +Y', 'thread_envelope': 'M6 x 1 nominal, Ø6 x 8 long', 'head': 'Ø9 x 7', 'bore': 'Ø3.1 through', 'note': 'modeled thread is a nominal smooth envelope, not helical geometry'},
        'KP-502': {'axis': 'global +Y', 'outer_diameter': 3.4, 'modeled_bore': 3.0, 'free_state_bore': 2.95, 'length': 2, 'supplier': 'TBD'},
        'KP-503': {'axis': 'global +Y', 'outer_diameter': 3, 'inner_diameter': 1.6, 'length': 35},
    }
    result = {
        'revision': P['revision'],
        'units': 'mm',
        'status': P['status'],
        'source': 'design_basis.json and scripts/cad_common.py',
        'parts': rows,
        'dimensions': dims,
        'limitations': [
            'Electrode materials are unresolved; KP-101 and KP-102 material labels are intentionally provisional.',
            'KP-501 represents M6x1 with a nominal cylindrical envelope; helical threads are omitted.',
            'No operating pressure, current, electrolyte, seal qualification, manufacturing tolerances, or material grades are inferred.',
            'KP-202 and KP-203 are full-area support insulators, including under the electrode active area.',
            'The 56 mm electrode coupons sit in separate carrier windows; manifold, fastener and locator features are in the carriers, not the metal coupons.',
            'KP-601/KP-602 film thickness tolerance is provisional; confirm film grade, thickness tolerance, and supplier before release.',
            'KP-202 port bores use a smooth Ø6 clearance envelope with M6x1 nominal metadata; threads are not modeled helically.',
            'KP-203 rear insulator grooves and blind manifold recesses are on the z=0 inner face; assembly may flip the panel to align the face.',
        ],
    }
    (ROOT / 'validation' / 'mechanical_parts.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({'count': len(rows), 'parts': rows}, indent=2))


if __name__ == '__main__':
    main()
