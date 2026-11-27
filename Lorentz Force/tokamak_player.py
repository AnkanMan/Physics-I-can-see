"""Build a standalone tokamak player with live parameters and field-line overlays."""
import json
import math


def make_tokamak_player(R_0, a, B_0, q_s, Q, m, E_params, x, v, t):
    p, velocity = x[0], v[0]
    R = math.hypot(p[0], p[1])
    theta = math.atan2(p[2], R - R_0)
    phi = math.atan2(p[1], p[0])
    radial = [math.cos(theta) * math.cos(phi), math.cos(theta) * math.sin(phi), math.sin(theta)]
    br, bp, bz = -B_0*p[2]/(q_s*R), B_0*R_0/R, B_0*(R-R_0)/(q_s*R)
    field = [br*math.cos(phi)-bp*math.sin(phi), br*math.sin(phi)+bp*math.cos(phi), bz]
    norm = math.sqrt(sum(c*c for c in field))
    direction = [c/norm for c in field] if norm else [-math.sin(phi), math.cos(phi), 0]
    config = {"R0": float(R_0), "a": float(a), "B0": float(B_0), "qs": float(q_s),
              "ratio": float(Q/m), "Ephi": float(E_params.get("E_phi0", 0)),
              "kE": float(E_params.get("k_E", 0)), "omega": float(E_params.get("omega", 0)),
              "phase": float(E_params.get("phase", 0)), "r0": float(math.hypot(R-R_0,p[2])/a),
              "theta": math.degrees(theta), "phi": phi,
              "vpar": float(sum(velocity[i]*direction[i] for i in range(3))),
              "vperp": float(sum(velocity[i]*radial[i] for i in range(3))),
              "duration": float(t[-1]-t[0]), "dt": float(t[1]-t[0])}
    return _HTML.replace("__TOKAMAK_CONFIG__", json.dumps(config))


_HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tokamak — live controls</title>
<style>
:root{color-scheme:dark;font-family:system-ui,sans-serif;background:#080e1c;color:#edf5ff}*{box-sizing:border-box}
body{margin:0;padding:24px}main{max-width:1080px;margin:auto}.eyebrow{font-size:12px;letter-spacing:2px;color:#6ce6ef;font-weight:700}
h1{font-size:clamp(24px,4vw,36px);margin:10px 0 20px}.panel{background:#0c1629;border:1px solid #23384f;border-radius:18px;overflow:hidden}
canvas{display:block;width:100%;height:480px;touch-action:none;cursor:grab}canvas:active{cursor:grabbing}
.controls{padding:22px;border-top:1px solid #23384f}.parameters{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:20px}
fieldset{margin:0;padding:12px;border:1px solid #28405a;border-radius:10px;min-width:0}legend{padding:0 5px;font-size:13px;font-weight:600}
.components{display:grid;grid-template-columns:repeat(3,1fr);gap:7px}label{display:block;color:#879bb5;font-size:12px}
input[type=number]{width:100%;margin-top:6px;padding:9px 6px;background:#080e1c;border:1px solid #28405a;border-radius:6px;color:#edf5ff;font:14px monospace}
input:focus-visible,button:focus-visible{outline:2px solid #ff85c8;outline-offset:3px}
.transport{display:flex;align-items:center;gap:12px}button{border:1px solid #38536d;border-radius:8px;padding:10px 16px;background:#14273e;color:#edf5ff;cursor:pointer;white-space:nowrap}button:hover{border-color:#6ce6ef}
#play{background:#6ce6ef;color:#080e1c;font-weight:700;min-width:82px}.timeline{flex:1}input[type=range]{width:100%;accent-color:#6ce6ef;cursor:pointer}#clock{color:#b7c9df;font:13px monospace;min-width:65px}
.note{color:#879bb5;font-size:12px;line-height:1.6;margin-top:16px}#error{color:#ffb3bd;font-size:13px;margin-bottom:12px}#error:empty{display:none}
@media(max-width:760px){body{padding:12px}.parameters{grid-template-columns:1fr 1fr}.controls{padding:15px}.transport{flex-wrap:wrap}.timeline{flex-basis:100%;order:5}canvas{height:400px}}
@media(max-width:410px){.parameters{grid-template-columns:1fr}}
</style></head>
<body><main><div class="eyebrow">TOKAMAK / SINGLE PARTICLE</div><h1>Explore magnetic confinement.</h1>
<div class="panel"><canvas id="scene" role="img" aria-label="Tokamak particle orbit, dotted magnetic and electric field lines, and poloidal cross-section"></canvas>
<div class="controls"><div class="parameters"><fieldset><legend>Magnetic field</legend><div class="components" style="grid-template-columns:1fr 1fr"><label for="b0">B₀<input id="b0" type="number" step="0.5"></label><label for="qs">Twist qₛ<input id="qs" type="number" step="0.1"></label><label for="ratio">q / m<input id="ratio" type="number" step="0.1"></label></div></fieldset><fieldset><legend>Electric field</legend><div class="components" style="grid-template-columns:1fr 1fr"><label for="ephi">Toroidal Eφ₀<input id="ephi" type="number" step="0.01"></label><label for="ke">Radial k_E<input id="ke" type="number" step="0.01"></label><label for="omega">Frequency ω<input id="omega" type="number" step="0.1"></label><label for="phase">Phase [rad]<input id="phase" type="number" step="0.1"></label></div></fieldset><fieldset><legend>Initial particle</legend><div class="components" style="grid-template-columns:1fr 1fr"><label for="r0">Starting r / a<input id="r0" type="number" step="0.05"></label><label for="theta0">Poloidal θ [°]<input id="theta0" type="number" step="5"></label><label for="vpar">v∥<input id="vpar" type="number" step="0.1"></label><label for="vperp">v⊥<input id="vperp" type="number" step="0.1"></label></div></fieldset><fieldset><legend>Geometry and duration</legend><div class="components" style="grid-template-columns:1fr 1fr"><label for="rmajor">Major radius R₀<input id="rmajor" type="number" step="0.1"></label><label for="aminor">Minor radius a<input id="aminor" type="number" step="0.1"></label><label for="tmax">Time limit<input id="tmax" type="number" step="5"></label></div></fieldset></div><div id="error" role="status"></div>
<div style="display:flex;gap:22px;margin-bottom:16px"><label><input id="showB" type="checkbox" checked> Dotted B lines</label><label><input id="showE" type="checkbox" checked> Dotted E lines</label></div><div class="transport"><button id="play" type="button">Play</button><button id="restart" type="button">Restart</button><button id="resetview" type="button">Reset view</button>
<div class="timeline"><label for="time">Time</label><input id="time" type="range" min="0" step="0.01" value="0"></div><span id="clock">0.00</span></div>
<div class="note">Edit any value to recalculate and restart. Drag the plot to rotate; scroll to zoom.<br>
Pink: particle orbit. Dotted cyan: B lines. Dotted gold: E lines. Arrows show field direction, not strength.<br>B is static. E is static when ω = 0; otherwise E lines show a time snapshot. Normalized units; prescribed fields, single particle.</div>
</div></div></main>
<script>
'use strict';
const config=__TOKAMAK_CONFIG__;
const canvas=document.getElementById('scene'),ctx=canvas.getContext('2d');
const ids=['b0','qs','ratio','ephi','ke','omega','phase','r0','theta0','vpar','vperp','rmajor','aminor','tmax'];
const inputs=ids.map(id=>document.getElementById(id));
const keys=['B0','qs','ratio','Ephi','kE','omega','phase','r0','theta','vpar','vperp','R0','a','duration'];
inputs.forEach((el,i)=>el.value=Number(config[keys[i]].toPrecision(12)));
const timeSlider=document.getElementById('time'),play=document.getElementById('play');
const showB=document.getElementById('showB'),showE=document.getElementById('showE');
const add=(a,b)=>a.map((v,i)=>v+b[i]),mul=(a,s)=>a.map(v=>v*s),norm=a=>Math.hypot(...a);
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
let active=null,orbit=null,currentTime=0,playing=false,lastStamp=null,yaw=-.8,pitch=.5,zoom=1,drag=null;
let shell=[],bLines=[],eLines=[],eSnapshotTime=NaN,seeds=[],extent=1;
function magnetic(p,c){const R=Math.hypot(p[0],p[1]),br=-c.B0*p[2]/(c.qs*R),bp=c.B0*c.R0/R;return [br*p[0]/R-bp*p[1]/R,br*p[1]/R+bp*p[0]/R,c.B0*(R-c.R0)/(c.qs*R)];}
function electric(p,time,c){const R=Math.hypot(p[0],p[1]),ep=c.Ephi*c.R0/R*Math.cos(c.omega*time+c.phase),er=-c.kE*(R-c.R0);return [er*p[0]/R-ep*p[1]/R,er*p[1]/R+ep*p[0]/R,-c.kE*p[2]];}
function minorRadius(p,c){return Math.hypot(Math.hypot(p[0],p[1])-c.R0,p[2]);}
function initialState(c){
 const theta=c.theta*Math.PI/180,phi=config.phi,r=c.r0*c.a;
 const p=[(c.R0+r*Math.cos(theta))*Math.cos(phi),(c.R0+r*Math.cos(theta))*Math.sin(phi),r*Math.sin(theta)];
 const B=magnetic(p,c),bn=norm(B),b=bn?mul(B,1/bn):[-Math.sin(phi),Math.cos(phi),0];
 const radial=[Math.cos(theta)*Math.cos(phi),Math.cos(theta)*Math.sin(phi),Math.sin(theta)];
 return {p,v:add(mul(b,c.vpar),mul(radial,c.vperp))};
}
function simulate(c){
 const inner=c.R0-c.a;
 const bound=Math.hypot(c.B0*c.R0/inner,c.B0*c.a/(c.qs*inner));
 const maxStep=Math.min(config.dt,.08/(Math.abs(c.ratio)*bound+1e-20));
 const count=Math.ceil(c.duration/maxStep);if(count>120000)throw Error('These settings need too many steps. Reduce time, |q/m| or field strength.');
 const dt=c.duration/count,state=initialState(c),positions=[state.p],velocities=[state.v];let wall=false;
 for(let i=0;i<count;i++){
  const p=positions[i],v=velocities[i],mid=add(p,mul(v,dt/2));
  if(Math.hypot(mid[0],mid[1])<1e-10)throw Error('Step reached the singular axis; reduce the velocity or time step.');
  const kick=mul(electric(mid,(i+.5)*dt,c),c.ratio*dt/2),minus=add(v,kick);
  const rotation=mul(magnetic(mid,c),c.ratio*dt/2),s=mul(rotation,2/(1+norm(rotation)**2));
  const prime=add(minus,cross(minus,rotation)),nextV=add(add(minus,cross(prime,s)),kick),nextP=add(mid,mul(nextV,dt/2));
  if([...nextP,...nextV].some(x=>!Number.isFinite(x)))throw Error('Numerical overflow; reduce the parameter magnitudes.');
  positions.push(nextP);velocities.push(nextV);
  if(minorRadius(nextP,c)>=c.a){wall=true;break;}
 }
 return {positions,velocities,dt,wall,duration:(positions.length-1)*dt};
}
function traceField(field,seed,c,length=8*Math.PI*c.R0){
 const ds=Math.min(.05*c.a,.05*c.R0*Math.abs(c.qs));
 const steps=Math.min(4500,Math.ceil(length/(2*ds)));
 function direction(p){const f=field(p),n=norm(f);return n>1e-12?mul(f,1/n):[0,0,0];}
 const branches=[];
 for(const sign of [-1,1]){let p=seed.slice();const pts=[p];const step=sign*ds;
  for(let i=0;i<steps;i++){
   const k1=direction(p);if(norm(k1)===0)break;
   const k2=direction(add(p,mul(k1,step/2))),k3=direction(add(p,mul(k2,step/2))),k4=direction(add(p,mul(k3,step)));
   const next=add(p,mul(add(add(k1,mul(k2,2)),add(mul(k3,2),k4)),step/6));
   if(minorRadius(next,c)>=c.a||norm(add(next,mul(p,-1)))<1e-12)break;
   pts.push(next);p=next;
  }branches.push(pts);
 }
 return branches[0].slice(1).reverse().concat(branches[1]);
}
function makeShell(c){
 const lines=[];
 for(let j=0;j<8;j++){const theta=j*Math.PI/4,pts=[];for(let i=0;i<=80;i++){const phi=i*2*Math.PI/80,R=c.R0+c.a*Math.cos(theta);pts.push([R*Math.cos(phi),R*Math.sin(phi),c.a*Math.sin(theta)]);}lines.push(pts);}
 for(let j=0;j<12;j++){const phi=j*2*Math.PI/12,pts=[];for(let i=0;i<=40;i++){const theta=i*2*Math.PI/40,R=c.R0+c.a*Math.cos(theta);pts.push([R*Math.cos(phi),R*Math.sin(phi),c.a*Math.sin(theta)]);}lines.push(pts);}
 return lines;
}
function rebuildFields(){
 seeds=[.35,.65].map((r,i)=>[active.R0+r*active.a*(i?-1:1),0,0]);
 shell=makeShell(active);bLines=seeds.map(seed=>traceField(p=>magnetic(p,active),seed,active));eSnapshotTime=NaN;
}
function refreshElectric(force=false){
 if(force||!Number.isFinite(eSnapshotTime)||(active.omega!==0&&Math.abs(currentTime-eSnapshotTime)>=.25)){
  eSnapshotTime=currentTime;eLines=seeds.map(seed=>traceField(p=>electric(p,eSnapshotTime,active),seed,active,4*Math.PI*active.R0));
 }
}
function recalculate(){
 try{
  if(inputs.some(el=>el.value.trim()===''||!Number.isFinite(Number(el.value))))throw Error('Enter a finite number in every parameter.');
  const c={};inputs.forEach((el,i)=>c[keys[i]]=Number(el.value));
  if(!(c.R0>c.a&&c.a>0))throw Error('Geometry requires R₀ > a > 0.');
  if(c.qs===0)throw Error('Twist qₛ must be nonzero.');
  if(c.r0<0||c.r0>=1)throw Error('Starting r/a must be between 0 (included) and 1 (excluded).');
  if(c.duration<=0)throw Error('Time limit must be positive.');
  const result=simulate(c);active=c;orbit=result;extent=2*(active.R0+1.15*active.a);currentTime=0;lastStamp=null;
  timeSlider.max=orbit.duration;timeSlider.step=orbit.dt;rebuildFields();refreshElectric(true);
  document.getElementById('error').textContent='';draw();
 }catch(e){document.getElementById('error').textContent=e.message;setPlaying(false);}
}
function project(p){
 const xx=Math.cos(yaw)*p[0]-Math.sin(yaw)*p[1],yy=Math.sin(yaw)*p[0]+Math.cos(yaw)*p[1];
 const vertical=Math.cos(pitch)*p[2]-Math.sin(pitch)*yy,scale=Math.min(canvas.clientWidth*.62,canvas.clientHeight*1.12)*zoom/extent;
 return [canvas.clientWidth*.36+xx*scale,canvas.clientHeight*.54-vertical*scale];
}
function line3D(points,color,width=1,alpha=1,dotted=false){
 if(points.length<2)return;ctx.beginPath();ctx.strokeStyle=color;ctx.lineWidth=width;ctx.globalAlpha=alpha;ctx.setLineDash(dotted?[1,5]:[]);ctx.lineCap='round';
 points.forEach((p,i)=>{const a=project(p);i?ctx.lineTo(...a):ctx.moveTo(...a);});ctx.stroke();ctx.globalAlpha=1;ctx.setLineDash([]);
}
function fieldArrow(p,vector,color){
 const n=norm(vector);if(n<1e-12)return;const b=project(add(p,mul(vector,.17*active.a/n))),a=project(p),angle=Math.atan2(b[1]-a[1],b[0]-a[0]);
 if(Math.hypot(b[0]-a[0],b[1]-a[1])<1)return;
 ctx.strokeStyle=color;ctx.lineWidth=1.5;ctx.beginPath();ctx.moveTo(...a);ctx.lineTo(...b);ctx.moveTo(b[0]-6*Math.cos(angle-.5),b[1]-6*Math.sin(angle-.5));ctx.lineTo(...b);ctx.lineTo(b[0]-6*Math.cos(angle+.5),b[1]-6*Math.sin(angle+.5));ctx.stroke();
}
function dottedLines(lines,field,color){for(const line of lines){line3D(line,color,1.3,.7,true);if(line.length>2){for(const fraction of [.35,.7]){const p=line[Math.floor(line.length*fraction)];fieldArrow(p,field(p),color);}}}}
function draw(){
 if(!orbit)return;refreshElectric();const w=canvas.clientWidth,h=canvas.clientHeight;
 ctx.clearRect(0,0,w,h);ctx.fillStyle='#0c1629';ctx.fillRect(0,0,w,h);ctx.font='12px system-ui';
 for(const line of shell)line3D(line,'#527b98',.7,.24);
 if(showB.checked)dottedLines(bLines,p=>magnetic(p,active),'#6ce6ef');
 if(showE.checked)dottedLines(eLines,p=>electric(p,eSnapshotTime,active),'#ffc56e');
 line3D(orbit.positions,'#ffb3dc',.7,.12);
 const index=Math.min(orbit.positions.length-1,Math.round(currentTime/orbit.dt));
 const start=Math.max(0,index-Math.round(16/orbit.dt)),trail=orbit.positions.slice(start,index+1);
 line3D(trail,'#ff85c8',7,.07);line3D(trail,'#ffb3dc',1.8,.95);
 const state=orbit.positions[index],p=project(state),glow=ctx.createRadialGradient(...p,2,...p,25);
 glow.addColorStop(0,'rgba(255,133,200,.4)');glow.addColorStop(1,'rgba(255,133,200,0)');ctx.fillStyle=glow;ctx.beginPath();ctx.arc(...p,25,0,Math.PI*2);ctx.fill();ctx.fillStyle='#ffd0e9';ctx.beginPath();ctx.arc(...p,6,0,Math.PI*2);ctx.fill();
 // Poloidal R-Z projection with a fixed vessel boundary.
 const insetX=w*.845,insetY=h*.45,radius=Math.min(w*.115,h*.24),rz=p=>[insetX+(Math.hypot(p[0],p[1])-active.R0)/active.a*radius,insetY-p[2]/active.a*radius];
 ctx.fillStyle='#b7c9df';ctx.font='11px system-ui';ctx.fillText('POLOIDAL R–Z',insetX-45,insetY-radius-20);
 ctx.strokeStyle='#6ce6ef';ctx.lineWidth=1;ctx.beginPath();ctx.arc(insetX,insetY,radius,0,Math.PI*2);ctx.stroke();
 ctx.strokeStyle='#28405a';ctx.beginPath();ctx.moveTo(insetX-radius,insetY);ctx.lineTo(insetX+radius,insetY);ctx.moveTo(insetX,insetY-radius);ctx.lineTo(insetX,insetY+radius);ctx.stroke();
 ctx.beginPath();ctx.strokeStyle='#ffb3dc';ctx.lineWidth=1;const skip=Math.max(1,Math.floor(index/2500));for(let i=0;i<=index;i+=skip){const point=rz(orbit.positions[i]);i?ctx.lineTo(...point):ctx.moveTo(...point);}ctx.stroke();const sectionPoint=rz(state);ctx.fillStyle='#ffd0e9';ctx.beginPath();ctx.arc(...sectionPoint,4,0,Math.PI*2);ctx.fill();
 ctx.font='12px monospace';ctx.fillStyle='#d3e5f8';const r=minorRadius(state,active)/active.a,status=orbit.wall&&index===orbit.positions.length-1?'WALL HIT':'IN VESSEL';
 ctx.fillText('t     '+currentTime.toFixed(2),20,30);ctx.fillText('r/a   '+r.toFixed(3),20,50);ctx.fillText('|v|   '+norm(orbit.velocities[index]).toFixed(3),20,70);ctx.fillText(status,20,90);
 ctx.font='11px system-ui';ctx.fillStyle='#879bb5';ctx.fillText(active.omega===0?'STATIC FIELDS':'E snapshot t = '+eSnapshotTime.toFixed(2),20,h-18);
 if(showE.checked&&!eLines.some(line=>line.length>1))ctx.fillText('E = 0 at this time',w*.72,h-18);
 timeSlider.value=currentTime;document.getElementById('clock').textContent=currentTime.toFixed(2);
}
function resize(){const ratio=window.devicePixelRatio||1;canvas.width=Math.round(canvas.clientWidth*ratio);canvas.height=Math.round(canvas.clientHeight*ratio);ctx.setTransform(ratio,0,0,ratio,0,0);draw();}
function setPlaying(value){playing=value;lastStamp=null;play.textContent=value?'Pause':'Play';}
let debounce;inputs.forEach(el=>el.addEventListener('input',()=>{clearTimeout(debounce);debounce=setTimeout(recalculate,180);}));
showB.addEventListener('change',draw);showE.addEventListener('change',draw);
timeSlider.addEventListener('input',()=>{setPlaying(false);currentTime=Number(timeSlider.value);if(active.omega!==0)eSnapshotTime=NaN;draw();});
play.addEventListener('click',()=>{if(orbit&&currentTime>=orbit.duration)currentTime=0;setPlaying(!playing);draw();});
document.getElementById('restart').addEventListener('click',()=>{currentTime=0;lastStamp=null;eSnapshotTime=NaN;draw();});
document.getElementById('resetview').addEventListener('click',()=>{yaw=-.8;pitch=.5;zoom=1;draw();});
canvas.addEventListener('pointerdown',e=>{drag={x:e.clientX,y:e.clientY};canvas.setPointerCapture(e.pointerId);});
canvas.addEventListener('pointermove',e=>{if(!drag)return;yaw+=(e.clientX-drag.x)*.008;pitch=Math.max(-1.45,Math.min(1.45,pitch+(e.clientY-drag.y)*.008));drag={x:e.clientX,y:e.clientY};draw();});
canvas.addEventListener('pointerup',()=>drag=null);canvas.addEventListener('pointercancel',()=>drag=null);
canvas.addEventListener('wheel',e=>{e.preventDefault();zoom=Math.max(.3,Math.min(3,zoom*Math.exp(-e.deltaY*.001)));draw();},{passive:false});
window.addEventListener('resize',resize);
function frame(stamp){if(playing&&orbit){if(lastStamp!==null){currentTime=Math.min(orbit.duration,currentTime+Math.min((stamp-lastStamp)/1000,.1)*orbit.duration/12);if(currentTime>=orbit.duration)setPlaying(false);}lastStamp=stamp;draw();}requestAnimationFrame(frame);}
recalculate();resize();requestAnimationFrame(frame);

</script></body></html>'''
