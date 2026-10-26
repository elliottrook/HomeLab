"""Build the bounded Aster palette successor without touching camera code."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from home_aster_palette import assets, build, FOLDER

source, destination = map(Path, sys.argv[1:])
destination.mkdir(mode=0o700, parents=True, exist_ok=False)
raw = source.read_bytes()
(destination / 'custom_1112_home.xml').write_bytes(build(raw))
media = destination / FOLDER
media.mkdir()
vectors = destination / 'svg'
vectors.mkdir()
node = os.environ.get('ASTER_NODE', '/Users/jelliott/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node')
sharp = os.environ.get('ASTER_SHARP', '/Users/jelliott/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp')
for name, svg in assets().items():
    (vectors / (name + '.svg')).write_text(svg)
    subprocess.run([node, '-e', 'require(process.argv[1])(Buffer.from(process.argv[2])).png().toFile(process.argv[3])', sharp, svg, str(media / (name + '.png'))], check=True)
files = {str(p.relative_to(destination)): hashlib.sha256(p.read_bytes()).hexdigest() for p in destination.rglob('*') if p.is_file() and 'svg' not in p.relative_to(destination).parts}
(destination / 'manifest.json').write_text(json.dumps(dict(kind='home-palette-1', predecessor=hashlib.sha256(raw).hexdigest(), files=files), sort_keys=True, indent=2) + '\n')
print(json.dumps(dict(files=len(files), manifest=hashlib.sha256((destination / 'manifest.json').read_bytes()).hexdigest())))
