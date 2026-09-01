import tempfile
import unittest
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
