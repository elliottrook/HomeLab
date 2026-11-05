"""Attach existing delegation and the capability-scoped AsterTV route."""

from aster_agent import app, companion_owner
from astertv_gateway import from_environment
from delegation.deployment import attach


attach(app, companion_owner)
app.include_router(from_environment().router)
