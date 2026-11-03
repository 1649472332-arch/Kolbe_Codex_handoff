#!/usr/bin/env python3
"""用 FreeCAD/OCCT 重建 V37 半框，仅派生流体孔；单位 mm。运行方法见 README。"""
from pathlib import Path
import hashlib
import itertools
import json
import math
import subprocess
import sys

try:
    import FreeCAD as App
except ImportError:
    sys.path.insert(0, '/usr/lib/freecad-python3/lib')
    import FreeCAD as App
import Part
sys.path.append(str(Path(App.getResourceDir()) / 'Mod'))
import PartDesign

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = ROOT / 'reference/Kolbe_v37_104p7_shell_68_chamber_8bolts_centered_ports_shifted.scad'
V = App.Vector
TOL = 1e-6
MIN_WALL = 3.0  # 研究阶段的几何筛选值，不是材料/承压设计规范
BOLTS = [(x, y) for x in (-44.175, 44.175) for y in (-44.175, 44.175)]
BOLTS += [(44.175, 0), (-44.175, 0), (0, 44.175), (0, -44.175)]
ZC = {'A': -10.09, 'B': 10.09}  # 保留原装配 0.18 间距；无隔膜，不放入膜实体
SOCKETS = {'A': [(-18., 2.), (18., -2.)], 'B': [(-16., -2.)]}


def moved(s, x=0, y=0, z=0):
    s = s.copy()
    s.translate(V(x, y, z))
    return s


def union(shapes):
    return shapes[0].multiFuse(shapes[1:]).removeSplitter() if len(shapes) > 1 else shapes[0]


def rr_face(w, h, r, x=0, y=0):
    """精确圆弧圆角矩形，对应 OpenSCAD offset(r) square。"""
    a, b = w / 2, h / 2
    points = [(-a+r, -b), (a-r, -b), (a, -b+r), (a, b-r),
              (a-r, b), (-a+r, b), (-a, b-r), (-a, -b+r)]
    c = [(a-r, -b+r), (a-r, b-r), (-a+r, b-r), (-a+r, -b+r)]
    edges = []
    for i in range(4):
        p, q, end = points[2*i], points[2*i+1], points[(2*i+2) % 8]
        edges.append(Part.makeLine(V(*p, 0), V(*q, 0)))
        cx, cy = c[i]
        theta = -math.pi/4 + i*math.pi/2
        mid = V(cx+r*math.cos(theta), cy+r*math.sin(theta), 0)
        edges.append(Part.Arc(V(*q, 0), mid, V(*end, 0)).toShape())
    return moved(Part.Face(Part.Wire(edges)), x=x, y=y)


def slab(face, z, height):
    return moved(face, z=z).extrude(V(0, 0, height))


def cylinder(p, q, d):
    axis = V(*q) - V(*p)
    return Part.makeCylinder(d/2, axis.Length, V(*p), axis.normalize())


def socket_cut(x, z):
    # 源码 y_top=60.75，主孔止于45.75；小孔从45.8延伸到32。
    return union([cylinder((x, 60.75, z), (x, 45.75, z), 10.6),
                  cylinder((x, 45.8, z), (x, 32, z), 6.65)])


