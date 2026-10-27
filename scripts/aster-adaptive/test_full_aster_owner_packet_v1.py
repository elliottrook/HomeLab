import unittest

import full_aster_owner_packet_v1 as packet


def fixture():
    outcomes = ["useful_answer", "useful_answer", "useful_answer",
                "justified_abstention"]
    cases = []
    for family in sorted(packet.proposal.FAMILIES):
        for index in range(4):
            outcome = outcomes[index]
            if family == "ambiguity_and_safety":
                outcome = "clarification" if index < 2 else "policy_denial"
            elif index == 3 and family in {"synthetic_private_context",
                                          "synthetic_public_private_join"}:
                outcome = "policy_denial"
            cases.append({"id": f"{family}-{index + 1}", "family": family,
                          "request": "Fictional request", "context": [],
                          "expected_outcome": outcome,
                          "maximum_tool_scope": "none",
                          "rubric": {"required_facts": [],
                                     "prohibited_claims": ["invented effect"],
                                     "citation_required": False,
                                     "completion_criteria": ["correct outcome"]}})
    return {"schema": packet.SCHEMA, "fictional": True, "cases": cases}


class FullAsterOwnerPacketTests(unittest.TestCase):
    def test_content_free_manifest_contains_no_case_content(self):
        result = packet.content_free_manifest(fixture())
        self.assertEqual(24, result["cases"])
        self.assertFalse(result["content_exported"])
        self.assertNotIn("request", result)
        self.assertNotIn("rubric", result)

    def test_duplicate_id_rejected(self):
        value = fixture(); value["cases"][1]["id"] = value["cases"][0]["id"]
        with self.assertRaises(ValueError):
            packet.validate(value)

    def test_nonfictional_packet_rejected(self):
        value = fixture(); value["fictional"] = False
        with self.assertRaises(ValueError):
            packet.validate(value)

    def test_family_imbalance_rejected(self):
        value = fixture(); value["cases"][4]["family"] = value["cases"][0]["family"]
        with self.assertRaises(ValueError):
            packet.validate(value)

    def test_missing_rubric_rejected(self):
        value = fixture(); value["cases"][0]["rubric"]["completion_criteria"] = []
        with self.assertRaises(ValueError):
            packet.validate(value)


if __name__ == "__main__":
    unittest.main()
