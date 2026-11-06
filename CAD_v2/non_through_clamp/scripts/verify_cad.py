#!/usr/bin/env python3
"""Mesh, section and manifold Boolean audits for PLAN.md Scope A.

Only the two local front-plate press-fit regions may overlap. No frame,
seal, electrode or hardware pair is exempted from Boolean checking.
"""
import argparse
import itertools
import json
from pathlib import Path
import sys
import traceback
import numpy as np
import trimesh
import manifold3d as mf
from export_manifest import SCAD, echo_records, sha, write_json

LENGTH_TOL = 0.02
VOLUME_TOL = 0.01


def solid(mesh):
    value = mf.Manifold(mf.Mesh64(np.asarray(mesh.vertices, dtype=np.float64),
                                np.asarray(mesh.faces, dtype=np.uint64)))
    if value.status() != mf.Error.NoError:
        raise ValueError('manifold input error: ' + str(value.status()))
    return value


def cylinder(d, h, pos=(0, 0, 0)):
    # Match the source $fn=96 angular stations; avoid false thin slivers
    # from a denser, differently inscribed circular probe.
    return mf.Manifold.cylinder(h, d/2, circular_segments=96).translate(pos)


def box(size, pos):
    return mf.Manifold.cube(size).translate(pos)


def bounds(s):
    return np.array(s.bounding_box()).reshape(2, 3)


def section_hits(s, z, axis, other):
    """All boundary coordinates on an actual mesh cross section."""
    hits = []
    for poly in s.slice(z).to_polygons():
        poly = np.asarray(poly)
        for a, b in zip(poly, np.roll(poly, -1, axis=0)):
            j = 1-axis
            if (a[j] <= other < b[j]) or (b[j] <= other < a[j]):
                hits.append(float(a[axis]+(other-a[j])*(b[axis]-a[axis])/(b[j]-a[j])))
    return sorted(hits)


def inside_xy(s, z, point):
    hits = section_hits(s, z, 0, point[1])
    return sum(x > point[0] for x in hits) % 2 == 1


def rr_points(w, h, r, n=48):
    points = []
    for q in range(4):
        center = [(1 if q in [0, 3] else -1)*(w/2-r),
                  (1 if q < 2 else -1)*(h/2-r)]
        for j in range(n+1):
            a = np.deg2rad(q*90+j*90/n)
            points.append([center[0]+r*np.cos(a), center[1]+r*np.sin(a)])
    return points


def band(w, h, r, width, depth):
    outer = mf.CrossSection([rr_points(w+width, h+width, r+width/2)])
    inner = mf.CrossSection([rr_points(w-width, h-width, r-width/2)])
    return (outer-inner).extrude(depth)


