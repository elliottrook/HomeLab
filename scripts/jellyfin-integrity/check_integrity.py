#!/usr/bin/env python3
"""Jellyfin library integrity check + safe auto-correction.

Usage:
    check_integrity.py --config config.json [--apply] [--max-actions N]

Default is dry-run (report only, touches nothing). --apply performs the
safe, reversible, purely-organizational corrections (orphan foldering,
scatter consolidation, gap-fills, art extraction) up to the configured
per-run action cap, and writes a duplicate-album report for anything that
needs a human decision. Nothing is ever deleted by this tool.
"""
import argparse
import fcntl
import json
import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.jellyfin import JellyfinClient, JellyfinError
from lib.lidarr import LidarrClient, LidarrError
from lib.paths import PathTranslator
from lib import orphans, scatter, artwork, duplicates, collections_check


def load_config(path):
    with open(path) as f:
        return json.load(f)


class ActionBudget:
    def __init__(self, cap):
        self.cap = cap
        self.spent = 0

    def remaining(self):
        return max(0, self.cap - self.spent)

    def spend(self, n):
        self.spent += n


def acquire_lock(lock_path):
    lock_file = open(lock_path, "w")
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print(f"Another run holds the lock ({lock_path}); exiting.", file=sys.stderr)
        sys.exit(1)
    return lock_file


def run(config, apply_mode, tool_dir, max_actions_override=None):
    report = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "mode": "apply" if apply_mode else "dry-run",
        "orphans": {}, "scatter": {}, "artwork": {}, "duplicates": {},
        "collections": {}, "config_drift": {}, "errors": [],
    }

    jf = JellyfinClient(config["jellyfin"]["base_url"], config["jellyfin"]["api_key"])
    try:
        jf.ping()
    except JellyfinError as e:
        print(f"FATAL: Jellyfin unreachable or key invalid: {e}", file=sys.stderr)
        sys.exit(2)

    # Jellyfin's /Items catalog is a cache of the filesystem and was
    # observed to still report tracks under a folder already deleted from
    # disk by a prior manual fix. Every detector below reads that catalog,
    # so force a fresh scan and wait for it before trusting anything it
    # returns.
    print("Running Jellyfin library scan to sync catalog with disk state...")
    try:
        jf.run_task_and_wait(config["jellyfin"]["scan_task_id"])
    except JellyfinError as e:
        print(f"FATAL: library scan did not complete: {e}", file=sys.stderr)
        sys.exit(2)

    lidarr = LidarrClient(config["lidarr"]["base_url"], config["lidarr"]["api_key"])
    try:
        lidarr_artist_names = lidarr.get_artist_names()
    except LidarrError as e:
        print(f"FATAL: Lidarr unreachable or key invalid: {e}", file=sys.stderr)
        sys.exit(2)

    translator = PathTranslator(
        config["paths"]["jellyfin_container_prefix"],
        config["paths"]["host_root"],
    )
    music_library_id = config["jellyfin"]["music_library_id"]
    music_root_container = jf.get_library_root_path(music_library_id)
    music_root = translator.to_host(music_root_container)
    max_actions = max_actions_override or config["limits"]["max_actions_per_run"]
    budget = ActionBudget(max_actions)

    # --- Orphan tracks -----------------------------------------------
    orphan_items = orphans.find_orphans(jf, music_library_id)
    plan, skipped = orphans.plan_moves(orphan_items, translator)
    report["orphans"] = {"found": len(orphan_items), "planned": len(plan), "skipped": skipped}
    if apply_mode and plan:
        write_manifest(tool_dir, "orphans", plan)
        applied, errors = orphans.apply_moves(plan, budget.remaining())
        budget.spend(len(applied))
        report["orphans"]["applied"] = applied
        report["orphans"]["errors"] = errors
    else:
        report["orphans"]["planned_detail"] = plan

    # --- Scatter -------------------------------------------------------
    candidates = scatter.find_scatter_candidates(jf, music_library_id, translator, lidarr_artist_names, music_root)
    auto = [c for c in candidates if c["auto_consolidate"]]
    review = [c for c in candidates if not c["auto_consolidate"]]
    report["scatter"] = {
        "found": len(candidates),
        "auto_consolidate": len(auto),
        "queued_for_review": [
            {"artist": c["artist"], "album": c["album"], "reason": c["reason"],
             "folders": list(c["folders"].keys())}
            for c in review
        ],
    }
    if apply_mode:
        scatter_applied, scatter_errors = [], []
        for c in auto:
            if budget.remaining() <= 0:
                break
            moves = scatter.plan_consolidation(c)
            write_manifest(tool_dir, "scatter", moves)
            done, errs = scatter.apply_consolidation(moves, budget.remaining())
            budget.spend(len(done))
            scatter_applied.extend(done)
            scatter_errors.extend(errs)
            if not errs:
                for folder in scatter.empty_stray_folders(c):
                    scatter.remove_if_empty(folder)
        report["scatter"]["applied"] = scatter_applied
        report["scatter"]["errors"] = scatter_errors

    # --- Missing artwork -------------------------------------------------
    missing_art = artwork.find_albums_missing_art(jf, music_library_id, translator)
    art_done, art_skipped = [], []
    for album in missing_art:
        if apply_mode and budget.remaining() <= 0:
            break
        try:
            track_paths = sorted(
                os.path.join(album["host_path"], f)
                for f in os.listdir(album["host_path"])
                if f.lower().endswith((".flac", ".mp3", ".m4a", ".mp4"))
            )
        except OSError:
            art_skipped.append({**album, "reason": "album folder unreadable"})
            continue
        result = artwork.extract_cover(track_paths)
        if not result:
            art_skipped.append({**album, "reason": "no embedded art in any track"})
            continue
        if apply_mode:
            mime, image_bytes = result
            dest = artwork.write_cover(album["host_path"], mime, image_bytes)
            budget.spend(1)
            art_done.append({**album, "cover_written": dest})
        else:
            art_done.append({**album, "would_write_cover": True})
    report["artwork"] = {"missing_before": len(missing_art), "resolved": art_done, "skipped": art_skipped}

    # --- Duplicates / gap-fills -----------------------------------------
    pairs = duplicates.find_candidate_pairs(jf, music_library_id, translator)
    dup_report, gap_applied, gap_errors = [], [], []
    for pair in pairs:
        cmp = duplicates.compare_folders(pair["folder_a"], pair["folder_b"], pair["jf_tracks_by_path"])
        kind = duplicates.classify(cmp)
        if kind == "duplicate":
            dup_report.append({"kind": "duplicate", **cmp})
        elif kind == "gap_fill":
            moves = duplicates.plan_gap_fill(cmp)
            if apply_mode and budget.remaining() > 0:
                write_manifest(tool_dir, "gap_fill", moves)
                for mv in moves[:budget.remaining()]:
                    try:
                        if os.path.exists(mv["dst_host"]):
                            gap_errors.append({**mv, "error": "destination already exists"})
                            continue
                        os.rename(mv["src_host"], mv["dst_host"])
                        gap_applied.append(mv)
                        budget.spend(1)
                    except OSError as e:
                        gap_errors.append({**mv, "error": str(e)})
            else:
                gap_applied.append({"would_apply": moves})
    report["duplicates"] = {"candidate_pairs": len(pairs), "queued_for_approval": dup_report,
                             "gap_fills_applied": gap_applied, "gap_fill_errors": gap_errors}

    # --- Collection/playlist regression + config drift -------------------
    state_path = os.path.join(tool_dir, "reports", "collections_baseline.json")
    report["collections"] = collections_check.check_counts(
        jf, state_path, config.get("collections_drop_threshold", 0.10))
    report["config_drift"] = collections_check.check_cleanup_task_trigger(
        jf, config["jellyfin"]["cleanup_task_id"])

    report["actions_spent"] = budget.spent
    report["actions_cap"] = budget.cap

    # A per-item refresh doesn't pick up new cover.jpg files or moved
    # tracks (confirmed in 04-Operations.md); only a full library scan
    # does. Re-sync so this run's own changes are visible immediately
    # rather than waiting for the next scheduled run's pre-scan.
    if apply_mode and budget.spent > 0:
        try:
            jf.run_task_and_wait(config["jellyfin"]["scan_task_id"])
            report["post_apply_scan"] = "completed"
        except JellyfinError as e:
            report["post_apply_scan"] = f"failed: {e}"

    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    return report


