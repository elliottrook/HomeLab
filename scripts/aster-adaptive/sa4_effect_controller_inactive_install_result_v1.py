"""Validate the inert SA4 effect-controller installation result."""
from __future__ import annotations
import hashlib
import sa4_effect_controller_inactive_install_plan_v1 as install
import sa4_single_file_repair_contract_v1 as contract
from nlu_threshold_policy import decode_unique_json

PLAN_SHA256="f39e52a7be98c7cc19667d293f458c7729d1b9f431c9178e5a7bbef98fe2c286"

def validate(raw: bytes) -> dict[str, object]:
    value=decode_unique_json(raw)
    fields={"schema","plan_sha256","changes","isolated_imports","runtime_directories_absent","controller_invoked","signer_invoked","authority_touched","target_touched","service_actions","production_healthy","rollback_ready","automatic_routing"}
    if (not isinstance(value,dict) or set(value)!=fields or contract.canonical(value)!=raw
            or value["schema"]!="aster-sa4-effect-controller-inactive-install-result.v1"
            or value["plan_sha256"]!=PLAN_SHA256
            or value["isolated_imports"]!=[x.destination for x in install.CHANGES]
            or value["runtime_directories_absent"] is not True
            or value["controller_invoked"] is not False
            or value["signer_invoked"] is not False
            or value["authority_touched"] is not False
            or value["target_touched"] is not False
            or value["service_actions"]!=[]
            or value["production_healthy"] is not True
            or value["rollback_ready"] is not True
            or value["automatic_routing"]!="off"):
        raise ValueError("SA4 effect-controller install result changed")
    if not isinstance(value["changes"],list) or len(value["changes"])!=3:
        raise ValueError("SA4 effect-controller install rows changed")
    for row,expected in zip(value["changes"],install.CHANGES):
        if (not isinstance(row,dict) or set(row)!={"host","destination","after_sha256","owner","group","mode","link_count","regular_file"}
                or row["host"]!=expected.host or row["destination"]!=expected.destination
                or row["after_sha256"]!=expected.after_sha256
                or (row["owner"],row["group"],row["mode"],row["link_count"],row["regular_file"]) != ("root","root","0644",1,True)):
            raise ValueError("SA4 effect-controller install row changed")
    return {"schema":"aster-sa4-effect-controller-install-validation.v1","result_sha256":hashlib.sha256(raw).hexdigest(),"changes_validated":3,"inactive":True,"effect_authorized":False,"automatic_routing":"off"}
