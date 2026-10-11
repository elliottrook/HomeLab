#!/usr/bin/env python3
"""Check authenticated synthetic generation without emitting credentials."""

import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def main():
    key = Path('/root/.news-aggregator-llama-key').read_text().strip()
    payload = {
        'messages': [{'role': 'user', 'content':
                      'Synthetic recovery test. What is 7 plus 5? Reply only with the number.'}],
        'max_tokens': 32,
        'temperature': 0,
        'stream': False,
    }
    request = urllib.request.Request(
        'http://192.168.70.12:11435/v1/chat/completions',
        data=json.dumps(payload).encode(),
        headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key},
    )
    start = time.monotonic()
    with urllib.request.urlopen(request, timeout=90) as response:
        data = json.load(response)
    content = data['choices'][0]['message'].get('content', '').strip()
    passed = content.strip('. \n') == '12'
    evidence = {
        'collected_at': datetime.now(timezone.utc).isoformat(),
        'synthetic_correctness_passed': passed,
        'authenticated_generation_passed': bool(content),
        'elapsed_seconds': time.monotonic() - start,
        'usage': data.get('usage', {}),
        'timings': data.get('timings', {}),
    }
    print(json.dumps(evidence, sort_keys=True))
    return 0 if passed else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print(json.dumps({'validation_failed': type(exc).__name__}))
        sys.exit(2)
