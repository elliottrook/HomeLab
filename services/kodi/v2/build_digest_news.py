"""Build a pinned two-file handler/shim overlay; never alter the v1 source."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
from digest_news_install import HUB, SHIM, BEFORE, PLAYER_PIN


def patch_handler(data):
    source = data.decode()
    needle = '    if page not in WINDOWS:\n'
    if hashlib.sha256(data).hexdigest() != BEFORE or source.count(needle) != 1:
        raise ValueError('exact-news-handler-required')
    addition = """    if page == 'digest' and action in ('play', 'chapter'):
        from aster_v2_digest import main as open_digest_player
        open_digest_player(action)
        return
"""
    result = source.replace(needle, addition+needle).encode()
    ast.parse(result)
    return result


def build(output):
    here = Path(__file__).resolve().parent
    output = Path(output)
    if output.exists(): raise ValueError('immutable-news-output')
    files = {HUB:patch_handler((here.parent/'skin.asterhome/tools/hub_data.py').read_bytes()),
        SHIM:(here/'tools/aster_v2_digest.py').read_bytes()}
    rows = []
    for name, data in sorted(files.items()):
        path = output/'payload'/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        rows.append(dict(path=name, sha256=hashlib.sha256(data).hexdigest(), before_sha256=BEFORE if name == HUB else None))
    helpers = {}
    for name in ('digest_news_install.py', 'deploy_digest_news.py'):
        data = (here/name if name == 'digest_news_install.py' else here/'tools'/name).read_bytes()
        (output/name).write_bytes(data)
        helpers[name] = hashlib.sha256(data).hexdigest()
    raw = (json.dumps(dict(kind='hp-digest-news.v1', player_manifest_sha256=PLAYER_PIN,
        files=rows, helpers=helpers), indent=2)+'\n').encode()
    (output/'manifest.json').write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    print(build(parser.parse_args().output))
