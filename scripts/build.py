from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from design_lab.server import public_files

destination=ROOT/'dist'
if destination.is_symlink(): raise SystemExit('Refusing a linked build directory.')
if destination.exists(): shutil.rmtree(destination)
for name in public_files(ROOT/'web'):
    source=ROOT/'web'/name
    if source.is_symlink() or not source.is_file(): raise SystemExit(f'Public source missing or linked: {name}')
    target=destination/name; target.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(source,target)
print(f'Built {len(public_files(ROOT/"web"))} public files.')
