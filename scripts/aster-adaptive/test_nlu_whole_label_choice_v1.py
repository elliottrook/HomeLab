from __future__ import annotations

import json
import unittest

import nlu_whole_label_choice_v1 as candidate


def response(label_id, *, finish_reason="stop", selection=None):
    content = selection if selection is not None else {"label_id": label_id}
    return json.dumps({
        "choices": [{
            "message": {"role": "assistant", "content": json.dumps(content)},
            "finish_reason": finish_reason,
        }]
    }).encode()


def find(**fields):
    matches = [
        label_id for label_id, value in candidate.CATALOGUE.items()
        if all(value[key] == expected for key, expected in fields.items())
    ]
    if len(matches) != 1:
        raise AssertionError(f"expected one label, found {matches}")
    return matches[0]


class WholeLabelChoiceTests(unittest.TestCase):
    def test_catalogue_is_fixed_complete_and_coherent(self):
        self.assertEqual(16, len(candidate.CATALOGUE))
        self.assertEqual(sorted(candidate.CATALOGUE), candidate.RESPONSE_SCHEMA["properties"]["label_id"]["enum"])
        for label_id, value in candidate.CATALOGUE.items():
            self.assertRegex(label_id, r"^L-[0-9a-f]{12}$")
            self.assertEqual(set(candidate.LABEL_FIELDS), set(value))
            candidate.contract._validate_semantics(value)

    def test_payload_is_deterministic_tool_free_selection_only(self):
        first = candidate.build_payload("Inspect the lab status")
        self.assertEqual(first, candidate.build_payload("Inspect the lab status"))
        payload = json.loads(first)
        self.assertEqual(candidate.MODEL, payload["model"])
        self.assertEqual(0, payload["temperature"])
        self.assertNotIn("tools", payload)
        self.assertEqual({"label_id"}, set(payload["response_format"]["schema"]["properties"]))
        for forbidden in ("authorization", "provider", "route", "confidence"):
            self.assertNotIn(forbidden, payload["response_format"]["schema"]["properties"])
        with self.assertRaises(ValueError):
            candidate.build_payload("Inspect status", model="unreviewed")

    def test_known_selection_maps_to_complete_label_without_authority(self):
        label_id = find(request_family="read-only-investigation", sensitivity="internal")
        record = candidate.result_record(
            case_id="public-1",
            request_text="Inspect the lab status",
            response_raw=response(label_id),
        )
        self.assertEqual("read-only-investigation", record["interpretation"]["request_family"])
        self.assertEqual(["lab.read"], record["interpretation"]["capability_needs"])
        self.assertEqual("not-granted", record["authority"])
        self.assertEqual("off", record["automatic_routing"])
        self.assertNotIn("Inspect the lab status", json.dumps(record))

    def test_unknown_extra_duplicate_and_unclean_responses_fail_closed(self):
        known = next(iter(candidate.CATALOGUE))
        invalid = [
            response("L-000000000000"),
            response(known, selection={"label_id": known, "confidence": 1}),
            response(known, finish_reason="length"),
            json.dumps({"choices": [], "usage": {}}).encode(),
        ]
        duplicate = json.dumps({
            "choices": [{
                "message": {"role": "assistant", "content": '{"label_id":"%s","label_id":"%s"}' % (known, known)},
                "finish_reason": "stop",
            }]
        }).encode()
        invalid.append(duplicate)
        for raw in invalid:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                candidate.parse_selection(raw)

    def test_deterministic_guard_tightens_private_and_impossible_requests(self):
        public_answer = find(
            request_family="general-answer", sensitivity="public",
            disposition="route",
        )
        private = candidate.interpret("Summarize my medication notes", response(public_answer))
        self.assertEqual("personal", private["sensitivity"])
        impossible = candidate.interpret("Read my unspoken thoughts", response(public_answer))
        self.assertEqual(("unsupported", "abstain"), (
            impossible["request_family"], impossible["disposition"],
        ))
        self.assertEqual([], impossible["capability_needs"])

    def test_guard_cannot_broaden_selected_capabilities(self):
        timer = find(capability_needs=["timer.control"], disposition="route")
        result = candidate.interpret("Set a timer for ten minutes", response(timer))
        self.assertEqual(["timer.control"], result["capability_needs"])
        clarify = find(request_family="household-command", disposition="clarify")
        result = candidate.interpret("Turn it off", response(clarify))
        self.assertEqual(("clarify", []), (
            result["disposition"], result["capability_needs"],
        ))

    def test_publication_safety_overrides_selected_route(self):
        public_web = find(
            request_family="external-research", sensitivity="public",
            disposition="route",
        )
        result = candidate.interpret(
            "Publish my private calendar on a public website",
            response(public_web),
        )
        self.assertEqual(("personal", "deny", "policy-denied"), (
            result["sensitivity"], result["disposition"], result["reason"],
        ))
        self.assertEqual(["web.publish"], result["capability_needs"])


if __name__ == "__main__":
    unittest.main()
