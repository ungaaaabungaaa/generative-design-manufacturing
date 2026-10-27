import { validateReport, volumeReduction, profilePoints } from './model.mjs';

const $=id=>document.getElementById(id);
const NS='http://www.w3.org/2000/svg';
const fmt=(value,digits=2)=>value.toLocaleString('en-US',{minimumFractionDigits:digits,maximumFractionDigits:digits});
function add(parent,name,attrs={},text){const el=document.createElementNS(NS,name);for(const[key,value]of Object.entries(attrs))el.setAttribute(key,String(value));if(text!==undefined)el.textContent=text;parent.append(el);return el;}

function drawBeam(report,design,showBaseline){
  const svg=$('beam-drawing');svg.replaceChildren();
  const w=svg.clientWidth,h=svg.clientHeight,c=report.config;
  svg.setAttribute('viewBox',`0 0 ${w} ${h}`);
  const left=28,cy=h*.49,s=(w-68)/(c.length_mm+.6*c.width_mm);
  const project=(x,y,z=0)=>[left+(x+.6*z)*s,cy-(y+.45*z)*s];
  const polygon=(points,attrs)=>add(svg,'polygon',{points:points.map(p=>project(...p).join(',')).join(' '),...attrs});
  const line=(x1,y1,x2,y2,attrs={})=>add(svg,'line',{x1,y1,x2,y2,stroke:'#839383','stroke-width':.8,...attrs});
  add(svg,'title',{},`Model beam: ${fmt(design.mass_g)} grams, ${fmt(design.tip_deflection_mm,3)} mm tip deflection. Physical validation pending.`);
  const rootHeight=design.heights_mm[0]*s;
  add(svg,'rect',{x:left-12,y:cy-rootHeight/2-12,width:13,height:rootHeight+24,fill:'#d2d9cc',stroke:'#7b8c7d','stroke-width':.7});
  for(let y=cy-rootHeight/2-8;y<cy+rootHeight/2+12;y+=6)line(left-12,y,left+1,y-6,{stroke:'#a7b3a4','stroke-width':.6});
  polygon(profilePoints(c,design.heights_mm).map(([x,y])=>[x,y,c.width_mm]),{fill:'#d5ded1',stroke:'#7e927f','stroke-width':.7});
  const dx=c.length_mm/c.sections;
  for(let i=0;i<c.sections;i++){
    const a=i*dx,b=(i+1)*dx,height=design.heights_mm[i],ratio=design.section_stress_mpa[i]/c.allowable_stress_mpa;
    polygon([[a,height/2,0],[b,height/2,0],[b,height/2,c.width_mm],[a,height/2,c.width_mm]],{fill:'#c5d2bf',stroke:'#8a9b87','stroke-width':.6});
    const face=polygon([[a,-height/2,0],[b,-height/2,0],[b,height/2,0],[a,height/2,0]],{fill:`hsl(${145-125*ratio} 25% 72%)`,stroke:'#6b806d','stroke-width':.65});
    add(face,'title',{},`Section ${i+1}: ${height} mm high; nominal stress ${fmt(design.section_stress_mpa[i])} MPa (${fmt(ratio*100,1)}% of limit).`);
  }
  if(showBaseline)polygon(profilePoints(c,report.baseline.heights_mm).map(([x,y])=>[x,y,0]),{fill:'none',stroke:'#6c796d','stroke-width':1,'stroke-dasharray':'4 3'});
  line(...project(0,0),...project(c.length_mm,0),{stroke:'#6b7d6b','stroke-dasharray':'3 4',opacity:.6});
  const tip=project(c.length_mm,0),top=cy-65;
  line(tip[0],top,tip[0],tip[1]-5,{stroke:'#c8532e','stroke-width':1.4});
  add(svg,'polygon',{points:`${tip[0]},${tip[1]} ${tip[0]-3},${tip[1]-7} ${tip[0]+3},${tip[1]-7}`,fill:'#c8532e'});
  add(svg,'text',{x:tip[0]-6,y:top-7,'text-anchor':'end',fill:'#a64729','font-size':11,'font-family':'monospace'},`${c.tip_load_n} N`);
  add(svg,'text',{x:left-12,y:cy+rootHeight/2+27,fill:'#5c6f5f','font-size':9,'font-family':'monospace'},'FIXED');
  const dimensionY=h-29;
  line(left,dimensionY,tip[0],dimensionY);line(left,dimensionY-4,left,dimensionY+4);line(tip[0],dimensionY-4,tip[0],dimensionY+4);
  add(svg,'text',{x:(left+tip[0])/2,y:dimensionY-7,'text-anchor':'middle',fill:'#546657','font-size':10,'font-family':'monospace'},`${c.length_mm} mm span`);
  add(svg,'text',{x:left,y:h-7,fill:'#637068','font-size':8,'font-family':'monospace'},showBaseline?'Dashed outline: uniform baseline':'Uniform baseline hidden');
}

