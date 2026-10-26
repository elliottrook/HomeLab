"""Deterministic SVG→PNG Home trial, preserving vector design sources."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from home_layered_visual import build,brush_svg,panel_svg,background_svg,PALETTES

def main():
    source,destination=map(Path,sys.argv[1:]);destination.mkdir(mode=0o700,parents=True,exist_ok=False)
    raw=source.read_bytes();(destination/'custom_1112_home.xml').write_bytes(build(raw))
    media=destination/'aster-home-layered-v1';media.mkdir();vectors=destination/'svg';vectors.mkdir()
    assets={'background':background_svg(),'camera-panel':panel_svg(560,510,('#2c3e4c','#182a39','#8ab5ca'),30),
        'timer-panel':panel_svg(550,510,('#263b36','#142621','#b3c69d'),30),
        'row':panel_svg(480,98,('#30414d','#1d2d3c','#87a9bf'),26),
        'row-focus':panel_svg(480,98,('#28725c','#10513f','#cae6c9'),26)}
    assets.update({f'metric-{i}':panel_svg(395,116,colours) for i,colours in enumerate(PALETTES)})
    assets.update({f'arc-{i}':brush_svg(i) for i in range(61)})
    node=os.environ.get('ASTER_NODE','/Users/jelliott/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node')
    sharp=os.environ.get('ASTER_SHARP','/Users/jelliott/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp')
    for name,svg in assets.items():
        (vectors/(name+'.svg')).write_text(svg)
        subprocess.run([node,'-e',"require(process.argv[1])(Buffer.from(process.argv[2])).png().toFile(process.argv[3])",sharp,svg,str(media/(name+'.png'))],check=True)
    members={str(p.relative_to(destination)):hashlib.sha256(p.read_bytes()).hexdigest() for p in destination.rglob('*') if p.is_file() and 'svg' not in p.relative_to(destination).parts}
    (destination/'manifest.json').write_text(json.dumps(dict(kind='home-layered-1',predecessor=hashlib.sha256(raw).hexdigest(),files=members),sort_keys=True,indent=2)+'\n')
    print(json.dumps(dict(files=len(members),manifest=hashlib.sha256((destination/'manifest.json').read_bytes()).hexdigest())))

if __name__=='__main__':main()
