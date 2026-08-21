#!/bin/bash

set -u

warning_seconds=$((30 * 24 * 60 * 60))
failures=0
checked=0
temp_dir="$(mktemp -d)"

trap 'rm -rf "$temp_dir"' EXIT

endpoints=(
    'Proxmox|192.168.50.10|8006'
    'Portainer|192.168.20.20|9443'
    'UniFi Controller|192.168.50.21|11443'
    'TrueNAS|192.168.20.40|443'
    'Main Synology|192.168.20.41|5001'
    'Backup Synology|192.168.20.42|5001'
)

printf '%s\n' 'HomeLab certificate monitoring:'

for endpoint in "${endpoints[@]}"; do
    IFS='|' read -r label host port <<< "$endpoint"
    checked=$((checked + 1))
    pem_file="$temp_dir/certificate-$checked.pem"

    printf '\n%s — %s:%s\n' "$label" "$host" "$port"

    if ! nc -z -w 5 "$host" "$port" >/dev/null 2>&1; then
        echo 'CRITICAL: TLS endpoint is unreachable'
        failures=$((failures + 1))
        continue
    fi

    printf '' |
    perl -e '
        $timeout = shift;
        alarm $timeout;
        exec @ARGV;
    ' 10 \
    openssl s_client \
      -connect "$host:$port" \
      -servername "$host" \
      -showcerts 2>/dev/null |
    sed -n \
      '/-----BEGIN CERTIFICATE-----/,/-----END CERTIFICATE-----/p' \
      > "$pem_file"

    if ! openssl x509 -in "$pem_file" -noout >/dev/null 2>&1; then
        echo 'CRITICAL: certificate could not be read'
        failures=$((failures + 1))
        continue
    fi

    subject="$(
        openssl x509 -in "$pem_file" -noout -subject |
        sed 's/^subject= *//'
    )"

    expiry="$(
        openssl x509 -in "$pem_file" -noout -enddate |
        sed 's/^notAfter=//'
    )"

    fingerprint="$(
        openssl x509 -in "$pem_file" -noout -fingerprint -sha256 |
        sed 's/^SHA256 Fingerprint=//'
    )"

    printf 'Subject: %s\n' "${subject:-unnamed certificate}"
    printf 'Expires: %s\n' "$expiry"
    printf 'Fingerprint: %s\n' "$fingerprint"

    if openssl x509 \
        -in "$pem_file" \
        -checkend "$warning_seconds" \
        -noout >/dev/null 2>&1
    then
        echo 'Status: OK — valid for more than 30 days'
    else
        echo 'CRITICAL: certificate expires within 30 days or has expired'
        failures=$((failures + 1))
    fi
done

printf '\nCertificates checked: %s\n' "$checked"
printf 'Certificate failures: %s\n' "$failures"

if [ "$failures" -gt 0 ]; then
    exit 1
fi

echo 'Certificate monitoring: healthy'
exit 0
