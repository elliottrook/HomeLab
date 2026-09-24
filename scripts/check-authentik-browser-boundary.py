#!/usr/bin/env python3
"""Read-only LAN checks. Requires curl/dig; never uses credentials or logs bodies.

Run from an approved management client, not NPM itself. HTTPS is pinned to NPM
with certificate verification; each DNS authority is checked independently.
Does not establish successful login, logout, recovery, or client compatibility.
"""
import concurrent.futures
import json
import shutil
import subprocess
import sys
from urllib.parse import urlsplit

NPM = "192.168.50.23"
RESOLVERS = ("192.168.50.1", "192.168.20.20", "192.168.20.40")
SERVICES = """home monitoring metrics sonarr radarr lidarr prowlarr sabnzbd
portainer dns1 dns2 proxy git logs homarr code dockge files netbox audiobooks
books proxmox""".split()
NATIVE_ROOTS = {"metrics", "portainer", "git", "audiobooks"}
BACKENDS = {
    "logs": "192.168.20.40:8888", "homarr": "192.168.20.20:7575",
    "code": "192.168.20.20:8443", "dockge": "192.168.20.40:31014",
    "files": "192.168.20.40:30051", "netbox": "192.168.20.32:8000",
}


def run(args):
    return subprocess.run(args, capture_output=True, text=True, timeout=15)


def dns(name, resolver):
    result = run(["dig", "@" + resolver, name + ".elliottrook.com", "A",
                  "+short", "+time=2", "+tries=1"])
    return result.returncode == 0 and result.stdout.strip() == NPM


def http(name, backend=False, spoof=False):
    host = name + ".elliottrook.com"
    url = "http://" + BACKENDS[name] if backend else "https://" + host
    args = ["curl", "--silent", "--show-error", "--noproxy", "*",
            "--connect-timeout", "4", "--max-time", "10", "--output",
            "/dev/null", "--write-out", "%{http_code} %{redirect_url}"]
    if not backend:
        args += ["--resolve", host + ":443:" + NPM]
    if spoof:
        args += ["--header", "X-Homelab-Authentik-User: jason",
                 "--header", "X-Authentik-Username: jason",
                 "--header", "X-Forwarded-For: " + NPM]
    result = run(args + [url])
    fields = result.stdout.split(" ", 1)
    if result.returncode != 0 or len(fields) != 2:
        return False
    status, location = fields
    target = urlsplit(location)
    if backend:
        return status == "302" and target.scheme == "https" and target.hostname == host
    if name in NATIVE_ROOTS:
        return status == "200"
    if status != "302":
        return False
    if name == "proxmox":
        return target.hostname == host and target.path == "/sso"
    if name == "monitoring":
        return target.hostname == host and target.path in ("/login", "/login/generic_oauth")
    if name == "books":
        return target.hostname in (host, "auth.elliottrook.com")
    return target.hostname in (host, "auth.elliottrook.com") and (
        target.path.startswith("/outpost.goauthentik.io/") or
        target.path.startswith("/application/o/") or
        target.path.startswith("/if/flow/"))


def main():
    if not all(shutil.which(command) for command in ("curl", "dig")):
        print("curl and dig are required", file=sys.stderr)
        return 2
    jobs = [(f"dns:{n}:{r}", dns, (n, r)) for n in SERVICES for r in RESOLVERS]
    jobs += [(f"https:{n}", http, (n,)) for n in SERVICES]
    jobs += [(f"direct:{n}:{mode}", http, (n, True, spoof))
             for n in BACKENDS for mode, spoof in (("plain", False), ("spoof", True))]

    def check(job):
        label, function, arguments = job
        try:
            return {"check": label, "passed": function(*arguments)}
        except (OSError, subprocess.TimeoutExpired, ValueError):
            return {"check": label, "passed": False}

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(check, jobs))
    for result in results:
        print(json.dumps(result))
    passed = sum(result["passed"] for result in results)
    print(json.dumps({"passed": passed, "total": len(results),
                      "scope": "DNS, TLS routing, unauthenticated boundary only"}))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
