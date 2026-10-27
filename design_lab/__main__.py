import argparse
import json
from pathlib import Path
import stat
import sys

from .mechanics import Config, InputError
from .search import benchmark
from .bundle import write_bundle


def load_config(path):
    if path is None:
        return Config()
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > 16384:
        raise InputError('config must be a regular UTF-8 JSON file no larger than 16 KiB')
    with path.open('rb') as source:
        raw = source.read(16385)
    if len(raw) > 16384:
        raise InputError('config exceeds 16 KiB')
    try:
        values = json.loads(raw.decode('utf-8'))
    except (ValueError, UnicodeError, RecursionError) as error:
        raise InputError('config must contain valid UTF-8 JSON') from error
    return Config.from_dict(values)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Generate constrained beam geometries using seeded evolutionary search.')
    commands = parser.add_subparsers(dest='command', required=True)
    generate = commands.add_parser('generate', help='Write a new reproducible report and SVG/DXF/OpenSCAD bundle')
    generate.add_argument('--out', type=Path, required=True)
    generate.add_argument('--config', type=Path)
    generate.add_argument('--seeds', nargs='+', type=int, default=[7, 21, 42])
    generate.add_argument('--generations', type=int, default=80)
    generate.add_argument('--population', type=int, default=32)
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        if args.out.exists() or args.out.is_symlink():
            raise FileExistsError('output directory exists; choose a new path')
        report = benchmark(config, seeds=args.seeds, generations=args.generations, population=args.population)
        count = write_bundle(report, args.out)
        print(f'Seeded evolutionary study: {len(report["runs"])} runs, {report["summary"]["total_evaluations"]} candidate evaluations.')
        print(f'Wrote {count} new files. Median model volume reduction: {report["summary"]["median_reduction_pct"]:.2f}%. Physical validation remains pending.')
        return 0
    except InputError as error:
        print(f'Input error: {error}', file=sys.stderr)
        return 2
    except OSError as error:
        print(f'File error: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
