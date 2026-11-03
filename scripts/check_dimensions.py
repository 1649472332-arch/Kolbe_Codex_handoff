"""Independent dimensional review, based on the Rev A design basis (mm)."""
import json, math
from pathlib import Path

root=Path(__file__).resolve().parents[1]
rows=[]
for n in [3,5,7]:
    for gap in [2,4,6]:
        cs=gap/4
        checks={
            'groove_inner_to_window_land':30-1.4*cs/2-25,
            'port_to_groove_floor_ligament':gap/2-.75*cs-cs/2,
            'opposing_grooves_middle_web':gap-1.5*cs,
            'bolt_to_electrode_body_clearance':50-7/2-40,
            'bolt_to_frame_edge_land':60-50-7/2,
            'tube_to_next_tube_clearance':gap+.35-(cs+.4),
            'ear_to_nearest_washer_clearance':15-6-5,
        }
        assert all(v>0 for v in checks.values()), checks
        rows.append(dict(electrodes=n,gap_mm=gap,stack_mm=n*.35+(n-1)*gap+28,
                         nominal_gasket_compression=.25,nominal_groove_fill=math.pi/4/1.05,
                         clearances_mm=checks))
(root/'validation').mkdir(exist_ok=True)
(root/'validation/dimension_checks.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print('PASS: nine nominal dimensional configurations. Not a stress, leak or flow validation.')
