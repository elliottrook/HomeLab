"""Fixed, narrow nftables helper for the temporary A1 backend claim."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

FAMILY = "inet"
TABLE = "filter"
CHAIN = "input"
SOURCE = "192.168.70.10"
PORT = "11435"
COMMENT = "aster-a1-exclusive-v1"
CHECKPOINT = Path("/var/lib/local-ai-lab/application-b60/llama-ingress-policy.checkpoint")


def parse_chain(payload: str) -> tuple[dict, list[dict]]:
    value = json.loads(payload)
    objects = value.get("nftables")
    if not isinstance(objects, list):
        raise ValueError("invalid nft JSON")
    chains = [item["chain"] for item in objects if isinstance(item, dict) and "chain" in item]
    rules = [item["rule"] for item in objects if isinstance(item, dict) and "rule" in item]
    if len(chains) != 1 or any(rule.get("chain") != CHAIN for rule in rules):
        raise ValueError("unexpected nft chain response")
    chain = chains[0]
    if (chain.get("family"), chain.get("table"), chain.get("name")) != (FAMILY, TABLE, CHAIN):
        raise ValueError("unexpected nft chain identity")
    return chain, rules


def baseline(chain: dict, rules: list[dict]) -> bool:
    expected = {"family": FAMILY, "table": TABLE, "name": CHAIN,
                "handle": 1, "type": "filter", "hook": "input",
                "prio": 0, "policy": "accept"}
    return chain == expected and rules == []


def tagged_rules(rules: list[dict]) -> list[dict]:
    return [rule for rule in rules if rule.get("comment") == COMMENT]


def expected_rule(rule: dict) -> bool:
    if (rule.get("family"), rule.get("table"), rule.get("chain"), rule.get("comment")) != (FAMILY, TABLE, CHAIN, COMMENT):
        return False
    expressions = rule.get("expr")
    if not isinstance(expressions, list) or len(expressions) != 4:
        return False
    matches = []
    has_counter = has_drop = False
    for expression in expressions:
        if "match" in expression:
            matches.append(expression["match"])
        elif "counter" in expression and (expression["counter"] == {} or
                                             set(expression["counter"]) <= {"packets", "bytes"}):
            has_counter = True
        elif "drop" in expression and expression["drop"] in (None, {}):
            has_drop = True
        else:
            return False
    if not (has_counter and has_drop and len(matches) == 2):
        return False
    required = {("saddr", "192.168.70.10", "!=", "ip"), ("dport", 11435, "==", "tcp")}
    actual = set()
    for match in matches:
        left = match.get("left", {}).get("payload", {})
        actual.add((left.get("field"), match.get("right"), match.get("op"), left.get("protocol")))
    return actual == required


def _nft_json() -> str:
    result = subprocess.run(["/usr/sbin/nft", "-j", "-s", "list", "chain", FAMILY, TABLE, CHAIN], check=True, capture_output=True, text=True)
    return result.stdout


def _atomic_checkpoint(payload: str) -> None:
    CHECKPOINT.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if CHECKPOINT.exists():
        if CHECKPOINT.read_text(encoding="utf-8") != payload:
            raise ValueError("ingress checkpoint already exists with different content")
        return
    fd, name = tempfile.mkstemp(prefix=".ingress.", dir=CHECKPOINT.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, CHECKPOINT)
        directory = os.open(CHECKPOINT.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except Exception:
        try:
            os.unlink(name)
        except FileNotFoundError:
            pass
        raise


def apply() -> None:
    if os.geteuid() != 0:
        raise PermissionError("ingress policy helper requires root")
    chain, rules = parse_chain(_nft_json())
    if not baseline(chain, rules):
        raise ValueError("LXC110 input chain is not the observed empty baseline")
    _atomic_checkpoint(json.dumps(chain, sort_keys=True, separators=(",", ":")) + "\n")
    subprocess.run(["/usr/sbin/nft", "add", "rule", FAMILY, TABLE, CHAIN, "ip", "saddr", "!=", SOURCE, "tcp", "dport", PORT, "counter", "drop", "comment", COMMENT], check=True)
    chain_after, rules_after = parse_chain(_nft_json())
    if chain_after != chain or len(tagged_rules(rules_after)) != 1 or len(rules_after) != 1 or not expected_rule(rules_after[0]):
        raise ValueError("A1 ingress rule was not the only added rule")


def restore() -> None:
    if os.geteuid() != 0:
        raise PermissionError("ingress policy helper requires root")
    if not CHECKPOINT.exists():
        raise ValueError("ingress checkpoint is missing")
    checkpoint = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
    chain, rules = parse_chain(_nft_json())
    if chain != checkpoint or not baseline(checkpoint, []) or len(tagged_rules(rules)) != 1 or len(rules) != 1 or not expected_rule(rules[0]):
        raise ValueError("ingress chain drift or uncertain A1 rule state")
    subprocess.run(["/usr/sbin/nft", "delete", "rule", FAMILY, TABLE, CHAIN, "handle", str(tagged_rules(rules)[0]["handle"])], check=True)
    chain_after, rules_after = parse_chain(_nft_json())
    if not baseline(chain_after, rules_after):
        raise ValueError("ingress policy did not restore to the checkpoint")


if __name__ == "__main__":
    if sys.argv[1:] == ["apply"]:
        apply()
    elif sys.argv[1:] == ["restore"]:
        restore()
    else:
        raise SystemExit("usage: a1_ingress_policy.py apply|restore")
