#!/usr/bin/env node
// Deterministic offline STL packer. Dependencies are deliberately outside the repo.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
import {STLLoader} from '/workspace/kolbe_tools/node_modules/three/examples/jsm/loaders/STLLoader.js';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const require = createRequire('/workspace/kolbe_tools/package.json');
const esbuild = require('esbuild');
const threeRoot = '/workspace/kolbe_tools/node_modules/three';
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const read = p => fs.readFileSync(path.resolve(root, p));
const manifestPath = process.argv[2] || 'stack_manifest.json';
const manifest = JSON.parse(read(manifestPath));
const outputPath=path.resolve(root,process.argv[3]||'demo_v2.html');
const readMesh=file=>read(path.join(path.dirname(manifestPath),file));
function assert(ok, why) { if (!ok) throw new Error(why); }
assert(JSON.parse(fs.readFileSync(path.join(threeRoot,'package.json'))).version === '0.170.0', 'three must be r170');
assert(esbuild.version === '0.24.0', 'esbuild must be 0.24.0');
assert(manifest.schema_version === 1 && manifest.units === 'mm', 'Unsupported manifest');
assert(sha(read('kolbe_non_through.scad')) === manifest.source_sha256, 'SCAD source hash mismatch');
const ids = new Set();
for (const i of manifest.instances) {
  assert(!ids.has(i.id), 'Duplicate instance id'); ids.add(i.id);
  assert(manifest.files[i.stl], `Missing file record ${i.stl}`);
  for (const k of ['translation','scale','rotation_deg','exploded_translation','exploded_scale','exploded_rotation_deg'])
    assert(i[k]?.length === 3 && i[k].every(Number.isFinite), `Invalid ${i.id}.${k}`);
}
// Check every exported input, including the unassembled plain electrode; only pack referenced ones.
for (const [file, info] of Object.entries(manifest.files))
  assert(sha(readMesh(file)) === info.sha256, `STL hash mismatch: ${file}`);
