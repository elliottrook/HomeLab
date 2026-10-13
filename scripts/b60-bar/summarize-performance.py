#!/usr/bin/env python3
"""Sanitized historical/current comparison, without overstating causality."""
import hashlib
import json
import statistics
from pathlib import Path

root = Path('/var/lib/b60-inference/evidence')
before_path = root / 'aster-analysis-summary-v2-9b-production-20261010.json'
paths = [root / f'bar-full-20261010-{i}.json' for i in range(1, 6)]
before = json.loads(before_path.read_text())
after = [json.loads(p.read_text()) for p in paths]
assert all(d['suite_sha256'] == before['suite_sha256'] for d in after)
rows = []
for old in before['results']:
    current = [next(r for r in d['results'] if r['id'] == old['id']) for d in after]
    median = statistics.median(r['elapsed_seconds'] for r in current)
    rows.append({'id': old['id'], 'before_seconds': old['elapsed_seconds'],
                 'after_median_seconds': median,
                 'latency_reduction_percent': 100 * (1 - median / old['elapsed_seconds']),
                 'before_passed': old['passed'],
                 'after_pass_count': sum(r['passed'] for r in current),
                 'before_completion_tokens': old['usage']['completion_tokens'],
                 'after_completion_tokens': [r['usage']['completion_tokens'] for r in current]})
medians = [d['median_latency_seconds'] for d in after]
median = statistics.median(medians)
report = {'before_median_seconds': before['median_latency_seconds'],
          'after_suite_medians_seconds': medians, 'after_median_seconds': median,
          'after_suite_median_range_seconds': [min(medians), max(medians)],
          'latency_reduction_percent': 100 * (1 - median / before['median_latency_seconds']),
          'before_pass_count': before['pass_count'],
          'after_pass_counts': [d['pass_count'] for d in after],
          'case_count': before['case_count'], 'rows': rows,
          'evidence_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in [before_path] + paths},
          'limitations': ['Historical baseline has only one suite, not five repeats.',
                         'Kernel changed with BAR fix; BAR causality is not isolated.',
                         'Historical within-suite latency drift requires scrutiny.',
                         'These are end-to-end latencies, not isolated decode rates.']}
print(json.dumps(report, sort_keys=True))
