"""Original companion glyphs for the accepted floating Music control family."""
import os
from pathlib import Path
import subprocess

DEST=Path(__file__).resolve().parents[1]/'player-control-assets'
SHAPES={
 'previous':'<path d="M20 18 V46"/><path d="M47 18 L27 32 L47 46 Z" fill="white" stroke="none"/>',
 'audio':'<path d="M12 26 H22 L33 17 V47 L22 38 H12 Z"/><path d="M42 23 Q51 32 42 41 M49 16 Q64 32 49 48"/>',
 'subtitles':'<rect x="10" y="16" width="44" height="32" rx="4"/><path d="M17 29 H27 M34 29 H47 M17 38 H35 M42 38 H47"/>',
 'quality':'<path d="M12 23 V13 H22 M42 13 H52 V23 M52 41 V51 H42 M22 51 H12 V41"/><path d="M26 39 V25 H35 Q43 25 43 32 Q43 39 35 39 Z"/>',
 'info':'<circle cx="32" cy="32" r="21"/><path d="M32 30 V44"/><circle cx="32" cy="21" r="2" fill="white" stroke="none"/>',
 'return':'<path d="M29 16 L13 32 L29 48 M15 32 H51"/>',
 'full-digest':'<path d="M11 17 H40 M11 29 H30 M11 41 H27"/><path d="M39 31 L54 41 L39 51 Z" fill="white" stroke="none"/>',
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
