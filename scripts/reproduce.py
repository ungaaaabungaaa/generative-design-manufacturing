"""Reproduce every bundled measurement and final geometry, without network."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from design_lab.bundle import artifact_texts
from design_lab.mechanics import Config
from design_lab.search import benchmark

artifacts = artifact_texts(benchmark(Config()))
for name, text in artifacts.items():
    if (ROOT / 'web/assets' / name).read_text(encoding='utf-8') != text:
        raise SystemExit(f'Reproduction failed: {name}')
print(f'Reproduced {len(artifacts)} bundled report/export files byte-for-byte.')
