"""Self-contained MIPS player; mirror the update rules in Mips.ipynb."""
import json


def make_mips_player(N, L, v_0, mu, A, kappa, D_r, dt, n_steps, seed):
    config = {"N": int(N), "L": float(L), "v0": float(v_0),
              "mu": float(mu), "A": float(A), "kappa": float(kappa),
              "Dr": float(D_r), "dt": float(dt), "steps": int(n_steps),
              "seed": int(seed) % (2**32) if seed is not None else 42}
    return _HTML.replace("__MIPS_CONFIG__", json.dumps(config))


_HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MIPS — live controls</title>
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
<body><main><div class="eyebrow">MIPS / ACTIVE PARTICLES</div><h1>Self propulsion meets repulsion.</h1>
<div class="panel"><canvas id="scene" role="img" aria-label="Repulsive active particles in a periodic box, with heading arrows and mean drift speed"></canvas>
<div style="padding:16px 22px;border-top:1px solid #23384f"><strong style="color:#6ce6ef">KDE mean velocity</strong><span style="color:#879bb5;font-size:12px"> · synchronized with the particle timeline</span></div>
<canvas id="kde-scene" role="img" aria-label="Animated periodic KDE average velocity field"></canvas>
<div class="controls"><fieldset style="margin-bottom:18px"><legend>KDE field</legend><div class="components" style="grid-template-columns:repeat(auto-fit,minmax(110px,1fr))">
<label for="kde-width">Width h/L<input id="kde-width" type="number" min="0.01" max="0.5" step="0.01" value="0.06"></label>
<label for="kde-grid">Grid points / side<input id="kde-grid" type="number" min="12" max="48" step="2" value="24"></label>
<label for="kde-window">Trailing window Δt<input id="kde-window" type="number" min="0" step="0.05" value="0"></label>
<label for="kde-floor">Density floor / (N/L²)<input id="kde-floor" type="number" min="0" max="1" step="0.01" value="0.05"></label>
<label for="kde-visible">Show KDE<input id="kde-visible" type="checkbox" checked></label></div><div id="kde-error" role="status" style="color:#ffb3bd;font-size:12px;margin-top:8px"></div></fieldset>
<div class="parameters"><fieldset><legend>Particles and box</legend><div class="components" style="grid-template-columns:1fr 1fr"><label for="n">Count N<input id="n" type="number" step="1"></label><label for="box">Box size L<input id="box" type="number" step="1"></label></div></fieldset><fieldset><legend>Propulsion and mobility</legend><div class="components" style="grid-template-columns:1fr 1fr"><label for="speed">Speed v₀<input id="speed" type="number" step="0.1"></label><label for="mobility">Mobility μ<input id="mobility" type="number" step="0.1"></label></div></fieldset><fieldset><legend>Yukawa repulsion</legend><div class="components" style="grid-template-columns:1fr 1fr"><label for="strength">Strength A<input id="strength" type="number" step="0.1"></label><label for="screen">Screening κ<input id="screen" type="number" step="0.1"></label></div></fieldset><fieldset><legend>Diffusion and time</legend><div class="components" style="grid-template-columns:1fr 1fr"><label for="noise">Rotation Dᵣ<input id="noise" type="number" step="0.01"></label><label for="dt">Time step Δt<input id="dt" type="number" step="0.001"></label><label for="steps">Steps<input id="steps" type="number" step="100"></label><label for="seed">Seed<input id="seed" type="number" step="1"></label></div></fieldset></div><div id="error" role="status"></div>
<div class="transport"><button id="play" type="button">Play</button><button id="restart" type="button">Restart</button>
<div class="timeline"><label for="time">Time</label><input id="time" type="range" min="0" step="0.01" value="0"></div><span id="clock">0.00</span></div>
<div class="note">Edit any value to recalculate and restart. Arrows show heading; colors show direction.<br>Periodic boundaries connect opposite sides. Brownian turning: √(2DᵣΔt) × Gaussian noise; no alignment.<br>Arrows indicate propulsion heading, not total drift. Marker size is cosmetic. Phase separation depends on density, persistence, and run duration.<br>Clustering preset: L = 7, Dᵣ = 0.02, duration = 100. Clustering is not guaranteed.<br>Long runs calculate in chunks; the slider stores up to about 2,001 snapshots. Large forces may need a smaller Δt. KDE uses total drift velocities and periodic Gaussian averaging; its trailing window samples up to seven stored snapshots. Changing KDE settings redraws the field without rerunning particles. Browser controls affect this page only; the MP4 records the notebook run.</div>
</div></div></main>
<script>
'use strict';
const config=__MIPS_CONFIG__;
const canvas=document.getElementById('scene'),ctx=canvas.getContext('2d');
const ids=['n','box','speed','mobility','strength','screen','noise','dt','steps','seed'];
const keys=['N','L','v0','mu','A','kappa','Dr','dt','steps','seed'];
const inputs=ids.map(id=>document.getElementById(id));inputs.forEach((el,i)=>el.value=config[keys[i]]);
const timeSlider=document.getElementById('time'),play=document.getElementById('play');
let active=null,data=null,currentTime=0,playing=false,lastStamp=null;
function randomGenerator(seed){let state=seed>>>0;return ()=>{state=(state+0x6D2B79F5)>>>0;let z=state;z=Math.imul(z^(z>>>15),z|1);z^=z+Math.imul(z^(z>>>7),z|61);return ((z^(z>>>14))>>>0)/4294967296;};}
// Pairwise minimum-image Yukawa force, synchronous Euler drift, Brownian turning.
function* simulationSteps(c,initial=null,noiseTape=null){
 const rng=randomGenerator(c.seed),N=c.N,stride=Math.max(1,Math.ceil(c.steps/2000)),frames=Math.ceil(c.steps/stride)+1;
 const xs=new Float64Array(frames*N*2),angles=new Float64Array(frames*N),speed=new Float64Array(frames),sampleSteps=new Uint32Array(frames);
 const position=new Float64Array(N*2),heading=new Float64Array(N);let saved=0;
 const vs=new Float64Array(frames*N*2);
 const force=new Float64Array(N*2),side=Math.ceil(Math.sqrt(N)),spacing=c.L/side;
 const cells=Array.from({length:side*side},(_,i)=>i);
 for(let j=cells.length-1;j>0;j--){const k=Math.floor(rng()*(j+1));[cells[j],cells[k]]=[cells[k],cells[j]];}
 for(let i=0;i<N;i++){
  position[2*i]=initial?initial.x[i][0]:spacing*(cells[i]%side+.5)+spacing*.2*(rng()-.5);
  position[2*i+1]=initial?initial.x[i][1]:spacing*(Math.floor(cells[i]/side)+.5)+spacing*.2*(rng()-.5);
 }
 for(let i=0;i<N;i++)heading[i]=initial?initial.theta[i]:rng()*2*Math.PI;
 let spare=null;
 function gaussian(){if(spare!==null){const value=spare;spare=null;return value;}
  const radius=Math.sqrt(-2*Math.log(1-rng())),phase=2*Math.PI*rng();
  spare=radius*Math.sin(phase);return radius*Math.cos(phase);}
 for(let step=0;step<=c.steps;step++){
  force.fill(0);let meanSpeed=0;
  const save=step%stride===0||step===c.steps;
  if(save){xs.set(position,saved*N*2);angles.set(heading,saved*N);sampleSteps[saved]=step;}
  if(c.A!==0)for(let i=0;i<N;i++)for(let j=i+1;j<N;j++){
   let dx=position[2*i]-position[2*j],dy=position[2*i+1]-position[2*j+1];
   dx-=c.L*Math.round(dx/c.L);dy-=c.L*Math.round(dy/c.L);
   const r=Math.hypot(dx,dy);if(r===0)throw Error('Particles coincide; reduce Δt or change initialization.');
   const coefficient=c.A*Math.exp(-c.kappa*r)*(1/(r*r*r)+c.kappa/(r*r));
   const fx=coefficient*dx,fy=coefficient*dy;
   force[2*i]+=fx;force[2*i+1]+=fy;force[2*j]-=fx;force[2*j+1]-=fy;
  }
  for(let i=0;i<N;i++){
   const angle=heading[i],vx=c.v0*Math.cos(angle)+c.mu*force[2*i],vy=c.v0*Math.sin(angle)+c.mu*force[2*i+1];
   if(!Number.isFinite(vx)||!Number.isFinite(vy)||!Number.isFinite(vx*c.dt)||!Number.isFinite(vy*c.dt))throw Error('Numerical overflow; reduce Δt or force strength.');
   meanSpeed+=Math.hypot(vx,vy)/N;
   if(save){vs[2*(saved*N+i)]=vx;vs[2*(saved*N+i)+1]=vy;}
   if(step<c.steps){
    position[2*i]=((position[2*i]+vx*c.dt)%c.L+c.L)%c.L;
    position[2*i+1]=((position[2*i+1]+vy*c.dt)%c.L+c.L)%c.L;
    const z=noiseTape?noiseTape[step*N+i]:gaussian();
    heading[i]=((angle+Math.sqrt(2*c.Dr*c.dt)*z)%(2*Math.PI)+2*Math.PI)%(2*Math.PI);
   }
  }
  if(save)speed[saved++]=meanSpeed;
  if(step%250===0)yield step;
 }
 return {xs,vs,angles,speed,sampleSteps,stride,speedMax:Math.max(1e-6,...speed)*1.05};
}
// Synchronous entry point for small parity checks; the UI runs chunks asynchronously.
function simulate(c,initial=null,noiseTape=null){const run=simulationSteps(c,initial,noiseTape);let result;do{result=run.next();}while(!result.done);return result.value;}
let calculation=0;
async function recalculate(){const token=++calculation;setPlaying(false);try{
 if(inputs.some(el=>el.value.trim()===''||!Number.isFinite(Number(el.value))))throw Error('Enter a finite number in every field.');
 const c={};inputs.forEach((el,i)=>c[keys[i]]=Number(el.value));
 if(!Number.isInteger(c.N)||c.N<1||c.N>500)throw Error('Use an integer particle count from 1 to 500.');
 if(!Number.isInteger(c.steps)||c.steps<1||c.steps>100000)throw Error('Use an integer step count from 1 to 100000.');
 if(c.N*c.N*c.steps>1000000000)throw Error('Reduce particle count or steps for a responsive simulation.');
 if(c.L<=0||c.dt<=0||c.v0<0||c.mu<0||c.A<0||c.kappa<0||c.Dr<0)throw Error('Box size/time step must be positive; speed, mobility, repulsion and diffusion must be nonnegative.');
 if(!Number.isInteger(c.seed)||c.seed<0||c.seed>4294967295)throw Error('Use an integer seed between 0 and 4294967295.');
 if(!Number.isFinite(c.steps*c.dt)||!Number.isFinite(c.v0*c.dt)||!Number.isFinite(2*c.Dr*c.dt))throw Error('Parameter magnitudes are too large.');
 document.getElementById('error').textContent='Calculating…';
 const run=simulationSteps(c);let result;
 do{result=run.next();if(!result.done){
  document.getElementById('error').textContent=`Calculating ${Math.round(100*result.value/c.steps)}%…`;
  await new Promise(resolve=>setTimeout(resolve,0));if(token!==calculation)return;
 }}while(!result.done);
 const next=result.value;kdeCache.clear();data=next;active=c;currentTime=0;lastStamp=null;timeSlider.max=c.steps*c.dt;timeSlider.step=c.dt;
 document.getElementById('error').textContent='';draw();
}catch(e){document.getElementById('error').textContent=e.message;setPlaying(false);}}
function draw(){
 if(!data)return;const w=canvas.clientWidth,h=canvas.clientHeight;
 ctx.fillStyle='#0c1629';ctx.fillRect(0,0,w,h);const size=Math.min(w<680?w-70:w*.65,h-100),left=45,top=60;
 const index=Math.min(data.speed.length-1,Math.round(currentTime/active.dt/data.stride)),offset=index*active.N;
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
 ctx.font='12px monospace';ctx.fillStyle='#d3e5f8';ctx.fillText(`t  ${currentTime.toFixed(2)}   step ${data.sampleSteps[index]} / ${active.steps}`,left,28);
 ctx.fillStyle='#879bb5';ctx.font='11px system-ui';ctx.fillText('0',left-15,top+size+17);ctx.fillText(active.L.toFixed(1),left+size-12,top+size+17);ctx.fillText('x',left+size/2,top+size+33);ctx.fillText('y',left-22,top+size/2);
 const meanSpeed=data.speed[index];
 if(w>=680){
  const gx=w*.77,gy=100,gw=w*.18,gh=135;
  ctx.fillStyle='#b7c9df';ctx.font='12px system-ui';ctx.fillText('MEAN DRIFT SPEED',gx,gy-25);
  ctx.fillStyle='#6ce6ef';ctx.font='bold 30px monospace';ctx.fillText(meanSpeed.toFixed(3),gx,gy+15);
  const chartY=gy+60;ctx.strokeStyle='#28405a';ctx.lineWidth=1;ctx.strokeRect(gx,chartY,gw,gh);
  ctx.beginPath();ctx.strokeStyle='#6ce6ef';ctx.lineWidth=2;
  for(let j=0;j<=index;j++){const px=gx+data.sampleSteps[j]/active.steps*gw,py=chartY+gh*(1-data.speed[j]/data.speedMax);j?ctx.lineTo(px,py):ctx.moveTo(px,py);}ctx.stroke();
  ctx.fillStyle='#879bb5';ctx.font='11px system-ui';ctx.fillText('|v₀ heading + μ force|' ,gx,chartY+gh+22);ctx.fillText('Averaged over particles',gx,chartY+gh+40);ctx.fillText('Colors show heading',gx,chartY+gh+76);
 }else{ctx.fillStyle='#6ce6ef';ctx.fillText('Mean speed '+meanSpeed.toFixed(3),left,top+size+51);}
 timeSlider.value=currentTime;document.getElementById('clock').textContent=currentTime.toFixed(2);drawKDE(index);
}
function resize(){const ratio=window.devicePixelRatio||1;canvas.width=Math.round(canvas.clientWidth*ratio);canvas.height=Math.round(canvas.clientHeight*ratio);ctx.setTransform(ratio,0,0,ratio,0,0);kdeCanvas.width=Math.round(kdeCanvas.clientWidth*ratio);kdeCanvas.height=Math.round(kdeCanvas.clientHeight*ratio);kdeCtx.setTransform(ratio,0,0,ratio,0,0);draw();}
function setPlaying(value){playing=value;lastStamp=null;play.textContent=value?'Pause':'Play';}
let debounce;inputs.forEach(el=>el.addEventListener('input',()=>{clearTimeout(debounce);calculation++;setPlaying(false);debounce=setTimeout(recalculate,160);}));
timeSlider.addEventListener('input',()=>{setPlaying(false);currentTime=Number(timeSlider.value);draw();});
play.addEventListener('click',()=>{if(document.getElementById('error').textContent)return;if(active&&currentTime>=active.steps*active.dt)currentTime=0;setPlaying(!playing);draw();});
document.getElementById('restart').addEventListener('click',()=>{currentTime=0;lastStamp=null;draw();});
window.addEventListener('resize',resize);
function frame(stamp){if(playing&&active){if(lastStamp!==null){const duration=active.steps*active.dt;currentTime=Math.min(duration,currentTime+Math.min((stamp-lastStamp)/1000,.1)*duration/12);if(currentTime>=duration)setPlaying(false);}lastStamp=stamp;draw();}requestAnimationFrame(frame);}