def write_manifest(tool_dir, action_type, entries):
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(tool_dir, "reports", f"{ts}-{action_type}-manifest.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(entries, f, indent=2)


def write_report(tool_dir, report):
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    reports_dir = os.path.join(tool_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    json_path = os.path.join(reports_dir, f"{ts}-run.json")
    with open(json_path, "w") as f:
        json.dump(report, f, indent=2)

    txt_path = os.path.join(reports_dir, f"{ts}-run.txt")
    with open(txt_path, "w") as f:
        f.write(f"Jellyfin integrity check — {report['mode']} — {report['started_at']}\n\n")
        f.write(f"Orphans: {report['orphans']['found']} found, "
                f"{len(report['orphans'].get('applied', []))} fixed\n")
        f.write(f"Scatter: {report['scatter']['found']} candidates, "
                f"{report['scatter']['auto_consolidate']} auto-consolidated, "
                f"{len(report['scatter']['queued_for_review'])} queued for review\n")
        f.write(f"Artwork: {report['artwork']['missing_before']} missing, "
                f"{len([a for a in report['artwork']['resolved'] if 'cover_written' in a or 'would_write_cover' in a])} resolved\n")
        f.write(f"Duplicates: {report['duplicates']['candidate_pairs']} candidate pairs, "
                f"{len(report['duplicates']['queued_for_approval'])} queued for approval, "
                f"{len(report['duplicates']['gap_fills_applied'])} gap-fills applied\n")
        if report["collections"]["alerts"]:
            f.write(f"\n*** COLLECTION/PLAYLIST COUNT ALERT: {report['collections']['alerts']} ***\n")
        if report["config_drift"]["drifted"]:
            f.write(f"\n*** CLEANUP TASK TRIGGER RE-ENABLED: {report['config_drift']['triggers']} ***\n")
        f.write(f"\nActions: {report['actions_spent']}/{report['actions_cap']} used\n")
    return json_path, txt_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--apply", action="store_true", help="Perform safe corrections (default: dry-run)")
    parser.add_argument("--max-actions", type=int, default=None)
    args = parser.parse_args()

    tool_dir = os.path.dirname(os.path.abspath(__file__))

    lock_path = os.path.join(tool_dir, "reports", ".lock")
    os.makedirs(os.path.dirname(lock_path), exist_ok=True)
    lock_file = acquire_lock(lock_path)

    try:
        config = load_config(args.config)
        report = run(config, args.apply, tool_dir, args.max_actions)
        json_path, txt_path = write_report(tool_dir, report)
        print(f"Report written: {json_path}\n{txt_path}")
        if report["collections"]["alerts"] or report["config_drift"]["drifted"]:
            sys.exit(3)  # distinct exit code for "needs attention"
    finally:
        fcntl.flock(lock_file, fcntl.LOCK_UN)
        lock_file.close()


if __name__ == "__main__":
    main()
