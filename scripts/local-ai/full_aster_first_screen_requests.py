"""Fixed two-request guest workload for the full-Aster compatibility screen."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time
import urllib.error
import urllib.request


ENDPOINT = "http://192.168.70.12:11435/v1/chat/completions"
KEY_FILE = Path("/etc/aster-llama-api-keys")
TIMEOUT = 60
PROMPTS = (
    "Fictional compatibility check. Return only the final answer: what is 17 plus 25?",
    "Fictional home diagnosis. A motion sensor reports occupied while its battery is missing and no timestamp is supplied. State the ambiguity and one safe read-only next check in two short sentences.",
)


class RequestError(RuntimeError):
    pass


def _key(path: Path = KEY_FILE) -> str:
    values = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()
              if line.strip()]
    if not 1 <= len(values) <= 16 or any(len(value) < 16 for value in values):
        raise RequestError("API key file is not the bounded line-key form")
    return values[0]


def payload(prompt: str) -> bytes:
    if prompt not in PROMPTS:
        raise RequestError("request prompt is not fixed")
    return json.dumps({
        "model": "aster-qwen36-35b-first-screen",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 256,
        "stream": False,
    }, sort_keys=True, separators=(",", ":")).encode()


def run(*, opener=urllib.request.urlopen, key_reader=_key,
        monotonic=time.monotonic) -> dict[str, object]:
    key = key_reader()
    rows = []
    for index, prompt in enumerate(PROMPTS, 1):
        request = urllib.request.Request(
            ENDPOINT, data=payload(prompt), method="POST",
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/json"})
        started = monotonic()
        try:
            with opener(request, timeout=TIMEOUT) as response:
                raw = response.read(1024 * 1024 + 1)
                status = int(response.status)
        except (OSError, urllib.error.URLError) as error:
            raise RequestError(f"request {index} transport failed") from error
        elapsed = round((monotonic() - started) * 1000)
        if status != 200 or len(raw) > 1024 * 1024:
            raise RequestError(f"request {index} HTTP result is invalid")
        try:
            value = json.loads(raw)
            choice = value["choices"][0]
            message = choice["message"]
            content = message["content"]
        except (UnicodeError, json.JSONDecodeError, KeyError, IndexError, TypeError) as error:
            raise RequestError(f"request {index} response is malformed") from error
        if (not isinstance(content, str) or not content.strip()
                or choice.get("finish_reason") != "stop"):
            raise RequestError(f"request {index} response is empty or truncated")
        rows.append({"request": index, "http_status": status,
                     "elapsed_ms": elapsed, "finish_reason": "stop",
                     "content_chars": len(content),
                     "reasoning_field_present": bool(message.get("reasoning_content"))})
    return {"schema": "aster-full-path-first-screen-result.v1",
            "state": "complete", "requests": rows,
            "request_count": 2, "retries": 0,
            "answer_content_retained": False,
            "hidden_reasoning_retained": False}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-authorized", action="store_true")
    args = parser.parse_args(argv)
    if not args.run_authorized:
        print(json.dumps({"state": "disabled", "requests": 0}, sort_keys=True))
        return 0
    try:
        result = run()
    except RequestError:
        print(json.dumps({"state": "failed", "requests": 0}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
