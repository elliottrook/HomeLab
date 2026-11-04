"""Build the preregistered, effect-free J2 natural-language corpus candidate.

The builder has no model, network, training, routing, or deployment behavior.
It accepts the eight exposed reference corpora explicitly and delegates all
custody, balance, ontology, and non-overlap checks to ``nlu_j2_corpus_v1``.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import re
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
WORD = re.compile(r"[a-z0-9']+")
MIN_UNIQUE_FOUR_TOKEN_PREFIXES = 850
MAX_FOUR_TOKEN_PREFIX_REUSE = 4


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
          ("Please change {x}.", "Could {x} be updated?", "Adjust {x} for me, please.",
           "{x} needs modification; can you handle it?", "Reconfigure {x} for me.",
           "Change {x} for me.")),
    _spec(_label_id(family="general-answer", sensitivity="public", capabilities=[],
                    ambiguity="ambiguous", disposition="clarify", reason="ambiguous"),
          ("that idea", "the earlier claim", "this term", "the second point", "that process",
           "the concept above", "the former method", "that example", "this subject", "the last topic"),
          ("Explain {x}.", "What does {x} mean?", "{x}: describe it for me.",
           "{x}: add more detail, please.", "How does {x} work?", "Clarify {x} for me.")),
    _spec(_label_id(family="household-command", sensitivity="internal", capabilities=[],
                    ambiguity="ambiguous", disposition="clarify", reason="ambiguous"),
          ("the light over there", "that appliance", "the other switch", "the device upstairs",
           "that room", "the one near it", "the usual lamp", "that thermostat",
           "the thing in the hall", "the equipment we mentioned"),
          ("Turn {x} off.", "Switch {x} on.", "Adjust {x} for me.",
           "Set {x} to my usual preference.", "Toggle {x}.", "Please adjust {x}.")),
    _spec(_label_id(family="change-request", sensitivity="internal", capabilities=["backup.delete"],
                    ambiguity="clear", disposition="deny", reason="policy-denied"),
          ("the retired database snapshots", "all mail-server archives", "yesterday's NAS snapshot",
           "the off-site photo backups", "the finance-share archives", "the oldest VM archives",
           "the workstation recovery images", "the weekly configuration backups",
           "the media-library snapshots", "the encrypted laptop backups"),
          ("Delete {x} permanently.", "Remove {x} with no recovery copy.",
           "Erase {x} from backup storage.", "Purge {x} now.",
           "Destroy {x}, including every retained copy.", "Delete {x} to free storage.")),
    _spec(_label_id(family="external-research", sensitivity="personal",
                    capabilities=["calendar.read", "web.publish"], ambiguity="clear",
                    disposition="deny", reason="policy-denied"),
          ("my medical appointments", "my children's school schedule", "my private work meetings",
           "my therapy sessions", "my upcoming travel plans", "my job interview times",
           "my family commitments", "my legal consultation dates", "my personal reminders",
           "my calendar for next month"),
          ("Publish {x} on a public website.", "Post {x} publicly.",
           "Copy {x} to a public page.", "Expose {x} to everyone online.",
           "Announce {x} on the open web.", "Make {x} publicly accessible.")),
    _spec(_label_id(family="external-research", sensitivity="personal",
                    capabilities=["calendar.read", "web.read", "local.join"], ambiguity="clear",
                    disposition="route", reason="understood"),
          ("a conference", "my scheduled hiking trip", "a concert I plan to attend",
           "my next dentist appointment", "a family reunion", "my booked train journey",
           "an upcoming client visit", "my reserved museum day", "a class on my schedule",
           "my planned volunteer shift"),
          ("{x} is on my calendar; research it online and summarize it privately.",
           "Research {x}, then merge the findings with my calendar.",
           "Compare {x} with current web information and my calendar.",
           "Research {x} online and join the findings with its calendar time.",
           "Summarize {x} using web research plus my calendar.",
           "For {x}, combine current web information with my calendar.")),
    _spec(_label_id(family="read-only-investigation", sensitivity="personal",
                    capabilities=["calendar.read"], ambiguity="clear", disposition="route",
                    reason="understood"),
          ("my first meeting tomorrow", "my appointments on Friday", "the next event on my calendar",
           "my free time this afternoon", "my meetings after lunch", "my weekend commitments",
           "my earliest event next week", "my calendar entries for Tuesday", "my evening plans",
           "my scheduled calls today"),
          ("Summarize {x} for me.", "Check {x}.", "{x}: give me the details.",
           "Look up {x}.", "Find {x} without changing anything.", "Summarize {x}.")),
    _spec(_label_id(family="general-answer", sensitivity="public", capabilities=["facts.answer"],
                    ambiguity="clear", disposition="route", reason="understood"),
          ("why leaves change colour", "how a compass points north", "what causes ocean tides",
           "how rainbows form", "why the sky appears blue", "how yeast makes bread rise",
           "what a prime number is", "why seasons change", "how sound travels", "what photosynthesis does"),
          ("Explain {x}.", "Fact-check {x} for me.", "Teach me about {x}.",
           "Describe {x} in more depth.", "Describe {x} in plain language.",
           "Break down {x}.")),
    _spec(_label_id(family="household-command", sensitivity="internal",
                    capabilities=["home.control"], ambiguity="clear", disposition="route",
                    reason="understood"),
          ("turn off the pantry light", "switch on the porch lamp", "dim the dining-room lights to forty percent",
           "set the bedroom thermostat to nineteen degrees", "close the living-room blinds",
           "turn on the kitchen fan", "lock the back door", "open the study blinds",
           "set the hallway light to warm white", "lower the den thermostat by two degrees"),
          ("Please {x}.", "Can you {x}?", "Go ahead and {x}.", "Would you {x}?",
           "Right now, {x}.", "{x}, using the home controls.")),
    _spec(_label_id(family="change-request", sensitivity="internal", capabilities=["lab.change"],
                    ambiguity="clear", disposition="route", reason="understood"),
          ("restart the staging dashboard container", "increase the test VM's memory to four gigabytes",
           "disable the unused sandbox account", "apply the approved DNS change",
           "rotate the development service's local token", "add the test host to the monitoring group",
           "update the lab proxy's configuration", "create a snapshot of the staging VM",
           "enable metrics on the development database", "rename the temporary lab network"),
          ("Please {x}.", "For the lab, {x}.", "Can you {x}?", "Safely {x}.",
           "Within the lab, {x}.", "Proceed to {x}.")),
    _spec(_label_id(family="read-only-investigation", sensitivity="internal",
                    capabilities=["lab.read"], ambiguity="clear", disposition="route",
                    reason="understood"),
          ("the disk usage on the staging host", "which containers are running in the lab",
           "the test database's current version", "recent errors from the development proxy",
           "the lab VM's assigned memory", "the status of the internal DNS resolver",
           "the monitoring state of the sandbox host", "the current lab network routes",
           "the staging service's uptime", "the test cluster's node inventory"),
          ("Check {x} without making changes.", "Inspect {x}.", "Report {x} to me.",
           "Summarize {x} without changes.", "Look up {x}.",
           "Read {x} without making changes.")),
    _spec(_label_id(family="household-command", sensitivity="internal",
                    capabilities=["timer.control"], ambiguity="clear", disposition="route",
                    reason="understood"),
          ("a twelve-minute pasta timer", "the laundry timer for thirty minutes", "a five-minute tea timer",
           "the oven timer for forty-five minutes", "a twenty-minute exercise timer",
           "the ten-minute bread timer", "a ninety-second stretch timer",
           "the kitchen timer", "a one-hour study timer", "the sprinkler timer"),
          ("Start {x}.", "Set {x}.", "Create {x} now.", "Begin {x}.",
           "Pause {x}.", "Cancel {x}.")),
    _spec(_label_id(family="external-research", sensitivity="public", capabilities=["web.read"],
                    ambiguity="clear", disposition="route", reason="understood"),
          ("today's weather in Victoria", "the current ferry schedule to Nanaimo", "recent images from Mars",
           "this week's local theatre listings", "the latest stable Python release", "current wildfire advisories",
           "today's exchange rate for euros", "the next public lunar eclipse", "recent municipal election results",
           "the opening hours of the science museum"),
          ("Search online for {x}.", "Find {x} online.", "Research {x} online.",
           "Verify {x} using reliable websites.", "Look up {x}.",
           "Web-search {x} and summarize the findings.")),
    _spec(_label_id(family="unsupported", sensitivity="internal", capabilities=[], ambiguity="clear",
                    disposition="abstain", reason="unsupported"),
          ("carry the server rack across the room", "solder a loose connector inside the router",
           "replace the cracked window in the workshop", "label every cable in the cabinet",
           "clean dust from the lab's ceiling vents", "move the heavy UPS onto the top shelf",
           "drill mounting holes in the network closet", "repair the broken latch on the equipment case",
           "deliver the spare switch to the office", "paint the inside of the utility room"),
          ("Please {x}.", "Could you {x}?", "{x}; this requires a person.",
           "At the lab, {x}.", "Physically {x}.",
           "Before tonight, {x}.")),
    _spec(_label_id(family="unsupported", sensitivity="personal", capabilities=[], ambiguity="clear",
                    disposition="abstain", reason="unsupported"),
          ("drive me to my medical appointment", "cut my hair before dinner", "pick up my prescription",
           "carry my suitcase through the airport", "sign my private legal form for me",
           "give me a physical examination", "walk my dog while I am away", "cook my prescribed meal at my home",
           "repair the clasp on my wedding necklace", "hand-deliver my private letter"),
          ("Please {x}.", "Could you {x}?", "{x}; this requires a person.",
           "Come over and {x}.", "Personally {x}.", "Today, {x}.")),
    _spec(_label_id(family="unsupported", sensitivity="public", capabilities=[], ambiguity="clear",
                    disposition="abstain", reason="unsupported"),
          ("plant a tree in the public park", "carry the town's parade banner", "repair a bench at the bus stop",
           "direct traffic at the community festival", "paint the public library's front door",
           "deliver paper flyers across downtown", "sweep the pavement outside city hall",
           "install a sculpture in the civic plaza", "referee the neighbourhood football match",
           "collect litter along the public trail"),
          ("Please {x}.", "Could you {x}?", "{x}; this requires a person.",
           "Volunteer to {x}.", "Physically {x}.", "This afternoon, {x}.")),
)


# Validation subjects use distinct sentence frames so the learner cannot pass
# by memorizing the exact six training openings for each label.
VALIDATION_TEMPLATES = (
    ("Could you alter {x}?", "Please revise {x}.",
     "Update {x}, if you know which one I mean.", "I want {x} changed.",
     "Handle the change to {x}.", "Fix {x} for me."),
    ("What is {x}?", "Can you clarify {x}?", "I need context about {x}.",
     "Please unpack {x}.", "Why is {x} important?", "Summarize {x} for me."),
    ("Switch {x} off.", "Please turn {x} on.", "Dim {x}.",
     "Change {x} now.", "Set {x} differently.", "Operate {x} for me."),
    ("Wipe {x} permanently.", "Discard {x} without another copy.",
     "Remove every recovery copy of {x}.", "Erase {x}, leaving no restore point.",
     "Delete {x} even though no other copies remain.",
     "Destroy {x} with no replacement backup."),
    ("Put {x} on an open website.", "Share {x} publicly.",
     "Publish a public post containing {x}.",
     "Expose {x} through an unauthenticated page.",
     "Send {x} to a public forum.", "Make an open webpage from {x}."),
    ("Cross-check {x} with current online information and my calendar.",
     "Research {x} online, then align it with my calendar.",
     "Prepare a private combined calendar and web brief for {x}.",
     "Join my calendar timing for {x} with public web details.",
     "Use both my calendar and web sources to summarize {x}.",
     "Privately combine online findings about {x} with its scheduled time."),
    ("Read my calendar details for {x}.", "Show me {x} from my calendar.",
     "Check whether my calendar contains {x}.", "Find every scheduled time for {x}.",
     "What does my calendar say about {x}?", "Report {x} from my calendar."),
    ("What is the explanation for {x}?", "Teach me the basics of {x}.",
     "Give a factual summary of {x}.", "Please explain this topic: {x}.",
     "Describe the science behind {x}.", "Answer a basic question about {x}."),
    ("Use the home system to {x}.", "Now {x}.", "Would you please {x}?",
     "Carry out this home command: {x}.", "From Home Assistant, {x}.",
     "Go ahead: {x}."),
    ("Carry out this lab change: {x}.", "On the test systems, {x}.",
     "Please make the lab do this: {x}.", "Apply this staging change: {x}.",
     "Execute the approved lab action to {x}.",
     "Change the lab by doing this: {x}."),
    ("Read and report {x}.", "Give me a read-only view of {x}.",
     "Without changing anything, inspect {x}.", "Show the current value of {x}.",
     "Retrieve {x} from the lab.", "Audit {x} without making changes."),
    ("Activate {x}.", "Schedule {x}.", "Make {x}.", "Run {x}.",
     "Stop {x} temporarily.", "Remove {x}."),
    ("Look online for {x}.", "Check the web for {x}.",
     "Find recent sources about {x}.", "Research current information on {x}.",
     "Browse public sources for {x}.", "Get an online update about {x}."),
    ("Go and {x}.", "Can someone {x}?", "This physical lab task needs doing: {x}.",
     "{x}; a person must do this.", "At the site, please {x}.",
     "Arrange for someone to {x}."),
    ("Come and {x}.", "Can somebody {x}?", "This personal physical task needs doing: {x}.",
     "{x}; a person must do this.", "Please visit and {x}.",
     "Arrange in-person help to {x}."),
    ("Go outside and {x}.", "Can a volunteer {x}?",
     "This public physical task needs doing: {x}.", "{x}; a person must do this.",
     "At the public site, {x}.", "Arrange for someone to {x}."),
)
if len(VALIDATION_TEMPLATES) != len(SPECS):  # pragma: no cover
    raise RuntimeError("J2 validation frames do not cover every label")


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def _sentence(template: str, subject: str) -> str:
    text = template.format(x=subject)
    return text[:1].upper() + text[1:]


def naturalness(raw: bytes) -> dict[str, int]:
    value = json.loads(raw)
    cases = value.get("cases") if isinstance(value, dict) else None
    if not isinstance(cases, list) or len(cases) != 960:
        raise ValueError("J2 naturalness gate requires exactly 960 cases")
    prefixes = Counter()
    word_counts = []
    for case in cases:
        words = WORD.findall(case["text"].casefold())
        if not 3 <= len(words) <= 30:
            raise ValueError("J2 corpus contains implausible request length")
        prefixes[" ".join(words[:4])] += 1
        word_counts.append(len(words))
    if len(prefixes) < MIN_UNIQUE_FOUR_TOKEN_PREFIXES:
        raise ValueError("J2 corpus repeats too many four-token openings")
    if max(prefixes.values()) > MAX_FOUR_TOKEN_PREFIX_REUSE:
        raise ValueError("J2 corpus overuses one four-token opening")
    return {
        "unique_four_token_prefixes": len(prefixes),
        "max_four_token_prefix_reuse": max(prefixes.values()),
        "minimum_word_count": min(word_counts),
        "maximum_word_count": max(word_counts),
    }


def build_corpus(references: dict[str, bytes]) -> tuple[bytes, dict[str, object]]:
    """Return exact corpus bytes and the boundary validator's content-free summary."""
    if not isinstance(references, dict) or tuple(sorted(references)) != tuple(sorted(REFERENCE_ARGUMENTS)):
        raise ValueError("J2 builder requires the eight named reference corpora")
    cases = []
    for label_index, (label_id, subjects, train_templates) in enumerate(SPECS):
        for subject_index, subject in enumerate(subjects):
            split = "train" if subject_index < 8 else "validation"
            templates = (train_templates if split == "train"
                         else VALIDATION_TEMPLATES[label_index])
            for template_index, template in enumerate(templates):
                ordinal = subject_index * len(templates) + template_index
                cases.append({
                    "id": f"j2-{split}-l{label_index:02d}-case-{ordinal:02d}",
                    "split": split,
                    "text": _sentence(template, subject),
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
    summary = boundary.validate_corpus(raw, references)
    summary.update(naturalness(raw))
    return raw, summary


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
