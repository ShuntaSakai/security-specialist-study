from __future__ import annotations

import re
import unittest
from pathlib import Path


class SkillStructureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = Path(__file__).resolve().parents[1]
        cls.root = cls.skill.parents[1]

    def test_required_files_exist(self) -> None:
        expected = [
            self.root / "AGENTS.md",
            self.skill / "SKILL.md",
            self.skill / "agents" / "openai.yaml",
            self.root / "README.md",
            self.root / "progress" / "terms.md",
            self.root / "progress" / "domains.md",
            self.root / "progress" / "history.md",
            self.root / "references" / "taxonomy.md",
            self.root / "references" / "scoring-rules.md",
            self.root / "references" / "session-format.md",
        ]
        self.assertEqual([], [str(path) for path in expected if not path.is_file()])

    def test_skill_frontmatter_has_only_name_and_description(self) -> None:
        text = (self.skill / "SKILL.md").read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---", text, flags=re.DOTALL)
        self.assertIsNotNone(match)
        assert match
        fields = [line.split(":", 1)[0] for line in match.group(1).splitlines() if ":" in line]
        self.assertEqual(["name", "description"], fields)
        self.assertIn("name: security-specialist-trainer", match.group(1))
        self.assertNotIn("TODO", text)

    def test_openai_metadata_has_explicit_skill_prompt(self) -> None:
        text = (self.skill / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("display_name:", text)
        self.assertIn("short_description:", text)
        self.assertIn("$security-specialist-trainer", text)


if __name__ == "__main__":
    unittest.main()
