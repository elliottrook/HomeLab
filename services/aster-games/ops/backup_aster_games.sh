#!/bin/bash
set -euo pipefail

OUTPUT="${1:-}"
STATE=/srv/aster-games/state
SOURCE=/opt/aster-games
if [[ "$OUTPUT" != /srv/aster-games/backups/* ]] || [[ -e "$OUTPUT" ]]; then
    echo "usage: $0 /srv/aster-games/backups/<new-backup-id>" >&2
    exit 2
fi

install -d -o root -g root -m 0700 "$OUTPUT"
restart_application() {
    docker start aster-games-romm-1 >/dev/null 2>&1 || true
    for _ in {1..24}; do
        [[ "$(docker inspect --format '{{.State.Health.Status}}' aster-games-romm-1 2>/dev/null || true)" == healthy ]] && break
        sleep 5
    done
    docker start aster-games-romarr-1 aster-games-broker-1 >/dev/null 2>&1 || true
}
trap restart_application EXIT

docker stop aster-games-broker-1 aster-games-romarr-1 aster-games-romm-1 >/dev/null
docker exec aster-games-romm-db-1 sh -c \
    'MYSQL_PWD="$MARIADB_PASSWORD" exec mariadb-dump --single-transaction --quick --routines --events -u "$MARIADB_USER" "$MARIADB_DATABASE"' \
    > "$OUTPUT/romm.sql"

tar --numeric-owner -C "$STATE" -cpf "$OUTPUT/romm-state.tar" romm
tar --numeric-owner -C "$STATE" -cpf "$OUTPUT/romarr-state.tar" romarr
tar --numeric-owner -C "$STATE" -cpf "$OUTPUT/broker-state.tar" broker
tar --numeric-owner -C /srv/aster-games -cpf "$OUTPUT/dats.tar" dats

docker inspect --format '{{.Name}} {{.Config.Image}} {{.Image}}' \
    aster-games-romm-db-1 aster-games-romm-cache-1 aster-games-romm-1 \
    aster-games-romarr-1 aster-games-broker-1 > "$OUTPUT/image-identities.txt"
sha256sum "$SOURCE/compose.yaml" "$SOURCE/config/release-gate.json" \
    > "$OUTPUT/deployment-manifest.sha256"
{
    echo /etc/aster-games/aster-games.env
    echo /etc/aster-games/secrets/broker-client-token
    echo /etc/aster-games/secrets/romm-broker-token
    echo /etc/aster-games/secrets/romm-romarr-token
    echo "Secret values are excluded; recover from the source-local custody record."
} > "$OUTPUT/secret-references.txt"

docker exec aster-games-romm-db-1 sh -c \
    'MYSQL_PWD="$MARIADB_PASSWORD" exec mariadb -N -B -u "$MARIADB_USER" "$MARIADB_DATABASE" -e "SELECT CONCAT(\"users=\",COUNT(*)) FROM users UNION ALL SELECT CONCAT(\"roms=\",COUNT(*)) FROM roms UNION ALL SELECT CONCAT(\"saves=\",COUNT(*)) FROM saves UNION ALL SELECT CONCAT(\"states=\",COUNT(*)) FROM states UNION ALL SELECT CONCAT(\"client_tokens=\",COUNT(*)) FROM client_tokens UNION ALL SELECT CONCAT(\"devices=\",COUNT(*)) FROM devices"' \
    > "$OUTPUT/source-counts.txt"
python3 - "$STATE/broker/proposals.sqlite3" >> "$OUTPUT/source-counts.txt" <<'PY'
import sqlite3
import sys
with sqlite3.connect(sys.argv[1]) as database:
    print("proposals=" + str(database.execute("select count(*) from proposals").fetchone()[0]))
PY

sha256sum "/srv/aster-games/library/nes/Aster Infrastructure Test (World) (Homebrew).nes" \
    | awk '{print $1}' > "$OUTPUT/sampled-media.sha256"
find "$OUTPUT" -type f -exec chmod 0600 {} +
(
    cd "$OUTPUT"
    find . -maxdepth 1 -type f ! -name MANIFEST.sha256 -print0 \
        | sort -z | xargs -0 sha256sum > MANIFEST.sha256
)
chmod 0600 "$OUTPUT/MANIFEST.sha256"

trap - EXIT
restart_application
printf 'backup_complete=true files=%s\n' "$(find "$OUTPUT" -maxdepth 1 -type f | wc -l | tr -d ' ')"
