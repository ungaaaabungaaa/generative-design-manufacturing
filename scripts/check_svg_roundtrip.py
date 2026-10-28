"""Validate bounded SVG exports against the bundle's evaluated profiles."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import stat
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from design_lab.mechanics import Config, InputError
from design_lab.roundtrip import validate_svg


def read_bounded(path, limit):
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
        raise InputError('Expected a bounded regular file without symlinks')
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise InputError('Input exceeds its byte bound')
    return raw


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, default=ROOT / 'web/assets')
    parser.add_argument('--out', type=Path, required=True, help='New JSON file; never overwrite')
    args = parser.parse_args(argv)
    try:
        raw = read_bounded(args.bundle / 'report.json', 2_000_000)
        report = json.loads(raw.decode('utf-8'))
        config = Config.from_dict(report['config'])
        runs = report['runs']
        if not isinstance(runs, list) or not 1 <= len(runs) <= 8 or any(type(run['seed']) is not int or not 0 <= run['seed'] <= 2**32 - 1 for run in runs) or len({run['seed'] for run in runs}) != len(runs):
            raise InputError('Bundle must contain one to eight unique bounded integer seeds')
        designs = [('baseline', report['baseline'])] + [(f'seed-{run["seed"]}', run['best']) for run in runs]
        results = {}
        for name, design in designs:
            svg = read_bounded(args.bundle / 'designs' / (name + '.svg'), 65536)
            results[name] = validate_svg(config, design['heights_mm'], svg.decode('utf-8')) | {'svg_sha256': sha256(svg).hexdigest()}
        text = json.dumps({'schemaVersion': 1, 'source_report_sha256': sha256(raw).hexdigest(),
                           'interpretation': 'SVG profile/units/closure/area checks only; no CAD application, fabrication, or physical certification.',
                           'designs': results}, indent=2, allow_nan=False) + '\n'
        with args.out.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(text)
        print(f'Validated {len(results)} SVG profiles against evaluator geometry and volume.')
        return 0
    except (ValueError, KeyError, TypeError, RecursionError) as error:
        print(f'Input error: {error}', file=sys.stderr)
        return 2
    except OSError as error:
        print(f'File error: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
