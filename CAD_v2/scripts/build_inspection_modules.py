"""Create self-contained inspection modules without changing source assemblies."""
import json
from pathlib import Path
import FreeCAD as A
import Part
from chinese_names import localize_document, document_label

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'modules'
OUT.mkdir(exist_ok=True)

def category(o):
    role, code = o.Function, o.PartNumber
    if role.startswith('Electrode ') or role.startswith('Precision insulating carrier '):
        return 'electrode_%02d' % int(role.split()[1 if role.startswith('Electrode ') else 3])
    if role.startswith('Parallel flow channel ') or role.startswith('Channel '):
        return 'flow_%02d' % int(role.split()[3 if role.startswith('Parallel') else 1])
    if role.startswith('Front manifold') or code in ('KP-201', 'KP-202'):
        return 'front_end'
    if role.startswith('Rear manifold') or code in ('KP-203', 'KP-204'):
        return 'rear_end'
    if code in ('KP-501', 'KP-502', 'KP-503'):
        return 'fluid_ports'
    if code.startswith('STD-M8') or code.startswith('STD-LOCATOR'):
        return 'tie_rods_alignment'
    return 'electrical_busbars'

def main():
    report = []
    for n in (3, 5, 7):
        source = A.openDocument(str(ROOT/'assemblies'/f'Kolbe_{n}.FCStd'))
        groups = {}
        for o in source.Objects:
            if o.TypeId == 'App::Link' and hasattr(o, 'PartNumber'):
                groups.setdefault(category(o), []).append(o)
        seen = []
        for key, objects in groups.items():
            stem = f'Kolbe_{n}_{key}'
            d = A.newDocument(stem)
            for original in objects:
                f = d.addObject('PartDesign::Feature', original.Name)
                f.Label = original.Label
                f.Shape = original.Shape.copy()
                for prop, value in [('PartNumber', original.PartNumber), ('SourceObject', original.Name),
                                    ('SourceAssembly', f'assemblies/Kolbe_{n}.FCStd'),
                                    ('EditableSource', 'parts/'+original.PartNumber.replace('-COMP','')+'.FCStd'),
                                    ('DisplayColor', original.DisplayColor)]:
                    f.addProperty('App::PropertyString', prop, 'Source'); setattr(f, prop, value)
                f.addProperty('App::PropertyString', 'Representation', 'Source')
                f.Representation = 'Independent inspection solid in assembly coordinates; editable feature history in EditableSource. COMP seals show compressed shape.'
                assert f.Shape.isValid() and len(f.Shape.Solids) == 1
            d.recompute()
            path = OUT/(document_label(stem).replace('｜','_')+'.FCStd')
            localize_document(d)
            d.saveAs(str(path)); Part.export(d.Objects, str(path.with_suffix('.step')))
            expected = sum(o.Shape.Volume for o in objects)
            names = [o.Name for o in objects]
            A.closeDocument(d.Name)
            reopened = A.openDocument(str(path))
            assert len(reopened.Objects) == len(objects)
            actual = sum(o.Shape.Volume for o in reopened.Objects)
            assert abs(actual-expected) < 1e-5
            assert all(o.Shape.isValid() and len(o.Shape.Solids)==1 for o in reopened.Objects)
            rt = Part.Shape(); rt.read(str(path.with_suffix('.step')))
            assert rt.isValid() and len(rt.Solids)==len(objects)
            assert abs(rt.Volume-expected)<max(1e-4, expected*1e-6), (stem, rt.Volume, expected)
            report.append({'file': str(path.relative_to(ROOT)), 'module':key,'configuration':n,
                           'objects':names,'solids':len(objects),'volume_mm3':actual,
                           'native_reopen_valid':True,'step_roundtrip_valid':True,
                           'step_volume_delta_mm3':rt.Volume-expected,'step_relative_volume_tolerance':1e-6})
            seen.extend(names); A.closeDocument(reopened.Name)
        all_links = [o.Name for o in source.Objects if o.TypeId=='App::Link' and hasattr(o,'PartNumber')]
        assert len(seen)==len(set(seen)) and set(seen)==set(all_links)
        A.closeDocument(source.Name)
    (ROOT/'validation'/'inspection_modules.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'modules':len(report),'all_valid':True}))

if __name__ == '__main__': main()
