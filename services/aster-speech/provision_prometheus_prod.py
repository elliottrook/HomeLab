"""Add the production Aster Voice scrape target and alert rules on LXC 109."""

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
PROMTOOL = "/usr/local/bin/promtool"
JOB = """

  - job_name: aster-voice-production
    scrape_interval: 15s
    scrape_timeout: 5s
    metrics_path: /metrics
    static_configs:
      - targets:
          - 192.168.20.37:9131
"""
ALERTS = """

      - alert: AsterVoiceProductionUnavailable
        expr: up{job="aster-voice-production"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: Production Aster Voice metrics endpoint is unavailable

      - alert: AsterVoiceProductionInteractiveLatencyHigh
        expr: |
          histogram_quantile(0.95,
            sum by (le) (rate(aster_voice_request_duration_seconds_bucket{job="aster-voice-production",caller="interactive"}[10m]))) > 1.5
          and sum(rate(aster_voice_request_duration_seconds_count{job="aster-voice-production",caller="interactive"}[10m])) > 0
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: Production Aster Voice interactive p95 exceeds 1.5 seconds

      - alert: AsterVoiceProductionRendererErrors
        expr: sum(increase(aster_voice_render_errors_total{job="aster-voice-production"}[15m])) >= 3
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: Production Aster Voice has repeated renderer failures

      - alert: AsterVoiceProductionInteractiveQueueStuck
        expr: aster_voice_queue_depth{job="aster-voice-production",caller="interactive"} > 0
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: Production Aster Voice interactive work is persistently queued

      - alert: AsterVoiceProductionInteractiveWorkersSaturated
        expr: aster_voice_workers_busy{job="aster-voice-production",caller="interactive"} >= 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: Production Aster Voice interactive workers are persistently busy
"""

raw_config = CONFIG.read_text(encoding="utf-8")
raw_rules = RULES.read_text(encoding="utf-8")
job_present = "job_name: aster-voice-production" in raw_config
alerts_present = "alert: AsterVoiceProductionUnavailable" in raw_rules
if job_present != alerts_present:
    raise RuntimeError("production scrape and alert configuration are partially applied")

candidate_config = raw_config if job_present else raw_config.rstrip() + JOB
candidate_rules = raw_rules if alerts_present else raw_rules.rstrip() + ALERTS
if candidate_config.count("job_name: aster-voice-production") != 1:
    raise RuntimeError("production scrape job is not unique")
if candidate_rules.count("alert: AsterVoiceProductionUnavailable") != 1:
    raise RuntimeError("production unavailable alert is not unique")

with tempfile.TemporaryDirectory(prefix="aster-prod-prometheus-") as temporary:
    temporary_path = Path(temporary)
    config_path = temporary_path / "prometheus.yml"
    rules_path = temporary_path / "aster-voice-alerts.yml"
    rules_path.write_text(candidate_rules, encoding="utf-8")
    config_path.write_text(
        candidate_config.replace(str(RULES), str(rules_path)), encoding="utf-8"
    )
    subprocess.run([PROMTOOL, "check", "rules", str(rules_path)], check=True)
    subprocess.run([PROMTOOL, "check", "config", str(config_path)], check=True)

apply = "--apply" in sys.argv
print({"job": "aster-voice-production", "target": "192.168.20.37:9131",
       "present": job_present, "mode": "apply" if apply else "dry-run"})
if apply and not job_present:
    stamp = time.strftime("%Y%m%d-%H%M%S")
    for path, candidate in ((CONFIG, candidate_config), (RULES, candidate_rules)):
        backup = path.with_name(path.name + f".aster-voice-prod-before-{stamp}")
        shutil.copy2(path, backup)
        backup.chmod(0o600)
        temporary = path.with_name(path.name + ".aster-voice-prod-candidate")
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o640)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(candidate)
            stream.flush()
            os.fsync(stream.fileno())
        shutil.chown(temporary, user="root", group="prometheus")
        os.replace(temporary, path)
        print({"backup": str(backup)})
    subprocess.run([PROMTOOL, "check", "config", str(CONFIG)], check=True)
    print({"reload_pending": True})
