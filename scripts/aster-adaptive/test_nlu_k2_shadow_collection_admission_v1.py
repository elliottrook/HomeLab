import copy
import json
import unittest

import nlu_k2_shadow_collection_admission_v1 as admission
import nlu_k2_shadow_fixture_custody_v1 as custody
import nlu_k2_shadow_label_review_v1 as label_review
import nlu_whole_label_choice_v1 as ontology
from nlu_threshold_policy import FAMILIES


def evidence():
    selected = {}
    for label_id, value in ontology.CATALOGUE.items():
        selected.setdefault(value["request_family"], label_id)
    rows = [{"id": f"shadow-{family}-{index}",
             "request_text": f"Sanitized fictional {family} request {index}",
             "expected_label_id": selected[family],
             "data_class": "synthetic-sanitized-S0"}
            for family in FAMILIES for index in range(10)]
    receipt = custody.seal(rows, development_case_ids=["dev"],
        development_request_sha256=["1" * 64], sealed_case_ids=["sealed"],
        sealed_request_sha256=["2" * 64], custodian_id="custodian",
        label_reviewer_id="reviewer")
    labels = [{"id": row["id"], "expected_label_id": row["expected_label_id"]}
              for row in rows]
    review = label_review.review(receipt, labels, reviewer_id="reviewer",
                                 candidate_output_present=False)
    development = {"schema":"aster-m3-k2-development-reconciliation.v1",
        "state":"complete", "booking_id":admission.DEVELOPMENT_BOOKING,
        "requests":192, "retries":0, "errors":0, "production_restored":True,
        "development_gate_passed":True, "status":"pass", "result_sha256":"3"*64}
    sealed = {"schema":"aster-nlu-k2-sealed-evaluation-score.v1",
        "status":"pass", "cases":32, "model_requests":32, "retries":0,
        "response_errors":0, "exact":31, "unsafe_false_routes":0,
        "routed_privacy_underclassifications":0, "result_sha256":"4"*64,
        "authority":"not-granted", "automatic_routing":"off",
        "production_restored":True}
    encode=lambda value:(json.dumps(value,sort_keys=True,separators=(",",":"))+"\n").encode()
    return encode(development), encode(sealed), receipt, review


class K2ShadowCollectionAdmissionTests(unittest.TestCase):
    def test_exact_passing_chain_yields_non_authorizing_review_candidate(self):
        development, sealed, receipt, review = evidence()
        value = admission.admit(development_raw=development,
            sealed_score_raw=sealed, custody_receipt=receipt,
            label_review_receipt=review)
        self.assertEqual(60, value["model_requests"])
        self.assertFalse(value["collection_effect_authorized"])
        self.assertTrue(value["own_lab_hours_booking_required_if_b60_used"])

    def test_failed_or_unrestored_development_fails_closed(self):
        development, sealed, receipt, review = evidence()
        value=json.loads(development); value["production_restored"]=False
        with self.assertRaisesRegex(ValueError, "development"):
            admission.admit(development_raw=json.dumps(value).encode(),
                sealed_score_raw=sealed,custody_receipt=receipt,label_review_receipt=review)

    def test_failed_or_unsafe_sealed_score_fails_closed(self):
        development, sealed, receipt, review = evidence()
        value=json.loads(sealed); value["unsafe_false_routes"]=1
        with self.assertRaisesRegex(ValueError, "sealed"):
            admission.admit(development_raw=development,
                sealed_score_raw=json.dumps(value).encode(),custody_receipt=receipt,
                label_review_receipt=review)

    def test_changed_custody_or_review_binding_fails_closed(self):
        development, sealed, receipt, review = evidence(); receipt["case_count"]=59
        with self.assertRaisesRegex(ValueError, "custody"):
            admission.admit(development_raw=development,sealed_score_raw=sealed,
                custody_receipt=receipt,label_review_receipt=review)
        development, sealed, receipt, review = evidence(); review["fixture_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError, "review"):
            admission.admit(development_raw=development,sealed_score_raw=sealed,
                custody_receipt=receipt,label_review_receipt=review)

    def test_review_after_candidate_output_fails_closed(self):
        development, sealed, receipt, review = evidence(); review["candidate_output_observed"]=True
        with self.assertRaisesRegex(ValueError, "review"):
            admission.admit(development_raw=development,sealed_score_raw=sealed,
                custody_receipt=receipt,label_review_receipt=review)


if __name__ == "__main__": unittest.main()
