"""Private immutable HP feed-trial payload; never an active add-on installer."""
import argparse
import hashlib
import json
from pathlib import Path

MEMBERS={'live_home_feed_trial.py','home_publication.py','home_delivery.py',
         'home_dashboard_model.py','home_freshness.py'}


def build(output):
    root=Path(output);here=Path(__file__).resolve().parent
    root.mkdir(mode=0o700)
    rows=[]
    for name in sorted(MEMBERS):
        source=here/('tools/'+name if name.startswith('live_') else name)
        raw=source.read_bytes();path=root/name;path.write_bytes(raw);path.chmod(0o600)
        rows.append(dict(path=name,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw)))
    manifest=dict(kind='hp-home-feed-trial.v1',one_shot=True,restore_original=True,
                  production=False,automatic_refresh=False,files=rows)
    path=root/'manifest.json';path.write_text(json.dumps(manifest,indent=2)+'\n');path.chmod(0o600)
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True)
    print(build(parser.parse_args().output))
