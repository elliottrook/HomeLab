"""Build an additive registry route from exact observed public source bytes.

Does not connect, install, reserve, claim or run. Preserve every unrelated
registration and handler; only this fixed ID uses the pre-claim bridge.
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE/'registry-predecessor'
DEST = Path('/private/tmp/b60-post-xe-registration-20261106')
WORKLOAD = 'b60-accepted-sycl-post-xe-qualification-v1'
BRIDGE = 'b60_post_xe_card_bridge.py'
PREDECESSORS = {'lab_hours_workloads.py': '0d263478c8b232591d59865d31cd96f6d0e09dcb3df9394605869971a106f3bb', 'lab_hours_reserved_runner.py': 'f0f740d82e5312239b9553bffe0d009dc4608d0c0ab9def84d526505b69c3644'}


def build():
    DEST.mkdir(mode=0o700, exist_ok=True)
    sha = hashlib.sha256((HERE/BRIDGE).read_bytes()).hexdigest()
    raw = (SOURCE/'lab_hours_workloads.py').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == PREDECESSORS['lab_hours_workloads.py']
    registry = raw.decode()
    entry = '\nWORKLOADS['+repr(WORKLOAD)+'] = WorkloadSpec(\n' + (
        "    workload_id=%r, owner='b60-stream-a', request_count=3,\n"
        "    per_request_timeout_seconds=30, deadline_seconds=900,\n"
        "    minimum_booking_seconds=2700, recovery_reserve_seconds=900,\n"
        "    runner_kind='b60-post-xe-card',\n"
        "    runtime_pins=(('b60_post_xe_card_bridge.py', %r),),\n"
        "    result_max_bytes=8192, retryable_session=False, maximum_attempts=1,\n)\n\n"
    ) % (WORKLOAD, sha)
    snapshot = 'REGISTERED_WORKLOADS = frozenset(WORKLOADS)'
    assert registry.count(snapshot) == 1
    registry = registry.replace(snapshot, entry+'\n'+snapshot)
    guard = '''
    b60 = workload('b60-accepted-sycl-post-xe-qualification-v1')
    if (b60.owner != 'b60-stream-a' or b60.runner_kind != 'b60-post-xe-card'
            or b60.request_count != 3 or b60.per_request_timeout_seconds != 30
            or b60.deadline_seconds != 900 or b60.minimum_booking_seconds != 2700
            or b60.recovery_reserve_seconds != 900 or b60.retryable_session
            or b60.maximum_attempts != 1 or b60.result_max_bytes != 8192
            or b60.runtime_pins != (('b60_post_xe_card_bridge.py', BRIDGE_SHA),)):
        raise ValueError('B60 fixed-card registration drift')
'''.replace('BRIDGE_SHA', repr(sha))
    assert registry.count('\ndef _local_imports(') == 1
    registry = registry.replace('\ndef _local_imports(', guard+'\ndef _local_imports(')
    raw = (SOURCE/'lab_hours_reserved_runner.py').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == PREDECESSORS['lab_hours_reserved_runner.py']
    reserved = raw.decode()
    reserved = reserved.replace('REGISTERED_RUNNER_KINDS = frozenset({',
        'REGISTERED_RUNNER_KINDS = frozenset({\n    "b60-post-xe-card",')
    branch = '''
    # A registered exclusive-card booking is dispatched by its exact future
    # clock. The qualified inner controller remains its ONLY ledger claimant.
    # Never import that controller here: shared module names must stay isolated.
    if os.geteuid() == 0:
        try:
            exclusive = ReservationStore(RESERVATIONS).get(booking_id)
        except Exception:
            exclusive = None
        if exclusive is not None and exclusive.get('workload') == 'b60-accepted-sycl-post-xe-qualification-v1':
            try:
                if retry:
                    raise RunError('EXCLUSIVE_CARD_NOT_RETRYABLE')
                load_manifest()
                from lab_hours_workloads import validate_registry, validate_inactive_target
                validate_registry()
                validate_inactive_target(PILOT, workload_id='b60-accepted-sycl-post-xe-qualification-v1')
                from b60_post_xe_card_bridge import dispatch
                return dispatch(exclusive, workload('b60-accepted-sycl-post-xe-qualification-v1'))
            except Exception:
                print(json.dumps({'state':'dispatch-refused','booking_id':booking_id,
                    'workload':'b60-accepted-sycl-post-xe-qualification-v1',
                    'qualification_claimed':False},sort_keys=True))
                return 1
'''
    signature = 'def run(booking_id: str, *, retry: bool = False) -> int:\n'
    assert reserved.count(signature) == 1
    reserved = reserved.replace(signature, signature+branch)
    outputs = {'lab_hours_workloads.py': registry.encode(),
               'lab_hours_reserved_runner.py': reserved.encode(), BRIDGE: (HERE/BRIDGE).read_bytes()}
    for name, raw in outputs.items():
        compile(raw, name, 'exec')
        (DEST/name).write_bytes(raw)
    manifest = json.loads((SOURCE/'release-snapshot.json').read_bytes())['manifest']
    old_pins = dict(manifest['pins'])
    manifest['pins'].update({n:hashlib.sha256(raw).hexdigest() for n,raw in outputs.items()})
    manifest['release'] = str(manifest['release'])+'-b60-fixed-card-capture-v1'
    assert all(manifest['pins'][n] == value for n,value in old_pins.items() if n not in outputs)
    (DEST/'lab_hours_release_manifest.json').write_text(json.dumps(manifest,sort_keys=True,separators=(',',':'))+'\n')
    return {n:hashlib.sha256(raw).hexdigest() for n,raw in outputs.items()}


if __name__ == '__main__':
    print(json.dumps(build(), sort_keys=True))