def make_baseline(which):
    chamber = rr_face(68, 68, 4)
    # 源码只用四角 keepout；本版68窗未碰到这些圆，但仍忠实保留运算。
    for x, y in BOLTS[:4]:
        disk = Part.Face(Part.Wire(Part.makeCircle(10.25, V(x, y, 0))))
        chamber = chamber.cut(disk)
    outer = rr_face(104.7, 104.7, 3)
    blank = slab(outer, -10, 20)
    wet = slab(chamber, -10.2, 20.4)
    bolts = [Part.makeCylinder(3.75, 20.4, V(x, y, -10.2)) for x, y in BOLTS]
    body = blank.cut(wet).cut(union(bolts))
    bosses = [slab(rr_face(24, 12, 3, x, 54.35), -10, 20) for x, _ in SOCKETS[which]]
    body = union([body] + bosses)
    # offset(delta=2) 对应 R4 -> R6；68窗四角不碰 keepout，外扩亦不碰。
    ring = rr_face(72, 72, 6).cut(chamber)
    for x, y in BOLTS:
        dry = Part.Face(Part.Wire(Part.makeCircle(6, V(x, y, 0))))
        ring = ring.cut(dry)
    # 源码实际槽深为0.52：zc=±9.77，height=.58，伸出面.06。
    groove = slab(ring, 9.48 if which == 'A' else -10.06, .58)
    sockets = union([socket_cut(x, z) for x, z in SOCKETS[which]])
    body = body.cut(groove).cut(sockets).removeSplitter()
    assert body.isValid() and len(body.Solids) == 1
    return dict(shape=body, groove=groove, bolts=bolts, sockets=sockets,
                wet=wet, chamber=chamber, outer=outer, bosses=bosses)


def electrode_set(which):
    x = 18. if which == 'A' else -16.
    z = -2.  # 两根工作电极均为 local Z=-2
    # 源码 footprint_scale=2，实际片高60，片宽14，片厚.35；片顶28.5。
    plate = Part.makeBox(.35, 60, 14, V(x-.175, -31.5, z-7))
    rod = cylinder((x, 27.5, z), (x, 60.6, z), 3.)
    # SCAD 没有柱状夹具实体；以下为间隙配合示意，不建螺纹/夹紧机构。
    holder = union([cylinder((x, 46.15, z), (x, 60.35, z), 10.2),
                    cylinder((x, 60.35, z), (x, 65.35, z), 14.)])
    holder = holder.cut(cylinder((x, 46., z), (x, 65.5, z), 3.2))
    return {'plate': plate, 'rod': rod, 'holder': holder}


def port(name, kind, p, q, d):
    return dict(name=name, kind=kind, p=list(p), q=list(q), diameter_mm=d)


def top_outlets():
    # 每半框两路顶部出口，避开中心螺栓与M12孔；进口不复用M12孔。
    return [port('顶部出口'+str(x), 'outlet', (x, 53, 0), (x, 31, 0), 6.) for x in (-33, 33)]


def layouts():
    return {
        'inlet_top': dict(title='顶部进液／下侧出液＋顶部排气', ports=[
            port('顶部进口', 'inlet', (33, 53, 0), (33, 31, 0), 4.),
            port('下侧液体出口', 'outlet', (-53, -24, 0), (-32, -24, 0), 6.),
            port('顶部气液出口', 'vent', (-33, 53, 0), (-33, 31, 0), 6.)]),
        'inlet_tangential': dict(title='下侧偏置射流／顶部双出口', ports=[
            port('下侧偏置进口', 'inlet', (-53, -30, 0), (-30, -30, 0), 4.)] + top_outlets()),
        'inlet_bottom_top': dict(title='底部进液／顶部双出口', ports=[
            port('底部进口', 'inlet', (24, -53, 0), (24, -32, 0), 4.)] + top_outlets()),
        'inlet_multipoint': dict(title='四点底部分布进液／顶部双出口', ports=[
            port('底部进口'+str(x), 'inlet', (x, -53, 0), (x, -32, 0), 3.)
            for x in (-26, -12, 12, 26)] + top_outlets()),
    }


def checked(value, text):
    if not value:
        raise AssertionError(text)


