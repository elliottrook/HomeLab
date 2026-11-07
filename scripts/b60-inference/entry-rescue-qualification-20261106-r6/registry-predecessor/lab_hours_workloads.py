"""Fixed, root-installed Lab Hours workload registrations.

This module is deliberately data-only at the admission boundary: booking
records select a registered identity, never an arbitrary command.  The
platform runner validates the selected identity and its pinned runtime files
before any effect.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import subprocess


@dataclass(frozen=True)
class WorkloadSpec:
    workload_id: str
    owner: str
    request_count: int
    per_request_timeout_seconds: int
    deadline_seconds: int
    minimum_booking_seconds: int
    recovery_reserve_seconds: int
    runner_kind: str
    runtime_pins: tuple[tuple[str, str], ...]
    packet_sha256: str | None = None
    result_max_bytes: int | None = None
    retryable_session: bool = False
    maximum_attempts: int | None = 1

    @property
    def rescue_after_seconds(self) -> int:
        return self.deadline_seconds


ACCEPTED_BASELINE_PINS = (
    ("model_sha256", "cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13"),
    ("binary_sha256", "0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5"),
    ("unit_sha256", "a4c75169673a1a230682b73d362a05c1bdd30f7a5c41cfb9c77463204dfd4cb3"),
)


WORKLOADS = {
    "accepted-9b-direct-control-smoke-v1": WorkloadSpec(
        workload_id="accepted-9b-direct-control-smoke-v1", owner="lab-hours",
        request_count=3, per_request_timeout_seconds=120, deadline_seconds=1800,
        minimum_booking_seconds=1800, recovery_reserve_seconds=900,
        runner_kind="full-inference-pilot", runtime_pins=(),
    ),
    "accepted-9b-owner-loss-exercise-v1": WorkloadSpec(
        workload_id="accepted-9b-owner-loss-exercise-v1", owner="lab-hours",
        request_count=0, per_request_timeout_seconds=0, deadline_seconds=120,
        minimum_booking_seconds=300, recovery_reserve_seconds=120,
        runner_kind="owner-loss-exercise", runtime_pins=(),
    ),
    "sa3-expanded-source-quality-v1": WorkloadSpec(
        workload_id="sa3-expanded-source-quality-v1", owner="aster-stream-a",
        request_count=20, per_request_timeout_seconds=120, deadline_seconds=2700,
        minimum_booking_seconds=3600, recovery_reserve_seconds=900,
        runner_kind="sa3-expanded-quality", runtime_pins=(
            ("sa3-expanded-source-quality-v1.json",
             "ed75836af74401709a74333a96d0a22629b23e389e5262bbc365ab6aed018d23"),
            ("sa3_expanded_quality_packet.py",
             "b9011bef592421b6e6c28ec830b17f1296409daa30fd4f508d913ba35c104657"),
            ("sa3_expanded_quality_runner.py",
             "39f01d80d5c2a4a43bd9af24ca0060c5323cdb3011a7f9b3d14a19bfcaaaf351"),
            ("sa3_fair_scorer.py",
             "92a4526886b21492995b73c834844a570b7718415abcadce848bcd1da6860bda"),
        ),
        packet_sha256="d8c7945924a98bfae45522fd4ac9f377871db3243136b4a00617263cf44e9066",
        result_max_bytes=262144,
    ),
    "m3-joint-semantic-35b-public-v1": WorkloadSpec(
        workload_id="m3-joint-semantic-35b-public-v1", owner="aster-stream-a",
        request_count=24, per_request_timeout_seconds=90, deadline_seconds=2700,
        minimum_booking_seconds=3600, recovery_reserve_seconds=900,
        runner_kind="m3-joint-semantic-35b", runtime_pins=(
            ("nlu_joint_semantic_35b_v1.py", "b2682aa294e5d29b36c961c0b6b5b1593312781026c4f1e3424836ee44f63309"),
            ("nlu_joint_semantic_35b_public_runner_v1.py", "b91e2dc3c2b6c8fbb89d912d8789ea2ac49d6ac412d9e77f854f66c259ac18d3"),
            ("nlu_whole_label_public_runner_v1.py", "fe5186020f9fcad1bbe25f72f3a22c95a1d9ed23342aef611dd510d59a1b45f3"),
            ("nlu_whole_label_choice_v1.py", "6e7ee332ce74a44a5bb19877f9f8f0c90f814687279b3c4993fbb93fbd58948a"),
            ("nlu_deterministic_guard_v1.py", "d7d62d19008519ae50aa9b46799ab1f277a51904f2e80e65c30517abca8a7135"),
            ("nlu_local_model_adapter.py", "3a3b09f12bcd2088f0d604363a5bc0e69190c177eced50dc5a14eb582749aed0"),
            ("nlu_threshold_policy.py", "984932d8716531858972e22723fe962701077f9a15991c58384c6ee6661ebb5d"),
            ("nlu-development-v1.json", "1565a21c78875f64f4f25a190e977ae34dc01bdfcfd5e49c056e8365268b3785"),
            ("m3_joint_semantic_35b_guest_workload.py", "91fa17ad55177b5d2c53fefb8569c13c48e1bfeec8332b97726e8d30bab0d85b"),
            ("m3_joint_semantic_35b_transaction.py", "dc92e35ee11ed12cd5d842282027adbcbf4c24611ba6b4be64a820fa951f0677"),
            ("m3_joint_semantic_35b_guardian.py", "a485c2cde71447a8a4feda0c25f7e22d26fe0e9ace2da7b524e698a96275113b"),
            ("full_aster_first_screen_candidate.py", "eb07b46c1f592ef35c9e0bcb7f0f6aaa0d484775e18ab991b6c29dbe1dc2af6b"),
            ("full_aster_first_screen_observer.py", "277fa96f411737e265f3fcfb3169d00a3dfb0289d5b075150f677b04469ce340"),
            ("full_aster_first_screen_recovery.py", "992e7d4bbf8b0f62cc72546dae9ad2ab9622830deef78d096afc028c2b5eb3f4"),
        ),
        packet_sha256="1565a21c78875f64f4f25a190e977ae34dc01bdfcfd5e49c056e8365268b3785",
        result_max_bytes=262144,
    ),
    "sa3-evidence-envelope-quality-v1": WorkloadSpec(
        workload_id="sa3-evidence-envelope-quality-v1", owner="aster-stream-a",
        request_count=20, per_request_timeout_seconds=120, deadline_seconds=2700,
        minimum_booking_seconds=3600, recovery_reserve_seconds=900,
        runner_kind="sa3-evidence-envelope-quality", runtime_pins=(
            ("sa3-evidence-envelope-quality-v1.json",
             "a01c6d71dce91141f2eae9bad21a56641f6aa269cdc3561a165385d210e3ec2a"),
            ("sa3_deterministic_evidence_envelope_v1.py",
             "9f8b14f8f1a4d162eed03f39e82b868118b0c5bdcb3a7fce744a28e9d13e3da3"),
            ("sa3_evidence_envelope_batch_v1.py",
             "78abc29951fe80a469c49ee44af6a9380f032648ad757f3182c11bd0f0464500"),
            ("sa3_evidence_envelope_quality_freeze_v1.py",
             "95cf006fc7e3b2aeb3acf0e926336e65e3c3a8b5e5f8cb5cc083e4e5ab7b3483"),
            ("sa3_evidence_envelope_runner_v1.py",
             "372c19ef3c2f5e8f0965167011c4bba47d9326e5f5ffe7d0b77d9ac5898fc352"),
        ),
        packet_sha256="a01c6d71dce91141f2eae9bad21a56641f6aa269cdc3561a165385d210e3ec2a",
        result_max_bytes=524288,
    ),
    "sa3-evidence-envelope-candidate-i-quality-v1": WorkloadSpec(
        workload_id="sa3-evidence-envelope-candidate-i-quality-v1",
        owner="aster-stream-a",
        request_count=20, per_request_timeout_seconds=120, deadline_seconds=2700,
        minimum_booking_seconds=3600, recovery_reserve_seconds=900,
        runner_kind="sa3-evidence-envelope-candidate-i-quality", runtime_pins=(
            ("sa3-evidence-envelope-candidate-i-quality-v1.json",
             "0b9bfb86ef0e3381aca520e294b90b01f9616c51caea21e71d559467837625d0"),
            ("sa3_deterministic_evidence_envelope_v1.py",
             "9f8b14f8f1a4d162eed03f39e82b868118b0c5bdcb3a7fce744a28e9d13e3da3"),
            ("sa3_deterministic_evidence_envelope_v2.py",
             "4ca154c6ea0b0738adc3c9e21544ac0a6d3c05473852f88f97b6e5e7e1611943"),
            ("sa3_evidence_envelope_batch_v2.py",
             "eaeddb10d5a36df5dd3f3646691d19857f094f2872086d7b78056d6ff7c70d4e"),
            ("sa3_evidence_envelope_runner_v2.py",
             "58b932a65afb6d88d4624d3d74b0d4d021091e0989c74e1ca4cf0afdede9188c"),
        ),
        packet_sha256="0b9bfb86ef0e3381aca520e294b90b01f9616c51caea21e71d559467837625d0",
        result_max_bytes=524288,
    ),
    "sa3-evidence-matrix-candidate-j-public-v1": WorkloadSpec(
        workload_id="sa3-evidence-matrix-candidate-j-public-v1",
        owner="aster-stream-a",
        request_count=6, per_request_timeout_seconds=120, deadline_seconds=1800,
        minimum_booking_seconds=2700, recovery_reserve_seconds=900,
        runner_kind="sa3-evidence-matrix-candidate-j-public", runtime_pins=(
            ("sa3-evidence-matrix-candidate-j-public-v1.json",
             "40f7cfeeb3884887c32f5674afdb840d764214730a23e71c1df660a08953572f"),
            ("sa3_evidence_matrix_candidate_j_contract.py",
             "b243d429218b134177f2b2cdf5ca4e3f28c8e0ed08a55b11e9d2ccb6bd17b2af"),
            ("sa3_evidence_matrix_candidate_j_runner.py",
             "ee3410dbed70dc9399a094e0260e0af94985daef961017de2dd9f70b4691d223"),
            ("sa3_evidence_matrix_candidate_j_public.py",
             "727d1de9707b5d654d828f6d1978bdbcd6da6ca597f234f4f793d4cfe3eed294"),
            ("sa3_evidence_matrix_candidate_j_batch.py",
             "856bc39083d078712dbf7289d2524dc0688e07ad5c645382d5dba9d99a75b388"),
        ),
        packet_sha256="40f7cfeeb3884887c32f5674afdb840d764214730a23e71c1df660a08953572f",
        result_max_bytes=262144,
    ),
    "astertv-v3-ebook-word-alignment-v1": WorkloadSpec(
        workload_id="astertv-v3-ebook-word-alignment-v1", owner="astertv-v3-m5",
        request_count=1, per_request_timeout_seconds=600, deadline_seconds=900,
        minimum_booking_seconds=1800, recovery_reserve_seconds=900,
        runner_kind="ebook-word-alignment", runtime_pins=(
            ("epub_word_alignment_transaction.py", "fb4cbcb5dd22963ae9557971e2b74eaba634a39ae233c3c75d00262125730a50"),
            ("epub_word_alignment_adapter.py", "8df7f426c941d043e5e69b1c1ba8f214d479750793c5e0d6cd7551c3af15e29e"),
        ),
        packet_sha256="1fde84377288795f522d5946380734e43dc643fd58b06720fdf79b56d59dd257",
        result_max_bytes=65536,
    ),
    "aster-tts-qwen-0p6b-cpu-screen-v1": WorkloadSpec(
        workload_id="aster-tts-qwen-0p6b-cpu-screen-v1", owner="aster-tts-experiment",
        request_count=1, per_request_timeout_seconds=2100, deadline_seconds=2400,
        minimum_booking_seconds=3600, recovery_reserve_seconds=900,
        runner_kind="aster-tts-single-cpu-screen", runtime_pins=(
            ("tts_single_cpu_screen_transaction.py", "cab558a729a07ce3a3b67edffbc54d3e54f3514dc1d54cf71888cf5526116f52"),
            ("tts_single_cpu_screen_adapter.py", "7846e324019d8dfbcdca7d53fcb565dbd2d332ddcf5dc2779b24112d9e034e8d"),
        ),
        packet_sha256="83616d4e4e5329d626e23597542487f0e43903622f0daea4c5648d53d74a6f90",
        result_max_bytes=65536,
    ),
    "aster-tts-qwen-1p7b-cpu-screen-v1": WorkloadSpec(
        workload_id="aster-tts-qwen-1p7b-cpu-screen-v1", owner="aster-tts-experiment",
        request_count=1, per_request_timeout_seconds=2100, deadline_seconds=2400,
        minimum_booking_seconds=3600, recovery_reserve_seconds=900,
        runner_kind="aster-tts-single-cpu-screen", runtime_pins=(
            ("tts_single_cpu_screen_transaction.py", "cab558a729a07ce3a3b67edffbc54d3e54f3514dc1d54cf71888cf5526116f52"),
            ("tts_single_cpu_screen_adapter.py", "7846e324019d8dfbcdca7d53fcb565dbd2d332ddcf5dc2779b24112d9e034e8d"),
        ),
        packet_sha256="83616d4e4e5329d626e23597542487f0e43903622f0daea4c5648d53d74a6f90",
        result_max_bytes=65536,
    ),
    "sa3-evidence-matrix-candidate-j-quality-v1": WorkloadSpec(
        workload_id="sa3-evidence-matrix-candidate-j-quality-v1",
        owner="aster-stream-a",
        request_count=20, per_request_timeout_seconds=120, deadline_seconds=2700,
        minimum_booking_seconds=3600, recovery_reserve_seconds=900,
        runner_kind="sa3-evidence-matrix-candidate-j-quality", runtime_pins=(
            ("sa3-evidence-matrix-candidate-j-quality-v1.json",
             "53cfd6a5a8b09ada122c64c60af3264b0ebda595bf1f2d5d53da2710e0141132"),
            ("sa3_evidence_matrix_candidate_j_contract.py",
             "b243d429218b134177f2b2cdf5ca4e3f28c8e0ed08a55b11e9d2ccb6bd17b2af"),
            ("sa3_evidence_matrix_candidate_j_runner.py",
             "ee3410dbed70dc9399a094e0260e0af94985daef961017de2dd9f70b4691d223"),
            ("sa3_evidence_matrix_candidate_j_quality_runtime.py",
             "4ea9b457d605926d88ce3bce92de0e377d657a0737854df30fe23b182037fea4"),
        ),
        packet_sha256="53cfd6a5a8b09ada122c64c60af3264b0ebda595bf1f2d5d53da2710e0141132",
        result_max_bytes=524288,
    ),
    "aster-news-video-musetalk-xpu-smoke-v1": WorkloadSpec(
        workload_id="aster-news-video-musetalk-xpu-smoke-v1",
        owner="aster-news-video",
        request_count=1, per_request_timeout_seconds=1200, deadline_seconds=1200,
        minimum_booking_seconds=5400, recovery_reserve_seconds=900,
        runner_kind="aster-news-video-musetalk-xpu", runtime_pins=(
            ("b60_musetalk_xpu_transaction.py",
             "a2c67006c3559ff86ab35dadfa6c7e511293d28b21d4a08589248608c053b58b"),
            ("b60_musetalk_xpu_adapter.py",
             "694c9b412cd769b62b5302679ff5453cb2a6b376a61b5583d7e78771d603308b"),
        ),
        packet_sha256="224c7b45aab24076c15b5009efd77f679f0b271767d8bddbff64ab6309390209",
        result_max_bytes=65536,
        retryable_session=True, maximum_attempts=None,
    ),
    "aster-news-video-musetalk-openvino-smoke-v1": WorkloadSpec(
        workload_id="aster-news-video-musetalk-openvino-smoke-v1",
        owner="aster-news-video",
        request_count=1, per_request_timeout_seconds=900, deadline_seconds=900,
        minimum_booking_seconds=1500, recovery_reserve_seconds=900,
        runner_kind="aster-news-video-musetalk-xpu", runtime_pins=(
            ("b60_musetalk_openvino_transaction.py",
             "e189f0aa0f96b135b74d0e49053bc3aed2139ffba95f96837cff6036aa1921d8"),
            ("b60_musetalk_openvino_adapter.py",
             "6c4a2416f8ebed93f9c052c8967a499c7e9123d8c5a238d960da620d5148ed66"),
            ("b60_musetalk_xpu_adapter.py",
             "694c9b412cd769b62b5302679ff5453cb2a6b376a61b5583d7e78771d603308b"),
            ("b60_musetalk_xpu_transaction.py",
             "a2c67006c3559ff86ab35dadfa6c7e511293d28b21d4a08589248608c053b58b"),
        ),
        packet_sha256="0082de9f397b4eb4061c545cea075c3cfd598a5bb8d5970db7f668179c5f2133",
        result_max_bytes=65536,
        retryable_session=True, maximum_attempts=None,
    ),
    "m3-k2-shortlist-arbitration-development-v1": WorkloadSpec(
        workload_id="m3-k2-shortlist-arbitration-development-v1",
        owner="aster-stream-a", request_count=192,
        per_request_timeout_seconds=45, deadline_seconds=1800,
        minimum_booking_seconds=3600, recovery_reserve_seconds=900,
        runner_kind="m3-k2-shortlist-arbitration-development",
        runtime_pins=(
            ("nlu_deterministic_guard_v1.py", "d7d62d19008519ae50aa9b46799ab1f277a51904f2e80e65c30517abca8a7135"),
            ("nlu_k2_consensus_policy_v1.py", "9027abbcc446d9c63100178e3ce9add60275a1f134bde9d7beeb30aa4a4d504e"),
            ("nlu_k2_development_runner_v1.py", "d5c9ef87bd49185466a12e7b53eab741d0f0dc40ce92c2977389dd2b0e5e3785"),
            ("nlu_k2_development_scorer_v1.py", "c43f3894ba65251b6fadbda1012bd2aead44c3357323b09f491f590ffd6e8558"),
            ("nlu_k2_shortlist_arbitration_preregistration_v1.py", "f3e633ac81d32bd63fb53e5a51339787cab1e66ee65f56874c012132a32f4f6a"),
            ("nlu_k2_shortlist_arbitrator_v1.py", "7c81894da9adbd1c3ee22b97d1487fcf2feadc1e4bc1e321a7c715479c517962"),
            ("nlu_local_model_adapter.py", "3a3b09f12bcd2088f0d604363a5bc0e69190c177eced50dc5a14eb582749aed0"),
            ("nlu_threshold_policy.py", "984932d8716531858972e22723fe962701077f9a15991c58384c6ee6661ebb5d"),
            ("nlu_whole_label_choice_v1.py", "6e7ee332ce74a44a5bb19877f9f8f0c90f814687279b3c4993fbb93fbd58948a"),
            ("nlu-k2-runtime-manifest-v1.json", "619450ce1eca89d3c21c5007d23c2f27c85e67f80e3b0709d0ebccb17ec86c88"),
            ("nlu-k2-development-corpus-v1.json", "9e2dd321c6660ad4bd09e9824c24b9727a30eba60a8df37e09f17d436ccce90a"),
            ("nlu-k2-shortlist-v1.json", "620f5b5badce1c3ee70b5718a0d05ff4ad6261308360cc5c5dad588e4b977f6e"),
        ),
        packet_sha256="619450ce1eca89d3c21c5007d23c2f27c85e67f80e3b0709d0ebccb17ec86c88",
        result_max_bytes=1048576,
    ),
}



WORKLOADS['b60-accepted-sycl-post-xe-qualification-v1'] = WorkloadSpec(
    workload_id='b60-accepted-sycl-post-xe-qualification-v1', owner='b60-stream-a', request_count=3,
    per_request_timeout_seconds=30, deadline_seconds=900,
    minimum_booking_seconds=2700, recovery_reserve_seconds=900,
    runner_kind='b60-post-xe-card',
    runtime_pins=(('b60_post_xe_card_bridge.py', '2c2f57a9d42d248456deb1d354d12bfd08e5e56ee3fa4ff7c92bebcac9934600'),),
    result_max_bytes=8192, retryable_session=False, maximum_attempts=1,
)



WORKLOADS['b60-accepted-sycl-post-xe-qualification-v2'] = WorkloadSpec(
    workload_id='b60-accepted-sycl-post-xe-qualification-v2', owner='b60-stream-a', request_count=3,
    per_request_timeout_seconds=30, deadline_seconds=600,
    minimum_booking_seconds=1800, recovery_reserve_seconds=900,
    runner_kind='b60-post-xe-card-r5',
    runtime_pins=(('b60_post_xe_r5_card_bridge.py', '3bd94a1e99491a0c23b4e530161389d3ef80a13fa7f2f5a35a9bad5f918df209'),),
    result_max_bytes=8192, retryable_session=False, maximum_attempts=1,
)



WORKLOADS['b60-qwen36-35b-failure-capture-v1'] = WorkloadSpec(
    workload_id='b60-qwen36-35b-failure-capture-v1', owner='b60-stream-a', request_count=2,
    per_request_timeout_seconds=60, deadline_seconds=1200,
    minimum_booking_seconds=2700, recovery_reserve_seconds=900,
    runner_kind='b60-exclusive-card-capture',
    runtime_pins=(('b60_exclusive_card_bridge.py', '079e16a415276562227f1645fe1e3ab64f5b0b41c1f453ae215935b1ca14f7d9'),),
    result_max_bytes=8192, retryable_session=False, maximum_attempts=1,
)


REGISTERED_WORKLOADS = frozenset(WORKLOADS)


def workload(name: str) -> WorkloadSpec:
    try:
        return WORKLOADS[name]
    except KeyError as exc:
        raise ValueError("workload is not registered") from exc


def validate_registry() -> None:
    sa3 = workload("sa3-expanded-source-quality-v1")
    if sa3.request_count != 20 or sa3.deadline_seconds != 2700:
        raise ValueError("SA3 workload budget drift")
    if sa3.minimum_booking_seconds != 3600 or sa3.recovery_reserve_seconds != 900:
        raise ValueError("SA3 booking boundary drift")
    if sa3.runner_kind != "sa3-expanded-quality" or len(sa3.runtime_pins) != 4:
        raise ValueError("SA3 runner registration drift")
    if sa3.result_max_bytes != 262144 or not sa3.packet_sha256:
        raise ValueError("SA3 result boundary drift")
    if any(name.endswith("keys-v1.json") or "review" in name
           for name, _ in sa3.runtime_pins):
        raise ValueError("SA3 excluded material entered runtime registration")
    m3 = workload("m3-joint-semantic-35b-public-v1")
    if (m3.request_count != 24 or m3.deadline_seconds != 2700
            or m3.minimum_booking_seconds != 3600
            or m3.recovery_reserve_seconds != 900
            or m3.runner_kind != "m3-joint-semantic-35b"
            or len(m3.runtime_pins) != 14
            or m3.packet_sha256 != "1565a21c78875f64f4f25a190e977ae34dc01bdfcfd5e49c056e8365268b3785"):
        raise ValueError("M3 workload registration drift")
    envelope = workload("sa3-evidence-envelope-quality-v1")
    if (envelope.owner != "aster-stream-a"
            or envelope.request_count != 20
            or envelope.per_request_timeout_seconds != 120
            or envelope.deadline_seconds != 2700
            or envelope.minimum_booking_seconds != 3600
            or envelope.recovery_reserve_seconds != 900
            or envelope.runner_kind != "sa3-evidence-envelope-quality"
            or len(envelope.runtime_pins) != 5
            or envelope.packet_sha256 != "a01c6d71dce91141f2eae9bad21a56641f6aa269cdc3561a165385d210e3ec2a"
            or envelope.result_max_bytes != 524288):
        raise ValueError("SA3 evidence-envelope registration drift")
    if any("keys" in name or "review" in name for name, _ in envelope.runtime_pins):
        raise ValueError("SA3 evidence-envelope excluded material entered runtime registration")
    candidate_i = workload("sa3-evidence-envelope-candidate-i-quality-v1")
    if (candidate_i.owner != "aster-stream-a"
            or candidate_i.request_count != 20
            or candidate_i.per_request_timeout_seconds != 120
            or candidate_i.deadline_seconds != 2700
            or candidate_i.minimum_booking_seconds != 3600
            or candidate_i.recovery_reserve_seconds != 900
            or candidate_i.runner_kind != "sa3-evidence-envelope-candidate-i-quality"
            or len(candidate_i.runtime_pins) != 5
            or candidate_i.packet_sha256 !=
                "0b9bfb86ef0e3381aca520e294b90b01f9616c51caea21e71d559467837625d0"
            or candidate_i.result_max_bytes != 524288):
        raise ValueError("SA3 candidate-i registration drift")
    if any("keys" in name or "review" in name
           for name, _ in candidate_i.runtime_pins):
        raise ValueError("SA3 candidate-i excluded material entered runtime registration")
    candidate_j = workload("sa3-evidence-matrix-candidate-j-public-v1")
    if (candidate_j.owner != "aster-stream-a"
            or candidate_j.request_count != 6
            or candidate_j.per_request_timeout_seconds != 120
            or candidate_j.deadline_seconds != 1800
            or candidate_j.minimum_booking_seconds != 2700
            or candidate_j.recovery_reserve_seconds != 900
            or candidate_j.runner_kind != "sa3-evidence-matrix-candidate-j-public"
            or len(candidate_j.runtime_pins) != 5
            or candidate_j.packet_sha256 !=
                "40f7cfeeb3884887c32f5674afdb840d764214730a23e71c1df660a08953572f"
            or candidate_j.result_max_bytes != 262144):
        raise ValueError("SA3 candidate-j registration drift")
    if any("keys" in name or "review" in name
           for name, _ in candidate_j.runtime_pins):
        raise ValueError("SA3 candidate-j excluded material entered runtime registration")

    ebook = workload("astertv-v3-ebook-word-alignment-v1")
    if (ebook.owner != "astertv-v3-m5"
            or ebook.request_count != 1
            or ebook.per_request_timeout_seconds != 600
            or ebook.deadline_seconds != 900
            or ebook.minimum_booking_seconds != 1800
            or ebook.recovery_reserve_seconds != 900
            or ebook.runner_kind != "ebook-word-alignment"
            or len(ebook.runtime_pins) != 2
            or ebook.packet_sha256 !=
                "1fde84377288795f522d5946380734e43dc643fd58b06720fdf79b56d59dd257"
            or ebook.result_max_bytes != 65536):
        raise ValueError("eBook word-alignment registration drift")

    for tts_id in ("aster-tts-qwen-0p6b-cpu-screen-v1",
                   "aster-tts-qwen-1p7b-cpu-screen-v1"):
        tts = workload(tts_id)
        if (tts.owner != "aster-tts-experiment"
                or tts.request_count != 1
                or tts.per_request_timeout_seconds != 2100
                or tts.deadline_seconds != 2400
                or tts.minimum_booking_seconds != 3600
                or tts.recovery_reserve_seconds != 900
                or tts.runner_kind != "aster-tts-single-cpu-screen"
                or len(tts.runtime_pins) != 2
                or tts.packet_sha256 !=
                    "83616d4e4e5329d626e23597542487f0e43903622f0daea4c5648d53d74a6f90"
                or tts.result_max_bytes != 65536):
            raise ValueError("Aster TTS single CPU screen registration drift")

    candidate_j_quality = workload("sa3-evidence-matrix-candidate-j-quality-v1")
    if (candidate_j_quality.owner != "aster-stream-a"
            or candidate_j_quality.request_count != 20
            or candidate_j_quality.per_request_timeout_seconds != 120
            or candidate_j_quality.deadline_seconds != 2700
            or candidate_j_quality.minimum_booking_seconds != 3600
            or candidate_j_quality.recovery_reserve_seconds != 900
            or candidate_j_quality.runner_kind
                != "sa3-evidence-matrix-candidate-j-quality"
            or len(candidate_j_quality.runtime_pins) != 4
            or candidate_j_quality.packet_sha256 !=
                "53cfd6a5a8b09ada122c64c60af3264b0ebda595bf1f2d5d53da2710e0141132"
            or candidate_j_quality.result_max_bytes != 524288):
        raise ValueError("SA3 candidate-j quality registration drift")
    if any("keys" in name or "review" in name or "scorer" in name
           for name, _ in candidate_j_quality.runtime_pins):
        raise ValueError("SA3 candidate-j quality excluded material entered registration")

    k2 = workload("m3-k2-shortlist-arbitration-development-v1")
    if (k2.owner != "aster-stream-a" or k2.request_count != 192
            or k2.per_request_timeout_seconds != 45
            or k2.deadline_seconds != 1800
            or k2.minimum_booking_seconds != 3600
            or k2.recovery_reserve_seconds != 900
            or k2.runner_kind != "m3-k2-shortlist-arbitration-development"
            or len(k2.runtime_pins) != 12
            or k2.packet_sha256 !=
                "619450ce1eca89d3c21c5007d23c2f27c85e67f80e3b0709d0ebccb17ec86c88"
            or k2.result_max_bytes != 1048576):
        raise ValueError("M3 K2 registration drift")

    musetalk = workload("aster-news-video-musetalk-xpu-smoke-v1")
    if (musetalk.owner != "aster-news-video"
            or musetalk.request_count != 1
            or musetalk.per_request_timeout_seconds != 1200
            or musetalk.deadline_seconds != 1200
            or musetalk.minimum_booking_seconds != 5400
            or musetalk.recovery_reserve_seconds != 900
            or musetalk.runner_kind != "aster-news-video-musetalk-xpu"
            or len(musetalk.runtime_pins) != 2
            or musetalk.packet_sha256 !=
                "224c7b45aab24076c15b5009efd77f679f0b271767d8bddbff64ab6309390209"
            or musetalk.result_max_bytes != 65536
            or not musetalk.retryable_session
            or musetalk.maximum_attempts is not None):
        raise ValueError("MuseTalk XPU registration drift")
    musetalk_ov = workload("aster-news-video-musetalk-openvino-smoke-v1")
    if (musetalk_ov.owner != "aster-news-video"
            or musetalk_ov.request_count != 1
            or musetalk_ov.deadline_seconds != 900
            or musetalk_ov.minimum_booking_seconds != 1500
            or musetalk_ov.recovery_reserve_seconds != 900
            or musetalk_ov.runner_kind != "aster-news-video-musetalk-xpu"
            or len(musetalk_ov.runtime_pins) != 4
            or musetalk_ov.packet_sha256 !=
                "0082de9f397b4eb4061c545cea075c3cfd598a5bb8d5970db7f668179c5f2133"
            or musetalk_ov.result_max_bytes != 65536
            or not musetalk_ov.retryable_session
            or musetalk_ov.maximum_attempts is not None):
        raise ValueError("MuseTalk OpenVINO registration drift")


    b60 = workload('b60-accepted-sycl-post-xe-qualification-v1')
    if (b60.owner != 'b60-stream-a' or b60.runner_kind != 'b60-post-xe-card'
            or b60.request_count != 3 or b60.per_request_timeout_seconds != 30
            or b60.deadline_seconds != 900 or b60.minimum_booking_seconds != 2700
            or b60.recovery_reserve_seconds != 900 or b60.retryable_session
            or b60.maximum_attempts != 1 or b60.result_max_bytes != 8192
            or b60.runtime_pins != (('b60_post_xe_card_bridge.py', '2c2f57a9d42d248456deb1d354d12bfd08e5e56ee3fa4ff7c92bebcac9934600'),)):
        raise ValueError('B60 fixed-card registration drift')

    b60 = workload('b60-accepted-sycl-post-xe-qualification-v2')
    if (b60.owner != 'b60-stream-a' or b60.runner_kind != 'b60-post-xe-card-r5'
            or b60.request_count != 3 or b60.per_request_timeout_seconds != 30
            or b60.deadline_seconds != 600 or b60.minimum_booking_seconds != 1800
            or b60.recovery_reserve_seconds != 900 or b60.retryable_session
            or b60.maximum_attempts != 1 or b60.result_max_bytes != 8192
            or b60.runtime_pins != (('b60_post_xe_r5_card_bridge.py', '3bd94a1e99491a0c23b4e530161389d3ef80a13fa7f2f5a35a9bad5f918df209'),)):
        raise ValueError('B60 fixed-card registration drift')

    b60 = workload('b60-qwen36-35b-failure-capture-v1')
    if (b60.owner != 'b60-stream-a' or b60.runner_kind != 'b60-exclusive-card-capture'
            or b60.request_count != 2 or b60.per_request_timeout_seconds != 60
            or b60.deadline_seconds != 1200 or b60.minimum_booking_seconds != 2700
            or b60.recovery_reserve_seconds != 900 or b60.retryable_session
            or b60.maximum_attempts != 1 or b60.result_max_bytes != 8192
            or b60.runtime_pins != (('b60_exclusive_card_bridge.py', '079e16a415276562227f1645fe1e3ab64f5b0b41c1f453ae215935b1ca14f7d9'),)):
        raise ValueError('B60 fixed-card registration drift')

def _local_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".", 1)[0])
    return names


def _validate_k2_guest_target(spec: WorkloadSpec, *, expected_uid: int,
                              runner=subprocess.run) -> dict[str, object]:
    script = r'''import ast,hashlib,json,os,stat,sys
from pathlib import Path
value=json.loads(sys.stdin.read());root=Path(value["root"]);pins=value["pins"]
modules={Path(name).stem for name in pins if name.endswith(".py")};imports=set()
for name,expected in pins.items():
 path=root/name
 try: info=path.lstat()
 except FileNotFoundError: raise SystemExit("MISSING:"+name)
 mode=0o600 if name in {"nlu-k2-development-corpus-v1.json","nlu-k2-shortlist-v1.json"} else 0o644
 if (not stat.S_ISREG(info.st_mode) or info.st_uid!=value["uid"] or info.st_nlink!=1
     or stat.S_IMODE(info.st_mode)!=mode): raise SystemExit("CUSTODY:"+name)
 raw=path.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=expected: raise SystemExit("PIN:"+name)
 if name.endswith(".py"):
  tree=ast.parse(raw,filename=name)
  for node in ast.walk(tree):
   if isinstance(node,ast.Import): imports.update(a.name.split(".",1)[0] for a in node.names)
   elif isinstance(node,ast.ImportFrom) and node.level==0 and node.module: imports.add(node.module.split(".",1)[0])
missing=sorted(name for name in imports if name.startswith("nlu_") and name not in modules)
if missing: raise SystemExit("DEPENDENCY:"+",".join(missing))
print(json.dumps({"runtime_files":len(pins),"runtime_location":"lxc110","dependencies":"complete"},sort_keys=True))'''
    payload = {"root": "/usr/local/libexec/local-ai-lease/full-inference-pilot",
               "pins": dict(spec.runtime_pins), "uid": expected_uid}
    result = runner(("pct", "exec", "110", "--", "/usr/bin/python3", "-B",
                     "-c", script), input=json.dumps(payload), capture_output=True,
                    text=True, timeout=30, check=False)
    try:
        value = json.loads(result.stdout)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError("K2 guest runtime validation failed") from exc
    if (result.returncode != 0 or value != {
            "runtime_files": len(spec.runtime_pins),
            "runtime_location": "lxc110", "dependencies": "complete"}):
        raise ValueError("K2 guest runtime validation failed")
    return value


def validate_inactive_target(pilot_root: Path, *, unit_root: Path | None = None,
                             expected_uid: int = 0,
                             workload_id: str = "sa3-expanded-source-quality-v1",
                             guest_runner=subprocess.run) -> dict[str, object]:
    """Validate a root-owned, inert SA3 installation without executing it.

    The dependency-closure check is intentional.  A workload cannot become
    admitted merely because its named files hash correctly while one of
    their local imports is omitted from the registration.
    """
    spec = workload(workload_id)
    root = Path(pilot_root)
    if spec.runner_kind == "m3-k2-shortlist-arbitration-development":
        target = _validate_k2_guest_target(spec, expected_uid=expected_uid,
                                           runner=guest_runner)
    else:
        for name, expected in spec.runtime_pins:
            path = root / name
            try:
                stat = path.lstat()
            except FileNotFoundError as exc:
                raise ValueError(f"target file missing:{name}") from exc
            if (not path.is_file() or path.is_symlink() or stat.st_uid != expected_uid
                    or stat.st_nlink != 1 or hashlib.sha256(path.read_bytes()).hexdigest() != expected):
                raise ValueError(f"target pin or custody mismatch:{name}")

        local_modules = {Path(name).stem for name, _ in spec.runtime_pins if name.endswith(".py")}
        imports = set()
        for name, _ in spec.runtime_pins:
            if name.endswith(".py"):
                imports.update(_local_imports(root / name))
        registered_local_modules = {
            Path(name).stem for item in WORKLOADS.values()
            for name, _ in item.runtime_pins if name.endswith(".py")
        }
        missing = sorted(name for name in imports
                         if name in registered_local_modules and name not in local_modules)
        if missing:
            raise ValueError("unregistered local dependency:" + ",".join(missing))
        target = {"runtime_files": len(spec.runtime_pins),
                  "runtime_location": "host", "dependencies": "complete"}

    unit_root = Path("/etc/systemd/system") if unit_root is None else Path(unit_root)
    target_prefix = unit_root / f"aster-lab-hours-booking-{spec.workload_id}"
    for suffix in (".service", ".timer"):
        if (target_prefix.with_suffix(suffix)).exists():
            raise ValueError(f"target unit must remain inactive:{suffix}")
    return {"workload_id": spec.workload_id, **target,
            "target_units": "absent", "effects": "not-attempted"}


validate_registry()
