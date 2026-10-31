"""Build the exact synthetic draft for the M3 J1 corpus custodian.

The draft is not a training release.  It requires later independent label
review and seven content-free non-overlap receipts before training may begin.
"""

from __future__ import annotations

import argparse
import itertools
import json
import os
from pathlib import Path

import nlu_joint_training_corpus_v1 as boundary
import nlu_whole_label_choice_v1 as ontology


def _key(label: dict) -> tuple:
    return (
        label["request_family"], label["sensitivity"],
        tuple(label["capability_needs"]), label["ambiguity"],
        label["disposition"], label["reason"],
    )


LABELS = {_key(label): label_id for label_id, label in ontology.CATALOGUE.items()}


DESIGNS = (
    (("change-request", "internal", (), "ambiguous", "clarify", "ambiguous"),
     ("Please repair {x} for me", "Could you update {x}", "Make {x} work again",
      "Change {x} when you can", "Sort out {x} please"),
     ("that", "the earlier thing", "what we discussed", "the broken part", "the problem")),
    (("general-answer", "public", (), "ambiguous", "clarify", "ambiguous"),
     ("Could you explain {x}", "What can you tell me about {x}", "Describe {x} for me",
      "Why is {x} important", "Give me the background on {x}"),
     ("that", "the previous topic", "what I mentioned", "the subject", "it")),
    (("household-command", "internal", (), "ambiguous", "clarify", "ambiguous"),
     ("Switch {x} off", "Turn {x} on", "Lower {x}", "Stop {x}", "Adjust {x}"),
     ("that one", "the device", "it over there", "the thing nearby", "the other one")),
    (("change-request", "internal", ("backup.delete",), "clear", "deny", "policy-denied"),
     ("Delete {x}", "Erase {x}", "Destroy {x}", "Remove {x}", "Permanently discard {x}"),
     ("the sole recovery archive", "our only server backup", "the last snapshot",
      "the only rollback checkpoint", "the final disaster recovery copy")),
    (("external-research", "personal", ("calendar.read", "web.publish"), "clear", "deny", "policy-denied"),
     ("Publish {x} on a public website", "Upload {x} to an open forum",
      "Post {x} on a public page", "Send {x} to a public message board",
      "Expose {x} through an unauthenticated site"),
     ("my private appointments", "my personal calendar entries", "my confidential schedule",
      "my family calendar records", "my private meeting details")),
    (("external-research", "personal", ("calendar.read", "web.read", "local.join"), "clear", "route", "understood"),
     ("Compare {x} with the public festival schedule", "Cross-check {x} against the public event listing",
      "Combine {x} with the public conference timetable", "Match {x} to the public venue programme",
      "Reconcile {x} with the public community calendar"),
     ("my calendar", "my appointments", "my personal schedule", "my meeting diary", "my event list")),
    (("read-only-investigation", "personal", ("calendar.read",), "clear", "route", "understood"),
     ("Read {x} from my calendar", "Show {x} in my calendar", "Inspect {x} on my calendar",
      "List {x} from my calendar", "Check {x} in my calendar"),
     ("tomorrow's appointments", "next week's meetings", "today's remaining events",
      "my upcoming reminders", "the weekend schedule")),
    (("general-answer", "public", ("facts.answer",), "clear", "route", "understood"),
     ("Explain {x}", "Who discovered {x}", "When did {x} happen", "What causes {x}", "How does {x} work"),
     ("plate tectonics", "penicillin", "the Renaissance", "a solar eclipse", "photosynthesis in plants")),
    (("household-command", "internal", ("home.control",), "clear", "route", "understood"),
     ("Turn on {x}", "Switch off {x}", "Dim {x}", "Raise {x}", "Close {x}"),
     ("the hallway lamp", "the living room fan", "the dining room lights",
      "the study blind", "the kitchen shade")),
    (("change-request", "internal", ("lab.change",), "clear", "route", "understood"),
     ("Restart {x}", "Update {x}", "Reconfigure {x}", "Deploy a patch to {x}", "Reload {x}"),
     ("the test web service", "the staging container", "the lab proxy",
      "the development database", "the sandbox worker")),
    (("read-only-investigation", "internal", ("lab.read",), "clear", "route", "understood"),
     ("Read the status of {x}", "Show the latest health report for {x}", "Inspect the logs for {x}",
      "Check whether {x} is healthy", "Report the current state of {x}"),
     ("the Proxmox host", "the backup service", "the lab gateway", "the storage pool", "the Doctor monitor")),
    (("household-command", "internal", ("timer.control",), "clear", "route", "understood"),
     ("Set {x}", "Start {x}", "Create {x}", "Cancel {x}", "Stop {x}"),
     ("a five minute timer", "the kitchen countdown", "a half hour timer",
      "the laundry timer", "a ten second countdown")),
    (("external-research", "public", ("web.read",), "clear", "route", "understood"),
     ("Find the latest public information about {x}", "Look up the current public report on {x}",
      "Search online for the newest public {x}", "Read the public release notes for {x}",
      "Check the public website for {x}"),
     ("Vancouver weather", "the OpenVINO release", "the transit timetable",
      "the museum opening hours", "the library holiday schedule")),
    (("unsupported", "internal", (), "clear", "abstain", "unsupported"),
     ("Predict the exact future failure time of {x}", "Recover the never-recorded history of {x}",
      "Guarantee the next outage date for {x}", "Tell me the unknowable future state of {x}",
      "Reconstruct nonexistent telemetry from {x}"),
     ("the lab server", "the storage array", "the network switch", "the backup host", "the hypervisor")),
    (("unsupported", "personal", (), "clear", "abstain", "unsupported"),
     ("Read the unspoken thoughts of {x}", "Predict the exact private future of {x}",
      "Recover the never-written diary of {x}", "Tell me the unknowable memories of {x}",
      "Reveal the nonexistent private messages of {x}"),
     ("my neighbour", "my colleague", "my friend", "a family member", "another person")),
    (("unsupported", "public", (), "clear", "abstain", "unsupported"),
     ("Predict {x}", "Guarantee {x}", "Reveal {x}", "State {x}", "Provide {x}"),
     ("next week's winning lottery numbers", "the exact stock price next year",
      "tomorrow's unknowable headline", "the result of an event that never occurs",
      "a guaranteed future election result")),
)


def build() -> dict:
    cases = []
    for label_index, (key, frames, items) in enumerate(DESIGNS):
        label_id = LABELS[key]
        phrases = [frame.format(x=item) for frame, item in itertools.product(frames, items)]
        if len(phrases) != 25 or len(set(phrases)) != 25:
            raise ValueError("J1 draft design must produce 25 unique cases per label")
        for index, text in enumerate(phrases):
            split = "train" if index < boundary.TRAIN_PER_LABEL else "validation"
            cases.append({
                "id": f"j1-{split}-label-{label_index:02d}-case-{index:02d}",
                "split": split,
                "text": text,
                "label_id": label_id,
            })
    return {
        "schema": boundary.SCHEMA,
        "data_class": boundary.DATA_CLASS,
        "evidence_class": boundary.EVIDENCE_CLASS,
        "ontology_sha256": boundary.ontology_sha256(),
        "custodian": boundary.CUSTODIAN,
        "authority": boundary.AUTHORITY,
        "cases": cases,
    }


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    value = build()
    raw = canonical(value)
    summary = boundary.validate_corpus(raw, {"development-v1": args.public_reference.read_bytes()})
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
