"""Container-path <-> host-path translation.

Jellyfin reports item Paths using its own container bind-mount prefix
(e.g. /media/music/...). This tool runs directly on the TrueNAS host, so
every file-touching action needs the equivalent host path
(/mnt/Media/data/media/...).
"""
import os


class PathTranslationError(Exception):
    pass


class PathTranslator:
    def __init__(self, container_prefix, host_root):
        self.container_prefix = container_prefix.rstrip("/")
        self.host_root = host_root.rstrip("/")

    def to_host(self, container_path):
        if not container_path.startswith(self.container_prefix + "/"):
            raise PathTranslationError(
                f"path {container_path!r} does not start with expected "
                f"container prefix {self.container_prefix!r}"
            )
        rel = container_path[len(self.container_prefix) + 1:]
        return os.path.join(self.host_root, rel)
