import * as THREE from 'three';
import {OrbitControls} from 'local-three/examples/jsm/controls/OrbitControls.js';
import {RoomEnvironment} from 'local-three/examples/jsm/environments/RoomEnvironment.js';
const {manifest:M,geometries:packed,metadata}=window.DEMO_DATA;
const $=id=>document.getElementById(id), vec=a=>new THREE.Vector3(...a);
const defaultDirection=vec([1.1,.8,-1.4]).normalize();
const S={target:0,actual:0,selected:null,isolation:'ghost',section:false,cut:71.75/74,opaque:false,gasket:M.gasket_material,metal:M.parameters.electrode_material,group:null};
const order=['stack','bolts','washers','heatsets','locators'].flatMap(g=>M.groups[g]);
const records=new Map(M.instances.map(i=>[i.id,i])), objects=new Map(), geometries=new Map(), edges=new Map();
let renderer,scene,camera,controls,root,ground,key,fill,fly=null,flipBack=null,dirty=true,settledFrames=0;
let last=performance.now(),renderCount=0,selectionEvents=0,frameIntervals=[],previousRendered=false,frameTimes=[],idleWaiters=[],controlMoving=false;
const v2=new THREE.Vector2(), raycaster=new THREE.Raycaster(), cutPlane=new THREE.Plane(new THREE.Vector3(-1,0,0),34.75);
const clipping=[];
function decode(base64,Type){const bytes=Uint8Array.from(atob(base64),c=>c.charCodeAt(0));return new Type(bytes.buffer);}
function unpack(g){
  const raw=decode(g.positions,g.encoding==='uint16'?Uint16Array:Float32Array), positions=new Float32Array(raw.length);
  for(let n=0;n<raw.length;n++)positions[n]=g.encoding==='uint16'?g.min[n%3]+raw[n]/65535*g.extent[n%3]:raw[n];
  const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.BufferAttribute(positions,3));
  geo.setAttribute('normal',new THREE.BufferAttribute(decode(g.normals,Int16Array),3,true));
  geo.setIndex(new THREE.BufferAttribute(decode(g.indices,g.index32?Uint32Array:Uint16Array),1));
  geo.computeBoundingBox();geo.computeBoundingSphere();return geo;
}
function baseMaterial(i){
  let p={color:'#2b2f36',metalness:.10,roughness:.62};
  if(i.part==='frame')p={color:'#9fb7c9',metalness:0,roughness:.38,opacity:S.opaque?1:.58,transparent:!S.opaque,depthWrite:S.opaque};
  if(i.part.includes('gasket'))p={color:{EPDM:'#1c1c1c',FKM:'#342820',PTFE:'#f4f3ec'}[S.gasket],metalness:0,roughness:.90};
  if(i.part.startsWith('electrode'))p={color:S.metal==='platinum'?'#d9d6cf':'#8a8d91',metalness:.85,roughness:.28};
  if(['bolt','washer','locator_pin'].includes(i.part))p={color:'#c8ccd0',metalness:.85,roughness:.25};
  if(i.part==='heatset_nut')p={color:'#b5893b',metalness:.80,roughness:.30};
  return new THREE.MeshStandardMaterial({...p,clipShadows:true,polygonOffset:true,polygonOffsetFactor:1,polygonOffsetUnits:1+i.sequence_index*.1,side:THREE.FrontSide,clippingPlanes:clipping});
}
function updateLighting(){
  if(!key||!ground)return;
  const visible=order.filter(id=>objects.get(id).group.visible),b=bounds(currentIDs(),S.actual),center=b.getCenter(new THREE.Vector3());
  const span=Math.max(...b.getSize(new THREE.Vector3()).toArray()),radius=Math.max(span*.85,25);
  const positive=S.selected&&['frame','gasket'].some(p=>records.get(S.selected).part.startsWith(p));
  key.position.copy(center).add(vec([100,230,positive?200:-200]));key.target.position.copy(center);
  const c=key.shadow.camera;Object.assign(c,{left:-radius,right:radius,top:radius,bottom:-radius,near:.1,far:2000});c.updateProjectionMatrix();
  key.shadow.normalBias=S.selected ? .025 : .10;
  ground.position.y=bounds(visible,S.actual).min.y-4;
}
function chosen(id){return S.selected===id || (S.group&&M.groups[S.group].includes(id));}
function applyMaterials(){
  for(const [id,o]of objects){
    o.mesh.material.dispose();o.mesh.material=baseMaterial(o.record);
    const active=chosen(id),other=(S.selected||S.group)&&!active;
    o.group.visible=!(other&&S.isolation==='hide');o.ghost=!!other;
    if(other){o.mesh.material.transparent=true;o.mesh.material.opacity=.08;o.mesh.material.depthWrite=false;}
    if(active){o.mesh.material.emissive.set('#30789d');o.mesh.material.emissiveIntensity=.10;}
    o.line.material.color.set(active?'#265b78':'#34434f');o.line.material.opacity=other?.045:active?.6:S.section?.10:.28;
    o.mesh.castShadow=!other;o.mesh.receiveShadow=!other;
  }
  dirty=true;if(renderer)renderer.shadowMap.needsUpdate=true;updateLighting();
}
function transform(i,v){return {position:i.translation.map((x,j)=>THREE.MathUtils.lerp(x,i.exploded_translation[j],v)),
  scale:i.scale.map((x,j)=>THREE.MathUtils.lerp(x,i.exploded_scale[j],v)),
  rotation:i.rotation_deg.map((x,j)=>THREE.MathUtils.degToRad(THREE.MathUtils.lerp(x,i.exploded_rotation_deg[j],v)))};}
