import tempfile
import unittest
import json
from pathlib import Path

from aster_agent import ChatRequest, TOOLS, preload_read_only_context, search_knowledge, select_tools


class AsterAgentTests(unittest.TestCase):
    def test_casual_chat_has_no_tools(self):
        self.assertEqual(select_tools([{"role": "user", "content": "Tell me a short joke"}]), [])

    def test_streaming_request_is_supported(self):
        request = ChatRequest(messages=[{"role": "user", "content": "Hello"}], stream=True)
        self.assertTrue(request.stream)

    def test_homelab_question_selects_knowledge(self):
        names = [tool["function"]["name"] for tool in select_tools([{"role": "user", "content": "What GPU is in my homelab?"}])]
        self.assertIn("search_knowledge", names)

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
            projects = docs / "projects"
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
            projects = docs / "projects"
            projects.mkdir(parents=True)
            (docs / "03-Hardware-Inventory.md").write_text(
                "The current B60 GPU uses Vulkan because its physical BAR is 256 MB.",
                encoding="utf-8",
            )
            (docs / "Aster-Operations.md").write_text(
                "LXC 104 runs the Aster API. LXC 110 runs llama.cpp with Qwen3.8-27B.",
                encoding="utf-8",
            )
            (docs / "AI-Hermes-Second-Brain.md").write_text(
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
            self.assertIn("docs/Aster-Operations.md", sources)
            self.assertIn("docs/AI-Hermes-Second-Brain.md", sources)
            self.assertIn("docs/projects/Local-AI.md", sources)

    def test_operational_source_has_distinct_authority(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            docs = root / "docs"
            docs.mkdir()
            (docs / "Aster-Operations.md").write_text(
                "LXC 104 runs the Aster service with the Qwen model.", encoding="utf-8"
            )
            result = search_knowledge("Aster LXC model", root=root)
            self.assertEqual(result["results"][0]["authority"], "current_operations")

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

    def test_multi_part_query_prefers_answer_sections(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            docs = root / "docs"
            projects = docs / "projects"
            projects.mkdir(parents=True)
            filler = "Aster LXC inference service operational notes. " * 40
            (docs / "Aster-Operations.md").write_text(
                f"{filler}\n\n## Runtime configuration\n"
                "LXC 110 runs llama.cpp with Qwen3.8-27B UD-IQ4_XS and Vulkan.\n",
                encoding="utf-8",
            )
            (docs / "AI-Hermes-Second-Brain.md").write_text(
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
            self.assertIn("Qwen3.8-27B", excerpts["docs/Aster-Operations.md"])
            self.assertIn("Define the knowledge boundary", excerpts["docs/AI-Hermes-Second-Brain.md"])
            self.assertIn("Test backup and restore", excerpts["docs/AI-Hermes-Second-Brain.md"])
            self.assertIn("Establish a monthly health review", excerpts["docs/AI-Hermes-Second-Brain.md"])
            self.assertIn("256 MB BAR", excerpts["docs/projects/Local-AI.md"])

    def test_focused_checklist_can_return_multiple_chunks_from_one_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            docs = root / "docs"
            docs.mkdir()
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
            (docs / "AI-Hermes-Second-Brain.md").write_text(
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
                {"docs/AI-Hermes-Second-Brain.md"},
            )
            combined = " ".join(item["excerpt"] for item in result["results"])
            self.assertIn("Define the knowledge boundary", combined)
            self.assertIn("Test backup and restore", combined)
            self.assertIn("Establish a monthly health review", combined)


class AsterPreloadTests(unittest.IsolatedAsyncioTestCase):
    async def test_time_tool_is_preloaded_without_model_round_trip(self):
        result = await preload_read_only_context(
            [{"role": "user", "content": "What time is it?"}],
            [TOOLS["get_current_time"]],
        )
        self.assertEqual(result[0]["function"], "get_current_time")
        self.assertEqual(result[0]["result"]["timezone"], "America/Vancouver")


if __name__ == "__main__":
    unittest.main()
