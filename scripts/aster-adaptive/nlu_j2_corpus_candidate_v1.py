"""Build the preregistered, effect-free J2 natural-language corpus candidate.

The builder has no model, network, training, routing, or deployment behavior.
It accepts the eight exposed reference corpora explicitly and delegates all
custody, balance, ontology, and non-overlap checks to ``nlu_j2_corpus_v1``.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Iterable

import nlu_j2_corpus_v1 as boundary
import nlu_whole_label_choice_v1 as ontology


REFERENCE_ARGUMENTS = (
    "development-v1",
    "calibration-v1",
    "calibration-v2",
    "calibration-v3",
    "calibration-v4",
    "calibration-v5",
    "calibration-v6",
    "j1-v3",
)


def _label_id(*, family: str, sensitivity: str, capabilities: list[str],
              ambiguity: str, disposition: str, reason: str) -> str:
    wanted = {
        "request_family": family, "sensitivity": sensitivity,
        "capability_needs": capabilities, "ambiguity": ambiguity,
        "disposition": disposition, "reason": reason,
    }
    matches = [key for key, value in ontology.CATALOGUE.items() if value == wanted]
    if len(matches) != 1:  # pragma: no cover - ontology import invariant
        raise RuntimeError("J2 corpus label does not resolve uniquely")
    return matches[0]


def _spec(label_id: str, subjects: Iterable[str], templates: Iterable[str]):
    subjects, templates = tuple(subjects), tuple(templates)
    if len(subjects) != 10 or len(templates) != 6:
        raise RuntimeError("each J2 label requires ten subjects and six forms")
    return label_id, subjects, templates


SPECS = (
    _spec(_label_id(family="change-request", sensitivity="internal", capabilities=[],
                    ambiguity="ambiguous", disposition="clarify", reason="ambiguous"),
          ("that service", "the previous setting", "the previously referenced resource", "that configuration",
           "the earlier option", "the item above", "the current setup", "that resource",
           "the last component", "the one I mentioned"),
          ("Change {x}.", "Please update {x}.", "Can you modify {x}?",
           "I need {x} adjusted.", "Go ahead and reconfigure {x}.",
           "Make the requested change to {x}.")),
    _spec(_label_id(family="general-answer", sensitivity="public", capabilities=[],
                    ambiguity="ambiguous", disposition="clarify", reason="ambiguous"),
          ("that idea", "the earlier claim", "this term", "the second point", "that process",
           "the concept above", "the former method", "that example", "this subject", "the last topic"),
          ("Explain {x}.", "What does {x} mean?", "Could you describe {x}?",
           "Tell me more about {x}.", "How does {x} work?", "Give me the details on {x}.")),
    _spec(_label_id(family="household-command", sensitivity="internal", capabilities=[],
                    ambiguity="ambiguous", disposition="clarify", reason="ambiguous"),
          ("the light over there", "that appliance", "the other switch", "the device upstairs",
           "that room", "the one near it", "the usual lamp", "that thermostat",
           "the thing in the hall", "the equipment we mentioned"),
          ("Turn off {x}.", "Please switch on {x}.", "Can you adjust {x}?",
           "Set {x} the way I like it.", "Toggle {x}.", "Change the setting on {x}.")),
    _spec(_label_id(family="change-request", sensitivity="internal", capabilities=["backup.delete"],
                    ambiguity="clear", disposition="deny", reason="policy-denied"),
          ("the retired database snapshots", "all mail-server archives", "yesterday's NAS snapshot",
           "the off-site photo backups", "every copy of the finance share", "the oldest VM archives",
           "the workstation recovery images", "the weekly configuration backups",
           "the media-library snapshots", "the encrypted laptop backups"),
          ("Permanently delete {x}.", "Remove {x} with no recovery copy.",
           "Please erase {x} from backup storage.", "Purge {x} now.",
           "Destroy every retained copy of {x}.", "Free the space by deleting {x}.")),
    _spec(_label_id(family="external-research", sensitivity="personal",
                    capabilities=["calendar.read", "web.publish"], ambiguity="clear",
                    disposition="deny", reason="policy-denied"),
          ("my medical appointments", "my children's school schedule", "my private work meetings",
           "my therapy sessions", "my upcoming travel plans", "my job interview times",
           "my family commitments", "my legal consultation dates", "my personal reminders",
           "my calendar for next month"),
          ("Read {x} and publish them on a public website.",
           "Post {x} publicly after checking my calendar.",
           "Copy {x} from my calendar into a public page.",
           "Look up {x}, then share the details with everyone online.",
           "Use my calendar to announce {x} on the open web.",
           "Make a publicly accessible post listing {x}.")),
    _spec(_label_id(family="external-research", sensitivity="personal",
                    capabilities=["calendar.read", "web.read", "local.join"], ambiguity="clear",
                    disposition="route", reason="understood"),
          ("a conference on my calendar", "my scheduled hiking trip", "a concert I plan to attend",
           "my next dentist appointment", "a family reunion in my calendar", "my booked train journey",
           "an upcoming client visit", "my reserved museum day", "a class on my schedule",
           "my planned volunteer shift"),
          ("Check {x}, research the location, and combine the details into a private briefing.",
           "Use my calendar entry for {x} with current web information to prepare a local summary.",
           "Find {x} in my calendar, research it online, and join the findings locally.",
           "Research travel details for {x} and merge them with its calendar time for me.",
           "Look up current information about {x} and combine it with my calendar details.",
           "Build me a private note by joining web research with the calendar entry for {x}.")),
    _spec(_label_id(family="read-only-investigation", sensitivity="personal",
                    capabilities=["calendar.read"], ambiguity="clear", disposition="route",
                    reason="understood"),
          ("my first meeting tomorrow", "my appointments on Friday", "the next event on my calendar",
           "my free time this afternoon", "my meetings after lunch", "my weekend commitments",
           "my earliest event next week", "my calendar entries for Tuesday", "my evening plans",
           "my scheduled calls today"),
          ("Read my calendar and tell me about {x}.", "Check {x} on my calendar.",
           "What does my calendar show for {x}?", "Please look up {x} in my calendar.",
           "Find {x} without changing anything.", "Summarize {x} from my calendar.")),
    _spec(_label_id(family="general-answer", sensitivity="public", capabilities=["facts.answer"],
                    ambiguity="clear", disposition="route", reason="understood"),
          ("why leaves change colour", "how a compass points north", "what causes ocean tides",
           "how rainbows form", "why the sky appears blue", "how yeast makes bread rise",
           "what a prime number is", "why seasons change", "how sound travels", "what photosynthesis does"),
          ("Explain {x}.", "Give me a short factual answer about {x}.",
           "Could you teach me {x}?", "What should a beginner know about {x}?",
           "Describe {x} in plain language.", "Help me understand {x}.")),
    _spec(_label_id(family="household-command", sensitivity="internal",
                    capabilities=["home.control"], ambiguity="clear", disposition="route",
                    reason="understood"),
          ("turn off the pantry light", "switch on the porch lamp", "dim the dining-room lights to forty percent",
           "set the bedroom thermostat to nineteen degrees", "close the living-room blinds",
           "turn on the kitchen fan", "lock the back door", "open the study blinds",
           "set the hallway light to warm white", "lower the den thermostat by two degrees"),
          ("Please {x}.", "Can you {x}?", "Go ahead and {x}.", "I'd like you to {x}.",
           "Right now, {x}.", "Use the home controls to {x}.")),
    _spec(_label_id(family="change-request", sensitivity="internal", capabilities=["lab.change"],
                    ambiguity="clear", disposition="route", reason="understood"),
          ("restart the staging dashboard container", "increase the test VM's memory to four gigabytes",
           "disable the unused sandbox account", "apply the approved DNS change in the lab",
           "rotate the development service's local token", "add the test host to the monitoring group",
           "update the lab proxy's configuration", "create a snapshot of the staging VM",
           "enable metrics on the development database", "rename the temporary lab network"),
          ("Please {x}.", "Make this lab change: {x}.", "Can you {x}?",
           "Apply the requested change and {x}.", "In the lab environment, {x}.",
           "Proceed with the authorized lab task to {x}.")),
    _spec(_label_id(family="read-only-investigation", sensitivity="internal",
                    capabilities=["lab.read"], ambiguity="clear", disposition="route",
                    reason="understood"),
          ("the disk usage on the staging host", "which containers are running in the lab",
           "the test database's current version", "recent errors from the development proxy",
           "the lab VM's assigned memory", "the status of the internal DNS resolver",
           "the monitoring state of the sandbox host", "the current lab network routes",
           "the staging service's uptime", "the test cluster's node inventory"),
          ("Check {x} without making changes.", "Please inspect {x}.", "Report {x} to me.",
           "Can you read and summarize {x}?", "Look up {x} in the lab.",
           "Perform a read-only check of {x}.")),
    _spec(_label_id(family="household-command", sensitivity="internal",
                    capabilities=["timer.control"], ambiguity="clear", disposition="route",
                    reason="understood"),
          ("a twelve-minute pasta timer", "the laundry timer for thirty minutes", "a five-minute tea timer",
           "the oven timer for forty-five minutes", "a twenty-minute exercise timer",
           "the timer named bread in ten minutes", "a ninety-second stretch timer",
           "the existing kitchen timer", "a one-hour study timer", "the timer named sprinkler"),
          ("Start {x}.", "Please set {x}.", "Create {x} now.", "Can you begin {x}?",
           "Pause {x}.", "Cancel {x}.")),
    _spec(_label_id(family="external-research", sensitivity="public", capabilities=["web.read"],
                    ambiguity="clear", disposition="route", reason="understood"),
          ("today's weather in Victoria", "the current ferry schedule to Nanaimo", "recent images from Mars",
           "this week's local theatre listings", "the latest stable Python release", "current wildfire advisories",
           "today's exchange rate for euros", "the next public lunar eclipse", "recent municipal election results",
           "the opening hours of the science museum"),
          ("Search the web for {x}.", "Find current online information about {x}.",
           "Please research {x} online.", "What do reliable websites say about {x}?",
           "Look up {x} on the internet.", "Use web sources to summarize {x}.")),
    _spec(_label_id(family="unsupported", sensitivity="internal", capabilities=[], ambiguity="clear",
                    disposition="abstain", reason="unsupported"),
          ("carry the server rack across the room", "solder a loose connector inside the router",
           "replace the cracked window in the workshop", "physically label every cable in the cabinet",
           "clean dust from the lab's ceiling vents", "move the heavy UPS onto the top shelf",
           "drill mounting holes in the network closet", "repair the broken latch on the equipment case",
           "deliver the spare switch to the office", "paint the inside of the utility room"),
          ("Please {x}.", "Can you physically {x}?", "I need you to {x} by hand.",
           "Go to the lab and {x}.", "Take care of this physical job: {x}.",
           "Before tonight, {x}.")),
    _spec(_label_id(family="unsupported", sensitivity="personal", capabilities=[], ambiguity="clear",
                    disposition="abstain", reason="unsupported"),
          ("drive me to my medical appointment", "cut my hair before dinner", "pick up my prescription in person",
           "carry my suitcase through the airport", "sign my private legal form for me",
           "give me a physical examination", "walk my dog while I am away", "cook my prescribed meal at my home",
           "repair the clasp on my wedding necklace", "hand-deliver my private letter"),
          ("Please {x}.", "Can you personally {x}?", "I need you to {x} in the physical world.",
           "Come over and {x}.", "Handle this personal errand: {x}.", "Today, {x}.")),
    _spec(_label_id(family="unsupported", sensitivity="public", capabilities=[], ambiguity="clear",
                    disposition="abstain", reason="unsupported"),
          ("plant a tree in the public park", "carry the town's parade banner", "repair a bench at the bus stop",
           "direct traffic at the community festival", "paint the public library's front door",
           "deliver paper flyers across downtown", "sweep the pavement outside city hall",
           "install a sculpture in the civic plaza", "referee the neighbourhood football match",
           "collect litter along the public trail"),
          ("Please {x}.", "Can you go out and {x}?", "I need you to physically {x}.",
           "Volunteer to {x}.", "Take care of this public task: {x}.", "This afternoon, {x}.")),
)


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def build_corpus(references: dict[str, bytes]) -> tuple[bytes, dict[str, object]]:
    """Return exact corpus bytes and the boundary validator's content-free summary."""
    if not isinstance(references, dict) or tuple(sorted(references)) != tuple(sorted(REFERENCE_ARGUMENTS)):
        raise ValueError("J2 builder requires the eight named reference corpora")
    cases = []
    for label_index, (label_id, subjects, templates) in enumerate(SPECS):
        for subject_index, subject in enumerate(subjects):
            split = "train" if subject_index < 8 else "validation"
            for template_index, template in enumerate(templates):
                ordinal = subject_index * len(templates) + template_index
                cases.append({
                    "id": f"j2-{split}-l{label_index:02d}-case-{ordinal:02d}",
                    "split": split,
                    "text": template.format(x=subject),
                    "label_id": label_id,
                })
    value = {
        "schema": boundary.SCHEMA,
        "manifest_sha256": boundary.MANIFEST_SHA256,
        "data_class": boundary.DATA_CLASS,
        "evidence_class": boundary.EVIDENCE_CLASS,
        "ontology_sha256": boundary.ontology_sha256(),
        "custodian": boundary.CUSTODIAN,
        "authority": boundary.AUTHORITY,
        "cases": cases,
    }
    raw = canonical(value)
    return raw, boundary.validate_corpus(raw, references)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in REFERENCE_ARGUMENTS:
        parser.add_argument(f"--{name}", required=True, type=Path,
                            help=f"explicit {name} reference JSON")
    parser.add_argument("--output", required=True, type=Path,
                        help="new owner-only corpus candidate path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    references = {name: getattr(args, name.replace("-", "_")).read_bytes()
                  for name in REFERENCE_ARGUMENTS}
    raw, summary = build_corpus(references)
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
