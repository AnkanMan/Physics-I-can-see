"""Standalone Lorentz-force player with editable uniform fields and initial state."""
import json


def make_lorentz_player(x, v, t, E, B, q, m):
    config = {"position": x[0].tolist(), "velocity": v[0].tolist(),
              "E": list(map(float, E)), "B": list(map(float, B)),
              "ratio": float(q / m), "duration": float(t[-1] - t[0]),
              "count": len(t)}
    return _HTML.replace("__LORENTZ_CONFIG__", json.dumps(config))


_HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Lorentz force — live controls</title>
<style>
:root{color-scheme:dark;font-family:system-ui,sans-serif;background:#080e1c;color:#edf5ff}*{box-sizing:border-box}
body{margin:0;padding:24px}main{max-width:1080px;margin:auto}.eyebrow{font-size:12px;letter-spacing:2px;color:#6ce6ef;font-weight:700}
h1{font-size:clamp(24px,4vw,36px);margin:10px 0 20px}.panel{background:#0c1629;border:1px solid #23384f;border-radius:18px;overflow:hidden}
canvas{display:block;width:100%;height:480px;touch-action:none;cursor:grab}canvas:active{cursor:grabbing}
.controls{padding:22px;border-top:1px solid #23384f}.parameters{display:grid;grid-template-columns:repeat(3,1fr) 0.65fr;gap:16px;margin-bottom:20px}
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
<body><main><div class="eyebrow">LORENTZ / IN MOTION</div><h1>Fields shape the motion.</h1>
<div class="panel"><canvas id="scene" role="img" aria-label="Three-dimensional particle trajectory; drag to rotate, scroll to zoom"></canvas>
<div class="controls"><div class="parameters">
<fieldset><legend style="color:#ffc56e">Electric field E</legend><div class="components">
<label for="ex">x<input id="ex" type="number" step="0.1"></label><label for="ey">y<input id="ey" type="number" step="0.1"></label><label for="ez">z<input id="ez" type="number" step="0.1"></label></div></fieldset>
<fieldset><legend style="color:#6ce6ef">Magnetic field B</legend><div class="components">
<label for="bx">x<input id="bx" type="number" step="0.1"></label><label for="by">y<input id="by" type="number" step="0.1"></label><label for="bz">z<input id="bz" type="number" step="0.1"></label></div></fieldset>
<fieldset><legend style="color:#ffb3dc">Initial velocity v₀</legend><div class="components">
<label for="vx">x<input id="vx" type="number" step="0.1"></label><label for="vy">y<input id="vy" type="number" step="0.1"></label><label for="vz">z<input id="vz" type="number" step="0.1"></label></div></fieldset>
<fieldset><legend>Charge / mass</legend><label for="ratio">q / m<input id="ratio" type="number" step="0.1"></label></fieldset>
</div><div id="error" role="status"></div>
<div class="transport"><button id="play" type="button">Play</button><button id="restart" type="button">Restart</button><button id="resetview" type="button">Reset view</button>
<div class="timeline"><label for="time">Time</label><input id="time" type="range" min="0" step="0.01" value="0"></div><span id="clock">0.00</span></div>
<div class="note">Edit any value to recalculate and restart. Drag the plot to rotate; scroll to zoom.<br>
Cyan: trajectory and B direction. Gold: E direction. Arrows show direction, not field strength. Normalized units; uniform, constant fields.</div>
</div></div></main>
<script>
'use strict';
const config=__LORENTZ_CONFIG__;
const canvas=document.getElementById('scene'),ctx=canvas.getContext('2d');
const ids=['ex','ey','ez','bx','by','bz','vx','vy','vz','ratio'];
const inputs=ids.map(id=>document.getElementById(id));
const defaults=[...config.E,...config.B,...config.velocity,config.ratio];
inputs.forEach((input,i)=>input.value=defaults[i]);
const timeSlider=document.getElementById('time'),play=document.getElementById('play');timeSlider.max=config.duration;
const add=(a,b)=>a.map((x,i)=>x+b[i]),mul=(a,s)=>a.map(x=>x*s);
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const norm=a=>Math.hypot(...a);
let positions=[],velocities=[],currentTime=0,playing=false,lastStamp=null;
let active={E:config.E,B:config.B,v0:config.velocity,ratio:config.ratio};
let center=[0,0,0],extent=1,yaw=-0.8,pitch=0.42,zoom=1,drag=null;
const dt=config.duration/(config.count-1);
function simulate(E,B,ratio,initialVelocity){
 const positions=[config.position.slice()],velocities=[initialVelocity.slice()];
 const kick=mul(E,ratio*dt/2),rotation=mul(B,ratio*dt/2);
 const s=mul(rotation,2/(1+norm(rotation)**2));
 for(let i=1;i<config.count;i++){
  const minus=add(velocities[i-1],kick);
  const prime=add(minus,cross(minus,rotation));
  const plus=add(minus,cross(prime,s));
  const next=add(plus,kick);
  positions.push(add(positions[i-1],mul(add(velocities[i-1],next),dt/2)));
  velocities.push(next);
 }
 return {positions,velocities};
}
function recalculate(){
 if(inputs.some(el=>el.value.trim()===''||!Number.isFinite(Number(el.value)))){
  document.getElementById('error').textContent='Enter a finite number in every field.';setPlaying(false);return;
 }
 const values=inputs.map(el=>Number(el.value));
 const next={E:values.slice(0,3),B:values.slice(3,6),v0:values.slice(6,9),ratio:values[9]};
 const result=simulate(next.E,next.B,next.ratio,next.v0);
 if(result.positions.some(p=>p.some(x=>!Number.isFinite(x)))){
  document.getElementById('error').textContent='These values exceed the numerical range. Reduce their magnitude.';setPlaying(false);return;
 }
 active=next;positions=result.positions;velocities=result.velocities;
 const lo=positions[0].slice(),hi=lo.slice();
 for(const p of positions)for(let j=0;j<3;j++){lo[j]=Math.min(lo[j],p[j]);hi[j]=Math.max(hi[j],p[j]);}
 center=lo.map((value,i)=>(value+hi[i])/2);extent=Math.max(1,...lo.map((value,i)=>hi[i]-value))*1.15;
 currentTime=0;lastStamp=null;document.getElementById('error').textContent='';draw();
}
function project(point){
 const p=point.map((x,i)=>(x-center[i])/extent);
 const xx=Math.cos(yaw)*p[0]-Math.sin(yaw)*p[1];
 const yy=Math.sin(yaw)*p[0]+Math.cos(yaw)*p[1];
 const vertical=Math.cos(pitch)*p[2]-Math.sin(pitch)*yy;
 const scale=Math.min(canvas.clientWidth*0.64,canvas.clientHeight*0.62)*zoom;
 return [canvas.clientWidth/2+xx*scale,canvas.clientHeight/2-vertical*scale];
}
function line3D(points,color,width=1,alpha=1){
 if(points.length<2)return;ctx.beginPath();ctx.strokeStyle=color;ctx.lineWidth=width;ctx.globalAlpha=alpha;
 points.forEach((p,i)=>{const a=project(p);i===0?ctx.moveTo(...a):ctx.lineTo(...a);});ctx.stroke();ctx.globalAlpha=1;
}
function arrow(origin,direction,color,label){
 if(norm(direction)<1e-12)return;
 const tip=add(origin,mul(direction,extent*.22/norm(direction))),a=project(origin),b=project(tip);
 if(Math.hypot(b[0]-a[0],b[1]-a[1])<2)return;
 line3D([origin,tip],color,2);const angle=Math.atan2(b[1]-a[1],b[0]-a[0]);
 ctx.fillStyle=color;ctx.beginPath();ctx.moveTo(...b);ctx.lineTo(b[0]-9*Math.cos(angle-.4),b[1]-9*Math.sin(angle-.4));ctx.lineTo(b[0]-9*Math.cos(angle+.4),b[1]-9*Math.sin(angle+.4));ctx.closePath();ctx.fill();ctx.fillText(label,b[0]+7,b[1]+(label==='E'?14:-5));
}
function draw(){
 if(!positions.length)return;
 const w=canvas.clientWidth,h=canvas.clientHeight;ctx.clearRect(0,0,w,h);ctx.fillStyle='#0c1629';ctx.fillRect(0,0,w,h);ctx.font='12px system-ui';
 const base=center.map(x=>x-extent*.48),edge=extent*.96;
 for(let i=0;i<=4;i++){
  line3D([base.map((x,j)=>j===0?x+edge*i/4:x),base.map((x,j)=>j===0?x+edge*i/4:j===1?x+edge:x)],'#28405a',.7,.5);
  line3D([base.map((x,j)=>j===1?x+edge*i/4:x),base.map((x,j)=>j===1?x+edge*i/4:j===0?x+edge:x)],'#28405a',.7,.5);
 }
 for(let j=0;j<3;j++){
  const end=base.slice();end[j]+=edge;line3D([base,end],'#52718b',1,.7);
  const p=project(end);ctx.fillStyle='#b7c9df';ctx.fillText(['x','y','z'][j],p[0]+7,p[1]);
 }
 line3D(positions,'#6ce6ef',1,.14);
 const index=Math.min(config.count-1,Math.round(currentTime/dt));
 const start=Math.max(0,index-Math.round(2.5/dt)),trail=positions.slice(start,index+1);
 line3D(trail,'#6ce6ef',8,.06);line3D(trail,'#6ce6ef',2.2,.95);
 arrow(config.position,active.B,'#6ce6ef','B');arrow(config.position,active.E,'#ffc56e','E');
 const p=project(positions[index]),glow=ctx.createRadialGradient(...p,3,...p,28);
 glow.addColorStop(0,'rgba(255,133,200,0.35)');glow.addColorStop(1,'rgba(255,133,200,0)');
 ctx.fillStyle=glow;ctx.beginPath();ctx.arc(...p,28,0,Math.PI*2);ctx.fill();
 ctx.fillStyle='#ffd0e9';ctx.strokeStyle='#ff85c8';ctx.lineWidth=2;ctx.beginPath();ctx.arc(...p,7,0,Math.PI*2);ctx.fill();ctx.stroke();
 ctx.fillStyle='rgba(8,14,28,0.88)';ctx.fillRect(18,16,178,100);ctx.fillStyle='#d3e5f8';ctx.font='13px monospace';
 ctx.fillText('t     '+currentTime.toFixed(2),30,40);ctx.fillText('|v|   '+norm(velocities[index]).toFixed(3),30,62);ctx.fillText('q/m   '+active.ratio.toFixed(3),30,84);ctx.fillText('|B|   '+norm(active.B).toFixed(3),30,106);
 timeSlider.value=currentTime;document.getElementById('clock').textContent=currentTime.toFixed(2);
}
function resize(){const ratio=window.devicePixelRatio||1;canvas.width=Math.round(canvas.clientWidth*ratio);canvas.height=Math.round(canvas.clientHeight*ratio);ctx.setTransform(ratio,0,0,ratio,0,0);draw();}
function setPlaying(value){playing=value;lastStamp=null;play.textContent=value?'Pause':'Play';}
let debounce;inputs.forEach(el=>el.addEventListener('input',()=>{clearTimeout(debounce);debounce=setTimeout(recalculate,100);}));
timeSlider.addEventListener('input',()=>{setPlaying(false);currentTime=Number(timeSlider.value);draw();});
play.addEventListener('click',()=>{if(currentTime>=config.duration)currentTime=0;setPlaying(!playing);draw();});
document.getElementById('restart').addEventListener('click',()=>{currentTime=0;lastStamp=null;draw();});
document.getElementById('resetview').addEventListener('click',()=>{yaw=-.8;pitch=.42;zoom=1;draw();});
canvas.addEventListener('pointerdown',e=>{drag={x:e.clientX,y:e.clientY};canvas.setPointerCapture(e.pointerId);});
canvas.addEventListener('pointermove',e=>{if(!drag)return;yaw+=(e.clientX-drag.x)*.008;pitch=Math.max(-1.45,Math.min(1.45,pitch+(e.clientY-drag.y)*.008));drag={x:e.clientX,y:e.clientY};draw();});
canvas.addEventListener('pointerup',()=>drag=null);canvas.addEventListener('pointercancel',()=>drag=null);
canvas.addEventListener('wheel',e=>{e.preventDefault();zoom=Math.max(.3,Math.min(4,zoom*Math.exp(-e.deltaY*.001)));draw();},{passive:false});
window.addEventListener('resize',resize);
function frame(stamp){if(playing){if(lastStamp!==null){currentTime=Math.min(config.duration,currentTime+Math.min((stamp-lastStamp)/1000,.1));if(currentTime>=config.duration)setPlaying(false);}lastStamp=stamp;draw();}requestAnimationFrame(frame);}
recalculate();resize();requestAnimationFrame(frame);
</script></body></html>'''
