#!/usr/bin/env python3
"""Summarize immutable matched backend results without inventing missing runs."""
import hashlib
import json
import statistics
import argparse
import os
import re
from pathlib import Path

root = Path('/var/lib/b60-inference/evidence')
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--fusion-disabled-retry', action='store_true')
parser.add_argument('--instrumented', action='store_true')
parser.add_argument('--exclusive', action='store_true')
parser.add_argument('--run-id')
parser.add_argument('--write-report', action='store_true')
parser.add_argument('--evidence-root', type=Path, default=root, help='Override only for offline fixtures')
args = parser.parse_args()
root = args.evidence_root
assert args.run_id is None or (args.exclusive and re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}',args.run_id))
prefix = ('matched-sycl-exclusive-' + (args.run_id or '20261010') if args.exclusive else
          'matched-sycl-instrumented-20261010' if args.instrumented else
          'matched-sycl-fusion-off-20261010' if args.fusion_disabled_retry else 'matched-sycl-20261010')
groups = {}
hashes = {}
for label in ['vulkan-pre', 'sycl', 'vulkan-post']:
    group = []
    for rep in range(1, 6):
        path = root / f'{prefix}-{label}-{rep}.json'
        if path.exists():
            raw = path.read_bytes()
            hashes[path.name] = hashlib.sha256(raw).hexdigest()
            group.append(json.loads(raw))
    groups[label] = group

report = {'schema_version': 1, 'completed_repetitions': {k: len(v) for k, v in groups.items()},
          'evidence_sha256': hashes, 'backends': {},
          'limitations': ['End-to-end request latency, not isolated decode or TTFT.',
                          'Official FP32 SYCL and Vulkan release builds use different backend kernels.',
                          'Four known fixture-scoring failures remain baseline limitations.',
                          'Synthetic post-policy analysis does not prove arbitrary household correctness.']}
for label, group in groups.items():
    if not group:
        continue
    medians = [d['median_latency_seconds'] for d in group]
    report['backends'][label] = {
        'suite_medians_seconds': medians, 'median_seconds': statistics.median(medians),
        'range_seconds': [min(medians), max(medians)], 'pass_counts': [d['pass_count'] for d in group],
        'failed_ids': [sorted(r['id'] for r in d['results'] if not r['passed']) for d in group]}
if all(len(group) == 5 for group in groups.values()):
    vk = groups['vulkan-pre'] + groups['vulkan-post']
    sycl = groups['sycl']
    assert len({d['suite_sha256'] for d in vk + sycl}) == 1
    rows = []
    for old in vk[0]['results']:
        controls = [next(r for r in d['results'] if r['id'] == old['id']) for d in vk]
        candidates = [next(r for r in d['results'] if r['id'] == old['id']) for d in sycl]
        a = statistics.median(r['elapsed_seconds'] for r in controls)
        b = statistics.median(r['elapsed_seconds'] for r in candidates)
        rows.append({'id': old['id'], 'vulkan_median_seconds': a, 'sycl_median_seconds': b,
                     'latency_reduction_percent': 100*(1-b/a),
                     'vulkan_completion_tokens': sorted({r['usage']['completion_tokens'] for r in controls}),
                     'sycl_completion_tokens': sorted({r['usage']['completion_tokens'] for r in candidates})})
    a = statistics.median(d['median_latency_seconds'] for d in vk)
    b = statistics.median(d['median_latency_seconds'] for d in sycl)
    report.update({'complete': True, 'latency_reduction_percent': 100*(1-b/a),
                   'request_speedup_factor': a/b, 'rows': rows})
    equal_length = [row for row in rows if len(row['vulkan_completion_tokens']) == 1
                    and row['vulkan_completion_tokens'] == row['sycl_completion_tokens']]
    report['identical_completion_length_case_count'] = len(equal_length)
    report['identical_completion_length_median_latency_reduction_percent'] = (
        statistics.median(row['latency_reduction_percent'] for row in equal_length)
        if equal_length else None)
else:
    report['complete'] = False
serialized = json.dumps(report, sort_keys=True) + '\n'
if args.write_report:
    assert report['complete'], 'refuse to publish an incomplete matched comparison'
    path = root / (prefix + '-report.json')
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as f:
        f.write(serialized); f.flush(); os.fsync(f.fileno())
print(serialized, end='')