class Audit:
    def __init__(self, manifest):
        self.path = Path(manifest).resolve()
        self.m = json.loads(self.path.read_text())
        self.p, self.d = self.m['parameters'], self.m['derived']
        self.results = []
        self.meshes, self.local, self.world = {}, {}, {}
        self.records = {r['id']: r for r in self.m['instances']}

    def check(self, name, ok, **details):
        self.results.append({'check': name, 'pass': bool(ok), **details})
        if not ok:
            print('FAIL:', name, details, flush=True)

    def near(self, name, actual, expected, tol=LENGTH_TOL):
        self.check(name, np.all(np.abs(np.asarray(actual)-expected) <= tol),
                   actual=np.asarray(actual).tolist(), expected=np.asarray(expected).tolist())

    def file_for(self, part):
        return next(k for k in self.m['files'] if Path(k).stem == part)

    def get(self, part):
        return self.local[self.file_for(part)]

    def run(self):
        self.integrity()
        self.instances()
        self.interference()
        self.nesting()
        self.seals_and_electrodes()
        self.tab_clearances()
        self.fasteners_and_pins()
        self.polarity()
        return {'pass': all(r['pass'] for r in self.results), 'schema_version': 1,
                'source_sha256': self.m['source_sha256'], 'tools': self.m['tools'],
                'configuration': {k: self.p[k] for k in ['frame_count', 'seal_mode', 'gasket_material']},
                'tolerances': {'length_mm': LENGTH_TOL, 'bbox_mm': LENGTH_TOL, 'volume_mm3': VOLUME_TOL},
                'instance_count': len(self.records), 'checks': self.results,
                'electrode_support': 'modeled: integral 25 mm lateral lands and clamped perimeter flange; mechanical/electrical ratings unvalidated',
                'physical_validation': 'not_run: pressure, loads, chemistry, insulation, creep and service life'}

    def integrity(self):
        self.check('source hash', sha(SCAD) == self.m['source_sha256'])
        for rel, info in self.m['files'].items():
            path = self.path.parent / rel
            mesh = trimesh.load_mesh(path, process=True)
            self.meshes[rel], self.local[rel] = mesh, solid(mesh)
            edge_counts = np.bincount(mesh.edges_unique_inverse)
            components = mesh.split(only_watertight=False)
            expected_components = 1
            self.check('mesh '+rel, sha(path) == info['sha256'] and
                       np.isfinite(mesh.vertices).all() and mesh.volume > 0 and
                       mesh.is_watertight and mesh.is_winding_consistent and
                       np.all(edge_counts == 2) and np.all(mesh.area_faces > 1e-12) and
                       len(components) == expected_components and
                       all(c.is_watertight and c.is_winding_consistent and c.volume > 0 for c in components),
                       triangles=len(mesh.faces), volume_mm3=float(mesh.volume),
                       components=len(components), expected_components=expected_components)
            self.near('local bbox '+rel, mesh.bounds, info['local_bbox_mm'])
        # Compare echo records with parsed fields using precisely the stored parameters.
        defines = [k+'='+json.dumps(v) for k, v in self.p.items() if k != 'part']
        echoed = echo_records(defines)
        echoed_instances = [v for t, v in echoed if t == 'instance']
        self.check('echo ids and transforms', len(echoed_instances) == len(self.records) and
                   all(v[0] in self.records and np.allclose(v[2], self.records[v[0]]['translation'], atol=1e-5)
                       and np.allclose(v[4], self.records[v[0]]['exploded_translation'], atol=1e-5)
                       for v in echoed_instances))

        radius = max(self.p['endplate_corner_r_mm'],self.p['port_boss_od_mm']/2,
                     self.p['washer_od_mm']/2,self.d['seal_cl_r'])
        chord_error = radius*(1-np.cos(np.pi/self.p['$fn']))
        self.check('circle chord error',chord_error<LENGTH_TOL,max_mm=float(chord_error))
        p,d = self.p,self.d
        expected = {
            'front_endplate': [[-p['endplate_w_mm']/2,-p['endplate_h_mm']/2,-p['port_boss_h_mm']],
                              [p['endplate_w_mm']/2,p['endplate_h_mm']/2,d['front_bbox_max_z']]],
            'rear_endplate': [[-p['endplate_w_mm']/2,-p['endplate_h_mm']/2,0],
                             [p['endplate_w_mm']/2,p['endplate_h_mm']/2,p['endplate_t_mm']]],
            'frame': [[-p['frame_w_mm']/2,-p['frame_h_mm']/2,0],
                      [p['frame_w_mm']/2,p['frame_h_mm']/2,d['frame_bbox_h']]],
            'locator_pin': [[-p['locator_d_mm']/2,-p['locator_d_mm']/2,0],
                            [p['locator_d_mm']/2,p['locator_d_mm']/2,d['locator_len_mm']]],
            'bolt': [[-p['bolt_head_d_mm']/2,-p['bolt_head_d_mm']/2,-p['bolt_head_h_mm']],
                     [p['bolt_head_d_mm']/2,p['bolt_head_d_mm']/2,d['bolt_length_mm']]],
            'washer': [[-p['washer_od_mm']/2,-p['washer_od_mm']/2,0],
                       [p['washer_od_mm']/2,p['washer_od_mm']/2,p['washer_t_mm']]],
            'heatset_nut': [[-p['heatset_od_mm']/2,-p['heatset_od_mm']/2,0],
                           [p['heatset_od_mm']/2,p['heatset_od_mm']/2,p['heatset_depth_mm']]],
        }
        for name in ['electrode_tab','electrode_tab_right','electrode_plain']:
            expected[name]=[[-p['electrode_flange_w_mm']/2,-p['electrode_flange_h_mm']/2,0],
                            [p['electrode_flange_w_mm']/2,p['electrode_flange_h_mm']/2 if name=='electrode_plain' else d['tab_end_y'],p['electrode_t_mm']]]
        if p['seal_mode']=='flat_gasket':
            expected['gasket']=[[-p['gasket_w_mm']/2,-p['gasket_h_mm']/2,0],
                                [p['gasket_w_mm']/2,p['gasket_h_mm']/2,p['gasket_t_mm']]]
        for name,bbox in expected.items():
            self.near('parameter-contract bbox '+name,bounds(self.get(name)),bbox)

    def instances(self):
        n, p, d = self.p['frame_count'], self.p, self.d
        self.check('instance count and unique ids', len(self.records) == 4*n+29 and
                   len(self.m['instances']) == len(self.records))
        expected = {'frame': n, 'electrode_tab': n, 'gasket': 2*n+1,
                    'front_endplate': 1, 'rear_endplate': 1, 'bolt': 8,
                    'washer': 8, 'heatset_nut': 8, 'locator_pin': 2}
        counts = {k: 0 for k in expected}
        for r in self.records.values():
            k = r['part'].replace('electrode_tab_right', 'electrode_tab').replace('gasket_oring', 'gasket')
            if k.startswith('gasket_tab_'): k = 'gasket'
            counts[k] += 1
            rel = r.get('compressed_stl', r['stl'])
            self.world[r['id']] = self.local[rel].scale(r['scale']).translate(r['translation'])
            self.near('assembled bbox '+r['id'], bounds(self.world[r['id']]), r['assembled_bbox_mm'])
            exp = self.local[r['stl']].scale(r['exploded_scale']).translate(r['exploded_translation'])
            self.near('exploded bbox '+r['id'], bounds(exp), r['exploded_bbox_mm'])
        self.check('part counts', counts == expected, actual=counts, expected=expected)
        chain = sorted((r for r in self.records.values() if r['group'] == 'stack'), key=lambda r:r['sequence_index'])
        self.chain = chain
        t = d['seal_gap']
        self.near('active chain', d['active_stack_t'], n*(p['frame_t_mm']+p['electrode_t_mm'])+(2*n+1)*t)
        self.near('total chain', d['total_stack_t'], 2*p['endplate_t_mm']+d['active_stack_t'])
        for i in range(n):
            f, e = self.records[f'frame_{i+1}'], self.records[f'electrode_{i+1}']
            fz = p['endplate_t_mm']+t+i*(p['frame_t_mm']+p['electrode_t_mm']+2*t)
            self.near('frame body position '+str(i+1), f['translation'][2], fz)
            self.near('electrode body position '+str(i+1), e['translation'], [0,0,fz+p['frame_t_mm']+t])
        # Actual free bboxes determine the exploded clearances, including both dowels.
        ordered = [chain[0]]+[self.records['locator_pin_1'], self.records['locator_pin_2']]+chain[1:]
        for a, b in zip(ordered, ordered[1:]):
            self.near('exploded gap '+a['id']+'/'+b['id'], b['exploded_bbox_mm'][0][2]-a['exploded_bbox_mm'][1][2], p['explode_gap_mm'])
        if n == 3 and p['seal_mode'] == 'flat_gasket' and p['gasket_material'] in ['EPDM','FKM']:
            self.near('PLAN default stack Z table', [r['translation'][2] for r in chain],
                      [0,20,20.6,24.6,25.2,26.2,26.8,30.8,31.4,32.4,33,37,37.6,38.6,39.2])
            self.near('PLAN default exploded Z table', [r['exploded_translation'][2] for r in chain],
                      [0,123.8,138.6,160,174.8,189.8,204.6,226,240.8,255.8,270.6,292,306.8,321.8,336.6])
            bbox = np.array([bounds(s) for s in self.world.values()])
            self.near('PLAN overall bbox', [bbox[:,0].min(axis=0),bbox[:,1].max(axis=0)], [[-56,-60,-8],[56,64.5,59.2]])

    def interference(self):
        checked, raw_press = 0, []
        for aid, bid in itertools.combinations(self.world, 2):
            a, b = self.world[aid], self.world[bid]
            ab, bb = bounds(a), bounds(b)
            if np.any(np.minimum(ab[1],bb[1])-np.maximum(ab[0],bb[0]) <= 1e-7):
                continue
            checked += 1
            intersection = a ^ b
            volume = max(0., intersection.volume())
            remainder = volume
            if 'front_endplate' in [aid,bid] and (aid.startswith('locator_pin_') or bid.startswith('locator_pin_')):
                pin_id = aid if aid.startswith('locator_pin_') else bid
                r = self.records[pin_id]
                allowed = cylinder(self.p['locator_d_mm'], self.p['locator_press_depth_mm'], r['translation'])
                remainder = max(0., (intersection-allowed).volume())
                raw_press.append({'pair':[aid,bid], 'raw_volume_mm3':volume, 'outside_allowed_region_mm3':remainder})
            self.check('interference '+aid+'/'+bid, remainder <= VOLUME_TOL,
                       raw_volume_mm3=volume, forbidden_volume_mm3=remainder)
        self.check('front press fits measured', len(raw_press)==2 and all(x['raw_volume_mm3']>0 for x in raw_press), regions=raw_press)
        self.check('all-pairs Boolean completed', checked>0,
                   total_pairs=len(self.world)*(len(self.world)-1)//2, broadphase_candidates=checked)

    def nesting(self):
        p, d = self.p, self.d
        receiving = self.get('frame')
        # Measure inner/outer straight faces, rounded rail end, and channel edges.
        measurements = []
        samples = [(0,0,p['nest_side_x_mm']-p['nest_lip_w_mm']/2,-1),
                   (0,0,p['nest_side_x_mm']+p['nest_lip_w_mm']/2,1),
                   (1,p['nest_side_x_mm'],p['nest_side_len_mm']/2,1),
                   (1,0,-p['nest_end_y_mm']-p['nest_lip_w_mm']/2,-1),
                   (0,-p['nest_end_y_mm'],p['nest_end_len_mm']/2,1),
                   (0,p['nest_end_y_mm'],p['nest_end_len_mm']/2,1)]
        # Rail end centerline enters the semicircular end radius at a tangent;
        # sample a nearby parallel ray to avoid degenerate coincident edges.
        for axis, other, nominal, direction in samples:
            male_hits = section_hits(self.get('frame'), d['frame_stop_h']+p['frame_t_mm']+0.4, axis, other)
            female_hits = section_hits(receiving, 0.6, axis, other)
            male = min(male_hits, key=lambda v:abs(v-nominal))
            target = nominal+direction*p['nest_radial_clearance_mm']
            female = min(female_hits, key=lambda v:abs(v-target))
            gap = direction*(female-male)
            measurements.append({'axis':axis,'other':other,'male':male,'female':female,'gap_mm':gap})
            self.near('measured rabbet gap '+str(len(measurements)), gap, p['nest_radial_clearance_mm'])
        self.check('rabbet offset section samples', True, measurements=measurements)
        chamfer_z = d['frame_bbox_h']-p['nest_leadin_mm']/2
        hits=section_hits(self.get('frame'),chamfer_z,0,0)
        base=p['nest_side_x_mm']+p['nest_lip_w_mm']/2
        measured=min(hits,key=lambda v:abs(v-base+p['nest_leadin_mm']/2))
        self.near('45 degree male lead-in',measured,base-p['nest_leadin_mm']/2,0.001)
        male_profile = self.get('frame').slice(d['frame_stop_h']+p['frame_t_mm']+0.4)
        expected_profile = male_profile.offset(p['nest_radial_clearance_mm'], circular_segments=p['$fn'])
        # Through-open tab exits intentionally have no female end wall. Their
        # 0.3-per-side clearance is measured independently in tab_clearances().
        for x in p['tab_x_offsets_mm']:
            expected_profile -= box([d['tab_slot_w_mm'],20,1],
                                    [x-d['tab_slot_w_mm']/2,p['tab_slot_start_y_mm'],0]).slice(0.5)
        groove_profile = receiving.slice(p['frame_t_mm']/2)-receiving.slice(0.6)
        difference = (expected_profile-groove_profile).area()+(groove_profile-expected_profile).area()
        self.check('whole rabbet offset profile',difference<0.05,symmetric_difference_mm2=difference,
                   excluded='two through-open tab exits, separately verified at 0.3 mm per side')
        for name in ['frame','rear_endplate']:
            s = self.get(name)
            probe = [p['nest_side_x_mm'], 0]
            self.check('rabbet bottom '+name,
                       not inside_xy(s,p['nest_rabbet_d_mm']-0.005,probe) and
                       inside_xy(s,p['nest_rabbet_d_mm']+0.005,probe))
        side_hits = section_hits(receiving,0.6,0,0)
        end_hits = section_hits(receiving,0.6,1,0)
        side_wall = side_hits[-1]-side_hits[-2]
        end_wall = end_hits[-1]-end_hits[-2]
        self.check('measured structural walls', min(side_wall,end_wall)>=p['min_structural_wall_mm']-1e-5,
                   side_mm=side_wall,end_mm=end_wall)
        # Mouth flare is evaluated just inside z=0 to avoid coincident surfaces.
        mouths = [section_hits(receiving,0.0001,0,0), section_hits(receiving,0.0001,1,0)]
        mouth_walls = [h[-1]-h[-2] for h in mouths]
        self.check('measured mouth walls', min(mouth_walls)>=0.7-0.001, walls_mm=mouth_walls)
        pairs = [('front_endplate','frame_1')]+[(f'frame_{i}', f'frame_{i+1}' if i<p['frame_count'] else 'rear_endplate') for i in range(1,p['frame_count']+1)]
        for a, b in pairs:
            ar, br = self.records[a], self.records[b]
            body_t = p['endplate_t_mm'] if a=='front_endplate' else p['frame_t_mm']
            stop_h = d['front_stop_h'] if a=='front_endplate' else d['frame_stop_h']
            shoulder_top = ar['translation'][2]+body_t+stop_h
            self.near('shoulder plane '+a, shoulder_top, br['translation'][2])
            self.near('axial bottom clearance '+a, br['translation'][2]+p['nest_rabbet_d_mm']-bounds(self.world[a])[1,2], d['nest_axial_gap'])
            contact = self.world[a].slice(shoulder_top-0.001) ^ self.world[b].slice(shoulder_top+0.001)
            self.check('hard-stop contact '+a, contact.area()>1, area_mm2=contact.area())
            v = (self.world[a] ^ self.world[b].translate([0,0,-0.05])).volume()
            self.check('hard-stop shift collision '+a, v>VOLUME_TOL and d['nest_axial_gap']>0.05, volume_mm3=v)

    def seals_and_electrodes(self):
        p, d = self.p, self.d
        seal_band = band(d['seal_cl_w'],d['seal_cl_h'],d['seal_cl_r'],1.6,0.01)
        for idx, r in enumerate(self.chain):
            if not r['id'].startswith('gasket_'):
                continue
            previous, following = self.chain[idx-1], self.chain[idx+1]
            prev_t = p['endplate_t_mm'] if previous['part']=='front_endplate' else p['frame_t_mm'] if previous['part']=='frame' else p['electrode_t_mm']
            low = previous['translation'][2]+prev_t
            high = following['translation'][2]
            self.near('actual interface gap '+r['id'], high-low, d['seal_gap'])
            sb = bounds(self.world[r['id']])
            if p['seal_mode']=='flat_gasket':
                self.near('compressed seal thickness '+r['id'], sb[1,2]-sb[0,2], d['gasket_compressed_t'])
                self.near('free seal thickness '+r['id'], np.diff(np.array(r['local_bbox_mm'])[:,2])[0], p['gasket_t_mm'])
                self.near('compression ratio '+r['id'], 1-(sb[1,2]-sb[0,2])/p['gasket_t_mm'],p['gasket_compression_ratio'],0.0001)
                for sid, z in [(r['id'],low+0.1),(previous['id'],low-0.02),(following['id'],high+0.01)]:
                    missing = (seal_band.translate([0,0,z])-self.world[sid]).volume()
                    self.check('continuous seal +/-0.8 '+r['id']+'/'+sid,missing<=VOLUME_TOL,missing_volume_mm3=max(0.,missing))
            else:
                self.near('oring compressed height '+r['id'],sb[1,2]-sb[0,2],d['oring_compressed_h'])
                self.near('oring area conservation', d['oring_compressed_h']*d['oring_compressed_w'],p['oring_cs_mm']**2,0.00001)
                groove_on_upper = int(r['id'].split('_')[-1])%2==1
                groove_z = high+0.01 if groove_on_upper else low-0.02
                owner = self.world[following['id'] if groove_on_upper else previous['id']]
                self.check('oring single groove '+r['id'], (seal_band.translate([0,0,groove_z]) ^ owner).volume()<=VOLUME_TOL)
        if p['seal_mode']=='oring':
            free = self.meshes[self.file_for('gasket_oring')]
            compressed = self.meshes[self.file_for('gasket_oring_compressed')]
            # OpenSCAD polyhedron exports preserve face order and vertex correspondence
            # in raw ASCII STL; compare triangle-soup index positions after inversion.
            a = trimesh.load_mesh(self.path.parent/self.file_for('gasket_oring'),process=False).triangles
            b = trimesh.load_mesh(self.path.parent/self.file_for('gasket_oring_compressed'),process=False).triangles
            core_extent = np.array([d['seal_cl_w']/2-d['seal_cl_r'],d['seal_cl_h']/2-d['seal_cl_r']])
            xy = a[:,:,:2]
            core = np.clip(xy,-core_extent,core_extent)
            unit = xy-core
            unit /= np.linalg.norm(unit,axis=2)[:,:,None]
            centerline = core+unit*d['seal_cl_r']
            expected = a.copy()
            expected[:,:,:2] = centerline+(xy-centerline)*d['oring_compressed_w']/p['oring_cs_mm']
            expected[:,:,2] *= d['oring_compressed_h']/p['oring_cs_mm']
            error = float(np.max(np.abs(expected-b))) if a.shape==b.shape else float('inf')
            self.check('oring equal topology and corresponding vertices',a.shape==b.shape and error<0.002,
                       triangles=len(a),max_correspondence_error_mm=error)
            self.near('oring free bbox',free.extents,[d['seal_cl_w']+p['oring_cs_mm'],d['seal_cl_h']+p['oring_cs_mm'],p['oring_cs_mm']])
            self.near('oring compressed bbox',compressed.extents,[d['seal_cl_w']+d['oring_compressed_w'],d['seal_cl_h']+d['oring_compressed_w'],d['oring_compressed_h']])
        # One-piece metal continuity is required; the historical central bridges
        # stay empty. Broad side lands carry pad -> clamped flange -> offset tab.
        thickness = p['electrode_t_mm']
        pad = mf.CrossSection([rr_points(p['electrode_w_mm'],p['electrode_h_mm'],
                                        p['electrode_corner_r_mm'],n=24)]).extrude(thickness)
        for name in ['electrode_tab','electrode_tab_right','electrode_plain']:
            local = self.get(name)
            components = self.meshes[self.file_for(name)].split(only_watertight=False)
            self.check('one-piece supported pad '+name,len(components)==1 and (pad-local).volume()<=VOLUME_TOL,
                       components=len(components),support='broad lateral lands to perimeter flange')
            land = box([p['window_w_mm']+2*p['electrode_land_overlap_mm'],p['electrode_land_h_mm'],thickness],
                       [-p['window_w_mm']/2-p['electrode_land_overlap_mm'],-p['electrode_land_h_mm']/2,0])
            self.check('full broad lateral lands '+name,(land-local).volume()<=VOLUME_TOL,
                       height_mm=p['electrode_land_h_mm'],metal_thickness_mm=thickness)
            for sign in [-1,1]:
                gap = (p['window_h_mm']-p['electrode_h_mm'])/2
                y = sign*(p['electrode_h_mm']/2+p['window_h_mm']/2)/2
                probe = box([4,gap-0.02,thickness],[-2,y-(gap-0.02)/2,0])
                volume = max(0.,(probe ^ local).volume())
                self.check('old bridge region empty '+name+'/'+str(sign),
                           not inside_xy(local,thickness/2,[0,y]) and volume<=VOLUME_TOL,
                           center_mm=[0,y,thickness/2],volume_mm3=volume)
                # A through-flow path at each original port position remains open.
                flow = cylinder(p['port_through_d_mm'],thickness,[p['port_x_mm'],sign*p['port_y_mm'],0])
                self.check('electrode fluid bypass '+name+'/'+str(sign),(flow ^ local).volume()<=VOLUME_TOL)
            if name!='electrode_plain':
                x = p['tab_x_offsets_mm'][1] if name.endswith('_right') else p['tab_offset_mm']
                tab = box([p['tab_w_mm'],p['tab_len_mm']-p['tab_hole_offset_mm']-p['tab_hole_d_mm'],thickness],
                          [x-p['tab_w_mm']/2,d['tab_start_y'],0])
                self.check('integral tab to pad '+name,len(components)==1 and (tab-local).volume()<=VOLUME_TOL and
                           inside_xy(local,thickness/2,[x,d['tab_end_y']-1]),tab_x_mm=x)
        for i in range(1,p['frame_count']+1):
            r = self.records[f'electrode_{i}']; s = self.world[r['id']]; local = self.local[r['stl']]
            z = p['electrode_t_mm']/2
            pad_probe = box([p['electrode_w_mm']-2*p['electrode_corner_r_mm'],p['electrode_h_mm']-2*p['electrode_corner_r_mm'],0.1],[-(p['electrode_w_mm']-2*p['electrode_corner_r_mm'])/2,-(p['electrode_h_mm']-2*p['electrode_corner_r_mm'])/2,z-0.05])
            self.check('central electrode pad '+r['id'],(pad_probe-local).volume()<=VOLUME_TOL)
            self.near('electrode tab end '+r['id'],bounds(local)[1,1],d['tab_end_y'])
            x = p['tab_x_offsets_mm'][(i-1)%len(p['tab_x_offsets_mm'])]
            y = d['tab_end_y']-p['tab_hole_offset_mm']
            self.check('tab hole '+r['id'],not inside_xy(local,z,[x,y]))
            hits = section_hits(local,z,0,y)
            self.near('tab hole diameter '+r['id'],min(hits,key=lambda v:abs(v-x-p['tab_hole_d_mm']/2))-min(hits,key=lambda v:abs(v-x+p['tab_hole_d_mm']/2)),p['tab_hole_d_mm'])

    def tab_clearances(self):
        p,d = self.p,self.d
        root,width = p['tab_slot_start_y_mm'],d['tab_slot_w_mm']
        self.near('tab slot design width',width,8.6,1e-6)
        self.near('tab slot per-side allowance',(width-p['tab_w_mm'])/2,0.3,1e-6)
        self.check('slot root outside seal and window',
                   root>(d['seal_cl_h']+p['oring_groove_w_mm'])/2 and root>p['window_h_mm']/2,
                   groove_outer_margin_mm=d['tab_slot_seal_margin_mm'],
                   window_margin_mm=root-p['window_h_mm']/2)
        # Volume probes span the ENTIRE frame body, shoulder and lip, not samples
        # only. Side-wall measurements at the body and lip prove the 8.6 opening.
        for x in p['tab_x_offsets_mm']:
            opening = box([width,20,d['frame_bbox_h']], [x-width/2,root,0])
            volume = max(0.,(opening ^ self.get('frame')).volume())
            self.check('frame full-height open tab channel '+str(x),volume<=VOLUME_TOL,volume_mm3=volume)
            for label,y,z in [('body',root+0.5,p['frame_t_mm']/2),
                              ('shoulder',p['nest_end_y_mm'],p['frame_t_mm']+d['frame_stop_h']/2),
                              ('lip',p['nest_end_y_mm'],p['frame_t_mm']+d['frame_stop_h']+0.4)]:
                hits=section_hits(self.get('frame'),z,0,y)
                edges=[min(hits,key=lambda v:abs(v-x+width/2)),min(hits,key=lambda v:abs(v-x-width/2))]
                self.near('measured tab '+label+' walls '+str(x),edges,[x-width/2,x+width/2],0.001)
                self.near('measured tab '+label+' clearances '+str(x),
                          [x-p['tab_w_mm']/2-edges[0],edges[1]-x-p['tab_w_mm']/2],[0.3,0.3],0.001)
            front_opening=box([width,20,d['front_stop_h']+p['nest_lip_h_mm']],
                              [x-width/2,root,p['endplate_t_mm']])
            self.check('front stop open tab channel '+str(x),
                       (front_opening ^ self.get('front_endplate')).volume()<=VOLUME_TOL)
        if p['seal_mode']=='flat_gasket':
            # Only actual adjacent layers get a slot; G1 has no tab at its Z.
            g1=self.world['gasket_1']
            for x in p['tab_x_offsets_mm']:
                patch=box([width,0.8,d['gasket_compressed_t']],
                          [x-width/2,root+0.1,self.records['gasket_1']['translation'][2]])
                self.check('G1 intact dry land '+str(x),(patch-g1).volume()<=VOLUME_TOL)
            for name,x in [('gasket_tab_left',p['tab_x_offsets_mm'][0]),
                           ('gasket_tab_right',p['tab_x_offsets_mm'][1])]:
                local=self.get(name)
                probe=box([width,20,p['gasket_t_mm']],[x-width/2,root,0])
                self.check('free gasket full-thickness slot '+name,(probe ^ local).volume()<=VOLUME_TOL)
                # The unused mirror slot is absent, so unnecessary cuts cannot pass.
                other=box([width,0.8,p['gasket_t_mm']],[-x-width/2,root+0.1,0])
                self.check('gasket unused side intact '+name,(other-local).volume()<=VOLUME_TOL)
                for z in [0.01,p['gasket_t_mm']/2,p['gasket_t_mm']-0.01]:
                    hits=section_hits(local,z,0,root+0.5)
                    edges=[min(hits,key=lambda v:abs(v-x+width/2)),min(hits,key=lambda v:abs(v-x-width/2))]
                    self.near('gasket measured slot '+name+'/'+str(z),edges,[x-width/2,x+width/2],0.001)
        else:
            # Closed O-rings sit inside the dry slots; never cut a ring to mimic
            # a slotted flat gasket. Check free/compressed meshes AND groove bands.
            for name in ['gasket_oring','gasket_oring_compressed']:
                ring=self.get(name)
                for x in p['tab_x_offsets_mm']:
                    probe=box([width,20,p['oring_cs_mm']],[x-width/2,root,0])
                    self.check('O-ring outside dry slot '+name+'/'+str(x),(probe ^ ring).volume()<=VOLUME_TOL)
            self.check('O-ring slot compatibility',d['tab_slot_seal_margin_mm']>=0.5,
                       compatible=True,reason='closed ring/groove inside slot root; no O-ring notch',
                       groove_margin_mm=d['tab_slot_seal_margin_mm'])
        for number in range(1,p['frame_count']+1):
            r=self.records[f'electrode_{number}']
            x=p['tab_x_offsets_mm'][(number-1)%len(p['tab_x_offsets_mm'])]
            low=r['translation'][2]; high=low+p['electrode_t_mm']
            envelope=box([width,p['tab_len_mm'],p['electrode_t_mm']],
                         [x-width/2,d['tab_start_y'],low])
            collisions=[]
            for sid,other in self.world.items():
                if sid==r['id']: continue
                volume=max(0.,(envelope ^ other).volume())
                if volume>VOLUME_TOL: collisions.append({'other':sid,'volume_mm3':volume})
            self.check('handle clearance all assembled parts '+r['id'],not collisions,
                       tab_x_mm=x,z_mm=[low,high],collisions=collisions,per_side_mm=0.3)
            self.check('all three pads connected to own tab '+r['id'],
                       len(self.world[r['id']].decompose())==1 and r['part']==('electrode_tab' if x<0 else 'electrode_tab_right'),
                       tab_x_mm=x,metal_components=len(self.world[r['id']].decompose()))
            for sn,expected_z in [(2*number,low),(2*number+1,high)]:
                seal=self.records[f'gasket_{sn}']; sb=bounds(self.world[seal['id']])
                self.near('adjacent gasket meets metal plane '+seal['id'],sb[1 if sn%2==0 else 0,2],expected_z)
                if p['seal_mode']=='flat_gasket':
                    expected_part='gasket_tab_left' if x<0 else 'gasket_tab_right'
                    self.check('matched gasket tab side '+seal['id'],seal['part']==expected_part,part=seal['part'],tab_x_mm=x)
                    probe=box([width,20,sb[1,2]-sb[0,2]],[x-width/2,root,sb[0,2]])
                    volume=max(0.,(probe ^ self.world[seal['id']]).volume())
                    self.check('assembled gasket full-thickness slot '+seal['id'],volume<=VOLUME_TOL,
                               thickness_mm=sb[1,2]-sb[0,2],volume_mm3=volume)

    def fasteners_and_pins(self):
        p, d = self.p, self.d
        clearances = []
        for i, xy in enumerate(p['bolt_points'],1):
            r = self.records[f'bolt_{i}']
            self.near('bolt XY '+str(i),r['translation'][:2],xy)
            frame_gap = np.linalg.norm(np.maximum(np.abs(xy)-[p['frame_w_mm']/2,p['frame_h_mm']/2],0))-p['washer_od_mm']/2
            edge_margin = min(p['endplate_w_mm']/2-abs(xy[0]),p['endplate_h_mm']/2-abs(xy[1]))-p['washer_od_mm']/2
            tab_gaps = []
            for tx in p['tab_x_offsets_mm']:
                delta = np.maximum(np.abs(np.array(xy)-[tx,(d['tab_start_y']+d['tab_end_y'])/2])-[p['tab_w_mm']/2,p['tab_len_mm']/2],0)
                tab_gaps.append(float(np.linalg.norm(delta)-p['washer_od_mm']/2))
            boss_gap = min(np.linalg.norm(np.array(xy)-[p['port_x_mm'],s*p['port_y_mm']])-p['washer_od_mm']/2-p['port_boss_od_mm']/2 for s in [-1,1])
            self.check('conservative hardware XY clearance '+str(i),frame_gap>=2 and min(tab_gaps)>=2 and boss_gap>=2 and edge_margin>=3,
                       frame_mm=float(frame_gap),tab_mm=min(tab_gaps),boss_mm=float(boss_gap),edge_mm=float(edge_margin))
            clearances.append(float(frame_gap))
            # Actual hole sections, not just centerline/bbox tests.
            for name,z in [('front_endplate',p['endplate_t_mm']/2),('rear_endplate',(p['endplate_t_mm']-p['heatset_depth_mm'])/2)]:
                hits = section_hits(self.get(name),z,0,xy[1])
                left = min(hits,key=lambda v:abs(v-xy[0]+p['bolt_clear_d_mm']/2))
                right = min(hits,key=lambda v:abs(v-xy[0]-p['bolt_clear_d_mm']/2))
                self.near('bolt bore '+name+'/'+str(i),[left,right],[xy[0]-p['bolt_clear_d_mm']/2,xy[0]+p['bolt_clear_d_mm']/2])
            rear = self.get('rear_endplate')
            rod = cylinder(p['bolt_shank_d_mm'],p['endplate_t_mm'],[xy[0],xy[1],0])
            self.check('rear entrance-to-pocket connected '+str(i),(rod ^ rear).volume()<=VOLUME_TOL)
            tip = bounds(self.world[f'bolt_{i}'])[1,2]
            nut = bounds(self.world[f'heatset_{i}'])
            self.near('bolt engagement '+str(i),min(tip,nut[1,2])-nut[0,2],d['bolt_engagement_mm'])
            self.near('bolt tip recess '+str(i),d['total_stack_t']-tip,d['bolt_tip_recess_mm'])
            for sid, s in self.world.items():
                if sid.startswith(('frame_','gasket_','electrode_')):
                    self.check('non-through shank '+str(i)+'/'+sid,(self.world[f'bolt_{i}'] ^ s).volume()<=VOLUME_TOL)
        choices = sorted(l for l in p['bolt_standard_lengths_mm'] if min(p['heatset_depth_mm'],l-p['washer_t_mm']-d['heatset_z'])+1e-9>=p['bolt_min_engagement_mm'] and max(0,l-p['washer_t_mm']-d['total_stack_t'])<=p['bolt_max_rear_projection_mm']+1e-9)
        self.near('shortest standard bolt',d['bolt_length_mm'],choices[0])
        if p['frame_count']==3 and p['gasket_material'] in ['EPDM','FKM']:
            self.near('PLAN engagement',d['bolt_engagement_mm'],7.2)
            self.near('PLAN tip recess',d['bolt_tip_recess_mm'],0.8)
        for i,xy in enumerate(p['locator_points'],1):
            pin = self.world[f'locator_pin_{i}']; pb = bounds(pin)
            self.near('pin length '+str(i),pb[1,2]-pb[0,2],d['locator_len_mm'])
            self.near('rear pin bottom clearance '+str(i),d['rear_z']+p['locator_rear_depth_mm']-pb[1,2],d['locator_rear_clearance_mm'])
            for r in self.chain[1:-1]:
                if p['seal_mode']=='oring' and r['id'].startswith('gasket_'):
                    continue
                rb = np.array(r['assembled_bbox_mm'])
                self.check('pin traverses '+str(i)+'/'+r['id'],pb[0,2]<rb[0,2] and pb[1,2]>rb[1,2] and
                           (pin ^ self.world[r['id']]).volume()<=VOLUME_TOL)
                if r['id'].startswith('electrode_'):
                    local = self.local[r['stl']]
                    hits = section_hits(local,p['electrode_t_mm']/2,0,xy[1])
                    diameter = min(hits,key=lambda v:abs(v-xy[0]-p['electrode_pin_d_mm']/2))-min(hits,key=lambda v:abs(v-xy[0]+p['electrode_pin_d_mm']/2))
                    clearance = (diameter-p['locator_d_mm'])/2
                    self.check('electrical dowel gap '+str(i)+'/'+r['id'],clearance>=1.3-LENGTH_TOL and clearance-p['shoulder_inner_clearance_mm']>=1.0,
                               nominal_mm=clearance,worst_mm=clearance-p['shoulder_inner_clearance_mm'])
            # Steel pins must lie outside the entire closed sealing path.
            seal_outer = np.array([d['seal_cl_w'],d['seal_cl_h']])/2+p['oring_groove_w_mm']/2
            self.check('pin outside seal dry zone '+str(i),abs(xy[0])-p['locator_d_mm']/2>seal_outer[0] or abs(xy[1])-p['locator_d_mm']/2>seal_outer[1])
        front = self.get('front_endplate')
        for sign in [-1,1]:
            xy = [p['port_x_mm'],sign*p['port_y_mm']]
            bore = cylinder(p['port_through_d_mm'],p['endplate_t_mm']+p['port_boss_h_mm'],[*xy,-p['port_boss_h_mm']])
            self.check('port bore continuity '+str(sign),(bore ^ front).volume()<=VOLUME_TOL)
            for z,diam in [(-p['port_boss_h_mm']+0.1,p['port_counterbore_d_mm']),(-p['port_boss_h_mm']+p['port_counterbore_depth_mm']+0.1,p['port_through_d_mm'])]:
                h = section_hits(front,z,0,xy[1])
                self.near('port measured diameter '+str((sign,z)),[min(h,key=lambda v:abs(v+diam/2)),min(h,key=lambda v:abs(v-diam/2))],[-diam/2,diam/2])
        theta = np.arctan2(p['locator_points'][1][1]-p['locator_points'][0][1],
                           p['locator_points'][1][0]-p['locator_points'][0][0])
        along = np.array([np.cos(theta),np.sin(theta)])
        across = np.array([-along[1],along[0]])
        for name,z,diam,extra in [('frame',p['frame_t_mm']/2,p['locator_slip_d_mm'],p['locator_slot_extra_mm']),
                                  ('rear_endplate',p['locator_rear_depth_mm']/2,p['locator_slip_d_mm'],p['locator_slot_extra_mm']),
                                  ('gasket',p['gasket_t_mm']/2,p['gasket_pin_d_mm'],p['gasket_slot_extra_mm'])]:
            if name=='gasket' and p['seal_mode']=='oring':
                continue
            polygons = self.get(name).slice(z).to_polygons()
            for i,xy in enumerate(p['locator_points']):
                poly = min(polygons,key=lambda poly: np.linalg.norm(np.array(poly).mean(axis=0)-xy))
                projected = np.array(poly) @ np.array([along,across]).T
                extent = np.ptp(projected,axis=0)
                self.near('round/slot measured '+name+'/'+str(i+1),extent,[diam+(extra if i else 0),diam])
        # A mesh section must contain just one window and exactly two locator holes.
        # Nest pockets are intentionally additional contours on the -Z face.
        contours = self.get('frame').slice(p['frame_t_mm']/2).to_polygons()
        self.check('frame has no extra manifold bores',len(contours)==4,section_contours=len(contours))

    def polarity(self):
        samples = ['frame_1','electrode_1']
        if self.p['seal_mode']=='flat_gasket':
            samples.append('gasket_2')
        for rid in samples:
            r = self.records[rid]
            h = self.p['frame_t_mm'] if rid.startswith('frame') else self.p['electrode_t_mm'] if rid.startswith('electrode') else self.p['gasket_t_mm']
            for axis, signs in [('Z',[ -1,-1,1]),('X',[1,-1,-1]),('Y',[-1,1,-1])]:
                shift = [0,0,h if signs[2]<0 else 0]
                flipped = self.local[r['stl']].scale(signs).translate(shift).scale(r['scale']).translate(r['translation'])
                collisions = []
                for other, s in self.world.items():
                    if other==rid:
                        continue
                    v = max(0.,(flipped ^ s).volume())
                    if v>VOLUME_TOL:
                        collisions.append({'other':other,'volume_mm3':v})
                self.check('reject '+axis+'180 '+rid,bool(collisions),collisions=collisions)
        if self.p['seal_mode']=='oring':
            self.check('oring orientation applicability',True,reason='closed symmetric O-ring has no pin holes; polarity belongs to rigid parts')


def verify(manifest, report):
    audit = Audit(manifest)
    try:
        result = audit.run()
    except Exception as exc:
        result = {'pass':False,'checks':audit.results,'error':str(exc),'traceback':traceback.format_exc()}
    write_json(report,result)
    print(('PASS' if result['pass'] else 'FAIL')+f': {manifest}; {len(audit.results)} checks',flush=True)
    if not result['pass']:
        raise RuntimeError('CAD verification failed; see '+str(report))
    return result


if __name__=='__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--manifest',default='stack_manifest.json')
    ap.add_argument('--report',default='renders/cad_verification.json')
    args = ap.parse_args()
    try:
        verify(args.manifest,args.report)
    except Exception as exc:
        print(exc,file=sys.stderr)
        sys.exit(1)
