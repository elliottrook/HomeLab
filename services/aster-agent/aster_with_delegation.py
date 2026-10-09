"""Load the installed Aster application intact, then apply explicit attachment."""
from aster_agent import app, companion_owner
from delegation.deployment import attach

attach(app,companion_owner)
