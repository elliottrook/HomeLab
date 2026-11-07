#!/bin/bash
# Generate the B60-backed text digest, then hand narration to an independent
# systemd unit.  The narration unit uses the Mac-backed Aster voice path and
# deliberately has no dependency on this service, so a later B60 drain may
# stop the digest service without terminating narration already in progress.
set -uo pipefail
cd /opt/news-aggregator
PY=./venv/bin/python3

"$PY" digest.py || echo "digest.py exited non-zero, continuing"
systemctl start --no-block news-aggregator-audio.service \
    || echo "news-aggregator-audio.service failed to queue"
