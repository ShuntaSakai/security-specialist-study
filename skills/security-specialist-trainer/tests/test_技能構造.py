from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path


class 技能構造テスト(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = Path(__file__).resolve().parents[1]
        cls.root = cls.skill.parents[1]

    def test_必須ファイルが存在する(self) -> None:
        expected = [
            self.root / "AGENTS.md",
            self.root / ".github" / "workflows" / "python-tests.yml",
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
        self.assertTrue((self.root / "sessions" / "理解・応用問題").is_dir())
        self.assertTrue((self.root / "sessions" / "暗記語句問題").is_dir())

    def test_技能のフロントマターは必要項目だけを持つ(self) -> None:
        text = (self.skill / "SKILL.md").read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---", text, flags=re.DOTALL)
        self.assertIsNotNone(match)
        assert match
        fields = [line.split(":", 1)[0] for line in match.group(1).splitlines() if ":" in line]
        self.assertEqual(["name", "description"], fields)
        self.assertIn("name: security-specialist-trainer", match.group(1))
        self.assertNotIn("TODO", text)

    def test_エージェントメタデータに技能呼出しが明記される(self) -> None:
        text = (self.skill / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("display_name:", text)
        self.assertIn("short_description:", text)
        self.assertIn("$security-specialist-trainer", text)

    def test_暗記語句の手順と形式が文書化される(self) -> None:
        skill_text = (self.skill / "SKILL.md").read_text(encoding="utf-8")
        session_text = (self.root / "references" / "session-format.md").read_text(encoding="utf-8")
        scoring_text = (self.root / "references" / "scoring-rules.md").read_text(encoding="utf-8")
        self.assertIn("--mode term-recall", skill_text)
        self.assertIn("create exactly 10 questions", skill_text)
        self.assertIn("- Mode: term-recall", session_text)
        self.assertIn("Recall Score", scoring_text)
        self.assertIn("Explanation Score", scoring_text)
        self.assertIn("sessions/理解・応用問題/YYYY-MM-DD.md", session_text)
        self.assertIn("sessions/暗記語句問題/YYYY-MM-DD.md", session_text)
        self.assertIn("--mode standard", session_text)
        self.assertIn("--mode term-recall", session_text)
        self.assertIn("1〜30問", session_text)

    def test_採点手順は現在と旧セッション保存先を全て明記する(self) -> None:
        skill_text = (self.skill / "SKILL.md").read_text(encoding="utf-8")
        grade_section_match = re.search(
            r"^## Grade a session\n(?P<body>.*?)(?=^## |\Z)",
            skill_text,
            flags=re.MULTILINE | re.DOTALL,
        )
        self.assertIsNotNone(grade_section_match)
        assert grade_section_match
        grade_section = grade_section_match.group("body")
        for session_path in (
            "sessions/理解・応用問題/",
            "sessions/暗記語句問題/",
            "sessions/standard/",
            "sessions/term-recall/",
            "sessions/YYYY-MM-DD.md",
        ):
            with self.subTest(session_path=session_path):
                self.assertIn(session_path, grade_section)
        self.assertIn(
            "the literal `A` or `B` (including the literal `A/B`)",
            grade_section,
        )
        self.assertIn("exactly one integer `Question Count` from 1 to 30", grade_section)
        self.assertIn("unique and consecutive from `Q1`", grade_section)

    def test_自動テストが全てのプッシュで実行される(self) -> None:
        workflow = (
            self.root / ".github" / "workflows" / "python-tests.yml"
        ).read_text(encoding="utf-8")
        self.assertRegex(workflow, r"(?m)^on:\n  push:\s*$")
        self.assertNotIn("branches:", workflow)
        self.assertIn("python -m unittest discover", workflow)
        self.assertIn("-s skills/security-specialist-trainer/tests", workflow)

    def test_テスト名は日本語で記述される(self) -> None:
        japanese = re.compile(r"[ぁ-んァ-ヶ一-龠々]")
        english_word = re.compile(r"[A-Za-z]{2,}")

        def 日本語主体の名前(name: str) -> bool:
            return japanese.search(name) is not None and english_word.search(name) is None

        def 検査対象の名前(source: str) -> tuple[list[str], list[str]]:
            tree = ast.parse(source)
            class_names = [
                node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
            ]
            method_names = [
                node.name
                for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name.startswith("test_")
            ]
            return class_names, method_names

        self.assertTrue(日本語主体の名前("科目Bの比率を検証する"))
        self.assertFalse(日本語主体の名前("should_work_日本語"))
        bypass_classes, bypass_methods = 検査対象の名前(
            """class should_work_日本語(基底テスト):
    def test_should_work_日本語(self, value=None):
        pass
"""
        )
        self.assertEqual(["should_work_日本語"], bypass_classes)
        self.assertEqual(["test_should_work_日本語"], bypass_methods)
        self.assertFalse(all(日本語主体の名前(name) for name in bypass_classes))
        self.assertFalse(
            all(
                日本語主体の名前(name.removeprefix("test_"))
                for name in bypass_methods
            )
        )

        for path in sorted((self.skill / "tests").glob("test_*.py")):
            text = path.read_text(encoding="utf-8")
            class_names, method_names = 検査対象の名前(text)
            with self.subTest(path=path.name):
                self.assertTrue(class_names)
                self.assertTrue(method_names)
                self.assertTrue(
                    日本語主体の名前(path.stem.removeprefix("test_")), path.name
                )
                self.assertTrue(
                    all(日本語主体の名前(name) for name in class_names), path.name
                )
                self.assertTrue(
                    all(
                        日本語主体の名前(name.removeprefix("test_"))
                        for name in method_names
                    ),
                    path.name,
                )

        agents = (self.root / "AGENTS.md").read_text(encoding="utf-8")
        readme = (self.root / "README.md").read_text(encoding="utf-8")
        self.assertIn("test file names", agents)
        self.assertIn("テストファイル名", readme)


if __name__ == "__main__":
    unittest.main()
