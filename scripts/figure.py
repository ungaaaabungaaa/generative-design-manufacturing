"""Optional Matplotlib figure from the real bundled benchmark."""

import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent.parent
report=json.loads((ROOT/'web/assets/report.json').read_text())
fig,(left,right)=plt.subplots(1,2,figsize=(11,4.6),layout='constrained')
fig.set_facecolor('#f7f7f2')
for ax in (left,right):
    ax.set_facecolor('#f7f7f2');ax.spines[['top','right']].set_visible(False);ax.set_axisbelow(True)
names=['Uniform']+[f'Seed {run["seed"]}'for run in report['runs']]
mass=[report['baseline']['mass_g']]+[run['best']['mass_g']for run in report['runs']]
bars=left.bar(names,mass,color=['#99aa96']+['#c8532e']*len(report['runs']),width=.58)
left.bar_label(bars,labels=[f'{value:.2f}'for value in mass],padding=4,fontsize=9)
left.set_ylim(0,max(mass)*1.16);left.set_ylabel('Model mass (g)');left.set_title('Same load, geometry bounds, and model limits',loc='left',fontsize=11)
left.grid(axis='y',alpha=.2)
colors=['#c8532e','#5b806e','#90857c']
for run,color in zip(report['runs'],colors):
    right.plot([item['generation']for item in run['history']],[item['volume_mm3']/1000 for item in run['history']],label=f'Seed {run["seed"]}',color=color,lw=1.5)
right.set_xlabel('Generation');right.set_ylabel('Best feasible volume (cm³)');right.set_title('Recorded search progress',loc='left',fontsize=11)
right.grid(alpha=.2);right.legend(frameon=False,fontsize=9)
fig.suptitle('Constrained cantilever design: a reproducible evolutionary study',fontsize=14,x=.02,ha='left')
fig.text(.02,-.055,'Three fixed seeds, 80 generations, population 32. Results are one bounded beam-model study; no global-optimum claim.\nLocal step stresses, shear, fatigue, buckling, fixtures, and manufacturing validation are excluded.',fontsize=9)
(ROOT/'figures').mkdir(exist_ok=True)
fig.savefig(ROOT/'figures/benchmark.png',dpi=160,bbox_inches='tight')
fig.savefig(ROOT/'figures/benchmark.svg',bbox_inches='tight',metadata={'Date':None})
svg=ROOT/'figures/benchmark.svg';svg.write_text('\n'.join(line.rstrip()for line in svg.read_text().splitlines())+'\n')
plt.close(fig);print('Generated benchmark figures from the actual report.')
