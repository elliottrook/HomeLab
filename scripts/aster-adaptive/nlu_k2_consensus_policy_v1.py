"""Frozen deterministic acceptance policy for K2 arbitration records."""
from __future__ import annotations

import copy

import nlu_local_model_adapter as contract
import nlu_whole_label_choice_v1 as ontology


SCHEMA = "aster-nlu-k2-consensus-decision.v1"


def _label_id(interpretation: dict[str, object]) -> str:
    contract._validate_semantics(interpretation)
    matches = [label_id for label_id, value in ontology.CATALOGUE.items()
               if value == interpretation]
    if len(matches) != 1:
        raise ValueError("guarded interpretation is outside frozen ontology")
    return matches[0]


def decide(record: dict[str, object]) -> dict[str, object]:
    required = {
        "case_id", "shortlist_ids", "selected_label_id", "guard_changed",
        "interpretation", "latency_seconds", "authority",
    }
    if not isinstance(record, dict) or set(record) != required:
        raise ValueError("K2 arbitration record fields differ")
    case_id = record["case_id"]
    shortlist = record["shortlist_ids"]
    selected = record["selected_label_id"]
    guard_changed = record["guard_changed"]
    if (type(case_id) is not str or not case_id
            or not isinstance(shortlist, list) or len(shortlist) != 4
            or len(set(shortlist)) != 4
            or any(type(item) is not str or item not in ontology.CATALOGUE
                   for item in shortlist)
            or type(selected) is not str or selected not in shortlist
            or type(guard_changed) is not bool
            or record["authority"] != "not-granted"):
        raise ValueError("K2 arbitration record values differ")
    interpretation = copy.deepcopy(record["interpretation"])
    final_label_id = _label_id(interpretation)
    disposition = interpretation["disposition"]
    accepted = (
        (not guard_changed and selected == shortlist[0])
        or (guard_changed and disposition in {"abstain", "deny"})
    )
    return {
        "schema": SCHEMA,
        "case_id": case_id,
        "shortlist_ids": list(shortlist),
        "selected_label_id": selected,
        "final_label_id": final_label_id,
        "guard_changed": guard_changed,
        "accepted": accepted,
        "disposition": disposition,
        "authority": "not-granted",
        "route_effect": False,
    }