const kdeCanvas=document.getElementById('kde-scene'),kdeCtx=kdeCanvas.getContext('2d');
const kdeControls=['kde-width','kde-grid','kde-window','kde-floor'].map(id=>document.getElementById(id));
const kdeCache=new Map();let kdeSettings={width:.06,grid:24,window:0,floor:.05};
function kdeAverage(samples,N,L,width,G,floor){
 const h=width*L,ux=new Float64Array(G*G),uy=new Float64Array(G*G),weights=new Float64Array(G*G);
 const imageCount=Math.ceil(8*h/L),axisX=new Float64Array(G*N),axisY=new Float64Array(G*N);
 for(const sample of samples){
  for(let q=0;q<G;q++)for(let i=0;i<N;i++){
   let dx=q*L/G-sample.x[2*i],dy=q*L/G-sample.x[2*i+1];
   dx-=L*Math.round(dx/L);dy-=L*Math.round(dy/L);let wx=0,wy=0;
   for(let m=-imageCount;m<=imageCount;m++){wx+=Math.exp(-.5*((dx+m*L)/h)**2);wy+=Math.exp(-.5*((dy+m*L)/h)**2);}
   axisX[q*N+i]=wx;axisY[q*N+i]=wy;
  }
  for(let y=0;y<G;y++)for(let x=0;x<G;x++){
   const k=y*G+x;for(let i=0;i<N;i++){const w=axisX[x*N+i]*axisY[y*N+i];weights[k]+=w;ux[k]+=w*sample.v[2*i];uy[k]+=w*sample.v[2*i+1];}
  }
 }
 const rho=new Float64Array(G*G);let maxSpeed=0;
 for(let k=0;k<weights.length;k++){
  rho[k]=weights[k]/(samples.length*2*Math.PI*h*h);
  if(weights[k]>1e-300&&rho[k]>=floor*N/(L*L)){ux[k]/=weights[k];uy[k]/=weights[k];maxSpeed=Math.max(maxSpeed,Math.hypot(ux[k],uy[k]));}
  else{ux[k]=NaN;uy[k]=NaN;}
 }
 return {ux,uy,rho,maxSpeed:Math.max(1e-12,maxSpeed)};
}
function kdeField(index){
 if(kdeCache.has(index))return kdeCache.get(index);
 const target=data.sampleSteps[index]*active.dt-kdeSettings.window;let first=index;
 while(first>0&&data.sampleSteps[first-1]*active.dt>=target)first--;
 const count=Math.min(7,index-first+1),samples=[];
 for(let j=0;j<count;j++){
  const s=count===1?index:Math.floor(first+j*(index-first)/(count-1)),offset=s*active.N*2;
  samples.push({x:data.xs.subarray(offset,offset+active.N*2),v:data.vs.subarray(offset,offset+active.N*2)});
 }
 const field=kdeAverage(samples,active.N,active.L,kdeSettings.width,kdeSettings.grid,kdeSettings.floor);
 field.samples=count;kdeCache.set(index,field);if(kdeCache.size>32)kdeCache.delete(kdeCache.keys().next().value);return field;
}
function fieldColor(value){
 const stops=[[12,14,35],[83,22,107],[184,49,96],[246,119,70],[253,242,168]];
 const p=Math.max(0,Math.min(1,value))*4,i=Math.min(3,Math.floor(p)),f=p-i;
 return `rgb(${stops[i].map((v,j)=>Math.round(v*(1-f)+stops[i+1][j]*f)).join(',')})`;
}
function drawKDE(index){
 if(!document.getElementById('kde-visible').checked)return;
 const w=kdeCanvas.clientWidth,h=kdeCanvas.clientHeight,c=kdeCtx;
 c.fillStyle='#0c1629';c.fillRect(0,0,w,h);if(!data)return;
 const field=kdeField(index),G=kdeSettings.grid,size=Math.min(w-100,h-100),left=(w-size)/2,top=55,cell=size/G;
 c.save();c.beginPath();c.rect(left,top,size,size);c.clip();
 // Center each cell at the same grid point used by the Python KDE; wrap edge cells.
 for(let y=0;y<=G;y++)for(let x=0;x<=G;x++){
  const k=(y%G)*G+x%G,speed=Math.hypot(field.ux[k],field.uy[k]);
  c.fillStyle=Number.isFinite(speed)?fieldColor(speed/field.maxSpeed):'#0c1629';
  c.fillRect(left+(x-.5)*cell,top+size-(y+.5)*cell,cell+.5,cell+.5);
 }
 c.strokeStyle='#d7f8ff';c.lineWidth=1.2;
 for(let y=0;y<G;y+=2)for(let x=0;x<G;x+=2){
  const k=y*G+x;if(!Number.isFinite(field.ux[k]))continue;
  const px=left+x*cell,py=top+size-y*cell,dx=field.ux[k]/field.maxSpeed*cell*1.5,dy=-field.uy[k]/field.maxSpeed*cell*1.5;
  const tx=px+dx*.5,ty=py+dy*.5,angle=Math.atan2(dy,dx),head=Math.min(4,Math.hypot(dx,dy)*.4);
  c.beginPath();c.moveTo(px-dx*.5,py-dy*.5);c.lineTo(tx,ty);c.moveTo(tx-head*Math.cos(angle-.5),ty-head*Math.sin(angle-.5));c.lineTo(tx,ty);c.lineTo(tx-head*Math.cos(angle+.5),ty-head*Math.sin(angle+.5));c.stroke();
 }
 c.restore();c.strokeStyle='#38536d';c.strokeRect(left,top,size,size);
 c.fillStyle='#d3e5f8';c.font='12px monospace';c.fillText(`t ${ (data.sampleSteps[index]*active.dt).toFixed(3)}  h ${(kdeSettings.width*active.L).toFixed(3)}  window ${kdeSettings.window}  (${field.samples} samples)`,20,25);
 c.fillStyle='#879bb5';c.font='11px system-ui';c.fillText('x',left+size/2,top+size+27);c.fillText('y',left-20,top+size/2);
 c.fillText(`|mean velocity|: 0 – ${field.maxSpeed.toFixed(3)} · arrows/colors scaled per frame`,20,h-12);
}
function updateKDESettings(){
 const values=kdeControls.map(el=>Number(el.value));
 if(kdeControls.some(el=>el.value.trim()==='')||!values.every(Number.isFinite)||values[0]<.01||values[0]>.5||!Number.isInteger(values[1])||values[1]<12||values[1]>48||values[2]<0||values[3]<0||values[3]>1){
  document.getElementById('kde-error').textContent='Use h/L 0.01–0.5, integer grid 12–48, window ≥ 0 and density floor 0–1.';return;
 }
 kdeSettings={width:values[0],grid:values[1],window:values[2],floor:values[3]};kdeCache.clear();document.getElementById('kde-error').textContent='';draw();
}
kdeControls.forEach(el=>el.addEventListener('input',updateKDESettings));
document.getElementById('kde-visible').addEventListener('change',()=>{kdeCanvas.style.display=document.getElementById('kde-visible').checked?'block':'none';resize();});

recalculate();resize();requestAnimationFrame(frame);

</script></body></html>'''
