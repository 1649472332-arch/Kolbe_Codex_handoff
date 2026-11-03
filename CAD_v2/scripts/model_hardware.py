"""Generate editable electro-mechanical support hardware for the Kolbe stack.

Run with FreeCAD's bundled Python. Rigid hardware uses native Body/Sketch/
Pad/Pocket features. Free seals use a valid swept or toroidal BRep feature.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import cad_common as C
import FreeCAD as App
import Part

P = C.P
V = C.V


def body_doc(code, label):
    name = code.replace('-', '_')
    try:
        App.closeDocument(name)
    except Exception:
        pass
    d = App.newDocument(name)
    return d, C.body_new(d, 'Body', label)


def finish(d, b, code, material, color=(.7, .7, .7)):
    return C.finish(d, b, code, material, color)


def plane_sketch(body, name, geos, origin, rotation=None):
    if isinstance(origin, App.Placement):
        placement = origin
    else:
        placement = App.Placement(origin, rotation or App.Rotation())
    return C.sketch(body, name, geos, placement)


def make_comb(count, side):
    code = 'KB-' + side + str(count)
    label = ('Anode positive-X' if side == 'A' else 'Cathode negative-X') + ' copper comb busbar, ' + str(count) + ' layers'
    d, b = body_doc(code, label)
    sign = 1 if side == 'A' else -1
    x1, x2 = (115, 121) if sign > 0 else (-121, -115)
    pitch = .35 + 6
    active_h = count * .35 + (count - 1) * 6
    active_indices = [i for i in range(0, count)
                      if ((i % 2 == 1) if side == 'A' else (i % 2 == 0))]
    spine = C.sketch(b, 'SpineSection', C.rect(x1, -4, x2, 4), C.at_z(-2))
    f = C.pad(b, 'SpineLength', spine, active_h + 4)
    hole_zs = []
    for i in active_indices:
        z0, z1 = i * pitch - 2, i * pitch
        xx1, xx2 = (82, 116) if sign > 0 else (-116, -82)
        finger = C.sketch(b, 'Finger_%02d' % i, C.rect(xx1, -4, xx2, 4), C.at_z(z0))
        f = C.pad(b, 'FingerPad_%02d' % i, finger, z1-z0)
        hole_zs.append((i, z1-2, z1))
        terminal = plane_sketch(b, 'TerminalHole_%02d' % i,
                                [C.circle(sign * 90, 0, 2.25)], C.at_z(z1))
        f = C.pocket(b, 'TerminalPiercing_%02d' % i, terminal, 2)
    crossx = 121 if sign > 0 else -121
    crossrot = App.Rotation(V(0, 1, 0), 90 if sign > 0 else -90)
    for j, zc in enumerate((1, active_h-3), 1):
        # Sketch normal points outwards; Pocket travels back across the 6 mm spine.
        lx = -zc if sign > 0 else zc
        cross = plane_sketch(b, 'SupportCrossHole_%d' % j,
                             [C.circle(lx, 0, 1.65)], V(crossx, 0, 0), crossrot)
        f = C.pocket(b, 'SupportCrossDrill_%d' % j, cross, 6)
    b.addProperty('App::PropertyInteger', 'ElectrodeCount', 'Design')
    b.ElectrodeCount = count
    b.addProperty('App::PropertyString', 'PolaritySide', 'Design')
    b.PolaritySide = 'A positive-X' if side == 'A' else 'C negative-X'
    b.addProperty('App::PropertyLength', 'FingerBeamCrossSectionY', 'Design')
    b.FingerBeamCrossSectionY = 8
    b.addProperty('App::PropertyString', 'FingerIndices', 'Design')
    b.FingerIndices = ','.join(str(i) for i, _, _ in hole_zs)
    return finish(d, b, code, 'Copper, grade TBD; current rating not established', (.78, .38, .16))


def make_support(code, rear=False):
    label = 'Rear PEEK comb support bracket' if rear else 'Front PEEK comb support bracket'
    d, b = body_doc(code, label)
    foot = C.sketch(b, 'SupportFoot', C.rect(60, -30, 130, 30), C.at_z(-5))
    f = C.pad(b, 'FootPad', foot, 5)
    post_top = 25 if rear else 31.5
    post_h = post_top + .5
    post = C.sketch(b, 'CombMountPost', C.rect(121, -6, 128, 6), C.at_z(-.5))
    f = C.pad(b, 'PostPad', post, post_h)
    bolt_geos = [C.circle(65, -20, 4.5), C.circle(65, 20, 4.5)]
    bolt = C.sketch(b, 'TieRodFootHoles', bolt_geos, C.at_z(0))
    f = C.pocket(b, 'TieRodClearance', bolt, 5)
    cross_z = 21 if rear else 27
    rot = App.Rotation(V(0, 1, 0), 90)
    cross = plane_sketch(b, 'CombAttachmentCrossHole', [C.circle(-cross_z, 0, 2.25)], V(128, 0, 0), rot)
    f = C.pocket(b, 'CombAttachmentDrill', cross, 7)
    b.addProperty('App::PropertyString', 'AssemblyTransform', 'Design')
    b.AssemblyTransform = 'Flip 180 degrees about global Y and translate by total body stack height' if rear else 'Front global coordinates; negative-X mate may be mirrored by 180 degrees about Z'
    b.addProperty('App::PropertyString', 'StructuralStatus', 'Design')
    b.StructuralStatus = 'Preliminary geometry only; PEEK cantilever not structurally qualified'
    return finish(d, b, code, 'PEEK, grade TBD; structural qualification pending', (.08, .08, .09))


def axial_body(code, label):
    d, b = body_doc(code, label)
    b.Placement = App.Placement(V(0, 0, 0), App.Rotation(V(1, 0, 0), -90))
    return d, b


def make_cross_drill_plug():
    code = 'KH-901'
    d, b = axial_body(code, 'M4x0.7 nominal cross-drill plug')
    nose = C.sketch(b, 'ThreadEnvelope', [C.circle(0, 0, 1.65)])
    f = C.pad(b, 'NominalThreadCore', nose, 6)
    head = plane_sketch(b, 'LowProfileHead', [C.circle(0, 0, 2.75)], V(0, 0, 6))
    f = C.pad(b, 'HeadPad', head, 2)
    slot = plane_sketch(b, 'DriverSlot', C.rect(-3, -.5, 3, .5), V(0, 0, 8))
    f = C.pocket(b, 'DriverSlotCut', slot, .8)
    b.addProperty('App::PropertyLength', 'NominalMajorDiameter', 'Thread designation')
    b.NominalMajorDiameter = 4
    b.addProperty('App::PropertyLength', 'NominalPitch', 'Thread designation')
    b.NominalPitch = .7
    b.addProperty('App::PropertyString', 'ThreadGeometry', 'Thread designation')
    b.ThreadGeometry = 'M4x0.7 nominal; simplified smooth 脴3.3 envelope, no helical thread'
    return finish(d, b, code, '316L stainless steel; exact grade and thread fit TBD', (.7, .7, .73))


def make_plug_washer():
    code = 'KH-902'
    d, b = axial_body(code, 'Cross-drill plug washer')
    washer = C.sketch(b, 'WasherAnnulus', [C.circle(0, 0, 2.75), C.circle(0, 0, 2.1)])
    f = C.pad(b, 'WasherThickness', washer, .5)
    return finish(d, b, code, 'Washer stock TBD', (.68, .68, .7))


def make_main_seal():
    code = 'KS-101'
    d, b = body_doc(code, 'Closed rounded-square main seal')
    path_geos = C.rounded(P['seal_centerline_size'], P['seal_centerline_size'], P['seal_corner'])
    path = Part.Wire([g.toShape() for g in path_geos])
    start = V(-P['seal_centerline_size']/2 + P['seal_corner'], -P['seal_centerline_size']/2, 0)
    profile = Part.Wire([Part.makeCircle(P['seal_cs']/2, start, V(1, 0, 0))])
    shape = path.makePipeShell([profile], True, True)
    C.feature(b, 'SweptSealBRep', shape,
              CenterlineSize=P['seal_centerline_size'], CornerRadius=P['seal_corner'], CrossSection=P['seal_cs'])
    b.addProperty('App::PropertyString', 'MaterialStatus', 'Specification')
    b.MaterialStatus = 'Elastomer type, compound and hardness TBD'
    return finish(d, b, code, 'Elastomer TBD; seal compound and hardness unresolved', (.2, .2, .22))


def make_manifold_seal():
    code = 'KS-102'
    d, b = body_doc(code, 'Free manifold face seal')
    shape = Part.makeTorus(P['manifold_seal_mean_d']/2, P['manifold_seal_cs']/2)
    C.feature(b, 'TorusSealBRep', shape,
              MeanDiameter=P['manifold_seal_mean_d'], CrossSection=P['manifold_seal_cs'])
    b.addProperty('App::PropertyString', 'MaterialStatus', 'Specification')
    b.MaterialStatus = 'Elastomer type, compound and hardness TBD'
    return finish(d, b, code, 'Elastomer TBD; seal compound and hardness unresolved', (.2, .2, .22))


def main():
    rows = []
    for n in (3, 5, 7):
        for side in ('A', 'C'):
            rows.append(make_comb(n, side))
    rows.append(make_support('KB-801', False))
    rows.append(make_support('KB-802', True))
    rows.append(make_cross_drill_plug())
    rows.append(make_plug_washer())
    rows.append(make_main_seal())
    rows.append(make_manifold_seal())
    pitch = .35 + 6
    dims = {}
    for n in (3, 5, 7):
        active_h = n*.35 + (n-1)*6
        dims['KB-A%d' % n] = {'spine': 'X115..121, Y-4..4, Z-2..H+2', 'layer_indexing': 'zero-based i=0..n-1', 'finger_indices': [i for i in range(0, n) if i % 2 == 1], 'finger_interval': 'x=82..116, y=-4..4, z=(i*6.35-2)..i*6.35', 'through_holes': '脴4.5 along Z at x=90 on each active finger', 'support_crossholes': '脴4.5 along X through 6 mm spine at Z=1 and H-3; M4x0.7 tapped, core diameter 3.3', 'active_height': active_h}
        dims['KB-C%d' % n] = {'spine': 'X-121..-115, Y-4..4, Z-2..H+2', 'layer_indexing': 'zero-based i=0..n-1', 'finger_indices': [i for i in range(0, n) if i % 2 == 0], 'finger_interval': 'x=-116..-82, y=-4..4, z=(i*6.35-2)..i*6.35', 'through_holes': '脴4.5 along Z at x=-90 on each active finger', 'support_crossholes': '脴4.5 along X through 6 mm spine at Z=1 and H-3; M4x0.7 tapped, core diameter 3.3', 'active_height': active_h}
    dims.update({
        'KB-801': {'foot': 'X60..130, Y-30..30, Z-5..0', 'foot_holes': '2 x 脴9 through at (65,卤20)', 'post': 'X121..128, Y-6..6, Z-0.5..31.5', 'attachment_hole': '脴4.5 along X at Y=0,Z=27'},
        'KB-802': {'foot': 'X60..130, Y-30..30, Z-5..0', 'foot_holes': '2 x 脴9 through at (65,卤20)', 'post': 'X121..128, Y-6..6, Z-0.5..25', 'attachment_hole': '脴4.5 along X at Y=0,Z=21', 'assembly': 'flip 180 degrees about global X, translate to stack height'},
        'KH-901': {'axis': 'global +Y', 'thread': 'M4x0.7 nominal smooth 脴3.3 envelope, L6', 'head': '脴5.5 x 2, with 1.0 wide driver slot, depth 0.8'},
        'KH-902': {'axis': 'global +Y', 'outer_diameter': 5.5, 'inner_diameter': 4.2, 'thickness': .5},
        'KS-101': {'centerline': 'rounded square 53.6 x 53.6, R4.8', 'cross_section_diameter': 1, 'material': 'elastomer TBD'},
        'KS-102': {'mean_diameter': 14, 'cross_section_diameter': 1.5, 'material': 'elastomer TBD'},
    })
    result = {
        'revision': P['revision'],
        'units': 'mm',
        'status': P['status'],
        'source': 'design_basis.json and scripts/cad_common.py',
        'parts': rows,
        'dimensions': dims,
        'limitations': [
            'Copper grade and allowable bus current are unconfirmed; 6 x 8 mm beam cross-section is preliminary.',
            'PEEK support brackets are preliminary cantilevers and have not been structurally qualified.',
            'Elastomer compound, hardness, compression, and chemical compatibility remain unspecified.',
            'KH-901 M4x0.7 thread is a nominal smooth envelope, not helical thread geometry.',
        ],
    }
    (ROOT / 'validation' / 'hardware_parts.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({'count': len(rows), 'parts': rows}, indent=2))


if __name__ == '__main__':
    main()
