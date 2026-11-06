"""Source-only bridge to the exact peer-owned frozen benchmark contract.

This inspects public metadata, not owner-private cases/reviews or live evidence.
An owner-frozen document never becomes a launch, sampling waiver or acceptance.
"""
import hashlib,json,types
from pathlib import Path
ROOT=Path(__file__).resolve().parent/'peer-contract-20261105'
CONTRACT_SHA='023939fd25e61e47af9418387ee6fe82163fac394511472a8bf64eaaab40382c'
VALIDATOR_SHA='757dd3631f68555773446c23eea25d288a8d47e55ac916d08714097f87aa47f5'
MIN_OBSERVATIONS_PER_ACCEPTANCE_CLASS=100
MIN_INDEPENDENT_SESSIONS=2

def inspect_contract(root=ROOT):
    root=Path(root)
    source=(root/'full_aster_benchmark_contract_v1.py').read_bytes()
    raw=(root/'contract.json').read_bytes()
    if hashlib.sha256(source).hexdigest()!=VALIDATOR_SHA:
        raise ValueError('peer validator source differs from reviewed receipt')
    if hashlib.sha256(raw).hexdigest()!=CONTRACT_SHA:
        raise ValueError('peer contract differs from owner freeze')
    # Execute the already reviewed, hash-verified bytes, not a second path read.
    peer=types.ModuleType('pinned_peer_benchmark_contract')
    exec(compile(source,str(root/'full_aster_benchmark_contract_v1.py'),'exec'),peer.__dict__)
    contract=peer.validate(json.loads(raw,object_pairs_hook=peer._unique))
    families=contract['case_packet']['families'];roles=contract['models']
    return {
        'schema':'b60-benchmark-contract-preparation.v1',
        'peer_contract_sha256':CONTRACT_SHA,'peer_validator_sha256':VALIDATOR_SHA,
        'owner_frozen_contract_verified':True,'authority':contract['authority'],
        'model_roles':roles,'heldout_packet_sha256':contract['case_packet']['sha256'],
        'case_contents_read':False,'baseline_measurements_read':False,
        'nominal_cases_per_role':contract['case_packet']['cases'],
        'nominal_two_role_case_captures':len(roles)*contract['case_packet']['cases'],
        'cases_per_family_per_role':families,
        'owner_model_calls_max_unchanged':contract['resources']['model_calls_max'],
        'owner_quality_and_latency_bars_unchanged':True,
        'acceptance_sampling_requirements':{
            'observations_per_acceptance_class_across_sessions_min':MIN_OBSERVATIONS_PER_ACCEPTANCE_CLASS,
            'independent_sessions_min':MIN_INDEPENDENT_SESSIONS,
            'latency_class_mapping':'not specified in this contract',
            'family_as_latency_class_projection':{
                'accepted':False,'assumption':'each of the six families is an acceptance latency class',
                'two_role_complete_answer_observations_min':len(roles)*len(families)*MIN_OBSERVATIONS_PER_ACCEPTANCE_CLASS,
                'model_call_budget_derived':False}},
        'open_dependencies':[
            'fresh measured reasoning-off baseline per accepted latency class',
            'owner-defined acceptance latency-class mapping and repeat/session allocation',
            'owner-reviewed sampling/budget extension beyond the nominal matched run',
            'reviewed fixed candidate model/runtime/mount adapter and actual fresh admission'],
        'ready_for_live_execution':False,'milestone_accepted':False,
        'recovery_qualification_inferred_from_document':False}
