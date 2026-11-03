#!/usr/bin/env python3
"""独立重读最终交付：只读检查原生/STEP一致性、电极不变和文件完整性。"""
import hashlib
import json
from pathlib import Path
import re
import struct
import generate_variants as G

P, A, V = G.Part, G.App, G.V
HERE = Path(__file__).resolve().parent


def same(a, b):
    assert a.cut(b).Volume < .001 and b.cut(a).Volume < .001


def solids(doc):
    return [doc.getObject('HalfFrame'+w).Shape.copy() for w in ('A','B')] + [
        doc.getObject(w+n).Shape.copy() for w in ('A','B') for n in ('plate','rod','holder')]


def main():
    baseline = A.openDocument(str(HERE/'baseline_half_frame.FCStd'))
    reference = solids(baseline)
    A.closeDocument(baseline.Name)
    layouts = json.loads((HERE/'port_layouts.json').read_text())
    geometry = json.loads((HERE/'geometry_checks.json').read_text())
    assert geometry['source_sha256'] == hashlib.sha256(G.SOURCE.read_bytes()).hexdigest()
    report = {'passed': True, 'files': {}, 'variants': {}}
    for stem in ['baseline_half_frame']+list(layouts):
        doc = A.openDocument(str(HERE/(stem+'.FCStd')))
        native = solids(doc)
        for s in native:
            assert s.isValid() and len(s.Solids) == 1
        step = P.read(str(HERE/(stem+'.step')))
        assert step.isValid() and len(step.Solids) == 8
        same(P.Compound(native), step)
        if stem in layouts:
            for base, actual in zip(reference[2:], native[2:]):
                same(base, actual)
            for i, w in enumerate(('A','B')):
                b, s = reference[i], native[i]
                assert s.cut(b).Volume < 1e-6 and b.cut(s).Volume > 1
                tools = G.union([G.moved(G.cylinder(p['p'],p['q'],p['diameter_mm']), z=G.ZC[w])
                                 for p in layouts[stem]['ports']])
                same(b.cut(tools), s)
            png = (HERE/(stem+'.png')).read_bytes()
            assert png[:8] == b'\x89PNG\r\n\x1a\n'
            width, height = struct.unpack('>II', png[16:24])
            assert width >= 1600 and height >= 800
            report['variants'][stem] = {'valid_single_solids': 8, 'electrodes_rods_holders_unchanged': True,
                'only_designated_bores_changed': True, 'native_step_equal': True,
                'png_pixels': [width,height]}
        A.closeDocument(doc.Name)
        for ext in ['.FCStd','.step']+(['.png'] if stem in layouts else []):
            f = HERE/(stem+ext)
            report['files'][f.name] = {'bytes': f.stat().st_size, 'sha256': hashlib.sha256(f.read_bytes()).hexdigest()}
    # README中的本地相对文件链接必须能打开。
    for target in re.findall(r'\]\(([^)]+)\)', (HERE/'README.md').read_text()):
        if not target.startswith('http'):
            assert (HERE/target).exists(), target
    (HERE/'delivery_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('最终文件独立校验通过：5套原生/STEP、4张PNG，电极/杆/夹具不变，仅指定流体孔变化。')


if __name__ == '__main__':
    main()
