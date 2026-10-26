"""Build a presentation-only Home successor and rasterize retained SVG design."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from home_design import build, arc_svg

PREDECESSOR='242b0592bd72482195b21af839c15c0f4e677a9598d695d7ae8408bc7cc60a1e'

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('source',type=Path); parser.add_argument('destination',type=Path)
    args=parser.parse_args()
    data=args.source.read_bytes()
    if hashlib.sha256(data).hexdigest()!=PREDECESSOR: raise ValueError('home-source-drift')
    args.destination.mkdir(mode=0o700,parents=True,exist_ok=False)
    (args.destination/'custom_1112_home.xml').write_bytes(build(data))
    media=args.destination/'aster-home-timer-v2'; media.mkdir()
    node=os.environ.get('ASTER_NODE','/Users/jelliott/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node')
    sharp=os.environ.get('ASTER_SHARP','/Users/jelliott/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp')
    for second in range(61):
        svg=arc_svg(second)
        subprocess.run([node,'-e',"require(process.argv[1])(Buffer.from(process.argv[2])).png().toFile(process.argv[3])",sharp,svg,str(media/f'arc-{second}.png')],check=True)
    shutil.copyfile(Path(__file__).resolve().parents[1]/'script.astermusic.v2lab/resources/controls/stop.png',media/'stop.png')
    members={str(p.relative_to(args.destination)):hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(args.destination.rglob('*')) if p.is_file()}
    manifest={'predecessor':PREDECESSOR,'files':members,'kind':'home-design-1'}
    (args.destination/'manifest.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'files':len(members),'manifest':hashlib.sha256((args.destination/'manifest.json').read_bytes()).hexdigest()}))

if __name__=='__main__': main()