def audit(which, base, result, cutters, specs, electrodes):
    b = base['shape']
    checked(result.isValid() and len(result.Solids) == 1, '半框实体必须有效且连续')
    checked(result.cut(b).Volume < TOL, '只许减去流道，不许新增框体')
    delta = b.cut(result)
    checked(delta.Volume > TOL, '必须实际切除流道')
    tools = union(cutters)
    checked(delta.cut(tools).Volume < TOL, '变更必须局限于流体孔道')
    checked(b.common(tools).cut(delta).Volume < TOL, '孔道必须完整切除')
    # 两个宽面包含密封面及槽底；几何对称差必须为0。
    face_band = union([Part.makeBox(140, 140, .6, V(-70, -70, z)) for z in (-10, 9.4)])
    checked(delta.common(face_band).Volume < TOL, '密封面和宽面不得改变')
    checks = []
    for c, spec in zip(cutters, specs):
        seal_distance = c.distToShape(base['groove'])[0]
        bolt_distance = min(c.distToShape(bolt)[0] for bolt in base['bolts'])
        socket_distance = c.distToShape(base['sockets'])[0]
        face_wall = 10 - abs(spec['p'][2]) - spec['diameter_mm']/2
        checked(min(seal_distance, bolt_distance, socket_distance, face_wall) >= MIN_WALL-TOL,
                f'{which} {spec["name"]}: 壁厚/间距不足')
        checked(c.common(base['wet']).Volume > .1, '孔道必须通液腔')
        checked(c.common(b).Volume > .1, '孔道必须穿过实体壁')
        checked(c.common(result).Volume < TOL, '孔道必须无阻断')
        p = V(*spec['p'])
        checked(not b.isInside(p, TOL, False), '孔口轴线起点必须在外侧')
        axis = (V(*spec['q'])-p).normalize()
        entry_cap = Part.makeCylinder(spec['diameter_mm']/2, .01, p, axis)
        checked(entry_cap.common(b).Volume < TOL, '孔口完整截面必须露在实体外，不能被原加高座遮挡')
        checked(base['wet'].isInside(V(*spec['q']), TOL, False), '孔道终点必须在液腔')
        checked(all(c.common(s).Volume < TOL for s in electrodes.values()), '不许切碰电极或夹具')
        # 轴线沿程取样；只容许从一个指定外表面进入，其他侧壁保持>=3。
        q = V(*spec['q'])
        for step in range(101):
            t = step/100
            v = p + (q-p)*t
            if abs(v.x) < 52.35 and abs(v.y) < 52.35:
                if abs(p.x) > 52.35:
                    other_wall = 52.35-abs(v.y)-spec['diameter_mm']/2
                else:
                    other_wall = 52.35-abs(v.x)-spec['diameter_mm']/2
                checked(other_wall >= MIN_WALL, '孔道接近非指定外壁')
        checks.append(dict(name=spec['name'], seal_distance_mm=seal_distance,
                           bolt_distance_mm=bolt_distance, socket_distance_mm=socket_distance,
                           broad_face_wall_mm=face_wall, chamber_connected=True,
                           electrode_intersection_mm3=0.0))
    pair_clearance = min(a.distToShape(c)[0] for a, c in itertools.combinations(cutters, 2))
    checked(pair_clearance >= MIN_WALL, '独立孔道之间壁厚不足')
    # 电极/夹具与半框没有新增或既有实体重叠（杆与电极接触为原示意）。
    for name, s in electrodes.items():
        checked(s.common(result).Volume < TOL, f'{name}与半框干涉')
    return dict(valid=True, solids=1, base_volume_mm3=b.Volume, final_volume_mm3=result.Volume,
                removed_volume_mm3=delta.Volume, protected_face_change_mm3=delta.common(face_band).Volume,
                min_channel_separation_mm=pair_clearance, ports=checks)


def feature(doc, group, name, label, shape, color, transparency=0):
    obj = doc.addObject('PartDesign::Feature' if group.TypeId == 'PartDesign::Body' else 'Part::Feature', name)
    obj.Label = label
    group.addObject(obj)
    obj.Shape = shape
    if App.GuiUp:
        obj.ViewObject.ShapeColor = color
        obj.ViewObject.Transparency = transparency
    return obj


