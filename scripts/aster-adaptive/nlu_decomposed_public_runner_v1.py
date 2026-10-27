"""Public gate runner for decomposed semantic microtasks."""
from __future__ import annotations

import argparse, json, os, time, urllib.error, urllib.request
from pathlib import Path

import nlu_decomposed_microtasks_v1 as candidate
import nlu_whole_label_public_runner_v1 as common
from nlu_threshold_policy import decode_unique_json

ENDPOINT = common.ENDPOINT
FIXTURE_SHA256 = common.FIXTURE_SHA256
PER_CALL_TIMEOUT = 60
WALL_DEADLINE = 1200


def run(fixture_raw: bytes, token: str) -> dict:
    if common.sha256(fixture_raw) != FIXTURE_SHA256: raise ValueError("development fixture changed")
    fixture = decode_unique_json(fixture_raw)
    if not isinstance(fixture, dict) or len(fixture.get("cases", [])) != 24: raise ValueError("development fixture differs")
    if not isinstance(token, str) or not 16 <= len(token) <= 256: raise ValueError("credential boundary differs")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), common.NoRedirect())
    started = time.monotonic(); records = []
    for case in fixture["cases"]:
        one_started = time.monotonic(); answers = {}; failure = None
        for task in candidate.TASKS:
            remaining = WALL_DEADLINE - (time.monotonic() - started)
            if remaining <= 0: failure = "wall_deadline"; break
            request = urllib.request.Request(ENDPOINT, data=candidate.build_payload(case["text"], task), method="POST", headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"})
            try:
                with opener.open(request, timeout=min(PER_CALL_TIMEOUT, remaining)) as response:
                    raw=response.read(65_537); status=response.status
                if status != 200 or len(raw)>65_536: raise RuntimeError("engine boundary")
                body=decode_unique_json(raw)
                bounded=json.dumps({"choices":[{"message":body["choices"][0]["message"],"finish_reason":body["choices"][0]["finish_reason"]}]},sort_keys=True,separators=(",",":")).encode()
                answers[task]=candidate.parse_response(task,bounded)
            except (UnicodeError,json.JSONDecodeError,KeyError,TypeError,ValueError): failure="invalid_response"; break
            except (urllib.error.URLError,OSError,RuntimeError,TimeoutError): failure="engine_error"; break
        if failure:
            records.append({"id":case["id"],"valid":False,"latency_seconds":round(time.monotonic()-one_started,3),"failure":failure})
            if failure in {"wall_deadline","engine_error"}: break
        else:
            records.append({"id":case["id"],"valid":True,"latency_seconds":round(time.monotonic()-one_started,3),"interpretation":candidate.interpret(case["text"],answers)})
    return {"schema":"aster-nlu-decomposed-public-run.v1","candidate":"decomposed-microtasks-v1","model":candidate.MODEL,"fixture_sha256":FIXTURE_SHA256,"attempted":len(records),"valid":sum(r["valid"] for r in records),"elapsed_seconds":round(time.monotonic()-started,3),"records":records,"authority":"not-granted","automatic_routing":"off"}


def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("--fixture",type=Path,required=True); parser.add_argument("--key-file",type=Path,required=True); parser.add_argument("--output",type=Path,required=True); args=parser.parse_args()
    raw=args.fixture.read_bytes(); token=args.key_file.read_text().splitlines()[0].strip(); result=run(raw,token)
    fd=os.open(args.output,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,"w") as stream: json.dump(result,stream,sort_keys=True,separators=(",",":")); stream.write("\n")
    summary=common.summarize(raw,result); print(json.dumps(summary,sort_keys=True))
    return 0 if result["attempted"]==24 and result["valid"]==24 else 2


if __name__=="__main__": raise SystemExit(main())
