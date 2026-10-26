"""Read-only fixed HA report check. Never prints/saves a payload or publishes it."""
from datetime import datetime, timezone
import json
from pathlib import Path
import shlex
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from home_dashboard_model import TEMPERATURES, WEATHER
from home_delivery import SOURCE_KEYS, decode_guest_reply, prepare

SOURCE = '/mnt/data/supervisor/share/aster-home-registry/latest.json'


def source_filter():
    """Reviewed source-local boundary: unknown/raw attributes never leave HA."""
    keys = json.dumps(sorted(SOURCE_KEYS))
    temps, weather = json.dumps(sorted(TEMPERATURES)), json.dumps(sorted(WEATHER))
    return r'''
def exact($allowed): type == "object" and (keys == ($allowed|sort));
def temperature: (type == "object") and
  (.unit == "°C" or .unit == "°F") and (.value|type == "number") and
  (if .unit == "°C" then .value >= -50 and .value <= 60
   else .value >= -58 and .value <= 140 end);
def distinct: ([.[].alias]|length) == ([.[].alias]|unique|length);
select(exact(KEYS) and .schema_version == 3 and .snapshot_id == "ha-home-pilot-v3") |
select(.rooms == [] and .entities == [] and .timers == [] and .media_providers == []) |
select((.lights|type == "array" and length <= 1) and
  all(.lights[]; exact(["alias","state"]) and .alias == "laundry lights" and
    (.state == "on" or .state == "off"))) |
select((.temperatures|type == "array" and length <= 3 and distinct) and
  all(.temperatures[]; exact(["alias","value","unit"]) and
    (.alias as $a | TEMPS | index($a) != null) and temperature)) |
select((.weather|type == "array" and length <= 1) and
  all(.weather[];
    (exact(["alias","condition","temperature","unit"]) or
      exact(["alias","condition","temperature","unit","humidity"])) and
    .alias == "home weather" and (.condition as $c | WEATHER | index($c) != null) and
    ({unit:.unit,value:.temperature}|temperature) and
    ((has("humidity")|not) or (.humidity|type == "number" and . >= 0 and . <= 100))))
'''.replace('KEYS', keys).replace('TEMPS', temps).replace('WEATHER', weather).replace('°', r'\u00b0')


def source_command():
    # No file writes, eval, credentials, services, retries or arbitrary paths.
    script = '''set -eu
set -o pipefail
p=SOURCE
test -f "$p" && test ! -L "$p" && test ! -L "${p%/*}"
before=$(stat -c '%d|%i|%s|%Y|%Z|%a|%h|%y|%z' "$p")
size=$(stat -c '%s' "$p")
test "$size" -gt 0 && test "$size" -le 262144
snapshot=$(head -c 262145 "$p" | jq -ace FILTER)
after=$(stat -c '%d|%i|%s|%Y|%Z|%a|%h|%y|%z' "$p")
test "$before" = "$after"
jq -acn --arg before "$before" --arg after "$after" --argjson snapshot "$snapshot" \
 '{capture_version:1,before:$before,after:$after,snapshot:$snapshot}'
'''.replace('SOURCE', shlex.quote(SOURCE)).replace('FILTER', shlex.quote(source_filter()))
    return shlex.join(['qm', 'guest', 'exec', '103', '--', 'sh', '-c', script])


def check_source():
    reply = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5',
                            'proxmox', source_command()], stdout=subprocess.PIPE,
                           stderr=subprocess.DEVNULL, timeout=25, check=True)
    capture = decode_guest_reply(reply.stdout)
    candidate = prepare(capture, datetime.now(timezone.utc))
    return dict(checked=True, source_state='fresh',
                source_updated_at=candidate.source_updated_at,
                counts=dict(zip(('lights', 'temperatures', 'weather'), candidate.counts)),
                payload_bytes=len(candidate.encoded), published=False,
                camera_requests=0, hp_changed=False)


def main():
    if len(sys.argv) != 1:
        print(json.dumps(dict(checked=False, code='home-check-no-arguments')))
        return 2
    try:
        print(json.dumps(check_source(), sort_keys=True))
        return 0
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        code = str(error) if isinstance(error, ValueError) else 'home-check-transport-failed'
        print(json.dumps(dict(checked=False, code=code, published=False)))
        return 1


if __name__ == '__main__':
    sys.exit(main())
