"""Explicit fictional-fixture rehearsal; never calls provisioning endpoints.

Run only after approved staging into a fresh root-owned directory. The identity
option performs existing ORM preflight reads, without printing model objects.
"""
import io
import json
from pathlib import Path
import sys
import unittest


def run(*,identity=False):
    root=Path(__file__).resolve().parent
    for path in root.glob('*.py'):
        compile(path.read_bytes(),str(path),'exec')
    # All vault operations in these tests are patched; only temporary fictional
    # tokens/pipes are used. Never invoke node.vault outside those mocks.
    suite=unittest.defaultTestLoader.loadTestsFromName('test_provision_node')
    result=unittest.TextTestRunner(stream=io.StringIO()).run(suite)
    if result.testsRun!=8 or not result.wasSuccessful():
        raise RuntimeError('Fictional fixture rehearsal failed; no private output retained')
    count=None
    if identity:
        import identity_provision
        _,count=identity_provision.preflight()
    return {'passed':True,'fixture_tests':result.testsRun,'existing_apps_checked':count,
            'real_credentials_used':False,'accounts_created':False,
            'delegation_enabled':False,'model_calls':0,
            'python':list(sys.version_info[:3])}


if __name__=='__main__':
    try:
        if len(sys.argv)!=1: raise ValueError('Unsupported arguments')
        print(json.dumps(run()))
    except Exception:
        raise SystemExit('Rehearsal failed; no private output emitted') from None
