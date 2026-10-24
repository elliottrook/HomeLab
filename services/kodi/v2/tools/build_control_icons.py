"""Deterministic transparent monochrome transport glyphs, no pill/backplate.

Original geometric SVG sources are retained beside the rendered PNGs. Kodi's
image controls tint these white glyphs for normal/focused/disabled states.
"""
import os
from pathlib import Path
import subprocess

DEST=Path(__file__).resolve().parents[1]/'script.astermusic.v2lab/resources/controls'
SHAPES={
    'play':'<path d="M24 15 L49 32 L24 49 Z" fill="white" stroke="none"/>',
    'pause':'<path d="M23 17 V47 M41 17 V47" stroke-width="6"/>',
    'stop':'<rect x="19" y="19" width="26" height="26" rx="2" fill="white" stroke="none"/>',
    'back':'<path d="M31 18 L17 32 L31 46 M47 18 L33 32 L47 46"/>',
    'forward':'<path d="M17 18 L31 32 L17 46 M33 18 L47 32 L33 46"/>',
    'page-back':'<path d="M23 18 L10 32 L23 46 M33 20 H53 M33 32 H53 M33 44 H47"/>',
    'page-next':'<path d="M41 18 L54 32 L41 46 M11 20 H31 M11 32 H31 M11 44 H25"/>',
    'current':'<path d="M13 18 H35 M13 32 H27 M13 46 H35"/><path d="M39 24 L51 32 L39 40 Z" fill="white" stroke="none"/>',
    'add':'<path d="M12 18 H37 M12 32 H30 M12 46 H30 M45 31 V51 M35 41 H55"/>',
    'replace':'<path d="M12 23 H50 L42 15 M50 41 H14 L22 49"/>',
    'play-next':'<path d="M15 18 L35 32 L15 46 Z" fill="white" stroke="none"/><path d="M44 18 V46"/>',
    'shuffle':'<path d="M12 19 H18 C29 19 35 45 46 45 H53 M46 38 L53 45 L46 52 M12 45 H18 C23 45 26 38 29 33 M35 25 C39 19 42 19 53 19 M46 12 L53 19 L46 26"/>',
}

def main():
    DEST.mkdir(parents=True,exist_ok=True)
    node=os.environ.get('ASTER_NODE','/Users/jelliott/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node')
    sharp=os.environ.get('ASTER_SHARP','/Users/jelliott/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp')
    for name,shape in SHAPES.items():
        svg=('<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 64 64">'
             '<g fill="none" stroke="white" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round">'+shape+'</g></svg>')
        (DEST/(name+'.svg')).write_text(svg+'\n')
        subprocess.run([node,'-e',"require(process.argv[1])(Buffer.from(process.argv[2])).png().toFile(process.argv[3])",sharp,svg,str(DEST/(name+'.png'))],check=True)

if __name__=='__main__':main()