function drawHistory(report,run,generation){
  const svg=$('history-chart');svg.replaceChildren();const w=svg.clientWidth,h=svg.clientHeight;
  svg.setAttribute('viewBox',`0 0 ${w} ${h}`);
  const m={left:43,right:15,top:23,bottom:38};
  const low=Math.min(...report.runs.map(item=>item.best.volume_mm3))/1000-.5,high=report.baseline.volume_mm3/1000+.5;
  const x=g=>m.left+g/report.algorithm.generations*(w-m.left-m.right),y=v=>h-m.bottom-(v-low)/(high-low)*(h-m.top-m.bottom);
  add(svg,'title',{},`Best feasible volume by generation. Selected seed ${run.seed}.`);
  add(svg,'text',{x:0,y:11,fill:'#637068','font-size':9,'font-family':'monospace'},'Volume (cm³)');
  for(let i=0;i<3;i++){
    const v=low+(high-low)*i/2;
    add(svg,'line',{x1:m.left,x2:w-m.right,y1:y(v),y2:y(v),stroke:'#d5dcd1','stroke-width':.7});
    add(svg,'text',{x:m.left-7,y:y(v)+3,'text-anchor':'end',fill:'#637068','font-size':9,'font-family':'monospace'},fmt(v,1));
  }
  for(let i=0;i<5;i++){
    const g=Math.round(report.algorithm.generations*i/4);
    add(svg,'text',{x:x(g),y:h-m.bottom+17,'text-anchor':'middle',fill:'#637068','font-size':9,'font-family':'monospace'},g);
  }
  for(const item of report.runs){
    const active=item.seed===run.seed;
    add(svg,'polyline',{points:item.history.map(d=>`${x(d.generation)},${y(d.volume_mm3/1000)}`).join(' '),fill:'none',stroke:active?'#c8532e':'#9aab98','stroke-width':active?1.8:.9,opacity:active?1:.6});
  }
  const selected=run.history[generation];
  add(svg,'line',{x1:x(generation),x2:x(generation),y1:m.top,y2:h-m.bottom,stroke:'#afbaa9','stroke-width':.7,'stroke-dasharray':'3 3'});
  add(svg,'circle',{cx:x(generation),cy:y(selected.volume_mm3/1000),r:3,fill:'#c8532e'});
  add(svg,'text',{x:(m.left+w-m.right)/2,y:h-4,'text-anchor':'middle',fill:'#637068','font-size':9,'font-family':'monospace'},'Generation');
}

async function start(){
  const response=await fetch('assets/report.json');if(!response.ok)throw new Error('The measured design report could not be loaded.');
  const text=await response.text();if(text.length>4000000)throw new Error('The report exceeds the supported size.');
  const report=validateReport(JSON.parse(text)),c=report.config;
  const setup=[['Span',`${c.length_mm} mm`],['Width',`${c.width_mm} mm`],['Sections',c.sections],['Tip load',`${c.tip_load_n} N`],['Modulus',`${fmt(c.youngs_modulus_mpa/1000,0)} GPa`],['Height range',`${c.min_height_mm}–${c.max_height_mm} mm`],['Height grid',`${c.height_grid_mm} mm`],['Max. step',`${c.max_neighbor_step_mm} mm`]];
  for(const[label,value]of setup){const dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=label;dd.textContent=value;$('setup').append(dt,dd);}
  for(const run of report.runs){const option=document.createElement('option');option.value=run.seed;option.textContent=`Seed ${String(run.seed).padStart(3,'0')}`;$('seed').append(option);}
  $('generation').max=report.algorithm.generations;$('generation').value=report.algorithm.generations;
  let currentRun,currentDesign,currentGeneration;
  function draw(){if(currentRun){drawBeam(report,currentDesign,$('baseline-toggle').checked);drawHistory(report,currentRun,currentGeneration);}}
  function render(){
    currentRun=report.runs.find(run=>run.seed===Number($('seed').value));currentGeneration=Number($('generation').value);currentDesign=currentRun.history[currentGeneration];
    $('generation-value').textContent=`${currentGeneration} / ${report.algorithm.generations}`;
    $('drawing-title').textContent=`Seed ${String(currentRun.seed).padStart(3,'0')} · generation ${currentGeneration}`;
    $('reduction').textContent=`${fmt(volumeReduction(report,currentDesign))}%`;
    $('mass').textContent=`${fmt(currentDesign.mass_g)} g`;$('baseline-mass').textContent=`uniform baseline: ${fmt(report.baseline.mass_g)} g`;
    $('deflection').textContent=`${fmt(currentDesign.tip_deflection_mm,3)} mm`;$('deflection-limit').textContent=`limit ${c.max_tip_deflection_mm} mm · margin ${fmt(c.max_tip_deflection_mm-currentDesign.tip_deflection_mm,4)} mm`;
    $('stress').textContent=`${fmt(currentDesign.max_stress_mpa)} MPa`;$('stress-limit').textContent=`limit ${c.allowable_stress_mpa} MPa · margin ${fmt(c.allowable_stress_mpa-currentDesign.max_stress_mpa)} MPa`;
    for(const extension of ['svg','dxf','scad']){$(`download-${extension}`).href=`assets/designs/seed-${currentRun.seed}.${extension}`;}
    $('run-summary').textContent=`${report.summary.seed_count} fixed seeds · ${report.summary.total_evaluations.toLocaleString('en-US')} candidate evaluations (profiles may repeat; baseline grid scans excluded) · final volume reduction ${fmt(report.summary.min_reduction_pct)}–${fmt(report.summary.max_reduction_pct)}% · no claim of a global optimum.`;
    draw();
  }
  $('explorer').hidden=false;render();
  $('seed').addEventListener('change',render);$('generation').addEventListener('input',render);$('baseline-toggle').addEventListener('change',draw);
  new ResizeObserver(draw).observe($('beam-drawing'));new ResizeObserver(draw).observe($('history-chart'));
}
start().catch(error=>{$('error').hidden=false;$('error').textContent=`${error.message} Start the local server with “python3 scripts/serve.py” and reload.`;});
