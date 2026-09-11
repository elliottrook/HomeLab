#!/usr/bin/env python3
"""One-off manual archive of Rango, whose source is a raw UHD BluRay ISO the
normal pipeline can't probe. The main feature was already extracted by hand
(BDMV/STREAM/00100.m2ts, confirmed via ffprobe: 107.2 min, matches Rango's
real runtime, HEVC Main10 4K). This reuses the project's own tested
transcode/verify/archive/Radarr-cleanup logic exactly, just with a manually
supplied source file instead of one found by candidates.py's normal
Radarr-driven discovery (which still points at the untouched .iso).

Kept as a REUSABLE TEMPLATE for the next ISO source (see Video-Library-
Archiving.md's "ISO (disc image) sources" note for the full extraction
process this assumes has already happened). To reuse: update title,
arr_file_id/arr_parent_id (from Radarr's /api/v3/movie), source_path (the
extracted feature file), size_bytes, date_added, and archive_dest_path
below for the new movie."""
import datetime
import logging
import sys
from pathlib import Path

sys.path.insert(0, ".")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

from video_archiver.arr_client import RadarrClient, SonarrClient
from video_archiver.candidates import Candidate
from video_archiver.config import Config
from video_archiver.pipeline import RunLogger, _process_one

config = Config.load(Path("config.json"))
radarr = RadarrClient(config.radarr_url, config.radarr_api_key)
sonarr = SonarrClient(config.sonarr_url, config.sonarr_api_key)

candidate = Candidate(
    kind="movie",
    arr_file_id=22,
    title="Rango",
    source_path=Path("/mnt/Media/data/tools/video-archiver/work/rango-main-feature.m2ts"),
    size_bytes=64063211520,
    date_added=datetime.datetime(2024, 5, 29, tzinfo=datetime.timezone.utc),
    archive_dest_path=config.movies_archive_root / "Rango (2011)" / "Rango (2011).mkv",
    delete_fn_name="delete_movie_file",
    arr_parent_id=35,
)

run_log = RunLogger(config.log_dir)
ok = _process_one(candidate, config, False, radarr, sonarr, run_log)
print("SUCCESS" if ok else "FAILED")
run_log.close()