def add_meta(obj, name, val):
    obj.addProperty('App::PropertyString', name, '设计记录')
    setattr(obj, name, str(val))


def save_model(stem, title, bases, all_electrodes, layout=None):
    doc = App.newDocument(stem)
    assy = doc.addObject('App::Part', 'Assembly')
    assy.Label = title + '（未验证）'
    add_meta(assy, 'Source', str(SOURCE.relative_to(ROOT)))
    add_meta(assy, 'SourceSHA256', hashlib.sha256(SOURCE.read_bytes()).hexdigest())
    add_meta(assy, 'Status', '仅几何研究；无隔膜；没有承压、密封或流型验证')
    add_meta(assy, 'DatumGap', '原装配间距0.18 mm，未放入膜；周边垫片待定')
    export_objects, result_checks, world_shapes = [], {}, []
    for which in ('A', 'B'):
        base = bases[which]
        group = doc.addObject('PartDesign::Body', 'HalfFrame'+which)
        group.Label = '半框'+which+'（源码尺寸）'
        assy.addObject(group)
        original = feature(doc, group, 'Original'+which, 'V37半框原始实体',
                           moved(base['shape'], z=ZC[which]), (.25, .55, .85))
        final = original
        shape = base['shape']
        if layout:
            cuts = [cylinder(p['p'], p['q'], p['diameter_mm']) for p in layout['ports']]
            shape = shape.cut(union(cuts)).removeSplitter()
            result_checks[which] = audit(which, base, shape, cuts, layout['ports'], all_electrodes[which])
            final = feature(doc, group, 'FluidBores'+which, '仅切除进出口孔道',
                            moved(shape, z=ZC[which]), (.25, .55, .85) if which == 'A' else (.9, .6, .23), 55)
            final.addProperty('App::PropertyLink', 'SourceFrame', '设计记录')
            final.SourceFrame = original
            add_meta(final, 'PortTable', json.dumps(layout['ports'], ensure_ascii=False))
            original.Visibility = False
        group.Tip = final
        if App.GuiUp:
            group.ViewObject.ShapeColor = (.25, .55, .85) if which == 'A' else (.9, .6, .23)
            group.ViewObject.Transparency = 55
        export_objects.append(group)
        world_shapes.append(moved(shape, z=ZC[which]))
        eg = doc.addObject('App::Part', 'Electrode'+which)
        eg.Label = which+'侧电极及柱状夹具示意（各方案相同）'
        assy.addObject(eg)
        for name, es in all_electrodes[which].items():
            labels = {'plate': '60×14×0.35薄电极片（源码占位）', 'rod': '直径3导电杆（源码示意）',
                      'holder': '柱状夹具占位（无真实夹紧及螺纹细节）'}
            ob = feature(doc, eg, which+name, labels[name], moved(es, z=ZC[which]),
                         (.12, .75, .55) if name == 'plate' else (.22, .23, .25))
            add_meta(ob, 'GeometryStatus', '夹具为新增占位' if name == 'holder' else '忠实对应源码cross_electrode_under')
            export_objects.append(ob)
            world_shapes.append(ob.Shape.copy())
    doc.recompute()
    # Debian FreeCAD 1.0/Python3.13 的旧 makeCompound 包装器会异常退出；使用构造器。
    expected = Part.Compound(world_shapes)
    print(stem, '保存原生文件', flush=True)
    target = HERE / (stem+'.FCStd')
    doc.saveAs(str(target))
    step_path = HERE / (stem+'.step')
    Part.export(export_objects, str(step_path))
    # OCCT导出器会在部分语法行末添加空格；规范化空白方便git检查。
    step_path.write_text('\n'.join(line.rstrip() for line in step_path.read_text().splitlines())+'\n')
    print(stem, '验证文件往返', flush=True)
    # 重新打开原生文档及STEP，验证实际交付文件而非只查内存。
    print(stem, '关闭原生文档', flush=True)
    App.closeDocument(doc.Name)
    print(stem, '重新打开原生文档', flush=True)
    reopened = App.openDocument(str(target))
    print(stem, '原生文件已重读', flush=True)
    checked(all(o.Shape.isValid() for o in reopened.Objects if hasattr(o, 'Shape') and not o.Shape.isNull()),
            '保存后原生实体有效性失败')
    imported = Part.read(str(HERE / (stem+'.step')))
    print(stem, 'STEP已重读', flush=True)
    checked(imported.isValid() and len(imported.Solids) == len(expected.Solids), 'STEP重读实体数量失败')
    rel_volume = abs(imported.Volume-expected.Volume)/expected.Volume
    checked(rel_volume < 1e-7, 'STEP往返体积误差')
    checked(expected.cut(imported).Volume < .001 and imported.cut(expected).Volume < .001, 'STEP几何往返不一致')
    App.closeDocument(reopened.Name)
    return dict(frames=result_checks, step_roundtrip=dict(valid=True, solids=len(imported.Solids),
                relative_volume_error=rel_volume), native_reopened=True)


