"""Idempotently publish the private production Aster alias in Pi-hole v6."""

import argparse
import os
import re
import shutil
from pathlib import Path


ENTRY = "192.168.20.37 aster-voice.home.internal"

parser = argparse.ArgumentParser()
parser.add_argument("--apply", action="store_true")
parser.add_argument("--config", type=Path, default=Path("/etc/pihole/pihole.toml"))
parser.add_argument("--backup", type=Path, required=True)
args = parser.parse_args()

raw = args.config.read_text(encoding="utf-8")
dns_start = raw.find("[dns]")
if dns_start < 0:
    raise RuntimeError("Pi-hole [dns] section is missing")
match = re.search(r"(?m)^(\s*hosts\s*=\s*\[\n)(.*?)(^\s*\])", raw[dns_start:], re.S)
if not match:
    raise RuntimeError("Pi-hole dns.hosts array is missing")
body = match.group(2)
entries = re.findall(r'^\s*"([^"\n]+)"\s*,?\s*$', body, re.M)
if not entries:
    raise RuntimeError("Pi-hole dns.hosts array is unexpectedly empty")
matches = [item for item in entries if item.split()[-1] == "aster-voice.home.internal"]
if matches and matches != [ENTRY]:
    raise RuntimeError("existing production Aster DNS record is inconsistent")

print({"entry": ENTRY, "present": bool(matches), "apply": args.apply})
if not args.apply:
    print("aster-voice-private-dns=" + ("present" if matches else "pending"))
    raise SystemExit(0)

if not matches:
    if args.backup.exists():
        raise RuntimeError(f"refusing to replace backup: {args.backup}")
    shutil.copy2(args.config, args.backup)
    args.backup.chmod(0o600)
    replacement = match.group(1) + "".join(
        f'    "{item}",\n' for item in entries + [ENTRY]
    ) + match.group(3)
    absolute_start = dns_start + match.start()
    absolute_end = dns_start + match.end()
    candidate = raw[:absolute_start] + replacement + raw[absolute_end:]
    if candidate.count("aster-voice.home.internal") != 1:
        raise RuntimeError("candidate production Aster record is not unique")
    temporary = args.config.with_name(args.config.name + ".aster-voice-prod-candidate")
    metadata = args.config.stat()
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write(candidate)
        stream.flush()
        os.fsync(stream.fileno())
        os.fchmod(stream.fileno(), metadata.st_mode & 0o777)
        os.fchown(stream.fileno(), metadata.st_uid, metadata.st_gid)
    os.replace(temporary, args.config)

verified = args.config.read_text(encoding="utf-8")
if verified.count("aster-voice.home.internal") != 1:
    raise RuntimeError("production Aster DNS record did not verify uniquely")
print("aster-voice-private-dns=present")
