"""Pure Guest-route policy for the Jen M2 synthetic-account pilot."""

CONTROL_REQUIREMENTS = {
    9001: ("public_catalogue_browse", "jellyfin"),
    9002: ("books_private", "audiobookshelf"),
    9004: ("home_control", "home_assistant"),
    9007: ("listening_history", "jellyfin"),
    9009: ("requests_submit", "seerr"),
    135: ("aster_private_context", "aster"),
    136: ("personal_youtube", "youtube"),
    139: ("aster_private_context", "aster"),
    100: ("public_catalogue_browse", "jellyfin"),
    110: ("public_catalogue_browse", "jellyfin"),
    120: ("public_catalogue_browse", "jellyfin"),
    121: ("public_catalogue_browse", "jellyfin"),
    130: ("public_catalogue_browse", "jellyfin"),
    131: ("public_catalogue_browse", "jellyfin"),
    132: ("public_catalogue_browse", "jellyfin"),
    133: ("public_catalogue_browse", "jellyfin"),
    134: ("public_catalogue_browse", "jellyfin"),
    140: ("public_catalogue_browse", "jellyfin"),
    141: ("public_catalogue_browse", "jellyfin"),
    142: ("public_catalogue_browse", "jellyfin"),
    143: ("public_catalogue_browse", "jellyfin"),
    144: ("public_catalogue_browse", "jellyfin"),
    145: ("public_catalogue_browse", "jellyfin"),
    146: ("public_catalogue_browse", "jellyfin"),
}
WINDOW_REQUIREMENTS = {
    11110: ("books_private", "audiobookshelf"),
    11118: ("books_private", "audiobookshelf"),
    11119: ("books_private", "audiobookshelf"),
    11120: ("books_private", "audiobookshelf"),
    11112: ("home_control", "home_assistant"),
    11113: ("listening_history", "jellyfin"),
    11114: ("listening_history", "jellyfin"),
    11115: ("listening_history", "jellyfin"),
    11116: ("listening_history", "jellyfin"),
    11117: ("listening_history", "jellyfin"),
    11127: ("aster_private_context", "aster"),
    11128: ("aster_private_context", "aster"),
    11132: ("requests_submit", "seerr"),
    11133: ("requests_submit", "seerr"),
}


def active_profile(registry):
    profile_id = registry.get("active_profile_id")
    for profile in registry.get("profiles", ()):
        if profile.get("id") == profile_id:
            return profile
    return {"role": "guest", "entitlements": [], "service_mappings": []}


def active_role(registry):
    value = active_profile(registry).get("role")
    return value if value in ("member", "recovery_admin") else "guest"


def allows(registry, requirement):
    profile = active_profile(registry)
    entitlement, service = requirement
    entitlements = set(profile.get("entitlements", ()))
    enabled_services = {
        mapping.get("service") for mapping in profile.get("service_mappings", ())
        if mapping.get("enabled") is True
    }
    return entitlement in entitlements and service in enabled_services


def guest_catalogue_allowed(registry):
    return allows(registry, ("guest_catalogue_browse", "jellyfin_guest"))


def guest_playback_allowed(registry):
    return guest_catalogue_allowed(registry) and allows(
        registry, ("guest_media_playback", "jellyfin_guest")
    )


def select_decision(registry, focus_id):
    role = active_role(registry)
    if focus_id == 9005:
        return "allow" if role == "recovery_admin" else "profiles"
    if focus_id == 9001 and role == "guest" and guest_catalogue_allowed(registry):
        return "guest-catalogue"
    requirement = CONTROL_REQUIREMENTS.get(focus_id)
    if requirement and not allows(registry, requirement):
        return "deny"
    return "allow"


def private_surface(registry, window_id, folder_path=""):
    requirement = WINDOW_REQUIREMENTS.get(window_id)
    if requirement and not allows(registry, requirement):
        return True
    if window_id == 10000:
        return not allows(registry, ("public_catalogue_browse", "jellyfin"))
    if window_id == 10025:
        if "plugin://plugin.video.asterguest/" in folder_path:
            return not guest_catalogue_allowed(registry)
        if "plugin.video.youtube" in folder_path:
            return not allows(registry, ("personal_youtube", "youtube"))
        return not allows(registry, ("public_catalogue_browse", "jellyfin"))
    return False