function updateTransforms(){
  for(const o of objects.values()){
    const t=transform(o.record,S.actual);o.group.position.fromArray(t.position);o.group.scale.fromArray(t.scale);o.group.rotation.set(...t.rotation);
    if(o.morph){o.mesh.morphTargetInfluences[0]=1-S.actual;const a=o.edgeFree,b=o.edgeCompressed,p=o.line.geometry.attributes.position;for(let j=0;j<a.length;j++)p.array[j]=THREE.MathUtils.lerp(b[j],a[j],S.actual);p.needsUpdate=true;}
  }
  root.updateMatrixWorld(true);renderer.shadowMap.needsUpdate=true;dirty=true;updateLighting();
}
function localBounds(i,v){
  const free=M.files[i.stl].local_bbox_mm,comp=i.compressed_stl?M.files[i.compressed_stl].local_bbox_mm:free;
  return new THREE.Box3(vec(comp[0].map((x,j)=>THREE.MathUtils.lerp(x,free[0][j],v))),vec(comp[1].map((x,j)=>THREE.MathUtils.lerp(x,free[1][j],v))));
}
function bounds(ids=order,v=S.target){
  const b=new THREE.Box3(),matrix=new THREE.Matrix4(),q=new THREE.Quaternion();
  for(const id of ids){const i=records.get(id),t=transform(i,v);q.setFromEuler(new THREE.Euler(...t.rotation));
    matrix.compose(vec(t.position).add(root.position),q,vec(t.scale));
    b.union(localBounds(i,v).applyMatrix4(matrix));}
  return b;
}
function corners(b){return [0,1,2,3,4,5,6,7].map(n=>new THREE.Vector3(n&1?b.max.x:b.min.x,n&2?b.max.y:b.min.y,n&4?b.max.z:b.min.z));}
function currentIDs(){return S.selected?[S.selected]:S.group?M.groups[S.group]:order;}
function flyTo(position,target){
  controls.update();fly={start:performance.now(),from:camera.position.clone(),to:position.clone(),fromTarget:controls.target.clone(),toTarget:target.clone()};
  dirty=true;settledFrames=0;
}
function fit(ids=currentIDs(),direction){
  if(!camera)return;
  const b=bounds(ids),center=b.getCenter(new THREE.Vector3()),size=b.getSize(new THREE.Vector3());
  let dir=direction?.clone()||camera.position.clone().sub(controls.target).normalize();
  if(dir.length()<.1)dir=defaultDirection.clone();
  const right=new THREE.Vector3().crossVectors(camera.up,dir).normalize(),up=new THREE.Vector3().crossVectors(dir,right).normalize();
  const tanV=Math.tan(THREE.MathUtils.degToRad(40)/2),tanH=tanV*camera.aspect;
  let distance=0;
  for(const c of corners(b)){const d=c.sub(center),z=d.dot(dir);distance=Math.max(distance,z+Math.abs(d.dot(right))/tanH,z+Math.abs(d.dot(up))/tanV);}
  distance=Math.max(distance*1.25,Math.max(size.x,size.y)*.6,12);
  camera.near=.1;camera.far=Math.max(2000,10*size.length(),distance*4);camera.updateProjectionMatrix();
  flyTo(center.clone().addScaledVector(dir,distance),center);
}
function allDirection(){const portrait=$('viewport').clientWidth/$('viewport').clientHeight<.8;return defaultDirection.clone().lerp(vec(portrait?[.10,1.8,-.5]:[1.8,.55,-.55]).normalize(),S.target).normalize();}
function fitAll(){fit(order,allDirection());}
function updateUI(){
  $('explode-range').value=S.target;$('explode-range').setAttribute('aria-valuetext',`${Math.round(S.target*100)}%`);
  $('explode-value').value=`${Math.round(S.target*100)}%`;
  $('explode').setAttribute('aria-pressed',S.target===1);$('collapse').setAttribute('aria-pressed',S.target===0);
  $('ghost').setAttribute('aria-pressed',S.isolation==='ghost');$('hide').setAttribute('aria-pressed',S.isolation==='hide');
  $('section').setAttribute('aria-pressed',S.section);$('opaque').setAttribute('aria-pressed',S.opaque);
  $('cut').value=S.cut;$('cut-value').value=`${(-37+74*S.cut).toFixed(2)} mm`;
  $('cut').setAttribute('aria-valuetext',$('cut-value').value);
  $('gasket-material').value=S.gasket;$('metal-material').value=S.metal;
  for(const b of document.querySelectorAll('[data-piece]')){const active=chosen(b.dataset.piece);b.classList.toggle('active',!!active);b.setAttribute('aria-pressed',!!active);}
  for(const b of document.querySelectorAll('[data-group]'))b.setAttribute('aria-pressed',S.group===b.dataset.group);
  $('flip').disabled=!(S.selected||S.group);
  const title=S.selected?records.get(S.selected).display_name.zh:S.group?groupNames[S.group]:'完整装配';
  $('view-title').textContent=title+(S.section?' · 剖切显示':'');
  $('view-state').textContent=S.section?`SECTION · X = ${(-37+74*S.cut).toFixed(2)} mm`:S.target===0?`COMPRESSED STACK · ${M.derived.total_stack_t} mm`:`EXPLODED · ${Math.round(S.target*100)}%`;
  updateInfo();
}
function fmt(a){return a.map(x=>Number(x.toFixed(3))).join(' × ');}
function updateInfo(){
  let content;
  if(S.selected){const i=records.get(S.selected),o=objects.get(S.selected),b=bounds([S.selected],S.actual).getSize(new THREE.Vector3());
    const seal=i.part.includes('gasket'),t=transform(i,S.actual),thickness=i.compressed_stl?THREE.MathUtils.lerp(i.assembled_dims_mm[2],i.nominal_dims_mm[2],S.actual):i.nominal_dims_mm[2]*t.scale[2];
    content=`<h3>${i.display_name.zh}</h3><div class="en">${i.display_name.en} · ${i.id}</div><dl><dt>材质</dt><dd>${seal?S.gasket:i.part.startsWith('electrode')?S.metal:i.material}</dd><dt>名义尺寸</dt><dd>${fmt(i.nominal_dims_mm)} mm</dd><dt>当前 bbox</dt><dd>${fmt(b.toArray())} mm</dd>${seal?`<dt>当前厚度</dt><dd>${thickness.toFixed(3)} mm · 压缩 ${((1-thickness/i.nominal_dims_mm[2])*100).toFixed(1)}%</dd><dt>自由厚度</dt><dd>${i.nominal_dims_mm[2]} mm</dd>`:''}${i.active_pad_dims_mm?`<dt>中央片</dt><dd>${fmt(i.active_pad_dims_mm)} mm</dd>`:''}</dl><p class="hint">${S.section?'剖切显示 · 无封口面':i.part==='frame'?'主体 4 mm · 肩 2.2 · 唇 1.2 · 母槽 1.5':seal?(i.part==='gasket_oring'?'闭合 O-ring · 单面槽定位 · 椭圆压缩包络':'独立密封薄片 · 圆孔 + 长孔定位'):'真实 STL 几何 · 尺寸以当前 manifest 为准'}</p>`;
  }else if(S.group){const ids=M.groups[S.group],i=records.get(ids[0]);content=`<h3>${groupNames[S.group]}</h3><div class="en">${S.group} · ${ids.length} pieces</div><dl><dt>数量</dt><dd>${ids.length}</dd><dt>单件尺寸</dt><dd>${fmt(i.nominal_dims_mm)} mm</dd><dt>材质</dt><dd>${i.material}</dd></dl>`;
  }else content=`<h3>${S.section?'剖切显示':'41 件 · 一个完整装配'}</h3><div class="en">3 FRAMES / 3 ELECTRODES / 7 GASKETS</div><dl><dt>装配厚度</dt><dd>${M.derived.total_stack_t} mm</dd><dt>垫片厚度</dt><dd>${(THREE.MathUtils.lerp(M.seal_mode==='oring'?M.derived.oring_compressed_h:M.derived.gasket_compressed_t,M.seal_mode==='oring'?M.parameters.oring_cs_mm:M.parameters.gasket_t_mm,S.actual)).toFixed(3)} mm</dd><dt>压缩比例</dt><dd>${(M.parameters.gasket_compression_ratio*100*(1-S.actual)).toFixed(1)}% · 自由 ${M.seal_mode==='oring'?M.parameters.oring_cs_mm:M.parameters.gasket_t_mm} mm</dd><dt>螺栓</dt><dd>8 × M6 · L${M.derived.bolt_length_mm}</dd></dl><p class="hint">${S.section?'X=34.75 mm 截过右侧止口；拖动旋转检查肩、唇与母槽。':'点选零件查看尺寸，使用 Prev / Next 逐件浏览。'}</p>`;
  $('info').innerHTML=content;
}
function setExplode(v){S.target=THREE.MathUtils.clamp(Number(v),0,1);flipBack=null;updateUI();fit(currentIDs(),S.selected||S.group?undefined:allDirection());dirty=true;settledFrames=0;}
function select(id){
  if(!records.has(id))throw new Error(`Unknown instance: ${id}`);
  selectionEvents++;S.selected=id;S.group=null;document.querySelector('.panel-body').scrollTop=0;S.isolation='ghost';flipBack=null;applyMaterials();updateUI();
  const i=records.get(id),direction=i.part==='frame'?vec([.48,.32,1.5]):i.part.includes('gasket')?vec([.18,.24,1.6]):defaultDirection;
  fit([id],direction.normalize());
}
function selectGroup(group){document.querySelector('.panel-body').scrollTop=0;S.selected=null;S.group=group;S.isolation='ghost';flipBack=null;applyMaterials();updateUI();fit(M.groups[group]);}
function setIsolation(mode){if(!['ghost','hide'].includes(mode))throw new Error('Isolation must be ghost or hide');S.isolation=mode;applyMaterials();updateUI();}
function setSection(on,v=S.cut){
  const entering=!!on&&!S.section;S.section=!!on;S.cut=THREE.MathUtils.clamp(Number(v),0,1);cutPlane.constant=-37+74*S.cut+root.position.x;
  clipping.splice(0,clipping.length,...(S.section?[cutPlane]:[]));
  for(const o of objects.values()){o.mesh.receiveShadow=!o.ghost;o.line.material.opacity=o.ghost?.045:chosen(o.record.id)?.6:S.section?.10:.28;o.mesh.material.clippingPlanes=clipping;o.mesh.material.needsUpdate=true;o.line.material.clippingPlanes=clipping;o.line.material.needsUpdate=true;}
  renderer.shadowMap.needsUpdate=true;dirty=true;updateUI();if(entering)fit(currentIDs(),vec([1,.22,-.16]).normalize());
}
function showAll(){S.selected=null;S.group=null;S.isolation='ghost';flipBack=null;setSection(false);applyMaterials();updateUI();fitAll();}
function reset(){S.opaque=false;S.gasket=M.gasket_material;S.metal=M.parameters.electrode_material;setExplode(0);showAll();}
function flipSelected(){
  if(!S.selected&&!S.group)return;
  const target=controls.target.clone(),offset=camera.position.clone().sub(target);
  if(flipBack){flyTo(target.clone().add(flipBack),target);flipBack=null;}
  else {flipBack=offset.clone();offset.applyAxisAngle(camera.up,Math.PI);flyTo(target.clone().add(offset),target);}
}
const groupNames={bolts:'螺栓 ×8',washers:'垫圈 ×8',heatsets:'热熔螺母 ×8',locators:'定位销 ×2'};
function buildUI(){
  function chip(id){const i=records.get(id),button=document.createElement('button');button.className='chip';button.dataset.piece=id;
    const short=i.part==='gasket'?`G${id.split('_').pop()}`:i.part==='frame'?`F${id.split('_').pop()}`:i.part.startsWith('electrode')?`E${id.split('_').pop()}`:i.group==='stack'?i.display_name.zh:id.replace('locator_pin','P').replace('heatset','N').replace('washer','W').replace('bolt','B').replace('_','');
    button.innerHTML=`${short}<span>${i.display_name.zh}</span>`;button.setAttribute('aria-label',`${i.display_name.zh} ${id}`);button.onclick=()=>select(id);return button;}
  for(const id of M.groups.stack)$('stack-list').append(chip(id));
  for(const group of ['bolts','washers','heatsets','locators']){
    const row=document.createElement('div');row.className='group-row';const button=document.createElement('button');button.className='group-select';button.dataset.group=group;button.textContent=groupNames[group];button.setAttribute('aria-label',`选择${groupNames[group]}`);button.onclick=()=>selectGroup(group);
    const expand=document.createElement('button'),list=document.createElement('div');list.className='chips group-pieces';list.hidden=true;
    expand.textContent='＋';expand.setAttribute('aria-label',`展开${groupNames[group]}单件`);expand.setAttribute('aria-expanded','false');expand.onclick=()=>{list.hidden=!list.hidden;expand.textContent=list.hidden?'＋':'−';expand.setAttribute('aria-expanded',!list.hidden);};
    for(const id of M.groups[group])list.append(chip(id));row.append(button,expand);$('hardware-list').append(row,list);
  }
  $('explode-range').oninput=e=>setExplode(e.target.value);$('explode').onclick=()=>setExplode(1);$('collapse').onclick=()=>setExplode(0);
  $('show-all').onclick=showAll;$('reset').onclick=reset;$('ghost').onclick=()=>setIsolation('ghost');$('hide').onclick=()=>setIsolation('hide');$('flip').onclick=flipSelected;
  const step=delta=>{let idx=S.group?order.indexOf(M.groups[S.group][0]):S.selected?order.indexOf(S.selected):-1;select(order[S.group?idx:idx<0?(delta>0?0:order.length-1):(idx+delta+order.length)%order.length]);};
  $('prev').onclick=()=>step(-1);$('next').onclick=()=>step(1);
  $('section').onclick=()=>setSection(!S.section);$('cut').oninput=e=>setSection(S.section,e.target.value);
  $('opaque').onclick=()=>{S.opaque=!S.opaque;applyMaterials();updateUI();};
  $('gasket-material').onchange=e=>{S.gasket=e.target.value;applyMaterials();updateUI();};$('metal-material').onchange=e=>{S.metal=e.target.value;applyMaterials();updateUI();};
  $('panel-toggle').onclick=()=>{const closed=$('panel').classList.toggle('collapsed');$('panel-toggle').textContent=closed?'展开 ＋':'收起 −';$('panel-toggle').setAttribute('aria-expanded',!closed);$('panel-toggle').setAttribute('aria-label',closed?'展开零件面板':'收起零件面板');resize();};
}
function resize(){
  if(!renderer)return;const {width:w,height:h}=$('viewport').getBoundingClientRect();if(w<1||h<1)return;
  renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();fit(currentIDs(),S.selected||S.group?undefined:allDirection());dirty=true;
}
function pick(clientX,clientY){
  const r=renderer.domElement.getBoundingClientRect();v2.set((clientX-r.left)/r.width*2-1,-(clientY-r.top)/r.height*2+1);
  raycaster.setFromCamera(v2,camera);
  const hits=raycaster.intersectObjects([...objects.values()].filter(o=>o.group.visible&&!o.ghost).map(o=>o.mesh),false);
  return hits.find(h=>!S.section||cutPlane.distanceToPoint(h.point)>=-1e-5)?.object.userData.id||null;
}
function pointerEvents(){
  const active=new Set();let down=null,multiple=false;
  const canvas=renderer.domElement;
  canvas.addEventListener('pointerdown',e=>{active.add(e.pointerId);if(active.size>1)multiple=true;if(active.size===1){multiple=false;down={id:e.pointerId,x:e.clientX,y:e.clientY,time:performance.now(),max:0};}});
  canvas.addEventListener('pointermove',e=>{if(down&&e.pointerId===down.id)down.max=Math.max(down.max,Math.hypot(e.clientX-down.x,e.clientY-down.y));});
  canvas.addEventListener('pointerup',e=>{active.delete(e.pointerId);if(down&&e.pointerId===down.id&&!multiple&&performance.now()-down.time<=500&&down.max<=6){const id=pick(e.clientX,e.clientY);if(id)select(id);}if(!active.size){down=null;multiple=false;}});
  canvas.addEventListener('pointercancel',e=>{active.delete(e.pointerId);down=null;multiple=true;});
}
function state(){
  scene.updateMatrixWorld(true);camera.updateMatrixWorld(true);
  const r=renderer.domElement.getBoundingClientRect(),instances=[];
  for(const [id,o]of objects){const bb=bounds([id],S.actual);const projected=corners(bb).map(v=>v.project(camera));const screenBBox=[[Math.min(...projected.map(v=>v.x)),Math.min(...projected.map(v=>v.y))],[Math.max(...projected.map(v=>v.x)),Math.max(...projected.map(v=>v.y))]];instances.push({id,screenBBox,part:o.record.part,position:o.group.position.toArray(),scale:o.group.scale.toArray(),rotation:o.group.rotation.toArray(),bbox:[bb.min.toArray(),bb.max.toArray()],visible:o.group.visible,edgeVisible:o.group.visible&&o.line.visible,ghost:o.ghost,opacity:o.mesh.material.opacity,depthWrite:o.mesh.material.depthWrite,color:o.mesh.material.color.getHexString(),geometry:o.record.stl,triangles:o.mesh.geometry.index.count/3,clipping:o.mesh.material.clippingPlanes.length,edgeClipping:o.line.material.clippingPlanes.length,morph:o.mesh.morphTargetInfluences?.[0]??null});}
  // Real visible surface projections aid deterministic pointer-event verification.
  let pickPoint=null,clippedPickPoint=null;
  const candidates=S.selected?[objects.get(S.selected)]:[objects.get('frame_2'),...[...objects.values()].filter(o=>o.record.id!=='frame_2')];
  outer:for(const o of candidates){if(!o.group.visible||o.ghost)continue;const p=o.mesh.geometry.attributes.position,idx=o.mesh.geometry.index;
    for(let n=0;n<idx.count;n+=Math.max(3,Math.floor(idx.count/150/3)*3)){
      const center=new THREE.Vector3();for(let j=0;j<3;j++)center.add(new THREE.Vector3().fromBufferAttribute(p,idx.getX(n+j)));center.multiplyScalar(1/3).applyMatrix4(o.mesh.matrixWorld);
      const removed=S.section&&cutPlane.distanceToPoint(center)<0;
      center.project(camera);if(Math.abs(center.x)>.90||Math.abs(center.y)>.85)continue;
      const x=r.left+(center.x+1)*r.width/2,y=r.top+(1-center.y)*r.height/2;
      const hit=pick(x,y);
      if(removed){if(!hit)clippedPickPoint={id:o.record.id,x,y};continue;}
      if(hit===o.record.id){pickPoint={id:o.record.id,x,y};if(!S.section||clippedPickPoint)break outer;}
    }
  }
  const samples=frameTimes.slice().sort((a,b)=>a-b),all=bounds(order,S.actual);
  const intervals=frameIntervals.slice().sort((a,b)=>a-b);
  return {...S,compressionRatio:(M.seal_mode==='oring'?M.parameters.oring_compression_ratio:M.parameters.gasket_compression_ratio)*(1-S.actual),selectionEvents,motion:{controlMoving,fly:!!fly,settledFrames},ids:order,instances,geometryCount:geometries.size,geometryTriangles:Object.fromEntries([...geometries].map(([f,g])=>[f,g.index.count/3])),
    sharedGeometry:[...objects.values()].every(o=>o.mesh.geometry===geometries.get(o.record.stl)),
    bbox:[all.min.toArray(),all.max.toArray()],parentTranslation:root.position.toArray(),cutX:-37+74*S.cut,clippingPlane:{normal:cutPlane.normal.toArray(),constant:cutPlane.constant},
    camera:{position:camera.position.toArray(),target:controls.target.toArray(),aspect:camera.aspect,near:camera.near,far:camera.far,distance:camera.position.distanceTo(controls.target)},
    viewport:{width:r.width,height:r.height,dpr:renderer.getPixelRatio()},pickPoint,clippedPickPoint,
    performance:{renderedFrames:renderCount,samples:samples.length,frame_time_samples:intervals.length,frame_time_ms_median:intervals[Math.floor(intervals.length*.5)]||0,frame_time_ms_p95:intervals[Math.floor(intervals.length*.95)]||0,render_ms_median:samples[Math.floor(samples.length*.5)]||0,render_ms_p95:samples[Math.floor(samples.length*.95)]||0},
    three:THREE.REVISION,metadata};
}
function whenIdle(){settledFrames=0;return new Promise(resolve=>{idleWaiters.push(resolve);dirty=true;});}
function tick(now){
  requestAnimationFrame(tick);const dt=now-last;last=now;let moving=false;
  if(Math.abs(S.actual-S.target)>1e-4){S.actual+= (S.target-S.actual)*(1-Math.exp(-dt/180));if(Math.abs(S.actual-S.target)<1e-4)S.actual=S.target;updateTransforms();moving=true;updateInfo();}
  if(fly){const t=Math.min((now-fly.start)/450,1),s=t*t*(3-2*t);camera.position.lerpVectors(fly.from,fly.to,s);controls.target.lerpVectors(fly.fromTarget,fly.toTarget,s);dirty=true;moving=true;if(t===1)fly=null;}
  // Advance damping at 60 Hz even when software rendering delivers fewer frames.
  let changed=false;const dampingSteps=Math.max(1,Math.min(120,Math.round(dt/(1000/60))));
  for(let n=0;n<dampingSteps;n++)changed=controls.update()||changed;controlMoving=changed;
  if(changed)dirty=true;
  if(moving||controlMoving){settledFrames=0;}else settledFrames++;
  if(dirty||moving||controlMoving||settledFrames<=3){
    if(previousRendered){frameIntervals.push(dt);if(frameIntervals.length>300)frameIntervals.shift();}previousRendered=true;
    const start=performance.now();renderer.render(scene,camera);frameTimes.push(performance.now()-start);if(frameTimes.length>300)frameTimes.shift();renderCount++;dirty=false;
  }else previousRendered=false;
  if(!moving&&!controlMoving&&!fly&&settledFrames>=2){const pending=idleWaiters.splice(0);pending.forEach(resolve=>resolve());}
}
function init(){
  try{renderer=new THREE.WebGLRenderer({antialias:true,alpha:false});}
  catch(e){$('error').hidden=false;$('error').textContent='无法启动 WebGL2。请启用浏览器硬件加速后重新打开。';throw e;}
  renderer.setClearColor('#eef1f4');renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1;
  renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.shadowMap.autoUpdate=false;renderer.localClippingEnabled=true;
  $('viewport').append(renderer.domElement);renderer.domElement.setAttribute('aria-label','三维装配模型');
  renderer.domElement.addEventListener('webglcontextlost',()=>{console.error('WebGL context lost');$('error').hidden=false;$('error').textContent='WebGL 上下文丢失，请重新加载。';});
  scene=new THREE.Scene();scene.background=new THREE.Color('#eef1f4');
  const pmrem=new THREE.PMREMGenerator(renderer),room=new RoomEnvironment();scene.environment=pmrem.fromScene(room,.04).texture;room.dispose();pmrem.dispose();
  camera=new THREE.PerspectiveCamera(40,1,.1,2000);camera.up.set(0,1,0);camera.position.copy(defaultDirection).multiplyScalar(300);
  controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.dampingFactor=.08;controls.minDistance=8;controls.maxDistance=7000;
  controls.addEventListener('start',()=>{fly=null;flipBack=null;});controls.addEventListener('change',()=>{dirty=true;});
  root=new THREE.Group();scene.add(root);
  for(const [file,g]of Object.entries(packed)){const geo=unpack(g);geometries.set(file,geo);edges.set(file,new THREE.EdgesGeometry(geo,25));}
  for(const [file,g]of geometries){
    if(!packed[file].morphPositions)continue;
    const compressed=decode(packed[file].morphPositions,Float32Array),normals=decode(packed[file].morphNormals,Float32Array);
    g.morphAttributes.position=[new THREE.BufferAttribute(compressed,3)];g.morphAttributes.normal=[new THREE.BufferAttribute(normals,3)];g.morphTargetsRelative=false;g.computeBoundingBox();g.computeBoundingSphere();
    const table=new Map(),free=g.attributes.position;
    for(let n=0;n<free.count;n++)table.set([free.getX(n),free.getY(n),free.getZ(n)].join(','),n);
    const line=edges.get(file),p=line.attributes.position,target=new Float32Array(p.array.length);
    for(let n=0;n<p.count;n++){const index=table.get([p.getX(n),p.getY(n),p.getZ(n)].join(','));if(index===undefined)throw new Error('O-ring edge correspondence missing');target.set(compressed.slice(index*3,index*3+3),n*3);}
    line.userData.free=p.array.slice();line.userData.compressed=target;
  }
  for(const id of order){const i=records.get(id),group=new THREE.Group(),mesh=new THREE.Mesh(geometries.get(i.stl),baseMaterial(i));
    mesh.userData.id=id;mesh.castShadow=true;mesh.receiveShadow=true;
    const line=new THREE.LineSegments(edges.get(i.stl),new THREE.LineBasicMaterial({color:'#34434f',opacity:.28,transparent:true,depthWrite:false,clippingPlanes:clipping}));
    group.add(mesh,line);root.add(group);objects.set(id,{group,mesh,line,record:i,ghost:false,morph:!!mesh.morphTargetInfluences,edgeFree:line.geometry.userData.free,edgeCompressed:line.geometry.userData.compressed});
  }
  const initial=bounds(order,0).getCenter(new THREE.Vector3());root.position.copy(initial).negate();updateTransforms();
  ground=new THREE.Mesh(new THREE.PlaneGeometry(5000,5000),new THREE.ShadowMaterial({opacity:.18}));ground.rotation.x=-Math.PI/2;ground.position.y=bounds(order,0).min.y-4;ground.receiveShadow=true;scene.add(ground);
  key=new THREE.DirectionalLight('#fff7ec',3);key.position.set(100,230,-200);key.castShadow=true;key.shadow.mapSize.set(2048,2048);key.shadow.bias=-.0002;key.shadow.normalBias=.10;scene.add(key,key.target);
  const shadowCamera=key.shadow.camera;Object.assign(shadowCamera,{left:-420,right:420,top:420,bottom:-420,near:.1,far:1500});shadowCamera.updateProjectionMatrix();
  fill=new THREE.DirectionalLight('#e6f2ff',1);fill.position.set(-150,90,260);scene.add(fill);scene.add(new THREE.HemisphereLight('#ffffff','#cad4dc',.45));
  buildUI();applyMaterials();updateUI();pointerEvents();resize();
  new ResizeObserver(resize).observe($('viewport'));window.addEventListener('resize',resize);
  window.__demo={ready:false,setExplode,select,showAll,setSection,whenIdle,getState:state,setIsolation,flipSelected,fitAll};
  requestAnimationFrame(tick);whenIdle().then(()=>{window.__demo.ready=true;});
}
try{init();}catch(e){$('error').hidden=false;$('error').textContent=`模型启动失败：${e.message}`;console.error(e);}
