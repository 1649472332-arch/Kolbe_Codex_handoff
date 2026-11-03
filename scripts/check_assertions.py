"""Confirm deliberately invalid geometries are rejected by OpenSCAD assertions."""
import json, subprocess, shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1]
exe=shutil.which('openscad') or r'C:\Program Files\OpenSCAD\openscad.com'
cases={'even_electrodes':'electrode_count=4','oversize_port':'port_d_mm=4',
       'seal_breakout':'gasket_cs_mm=3','wet_bolt':'bolt_x_mm=30',
       'small_electrode':'electrode_size_mm=55'}
results=[]
for name,define in cases.items():
    p=subprocess.run([exe,'-o',str(root/'validation/csg'/f'invalid_{name}.csg'),'-D',define,str(root/'kolbe_stack.scad')],capture_output=True,text=True)
    output=p.stdout+p.stderr
    passed='Assertion' in output and 'ERROR:' in output
    (root/'validation/logs'/f'invalid_{name}.txt').write_text(p.stdout+p.stderr,encoding='utf-8')
    results.append(dict(case=name,rejected=passed))
(root/'validation/assertion_checks.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print(results)
assert all(r['rejected'] for r in results)
