"""Standalone Vicsek player. Keep the time-step convention in Viscek.ipynb."""
import json


def make_vicsek_player(N, L, v_0, R, eta, dt, n_steps, seed):
    config = {"N": int(N), "L": float(L), "v0": float(v_0), "R": float(R),
              "eta": float(eta), "dt": float(dt), "steps": int(n_steps),
              "seed": int(seed) % (2**32) if seed is not None else 42}
    return _HTML.replace("__VICSEK_CONFIG__", json.dumps(config))


_HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Vicsek model — live controls</title>
<style>
:root{color-scheme:dark;font-family:system-ui,sans-serif;background:#080e1c;color:#edf5ff}*{box-sizing:border-box}
body{margin:0;padding:24px}main{max-width:1080px;margin:auto}.eyebrow{font-size:12px;letter-spacing:2px;color:#6ce6ef;font-weight:700}
h1{font-size:clamp(24px,4vw,36px);margin:10px 0 20px}.panel{background:#0c1629;border:1px solid #23384f;border-radius:18px;overflow:hidden}
canvas{display:block;width:100%;height:510px;touch-action:none;cursor:default}canvas:active{cursor:grabbing}
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
<body><main><div class="eyebrow">VICSEK / COLLECTIVE MOTION</div><h1>Simple rules. Moving together.</h1>
<div class="panel"><canvas id="scene" role="img" aria-label="Vicsek particles in a periodic two-dimensional box, with heading arrows and an alignment history"></canvas>
<div class="controls"><div class="parameters"><fieldset><legend>Particles and box</legend><div class="components" style="grid-template-columns:1fr 1fr"><label for="n">Count N<input id="n" type="number" step="1"></label><label for="box">Box size L<input id="box" type="number" step="1"></label></div></fieldset><fieldset><legend>Motion and neighbors</legend><div class="components" style="grid-template-columns:1fr 1fr"><label for="speed">Speed v₀<input id="speed" type="number" step="0.05"></label><label for="radius">Radius R<input id="radius" type="number" step="0.1"></label></div></fieldset><fieldset><legend>Random turning</legend><div class="components" style="grid-template-columns:1fr 1fr"><label for="noise">Noise rate η<input id="noise" type="number" step="0.1"></label><label for="dt">Time step Δt<input id="dt" type="number" step="0.1"></label></div></fieldset><fieldset><legend>Duration and seed</legend><div class="components" style="grid-template-columns:1fr 1fr"><label for="steps">Steps<input id="steps" type="number" step="10"></label><label for="seed">Random seed<input id="seed" type="number" step="1"></label></div></fieldset></div><div id="error" role="status"></div>
<div class="transport"><button id="play" type="button">Play</button><button id="restart" type="button">Restart</button>
<div class="timeline"><label for="time">Time</label><input id="time" type="range" min="0" step="0.01" value="0"></div><span id="clock">0.00</span></div>
<div class="note">Edit any value to recalculate and restart. Arrows show heading; colors show direction.<br>Periodic boundaries connect opposite sides. Turning noise is multiplied by Δt; positions advance with the current velocity.</div>
</div></div></main>
<script>
'use strict';
const config=__VICSEK_CONFIG__;
const canvas=document.getElementById('scene'),ctx=canvas.getContext('2d');
const ids=['n','box','speed','radius','noise','dt','steps','seed'];
const keys=['N','L','v0','R','eta','dt','steps','seed'];
const inputs=ids.map(id=>document.getElementById(id));inputs.forEach((el,i)=>el.value=config[keys[i]]);
const timeSlider=document.getElementById('time'),play=document.getElementById('play');
let active=null,data=null,currentTime=0,playing=false,lastStamp=null;
function randomGenerator(seed){let state=seed>>>0;return ()=>{state=(state+0x6D2B79F5)>>>0;let z=state;z=Math.imul(z^(z>>>15),z|1);z^=z+Math.imul(z^(z>>>7),z|61);return ((z^(z>>>14))>>>0)/4294967296;};}
function simulate(c,initial=null,noiseTape=null){
 const rng=randomGenerator(c.seed),N=c.N,frames=c.steps+1;
 const xs=new Float64Array(frames*N*2),angles=new Float64Array(frames*N),order=new Float64Array(frames);
 for(let i=0;i<N;i++){xs[2*i]=initial?initial.x[i][0]:rng()*c.L;xs[2*i+1]=initial?initial.x[i][1]:rng()*c.L;}
 for(let i=0;i<N;i++)angles[i]=initial?initial.theta[i]:rng()*2*Math.PI;
 function alignment(frame){let cx=0,sy=0;for(let i=0;i<N;i++){cx+=Math.cos(angles[frame*N+i]);sy+=Math.sin(angles[frame*N+i]);}order[frame]=Math.hypot(cx,sy)/N;}
 alignment(0);
 for(let step=0;step<c.steps;step++){
  const previous=step*N,next=(step+1)*N;
  for(let i=0;i<N;i++){
   let cx=0,sy=0;
   for(let j=0;j<N;j++){
    let dx=xs[2*(previous+i)]-xs[2*(previous+j)],dy=xs[2*(previous+i)+1]-xs[2*(previous+j)+1];
    dx-=c.L*Math.round(dx/c.L);dy-=c.L*Math.round(dy/c.L);
    if(dx*dx+dy*dy<=c.R*c.R){cx+=Math.cos(angles[previous+j]);sy+=Math.sin(angles[previous+j]);}
   }
   const average=Math.hypot(cx,sy)>1e-12?Math.atan2(sy,cx):angles[previous+i];
   const randomRate=noiseTape?noiseTape[step*N+i]:c.eta*(rng()-.5);
   angles[next+i]=((average+randomRate*c.dt)%(2*Math.PI)+2*Math.PI)%(2*Math.PI);
   // Use the CURRENT velocity for position, matching the notebook convention.
   const oldAngle=angles[previous+i];
   xs[2*(next+i)]=((xs[2*(previous+i)]+c.v0*Math.cos(oldAngle)*c.dt)%c.L+c.L)%c.L;
   xs[2*(next+i)+1]=((xs[2*(previous+i)+1]+c.v0*Math.sin(oldAngle)*c.dt)%c.L+c.L)%c.L;
  }alignment(step+1);
 }
 return {xs,angles,order};
}
function recalculate(){try{
 if(inputs.some(el=>el.value.trim()===''||!Number.isFinite(Number(el.value))))throw Error('Enter a finite number in every field.');
 const c={};inputs.forEach((el,i)=>c[keys[i]]=Number(el.value));
 if(!Number.isInteger(c.N)||c.N<1||c.N>500)throw Error('Use an integer particle count from 1 to 500.');
 if(!Number.isInteger(c.steps)||c.steps<1||c.steps>2000)throw Error('Use an integer step count from 1 to 2000.');
 if(c.N*c.N*c.steps>60000000)throw Error('Reduce particle count or steps for a responsive simulation.');
 if(c.L<=0||c.dt<=0||c.v0<0||c.R<0||c.eta<0)throw Error('Box size/time step must be positive; speed, radius and noise must be nonnegative.');
 if(!Number.isInteger(c.seed)||c.seed<0||c.seed>4294967295)throw Error('Use an integer seed between 0 and 4294967295.');
 if(!Number.isFinite(c.steps*c.dt)||!Number.isFinite(c.v0*c.dt)||!Number.isFinite(c.eta*c.dt))throw Error('Parameter magnitudes are too large.');
 const next=simulate(c);data=next;active=c;currentTime=0;lastStamp=null;timeSlider.max=c.steps*c.dt;timeSlider.step=c.dt;
 document.getElementById('error').textContent='';draw();
}catch(e){document.getElementById('error').textContent=e.message;setPlaying(false);}}
function draw(){
 if(!data)return;const w=canvas.clientWidth,h=canvas.clientHeight;
 ctx.fillStyle='#0c1629';ctx.fillRect(0,0,w,h);const size=Math.min(w<680?w-70:w*.65,h-100),left=45,top=60;
 const index=Math.min(active.steps,Math.round(currentTime/active.dt)),offset=index*active.N;
 ctx.strokeStyle='#23384f';ctx.lineWidth=1;
 for(let j=0;j<=5;j++){const d=size*j/5;ctx.beginPath();ctx.moveTo(left+d,top);ctx.lineTo(left+d,top+size);ctx.moveTo(left,top+d);ctx.lineTo(left+size,top+d);ctx.stroke();}
 ctx.strokeStyle='#6ce6ef';ctx.globalAlpha=.35;ctx.strokeRect(left,top,size,size);ctx.globalAlpha=1;
 const arrowSize=Math.max(5,Math.min(13,size*.035));
 for(let i=0;i<active.N;i++){
  const angle=data.angles[offset+i],px=left+data.xs[2*(offset+i)]/active.L*size,py=top+size-data.xs[2*(offset+i)+1]/active.L*size;
  ctx.save();ctx.beginPath();ctx.rect(left,top,size,size);ctx.clip();ctx.translate(px,py);ctx.rotate(-angle);
  const color=`hsl(${angle*180/Math.PI} 80% 70%)`;ctx.fillStyle=color;ctx.shadowColor=color;ctx.shadowBlur=6;
  ctx.beginPath();ctx.moveTo(arrowSize*.65,0);ctx.lineTo(-arrowSize*.4,arrowSize*.3);ctx.lineTo(-arrowSize*.2,0);ctx.lineTo(-arrowSize*.4,-arrowSize*.3);ctx.closePath();ctx.fill();ctx.restore();
 }
 ctx.font='12px monospace';ctx.fillStyle='#d3e5f8';ctx.fillText(`t  ${currentTime.toFixed(2)}   step ${index} / ${active.steps}`,left,28);
 ctx.fillStyle='#879bb5';ctx.font='11px system-ui';ctx.fillText('0',left-15,top+size+17);ctx.fillText(active.L.toFixed(1),left+size-12,top+size+17);ctx.fillText('x',left+size/2,top+size+33);ctx.fillText('y',left-22,top+size/2);
 const align=data.order[index];
 if(w>=680){
  const gx=w*.77,gy=100,gw=w*.18,gh=135;
  ctx.fillStyle='#b7c9df';ctx.font='12px system-ui';ctx.fillText('COLLECTIVE ALIGNMENT',gx,gy-25);
  ctx.fillStyle='#6ce6ef';ctx.font='bold 30px monospace';ctx.fillText(align.toFixed(3),gx,gy+15);
  const chartY=gy+60;ctx.strokeStyle='#28405a';ctx.lineWidth=1;ctx.strokeRect(gx,chartY,gw,gh);
  ctx.beginPath();ctx.strokeStyle='#6ce6ef';ctx.lineWidth=2;
  for(let j=0;j<=index;j++){const px=gx+j/active.steps*gw,py=chartY+gh*(1-data.order[j]);j?ctx.lineTo(px,py):ctx.moveTo(px,py);}ctx.stroke();
  ctx.fillStyle='#879bb5';ctx.font='11px system-ui';ctx.fillText('1 = aligned',gx,chartY+gh+22);ctx.fillText('0 = cancelling directions',gx,chartY+gh+40);ctx.fillText('Colors show heading',gx,chartY+gh+76);
 }else{ctx.fillStyle='#6ce6ef';ctx.fillText('Alignment '+align.toFixed(3),left,top+size+51);}
 timeSlider.value=currentTime;document.getElementById('clock').textContent=currentTime.toFixed(2);
}
function resize(){const ratio=window.devicePixelRatio||1;canvas.width=Math.round(canvas.clientWidth*ratio);canvas.height=Math.round(canvas.clientHeight*ratio);ctx.setTransform(ratio,0,0,ratio,0,0);draw();}
function setPlaying(value){playing=value;lastStamp=null;play.textContent=value?'Pause':'Play';}
let debounce;inputs.forEach(el=>el.addEventListener('input',()=>{clearTimeout(debounce);debounce=setTimeout(recalculate,160);}));
timeSlider.addEventListener('input',()=>{setPlaying(false);currentTime=Number(timeSlider.value);draw();});
play.addEventListener('click',()=>{if(active&&currentTime>=active.steps*active.dt)currentTime=0;setPlaying(!playing);draw();});
document.getElementById('restart').addEventListener('click',()=>{currentTime=0;lastStamp=null;draw();});
window.addEventListener('resize',resize);
function frame(stamp){if(playing&&active){if(lastStamp!==null){const duration=active.steps*active.dt;currentTime=Math.min(duration,currentTime+Math.min((stamp-lastStamp)/1000,.1)*duration/12);if(currentTime>=duration)setPlaying(false);}lastStamp=stamp;draw();}requestAnimationFrame(frame);}
recalculate();resize();requestAnimationFrame(frame);

</script></body></html>'''
