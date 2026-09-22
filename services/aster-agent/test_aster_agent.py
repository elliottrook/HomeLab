import tempfile
import time
import unittest
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from pydantic import ValidationError

from aster_agent import (
    ASTER_SYSTEM_PROMPT,
    DEFAULT_PERSONA,
    PERSONAS,
    ArrRepairExecutionRequest,
    ChatRequest,
    TOOLS,
    chat,
    execute_arr_repair,
    execute_tool,
    get_lab_health,
    normalized_messages,
    personas,
    preload_read_only_context,
    require_api_key,
    search_knowledge,
    select_tools,
)


class AsterAgentTests(unittest.TestCase):
    def test_system_policy_leads_with_requested_facts(self):
        self.assertIn("every explicitly requested fact or identifier", ASTER_SYSTEM_PROMPT)
        self.assertIn("before optional", ASTER_SYSTEM_PROMPT)

    def test_system_policy_frontloads_runtime_and_recovery_dependencies(self):
        self.assertIn("Qwen3.8-27B on the B60 Vulkan path", ASTER_SYSTEM_PROMPT)
        self.assertIn("Always identify it explicitly as `VM 105`", ASTER_SYSTEM_PROMPT)
        self.assertIn("Aster is not the\nfirst recovery dependency", ASTER_SYSTEM_PROMPT)
        self.assertIn("independent local access", ASTER_SYSTEM_PROMPT)

    def test_credential_policy_omits_product_specific_recovery_details(self):
        self.assertIn("give only that generic refusal", ASTER_SYSTEM_PROMPT)
        self.assertIn("do not add product-specific UI", ASTER_SYSTEM_PROMPT)

    def test_system_policy_labels_bounded_health_source(self):
        self.assertIn("latest sanitized", ASTER_SYSTEM_PROMPT)
        self.assertIn("read-only HomeLab Doctor summary", ASTER_SYSTEM_PROMPT)

    def test_system_policy_frontloads_authority_conflicts(self):
        self.assertIn("first sentence must include both `conflict`", ASTER_SYSTEM_PROMPT)
        self.assertIn("and `current-operational`", ASTER_SYSTEM_PROMPT)

    def test_arr_broker_drop_in_has_no_execution_switch_or_radarr_credential(self):
        drop_in = (
            Path(__file__).with_name("systemd") / "aster-arr-broker.conf"
        ).read_text(encoding="utf-8")
        self.assertIn("EnvironmentFile=/etc/aster/arr-broker.env", drop_in)
        self.assertIn("ASTER_ARR_BROKER_URL=http://192.168.20.40:9421", drop_in)
        self.assertNotIn("ASTER_ARR_EXECUTION_ENABLED", drop_in)
        self.assertNotIn("RADARR_API_KEY", drop_in)

    def test_casual_chat_has_no_tools(self):
        self.assertEqual(select_tools([{"role": "user", "content": "Tell me a short joke"}]), [])

    def test_streaming_request_is_supported(self):
        request = ChatRequest(messages=[{"role": "user", "content": "Hello"}], stream=True)
        self.assertTrue(request.stream)

    def test_homelab_question_selects_knowledge(self):
        names = [tool["function"]["name"] for tool in select_tools([{"role": "user", "content": "What GPU is in my homelab?"}])]
        self.assertIn("search_knowledge", names)

    def test_inventory_serial_question_selects_knowledge(self):
        names = [
            tool["function"]["name"]
            for tool in select_tools(
                [{"role": "user", "content": "What is the serial number of the unassigned APC UPS?"}]
            )
        ]
        self.assertIn("search_knowledge", names)

    def test_authority_question_selects_knowledge(self):
        names = [
            tool["function"]["name"]
            for tool in select_tools(
                [{"role": "user", "content": "Which reviewed reference is authoritative when a project diary disagrees?"}]
            )
        ]
        self.assertIn("search_knowledge", names)

    def test_arr_question_selects_knowledge(self):
        names = [
            tool["function"]["name"]
            for tool in select_tools(
                [{"role": "user", "content": "Why did Lidarr import an album but Jellyfin not show it?"}]
            )
        ]
        self.assertIn("search_knowledge", names)

    def test_current_arr_question_selects_sanitized_report(self):
        names = [
            tool["function"]["name"]
            for tool in select_tools(
                [{"role": "user", "content": "How many items are currently stuck in the Radarr queue?"}]
            )
        ]
        self.assertIn("get_arr_report", names)

    def test_current_home_assistant_question_selects_sanitized_report(self):
        names = [tool["function"]["name"] for tool in select_tools(
            [{"role": "user", "content": "Is Home Assistant Supervisor currently healthy and up to date?"}]
        )]
        self.assertIn("get_ha_report", names)
        self.assertIn("search_knowledge", names)

    def test_home_assistant_policy_is_read_only_and_private(self):
        self.assertIn("For Home Assistant, remain read-only", ASTER_SYSTEM_PROMPT)
        self.assertIn("explicit action-specific approval", ASTER_SYSTEM_PROMPT)
        self.assertNotIn("execute_home_assistant", TOOLS)
        self.assertIn("You may repeat non-sensitive names", ASTER_SYSTEM_PROMPT)
        self.assertIn("Never redirect a refused Home Assistant action", ASTER_SYSTEM_PROMPT)

    def test_current_forgejo_question_selects_only_sanitized_report_reader(self):
        names = [
            tool["function"]["name"]
            for tool in select_tools(
                [{"role": "user", "content": "What is the latest Forgejo commit and action status?"}]
            )
        ]
        self.assertIn("get_forgejo_report", names)
        self.assertFalse(any("write" in name or "update" in name for name in names))

    def test_current_netbox_question_selects_only_sanitized_report_reader(self):
        names = [
            tool["function"]["name"]
            for tool in select_tools(
                [{"role": "user", "content": "What devices are in the current NetBox inventory?"}]
            )
        ]
        self.assertIn("get_netbox_report", names)
        self.assertFalse(any("write" in name or "update" in name for name in names))

    def test_natural_language_never_selects_an_execution_tool(self):
        names = [
            tool["function"]["name"]
            for tool in select_tools(
                [{"role": "user", "content": "Execute the approved Radarr repair now"}]
            )
        ]
        self.assertNotIn("execute_arr_repair", names)
        self.assertNotIn("execute_arr_repair", TOOLS)

    def test_structured_execution_request_rejects_extra_fields(self):
        with self.assertRaises(ValidationError):
            ArrRepairExecutionRequest(
                candidate_ref="radarr-q-abcdefghijklmnop",
                url="http://unapproved.invalid",
            )

    def test_arr_policy_is_advisory_and_approval_gated(self):
        self.assertIn("advisory-only", ASTER_SYSTEM_PROMPT)
        self.assertIn("explicit action-specific\napproval", ASTER_SYSTEM_PROMPT)
        self.assertIn("album rather\nthan a single track", ASTER_SYSTEM_PROMPT)
        self.assertIn("verification and explicit review are required", ASTER_SYSTEM_PROMPT)
        self.assertIn("Do not redirect an ARR question to a live service interface", ASTER_SYSTEM_PROMPT)
        self.assertIn("request/monitor, indexer, download queue, ARR import", ASTER_SYSTEM_PROMPT)

    def test_forgejo_and_netbox_policy_is_indirect_and_read_only(self):
        self.assertIn("Forgejo and NetBox access is also read-only and indirect", ASTER_SYSTEM_PROMPT)
        self.assertIn("never contact either\nAPI", ASTER_SYSTEM_PROMPT)
        self.assertIn("excludes source code, messages, authors", ASTER_SYSTEM_PROMPT)
        self.assertIn("excludes config\ncontexts, custom fields, contacts, secrets", ASTER_SYSTEM_PROMPT)
        self.assertNotIn("create_forgejo", TOOLS)
        self.assertNotIn("update_netbox", TOOLS)

    def test_source_report_mount_is_read_only(self):
        drop_in = (Path(__file__).with_name("systemd") / "aster-source-reports.conf").read_text(encoding="utf-8")
        self.assertEqual(drop_in.strip(), "[Service]\nReadOnlyPaths=/var/lib/aster/source-reports")

    def test_lab_health_uses_only_bounded_report(self):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "latest.json"
            report.write_text(json.dumps({"generated_at": "2026-09-01T00:00:00+00:00", "status": "warning", "checks": [{"name": "Doctor", "status": "warn", "summary": "Backup is overdue"}], "secret": "not returned"}), encoding="utf-8")
            result = get_lab_health(report)
            self.assertEqual(result["status"], "warning")
            self.assertEqual(result["checks"][0]["summary"], "Backup is overdue")
            self.assertNotIn("secret", result)

    def test_invalid_lab_health_report_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "latest.json"
            report.write_text('{"status":"healthy","checks":"not-a-list"}', encoding="utf-8")
            self.assertEqual(get_lab_health(report)["status"], "unavailable")

    def test_knowledge_search_is_scoped_and_ranked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "hardware.md").write_text("The Arc Pro B60 has 24 GB VRAM.\n\nUnrelated text.", encoding="utf-8")
            result = search_knowledge("B60 VRAM", root=root)
            self.assertEqual(result["results"][0]["source"], "hardware.md")
            self.assertIn("24 GB", result["results"][0]["excerpt"])

    def test_contiguous_markdown_list_returns_relevant_chunk(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            docs = root / "docs"
            docs.mkdir()
            filler = "\n".join(f"- unrelated device {index}" for index in range(100))
            (docs / "03-Hardware-Inventory.md").write_text(
                f"{filler}\n- Arc Pro B60 24 GB\n- BAR is 256 MB; Vulkan works but Level Zero is blocked.\n",
                encoding="utf-8",
            )
            result = search_knowledge("B60 BAR", root=root)
            self.assertIn("Level Zero", result["results"][0]["excerpt"])

    def test_current_state_prefers_inventory_over_history(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            docs = root / "docs"
            projects = docs / "projects" / "completed projects"
            projects.mkdir(parents=True)
            (docs / "03-Hardware-Inventory.md").write_text(
                "The currently installed B60 has a 256 MB BAR. Level Zero is blocked; Vulkan works.",
                encoding="utf-8",
            )
            (projects / "Local-AI.md").write_text(
                "Historical B60 GPU BAR test. Vulkan pending. " * 20,
                encoding="utf-8",
            )
            result = search_knowledge("What is currently true about the B60 GPU BAR?", root=root)
            self.assertEqual(result["results"][0]["source"], "docs/03-Hardware-Inventory.md")

    def test_current_state_keeps_complementary_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            docs = root / "docs"
            reference = docs / "reference"
            projects = docs / "projects" / "completed projects"
            reference.mkdir(parents=True)
            projects.mkdir(parents=True)
            (docs / "03-Hardware-Inventory.md").write_text(
                "The current B60 GPU uses Vulkan because its physical BAR is 256 MB.",
                encoding="utf-8",
            )
            (reference / "Aster-Operations.md").write_text(
                "LXC 104 runs the Aster API. LXC 110 runs llama.cpp with Qwen3.8-27B.",
                encoding="utf-8",
            )
            (reference / "AI-Hermes-Second-Brain.md").write_text(
                "Implementation tasks: the unfinished second brain task is a restore test.",
                encoding="utf-8",
            )
            (projects / "Local-AI.md").write_text(
                "VM 105 is a historical rollback path. SYCL is blocked; Vulkan is production.",
                encoding="utf-8",
            )
            result = search_knowledge(
                "Give the current B60 GPU state, LXC 104 and LXC 110 model, why VM 105 and SYCL are not production, and the unfinished second brain task",
                max_results=4,
                root=root,
            )
            sources = [item["source"] for item in result["results"]]
            self.assertEqual(sources[0], "docs/03-Hardware-Inventory.md")
            self.assertIn("docs/reference/Aster-Operations.md", sources)
            self.assertIn("docs/reference/AI-Hermes-Second-Brain.md", sources)
            self.assertIn("docs/projects/completed projects/Local-AI.md", sources)

    def test_operational_source_has_distinct_authority(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            docs = root / "docs"
            reference = docs / "reference"
            reference.mkdir(parents=True)
            (reference / "Aster-Operations.md").write_text(
                "LXC 104 runs the Aster service with the Qwen model.", encoding="utf-8"
            )
            result = search_knowledge("Aster LXC model", root=root)
            self.assertEqual(result["results"][0]["authority"], "current_operations")

    def test_source_report_architecture_prefers_aster_operations(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            reference = root / "reference" / "operations"
            project.mkdir(parents=True)
            reference.mkdir(parents=True)
            (project / "Aster-Operations.md").write_text(
                "General Aster operations. " * 50
                + "\n### Forgejo and NetBox read-only reports\n"
                + "Aster has no API token or direct network path. Source-local producers publish sanitized reports.",
                encoding="utf-8",
            )
            (reference / "ai-local-inference.md").write_text(
                "Generic Aster inference operations. " * 100,
                encoding="utf-8",
            )
            result = search_knowledge(
                "How is the Forgejo and NetBox read-only integration built?", root=root
            )
            self.assertEqual(result["results"][0]["source"], "project/Aster-Operations.md")
            self.assertIn("no API token", result["results"][0]["excerpt"])

    def test_provenance_controls_authority_and_is_returned(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "reference/infrastructure/hardware-inventory.md"
            source.parent.mkdir(parents=True)
            source.write_text("The current B60 GPU uses Vulkan.", encoding="utf-8")
            (root / ".aster-provenance.json").write_text(
                json.dumps(
                    {
                        "sources": [
                            {
                                "destination": "reference/infrastructure/hardware-inventory.md",
                                "authority": "current-with-exclusions",
                                "reviewed": "2026-09-01",
                                "commit": "abc123",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            result = search_knowledge("What is the current B60 GPU backend?", root=root)
            item = result["results"][0]
            self.assertEqual(item["authority"], "current-with-exclusions")
            self.assertEqual(item["reviewed"], "2026-09-01")
            self.assertEqual(item["commit"], "abc123")

    def test_mirror_result_retains_human_source_route(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "mirror/entries/synthetic/claim.md"
            source.parent.mkdir(parents=True)
            source.write_text(
                "---\nsource_path: docs/upstream/synthetic/content.txt\n"
                "generator_model: deterministic-extractive\n---\n\n"
                "## Source-located claim\n\nA synthetic UPS-1000 service requires private DNS.",
                encoding="utf-8",
            )
            decoy = root / "reference/operations/general.md"
            decoy.parent.mkdir(parents=True)
            decoy.write_text("A service may require routine operational checks.", encoding="utf-8")
            memory_decoy = root / "memory/README.md"
            memory_decoy.parent.mkdir(parents=True)
            memory_decoy.write_text(
                "A mirror excerpt should state maximum current; exact amperage may be unknown.",
                encoding="utf-8",
            )
            (root / ".aster-provenance.json").write_text(json.dumps({"sources": [{
                "destination": "mirror/entries/synthetic/claim.md",
                "authority": "derived-memory", "reviewed": None,
                "commit": "mirror123",
                "human_source": "docs/upstream/synthetic/content.txt",
                "source_locator": "lines 4-4",
            }, {
                "destination": "reference/operations/general.md",
                "authority": "current-operational", "reviewed": "2026-09-01",
                "commit": "reference123",
            }, {
                "destination": "memory/README.md",
                "authority": "derived-memory", "reviewed": "2026-09-01",
                "commit": "memory123",
            }]}), encoding="utf-8")
            item = search_knowledge("What does the synthetic service require?", root=root)["results"][0]
            self.assertEqual("derived-memory", item["authority"])
            self.assertEqual("docs/upstream/synthetic/content.txt", item["human_source"])
            self.assertEqual("lines 4-4", item["source_locator"])
            self.assertIn("A synthetic UPS-1000 service requires private DNS.", item["excerpt"])
            self.assertNotIn("generator_model", item["excerpt"])

            missing = search_knowledge("What is the UPS-1000 maximum current?", root=root)["results"][0]
            self.assertEqual("derived-memory", missing["authority"])
            self.assertEqual("docs/upstream/synthetic/content.txt", missing["human_source"])

            self.assertIn("explicitly name its supplied", ASTER_SYSTEM_PROMPT)
            self.assertIn("human_source and source_locator", ASTER_SYSTEM_PROMPT)

    def test_multi_part_query_prefers_answer_sections(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            docs = root / "docs"
            reference = docs / "reference"
            projects = docs / "projects" / "completed projects"
            reference.mkdir(parents=True)
            projects.mkdir(parents=True)
            filler = "Aster LXC inference service operational notes. " * 40
            (reference / "Aster-Operations.md").write_text(
                f"{filler}\n\n## Runtime configuration\n"
                "LXC 110 runs llama.cpp with Qwen3.8-27B UD-IQ4_XS and Vulkan.\n",
                encoding="utf-8",
            )
            (reference / "AI-Hermes-Second-Brain.md").write_text(
                f"Second brain task discussion. {filler}\n\n## Implementation tasks\n"
                "- [x] Pilot retrieval.\n- [ ] Define the knowledge boundary.\n"
                "- [ ] Test backup and restore.\n- [ ] Establish a monthly health review.\n",
                encoding="utf-8",
            )
            (projects / "Local-AI.md").write_text(
                f"SYCL Level Zero investigation. {filler}\n\n"
                "SYCL/Level Zero is blocked by the 256 MB BAR; Vulkan is production.\n",
                encoding="utf-8",
            )
            result = search_knowledge(
                "Which LXC model and inference backend are active, why is SYCL Level Zero blocked, and what unfinished second brain task is first?",
                max_results=3,
                root=root,
            )
            excerpts = {item["source"]: item["excerpt"] for item in result["results"]}
            self.assertIn("Qwen3.8-27B", excerpts["docs/reference/Aster-Operations.md"])
            self.assertIn("Define the knowledge boundary", excerpts["docs/reference/AI-Hermes-Second-Brain.md"])
            self.assertIn("Test backup and restore", excerpts["docs/reference/AI-Hermes-Second-Brain.md"])
            self.assertIn("Establish a monthly health review", excerpts["docs/reference/AI-Hermes-Second-Brain.md"])
            self.assertIn("256 MB BAR", excerpts["docs/projects/completed projects/Local-AI.md"])

    def test_arr_reference_prefers_inventory_and_automation_sections(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "reference/operations/arr-stack.md"
            source.parent.mkdir(parents=True)
            source.write_text(
                "General ARR operational context. " * 50
                + "\n## Current Service Inventory\n"
                + "| Sonarr | 4.0.19.2979 | /mnt/Media/data/media/tv | "
                + ("Sonarr inventory boundary. " * 50)
                + "\n| Radarr | 6.3.0.10514 | /mnt/Media/data/media/movies |\n"
                + "Dependency and downloader notes. " * 50
                + "\n## Automation and Mutation Map\n"
                + ("Automation boundary context. " * 60)
                + "\n"
                + "TrueNAS Cron Job 2 runs the bounded integrity automation.\n"
                + ("Built-in ARR behavior. " * 60)
                + "\nProwlarr application synchronization can change indexer definitions in connected ARR applications. "
                + "A stale connected-app key can break synchronization and downstream indexer health.\n",
                encoding="utf-8",
            )
            (root / ".aster-provenance.json").write_text(
                json.dumps(
                    {
                        "sources": [
                            {
                                "destination": "reference/operations/arr-stack.md",
                                "authority": "current-with-exclusions",
                                "reviewed": "2026-09-09",
                                "commit": "abc123",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            cases = (
                (
                    "What is the HomeLab ARR stack current state?",
                    "Sonarr inventory boundary",
                ),
                (
                    "What installed versions and ports do Sonarr and Radarr use?",
                    "4.0.19.2979",
                ),
                (
                    "When does the TrueNAS jellyfin-integrity workflow run, and what may it change?",
                    "Cron Job 2",
                ),
                (
                    "What are the Sonarr and Radarr canonical roots and downloader dependency path?",
                    "/mnt/Media/data/media/tv",
                ),
                (
                    "Sonarr says all indexers are unavailable after a Prowlarr key rotation. What is the safe diagnosis?",
                    "application synchronization",
                ),
            )
            for query, expected in cases:
                with self.subTest(query=query):
                    result = search_knowledge(query, max_results=4, root=root)
                    self.assertEqual(
                        result["results"][0]["source"],
                        "reference/operations/arr-stack.md",
                    )
                    self.assertIn(expected, " ".join(item["excerpt"] for item in result["results"]))
                    self.assertTrue(
                        all(
                            item["source"] == "reference/operations/arr-stack.md"
                            for item in result["results"]
                        )
                    )
                    self.assertEqual(result["results"][0]["reviewed"], "2026-09-09")

    def test_focused_checklist_can_return_multiple_chunks_from_one_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            docs = root / "docs"
            reference = docs / "reference"
            reference.mkdir(parents=True)
            prelude = "Second brain safeguards and implementation context. " * 20
            checklist = "\n".join(
                [
                    "## Implementation tasks",
                    "- [x] Complete the pilot.",
                    "- [x] Verify provenance.",
                    "- [x] Prefer current inventory.",
                    "- [ ] Define the knowledge boundary.",
                    "- [ ] Test backup and restore.",
                    "- [ ] Establish a monthly health review.",
                    "- [ ] Define document capture.",
                ]
            )
            (reference / "AI-Hermes-Second-Brain.md").write_text(
                f"{prelude}\n{checklist}\n", encoding="utf-8"
            )
            result = search_knowledge(
                "Search the Aster Second-Brain implementation checklist for the first three unchecked tasks",
                max_results=4,
                root=root,
            )
            self.assertTrue(result["results"])
            self.assertEqual(
                {item["source"] for item in result["results"]},
                {"docs/reference/AI-Hermes-Second-Brain.md"},
            )
            combined = " ".join(item["excerpt"] for item in result["results"])
            self.assertIn("Define the knowledge boundary", combined)
            self.assertIn("Test backup and restore", combined)
            self.assertIn("Establish a monthly health review", combined)

    def _mirror_fixture(self, root: Path, sources: dict[str, list[str]], directories: dict | None = None):
        """Build a minimal mirror/ tree: sources maps source_id -> list of
        entry body texts. directories, if given, is written verbatim as
        indexes/directories.json (omit to leave it absent, for the
        missing-index fallback case)."""
        entries_root = root / "mirror/entries"
        for source_id, bodies in sources.items():
            source_dir = entries_root / source_id
            source_dir.mkdir(parents=True)
            for index, body in enumerate(bodies, 1):
                (source_dir / f"{source_id}-{index:03d}.md").write_text(
                    f"---\nschema_version: 1\nsource_id: \"{source_id}\"\nauthority: \"derived-memory\"\n---\n\n"
                    f"## Source-located claim\n\n{body}\n",
                    encoding="utf-8",
                )
        provenance = {
            "schema_version": 1,
            "sources": [
                {"destination": f"mirror/entries/{source_id}/{source_id}-{index:03d}.md", "authority": "derived-memory"}
                for source_id, bodies in sources.items() for index in range(1, len(bodies) + 1)
            ],
        }
        (root / ".aster-provenance.json").write_text(json.dumps(provenance), encoding="utf-8")
        if directories is not None:
            index_dir = root / "mirror/indexes"
            index_dir.mkdir(parents=True)
            (index_dir / "directories.json").write_text(json.dumps({"schema_version": 1, "entries": directories}), encoding="utf-8")

    def test_directory_first_narrows_to_the_correct_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._mirror_fixture(
                root,
                sources={
                    "sonarr-docs": ["Sonarr manages TV episode downloads and notification connections."],
                    "opnsense-docs": ["OPNsense configures the firewall, DHCP address leases and connection state."],
                },
                directories={
                    "sonarr-docs": {"entry_count": 1, "abstract": "1 verified entries from sonarr-docs, most frequently covering: sonarr, episodes, downloads.", "topics": ["sonarr", "episodes", "downloads"]},
                    "opnsense-docs": {"entry_count": 1, "abstract": "1 verified entries from opnsense-docs, most frequently covering: firewall, dhcp, address.", "topics": ["firewall", "dhcp", "address"]},
                },
            )
            result = search_knowledge("How do I add a notification connection in Sonarr?", root=root, directory_first=True)
            self.assertTrue(result["results"])
            self.assertEqual({item["source"] for item in result["results"]}, {"mirror/entries/sonarr-docs/sonarr-docs-001.md"})

    def test_directory_first_falls_back_when_index_is_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._mirror_fixture(
                root,
                sources={"sonarr-docs": ["Sonarr manages TV episode downloads."]},
                directories=None,
            )
            flat = search_knowledge("Sonarr episode downloads", root=root, directory_first=False)
            narrowed = search_knowledge("Sonarr episode downloads", root=root, directory_first=True)
            self.assertEqual(flat, narrowed)
            self.assertTrue(narrowed["results"])

    def test_directory_first_falls_back_when_abstract_is_stale(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._mirror_fixture(
                root,
                sources={"sonarr-docs": ["Sonarr manages TV episode downloads."]},
                directories={
                    # Recorded entry_count (5) no longer matches the single
                    # real entry file on disk: this directory entry must be
                    # distrusted for narrowing, not used to (wrongly) confirm
                    # or restrict anything.
                    "sonarr-docs": {"entry_count": 5, "abstract": "stale", "topics": ["sonarr"]},
                },
            )
            flat = search_knowledge("Sonarr episode downloads", root=root, directory_first=False)
            narrowed = search_knowledge("Sonarr episode downloads", root=root, directory_first=True)
            self.assertEqual(flat, narrowed)
            self.assertTrue(narrowed["results"])

    def test_directory_first_falls_back_when_no_source_scores(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._mirror_fixture(
                root,
                sources={"sonarr-docs": ["Sonarr manages TV episode downloads."]},
                directories={
                    "sonarr-docs": {"entry_count": 1, "abstract": "1 verified entries from sonarr-docs, most frequently covering: episodes, downloads.", "topics": ["episodes", "downloads"]},
                },
            )
            # A query with no topic overlap at all against the only source's
            # abstract must still fall back to a real (flat) search rather
            # than returning nothing.
            flat = search_knowledge("What UPS battery runtime remains?", root=root, directory_first=False)
            narrowed = search_knowledge("What UPS battery runtime remains?", root=root, directory_first=True)
            self.assertEqual(flat, narrowed)

    def test_directory_first_never_narrows_reference_tier_content(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._mirror_fixture(
                root,
                sources={"sonarr-docs": ["Sonarr manages TV episode downloads."]},
                directories={
                    "sonarr-docs": {"entry_count": 1, "abstract": "1 verified entries from sonarr-docs, most frequently covering: sonarr, episodes, downloads.", "topics": ["sonarr", "episodes", "downloads"]},
                },
            )
            (root / "docs").mkdir()
            (root / "docs/03-Hardware-Inventory.md").write_text(
                "The currently installed B60 GPU has 24 GB VRAM.", encoding="utf-8",
            )
            # Narrowing is scoped to mirror/entries/; a reference-tier file
            # outside that tree must never be excluded by it.
            result = search_knowledge("What is currently true about the B60 GPU VRAM?", root=root, directory_first=True)
            self.assertEqual(result["results"][0]["source"], "docs/03-Hardware-Inventory.md")

class AsterPreloadTests(unittest.IsolatedAsyncioTestCase):
    async def test_time_tool_is_preloaded_without_model_round_trip(self):
        result = await preload_read_only_context(
            [{"role": "user", "content": "What time is it?"}],
            [TOOLS["get_current_time"]],
        )
        self.assertEqual(result[0]["function"], "get_current_time")
        self.assertEqual(result[0]["result"]["timezone"], "America/Vancouver")

    async def test_search_tool_uses_explicit_directory_feature_flag(self):
        with (
            patch("aster_agent.DIRECTORY_FIRST", True),
            patch("aster_agent.search_knowledge", return_value={"results": []}) as search,
        ):
            await execute_tool("search_knowledge", {"query": "Sonarr notifications", "max_results": 2})
        self.assertEqual(search.call_args.kwargs["directory_first"], True)

    async def test_arr_report_is_preloaded_without_model_round_trip(self):
        result = await preload_read_only_context(
            [{"role": "user", "content": "What is currently stuck in the Radarr queue?"}],
            [TOOLS["get_arr_report"]],
        )
        self.assertEqual(result[0]["function"], "get_arr_report")

    async def test_forgejo_and_netbox_reports_are_preloaded_without_model_round_trip(self):
        with (
            patch("aster_agent.read_forgejo_report", return_value={"source": "forgejo"}),
            patch("aster_agent.read_netbox_report", return_value={"source": "netbox"}),
        ):
            result = await preload_read_only_context(
                [{"role": "user", "content": "Show current Forgejo and NetBox inventory status"}],
                [TOOLS["get_forgejo_report"], TOOLS["get_netbox_report"]],
            )
        self.assertEqual([item["function"] for item in result], ["get_forgejo_report", "get_netbox_report"])


class FakeBrokerResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self.payload = payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("test response error")

    def json(self):
        return self.payload


class FakeAsyncClient:
    response = None
    requests = []

    def __init__(self, *args, **kwargs):
        self.timeout = kwargs.get("timeout")

    async def __aenter__(self):
        return self

    async def __aexit__(self, *unused):
        return False

    async def post(self, url, *, headers, json):
        type(self).requests.append((url, headers, json, self.timeout))
        return type(self).response


class ArrRepairExecutionTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.reference = "radarr-q-abcdefghijklmnop"
        self.report = {
            "generated_at": "2026-09-09T12:00:00Z",
            "repair_candidates": [
                {
                    "operation": "dismiss_stale_radarr_queue_record",
                    "service": "radarr",
                    "candidate_ref": self.reference,
                    "expires_at": "2026-09-09T12:05:00Z",
                }
            ],
        }
        self.result = {
            "operation": "dismiss_stale_radarr_queue_record",
            "candidate_ref": self.reference,
            "decision": "approved_execute",
            "report_age_seconds": 1,
            "result": "dismissed",
            "at": "2026-09-09T12:00:01+00:00",
        }
        FakeAsyncClient.requests = []
        FakeAsyncClient.response = FakeBrokerResponse(200, self.result)

    async def test_structured_endpoint_sends_only_report_issued_fields(self):
        with (
            patch("aster_agent.read_arr_report", return_value=self.report),
            patch("aster_agent.ARR_BROKER_URL", "http://broker.internal"),
            patch("aster_agent.ARR_BROKER_KEY", "broker-key"),
            patch("aster_agent.httpx.AsyncClient", FakeAsyncClient),
        ):
            response = await execute_arr_repair(self.reference)
        self.assertEqual(response, {"status": "completed", "audit": self.result})
        url, headers, payload, timeout = FakeAsyncClient.requests[0]
        self.assertEqual(url, "http://broker.internal/v1/execute")
        self.assertEqual(timeout, 40)
        self.assertEqual(
            set(payload),
            {"operation", "service", "candidate_ref", "report_generated_at"},
        )
        self.assertEqual(headers, {"Authorization": "Bearer broker-key"})

    async def test_candidate_absence_never_contacts_broker(self):
        with patch(
            "aster_agent.read_arr_report",
            return_value={"generated_at": "2026-09-09T12:00:00Z", "repair_candidates": []},
        ):
            with self.assertRaises(HTTPException) as raised:
                await execute_arr_repair(self.reference)
        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(FakeAsyncClient.requests, [])

    async def test_broker_denial_is_sanitized(self):
        FakeAsyncClient.response = FakeBrokerResponse(403, {"private": "must not surface"})
        with (
            patch("aster_agent.read_arr_report", return_value=self.report),
            patch("aster_agent.ARR_BROKER_URL", "http://broker.internal"),
            patch("aster_agent.ARR_BROKER_KEY", "broker-key"),
            patch("aster_agent.httpx.AsyncClient", FakeAsyncClient),
        ):
            with self.assertRaises(HTTPException) as raised:
                await execute_arr_repair(self.reference)
        self.assertEqual(raised.exception.status_code, 409)
        self.assertNotIn("private", str(raised.exception.detail))

    async def test_invalid_broker_audit_is_not_returned(self):
        FakeAsyncClient.response = FakeBrokerResponse(
            200,
            {**self.result, "at": "private response detail", "report_age_seconds": 901},
        )
        with (
            patch("aster_agent.read_arr_report", return_value=self.report),
            patch("aster_agent.ARR_BROKER_URL", "http://broker.internal"),
            patch("aster_agent.ARR_BROKER_KEY", "broker-key"),
            patch("aster_agent.httpx.AsyncClient", FakeAsyncClient),
        ):
            with self.assertRaises(HTTPException) as raised:
                await execute_arr_repair(self.reference)
        self.assertEqual(raised.exception.status_code, 503)
        self.assertNotIn("private", str(raised.exception.detail))


class AuthenticationTests(unittest.TestCase):
    """require_api_key: the existing bearer key plus the additive Authentik path."""

    @classmethod
    def setUpClass(cls):
        cls.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.public_key = cls.private_key.public_key()
        cls.other_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    def _token(self, private_key=None, issuer="https://auth.elliottrook.com/application/o/aster-companion/",
               audience="aster-companion", expires_in=300):
        now = int(time.time())
        payload = {
            "iss": issuer,
            "aud": audience,
            "sub": "jason",
            "iat": now,
            "exp": now + expires_in,
        }
        return jwt.encode(payload, private_key or self.private_key, algorithm="RS256")

    def _signing_key_patch(self):
        return patch(
            "aster_agent._authentik_jwks_client.get_signing_key_from_jwt",
            return_value=MagicMock(key=self.public_key),
        )

    def test_existing_bearer_key_is_unaffected(self):
        with patch("aster_agent.ASTER_API_KEY", "the-real-key"):
            require_api_key(authorization="Bearer the-real-key")  # does not raise

    def test_wrong_bearer_key_still_401s(self):
        with patch("aster_agent.ASTER_API_KEY", "the-real-key"):
            with self.assertRaises(HTTPException) as raised:
                require_api_key(authorization="Bearer wrong")
        self.assertEqual(raised.exception.status_code, 401)

    def test_missing_header_still_401s_when_key_configured(self):
        with patch("aster_agent.ASTER_API_KEY", "the-real-key"):
            with self.assertRaises(HTTPException) as raised:
                require_api_key(authorization=None)
        self.assertEqual(raised.exception.status_code, 401)

    def test_unconfigured_key_still_503s_with_no_authentik_token(self):
        with patch("aster_agent.ASTER_API_KEY", ""):
            with self.assertRaises(HTTPException) as raised:
                require_api_key(authorization=None)
        self.assertEqual(raised.exception.status_code, 503)

    def test_valid_authentik_token_is_accepted(self):
        with self._signing_key_patch(), patch("aster_agent.ASTER_API_KEY", "the-real-key"):
            require_api_key(authorization=f"Bearer {self._token()}")  # does not raise

    def test_authentik_token_for_a_different_application_is_refused(self):
        token = self._token(audience="some-other-app")
        with self._signing_key_patch(), patch("aster_agent.ASTER_API_KEY", "the-real-key"):
            with self.assertRaises(HTTPException) as raised:
                require_api_key(authorization=f"Bearer {token}")
        self.assertEqual(raised.exception.status_code, 401)

    def test_authentik_token_from_a_different_issuer_is_refused(self):
        token = self._token(issuer="https://not-authentik.example/application/o/aster-companion/")
        with self._signing_key_patch(), patch("aster_agent.ASTER_API_KEY", "the-real-key"):
            with self.assertRaises(HTTPException) as raised:
                require_api_key(authorization=f"Bearer {token}")
        self.assertEqual(raised.exception.status_code, 401)

    def test_expired_authentik_token_is_refused(self):
        token = self._token(expires_in=-60)
        with self._signing_key_patch(), patch("aster_agent.ASTER_API_KEY", "the-real-key"):
            with self.assertRaises(HTTPException) as raised:
                require_api_key(authorization=f"Bearer {token}")
        self.assertEqual(raised.exception.status_code, 401)

    def test_token_signed_by_a_different_key_is_refused(self):
        """Not just a different audience/issuer string - an actual forged signature."""
        token = self._token(private_key=self.other_private_key)
        with self._signing_key_patch(), patch("aster_agent.ASTER_API_KEY", "the-real-key"):
            with self.assertRaises(HTTPException) as raised:
                require_api_key(authorization=f"Bearer {token}")
        self.assertEqual(raised.exception.status_code, 401)

    def test_malformed_bearer_value_is_refused(self):
        with patch("aster_agent.ASTER_API_KEY", "the-real-key"):
            with self.assertRaises(HTTPException) as raised:
                require_api_key(authorization="Bearer not-a-jwt-at-all")
        self.assertEqual(raised.exception.status_code, 401)

    def test_valid_authentik_token_works_even_without_a_bearer_key_configured(self):
        """The two credential types are independent, not a fallback chain."""
        with self._signing_key_patch(), patch("aster_agent.ASTER_API_KEY", ""):
            require_api_key(authorization=f"Bearer {self._token()}")  # does not raise


class PersonaTests(unittest.TestCase):
    def test_sysadmin_persona_has_every_tool(self):
        self.assertEqual(PERSONAS["sysadmin"]["tools"], set(TOOLS.keys()))

    def test_media_persona_is_scoped_to_arr_and_excludes_other_systems(self):
        media_tools = PERSONAS["media"]["tools"]
        self.assertIn("get_arr_report", media_tools)
        self.assertIn("get_arr_repair_proposal", media_tools)
        self.assertNotIn("get_ha_report", media_tools)
        self.assertNotIn("get_forgejo_report", media_tools)
        self.assertNotIn("get_netbox_report", media_tools)
        self.assertNotIn("get_lab_health", media_tools)
        self.assertTrue(media_tools.issubset(set(TOOLS.keys())))

    def test_home_assistant_persona_is_scoped_to_ha_and_excludes_other_systems(self):
        ha_tools = PERSONAS["home_assistant"]["tools"]
        self.assertIn("get_ha_report", ha_tools)
        self.assertNotIn("get_arr_report", ha_tools)
        self.assertNotIn("get_forgejo_report", ha_tools)
        self.assertNotIn("get_netbox_report", ha_tools)
        self.assertNotIn("get_lab_health", ha_tools)
        self.assertTrue(ha_tools.issubset(set(TOOLS.keys())))

    def test_scoped_personas_exclude_broad_knowledge_search(self):
        """search_knowledge's own hint regex spans every system in the lab
        (including "home assistant" as a literal keyword) - live-caught
        2026-09-22 when the media persona used it to answer a Home
        Assistant question with real infrastructure detail, bypassing the
        persona's own out-of-scope instruction entirely. It stays available
        only to the unrestricted sysadmin persona."""
        self.assertNotIn("search_knowledge", PERSONAS["media"]["tools"])
        self.assertNotIn("search_knowledge", PERSONAS["home_assistant"]["tools"])
        self.assertIn("search_knowledge", PERSONAS["sysadmin"]["tools"])

    def test_default_persona_constant_is_a_registered_persona(self):
        self.assertIn(DEFAULT_PERSONA, PERSONAS)

    def test_chat_request_defaults_to_sysadmin_persona_with_no_tool_restriction(self):
        request = ChatRequest(messages=[{"role": "user", "content": "hi"}])
        self.assertEqual(request.persona, "sysadmin")
        self.assertIsNone(request.enabled_tools)

    def test_select_tools_allowed_set_restricts_matches(self):
        names = [
            tool["function"]["name"]
            for tool in select_tools(
                [{"role": "user", "content": "Is Home Assistant Supervisor currently healthy?"}],
                allowed={"get_current_time"},
            )
        ]
        self.assertEqual(names, [])

    def test_select_tools_with_no_allowed_set_is_unrestricted(self):
        names = [
            tool["function"]["name"]
            for tool in select_tools(
                [{"role": "user", "content": "Is Home Assistant Supervisor currently healthy?"}]
            )
        ]
        self.assertIn("get_ha_report", names)

    def test_normalized_messages_appends_persona_identity_after_base_prompt(self):
        messages = normalized_messages(
            [{"role": "user", "content": "hi"}], PERSONAS["media"]["identity"]
        )
        content = messages[0]["content"]
        self.assertIn(ASTER_SYSTEM_PROMPT, content)
        self.assertIn("Media Automation Aster persona", content)
        self.assertLess(content.index(ASTER_SYSTEM_PROMPT), content.index("Media Automation Aster persona"))

    def test_normalized_messages_without_persona_identity_is_unchanged(self):
        messages = normalized_messages([{"role": "user", "content": "hi"}])
        self.assertEqual(messages[0]["content"], ASTER_SYSTEM_PROMPT)


class PersonaChatEndpointTests(unittest.IsolatedAsyncioTestCase):
    @staticmethod
    def _fake_completion():
        return {
            "choices": [{"message": {"role": "assistant", "content": "ok"}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }

    async def test_unknown_persona_is_rejected(self):
        request = ChatRequest(messages=[{"role": "user", "content": "hi"}], persona="ghost")
        with self.assertRaises(HTTPException) as raised:
            await chat(request)
        self.assertEqual(raised.exception.status_code, 400)

    async def test_media_persona_excludes_home_assistant_tool_results(self):
        request = ChatRequest(
            messages=[{
                "role": "user",
                "content": (
                    "Is Home Assistant Supervisor currently healthy, and what is "
                    "currently stuck in the Radarr queue?"
                ),
            }],
            persona="media",
        )
        mocked = AsyncMock(return_value=self._fake_completion())
        with patch("aster_agent.upstream_completion", new=mocked):
            await chat(request)
        payload = mocked.call_args.args[0]
        system_content = payload["messages"][0]["content"]
        self.assertIn("Media Automation Aster persona", system_content)
        self.assertIn('"function":"get_arr_report"', system_content)
        self.assertNotIn("get_ha_report", system_content)

    async def test_media_persona_does_not_leak_home_assistant_knowledge(self):
        """Exact live repro (2026-09-22, Jason's phone): persona=media,
        "Tell me about home assistant" got back a full answer with real
        VM/IP/version detail, because search_knowledge's hint regex
        matches "home assistant" and was still in the media persona's
        tool set at the time. Guards against that regressing."""
        request = ChatRequest(
            messages=[{"role": "user", "content": "Tell me about home assistant"}],
            persona="media",
        )
        mocked = AsyncMock(return_value=self._fake_completion())
        with patch("aster_agent.upstream_completion", new=mocked):
            await chat(request)
        payload = mocked.call_args.args[0]
        system_content = payload["messages"][0]["content"]
        self.assertNotIn("Read-only function results for this turn follow as JSON", system_content)
        self.assertNotIn("search_knowledge", system_content)
        self.assertNotIn("get_ha_report", system_content)

    async def test_home_assistant_persona_excludes_arr_tool_results(self):
        request = ChatRequest(
            messages=[{
                "role": "user",
                "content": (
                    "Is Home Assistant Supervisor currently healthy, and what is "
                    "currently stuck in the Radarr queue?"
                ),
            }],
            persona="home_assistant",
        )
        mocked = AsyncMock(return_value=self._fake_completion())
        with patch("aster_agent.upstream_completion", new=mocked):
            await chat(request)
        payload = mocked.call_args.args[0]
        system_content = payload["messages"][0]["content"]
        self.assertIn("Home Assistant Aster persona", system_content)
        self.assertIn('"function":"get_ha_report"', system_content)
        self.assertNotIn("get_arr_report", system_content)

    async def test_enabled_tools_further_restricts_the_persona_default(self):
        request = ChatRequest(
            messages=[{
                "role": "user",
                "content": "What time is it, and what is currently stuck in the Radarr queue?",
            }],
            persona="sysadmin",
            enabled_tools=["get_current_time"],
        )
        mocked = AsyncMock(return_value=self._fake_completion())
        with patch("aster_agent.upstream_completion", new=mocked):
            await chat(request)
        payload = mocked.call_args.args[0]
        system_content = payload["messages"][0]["content"]
        self.assertIn('"function":"get_current_time"', system_content)
        self.assertNotIn("get_arr_report", system_content)

    async def test_enabled_tools_cannot_widen_a_persona_beyond_its_own_set(self):
        request = ChatRequest(
            messages=[{
                "role": "user",
                "content": "Is Home Assistant Supervisor currently healthy?",
            }],
            persona="media",
            enabled_tools=["get_ha_report"],
        )
        mocked = AsyncMock(return_value=self._fake_completion())
        with patch("aster_agent.upstream_completion", new=mocked):
            await chat(request)
        payload = mocked.call_args.args[0]
        self.assertNotIn("get_ha_report", payload["messages"][0]["content"])

    async def test_persona_and_enabled_tools_are_not_forwarded_upstream(self):
        request = ChatRequest(
            messages=[{"role": "user", "content": "hi"}],
            persona="media",
            enabled_tools=["get_arr_report"],
        )
        mocked = AsyncMock(return_value=self._fake_completion())
        with patch("aster_agent.upstream_completion", new=mocked):
            await chat(request)
        payload = mocked.call_args.args[0]
        self.assertNotIn("persona", payload)
        self.assertNotIn("enabled_tools", payload)

    async def test_personas_endpoint_lists_all_personas_with_scoped_tools(self):
        result = await personas()
        self.assertEqual(result["default"], "sysadmin")
        ids = {entry["id"] for entry in result["personas"]}
        self.assertEqual(ids, {"sysadmin", "media", "home_assistant"})
        media = next(entry for entry in result["personas"] if entry["id"] == "media")
        media_tool_names = {tool["name"] for tool in media["tools"]}
        self.assertIn("get_arr_report", media_tool_names)
        self.assertNotIn("get_ha_report", media_tool_names)
        self.assertNotIn("search_knowledge", media_tool_names)
        self.assertTrue(all("description" in tool for tool in media["tools"]))
        home_assistant = next(entry for entry in result["personas"] if entry["id"] == "home_assistant")
        ha_tool_names = {tool["name"] for tool in home_assistant["tools"]}
        self.assertIn("get_ha_report", ha_tool_names)
        self.assertNotIn("get_arr_report", ha_tool_names)
        self.assertNotIn("search_knowledge", ha_tool_names)


if __name__ == "__main__":
    unittest.main()
