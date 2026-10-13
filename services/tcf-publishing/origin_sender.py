"""Send verified static releases through the origin's forced-command SSH API."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import sys
import tarfile

from content import ContentError, SITES
from release import verify_manifest


DEFAULT_HOST = "tcf-deploy@192.168.20.36"
DEFAULT_KEY = Path("/var/lib/tcf-workflow/keys/origin_deploy_ed25519")
DEFAULT_KNOWN_HOSTS = Path("/var/lib/tcf-workflow/keys/origin_known_hosts")
RELEASE_ID = re.compile(r"(?:contrast|closet)-e[1-9][0-9]*-[0-9a-f]{12}")


def validate(site: str, release_id: str) -> None:
    if site not in SITES or not RELEASE_ID.fullmatch(release_id) or not release_id.startswith(site + "-"):
        raise ContentError("invalid site or release id")


def ssh_argv(command: list[str], host: str, key: Path, known_hosts: Path) -> list[str]:
    return [
        "ssh", "-T", "-i", str(key),
        "-o", "BatchMode=yes",
        "-o", "IdentitiesOnly=yes",
        "-o", "StrictHostKeyChecking=yes",
        "-o", "ConnectTimeout=10",
        "-o", f"UserKnownHostsFile={known_hosts}",
        host, *command,
    ]


def stage(release: Path, site: str, release_id: str, *, host: str = DEFAULT_HOST,
          key: Path = DEFAULT_KEY, known_hosts: Path = DEFAULT_KNOWN_HOSTS) -> subprocess.CompletedProcess:
    validate(site, release_id)
    verify_manifest(release)
    process = subprocess.Popen(
        ssh_argv(["stage", site, release_id], host, key, known_hosts),
        stdin=subprocess.PIPE,
    )
    assert process.stdin is not None
    try:
        with tarfile.open(fileobj=process.stdin, mode="w|") as archive:
            for path in sorted(release.rglob("*")):
                if path.is_symlink() or not path.is_file():
                    if path.is_symlink():
                        raise ContentError("release contains a symbolic link")
                    continue
                archive.add(path, arcname=path.relative_to(release).as_posix(), recursive=False)
    except BaseException:
        process.stdin.close()
        process.wait()
        raise
    process.stdin.close()
    returncode = process.wait()
    if returncode:
        raise subprocess.CalledProcessError(returncode, process.args)
    return subprocess.CompletedProcess(process.args, returncode)


def status(*, host: str = DEFAULT_HOST, key: Path = DEFAULT_KEY,
           known_hosts: Path = DEFAULT_KNOWN_HOSTS) -> dict:
    result = subprocess.run(
        ssh_argv(["status"], host, key, known_hosts),
        check=True, capture_output=True, text=True, timeout=30,
    )
    value = __import__("json").loads(result.stdout)
    if not isinstance(value, dict):
        raise ContentError("origin returned invalid status")
    return value


def request(action: str, site: str, release_id: str, digest: str, *, host: str = DEFAULT_HOST,
            key: Path = DEFAULT_KEY, known_hosts: Path = DEFAULT_KNOWN_HOSTS) -> subprocess.CompletedProcess:
    if action not in {"activate", "rollback"} or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise ContentError("invalid origin request")
    validate(site, release_id)
    return subprocess.run(
        ssh_argv([action, site, release_id, digest], host, key, known_hosts),
        check=True, timeout=30,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("stage", "activate", "rollback"))
    parser.add_argument("site", choices=tuple(sorted(SITES)))
    parser.add_argument("release_id")
    parser.add_argument("value", help="release directory for stage; manifest digest otherwise")
    arguments = parser.parse_args()
    if arguments.action == "stage":
        stage(Path(arguments.value), arguments.site, arguments.release_id)
    else:
        request(arguments.action, arguments.site, arguments.release_id, arguments.value)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ContentError, OSError, subprocess.SubprocessError, tarfile.TarError) as error:
        print(f"origin request failed: {error}", file=sys.stderr)
        raise SystemExit(2)
