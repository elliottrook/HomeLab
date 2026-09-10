#!/bin/sh
set -eu

readonly candidate=/run/aster-ha-report.candidate.json
readonly lxc_candidate=/tmp/aster-ha-report.candidate.json
trap 'rm -f "$candidate"' EXIT
ASTER_HA_REPORT_PATH="$candidate" /usr/bin/python3 /usr/local/libexec/produce-aster-ha-report.py
/usr/sbin/pct push 104 "$candidate" "$lxc_candidate"
/usr/sbin/pct exec 104 -- /usr/bin/install -o root -g aster -m 640 "$lxc_candidate" /var/lib/aster/ha-report/latest.json
/usr/sbin/pct exec 104 -- /usr/bin/rm -f "$lxc_candidate"