def compare_source(bases):
    """独立执行原SCAD导出网格，核对体积和包围盒；不使用网格生成FreeCAD实体。"""
    import Mesh
    import tempfile
    records = {}
    with tempfile.TemporaryDirectory(prefix='kolbe-source-') as tmp:
        for which in ('A', 'B'):
            out = Path(tmp) / (which+'.stl')
            r = subprocess.run(['openscad', '-o', str(out), '-D', 'part="half_frame_'+which+'"', str(SOURCE)],
                               capture_output=True, text=True, check=True)
            mesh = Mesh.Mesh(str(out))
            b = bases[which]['shape']
            volume_error = abs(mesh.Volume-b.Volume)/b.Volume
            dims = ['XMin', 'XMax', 'YMin', 'YMax', 'ZMin', 'ZMax']
            bbox_error = max(abs(getattr(mesh.BoundBox, d)-getattr(b.BoundBox, d)) for d in dims)
            checked(volume_error < .0015 and bbox_error < .005, '与SCAD源码几何不一致')
            records[which] = dict(scad_mesh_volume_mm3=mesh.Volume, freecad_exact_volume_mm3=b.Volume,
                                  relative_volume_error=volume_error, max_bbox_error_mm=bbox_error,
                                  note='SCAD圆柱为96边网格，FreeCAD为精确圆弧；比较允许0.15%体积偏差')
    return records


def main():
    bases = {w: make_baseline(w) for w in ('A', 'B')}
    electrodes = {w: electrode_set(w) for w in ('A', 'B')}
    # 严格保留参与设计的源参数；源文件变化须人工重新审核重建映射。
    source_checks = ['chamber_target = 68.0;', 'outer_R = 3.0;', 'gasket_ring_width = 2.0;',
                     'A_socket_x = -18.0;', 'B_socket_x = -16.0;', 'A_second_socket_x = 18.0;']
    checked(all(s in SOURCE.read_text() for s in source_checks), '源码参数已变化，请重新审核映射')
    report = dict(freecad_version=App.Version()[:3], source=str(SOURCE.relative_to(ROOT)),
                  source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                  minimum_screening_wall_mm=MIN_WALL, source_comparison=compare_source(bases),
                  baseline=save_model('baseline_half_frame', 'V37半框FreeCAD基准', bases, electrodes), variants={})
    configs = layouts()
    for stem, layout in configs.items():
        print('生成并校验', stem, flush=True)
        report['variants'][stem] = save_model(stem, layout['title'], bases, electrodes, layout)
    (HERE/'geometry_checks.json').write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n')
    (HERE/'port_layouts.json').write_text(json.dumps(configs, indent=2, ensure_ascii=False)+'\n')
    print('完成：基准及四版原生文件、STEP和几何检查记录。', flush=True)


if __name__ == '__main__':
    main()
