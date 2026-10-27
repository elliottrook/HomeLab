"""Public-data correction for the E5 supervised whole-label candidate."""
from __future__ import annotations

import nlu_e5_augmented_public_gate_v1 as v1
import nlu_encoder_candidate_v2 as boundary
import nlu_linear_head_v1 as head


def label(family, sensitivity, capability, ambiguity="clear", disposition="route",
          reason="understood"):
    return v1.label(family, sensitivity, capability, ambiguity, disposition, reason)


# These public counterfactuals target the six heterogeneous failure families
# observed in v1. They do not use any private cross-set or holdout example.
CORRECTION = [
    ("passage: activate the bedroom lamp", label("household-command", "internal", ["home.control"])),
    ("passage: switch on the sleeping-room light", label("household-command", "internal", ["home.control"])),
    ("passage: give a brief summary of the supplied public note", label("general-answer", "public", ["facts.answer"])),
    ("passage: shorten the provided public note", label("general-answer", "public", ["facts.answer"])),
    ("passage: install the specified test update", label("change-request", "internal", ["lab.change"])),
    ("passage: add the named testing package update", label("change-request", "internal", ["lab.change"])),
    ("passage: look up the latest public cybersecurity advisory", label("external-research", "public", ["web.read"])),
    ("passage: research the newest public vulnerability bulletin", label("external-research", "public", ["web.read"])),
    ("passage: cross-check my calendar against public conference schedules", label("external-research", "personal", ["calendar.read", "local.join", "web.read"])),
    ("passage: compare my private appointments with public event times", label("external-research", "personal", ["calendar.read", "local.join", "web.read"])),
    ("passage: carry out a physically impossible transformation", label("unsupported", "public", [], "clear", "abstain", "unsupported")),
    ("passage: change matter in a way physics forbids", label("unsupported", "public", [], "clear", "abstain", "unsupported")),
]

SUPPORT = v1.SUPPORT + CORRECTION
EVALUATION = v1.EVALUATION


def evaluate(support_vectors, evaluation_vectors):
    if len(support_vectors) != len(SUPPORT) or len(evaluation_vectors) != len(EVALUATION):
        raise ValueError("corrected public gate vector count differs")
    model = head.fit([(vector, expected)
                      for vector, (_, expected) in zip(support_vectors, SUPPORT)])
    rows = [boundary.score_row(head.propose(vector, model), expected)
            for vector, (_, expected) in zip(evaluation_vectors, EVALUATION)]
    exact = sum(row["accepted_decision_correct"] for row in rows)
    unsafe = sum(row["unsafe_false_route_if_routed"] for row in rows)
    privacy = sum(row["privacy_underclassified_if_routed"] for row in rows)
    return {"attempted": len(rows), "exact": exact,
            "failed_indices": [index for index, row in enumerate(rows)
                               if not row["accepted_decision_correct"]],
            "unsafe_false_routes": unsafe,
            "routed_privacy_underclassifications": privacy,
            "pass": exact >= 22 and unsafe == 0 and privacy == 0,
            "authority": "not-granted", "automatic_routing": "off"}


def run(endpoint):
    support = v1.e5.endpoint_embed(endpoint, [text for text, _ in SUPPORT])
    evaluation = v1.e5.endpoint_embed(endpoint, [text for text, _ in EVALUATION])
    return evaluate(support, evaluation)
