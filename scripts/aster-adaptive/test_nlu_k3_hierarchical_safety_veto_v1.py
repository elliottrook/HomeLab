import copy
import json
import unittest

import nlu_k3_hierarchical_safety_veto_v1 as k3
import nlu_whole_label_choice_v1 as ontology


LABELS = sorted(ontology.CATALOGUE)


def label(disposition, *, family=None):
    return next(
        label_id for label_id, value in ontology.CATALOGUE.items()
        if value["disposition"] == disposition
        and (family is None or value["request_family"] == family))


def record(selected, *, first=None):
    first = first or selected
    shortlist = [first] + [item for item in LABELS if item not in {first, selected}][:3]
    if selected not in shortlist:
        shortlist[-1] = selected
    return {
        "case_id": "case-1", "shortlist_ids": shortlist,
        "selected_label_id": selected, "guard_changed": False,
        "interpretation": copy.deepcopy(ontology.CATALOGUE[selected]),
        "latency_seconds": 0.5, "authority": "not-granted",
    }


def verdict(label_id):
    value = ontology.CATALOGUE[label_id]
    return {
        "schema": k3.SCHEMA,
        "request_family": value["request_family"],
        "disposition": value["disposition"],
        "sensitivity": value["sensitivity"],
        "ambiguity": value["ambiguity"],
        "route_eligible": (value["disposition"] == "route"
                           and value["ambiguity"] == "clear"),
        "authority": "not-granted",
    }


def response(value):
    body = {key: item for key, item in value.items()
            if key not in {"schema", "authority"}}
    return json.dumps({"choices": [{"message": {
        "role": "assistant", "content": json.dumps(body)},
        "finish_reason": "stop"}]}, sort_keys=True, separators=(",", ":")).encode()


class K3HierarchicalSafetyVetoTests(unittest.TestCase):
    def test_agreeing_route_is_only_a_non_effect_decision(self):
        route = label("route")
        value = k3.decide(record(route), verdict(route))
        self.assertTrue(value["accepted"])
        self.assertEqual("route", value["disposition"])
        self.assertFalse(value["route_effect"])
        self.assertEqual("off", value["automatic_routing"])

    def test_shared_k2_route_mistake_is_vetoed_by_independent_semantics(self):
        route = label("route", family="change-request")
        unsupported = label("abstain", family="unsupported")
        value = k3.decide(record(route), verdict(unsupported))
        self.assertFalse(value["accepted"])
        self.assertEqual("abstain", value["disposition"])

    def test_off_top_one_model_correction_can_pass_only_with_full_agreement(self):
        first = label("route", family="change-request")
        corrected = label("abstain", family="unsupported")
        value = k3.decide(record(corrected, first=first), verdict(corrected))
        self.assertTrue(value["accepted"])
        self.assertEqual(corrected, value["final_label_id"])

    def test_family_sensitivity_or_ambiguity_disagreement_vetoes(self):
        route = label("route")
        other_sensitivity = next(
            value for value in k3.SENSITIVITIES
            if value != ontology.CATALOGUE[route]["sensitivity"])
        for field, changed in (
                ("request_family", "unsupported"),
                ("sensitivity", other_sensitivity),
                ("ambiguity", "ambiguous")):
            changed_verdict = verdict(route); changed_verdict[field] = changed
            if field == "ambiguity":
                changed_verdict["route_eligible"] = False
            self.assertFalse(k3.decide(record(route), changed_verdict)["accepted"])

    def test_inconsistent_eligibility_or_authority_fails_closed(self):
        route = label("route")
        for field, changed in (("route_eligible", False),
                               ("authority", "granted")):
            changed_verdict = verdict(route); changed_verdict[field] = changed
            with self.assertRaises(ValueError):
                k3.decide(record(route), changed_verdict)

    def test_payload_and_parser_expose_no_final_label_catalogue(self):
        payload = json.loads(k3.build_payload("Please classify this request"))
        system = payload["messages"][0]["content"]
        self.assertTrue(all(label_id not in system for label_id in LABELS))
        self.assertNotIn("tools", payload)
        route = label("route")
        self.assertEqual(verdict(route), k3.parse_verdict(response(verdict(route))))

    def test_extra_or_duplicate_response_fields_fail_closed(self):
        route = label("route"); changed = verdict(route); changed["extra"] = True
        with self.assertRaises(ValueError): k3.validate_verdict(changed)
        body = {key: item for key, item in verdict(route).items()
                if key not in {"schema", "authority"}}
        body["schema"] = k3.SCHEMA
        extra_response = json.dumps({"choices": [{"message": {
            "role": "assistant", "content": json.dumps(body)},
            "finish_reason": "stop"}]}).encode()
        with self.assertRaises(ValueError): k3.parse_verdict(extra_response)
        duplicate = b'{"choices":[],"choices":[]}'
        with self.assertRaises(ValueError): k3.parse_verdict(duplicate)


if __name__ == "__main__": unittest.main()
