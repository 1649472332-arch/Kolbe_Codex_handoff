#!/usr/bin/env bash
# Scope A: stage -> verify every mode -> render CGAL -> publish named files only.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ -x /usr/bin/openscad ]]; then
  OSC=/usr/bin/openscad
else
  OSC="$(command -v openscad)"
fi
if [[ -z "${DISPLAY:-}" ]] && ! command -v xvfb-run >/dev/null; then
  echo 'PNG rendering needs DISPLAY or xvfb-run' >&2
  exit 1
fi
# Workspace-backed staging survives a machine reboot. Only our marked directory
# is reused; every asset/check/render has its own input and output fingerprints.
STAGE="$ROOT/.cad-export-stage"
if [[ -e "$STAGE" && ! -f "$STAGE/.kolbe-stage" ]]; then
  echo "Unrecognized staging directory: $STAGE" >&2
  exit 1
fi
mkdir -p "$STAGE"
touch "$STAGE/.kolbe-stage"
cleanup() {
  local result=$?
  if [[ "$result" == 0 ]]; then
    rm -rf "$STAGE"
  else
    echo "Failed stage retained for diagnosis: $STAGE" >&2
  fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
python3 - "$ROOT" "$STAGE" "$OSC" <<'PY'
from pathlib import Path
import json
import shutil
import subprocess
import sys
import hashlib
import struct
import numpy as np
root, stage, osc = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
sys.path.insert(0, str(root/'scripts'))
import export_manifest as ex
from verify_cad import verify
ex.OSC = osc
(stage/'renders').mkdir(exist_ok=True)

def checked(manifest, report):
    inputs={'manifest_sha256':ex.sha(manifest),'verifier_sha256':ex.sha(root/'scripts/verify_cad.py')}
    # Always rerun the mesh checks. A retained stage may reuse source-matched
    # meshes, but a cached passing report is never evidence for a fresh run.
    try:
        result=verify(manifest,report)
    except RuntimeError:
        result=json.loads(report.read_text())
        if result.get('error'):
            raise
        # Collect genuine geometry failures across every requested suite, then
        # fail the publication gate below. No failed check is waived.
    result['verification_inputs']=inputs
    ex.write_json(report,result)
    return result

print('Default EPDM flat gasket', flush=True)
default = ex.export_models(stage/'stack_manifest.json')
default_report = checked(stage/'stack_manifest.json',stage/'renders/cad_verification.json')
print('O-ring complete independent model set', flush=True)
oring_dir = stage/'stls/oring'
oring_dir.mkdir(exist_ok=True)
oring = ex.export_models(oring_dir/'stack_manifest.json',['seal_mode="oring"'],'.')
oring_report = checked(oring_dir/'stack_manifest.json',oring_dir/'cad_verification.json')
regression = []
for label, definitions in [
    ('N1',['frame_count=1','electrode_count=1']),
    ('N4',['frame_count=4','electrode_count=4']),
    ('N6',['frame_count=6','electrode_count=6']),
    ('FKM',['gasket_material="FKM"']),
    ('PTFE',['gasket_material="PTFE"']),
]:
    folder = stage/'regression'/label
    folder.mkdir(parents=True,exist_ok=True)
    print('Regression '+label, flush=True)
    m = ex.export_models(folder/'stack_manifest.json',definitions)
    report = checked(folder/'stack_manifest.json',folder/'cad_verification.json')
    regression.append({'name':label,'pass':report['pass'],'instance_count':len(m['instances']),
                       'derived':m['derived'],'checks':report['checks']})

invalid = []
for label, definitions in [
    ('zero frames',['frame_count=0']),
    ('unequal electrodes',['electrode_count=2']),
    ('invalid seal',['seal_mode="bad"']),
    ('PTFE O-ring',['gasket_material="PTFE"','seal_mode="oring"']),
    ('zero axial clearance',['nest_rabbet_d_mm=1.2']),
    ('thin structural wall',['nest_radial_clearance_mm=0.5']),
    ('slot cuts sealing land',['tab_slot_start_y_mm=34.5']),
    ('wrong tab side clearance',['tab_channel_clearance_mm=0.1']),
]:
    try:
        ex.echo_records(definitions)
    except RuntimeError as exc:
        if 'Assertion' not in str(exc):
            raise
        invalid.append({'name':label,'pass':True,'assert_message':str(exc).splitlines()[1]})
    else:
        raise RuntimeError('Invalid input did not assert: '+label)

# Same inputs: repeat every default mesh and manifest in a second clean directory.
repeat_dir = stage/'reproduce'
repeat_dir.mkdir(exist_ok=True)
repeat = ex.export_models(repeat_dir/'stack_manifest.json')
repro = {'manifest_equal':ex.sha(stage/'stack_manifest.json')==ex.sha(repeat_dir/'stack_manifest.json'),
         'stl_hashes_equal':all(default['files'][k]['sha256']==repeat['files'][k]['sha256'] for k in default['files'])}
if not all(repro.values()):
    raise RuntimeError('Non-reproducible default export: '+str(repro))

# Persist every fresh suite result before the render/publication gate. A failed
# geometry check must remain reviewable even on a host without an X/OpenGL view.
default_report.update(regressions=regression,
    oring={'pass':oring_report['pass'],'report':'stls/oring/cad_verification.json'},
    invalid_inputs=invalid,reproducibility=repro)
ex.write_json(stage/'renders/cad_verification.json',default_report)
failed_suites = [name for name, report in [('default',default_report),('oring',oring_report)] if not report['pass']]
failed_suites += [r['name'] for r in regression if not r['pass']]
if failed_suites:
    raise RuntimeError('Publication blocked by failed CAD suites: '+', '.join(failed_suites))

# Deterministic orthographic fit in both screen axes using the actual manifest
# bboxes. OpenSCAD's orthographic vertical FOV is 22.5 degrees. The gimbal
# view matrix is Rx(-x) Ry(-y) Rz(-z); no GUI camera state or fixed distance.
def render(name, part, angle, size=(1600,1200)):
    if part in ['tab_fit_left','tab_fit_right']:
        number=1 if part.endswith('left') else 2
        group=default['groups']['tab_fit_'+str(number)]
        boxes=np.array([r['assembled_bbox_mm'] for r in default['instances'] if r['id'] in group])
        x=default['parameters']['tab_x_offsets_mm'][number-1]
        bbox=np.array([[x-10,31,boxes[:,0,2].min()],[x+10,65,boxes[:,1,2].max()]])
        fill=0.8
    elif part in ['assembly','exploded']:
        key='assembled_bbox_mm' if part=='assembly' else 'exploded_bbox_mm'
        boxes=np.array([r[key] for r in default['instances']])
        bbox=np.array([boxes[:,0].min(axis=0),boxes[:,1].max(axis=0)])
        fill=0.85 if part=='assembly' else 0.90
    else:
        bbox=np.array(default['files']['stls/'+part+'.stl']['local_bbox_mm'])
        fill=0.75
    x,y,z=-np.deg2rad(angle)
    rx=np.array([[1,0,0],[0,np.cos(x),-np.sin(x)],[0,np.sin(x),np.cos(x)]])
    ry=np.array([[np.cos(y),0,np.sin(y)],[0,1,0],[-np.sin(y),0,np.cos(y)]])
    rz=np.array([[np.cos(z),-np.sin(z),0],[np.sin(z),np.cos(z),0],[0,0,1]])
    corners=np.array([[a,b,c] for a in bbox[:,0] for b in bbox[:,1] for c in bbox[:,2]])
    extent=np.ptp(corners @ (rx @ ry @ rz).T,axis=0)
    height=max(extent[1],extent[0]/(size[0]/size[1]))/fill
    distance=height/(2*np.tan(np.deg2rad(22.5/2)))
    extra=['--imgsize='+','.join(map(str,size)), '--colorscheme=DeepOcean',
           '--projection=o','--render=CGAL',
           '--camera='+','.join(map(str,bbox.mean(axis=0)))+','+','.join(map(str,angle))+','+str(distance)]
    signature=hashlib.sha256(json.dumps([default['source_sha256'],ex.sha(ex.__file__),part,extra]).encode()).hexdigest()
    destination=stage/'renders'/name
    previous=render_cache.get(name,{})
    if destination.exists() and previous.get('input_sha256')==signature and previous.get('sha256')==ex.sha(destination):
        render_warnings[name]=previous['warnings']
        print('  reused render '+name,flush=True)
        return
    log=ex.run_scad(destination,part,extra=extra,render=True)
    header=destination.read_bytes()[:24]
    if header[:8]!=b'\x89PNG\r\n\x1a\n' or struct.unpack('>II',header[16:24])!=size:
        raise RuntimeError('Incorrect PNG dimensions: '+name)
    render_warnings[name]=[line for line in log.splitlines() if 'WARNING:' in line]
    render_cache[name]={'input_sha256':signature,'sha256':ex.sha(destination),'warnings':render_warnings[name]}
    ex.write_json(stage/'.renders.json',render_cache)
    print('  rendered '+name,flush=True)

try:
    render_cache=json.loads((stage/'.renders.json').read_text())
except (OSError,ValueError):
    render_cache={}
render_warnings={}
render('assembly.png','assembly',(125,0,145))
render('exploded.png','exploded',(0,-115,0))
render('frame_front.png','frame',(20,0,0))
render('frame_rear.png','frame',(160,0,0))
render('gasket.png','gasket',(20,0,0))
render('gasket_left_slot.png','gasket_tab_left',(20,0,0))
render('gasket_right_slot.png','gasket_tab_right',(20,0,0))
render('electrode_isolated.png','electrode_tab',(0,0,0))
render('electrode_right.png','electrode_tab_right',(0,0,0))
render('tab_fit_left.png','tab_fit_left',(55,0,15))
render('tab_fit_right.png','tab_fit_right',(55,0,-15))
render('assembly_preview.png','assembly',(125,0,145),(1200,900))
render('exploded_preview.png','exploded',(0,-115,0),(1200,900))

# Rerun hash/echo checks against the final intended artifacts before publishing.
default_report.update(regressions=regression,
    oring={'pass':oring_report['pass'],'report':'stls/oring/cad_verification.json'},
    invalid_inputs=invalid,reproducibility=repro,
    renders={'pass':True,'engine':'CGAL','projection':'orthographic',
             'files':[p.name for p in sorted((stage/'renders').glob('*.png'))],
             'warnings':render_warnings})
ex.write_json(stage/'renders/cad_verification.json',default_report)
paths = [stage/'stack_manifest.json']+sorted((stage/'stls').rglob('*.stl'))+[
    oring_dir/'stack_manifest.json',oring_dir/'cad_verification.json']+sorted((stage/'renders').iterdir())
for path in paths:
    relative = path.relative_to(stage)
    destination = root/relative
    destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(path,destination)
    print('Published '+str(relative),flush=True)
print('Scope A CAD checks and exports passed.',flush=True)
PY