const geometries = {}, reports = {}, topologies=new Map();
const b64 = a => Buffer.from(a.buffer, a.byteOffset, a.byteLength).toString('base64');
const cross = (a,b) => [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
const sub = (a,b) => a.map((v,j)=>v-b[j]);
const dot = (a,b) => a.reduce((s,v,j)=>s+v*b[j],0);
function pack(file) {
  const bytes = readMesh(file), raw = new STLLoader().parse(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength));
  const p = raw.getAttribute('position');
  assert(p.count % 3 === 0, 'Incomplete STL face');
  const positions=[], welded=[], map=new Map(), faces=[], normals=[], areaNormals=[];
  for(let n=0;n<p.count;n++) {
    const v=[p.getX(n),p.getY(n),p.getZ(n)];
    assert(v.every(Number.isFinite), 'Nonfinite position');
    const key=v.map(x=>Math.round(x/1e-5)).join(',');
    if(!map.has(key)) { map.set(key,positions.length); positions.push(v); }
    welded.push(map.get(key));
  }
  for(let n=0;n<welded.length;n+=3) {
    const f=welded.slice(n,n+3), c=cross(sub(positions[f[1]],positions[f[0]]),sub(positions[f[2]],positions[f[0]]));
    const len=Math.hypot(...c); assert(len>0, `${file}: zero area face after welding`);
    faces.push(f); areaNormals.push(c); normals.push(c.map(v=>v/len));
  }
  assert(faces.length===manifest.files[file].triangles, `${file}: lost STL triangles`);
  // Union face corners only across smooth manifold edges; hard edges retain split normals.
  const parent=Array.from({length:p.count},(_,i)=>i);
  function find(i) { while(parent[i]!==i) {parent[i]=parent[parent[i]]; i=parent[i];} return i; }
  function join(a,b) { a=find(a); b=find(b); if(a!==b) parent[Math.max(a,b)]=Math.min(a,b); }
  const edges=new Map(), threshold=Math.cos(25*Math.PI/180);
  faces.forEach((f,fi)=>f.forEach((v,j)=>{
    const w=f[(j+1)%3], key=[Math.min(v,w),Math.max(v,w)].join(':');
    if(!edges.has(key)) edges.set(key,[]);
    edges.get(key).push({fi,a:fi*3+j,b:fi*3+(j+1)%3,v,w});
  }));
  for(const entries of edges.values()) if(entries.length===2) {
    const [a,b]=entries;
    if(dot(normals[a.fi],normals[b.fi])>=threshold) {
      join(a.a,a.v===b.v?b.a:b.b); join(a.b,a.w===b.w?b.b:b.a);
    }
  }
  const clusterMap=new Map(), outPositions=[], sums=[], indices=[];
  welded.forEach((v,c)=>{
    const key=find(c);
    if(!clusterMap.has(key)) {clusterMap.set(key,outPositions.length);outPositions.push(positions[v]);sums.push([0,0,0]);}
    const index=clusterMap.get(key); indices.push(index);
    for(let j=0;j<3;j++) sums[index][j]+=areaNormals[Math.floor(c/3)][j];
  });
  const min=[0,1,2].map(j=>Math.min(...positions.map(v=>v[j])));
  const max=[0,1,2].map(j=>Math.max(...positions.map(v=>v[j])));
  const extent=max.map((v,j)=>v-min[j]);
  for(let j=0;j<3;j++) {
    assert(Math.abs(min[j]-manifest.files[file].local_bbox_mm[0][j])<1e-4,'STL bbox mismatch');
    assert(Math.abs(max[j]-manifest.files[file].local_bbox_mm[1][j])<1e-4,'STL bbox mismatch');
  }
  let encoded=new Uint16Array(outPositions.flatMap(v=>v.map((x,j)=>extent[j]?Math.round((x-min[j])/extent[j]*65535):0)));
  let decoded=outPositions.map((_,i)=>[0,1,2].map(j=>min[j]+encoded[i*3+j]/65535*extent[j]));
  const collapsed=faces.reduce((n,_,f)=>{
    const [a,b,c]=indices.slice(f*3,f*3+3).map(i=>decoded[i]);
    return n+(Math.hypot(...cross(sub(b,a),sub(c,a)))===0?1:0);
  },0);
  const flipped=faces.reduce((n,f,fi)=>{const [a,b,c]=indices.slice(fi*3,fi*3+3).map(i=>decoded[i]);return n+(dot(cross(sub(b,a),sub(c,a)),areaNormals[fi])<0?1:0);},0);
  let encoding='uint16';
  let maxError=Math.max(...decoded.flatMap((v,i)=>v.map((x,j)=>Math.abs(x-outPositions[i][j]))));
  if(collapsed || flipped || maxError>0.002) {
    encoding='float32'; encoded=new Float32Array(outPositions.flat());
    decoded=outPositions.map((_,i)=>Array.from(encoded.slice(i*3,i*3+3)));
    maxError=Math.max(...decoded.flatMap((v,i)=>v.map((x,j)=>Math.abs(x-outPositions[i][j]))));
  }
  assert(maxError<=0.002,'Coordinate error exceeds 0.002 mm');
  const n16=new Int16Array(sums.flatMap(v=>{const len=Math.hypot(...v);return v.map(x=>Math.round(x/len*32767));}));
  const indexArray=outPositions.length>65535?new Uint32Array(indices):new Uint16Array(indices);
  const decodedMin=[0,1,2].map(j=>Math.min(...decoded.map(v=>v[j])));
  const decodedMax=[0,1,2].map(j=>Math.max(...decoded.map(v=>v[j])));
  reports[file]={triangles:faces.length,source_vertices:positions.length,vertices:outPositions.length,
    source_bbox:[min,max],decoded_bbox:[decodedMin,decodedMax],max_error_mm:maxError,
    encoding,quantized_collapsed_triangles:collapsed,quantized_flipped_triangles:flipped,retained_triangles:faces.length};
  topologies.set(file,{indices,decoded});
  return {min,extent,encoding,positions:b64(encoded),normals:b64(n16),indices:b64(indexArray),index32:outPositions.length>65535,triangles:faces.length};
}
for(const file of [...new Set(manifest.instances.map(i=>i.stl))].sort()) geometries[file]=pack(file);
// Keep the SCAD correspondence, using free-mesh smoothing clusters for both states.
for(const i of manifest.instances.filter(i=>i.compressed_stl)) {
  const free=geometries[i.stl];if(free.morphPositions)continue;
  const file=i.compressed_stl;pack(file);
  const bytes=readMesh(file),raw=new STLLoader().parse(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength));
  const p=raw.attributes.position,topo=topologies.get(i.stl);
  assert(p.count===topo.indices.length,'O-ring correspondence lost triangles');
  const values=new Float32Array(topo.decoded.length*3),sums=topo.decoded.map(()=>[0,0,0]);
  const seen=new Set();
  for(let n=0;n<p.count;n++) {
    const index=topo.indices[n],value=[p.getX(n),p.getY(n),p.getZ(n)];
    if(seen.has(index))assert(value.every((x,j)=>Math.abs(values[index*3+j]-x)<1e-5),'O-ring vertex correspondence mismatch');
    values.set(value,index*3);seen.add(index);
  }
  for(let n=0;n<p.count;n+=3) {
    const ids=topo.indices.slice(n,n+3),vertices=ids.map(i=>Array.from(values.slice(i*3,i*3+3)));
    const normal=cross(sub(vertices[1],vertices[0]),sub(vertices[2],vertices[0]));
    for(const index of ids)for(let j=0;j<3;j++)sums[index][j]+=normal[j];
  }
  free.morphPositions=b64(values);
  free.morphNormals=b64(new Float32Array(sums.flatMap(v=>{const len=Math.hypot(...v);return v.map(x=>x/len);})));
}
const appDir=path.join(root,'scripts/demo_v2');
const result=await esbuild.build({entryPoints:[path.join(appDir,'app.js')],bundle:true,write:false,format:'iife',
  platform:'browser',target:'es2020',minify:true,legalComments:'inline',
  alias:{three:path.join(threeRoot,'build/three.module.min.js')},
  plugins:[{name:'local-three-addons',setup(build){build.onResolve({filter:/^local-three\//},args=>({path:path.join(threeRoot,args.path.slice(12))}));}}]});
const sources=['scripts/build_demo_v2.mjs','scripts/demo_v2/app.js','scripts/demo_v2/style.css','scripts/demo_v2/template.html',manifestPath];
const metadata={three:'0.170.0',esbuild:esbuild.version,source_sha256:manifest.source_sha256,
  inputs:Object.fromEntries(sources.map(f=>[f,sha(read(f))])),geometry:reports};
const json=v=>JSON.stringify(v).replace(/<\/script/gi,'<\\/script');
const template=read('scripts/demo_v2/template.html').toString();
const html=template.replace('/* INLINE_STYLE */',read('scripts/demo_v2/style.css').toString())
  .replace('/* INLINE_DATA */',`window.DEMO_DATA=${json({manifest,geometries,metadata})};`)
  .replace('/* INLINE_APP */',()=>result.outputFiles[0].text.replace(/<\/script/gi,'<\\/script'));
assert(Buffer.byteLength(html)<8000000,'Offline HTML exceeds 8 MB');
fs.writeFileSync(outputPath,html);
fs.writeFileSync(process.argv[3]?outputPath+'.build.json':path.join(root,'renders/demo_v2_build.json'),JSON.stringify({...metadata,html_bytes:Buffer.byteLength(html),html_sha256:sha(html)},null,2)+'\n');
console.log(`${path.basename(outputPath)}: ${Buffer.byteLength(html)} bytes; SHA256 ${sha(html)}; ${Object.keys(geometries).length} shared geometries`);
