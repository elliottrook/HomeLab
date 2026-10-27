#!/usr/bin/env python3
"""HP entry point for the exact EPUB Doctor family successor."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from epub_doctor_family_install import run


def idle():
    try:
        import xbmc  # type: ignore
        response = json.loads(xbmc.executeJSONRPC(json.dumps({
            'jsonrpc': '2.0', 'id': 1, 'method': 'Player.GetActivePlayers'})))
        return response.get('result') == []
    except (ImportError, TypeError, ValueError, json.JSONDecodeError):
        return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('install', 'verify', 'rollback'))
    parser.add_argument('bundle')
    parser.add_argument('pin')
    parser.add_argument('--storage', default='/storage')
    args = parser.parse_args()
    print(json.dumps(run(args.mode, args.bundle, args.storage, args.pin,
                         idle=idle), sort_keys=True))
