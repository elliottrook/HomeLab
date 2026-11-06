"""Validate the inert fixed-runner installation result."""
import hashlib
import sa4_fixed_runner_inactive_install_plan_v1 as install
import sa4_single_file_repair_contract_v1 as contract
from nlu_threshold_policy import decode_unique_json
FIELDS={"schema","destination","after_sha256","owner","group","mode","link_count","regular_file","isolated_import","runtime_state_absent","runner_invoked","authority_touched","target_touched","service_actions","production_healthy","rollback_ready","automatic_routing"}
def validate(raw):
    value=decode_unique_json(raw)
    if (not isinstance(value,dict) or set(value)!=FIELDS or contract.canonical(value)!=raw or value["schema"]!="aster-sa4-fixed-runner-inactive-install-result.v1" or value["destination"]!=install.DESTINATION or value["after_sha256"]!=install.AFTER_SHA256 or (value["owner"],value["group"],value["mode"],value["link_count"],value["regular_file"]) != ("root","root","0644",1,True) or value["isolated_import"] is not True or value["runtime_state_absent"] is not True or value["runner_invoked"] is not False or value["authority_touched"] is not False or value["target_touched"] is not False or value["service_actions"]!=[] or value["production_healthy"] is not True or value["rollback_ready"] is not True or value["automatic_routing"]!="off"):
        raise ValueError("SA4 fixed-runner install result changed")
    return {"schema":"aster-sa4-fixed-runner-install-validation.v1","result_sha256":hashlib.sha256(raw).hexdigest(),"inactive":True,"effect_authorized":False}
