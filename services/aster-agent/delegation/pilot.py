"""One fictional subscription turn. Default is metadata-only preparation.

Execution requires --run and a prepared manifest fingerprint. This is an
operator pilot, not a network service or permission broker. The operator must
obtain the project's connected-test approval before invoking --run.
"""
import argparse
import hashlib
import json
import shutil
import tempfile
import time
from pathlib import Path

from isolation_probe import ConfigClient, DISABLED, disable_mcp_options, summarize
from session import Session
from store import DispatchStore
from transport import Transport

FIXTURE = (
    "Fictional exercise only. Service Orion returned HTTP 503 once. A later health "
    "check returned HTTP 200. No logs, dependency checks or user-path checks have "
    "been performed. Explain what is known, what remains unknown, and the next "
    "read-only checks. Do not claim you inspected or repaired anything. Use only "
    "this supplied information. Do not use tools."
)


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def options():
    args = []
    for flag in DISABLED:
        args += ["--disable", flag]
    return args + ["-c", 'web_search="disabled"', "-c", 'sandbox_mode="read-only"',
                   "-c", 'model_provider="openai"']


def initialize(client):
    client.call("initialize", {"clientInfo": {"name": "aster-d2-pilot", "version": "0.1.0"}})
    client.send({"method": "initialized", "params": {}})


def manifest(config, account, models):
    check = summarize(config)
    if (check["disabled_flags_unconfirmed"] or check["enabled_mcp_count"] or
            check["inherited_instruction_present"] or not check["read_only_requested"] or
            not check["web_search_disabled"]):
        raise ValueError("Restriction preflight failed")
    if (account.get("account") or {}).get("type") != "chatgpt":
        raise ValueError("ChatGPT authentication required")
    if config.get("model_provider") != "openai":
        raise ValueError("Only the native OpenAI provider is eligible")
    # Do not accept an overridden endpoint or custom provider under this name.
    custom = (config.get("model_providers") or {}).get("openai")
    if custom:
        raise ValueError("Custom OpenAI provider requires separate review")
    expected_endpoints = {
        "openai_base_url": {"https://api.openai.com/v1"},
        "chatgpt_base_url": {"https://chatgpt.com/backend-api", "https://chatgpt.com/backend-api/codex"},
    }
    for key, allowed in expected_endpoints.items():
        value = config.get(key)
        if value and value.rstrip("/") not in allowed:
            raise ValueError("Custom endpoint requires separate review")
    model = config.get("model")
    if model not in {m.get("model") for m in models.get("data", [])}:
        raise ValueError("Configured model absent from catalogue")
    sources = {name: hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest()
               for name in ("pilot.py", "transport.py", "session.py", "store.py",
                            "contract.py", "probe.py", "isolation_probe.py")}
    executable = shutil.which("codex")
    binary_hash = hashlib.sha256(Path(executable).read_bytes()).hexdigest() if executable else None
    return {"fixture": FIXTURE, "model": model, "source_hashes": sources,
            "codex_binary_sha256": binary_hash,
            "reasoning_effort": config.get("model_reasoning_effort"),
            "provider": "openai", "auth": "chatgpt", "max_turns": 1,
            "deadline_seconds": 180, "automatic_retry": False,
            "disabled_features": list(DISABLED), "enabled_mcp_count": 0,
            "sandbox": "read-only", "web_search": "disabled"}


def execute(client, cwd, prepared, output_dir):
    # Exclusive creation makes accidental invocation with the same destination
    # fail before thread or turn creation. No overwrite/retry path is provided.
    output_dir.mkdir(mode=0o700)
    (output_dir / "manifest.json").write_text(json.dumps(prepared, indent=2)+"\n")
    store = DispatchStore(output_dir / "jobs.sqlite")
    session = None
    started = time.monotonic()
    result = {"state": "not_dispatched", "answer": "", "automatic_retry": False}
    def event(message):
        return session.receive(message) if session else None
    transport = Transport(client.proc.stdout, client.proc.stdin,
                          {"thread/start", "turn/start", "turn/interrupt"}, event)
    transport.serial, transport.buffer = client.serial, client.buffer
    try:
        created = transport.call("thread/start", {
            "cwd": cwd, "model": prepared["model"], "modelProvider": "openai",
            "sandbox": "read-only", "ephemeral": False,
            "approvalPolicy": "on-request", "approvalsReviewer": "user"})
        tid = created["thread"]["id"]
        session = Session(store, "orion-d2", tid)
        request = session.prepare(FIXTURE)
        if prepared["reasoning_effort"]:
            request["params"]["effort"] = prepared["reasoning_effort"]
        response = transport.call(request["method"], request["params"])
        session.acknowledge(response["turn"]["id"])
        deadline = started + prepared["deadline_seconds"]
        while session.state in {"running", "cancel_requested"}:
            try:
                message = transport.read(deadline)
            except TimeoutError:
                interrupt = session.cancel()
                if interrupt:
                    transport.call(interrupt["method"], interrupt["params"], timeout=5)
                session.disconnect()
                break
            reply = session.receive(message)
            if reply:
                transport.send(reply, deadline)
        result.update(state=session.state, answer=session.answer,
                      failure_class=session.failure_class)
    except Exception:
        if session:
            session.disconnect()
        result.update(state="unknown" if session else "not_dispatched",
                      answer="", error="Pilot stopped; reconcile before any retry")
    finally:
        result["elapsed_seconds"] = round(time.monotonic()-started, 3)
        (output_dir / "result.json").write_text(json.dumps(result, indent=2)+"\n")
        transport.close(); store.close()
    return {"state": result["state"], "elapsed_seconds": result["elapsed_seconds"],
            "answer_available": bool(result["answer"]), "result_directory": str(output_dir)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--manifest-sha256")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    if args.run and (not args.manifest_sha256 or not args.output_dir or not args.output_dir.is_absolute()):
        raise SystemExit("Execution requires reviewed manifest fingerprint and absolute fresh output directory")
    with tempfile.TemporaryDirectory(prefix="aster-d2-work-") as cwd:
        opts = options()
        client = ConfigClient(shutil.which("codex"), options=opts, cwd=cwd)
        try:
            initialize(client)
            cfg = client.call("config/read", {"includeLayers": False, "cwd": cwd})["config"]
        finally:
            client.close()
        opts += disable_mcp_options(cfg)
        client = ConfigClient(shutil.which("codex"), options=opts, cwd=cwd)
        try:
            initialize(client)
            cfg = client.call("config/read", {"includeLayers": False, "cwd": cwd})["config"]
            account = client.call("account/read", {"refreshToken": False})
            models = client.call("model/list", {"limit": 100, "includeHidden": False})
            prepared = manifest(cfg, account, models)
            digest = fingerprint(prepared)
            if args.run:
                if digest != args.manifest_sha256:
                    raise ValueError("Prepared manifest changed; do not dispatch")
                print(json.dumps(execute(client, cwd, prepared, args.output_dir)))
            else:
                print(json.dumps({"manifest": prepared, "manifest_sha256": digest, "inference": False}, indent=2))
        finally:
            client.close()


if __name__ == "__main__":
    main()
