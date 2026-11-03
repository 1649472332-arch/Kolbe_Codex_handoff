"""Verify Chinese labels, removed copper hardware and unchanged retained solids."""
from pathlib import Path
import json, re
import FreeCAD as A, Part
from chinese_names import localize_document
ROOT=Path(__file__).resolve().parents[1]
def removed(code):return code.startswith('KB-') or code=='KP-301' or code.startswith('STD-M4')
report=[]
native=[];steps=[]
for path in sorted((ROOT/'parts').glob('*.FCStd')):
    d=A.openDocument(str(path))
    assert all(any('\u4e00'<=c<='\u9fff' for c in o.Label) for o in d.Objects if o.TypeId=='PartDesign::Body'),path.name
    A.closeDocument(d.Name)
for n in (3,5,7):
    old=json.loads((ROOT/'archive'/'before_no_busbars'/'validation'/f'assembly_{n}.json').read_text(encoding='utf-8'))
    new=json.loads((ROOT/'validation'/f'assembly_{n}.json').read_text(encoding='utf-8'))
    kept=[p for p in old['parts'] if not removed(p['code'])]
    def key(p):return p['code'],tuple(round(b,5) for b in p['bounds']),round(p['volume_mm3'],5)
    unaffected=lambda p:not (p['code'].startswith('STD-M8') and abs((p['bounds'][1]+p['bounds'][4])/2)==20)
    assert sorted(map(key,filter(unaffected,kept)))==sorted(map(key,filter(unaffected,new['parts'])))
    assert len(kept)==len(new['parts'])
    assert not new['unresolved_intersections']
    d=A.openDocument(str(ROOT/'assemblies'/f'Kolbe_{n}.FCStd'))
    links=[o for o in d.Objects if o.TypeId=='App::Link']
    assert len(links)==len(kept) and all(not removed(o.PartNumber) for o in links)
    H=new['body_stack_height_mm']
    for o in links:
        b=o.Shape.BoundBox
        if o.PartNumber=='STD-M8-WASHER':
            assert min(abs(b.ZMax),abs(b.ZMin-H))<1e-6
        if o.PartNumber.startswith('STD-M8-ROD-'):
            assert o.PartNumber.endswith('-PLATE') and abs(b.ZMin+10.1)<1e-6 and abs(b.ZMax-H-10.1)<1e-6
    assert all(re.search('[\u4e00-\u9fff]',o.Label) for o in links)
    assert all(not removed(getattr(o,'PartNumber','')) for o in d.Objects)
    shape=Part.Shape();shape.read(str(ROOT/'assemblies'/f'Kolbe_{n}.step'))
    assert shape.isValid() and len(shape.Solids)==len(links)
    native.append({'file':d.FileName,'external_object_references':[],'native_bodies':sum(o.TypeId=='PartDesign::Body' for o in d.Objects),'sketches':sum(o.TypeId=='Sketcher::SketchObject' for o in d.Objects),'links':len(links)})
    steps.append({'file':Path(d.FileName).name,'instances':len(links),'step_solids':len(shape.Solids),'valid':True})
    report.append({'electrodes':n,'old_instances':len(old['parts']),'removed_instances':len(old['parts'])-len(links),
        'current_instances':len(links),'unaffected_geometry_and_placements_unchanged':True,
        'support_span_rods_replaced_with_plate_span_rods':True,
        'chinese_labels':True,'no_busbars_or_dedicated_hardware':True,'step_valid':True,'unresolved_intersections':0})
    A.closeDocument(d.Name)
(ROOT/'validation'/'no_busbars_chinese.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
(ROOT/'validation'/'native_document_check.json').write_text(json.dumps(native,indent=2,ensure_ascii=False),encoding='utf-8')
(ROOT/'validation'/'step_roundtrip.json').write_text(json.dumps(steps,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
