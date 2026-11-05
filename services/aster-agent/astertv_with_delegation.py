"""Attach delegation plus capability-scoped AsterTV and Remote routes."""

from pathlib import Path

from aster_agent import app, companion_claims, companion_owner
from aster_remote import from_environment as remote_from_environment
from astertv_gateway import from_environment
from delegation.deployment import attach


attach(app, companion_owner)
app.include_router(from_environment().router)
app.include_router(remote_from_environment(
    companion_claims, Path(__file__).resolve().parent / "static" / "remote"
).router)
