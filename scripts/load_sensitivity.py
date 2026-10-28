"""Assess the bundled fixed designs at explicit loads with the actual beam evaluator."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from design_lab.mechanics import Config, InputError, evaluate_loads


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--loads', nargs='+', type=float, required=True, help='Tip loads in N, 1 to 5000')
    parser.add_argument('--out', type=Path, required=True, help='New JSON file; never overwrite')
    args = parser.parse_args(argv)
    created = False
    try:
        raw = (ROOT / 'web/assets/report.json').read_bytes()
        report = json.loads(raw)
        config = Config.from_dict(report['config'])
        designs = [('baseline', report['baseline'])] + [(f'seed-{run["seed"]}', run['best']) for run in report['runs']]
        assessment = {
            'schemaVersion': 1, 'source_report_sha256': sha256(raw).hexdigest(),
            'config': report['config'], 'loads_n': args.loads,
            'model': report['model'],
            'interpretation': 'Fixed geometry; model-only load sensitivity, not physical certification or optimization',
            'designs': {name: evaluate_loads(config, design['heights_mm'], args.loads) for name, design in designs},
        }
        text = json.dumps(assessment, indent=2, allow_nan=False) + '\n'
        with args.out.open('x', encoding='utf-8', newline='\n') as stream:
            created = True
            stream.write(text)
        print(f'Assessed {len(designs)} fixed designs at {len(args.loads)} explicit tip loads.')
        return 0
    except InputError as error:
        print(f'Input error: {error}', file=sys.stderr)
        return 2
    except OSError as error:
        if created:
            args.out.unlink(missing_ok=True)
        print(f'File error: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
