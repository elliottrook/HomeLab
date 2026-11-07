#!/bin/bash
set -euo pipefail

BACKUP="${1:-}"
PROOF="${2:-}"
if [[ "$BACKUP" != /srv/aster-games/backups/* ]] || \
   [[ "$PROOF" != /srv/aster-games/restore-proofs/* ]] || \
   [[ ! -f "$BACKUP/MANIFEST.sha256" ]] || [[ -e "$PROOF" ]]; then
    echo "usage: $0 /srv/aster-games/backups/<id> /srv/aster-games/restore-proofs/<new-id>" >&2
    exit 2
fi
for variable in ROMM_DB_PASSWORD ROMM_DB_ROOT_PASSWORD ROMM_AUTH_SECRET_KEY \
    ROMM_CACHE_PASSWORD ROMM_ROMARR_API_KEY ROMARR_PASSWORD ROMARR_API_KEY \
    PROWLARR_URL PROWLARR_API_KEY SABNZBD_URL SABNZBD_API_KEY; do
    [[ -n "${!variable:-}" ]] || { echo "missing required environment: $variable" >&2; exit 2; }
done

PREFIX=aster-games-restore-proof
NETWORK="$PREFIX"
DB="$PREFIX-db"
CACHE="$PREFIX-cache"
ROMM="$PREFIX-romm"
ROMARR="$PREFIX-romarr"
BROKER="$PREFIX-broker"
RUNTIME="$PROOF/runtime"
STARTED="$(date +%s)"
DB_IMAGE='mariadb:11.8.5@sha256:345fa26d595e8c7fe298e0c4098ed400356f502458769c8902229b3437d6da2b'
CACHE_IMAGE='valkey/valkey:8.1.4-alpine@sha256:e706d1213aaba6896c162bb6a3a9e1894e1a435f28f8f856d14fab2e10aa098b'
ROMM_IMAGE='rommapp/romm:5.4.0@sha256:03295f95a6290e752641f9553ac4198b0e5b71b879d57f7b2371b98f608feb54'
ROMARR_IMAGE='ghcr.io/blizzhacker/romarr:1.8.0@sha256:19cbfad5189d630cc914eed1efb174dbd05c1888484b9ef6eb3698f71dc56458'
BROKER_IMAGE='localhost/aster-games-broker:0.1.0'

for name in "$DB" "$CACHE" "$ROMM" "$ROMARR" "$BROKER"; do
    [[ -z "$(docker ps -aq --filter "name=^/${name}$")" ]] || {
        echo "disposable container already exists: $name" >&2
        exit 2
    }
done
[[ -z "$(docker network ls -q --filter "name=^${NETWORK}$")" ]] || {
    echo "disposable network already exists: $NETWORK" >&2
    exit 2
}

cleanup() {
    docker rm -f "$BROKER" "$ROMARR" "$ROMM" "$CACHE" "$DB" >/dev/null 2>&1 || true
    docker network rm "$NETWORK" >/dev/null 2>&1 || true
}
trap cleanup EXIT

install -d -o root -g root -m 0700 "$PROOF" "$RUNTIME" "$RUNTIME/state" \
    "$RUNTIME/library/nes" "$RUNTIME/staging" "$RUNTIME/mariadb"
(
    cd "$BACKUP"
    sha256sum -c MANIFEST.sha256 >/dev/null
)
tar -xf "$BACKUP/romm-state.tar" -C "$RUNTIME/state"
tar -xf "$BACKUP/romarr-state.tar" -C "$RUNTIME/state"
tar -xf "$BACKUP/broker-state.tar" -C "$RUNTIME/state"
tar -xf "$BACKUP/dats.tar" -C "$RUNTIME"
install -m 0644 "/srv/aster-games/library/nes/Aster Infrastructure Test (World) (Homebrew).nes" \
    "$RUNTIME/library/nes/Aster Infrastructure Test (World) (Homebrew).nes"
install -m 0644 "/media/usenet/complete/retro-games/aster-infrastructure-test/Aster Infrastructure Test (World) (Homebrew).nes" \
    "$RUNTIME/staging/Aster Infrastructure Test (World) (Homebrew).nes"
if [[ -d /srv/aster-games/library/.romarr-quarantine ]]; then
    cp -a /srv/aster-games/library/.romarr-quarantine "$RUNTIME/library/"
fi

docker network create --internal "$NETWORK" >/dev/null
docker run -d --name "$DB" --hostname restore-db --network "$NETWORK" \
    --network-alias romm-db \
    -e MARIADB_DATABASE=romm -e MARIADB_USER=romm \
    -e MARIADB_PASSWORD="$ROMM_DB_PASSWORD" \
    -e MARIADB_ROOT_PASSWORD="$ROMM_DB_ROOT_PASSWORD" \
    -v "$RUNTIME/mariadb:/var/lib/mysql" \
    --health-cmd 'healthcheck.sh --connect --innodb_initialized' \
    --health-interval 2s --health-timeout 3s --health-retries 30 \
    "$DB_IMAGE" >/dev/null
for _ in {1..40}; do
    [[ "$(docker inspect --format '{{.State.Health.Status}}' "$DB" 2>/dev/null || true)" == healthy ]] && break
    sleep 2
done
[[ "$(docker inspect --format '{{.State.Health.Status}}' "$DB")" == healthy ]]
docker exec -i "$DB" sh -c \
    'MYSQL_PWD="$MARIADB_PASSWORD" exec mariadb -u "$MARIADB_USER" "$MARIADB_DATABASE"' \
    < "$BACKUP/romm.sql"

docker run -d --name "$CACHE" --hostname restore-cache --network "$NETWORK" \
    --network-alias romm-cache -e ROMM_CACHE_PASSWORD="$ROMM_CACHE_PASSWORD" \
    --tmpfs /data \
    --health-cmd 'valkey-cli -a "$ROMM_CACHE_PASSWORD" ping' \
    --health-interval 2s --health-timeout 3s --health-retries 20 \
    "$CACHE_IMAGE" sh -c 'exec valkey-server --requirepass "$ROMM_CACHE_PASSWORD" --save ""' \
    >/dev/null
for _ in {1..20}; do
    [[ "$(docker inspect --format '{{.State.Health.Status}}' "$CACHE" 2>/dev/null || true)" == healthy ]] && break
    sleep 2
done
[[ "$(docker inspect --format '{{.State.Health.Status}}' "$CACHE")" == healthy ]]

docker run -d --name "$ROMM" --hostname aster-games-restore --network "$NETWORK" \
    --network-alias romm \
    -e DB_HOST=romm-db -e DB_NAME=romm -e DB_USER=romm \
    -e DB_PASSWD="$ROMM_DB_PASSWORD" -e REDIS_HOST=romm-cache \
    -e REDIS_PASSWORD="$ROMM_CACHE_PASSWORD" \
    -e ROMM_AUTH_SECRET_KEY="$ROMM_AUTH_SECRET_KEY" \
    -e ROMM_SESSION_SECURE_COOKIE=true \
    -e ROMM_CORS_ALLOWED_ORIGINS=https://restore.invalid \
    -e FORWARDED_ALLOW_IPS=127.0.0.1 -e HASHEOUS_API_ENABLED=false \
    -e DEVICE_INSTALL_ENABLED=false -e TZ=America/Vancouver \
    -v "$RUNTIME/library:/romm/library/roms:ro" \
    -v "$RUNTIME/state/romm/assets:/romm/assets" \
    -v "$RUNTIME/state/romm/config:/romm/config" \
    -v "$RUNTIME/state/romm/resources:/romm/resources" \
    "$ROMM_IMAGE" >/dev/null

for _ in {1..60}; do
    if docker exec "$ROMM" python -c \
        'import urllib.request; urllib.request.urlopen("http://127.0.0.1:8080/api/heartbeat",timeout=3)' \
        >/dev/null 2>&1; then break; fi
    [[ "$(docker inspect --format '{{.State.Status}}' "$ROMM" 2>/dev/null || true)" == running ]] || break
    sleep 3
done
if ! docker exec "$ROMM" python -c \
    'import urllib.request; urllib.request.urlopen("http://127.0.0.1:8080/api/heartbeat",timeout=3)' \
    >/dev/null; then
    docker inspect --format 'status={{.State.Status}} exit={{.State.ExitCode}}' "$ROMM" \
        > "$PROOF/romm-failure.log" 2>&1 || true
    docker logs --tail 80 "$ROMM" >> "$PROOF/romm-failure.log" 2>&1 || true
    chmod 0600 "$PROOF/romm-failure.log"
    exit 1
fi

docker run -d --name "$ROMARR" --hostname restore-romarr --network "$NETWORK" \
    --network-alias romarr \
    -e PUID=568 -e PGID=568 -e UMASK=002 -e TZ=America/Vancouver \
    -e LIBRARY_KIND=romm -e LIBRARY_URL=http://romm:8080 \
    -e LIBRARY_API_KEY="$ROMM_ROMARR_API_KEY" -e LIBRARY_PATH=/roms \
    -e ROMARR_PASSWORD="$ROMARR_PASSWORD" -e ROMARR_API_KEY="$ROMARR_API_KEY" \
    -e PROWLARR_URL="$PROWLARR_URL" -e PROWLARR_API_KEY="$PROWLARR_API_KEY" \
    -e SABNZBD_URL="$SABNZBD_URL" -e SABNZBD_API_KEY="$SABNZBD_API_KEY" \
    -e DAT_PATH=/dats \
    -v "$RUNTIME/state/romarr:/config" -v "$RUNTIME/library:/roms" \
    -v "$RUNTIME/staging:/restore-staging" -v "$RUNTIME/dats:/dats:ro" \
    "$ROMARR_IMAGE" >/dev/null

docker run -d --name "$BROKER" --hostname restore-broker --network "$NETWORK" \
    -e ASTER_GAMES_BIND=0.0.0.0 -e ASTER_GAMES_PORT=8099 \
    -e ASTER_GAMES_DB=/state/proposals.sqlite3 \
    -e ASTER_GAMES_CLIENT_TOKEN_FILE=/run/secrets/broker_client_token \
    -e ASTER_GAMES_ROMM_URL=http://romm:8080 \
    -e ASTER_GAMES_ROMM_TOKEN_FILE=/run/secrets/romm_broker_token \
    -e ASTER_GAMES_RELEASE_GATE=/config/release-gate.json \
    -v "$RUNTIME/state/broker:/state" \
    -v /opt/aster-games/config/release-gate.json:/config/release-gate.json:ro \
    -v /etc/aster-games/secrets/broker-client-token:/run/secrets/broker_client_token:ro \
    -v /etc/aster-games/secrets/romm-broker-token:/run/secrets/romm_broker_token:ro \
    --read-only --tmpfs /tmp --cap-drop ALL \
    --health-cmd 'python -c "import urllib.request; urllib.request.urlopen(\"http://127.0.0.1:8099/health\",timeout=4)"' \
    --health-interval 2s --health-timeout 3s --health-retries 20 \
    "$BROKER_IMAGE" >/dev/null

for _ in {1..40}; do
    if docker exec "$ROMARR" python -c \
           'import urllib.request; urllib.request.urlopen("http://127.0.0.1:6868/api/health",timeout=3)' \
           >/dev/null 2>&1 && \
       [[ "$(docker inspect --format '{{.State.Health.Status}}' "$BROKER" 2>/dev/null || true)" == healthy ]]; then
        break
    fi
    sleep 2
done
docker exec "$ROMARR" python -c \
    'import urllib.request; urllib.request.urlopen("http://127.0.0.1:6868/api/health",timeout=3)' \
    >/dev/null
[[ "$(docker inspect --format '{{.State.Health.Status}}' "$BROKER")" == healthy ]]

docker exec "$DB" sh -c \
    'MYSQL_PWD="$MARIADB_PASSWORD" exec mariadb -N -B -u "$MARIADB_USER" "$MARIADB_DATABASE" -e "SELECT CONCAT(\"users=\",COUNT(*)) FROM users UNION ALL SELECT CONCAT(\"roms=\",COUNT(*)) FROM roms UNION ALL SELECT CONCAT(\"saves=\",COUNT(*)) FROM saves UNION ALL SELECT CONCAT(\"states=\",COUNT(*)) FROM states UNION ALL SELECT CONCAT(\"client_tokens=\",COUNT(*)) FROM client_tokens UNION ALL SELECT CONCAT(\"devices=\",COUNT(*)) FROM devices"' \
    > "$PROOF/restored-counts.txt"
python3 - "$RUNTIME/state/broker/proposals.sqlite3" >> "$PROOF/restored-counts.txt" <<'PY'
import sqlite3
import sys
with sqlite3.connect(sys.argv[1]) as database:
    assert database.execute("pragma integrity_check").fetchone()[0] == "ok"
    print("proposals=" + str(database.execute("select count(*) from proposals").fetchone()[0]))
PY
cmp "$BACKUP/source-counts.txt" "$PROOF/restored-counts.txt"
COUNTS_MATCH=true

RESTORED_MEDIA_HASH="$(sha256sum "$RUNTIME/library/nes/Aster Infrastructure Test (World) (Homebrew).nes" | awk '{print $1}')"
EXPECTED_MEDIA_HASH="$(cat "$BACKUP/sampled-media.sha256")"
[[ "$RESTORED_MEDIA_HASH" == "$EXPECTED_MEDIA_HASH" ]]
MEDIA_MATCH=true

OVERWRITE_REFUSED="$(docker exec -i "$ROMARR" python - <<'PY'
import hashlib, json, os, urllib.error, urllib.request
target = "/roms/nes/Aster Infrastructure Test (World) (Homebrew).nes"
source = "/restore-staging/Aster Infrastructure Test (World) (Homebrew).nes"
digest = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
before = digest(target)
body = json.dumps({"path": source, "platform": "nes", "force": False}).encode()
request = urllib.request.Request(
    "http://127.0.0.1:6868/api/v1/manualimport", data=body, method="POST",
    headers={"X-Api-Key": os.environ["ROMARR_API_KEY"], "Content-Type": "application/json"})
try:
    with urllib.request.urlopen(request, timeout=20) as response:
        status = response.status
        result = json.load(response)
except urllib.error.HTTPError as error:
    status = error.code
    result = {}
after = digest(target)
refused = status >= 400 or not result.get("imported")
print("true" if before == after and refused else "false")
PY
)"
[[ "$OVERWRITE_REFUSED" == true ]]

if docker exec "$ROMARR" python -c \
    'import socket,sys
try:
    socket.create_connection(("1.1.1.1",443),2)
except OSError:
    raise SystemExit(0)
raise SystemExit(1)' \
    >/dev/null 2>&1; then
    NO_EGRESS=true
else
    echo "restore container unexpectedly reached the Internet" >&2
    exit 1
fi

ROMM_IP="$(docker inspect --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$ROMM")"
ROMARR_IP="$(docker inspect --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$ROMARR")"
run_doctor() {
    python3 /opt/aster-games/ops/doctor.py \
        --romm "http://$ROMM_IP:8080/api/heartbeat" \
        --romarr "http://$ROMARR_IP:6868/api/health" \
        --broker-container "$BROKER" --database-container "$DB" --cache-container "$CACHE" \
        --config "$RUNTIME/state/romarr/romarr.json" \
        --gate /opt/aster-games/config/release-gate.json \
        --library "$RUNTIME/library" --state "$RUNTIME/state" \
        --library-min-free-gib "${1:-1}" --state-min-free-gib 1
}
run_doctor 1 > "$PROOF/doctor.json"

if run_doctor 999999 > "$PROOF/capacity-alert.json"; then
    echo "capacity alert was not detected" >&2
    exit 1
fi
python3 - "$PROOF/capacity-alert.json" <<'PY'
import json, sys
d=json.load(open(sys.argv[1]))
library=next(x for x in d["services"] if x["name"] == "library")
assert d["ok"] is False and library["ok"] is False
PY
CAPACITY_ALERT_DETECTED=true

docker stop "$CACHE" >/dev/null
if run_doctor 1 > "$PROOF/dependency-alert.json"; then
    echo "dependency failure was not detected" >&2
    exit 1
fi
python3 - "$PROOF/dependency-alert.json" "$CACHE" <<'PY'
import json, sys
d=json.load(open(sys.argv[1]))
cache=next(x for x in d["services"] if x["name"] == sys.argv[2])
assert d["ok"] is False and cache["ok"] is False
PY
DEPENDENCY_ALERT_DETECTED=true
docker start "$CACHE" >/dev/null
for _ in {1..20}; do
    [[ "$(docker inspect --format '{{.State.Health.Status}}' "$CACHE" 2>/dev/null || true)" == healthy ]] && break
    sleep 2
done
[[ "$(docker inspect --format '{{.State.Health.Status}}' "$CACHE")" == healthy ]]

if docker exec "$ROMARR" python -c \
    'import urllib.error,urllib.request
r=urllib.request.Request("http://127.0.0.1:6868/api/v1/config",headers={"X-Api-Key":"deliberately-wrong"})
try:
    urllib.request.urlopen(r,timeout=5)
except urllib.error.HTTPError as e:
    raise SystemExit(0 if e.code == 401 else 1)
raise SystemExit(1)' && \
   docker exec "$ROMM" python -c \
    'import urllib.error,urllib.request
r=urllib.request.Request("http://127.0.0.1:8080/api/roms",headers={"Authorization":"Bearer deliberately-wrong"})
try:
    urllib.request.urlopen(r,timeout=5)
except urllib.error.HTTPError as e:
    raise SystemExit(0 if e.code == 401 else 1)
raise SystemExit(1)'; then
    AUTH_FAILURE_DETECTED=true
else
    echo "authentication failure was not detected" >&2
    exit 1
fi

ROLLBACK_CONFIG="$RUNTIME/state/romarr/romarr.json"
ROLLBACK_COPY="$RUNTIME/state/romarr/romarr.json.restore-proof-rollback"
docker stop "$ROMARR" >/dev/null
ROLLBACK_BEFORE="$(sha256sum "$ROLLBACK_CONFIG" | awk '{print $1}')"
cp -p "$ROLLBACK_CONFIG" "$ROLLBACK_COPY"
python3 - "$ROLLBACK_CONFIG" <<'PY'
import json, sys
p=sys.argv[1]
d=json.load(open(p))
d["settings"]["_restore_upgrade_probe"] = True
open(p,"w").write(json.dumps(d,sort_keys=True)+"\n")
PY
mv "$ROLLBACK_COPY" "$ROLLBACK_CONFIG"
ROLLBACK_AFTER="$(sha256sum "$ROLLBACK_CONFIG" | awk '{print $1}')"
[[ "$ROLLBACK_BEFORE" == "$ROLLBACK_AFTER" ]]
UPGRADE_ROLLBACK_STATE_MATCH=true
docker start "$ROMARR" >/dev/null
docker restart "$BROKER" >/dev/null
for _ in {1..30}; do
    if docker exec "$ROMARR" python -c \
           'import urllib.request; urllib.request.urlopen("http://127.0.0.1:6868/api/health",timeout=3)' \
           >/dev/null 2>&1 && \
       [[ "$(docker inspect --format '{{.State.Health.Status}}' "$BROKER" 2>/dev/null || true)" == healthy ]]; then
        break
    fi
    sleep 2
done
run_doctor 1 > "$PROOF/doctor.json"
RESTART_RECOVERY=true

if grep -Fq 'Aster Infrastructure Test' "$PROOF/doctor.json" || \
   grep -Eiq '(api[_-]?key|password|bearer|token)' "$PROOF/doctor.json"; then
    echo "Doctor output violated content-silent policy" >&2
    exit 1
fi
CONTENT_SILENT_OBSERVABILITY=true

ACQUISITION_DISABLED="$(python3 - "$RUNTIME/state/romarr/romarr.json" <<'PY'
import json, sys
s=json.load(open(sys.argv[1]))["settings"]
disabled=(not s.get("auto_import", False)
          and all(not x.get("enable", False) for x in s.get("indexers", []))
          and all(not x.get("enable", False) for x in s.get("download_clients", [])))
print("true" if disabled else "false")
PY
)"
[[ "$ACQUISITION_DISABLED" == true ]]

FINISHED="$(date +%s)"
cat > "$PROOF/evidence.json" <<EOF
{
  "schema_version": 1,
  "isolated_hostname": "aster-games-restore",
  "network_internal": true,
  "no_egress": $NO_EGRESS,
  "acquisition_disabled": $ACQUISITION_DISABLED,
  "counts_match": $COUNTS_MATCH,
  "sampled_media_hash_match": $MEDIA_MATCH,
  "existing_media_overwrite_refused": $OVERWRITE_REFUSED,
  "capacity_alert_detected": $CAPACITY_ALERT_DETECTED,
  "dependency_alert_detected": $DEPENDENCY_ALERT_DETECTED,
  "authentication_failure_detected": $AUTH_FAILURE_DETECTED,
  "restart_recovery": $RESTART_RECOVERY,
  "upgrade_rollback_state_match": $UPGRADE_ROLLBACK_STATE_MATCH,
  "content_silent_observability": $CONTENT_SILENT_OBSERVABILITY,
  "doctor_ok": true,
  "duration_seconds": $((FINISHED - STARTED)),
  "disposable_runtime_destroyed": true
}
EOF
chmod 0600 "$PROOF"/*.txt "$PROOF"/*.json
sha256sum "$PROOF/restored-counts.txt" "$PROOF/doctor.json" \
    "$PROOF/capacity-alert.json" "$PROOF/dependency-alert.json" \
    "$PROOF/evidence.json" \
    > "$PROOF/EVIDENCE.sha256"
chmod 0600 "$PROOF/EVIDENCE.sha256"

cleanup
trap - EXIT
find "$RUNTIME" -depth -mindepth 1 -delete
rmdir "$RUNTIME"
printf 'restore_proof_complete=true duration_seconds=%s\n' "$((FINISHED - STARTED))"
