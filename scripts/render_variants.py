"""Reproducible OpenSCAD export; no structural/pressure certification."""
import argparse, json, shutil, subprocess, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--openscad', default=shutil.which('openscad') or r'C:\Program Files\OpenSCAD\openscad.com')
    ap.add_argument('--quick', action='store_true', help='CSG matrix only')
    args = ap.parse_args()
    for d in ['renders', 'models', 'drawings', 'validation/logs', 'validation/csg']:
        (ROOT/d).mkdir(parents=True, exist_ok=True)
    results=[]
    def run(name, output, part, n=3, gap=4, extra=()):
        cmd=[args.openscad,'-o',str(ROOT/output),'-D',f'part="{part}"','-D',f'electrode_count={n}','-D',f'gap_mm={gap}',*extra,str(ROOT/'kolbe_stack.scad')]
        start=time.time()
        p=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=240)
        (ROOT/f'validation/logs/{name}.txt').write_text(p.stdout+p.stderr,encoding='utf-8')
        ok=p.returncode==0 and 'ERROR:' not in p.stdout+p.stderr and (ROOT/output).exists() and (ROOT/output).stat().st_size>0
        results.append(dict(name=name,ok=ok,seconds=round(time.time()-start,2),command=cmd))
        print(name, 'PASS' if ok else 'FAIL',flush=True)
    for n in [3,5,7]:
        for gap in [2,4,6]:
            run(f'csg_{n}_{gap}',f'validation/csg/stack_{n}_gap{gap}.csg','assembly',n,gap)
    if not args.quick:
        for n in [3,5,7]:
            run(f'assembly_{n}',f'renders/assembly_{n}.png','assembly',n,extra=['--imgsize=1600,1100','--viewall','--autocenter'])
        for part in ['exploded','one_frame','flow_section','terminal_detail']:
            camera=['-D','explode_step_mm=18','--camera=200,-260,130,0,0,90'] if part=='exploded' else []
            run(part,f'renders/{part}.png',part,extra=['--imgsize=1800,1200','--viewall','--autocenter',*camera])
        for part in ['one_frame','gasket','anode','cathode','endplate','insulator','tube_adapter']:
            run('stl_'+part,f'models/{part}.stl',part)
        for part in ['frame_profile','anode_profile','cathode_profile','endplate_profile','insulator_profile']:
            run('dxf_'+part,f'drawings/{part}.dxf',part)
    (ROOT/'validation/export_results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    if not all(r['ok'] for r in results):
        raise SystemExit('Some exports failed; inspect validation/logs')

if __name__=='__main__':
    main()
