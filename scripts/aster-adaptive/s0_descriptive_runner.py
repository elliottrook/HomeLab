"""Fixture-tested comparison candidate. Accepted-corpus launch remains disabled.

No CLI input loader, network, process launcher, output writer or production adapter.
A future reviewed OS-restricted launcher and exact run approval are prerequisites.
"""
import hashlib
import importlib.util
import itertools
import json
import math
import platform
import resource
import time
from pathlib import Path

from s0_descriptive import (PROFILES, aggregate, disagreement, input_text, latency,
                            score, training_rows)

SOURCE_HASH = '3e52c69f25dcf22100c521aeaa5b68b83e334ddf8ce9469d14d79822c8aa5864'
ENGINES = ('always-abstain', 'existing-keyword-rules', 'tfidf-nearest-fixed-0.2')
MAX_SECONDS = 60
MAX_RSS_MIB = 256
MAX_OUTPUT = 2 * 1024 * 1024


def load_engine_source(path):
    """Only the pinned, reviewed stdlib source; never its evaluate() entry point."""
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_HASH:
        raise ValueError('engine source changed')
    # Compile the already checked bytes, not a second path read (TOCTOU).
    spec = importlib.util.spec_from_loader('s0_pinned_routing', loader=None)
    module = importlib.util.module_from_spec(spec)
    module.__file__ = str(path)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def peak_rss_mib():
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if platform.system() == 'Darwin': return value / (1024 * 1024)
    if platform.system() == 'Linux': return value / 1024
    raise RuntimeError('unsupported RSS units')


def compare_fixtures(rows, engine_source, *, clock=time.perf_counter_ns,
                     rss=peak_rss_mib):
    """Test path exclusively. Guard excludes every current accepted pilot record.

    This guard is not security against callers changing code/inputs. It prevents
    accidental use of the accepted corpus under implementation-only permission.
    """
    if not rows or any(r.get('proposal_origin') != 'synthetic-evaluator-fixture' or
                       not r.get('family_id', '').startswith('fixture-') or
                       not r.get('request', '').startswith('[FIXTURE]') for r in rows):
        raise ValueError('accepted-corpus evaluation disabled')
    dev = sorted((r for r in rows if r['labels']['split'] == 'dev'), key=lambda r:r['family_id'])
    if not dev: raise ValueError('empty development')
    started = clock(); profiles = {}; stop = None
    def check():
        if (clock()-started)/1e9 > MAX_SECONDS: raise TimeoutError('wall-budget')
        usage = rss()
        if not math.isfinite(usage) or usage < 0 or usage > MAX_RSS_MIB: raise TimeoutError('rss-budget')
    for profile in PROFILES:
        results = {}; construction = None; engines = {}
        if stop is None:
            try:
                check(); before = clock()
                model = engine_source.Nearest(training_rows(rows, profile))
                construction = clock()-before; check()
                engines = {'always-abstain': lambda _:engine_source.proposal('abstain'),
                           'existing-keyword-rules': engine_source.rules,
                           'tfidf-nearest-fixed-0.2': lambda text:model.predict(text, .2)}
            except Exception:
                stop = 'construction-or-budget-failure'
        for name in ENGINES:
            outputs = []; first = []; warm = []; repeat_errors = 0
            for row in dev:
                prediction = None; error = 'not-processed' if stop else None
                elapsed = None
                if stop is None:
                    try:
                        check(); before = clock()
                        prediction = engines[name](input_text(row, profile))
                        elapsed = clock()-before; check()
                        encoded = json.dumps(prediction, allow_nan=False)
                        if len(encoded.encode()) > 16384: raise ValueError('oversized-prediction')
                    except TimeoutError:
                        stop = 'budget-exceeded'; prediction = None; error = stop
                    except Exception:
                        prediction = None; error = 'engine-error'
                checked = score(row['labels'], prediction)
                if error is None and not checked['valid']: error = 'malformed-output'
                outputs.append({'family_id': row['family_id'], 'reference': row['labels'],
                                'prediction': prediction, 'error': error, 'score': checked,
                                'first_pass_ns': elapsed})
                if elapsed is not None: first.append(elapsed)
            if stop is None:
                for _ in range(30):
                    for row in dev:
                        try:
                            check(); before = clock()
                            repeated = engines[name](input_text(row, profile))
                            elapsed = clock()-before; check()
                            if not score(row['labels'], repeated)['valid']: repeat_errors += 1
                            warm.append(elapsed)
                        except TimeoutError:
                            stop = 'budget-exceeded'; break
                        except Exception:
                            repeat_errors += 1
                    if stop: break
            results[name] = {'rows': outputs, 'metrics': aggregate([x['score'] for x in outputs]),
                             'first_pass_latency': latency(first), 'warm_latency': latency(warm),
                             'warm_errors': repeat_errors}
        pairs = {a+' vs '+b:disagreement(results[a]['rows'], results[b]['rows'])
                 for a,b in itertools.combinations(ENGINES,2)}
        profiles[profile] = {'construction_ns': construction, 'engines': results, 'disagreements': pairs}
    result = {'format': 's0-descriptive-fixture-result.v1', 'scope': 'synthetic-test-fixtures-only',
              'profiles': profiles, 'stop_reason': stop,
              'elapsed_ns': clock()-started, 'peak_rss_mib': rss(),
              'evaluation_authorized': False, 'promotion_authorized': False,
              'privacy_routing_quality': None, 'cloud_requirement_fraction': None,
              'production_local_resolution_fraction': None, 'confidence': None}
    if len(json.dumps(result, allow_nan=False).encode()) > MAX_OUTPUT:
        raise ValueError('output-budget; no output written')
    return result


def require_live_readiness(*_, **__):
    # No boolean, environment variable, receipt field or plan edit enables a run.
    raise PermissionError('accepted-corpus launch disabled: reviewed launcher and exact run approval required')


if __name__ == '__main__':
    raise SystemExit('No accepted-corpus execution entry point. Fixture tests only; no output written.')
