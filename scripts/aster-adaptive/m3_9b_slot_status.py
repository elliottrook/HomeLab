"""Read only allowlisted llama.cpp occupancy metrics as its service account."""
import json
from pathlib import Path
from urllib.request import Request, urlopen

key = Path("/etc/aster-llama-api-keys").read_text().splitlines()[0].strip()
if not key:
    raise SystemExit("local service credential unavailable")
req = Request("http://192.168.70.12:11435/metrics",
              headers={"Authorization": "Bearer " + key})
with urlopen(req, timeout=5) as response:
    metrics = response.read(131072).decode()
names = {
    "llamacpp:requests_processing", "llamacpp:requests_deferred",
    "llamacpp:prompt_tokens_total", "llamacpp:tokens_predicted_total",
}
result = {}
for line in metrics.splitlines():
    if line.startswith("#") or " " not in line:
        continue
    name, value = line.split(" ", 1)
    if name in names:
        result[name] = float(value.strip())
print(json.dumps(result, sort_keys=True))
