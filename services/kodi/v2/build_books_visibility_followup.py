"""Build the immutable HP Books visibility parser correction."""

import argparse
import json
from pathlib import Path
import shutil

import books_visibility_followup as subject


TARGET = ".kodi/addons/skin.asterhome/1080i/IncludesBooks.xml"


def build(source, output):
    source, output = Path(source), Path(output)
    if output.exists():
        raise ValueError("books-visibility-output")
    candidate = subject.render((source / 'IncludesBooks.xml').read_bytes())
    target = output / 'payload' / TARGET
    target.parent.mkdir(parents=True); target.write_bytes(candidate)
    helper = Path(__file__).parent / 'tools/deploy_books_visibility_followup.py'
    shutil.copyfile(helper, output / helper.name)
    manifest = {'schema': 1, 'kind': 'hp-books-visibility.v3',
                'production_changed': False,
                'files': [{'path': TARGET, 'before_sha256': subject.PREDECESSOR,
                           'sha256': subject.sha(candidate), 'bytes': len(candidate)}],
                'helper_sha256': subject.sha(helper.read_bytes())}
    rendered = json.dumps(manifest, indent=2, sort_keys=True).encode() + b'\n'
    (output / 'manifest.json').write_bytes(rendered)
    return subject.sha(rendered)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('source'); parser.add_argument('output')
    args = parser.parse_args(); print(build(args.source, args.output))
