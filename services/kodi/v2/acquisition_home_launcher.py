"""Exact Home transformation from the Seerr button to the Acquisition Hub."""


class LauncherError(ValueError):
    pass


OLD = "RunScript(script.asterseerr)"
NEW = "RunScript(script.asteracquisition)"


def add_hub(raw):
    if not isinstance(raw, str) or raw.count(OLD) != 1 or NEW in raw:
        raise LauncherError("acquisition-home-predecessor")
    result = raw.replace(OLD, NEW, 1)
    if result.count(NEW) != 1 or OLD in result:
        raise LauncherError("acquisition-home-transform")
    return result
