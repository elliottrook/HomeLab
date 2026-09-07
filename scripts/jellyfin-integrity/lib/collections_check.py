"""Collection/playlist count regression check — catches a recurrence of
the 'Clean up collections and playlists' startup-task deletion bug on
ANY Jellyfin library, not just music. Compares against the last known-good
baseline persisted between runs.

Also checks the cleanup task's own trigger configuration for drift back
to enabled, independent of whether a count drop has actually happened.
"""
import json
import os

DEFAULT_DROP_THRESHOLD = 0.10  # flag a drop of more than 10% from baseline


def load_baseline(state_path):
    if not os.path.isfile(state_path):
        return None
    with open(state_path) as f:
        return json.load(f)


def save_baseline(state_path, collections_count, playlists_count):
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    with open(state_path, "w") as f:
        json.dump({"collections": collections_count, "playlists": playlists_count}, f)


def check_counts(jf, state_path, drop_threshold=DEFAULT_DROP_THRESHOLD):
    collections = jf.get_collections()
    playlists = jf.get_playlists()
    current = {"collections": len(collections), "playlists": len(playlists)}

    baseline = load_baseline(state_path)
    result = {"current": current, "baseline": baseline, "alerts": []}

    if baseline is not None:
        for key in ("collections", "playlists"):
            before = baseline.get(key, 0)
            after = current[key]
            if before > 0 and after < before * (1 - drop_threshold):
                result["alerts"].append({
                    "type": f"{key}_count_drop",
                    "before": before,
                    "after": after,
                    "drop_fraction": round(1 - after / before, 3),
                })

    save_baseline(state_path, current["collections"], current["playlists"])
    return result


def check_cleanup_task_trigger(jf, task_id):
    """Flag if the 'Clean up collections and playlists' task's trigger
    list is non-empty (it should stay cleared — see 04-Operations.md).
    """
    task = jf.get_scheduled_task(task_id)
    triggers = task.get("Triggers", []) if task else []
    return {
        "task_id": task_id,
        "triggers": triggers,
        "drifted": len(triggers) > 0,
    }
