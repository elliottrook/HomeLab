"""Bind the independent observer to the accepted v2 canary checks."""
from __future__ import annotations

from contextlib import contextmanager

import sa4_canary_consumer_health_check_v1 as old_consumer
import sa4_canary_target_bytes_check_v1 as old_bytes
import sa4_canary_target_metadata_check_v1 as old_metadata
import sa4_canary_v2_consumer_health_check_v1 as consumer
import sa4_canary_v2_target_bytes_check_v1 as bytes_check
import sa4_canary_v2_target_metadata_check_v1 as metadata
import sa4_independent_receipt_producer_v1 as previous
import sa4_target_registry_v1 as registry_v1
import sa4_target_registry_v3 as registry_v3


LOCAL_HOST_ID = "unconfigured"


@contextmanager
def _bindings():
    originals = (previous.registry, previous.bytes_check,
                 previous.metadata_check, previous.consumer_check,
                 previous.LOCAL_HOST_ID)
    if (originals[0] not in {registry_v1, registry_v3}
            or originals[1:4] != (old_bytes, old_metadata, old_consumer)):
        raise ValueError("SA4 distinct observer predecessor changed")
    if LOCAL_HOST_ID not in {"unconfigured", "lxc104"}:
        raise ValueError("SA4 distinct observer host binding changed")
    previous.registry = registry_v3
    previous.bytes_check = bytes_check
    previous.metadata_check = metadata
    previous.consumer_check = consumer
    previous.LOCAL_HOST_ID = LOCAL_HOST_ID
    try:
        yield
    finally:
        (previous.registry, previous.bytes_check,
         previous.metadata_check, previous.consumer_check,
         previous.LOCAL_HOST_ID) = originals


def observe(*args, **kwargs) -> bytes:
    with _bindings():
        return previous.observe(*args, **kwargs)
