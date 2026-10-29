#!/bin/bash

set -u

repo="$HOME/lab/homelab"
state_dir="$HOME/lab/monitoring-state/reports"
latest_log="$state_dir/latest.log"
last_alert_hash="$state_dir/last-alert.sha256"
last_success="$state_dir/last-success.txt"
alert_script="$repo/scripts/backup-alert"

mkdir -p "$state_dir"

timestamp="$(date '+%Y-%m-%d %H:%M:%S %Z')"

set +e
drift_output="$("$repo/scripts/drift-check.sh" check 2>&1)"
drift_result=$?

doctor_capture="$state_dir/doctor-output.txt"
doctor_collector_result="$state_dir/doctor-collector-result.json"
rm -f "$doctor_collector_result"
/usr/bin/python3 "$repo/scripts/build-aster-health-report.py" \
    --doctor "$repo/scripts/doctor.sh" \
    --capture-output "$doctor_capture" \
    --output "$state_dir/aster-health.json" \
    --structured-output "$state_dir/aster-inference.json" \
    --catalogue-output "$state_dir/diagnostic-catalogue.json" \
    --result-output "$doctor_collector_result" \
    --publish
health_publish_result=$?
if [ "$health_publish_result" -eq 0 ] && [ -f "$doctor_collector_result" ]; then
    doctor_result="$(/usr/bin/python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["doctor_exit"])' "$doctor_collector_result")"
else
    doctor_result=1
fi
doctor_output="$(cat "$doctor_capture" 2>/dev/null || true)"

certificate_output="$("$repo/scripts/certificate-check.sh" 2>&1)"
certificate_result=$?
set -e

{
    printf 'HomeLab scheduled report: %s\n\n' "$timestamp"
    printf '%s\n' 'Configuration drift'
    printf '%s\n\n' "$drift_output"
    printf '%s\n' 'HomeLab Doctor'
    printf '%s\n\n' "$doctor_output"
    printf '%s\n' 'Certificate Monitoring'
    printf '%s\n' "$certificate_output"
} > "$latest_log"

problems=""
if [ "$health_publish_result" -ne 0 ]; then
    problems="Aster health-summary publication failed.\n"
fi

# Exit 1 means genuine drift; drift-check sends and deduplicates that alert.
# Anything higher means the drift checker itself failed.
if [ "$drift_result" -gt 1 ]; then
    problems="${problems}Configuration drift check could not complete.\n"
fi

if [ "$doctor_result" -ne 0 ]; then
    doctor_failures="$(
        printf '%s\n' "$doctor_output" |
        grep '^🔴' || true
    )"

    if [ -n "$doctor_failures" ]; then
        problems="${problems}${doctor_failures}\n"
    else
        problems="${problems}HomeLab Doctor exited with status ${doctor_result}.\n"
    fi
fi

if [ -n "$problems" ]; then
    alert_body="$(
        printf 'Scheduled HomeLab health check failed at %s.\n\n' "$timestamp"
        printf '%b' "$problems"
        printf '\nFull report: %s\n' "$latest_log"
    )"

    current_hash="$(
        printf '%s' "$problems" |
        shasum -a 256 |
        awk '{print $1}'
    )"

    previous_hash=""
    if [ -f "$last_alert_hash" ]; then
        previous_hash="$(cat "$last_alert_hash")"
    fi

    if [ "$current_hash" != "$previous_hash" ]; then
        if "$alert_script" \
            "HomeLab scheduled health failure" \
            "$alert_body"
        then
            printf '%s\n' "$current_hash" > "$last_alert_hash"
            printf '%s\n' 'New failure detected; alert sent.'
        else
            printf '%s\n' 'ERROR: failure alert could not be sent.'
            exit 2
        fi
    else
        printf '%s\n' 'Failure remains unchanged; duplicate alert suppressed.'
    fi

    exit 1
fi

rm -f "$last_alert_hash"
printf '%s\n' "$timestamp" > "$last_success"

if [ "$drift_result" -eq 1 ]; then
    printf '%s\n' 'Configuration drift detected; drift-check handled its alert.'
    exit 1
fi

printf '%s\n' 'Scheduled HomeLab report: healthy; no alert required.'
exit 0
