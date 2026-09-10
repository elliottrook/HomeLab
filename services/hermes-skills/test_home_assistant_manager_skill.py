import re
import unittest
from pathlib import Path


class HomeAssistantManagerSkillTests(unittest.TestCase):
    def test_frontmatter_and_safety_boundary(self) -> None:
        skill = Path(__file__).with_name("home-assistant-manager") / "SKILL.md"
        content = skill.read_text(encoding="utf-8")

        self.assertTrue(content.startswith("---\n"))
        frontmatter, body = content.split("\n---\n", 1)
        description = re.search(r'^description: "(.+)"$', frontmatter, re.M)
        self.assertIsNotNone(description)
        self.assertLessEqual(len(description.group(1)), 60)
        self.assertTrue(description.group(1).endswith("."))
        self.assertIn("platforms: [linux]", frontmatter)
        self.assertIn("does not hold a Home\nAssistant token", body)
        self.assertIn("does not invoke a\n  tool", body)
        self.assertIn("exact approval", body)
        self.assertIn("water/shutoff/lock", body)


if __name__ == "__main__":
    unittest.main()
