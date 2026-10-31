#!/usr/bin/env python3
"""Build the credential-free Aster-owned add-on snapshot manifest."""
import argparse
import hashlib
import json
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('snapshot',type=Path)
parser.add_argument('output',type=Path)
parser.add_argument('--release',required=True)
args=parser.parse_args()
files=[]
for path in sorted(candidate for candidate in args.snapshot.rglob('*') if candidate.is_file()):
    data=path.read_bytes()
    files.append({'path':str(path.relative_to(args.snapshot)),'bytes':len(data),
                  'sha256':hashlib.sha256(data).hexdigest()})
manifest={'schema':1,'release':args.release,'target':'HP AsterTV lab, 192.168.1.140',
          'source_git_ref':'main','source_commit':'local-r14-reconciliation',
          'snapshot_source':'Installed Aster-owned Kodi addon and skin directories, captured from live lab after r14 Series visual acceptance repair',
          'credentials_included':False,'Kodi profile/addon_data included':False,'files':files}
args.output.write_text(json.dumps(manifest,indent=2,sort_keys=False)+'\n')
