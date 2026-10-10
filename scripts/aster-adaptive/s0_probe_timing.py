"""Conservative inspection deadline measured before remote worker launch.

Worker sleeps ten seconds after readiness. Inspection ends by launch + eight
seconds, leaving at least two seconds before normal worker completion even if
readiness arrives late. No transport latency is subtracted from this margin.
"""
import time
from s0_lxc100_observe import parse_running, parse_canary

INSPECTION_SECONDS=8.0


def inspect_worker(call,started,*,clock=time.monotonic):
    end=started+INSPECTION_SECONDS
    def observe(operation):
        remaining=end-clock()
        if not 0<remaining<=INSPECTION_SECONDS:raise TimeoutError('inspection deadline')
        value=call(operation,deadline=remaining)
        if clock()>=end:raise TimeoutError('inspection completed too late')
        return value
    properties=observe('unit-properties')
    limits=observe('cgroup')
    canary=observe('canary-stat')
    return parse_running(properties,limits),parse_canary(canary)
