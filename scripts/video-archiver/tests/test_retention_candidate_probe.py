"""The operator probe must fail closed without exposing a source exception."""

import io
import json
from contextlib import redirect_stdout
from unittest import TestCase
from unittest.mock import patch

from video_archiver.retention_candidate_probe import main


class CandidateProbeTests(TestCase):
    def test_archive_movie_option_requires_archive_selection(self):
        output = io.StringIO()
        with (patch("sys.argv", ["probe", "--config", "/tmp/config.json",
                                 "--data-root", "/tmp", "--kind", "archive-movie"]),
              patch("video_archiver.retention_candidate_probe.observe",
                    return_value={"status": "observed_only", "deletion_enabled": False}) as movie,
              redirect_stdout(output)):
            main()
        self.assertTrue(movie.call_args.kwargs["archive"])

    def test_season_option_uses_season_observation_only(self):
        output = io.StringIO()
        with (patch("sys.argv", ["probe", "--config", "/tmp/config.json",
                                 "--data-root", "/tmp", "--kind", "season"]),
              patch("video_archiver.retention_candidate_probe.observe_season",
                    return_value={"status": "observed_only", "deletion_enabled": False}) as season,
              patch("video_archiver.retention_candidate_probe.observe") as movie,
              redirect_stdout(output)):
            main()
        season.assert_called_once()
        movie.assert_not_called()
        self.assertFalse(json.loads(output.getvalue())["deletion_enabled"])

    def test_source_change_reports_hold_without_traceback(self):
        output = io.StringIO()
        with (patch("sys.argv", ["probe", "--config", "/tmp/config.json",
                                 "--data-root", "/tmp"]),
              patch("video_archiver.retention_candidate_probe.observe",
                    side_effect=RuntimeError("Radarr or Jellyfin changed")),
              redirect_stdout(output)):
            main()
        self.assertEqual(json.loads(output.getvalue()),
                         {"status": "held_source_uncertain", "deletion_enabled": False})
