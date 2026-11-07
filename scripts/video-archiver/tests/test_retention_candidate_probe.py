"""The operator probe must fail closed without exposing a source exception."""

import io
import json
from contextlib import redirect_stdout
from unittest import TestCase
from unittest.mock import patch

from video_archiver.retention_candidate_probe import main


class CandidateProbeTests(TestCase):
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
