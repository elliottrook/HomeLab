"""Exact SSH forced-command contract for the schedule observer identity."""

SCHEDULE_WRAPPER = "/mnt/Media/.local-ai-lease/aster-schedule-observer-root"
MIRROR_WRAPPER = "/mnt/Media/.local-ai-lease/aster-mirror-observer-root"
MAC_WRAPPER = "/mnt/Media/.local-ai-lease/aster-mac-pull-observer-root"

ALLOWED = {
    "midclt call rsynctask.query": SCHEDULE_WRAPPER,
    "midclt call filesystem.listdir /mnt/Recovery/guests/aster-lxc110": MIRROR_WRAPPER,
    "aster-mac-pull-summary": MAC_WRAPPER,
}


def dispatch(original_command: str) -> str:
    """Return the only root wrapper allowed for an exact SSH command."""
    try:
        return ALLOWED[original_command]
    except KeyError as exc:
        raise ValueError("observer command is not allowlisted") from exc
