"""Known HP-only operator entry; public key only, never private key input."""
import json
import os
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from home_delivery_install import run
if __name__=='__main__':
    if os.uname().nodename!='AsterTV' or ROOT!=Path('/storage/.aster-staging/aster-home-delivery1') or len(sys.argv)!=4:
        raise SystemExit('delivery-install-hp-arguments')
    mode,pin,public=sys.argv[1:]
    print(json.dumps(run(mode,ROOT,pin,public)))
