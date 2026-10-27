import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { validateReport, volumeReduction, profilePoints } from '../web/model.mjs';

const report = JSON.parse(await readFile(new URL('../web/assets/report.json', import.meta.url)));
test('real report and all best-feasible histories satisfy the viewer contract', () => {
  assert.equal(validateReport(report), report);
  assert.equal(report.summary.total_evaluations, 7776);
});
test('volume reduction uses the uniform baseline and generation zero has no reduction', () => {
  assert.equal(volumeReduction(report, report.runs[0].history[0]), 0);
  assert.ok(Math.abs(volumeReduction(report, report.runs[0].best) - 20.34313725490196) < 1e-10);
});
test('display profile has the evaluated symmetric area and dimensions', () => {
  const design = report.runs[0].best, points = profilePoints(report.config, design.heights_mm);
  assert.deepEqual(points[0], points.at(-1));
  const area = Math.abs(points.slice(0,-1).reduce((sum,p,i)=>sum+p[0]*points[i+1][1]-points[i+1][0]*p[1],0))/2;
  assert.equal(area * report.config.width_mm, design.volume_mm3);
  assert.equal(Math.max(...points.map(p=>p[1])), -Math.min(...points.map(p=>p[1])));
});
test('invalid schemas, unsafe seeds, infeasible values and nonmonotone histories fail', () => {
  for (const mutate of [r=>r.schemaVersion=2, r=>r.runs[0].seed='../bad', r=>r.baseline.volume_mm3=0,
    r=>r.runs[0].best.tip_deflection_mm=100, r=>r.runs[0].history[0].mass_g=-1,
    r=>r.runs[0].history[0].heights_mm[0]=Number.NaN]) {
    const broken=structuredClone(report);mutate(broken);assert.throws(()=>validateReport(broken), /report/i);
  }
});
