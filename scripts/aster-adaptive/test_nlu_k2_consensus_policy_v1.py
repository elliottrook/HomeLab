import copy
import unittest

import nlu_k2_consensus_policy_v1 as policy
import nlu_whole_label_choice_v1 as ontology


LABELS = sorted(ontology.CATALOGUE)


def record(*, selected, first=None, guard_changed=False, interpretation=None):
    first = first or selected
    shortlist = [first] + [item for item in LABELS
                           if item not in {first, selected}][:3]
    if selected not in shortlist:
        shortlist[-1] = selected
    return {
        "case_id": "case-1",
        "shortlist_ids": shortlist,
        "selected_label_id": selected,
        "guard_changed": guard_changed,
        "interpretation": copy.deepcopy(
            interpretation or ontology.CATALOGUE[selected]),
        "latency_seconds": 0.5,
        "authority": "not-granted",
    }


class K2ConsensusPolicyTests(unittest.TestCase):
    def test_unchanged_top_one_agreement_is_accepted(self):
        decision = policy.decide(record(selected=LABELS[0]))
        self.assertTrue(decision["accepted"])
        self.assertFalse(decision["route_effect"])
        self.assertEqual("not-granted", decision["authority"])

    def test_model_correction_without_independent_guard_is_abstained(self):
        decision = policy.decide(record(selected=LABELS[1], first=LABELS[0]))
        self.assertFalse(decision["accepted"])

    def test_guarded_safety_tightening_can_be_accepted(self):
        safe_id = next(label_id for label_id, value in ontology.CATALOGUE.items()
                       if value["disposition"] == "abstain")
        decision = policy.decide(record(
            selected=LABELS[0], guard_changed=True,
            interpretation=ontology.CATALOGUE[safe_id]))
        self.assertTrue(decision["accepted"])
        self.assertEqual(safe_id, decision["final_label_id"])

    def test_guarded_route_or_clarify_change_is_not_accepted(self):
        for disposition in ("route", "clarify"):
            label_id = next(
                item for item, value in ontology.CATALOGUE.items()
                if value["disposition"] == disposition)
            decision = policy.decide(record(
                selected=LABELS[0], guard_changed=True,
                interpretation=ontology.CATALOGUE[label_id]))
            self.assertFalse(decision["accepted"])

    def test_unknown_fields_or_authority_fail_closed(self):
        changed = record(selected=LABELS[0])
        changed["extra"] = True
        with self.assertRaises(ValueError):
            policy.decide(changed)
        changed = record(selected=LABELS[0])
        changed["authority"] = "granted"
        with self.assertRaises(ValueError):
            policy.decide(changed)


if __name__ == "__main__":
    unittest.main()
