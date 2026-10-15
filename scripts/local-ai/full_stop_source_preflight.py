"""Source-bound pre-acquire gate for the disabled full-stop lease candidate.

The caller supplies fixed, trusted adapters. This module has no command,
network, credential or effect runner and never grants a lease by itself.
"""

from __future__ import annotations

import re

from lease_contract import (
    ACCEPTED_BACKEND, ACCEPTED_MODEL, LeaseReceipt,
    validate_pre_acquire_receipt,
)
from lease_watchdog import EXPECTED_SCHEDULES, Observation
from source_receipts import BackupSourceReceipt
from admission_gate import EXPECTED_BACKUP_SOURCE


class PreflightError(ValueError):
    pass


def prepare_pre_acquire(
    backup: BackupSourceReceipt,
    observation: Observation,
    *, lease_id: str,
    generation: int,
    expires_minute: int,
) -> LeaseReceipt:
    """Bind a retained archive proof and exact healthy production snapshot."""
    if (backup.source != EXPECTED_BACKUP_SOURCE or
            backup.chain_id != EXPECTED_BACKUP_SOURCE or
            backup.source_observed is not True or backup.integrity_verified is not True or
            not isinstance(backup.integrity_receipt, str) or
            not re.fullmatch(r"retained-archive-integrity-sha256:[0-9a-f]{64}", backup.integrity_receipt)):
        raise PreflightError("current-cycle retained backup evidence is incomplete")
    if backup.completed_minute > observation.now_minute:
        raise PreflightError("backup verification is from the future")
    if not all((
        observation.control_plane_healthy,
        observation.production_services_healthy,
        observation.accepted_gpu_visible,
        observation.schedule_restored,
        observation.schedules_enabled,
        observation.exact_binary_verified,
        observation.model_verified,
        observation.unit_verified,
        observation.auth_verified,
    )) or observation.schedule_points != EXPECTED_SCHEDULES:
        raise PreflightError("exact production and schedule preflight failed")
    receipt = LeaseReceipt(
        lease_id=lease_id, generation=generation,
        issued_minute=observation.now_minute, expires_minute=expires_minute,
        backup_receipt=backup.integrity_receipt,
        model_identity=ACCEPTED_MODEL, backend_identity=ACCEPTED_BACKEND,
        consumers_isolated=False, scheduled_work_quiesced=False,
    )
    validate_pre_acquire_receipt(
        receipt, now_minute=observation.now_minute,
        expected_backup_receipt=backup.integrity_receipt,
        watchdog_alive=observation.heartbeat_alive,
    )
    return receipt
