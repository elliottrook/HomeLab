#!/usr/bin/env python3
"""Bounded read-only Forgejo client through the existing AI-PAM broker."""
from __future__ import annotations

import argparse
import json
from pathlib import PurePosixPath

from bundle_runner import BrokerDenied, broker_call

TOOLS = frozenset({
    "get_repo", "list_branches", "get_file_content", "list_repo_contents",
    "get_repo_tree", "list_repo_commits",
})
PATH_TOOLS = frozenset({"get_file_content", "list_repo_contents"})


def payload(tool: str, *, path: str | None, ref: str, limit: int) -> dict[str, object]:
    if tool not in TOOLS:
        raise ValueError("read tool is not allowed")
    arguments: dict[str, object] = {"owner": "jason", "repo": "homelab"}
    if tool in PATH_TOOLS:
        if path is None:
            raise ValueError("path is required for this tool")
        parsed = PurePosixPath(path or ".")
        if parsed.is_absolute() or ".." in parsed.parts or len(path.encode()) > 512:
            raise ValueError("path is invalid")
        arguments["filePath"] = path
        arguments["ref"] = ref
    elif path is not None:
        raise ValueError("path is not accepted for this tool")
    if tool in {"get_repo_tree", "list_repo_commits"}:
        arguments["ref"] = ref
    if tool == "list_repo_commits":
        if not 1 <= limit <= 100:
            raise ValueError("limit is outside policy")
        arguments["limit"] = limit
    return {"tool": tool, "arguments": arguments}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("tool", choices=sorted(TOOLS))
    parser.add_argument("--broker-socket", required=True)
    parser.add_argument("--path")
    parser.add_argument("--ref", default="main")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    try:
        request_payload = payload(
            args.tool, path=args.path, ref=args.ref, limit=args.limit,
        )
        created = broker_call(args.broker_socket, {
            "method": "request.create", "capability": "forgejo.read.repository",
            "payload": request_payload, "ttl_seconds": 60,
            "display": {
                "reason": "Bounded Forgejo repository read",
                "target": "jason/homelab", "effect": args.tool,
                "rollback": "Read-only; no repository state changes",
            },
        })
        if created.get("status") != "approved" or not isinstance(created.get("request_id"), str):
            raise BrokerDenied("Green read request was not pre-authorized")
        result = broker_call(args.broker_socket, {
            "method": "request.consume", "request_id": created["request_id"],
            "payload": request_payload,
        })
    except (BrokerDenied, OSError, ValueError) as exc:
        raise SystemExit(f"DENIED {exc}") from None
    print(json.dumps(result.get("result"), sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
