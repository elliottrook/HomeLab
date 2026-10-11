"""Send verified Fotosforfun releases through its forced-command SSH boundary."""

from __future__ import annotations

from pathlib import Path
import re
import subprocess
import tarfile

from model import ContentError
from release import verify_manifest


DEFAULT_HOST = "fotosforfun-deploy@192.168.20.36"
DEFAULT_KEY = Path("/var/lib/fotosforfun/keys/origin_deploy_ed25519")
DEFAULT_KNOWN_HOSTS = Path("/var/lib/fotosforfun/keys/origin_known_hosts")
RELEASE_ID = re.compile(r"fotosforfun-[0-9a-f]{12}-[0-9a-f]{12}")


def ssh_argv(command: list[str], host: str = DEFAULT_HOST, key: Path = DEFAULT_KEY,
             known_hosts: Path = DEFAULT_KNOWN_HOSTS) -> list[str]:
    return ["ssh", "-T", "-i", str(key), "-o", "BatchMode=yes",
            "-o", "IdentitiesOnly=yes", "-o", "StrictHostKeyChecking=yes",
            "-o", "ConnectTimeout=10", "-o", f"UserKnownHostsFile={known_hosts}",
            host, *command]


def validate(release_id: str) -> None:
    if not RELEASE_ID.fullmatch(release_id):
        raise ContentError("invalid Fotosforfun release id")


def stage(release: Path, release_id: str) -> None:
    validate(release_id)
    verify_manifest(release)
    process = subprocess.Popen(ssh_argv(["stage", release_id]), stdin=subprocess.PIPE)
    assert process.stdin is not None
    with tarfile.open(fileobj=process.stdin, mode="w|") as archive:
        for path in sorted(release.rglob("*")):
            if path.is_symlink():
                raise ContentError("release contains a symbolic link")
            if path.is_file():
                archive.add(path, arcname=path.relative_to(release).as_posix(), recursive=False)
    process.stdin.close()
    if process.wait():
        raise ContentError("origin rejected staged release")


def request(action: str, release_id: str, digest: str) -> None:
    if action not in {"activate", "rollback"} or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ContentError("invalid origin request")
    validate(release_id)
    subprocess.run(ssh_argv([action, release_id, digest]), check=True, timeout=30)
