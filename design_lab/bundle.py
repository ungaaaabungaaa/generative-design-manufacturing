"""Deterministic study report and geometry exports from the same evaluator."""

import json
from pathlib import Path
import shutil

from .geometry import svg_export, dxf_export, scad_export
from .mechanics import Config


def artifact_texts(report):
    config = Config.from_dict(report['config'])
    artifacts = {'report.json': json.dumps(report, indent=2, allow_nan=False) + '\n'}
    designs = [('baseline', report['baseline'])] + [(f'seed-{run["seed"]}', run['best']) for run in report['runs']]
    for name, design in designs:
        for extension, exporter in [('svg', svg_export), ('dxf', dxf_export), ('scad', scad_export)]:
            artifacts[f'designs/{name}.{extension}'] = exporter(config, design['heights_mm'])
    return artifacts


def write_bundle(report, destination):
    destination = Path(destination)
    artifacts = artifact_texts(report)
    destination.mkdir()  # Existing files/directories are never overwritten.
    try:
        (destination / 'designs').mkdir()
        for name, text in artifacts.items():
            with (destination / name).open('x', encoding='utf-8', newline='\n') as target:
                target.write(text)
    except Exception:
        shutil.rmtree(destination)
        raise
    return len(artifacts)
