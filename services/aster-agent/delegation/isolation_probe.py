"""Read effective candidate configuration; no thread or inference methods.

Only emits allowlisted booleans/counts. Configuration acceptance is not proof
of effective tool isolation. Does not change user configuration or credentials.
"""
import argparse
import json
import shutil
import tempfile

from probe import MetadataClient

DISABLED = (
    "shell_tool", "unified_exec", "apps", "plugins", "hooks", "browser_use",
    "computer_use", "multi_agent", "code_mode", "code_mode_host", "memories",
    "image_generation", "view_image", "skill_search", "shell_snapshot",
)


class ConfigClient(MetadataClient):
    methods = MetadataClient.methods | {"config/read"}


def summarize(config):
    features = config.get("features") or {}
    servers = config.get("mcp_servers") or {}
    return {
        "disabled_flags_confirmed": [k for k in DISABLED if features.get(k) is False],
        "disabled_flags_unconfirmed": [k for k in DISABLED if features.get(k) is not False],
        "web_search_disabled": config.get("web_search") == "disabled",
        "read_only_requested": config.get("sandbox_mode") == "read-only",
        "enabled_mcp_count": sum(v.get("enabled", True) is not False
                                 for v in servers.values() if isinstance(v, dict)),
        "inherited_instruction_present": any(bool(config.get(k)) for k in
            ("instructions", "developer_instructions", "model_instructions_file")),
        "tool_isolation_proven": False,
        "inference": False,
    }


def disable_mcp_options(config):
    # Use an inline TOML table: CLI dotted-key overrides do not necessarily
    # implement TOML quoting for individual path segments.
    entries = [json.dumps(name) + "={enabled=false}"
               for name in (config.get("mcp_servers") or {})]
    return ["-c", "mcp_servers={" + ",".join(entries) + "}"] if entries else []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inspect-installed", action="store_true")
    args = parser.parse_args()
    if not args.inspect_installed:
        print(json.dumps({"status": "not_started", "inference": False}))
        return
    executable = shutil.which("codex")
    if not executable:
        raise SystemExit("Codex unavailable")
    options = []
    for flag in DISABLED:
        options.extend(["--disable", flag])
    options.extend(["-c", 'web_search="disabled"', "-c", 'sandbox_mode="read-only"'])
    with tempfile.TemporaryDirectory(prefix="aster-config-probe-") as cwd:
        client = ConfigClient(executable, options=options, cwd=cwd)
        try:
            client.call("initialize", {"clientInfo": {
                "name": "aster-isolation-preflight", "version": "0.1.0"}})
            client.send({"method": "initialized", "params": {}})
            result = client.call("config/read", {"includeLayers": False, "cwd": cwd})
        finally:
            client.close()
        initial_count = summarize(result["config"])["enabled_mcp_count"]
        options.extend(disable_mcp_options(result["config"]))
        del result
        # Re-read effective configuration in a new process; no disk mutation.
        client = ConfigClient(executable, options=options, cwd=cwd)
        try:
            client.call("initialize", {"clientInfo": {
                "name": "aster-isolation-preflight", "version": "0.1.0"}})
            client.send({"method": "initialized", "params": {}})
            result = client.call("config/read", {"includeLayers": False, "cwd": cwd})
            summary = summarize(result["config"])
            summary["initial_enabled_mcp_count"] = initial_count
            print(json.dumps(summary, sort_keys=True))
        finally:
            client.close()


if __name__ == "__main__":
    main()
