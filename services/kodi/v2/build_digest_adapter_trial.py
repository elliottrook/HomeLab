"""Build an immutable, HP-only native adapter trial, not a News replacement."""
import argparse
import hashlib
import json
from pathlib import Path


def build(output):
    here = Path(__file__).resolve().parent
    output = Path(output)
    if output.exists(): raise ValueError('immutable-trial-output')
    sources = {name:here / name for name in ('digest_timeline.py', 'digest_playback_state.py',
        'digest_player_adapter.py', 'digest_kodi_port.py')}
    sources.update({name:here / 'tools' / name for name in ('live_digest_adapter.py', 'deploy_startup.py')})
    output.mkdir()
    records = []
    for name, source in sorted(sources.items()):
        data = source.read_bytes()
        (output / name).write_bytes(data)
        records.append(dict(path=name, sha256=hashlib.sha256(data).hexdigest()))
    raw = (json.dumps(dict(kind='hp-digest-adapter-trial.v1', files=records), indent=2)+'\n').encode()
    (output / 'manifest.json').write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    print(build(parser.parse_args().output))
