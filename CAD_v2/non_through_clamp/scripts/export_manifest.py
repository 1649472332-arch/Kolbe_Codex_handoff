#!/usr/bin/env python3
"""Strict KOLBE_V1 echo reader; no model coordinates are calculated here."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import tempfile
import struct
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
SCAD = ROOT / 'kolbe_non_through.scad'
OSC = '/usr/bin/openscad'
PARTS = ['front_endplate', 'rear_endplate', 'frame', 'gasket', 'gasket_tab_left', 'gasket_tab_right', 'electrode_tab',
         'electrode_tab_right', 'electrode_plain', 'locator_pin', 'bolt', 'washer', 'heatset_nut']
FIELDS = ['id', 'part', 'translation', 'scale', 'exploded_translation', 'exploded_scale',
          'zh', 'en', 'material', 'nominal_dims_mm', 'assembled_dims_mm', 'group',
          'sequence_index', 'hardware_index']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run_scad(output, part, defines=(), extra=(), render=False):
    cmd = [OSC, '-o', str(output), '-D', 'part=' + json.dumps(part)]
    for d in defines:
        cmd += ['-D', d]
    cmd += list(extra) + [str(SCAD)]
    if render and not os.environ.get('DISPLAY'):
        cmd = ['xvfb-run', '-a'] + cmd
    result = subprocess.run(cmd, capture_output=True, text=True)
    # OpenSCAD 2021 sometimes returns zero even after assert failure.
    warnings = [line for line in result.stderr.splitlines() if 'WARNING:' in line]
    # PNGs depict the touching multi-part assembly. Its implicit union can
    # have non-manifold contacts even though every individual STL is manifold.
    # Keep this diagnostic visible; it never exempts any part or Boolean pair.
    composite_warning = 'WARNING: Object may not be a valid 2-manifold and may need repair!'
    permitted = render and part in ['assembly','exploded','tab_fit_left','tab_fit_right'] and Path(output).suffix == '.png'
    unexpected = [w for w in warnings if not (permitted and w == composite_warning)]
    if result.returncode or 'ERROR:' in result.stderr or unexpected:
        raise RuntimeError(f'OpenSCAD failed ({part}):\n{result.stderr}')
    if warnings:
        print(part+': '+ '\n'.join(warnings), flush=True)
    if not Path(output).exists():
        raise RuntimeError(f'OpenSCAD did not create {output}: {result.stderr}')
    return result.stderr


def canonical_stl(path, layout=None):
    """Serialize every CGAL triangle unchanged, in deterministic binary order.

    Binary STL uses IEEE float32 coordinates. Cyclic vertex rotation preserves
    winding; sorting triangles removes CGAL's non-semantic traversal order.
    No welding, decimation or triangle removal is performed.
    """
    triangles = np.asarray(trimesh.load_mesh(path,process=False).triangles,dtype='<f4')
    triangles[triangles==0]=0  # canonicalize signed zero without changing geometry
    if not np.isfinite(triangles).all():
        raise ValueError('Nonfinite CGAL triangle')
    if layout is None:
        starts = [min(range(3),key=lambda j:tuple(t[j])) for t in triangles]
        rotated = np.array([np.roll(t,-j,axis=0) for t,j in zip(triangles,starts)],dtype='<f4')
        flat = rotated.reshape(-1,9)
        order = np.lexsort(tuple(flat[:,j] for j in range(8,-1,-1)))
        triangles = rotated[order]
        layout = (order,np.array(starts)[order])
    else:
        order,starts = layout
        if len(order)!=len(triangles):
            raise ValueError('O-ring correspondence changed topology')
        triangles = np.array([np.roll(triangles[i],-j,axis=0) for i,j in zip(order,starts)],dtype='<f4')
    normals = np.cross(triangles[:,1].astype(float)-triangles[:,0],
                       triangles[:,2].astype(float)-triangles[:,0])
    lengths = np.linalg.norm(normals,axis=1)
    if np.any(lengths==0):
        raise ValueError('Degenerate CGAL triangle')
    normals /= lengths[:,None]
    normals[normals==0]=0
    dtype = np.dtype([('normal','<f4',(3,)),('vertices','<f4',(3,3)),('attribute','<u2')])
    data = np.zeros(len(triangles),dtype=dtype)
    data['normal'],data['vertices'] = normals,triangles
    header = b'KOLBE CGAL; all source triangles; stable cyclic vertex and facet order'.ljust(80,b' ')
    Path(path).write_bytes(header+struct.pack('<I',len(triangles))+data.tobytes())
    return layout


def echo_records(defines=()):
    with tempfile.TemporaryDirectory(prefix='kolbe-echo-') as tmp:
        log = run_scad(Path(tmp) / 'manifest.csg', 'manifest', defines)
    records = []
    for line in log.splitlines():
        if line.startswith('ECHO: '):
            value = json.loads(line[6:])
            if len(value) != 3 or value[0] != 'KOLBE_V1':
                raise ValueError('Unexpected echo record')
            records.append(value[1:])
    if not records:
        raise ValueError('No manifest echo records')
    return records


def write_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n')
    temporary.replace(path)


def make_manifest(out, defines=(), stl_dir='stls'):
    out = Path(out)
    records = echo_records(defines)
    params, derived, instances = {}, {}, []
    for typ, payload in records:
        if typ in ['parameter', 'derived']:
            target = params if typ == 'parameter' else derived
            if payload[0] in target:
                raise ValueError('Duplicate field')
            target[payload[0]] = payload[1]
        elif typ == 'instance':
            if len(payload) != len(FIELDS):
                raise ValueError('Missing instance fields')
            r = dict(zip(FIELDS, payload))
            r['display_name'] = {'zh': r.pop('zh'), 'en': r.pop('en')}
            for key in ['sequence_index', 'hardware_index']:
                if r[key] == -1:
                    r[key] = None
            r.update(rotation_deg=[0, 0, 0], mirror=[False]*3,
                     exploded_rotation_deg=[0, 0, 0])
            r['stl'] = (Path(stl_dir) / (r['part'] + '.stl')).as_posix()
            if r['part'].startswith('electrode'):
                r['active_pad_dims_mm'] = [params[f'electrode_{a}_mm'] for a in ['w', 'h', 't']]
                r['central_pad_support'] = 'integral broad lateral lands -> clamped perimeter flange -> single offset tab'
                r['central_pad_connected_to_tab'] = True
                number = int(r['id'].split('_')[-1])
                r['adjacent_gaskets'] = [f'gasket_{2*number}',f'gasket_{2*number+1}']
            if r['part'].startswith('gasket_tab_'):
                r['tab_slot_x_mm'] = params['tab_x_offsets_mm'][0 if r['part'].endswith('left') else 1]
                r['tab_slot_through_thickness'] = True
            if r['part'] == 'gasket_oring':
                r['compressed_stl'] = (Path(stl_dir) / 'gasket_oring_compressed.stl').as_posix()
                r['deformation'] = {'type': 'corresponding_vertices', 'assembled': 'compressed_stl',
                                    'exploded': 'stl', 'centerline_fixed': True}
            instances.append(r)
        else:
            raise ValueError('Unknown record type ' + typ)
    expected = 4*params['frame_count'] + 29
    if len(instances) != expected or len({r['id'] for r in instances}) != expected:
        raise ValueError('Missing/duplicate instances')
    names = PARTS + (['gasket_oring', 'gasket_oring_compressed'] if params['seal_mode'] == 'oring' else [])
    files = {}
    meshes = {}
    for name in names:
        rel = (Path(stl_dir) / (name + '.stl')).as_posix()
        mesh = trimesh.load_mesh(out.parent / rel, process=True)
        meshes[rel] = mesh
        files[rel] = {'sha256': sha(out.parent / rel), 'local_bbox_mm': mesh.bounds.tolist(),
                      'triangles': len(mesh.faces), 'vertices': len(mesh.vertices),
                      'components': len(mesh.split(only_watertight=False)),
                      'volume_mm3': float(mesh.volume)}
    for r in instances:
        for state, output_key in [('assembled', 'assembled_bbox_mm'), ('exploded', 'exploded_bbox_mm')]:
            assembled = state == 'assembled'
            mesh = meshes[r.get('compressed_stl', r['stl']) if assembled else r['stl']]
            scale = r['scale'] if assembled else r['exploded_scale']
            translation = r['translation'] if assembled else r['exploded_translation']
            r[output_key] = (mesh.bounds * scale + translation).tolist()
        r['local_bbox_mm'] = files[r['stl']]['local_bbox_mm']
    params['part'] = 'manifest'
    manifest = {'schema_version': 1, 'units': 'mm', 'axis': {'stack': '+Z', 'up': '+Y'},
                'parameters': params, 'derived': derived, 'source_sha256': sha(SCAD),
                'seal_mode': params['seal_mode'], 'gasket_material': params['gasket_material'],
                'exploded_gap_mm': params['explode_gap_mm'], 'files': files, 'instances': instances,
                'electrode_design': {'central_upper_lower_bridge_count': 0, 'components_per_stl': 1,
                                     'central_pad_supported': True, 'central_pad_connected_to_tab': True,
                                     'support_scheme': 'one-piece broad lateral lands and perimeter flange; flange clamped between seals',
                                     'lateral_land_height_mm': params['electrode_land_h_mm'],
                                     'manufacturing_status': 'geometrically continuous one-piece metal blank; strength, contact resistance, coating and sealing remain unqualified'},
                'tab_clearance': {'width_mm': derived['tab_slot_w_mm'], 'per_side_mm': params['tab_channel_clearance_mm'],
                                  'start_y_mm': params['tab_slot_start_y_mm'], 'open_to': '+Y exterior',
                                  'flat_gaskets': 'G1 intact; G2/G3 -> E1; G4/G5 -> E2; etc.; full Z cuts in dry land only',
                                  'oring_compatible': True, 'oring_reason': 'closed ring and 1.8 mm groove end below slot root, with measured dry-land clearance',
                                  'groove_outer_margin_mm': derived['tab_slot_seal_margin_mm']},
                'groups': {g: [r['id'] for r in instances if r['group'] == g]
                           for g in ['stack', 'bolts', 'washers', 'heatsets', 'locators']},
                'tools': {'openscad': subprocess.run([OSC, '--version'], capture_output=True, text=True).stderr.strip(),
                          'python': platform.python_version(),
                          **{n: importlib.metadata.version(n) for n in ['numpy', 'trimesh', 'manifold3d']}}}
    for n in range(1,params['frame_count']+1):
        manifest['groups']['tab_fit_'+str(n)] = [f'frame_{n}',f'gasket_{2*n}',f'electrode_{n}',f'gasket_{2*n+1}',
                                                f'frame_{n+1}' if n<params['frame_count'] else 'rear_endplate']
    write_json(out, manifest)
    return manifest


def export_models(out, defines=(), stl_dir='stls'):
    """Resume completed assets by input/file hash; cap CGAL concurrency at three."""
    out = Path(out)
    folder = out.parent / stl_dir
    folder.mkdir(parents=True, exist_ok=True)
    params = dict(payload for typ, payload in echo_records(defines) if typ == 'parameter')
    names = PARTS + (['gasket_oring', 'gasket_oring_compressed'] if params['seal_mode'] == 'oring' else [])
    versions = [importlib.metadata.version(n) for n in ['numpy','trimesh','manifold3d']]
    versions += [subprocess.run([OSC,'--version'],capture_output=True,text=True).stderr.strip()]
    key = hashlib.sha256(json.dumps([sha(SCAD),sha(__file__),params,versions],sort_keys=True).encode()).hexdigest()
    checkpoint = folder/'.exports.json'
    try:
        saved = json.loads(checkpoint.read_text())
    except (OSError,ValueError):
        saved = {}
    if saved.get('input_sha256') != key:
        saved = {'input_sha256':key,'files':{}}

    def valid(name):
        path = folder/(name+'.stl')
        return path.exists() and saved['files'].get(name)==sha(path)

    def remember(name):
        saved['files'][name] = sha(folder/(name+'.stl'))
        write_json(checkpoint,saved)
        print('  exported '+folder.name+'/'+name,flush=True)

    def export_one(name,layout=None):
        selector = 'electrode_tab' if name=='electrode_tab_right' else name
        overrides = list(defines)
        if name=='electrode_tab_right':
            overrides += ['tab_offset_mm='+str(params['tab_x_offsets_mm'][1])]
        path = folder/(name+'.stl')
        run_scad(path,selector,overrides)
        return canonical_stl(path,layout)

    heavy = ['front_endplate','rear_endplate','frame']
    with ThreadPoolExecutor(max_workers=3) as pool:
        pending = {pool.submit(export_one,name):name for name in heavy if not valid(name)}
        for future in as_completed(pending):
            future.result()
            remember(pending[future])
    ring_layout = None
    for name in names:
        if name in heavy:
            continue
        # A partial O-ring pair needs the free state's permutation again.
        force = name=='gasket_oring' and not valid('gasket_oring_compressed')
        if valid(name) and not force:
            print('  reused '+folder.name+'/'+name,flush=True)
            continue
        layout = export_one(name,ring_layout if name=='gasket_oring_compressed' else None)
        if name=='gasket_oring':
            ring_layout = layout
        remember(name)
    return make_manifest(out,defines,stl_dir)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', default='stack_manifest.json')
    ap.add_argument('--stl-dir', default='stls')
    ap.add_argument('--define', action='append', default=[])
    ap.add_argument('--export-stls', action='store_true')
    args = ap.parse_args()
    (export_models if args.export_stls else make_manifest)(args.out, args.define, args.stl_dir)
