"""Provision the Aster Voice Prometheus scrape and alert rules on LXC 109."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


CONFIG = Path("/etc/prometheus/prometheus.yml")
RULES = Path("/etc/prometheus/aster-voice-alerts.yml")
STAGED_RULES = Path("/run/aster-m8-prometheus/aster-voice-alerts.yml")
PROMTOOL = "/usr/local/bin/promtool"
JOB = """

  - job_name: aster-voice
    scrape_interval: 15s
    scrape_timeout: 5s
    metrics_path: /metrics
    static_configs:
      - targets:
          - 192.168.70.14:9131
"""

raw = CONFIG.read_text()
assert "job_name: aster-voice" not in raw, "Aster Voice scrape job already exists"
assert STAGED_RULES.is_file(), "staged Aster Voice alert rules are missing"
if "rule_files:" in raw:
    raise AssertionError("existing rule_files requires an explicit merge review")
candidate = raw.replace(
    "scrape_configs:\n",
    "rule_files:\n  - /etc/prometheus/aster-voice-alerts.yml\n\nscrape_configs:\n",
    1,
).rstrip() + JOB
assert candidate.count("job_name: aster-voice") == 1

with tempfile.TemporaryDirectory(prefix="aster-prometheus-") as temporary:
    candidate_path = Path(temporary) / "prometheus.yml"
    candidate_path.write_text(candidate)
    rules_path = Path(temporary) / "aster-voice-alerts.yml"
    shutil.copyfile(STAGED_RULES, rules_path)
    subprocess.run(
        [PROMTOOL, "check", "rules", str(rules_path)], check=True
    )
    # Validate paths using the final rules location in a disposable config.
    validation = candidate.replace(str(RULES), str(rules_path))
    candidate_path.write_text(validation)
    subprocess.run(
        [PROMTOOL, "check", "config", str(candidate_path)], check=True
    )

print({"job": "aster-voice", "target": "192.168.70.14:9131", "mode": "apply" if "--apply" in sys.argv else "dry-run"})

if "--apply" in sys.argv:
    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup = CONFIG.with_name(f"prometheus.yml.aster-voice-before-{stamp}")
    shutil.copy2(CONFIG, backup)
    rules_temporary = RULES.with_suffix(".yml.candidate")
    shutil.copyfile(STAGED_RULES, rules_temporary)
    os.chmod(rules_temporary, 0o640)
    shutil.chown(rules_temporary, user="root", group="prometheus")
    os.replace(rules_temporary, RULES)
    config_temporary = CONFIG.with_suffix(".yml.candidate")
    config_temporary.write_text(candidate)
    os.chmod(config_temporary, 0o640)
    shutil.chown(config_temporary, user="root", group="prometheus")
    os.replace(config_temporary, CONFIG)
    subprocess.run([PROMTOOL, "check", "config", str(CONFIG)], check=True)
    print({"backup": str(backup), "reload_pending": True})
