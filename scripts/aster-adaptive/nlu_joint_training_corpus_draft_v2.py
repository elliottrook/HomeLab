"""Build the natural-language M3 J1 corpus candidate v2.

Unlike v1, every request is individually written.  There is no Cartesian
template expansion.  This remains a synthetic, non-authoritative draft until
semantic review and all private-corpus non-overlap receipts pass.
"""

from __future__ import annotations

import argparse
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
    (("change-request", "internal", (), "ambiguous", "clarify", "ambiguous"), (
        "Could you fix that for me?", "Please update the thing we discussed.",
        "Can you sort out the broken bit?", "I'd like that changed, please.",
        "Please fix the earlier issue.", "Could you repair it when you get a chance?",
        "Please adjust the setting from before.", "Can you deal with that problem?",
        "I'd like you to modify the previous item.", "Please correct whatever went wrong there.",
        "Could you put that back the way it should be?", "Change the part I mentioned earlier.",
        "Can you apply the fix to that one?", "Please revise the thing that's causing trouble.",
        "Would you update it for me?", "Could you make the necessary change there?",
        "Please repair the component we were talking about.", "Can you straighten out that earlier problem?",
        "I'd like the old setting corrected.", "Please patch the affected part.",
        "Could you take care of that change?", "Restore the configuration we discussed earlier.",
        "Please fix the item I pointed out.", "Can you alter that as we discussed?",
        "Could you resolve the issue with it?",
    )),
    (("general-answer", "public", (), "ambiguous", "clarify", "ambiguous"), (
        "Could you explain that?", "What does the thing you mentioned mean?",
        "Why is that important?", "Tell me more about the earlier topic.",
        "Can you give me some background on it?", "How does that work?",
        "What should I know about the subject?", "Could you unpack that idea for me?",
        "Why did it happen?", "Can you describe the previous point in plain English?",
        "What's the story behind that?", "I'd like a clearer explanation of the topic.",
        "Could you put that into context?", "What are the main facts about it?",
        "Can you elaborate on what you just referred to?", "Why does the subject matter?",
        "Could you walk me through that concept?", "What caused the thing we discussed?",
        "Help me understand the previous subject.", "Can you summarize what that is?",
        "What makes it significant?", "I'm missing some context; what subject are we discussing?",
        "Give me an overview of the topic from before.", "What exactly are you referring to there?",
        "Which topic should I be learning about?",
    )),
    (("household-command", "internal", (), "ambiguous", "clarify", "ambiguous"), (
        "Turn that off.", "Switch the other one on.", "Could you dim it a little?",
        "Stop the device over there.", "Please close that one.",
        "Make it warmer in here.", "Can you lower the thing beside it?",
        "Turn the nearby one up.", "Please open that instead.", "Turn that appliance off for me.",
        "Could you switch that back on?", "Set the other blind halfway.",
        "Please make it quieter.", "Turn off whichever one is running.",
        "Can you adjust the thermostat over there?", "Close the other one.", "Please stop it now.",
        "Switch on the one in the other room.", "Could you lower that one?",
        "Make the device less bright.", "Please raise it a bit.",
        "Turn the second one off.", "Can you open it?", "Put that on the usual setting.",
        "Could you make the one by the window less intense?",
    )),
    (("change-request", "internal", ("backup.delete",), "clear", "deny", "policy-denied"), (
        "Delete the only backup of the server.", "Erase our last recovery archive.",
        "Remove the sole snapshot we could roll back to.", "Permanently discard the final disaster-recovery copy.",
        "Destroy the only remaining database backup.", "Wipe the last known-good system image.",
        "Please delete our one usable restore point.", "Get rid of the final copy of the NAS configuration.",
        "Remove the only off-site backup we have.", "Erase the last archive that contains this project.",
        "Delete the sole recovery copy of the virtual machine.", "Destroy the final checkpoint for the storage pool.",
        "Please wipe the only backup of the service data.", "Permanently remove the last retained snapshot.",
        "Discard our sole rollback image.", "Delete the one remaining copy of the encrypted backup.",
        "Erase the only archive that could restore the service.", "Remove the final backup before making a replacement.",
        "Destroy the last recovery bundle for the host.", "Wipe our sole copy of yesterday's backup.",
        "Please delete the only valid backup set.", "Get rid of the last restorable version.",
        "Destroy the recovery image even though it is the only one that boots.", "Permanently erase the sole recovery checkpoint.",
        "Delete the last backup even though there isn't another copy.",
    )),
    (("external-research", "personal", ("calendar.read", "web.publish"), "clear", "deny", "policy-denied"), (
        "Publish my private calendar on a public webpage.", "Post all my appointments to an open forum.",
        "Put my family schedule on a site anyone can access.", "Upload my confidential meeting diary to a public page.",
        "Share my personal calendar entries on social media.", "Expose my private appointments through an unauthenticated link.",
        "Copy my full calendar into a public message board.", "Publish the details of my medical appointments online.",
        "Post my children's schedule to a public website.", "Make my private meeting notes and times publicly searchable.",
        "Upload my personal event list where anyone can read it.", "Send my confidential calendar to an open community forum.",
        "Create a public page containing all my upcoming appointments.", "Put my private work schedule on the open web.",
        "Publish my home calendar without requiring a login.", "Share every personal reminder in my calendar publicly.",
        "Post my travel itinerary from the calendar on a public site.", "Expose my family's private events through an open feed.",
        "Upload my appointment history to a publicly indexed page.", "Make my confidential schedule available to anonymous visitors.",
        "Publish my personal meeting locations on the internet.", "Copy my private calendar entries into a public blog post.",
        "Post the contents of my calendar in an open chat room.", "Put my complete personal schedule on a public online noticeboard.",
        "Share my private calendar with the whole internet.",
    )),
    (("external-research", "personal", ("calendar.read", "web.read", "local.join"), "clear", "route", "understood"), (
        "Compare my calendar with the public festival schedule.", "Check my appointments against the conference programme online.",
        "Find public concerts that don't conflict with my personal schedule.", "Match my meeting diary to the published train timetable.",
        "Cross-reference my calendar with the museum's opening hours.", "See which public lectures fit around my appointments.",
        "Compare my travel dates with the airline's public schedule.", "Check my personal events against the community calendar.",
        "Find a public library event that fits my free evening.", "Reconcile my meeting times with the published venue programme.",
        "Look for public workshops that don't overlap my calendar.", "Compare my weekend plans with the city's event listing.",
        "Check whether the public tour times clash with my appointments.", "Match my availability to the conference's online timetable.",
        "Find a theatre performance that works with my schedule.", "Cross-check my diary against the public ferry timetable.",
        "Compare my calendar with the posted school-event schedule.", "Find public classes that fit between my meetings.",
        "Check my appointment times against the clinic's public hours.", "Match my free slots to the recreation centre's programme.",
        "Compare my trip calendar with the published exhibition dates.", "Find a public market time that doesn't conflict with my plans.",
        "Check my schedule against the public council-meeting calendar.", "Reconcile my availability with the online seminar timetable.",
        "Find public events I can attend without moving my appointments.",
    )),
    (("read-only-investigation", "personal", ("calendar.read",), "clear", "route", "understood"), (
        "What's on my calendar tomorrow?", "Show me next week's meetings.",
        "Do I have any appointments left today?", "List my events for Saturday.",
        "Check when my next dentist appointment is.", "Read out my calendar for this afternoon.",
        "What time is my first meeting on Monday?", "Show my upcoming reminders.",
        "Tell me whether I'm free tomorrow evening.", "Look up my appointments for the end of the month.",
        "Which meetings are on my calendar this morning?", "Check my schedule for the long weekend.",
        "Show me the events I've booked for Friday.", "When is my next calendar entry?",
        "List everything on my personal calendar today.", "Do I have a meeting around lunchtime?",
        "Read my schedule for the coming week.", "Check whether Tuesday afternoon is open in my calendar.",
        "What appointments do I have after work?", "Show the next three events in my calendar.",
        "Tell me what's scheduled for tomorrow morning.", "Look up the date of my next medical appointment.",
        "Am I free between two and four today?", "List my calendar reminders for this weekend.",
        "Check what I have planned for Wednesday.",
    )),
    (("general-answer", "public", ("facts.answer",), "clear", "route", "understood"), (
        "How do solar eclipses happen?", "Who discovered penicillin?",
        "Explain plate tectonics in simple terms.", "When did the Renaissance begin?",
        "Why do leaves change colour in autumn?", "How does photosynthesis work?",
        "What causes ocean tides?", "Tell me why the sky appears blue.",
        "Who wrote The Origin of Species?", "What is the difference between weather and climate?",
        "How are volcanic islands formed?", "Why do we have leap years?",
        "What led to the fall of the Roman Empire?", "Explain how vaccines train the immune system.",
        "Where does the Earth's magnetic field come from?", "What is a black hole?",
        "How does a bill become law in Canada?", "Why does ice float on water?",
        "Who developed the first practical telephone?", "What causes the northern lights?",
        "How do bees communicate with one another?", "When was the printing press invented?",
        "What makes a planet a dwarf planet?", "Explain the water cycle.",
        "Why are there different time zones?",
    )),
    (("household-command", "internal", ("home.control",), "clear", "route", "understood"), (
        "Turn on the hallway lamp.", "Switch off the living-room fan.",
        "Dim the dining-room lights to thirty percent.", "Close the blind in the study.",
        "Open the kitchen shade.", "Set the bedroom thermostat to nineteen degrees.",
        "Turn off the porch light.", "Raise the living-room blinds.",
        "Make the kitchen lights warmer.", "Start the ceiling fan in the bedroom.",
        "Turn on the entryway light.", "Lower the nursery blind halfway.",
        "Switch on the lamp beside the sofa.", "Turn the bathroom extractor fan off.",
        "Set the dining-room lights to reading brightness.", "Open the living-room curtains.",
        "Make the office a little cooler.", "Turn off every light downstairs.",
        "Set the front hall lamp to fifty percent.", "Close the curtains in the guest room.",
        "Switch the patio lights on.", "Stop the fan in the study.",
        "Raise the kitchen shade all the way.", "Warm the lounge to twenty-one degrees.",
        "Turn the bedside light off.",
    )),
    (("change-request", "internal", ("lab.change",), "clear", "route", "understood"), (
        "Restart the test web service.", "Update the staging container to the approved build.",
        "Reload the lab proxy configuration.", "Deploy the approved authentication patch to the sandbox worker.",
        "Set the development database connection pool to twenty connections.", "Set the test API request timeout to thirty seconds.",
        "Restart the integration-test runner.", "Upgrade the lab dashboard package.",
        "Change the staging service's log level to debug.", "Roll the development container back to the previous image.",
        "Reload nginx in the test environment.", "Install the approved certificate on the lab endpoint.",
        "Set the sandbox job queue concurrency to four workers.", "Restart the development cache service.",
        "Deploy the feature/login-fix branch to the internal test site.", "Set the lab worker's memory limit to two gigabytes.",
        "Rebuild the staging search index.", "Rotate the test service onto its standby instance.",
        "Set the development proxy's upstream timeout to sixty seconds.", "Restart the sandbox database replica.",
        "Set LOG_LEVEL to info in the lab container's environment file.", "Reload the test message broker.",
        "Set the staging health-check interval to thirty seconds.", "Install jq in the development image.",
        "Restart the lab authentication stub.",
    )),
    (("read-only-investigation", "internal", ("lab.read",), "clear", "route", "understood"), (
        "Is the Proxmox host healthy?", "Show me the latest backup-service status.",
        "Check the lab gateway logs for errors.", "Report the current state of the storage pool.",
        "Did HomeLab Doctor find anything overnight?", "Read the health report for the test cluster.",
        "Check whether the staging proxy is responding.", "Show recent warnings from the development database.",
        "How much free space is left on the backup volume?", "Tell me whether the sandbox worker is running.",
        "Inspect the latest logs from the lab API.", "Check the current replication status.",
        "Is the internal test site reachable?", "Show the uptime of the development container.",
        "Report any failed services on the lab host.", "Check whether last night's backup completed.",
        "Read the current temperature sensors on the server.", "Show the latest storage scrub result.",
        "Is the lab certificate close to expiring?", "Check the queue depth on the test broker.",
        "Report the current CPU load on the hypervisor.", "Show me the most recent Doctor summary.",
        "Check whether the development replica is caught up.", "Show the lab firewall's current health status.",
        "Tell me if the test worker has restarted recently.",
    )),
    (("household-command", "internal", ("timer.control",), "clear", "route", "understood"), (
        "Set a five-minute timer.", "Start a thirty-minute laundry timer.",
        "Cancel the kitchen countdown.", "Stop the timer that's ringing.",
        "Create a ten-second timer for the tea.", "Set a timer for twenty-five minutes.",
        "Pause the oven timer.", "Resume the workout countdown.",
        "Add two minutes to the current timer.", "Set a one-hour timer as a reminder.",
        "Cancel the timer named Bread.", "How about a fifteen-minute countdown?",
        "Set a timer to go off in ninety seconds.", "Stop every active timer.",
        "Create a three-minute brushing timer.", "Start a forty-five-minute focus timer.",
        "Please cancel the nap timer.", "Set a six-minute timer for the pasta.",
        "Resume the paused kitchen timer.", "Begin a twenty-second countdown.",
        "Remove five minutes from the laundry timer.", "Set a timer for an hour and a half.",
        "Delete the countdown with two minutes remaining.", "Start a twelve-minute timer for the rice.",
        "Stop the bedroom timer.",
    )),
    (("external-research", "public", ("web.read",), "clear", "route", "understood"), (
        "What's the latest public weather forecast for Vancouver?", "Look up today's transit timetable.",
        "Find the current museum opening hours online.", "Check the OpenVINO release notes.",
        "Search for the library's holiday schedule.", "Find the latest public air-quality report for Vancouver.",
        "Look up the ferry cancellations for today.", "Check the city's website for road closures.",
        "Find the current admission price for the aquarium.", "Search online for this weekend's public events.",
        "Look up the newest stable Python release.", "Check the park's public trail conditions.",
        "Find the posted schedule for the farmers' market.", "Search for the latest Bank of Canada rate announcement.",
        "Look up the public agenda for the next council meeting.", "Check whether the community centre is open tonight.",
        "Find the latest Ubuntu security notice.", "Search the airline's site for its baggage rules.",
        "Look up the current exchange rate published by the bank.", "Check this afternoon's train status.",
        "Find the gallery's exhibition dates online.", "Search for the most recent official wildfire update for British Columbia.",
        "Look up the official recycling schedule for the Kitsilano neighbourhood.", "Check the public documentation for the new API version.",
        "Find the latest election results from the official site.",
    )),
    (("unsupported", "internal", (), "clear", "abstain", "unsupported"), (
        "At what minute will the lab server fail next?", "Show me storage-array logs from before logging was enabled.",
        "Name the hypervisor component that will cause the next outage before any diagnostics exist.", "Fill in the network telemetry for the period when the switch was powered off.",
        "Give me next Christmas's backup-host state as a complete JSON record.", "Which disk serial number will be the first to fail next year?",
        "Show the server's history from before the server was installed.", "Answer yes or no: will the lab server ever crash again?",
        "Give me the complete packet bytes that will trigger the next network fault.", "Chart CPU load for the month before any CPU metrics were collected.",
        "What will the CPU temperature be, to a tenth of a degree, at noon next June?", "Write the storage pool's next scrub report word for word.",
        "Show the contents of a log file that was not created.", "At what second will the UPS battery die?",
        "Name the next service to fail and the time it will happen.", "Restore a configuration that was never created or applied anywhere.",
        "State the root cause of the next lab outage before it occurs.", "Promise that every future backup will be free of corruption.",
        "Plot performance metrics for the week before metric collection began.", "Give me the dates and times of all host restarts next year.",
        "Provide the router's configuration one year from now, byte for byte.", "Show an audit trail for actions that no system recorded.",
        "Give the remaining lifetime of each SSD to the nearest day.", "Write tomorrow's error log verbatim.",
        "Restore Tuesday's snapshot even though no snapshot was taken that day.",
    )),
    (("unsupported", "personal", (), "clear", "abstain", "unsupported"), (
        "What is my neighbour thinking about me right now?", "What does my colleague secretly think of the project?",
        "Show me the diary my friend considered writing but did not write.", "How will every part of my family's private life unfold?",
        "Read the message another person thought about sending but never sent.", "Tell me which childhood memory my partner has never described.",
        "What did a stranger dream about last night?", "Show me my neighbour's medical history even though no record exists.",
        "Which private decision will my friend make next year?", "What opinion has my colleague chosen not to express?",
        "Describe the dream my relative had without asking or observing them.", "Show me private photos from an event nobody photographed.",
        "What is another person feeling when there is no evidence to go on?", "How will my friend's relationships develop over the rest of their life?",
        "Write out the private conversation two people imagined but never had.", "What is going through my neighbour's mind across the street?",
        "Reveal the contents of my colleague's email that was never written.", "What secret plans has my colleague made without telling or recording them?",
        "Recover a memory another person neither remembers nor ever recorded.", "When will my friend decide to change careers?",
        "Describe the private decision my sibling has not made yet.", "Show someone's private browsing history from a device they never used.",
        "Tell me the unspoken secrets of a person I have never met.", "Which private choices will my neighbour make over the next decade?",
        "Describe a family member's dream that they never recorded or mentioned.",
    )),
    (("unsupported", "public", (), "clear", "abstain", "unsupported"), (
        "What numbers will win next week's lottery?", "What will this stock be worth to the cent one year from today?",
        "Quote tomorrow morning's leading headline word for word.", "Name the next federal election winner and final vote count.",
        "What will the final score be in Saturday's championship game?", "Give the coordinates of the next major earthquake before it occurs.",
        "Give the hour-by-hour weather here on this date five years from now.", "List every film that will win next season's major awards.",
        "At what value will the market close next Friday, down to the cent?", "Name the tournament winner before the first match is played.",
        "Give the date and time of the next volcanic eruption.", "Quote tomorrow night's leading news story before it is written.",
        "Give the final score of next month's championship before it is played.", "Give the date and time when people will first land on Mars.",
        "Name the next new species scientists will discover before they find it.", "Quote the verdict in the court's next major case before it is issued.",
        "Give each side's final vote count in the future referendum.", "Give the coordinates where the next tornado will touch down.",
        "What will gold cost to the cent ten years from today?", "List every recipient of next year's Nobel prizes before selections begin.",
        "Describe the next major scientific discovery before anyone makes it.", "What will tomorrow's exchange rate be to six decimal places?",
        "Rank the world's largest companies in 2040 and give their revenues.", "What path will the tropical storm take before it has formed?",
        "Name the winner and vote margin of the election that has not yet been called.",
    )),
)


def build() -> dict:
    cases = []
    for label_index, (key, phrases) in enumerate(DESIGNS):
        if len(phrases) != 25 or len(set(phrases)) != 25:
            raise ValueError("J1 v2 designs require 25 unique phrases per label")
        label_id = LABELS[key]
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
    raw = canonical(build())
    summary = boundary.validate_corpus(
        raw, {"development-v1": args.public_reference.read_bytes()}
    )
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
