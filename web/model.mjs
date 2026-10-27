export function validateReport(report) {
  const fail = () => { throw new Error('The design report is invalid or uses an unsupported schema.'); };
  const c = report?.config;
  if (report?.schemaVersion !== 1 || !c || !Object.values(c).every(v => typeof v === 'number' && Number.isFinite(v) && v > 0) || !Number.isInteger(c.sections) || c.sections < 4 || c.sections > 24) fail();
  if (!Array.isArray(report.runs) || report.runs.length < 1 || report.runs.length > 8 || !Number.isInteger(report.algorithm?.generations) || report.algorithm.generations < 1 || report.algorithm.generations > 300) fail();
  function check(design) {
    if (!design || design.feasible !== true || !Array.isArray(design.violations) || design.violations.length || !Array.isArray(design.heights_mm) || design.heights_mm.length !== c.sections) fail();
    const h = design.heights_mm;
    for (let i=0;i<h.length;i++) {
      if (!Number.isFinite(h[i]) || h[i] < c.min_height_mm || h[i] > c.max_height_mm || Math.abs(h[i]/c.height_grid_mm-Math.round(h[i]/c.height_grid_mm)) > 1e-8) fail();
      if (i && (h[i] > h[i-1]+1e-9 || h[i-1]-h[i] > c.max_neighbor_step_mm+1e-9)) fail();
    }
    for (const key of ['volume_mm3','mass_g','tip_deflection_mm','max_stress_mpa']) if (!Number.isFinite(design[key]) || design[key] <= 0) fail();
    if(!Array.isArray(design.section_stress_mpa)||design.section_stress_mpa.length!==c.sections||!design.section_stress_mpa.every(v=>Number.isFinite(v)&&v>=0)||Math.abs(Math.max(...design.section_stress_mpa)-design.max_stress_mpa)>1e-8) fail();
    const volume=c.width_mm*c.length_mm/c.sections*h.reduce((a,b)=>a+b,0);
    if (Math.abs(volume-design.volume_mm3)>1e-6 || Math.abs(volume*c.density_g_mm3-design.mass_g)>1e-7 || design.tip_deflection_mm>c.max_tip_deflection_mm*(1+1e-9) || design.max_stress_mpa>c.allowable_stress_mpa*(1+1e-9)) fail();
  }
  check(report.baseline);
  const seeds=new Set();
  for (const run of report.runs) {
    if (!Number.isInteger(run.seed) || run.seed<0 || run.seed>2**32-1 || seeds.has(run.seed) || !Array.isArray(run.history) || run.history.length!==report.algorithm.generations+1) fail();
    seeds.add(run.seed);check(run.best);
    let previous=report.baseline.volume_mm3;
    for(const [i,design] of run.history.entries()) {
      check(design);
      if(design.generation!==i || design.volume_mm3>previous+1e-7) fail();
      previous=design.volume_mm3;
    }
    if(JSON.stringify(run.best.heights_mm)!==JSON.stringify(run.history.at(-1).heights_mm) || run.best.volume_mm3!==run.history.at(-1).volume_mm3 || Math.abs(run.volume_reduction_pct-volumeReduction(report,run.best))>1e-8) fail();
  }
  if(report.summary?.seed_count!==report.runs.length || report.summary.total_evaluations!==report.runs.reduce((sum,run)=>sum+run.evaluations,0)) fail();
  return report;
}

export function volumeReduction(report, design) {
  return (report.baseline.volume_mm3-design.volume_mm3)/report.baseline.volume_mm3*100;
}

export function profilePoints(config, heights) {
  const dx=config.length_mm/config.sections;
  const points=[[0,-heights[0]/2]];
  for(let i=0;i<heights.length;i++) {
    points.push([(i+1)*dx,-heights[i]/2]);
    if(i+1<heights.length)points.push([(i+1)*dx,-heights[i+1]/2]);
  }
  points.push([config.length_mm,heights.at(-1)/2]);
  for(let i=heights.length-1;i>=0;i--) {
    points.push([i*dx,heights[i]/2]);if(i)points.push([i*dx,heights[i-1]/2]);
  }
  points.push(points[0]);
  return points.filter((p,i)=>!i||p[0]!==points[i-1][0]||p[1]!==points[i-1][1]);
}
