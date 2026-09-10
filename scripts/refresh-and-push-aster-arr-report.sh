#!/usr/bin/env bash
# TrueNAS root cron wrapper. Its SSH key is forced to the Proxmox receiver.
set -euo pipefail

readonly report_root=/mnt/Media/data/tools/aster-arr-report
readonly key_path="$report_root/transport/id_ed25519"
readonly known_hosts_path="$report_root/transport/known_hosts"

/usr/bin/python3 "$report_root/produce-aster-arr-report.py"
exec /usr/bin/ssh -i "$key_path" -o BatchMode=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile="$known_hosts_path" -o GlobalKnownHostsFile=/dev/null -o ClearAllForwardings=yes root@192.168.50.10 true < "$report_root/reports/latest.json"
