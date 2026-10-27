"""Optional independent DXF parsing/audit. Requires ezdxf, not the runtime."""

import json
import math
from pathlib import Path

import ezdxf

ROOT=Path(__file__).resolve().parent.parent
report=json.loads((ROOT/'web/assets/report.json').read_text())
designs=[('baseline',report['baseline'])]+[(f'seed-{run["seed"]}',run['best'])for run in report['runs']]
for name,design in designs:
    document=ezdxf.readfile(ROOT/'web/assets/designs'/f'{name}.dxf')
    polylines=list(document.modelspace().query('LWPOLYLINE'))
    if document.units!=4 or len(polylines)!=1 or not polylines[0].closed:
        raise SystemExit(f'{name}: expected one closed millimetre profile')
    points=list(polylines[0].get_points('xy'))
    area=abs(sum(a[0]*b[1]-b[0]*a[1]for a,b in zip(points,points[1:]+points[:1])))/2
    if not math.isclose(area*report['config']['width_mm'],design['volume_mm3'],rel_tol=1e-10):
        raise SystemExit(f'{name}: parsed DXF volume differs from the evaluator')
    audit=document.audit()
    if audit.errors or audit.fixes:
        raise SystemExit(f'{name}: DXF audit reported errors or repairs')
    print(f'{name}: closed mm profile, matching volume, audit clean')
print(f'Independent format check: ezdxf {ezdxf.__version__}. OpenSCAD execution and physical validation are separate.')
