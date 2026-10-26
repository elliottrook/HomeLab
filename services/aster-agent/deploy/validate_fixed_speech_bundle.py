#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = Path(__file__).with_name("fixed-speech-bundle-manifest.json")
EXPECTED_TARGETS = {
    "/opt/aster-agent/diagnostic_catalogue_v3.py",
    "/opt/aster-agent/speech_catalogue_incident_adapter.py",
    "/opt/aster-agent/fixed_speech_response.py",
    "/opt/aster-agent/fixed_speech_capability.py",
    "/opt/aster-agent/fixed_speech_gateway.py",
    "/opt/aster-agent/fixed_speech_caller.py",
    "/etc/systemd/system/aster-fixed-speech-caller.service",
    "/etc/systemd/system/aster-fixed-speech-gateway.service",
    "/usr/lib/sysusers.d/aster-fixed-speech.conf",
}
EXCLUDED = {"service-start","service-enable","broker-restart","database-enrollment","capability-grant","live-read","model-route","model-call","automatic-routing","repair","git-push"}

def validate(path: Path = MANIFEST) -> None:
    value=json.loads(path.read_text())
    if set(value)!={"schema","candidate","source_commit","activation","entries","dependencies","units","excluded"} or value["schema"]!=1 or value["activation"]!="inactive-additive-only": raise ValueError("shape")
    if len(value["source_commit"])!=40 or set(value["excluded"])!=EXCLUDED: raise ValueError("boundary")
    if value["units"]!={"must_remain_disabled_inactive":["aster-fixed-speech-caller.service","aster-fixed-speech-gateway.service"]}: raise ValueError("units")
    if value["dependencies"]!=[{"target":"/opt/aster-agent/sysadmin_investigation.py","sha256":"bfd5e9675b4a7ef06aa0ddb28e7c9b5fda2076a86957cd5474a75ccbd50ee6fe"}]: raise ValueError("dependency")
    seen=set()
    for item in value["entries"]:
        if set(item)!={"source","target","sha256","predecessor","owner","group","mode","rollback"}: raise ValueError("entry")
        if item["target"] in seen or item["target"] not in EXPECTED_TARGETS: raise ValueError("target")
        seen.add(item["target"])
        if (item["predecessor"],item["owner"],item["group"],item["mode"],item["rollback"])!=("absent","root","root","0644","remove"): raise ValueError("effect")
        source=(ROOT/item["source"]).resolve()
        if ROOT.resolve() not in source.parents or not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest()!=item["sha256"]: raise ValueError("source")
    if seen!=EXPECTED_TARGETS: raise ValueError("missing")

if __name__=="__main__":
    validate(); print("fixed speech bundle: PASS")
