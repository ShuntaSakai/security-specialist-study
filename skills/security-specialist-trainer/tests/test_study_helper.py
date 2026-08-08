from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "study_helper.py"
SPEC = importlib.util.spec_from_file_location("study_helper", SCRIPT)
assert SPEC and SPEC.loader
study_helper = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = study_helper
SPEC.loader.exec_module(study_helper)


class StudyHelperTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[3]
        cls.catalog = study_helper.load_catalog(cls.root)

    def test_initial_plan_is_eight_domain_diagnostic(self) -> None:
        plan = study_helper.diagnostic_plan(self.catalog, 8)
        self.assertEqual(8, len(plan))
        self.assertEqual(8, len({candidate.item.domain for _, candidate in plan}))
        self.assertTrue(all(2 <= candidate.suggested_level <= 3 for _, candidate in plan))

    def test_initial_focus_request_changes_diagnostic_mix(self) -> None:
        plan = study_helper.diagnostic_plan(self.catalog, 8, "Webセキュリティ")
        web_count = sum(candidate.item.domain == "Webセキュリティ" for _, candidate in plan)
        self.assertGreaterEqual(web_count, 3)

    def test_low_score_increases_priority_and_stays_basic(self) -> None:
        item = next(item for item in self.catalog if item.term == "DNSキャッシュポイズニング")
        weak = study_helper.TermRecord(
            item.term, item.domain, 31, date(2026, 8, 8), 2, 35, 2, date(2026, 8, 9), item.related, ""
        )
        strong = study_helper.TermRecord(
            item.term, item.domain, 92, date(2026, 8, 8), 5, 91, 5, date(2026, 9, 7), item.related, ""
        )
        weak_candidate = study_helper.build_candidates([item], {item.term: weak}, date(2026, 8, 9), {})[0]
        strong_candidate = study_helper.build_candidates([item], {item.term: strong}, date(2026, 8, 9), {})[0]
        self.assertGreater(weak_candidate.priority, strong_candidate.priority)
        self.assertEqual(1, weak_candidate.suggested_level)
        self.assertEqual(5, strong_candidate.suggested_level)

    def test_overdue_concept_gets_forgetting_priority(self) -> None:
        item = next(item for item in self.catalog if item.term == "CRL / OCSP")
        record = study_helper.TermRecord(
            item.term, item.domain, 70, date(2026, 8, 1), 3, 73, 3, date(2026, 8, 6), item.related, ""
        )
        candidate = study_helper.build_candidates([item], {item.term: record}, date(2026, 8, 9), {})[0]
        self.assertTrue(candidate.due)
        self.assertGreaterEqual(candidate.forgetting, 35)

    def test_level_cap_prevents_definition_only_mastery(self) -> None:
        self.assertEqual(70, study_helper.updated_mastery(None, 0, 100, 1))
        self.assertEqual(100, study_helper.updated_mastery(None, 0, 100, 5))

    def test_five_question_plan_keeps_all_adaptive_buckets(self) -> None:
        today = date(2026, 8, 9)
        wanted = {
            "SQLインジェクション": (35, date(2026, 8, 7), date(2026, 8, 8)),
            "XSS": (72, date(2026, 8, 1), date(2026, 8, 6)),
            "DMARC": (93, date(2026, 8, 8), date(2026, 9, 7)),
            "TLSハンドシェイク": (82, date(2026, 8, 8), date(2026, 8, 20)),
        }
        records = {}
        for item in self.catalog:
            if item.term in wanted:
                score, studied, review = wanted[item.term]
                records[item.term] = study_helper.TermRecord(
                    item.term, item.domain, score, studied, 3, score, 4, review, item.related, ""
                )
        candidates = study_helper.build_candidates(self.catalog, records, today, {})
        plan = study_helper.adaptive_plan(candidates, 5)
        buckets = [bucket for bucket, _ in plan]
        self.assertEqual(5, len(plan))
        self.assertIn("弱点", buckets)
        self.assertIn("復習期", buckets)
        self.assertIn("新規", buckets)
        self.assertIn("発展", buckets)

    def test_recent_high_score_is_not_due_but_remains_future_challenge(self) -> None:
        item = next(item for item in self.catalog if item.term == "DMARC")
        record = study_helper.TermRecord(
            item.term, item.domain, 95, date(2026, 8, 9), 6, 94, 5, date(2026, 9, 8), item.related, ""
        )
        candidate = study_helper.build_candidates([item], {item.term: record}, date(2026, 8, 9), {})[0]
        self.assertFalse(candidate.due)
        self.assertTrue(candidate.challenge)
        self.assertEqual(6, candidate.suggested_level)

    def test_new_mode_increases_new_topic_slots(self) -> None:
        item = next(item for item in self.catalog if item.term == "SQLインジェクション")
        record = study_helper.TermRecord(
            item.term, item.domain, 55, date(2026, 8, 8), 2, 55, 2, date(2026, 8, 10), item.related, ""
        )
        candidates = study_helper.build_candidates(
            self.catalog, {item.term: record}, date(2026, 8, 9), {}, mode="new"
        )
        plan = study_helper.adaptive_plan(candidates, 5, mode="new")
        self.assertGreaterEqual(sum(bucket == "新規" for bucket, _ in plan), 2)

    def test_five_question_mix_stays_within_subject_b_target(self) -> None:
        candidates = study_helper.build_candidates(self.catalog, {}, date(2026, 8, 10), {})
        plan = study_helper.adaptive_plan(candidates, 5)
        self.assertEqual(4, sum(candidate.item.track == "B" for _, candidate in plan))

    def test_progress_term_not_in_catalog_remains_eligible(self) -> None:
        record = study_helper.TermRecord(
            "プレースホルダ", "Webセキュリティ", 35, date(2026, 8, 9), 1, 35, 2, date(2026, 8, 10), "SQLインジェクション", ""
        )
        merged = study_helper.merge_uncatalogued_terms(self.catalog, {record.term: record})
        self.assertIn("プレースホルダ", {item.term for item in merged})

    def test_high_level_success_has_longer_review_interval(self) -> None:
        self.assertEqual(30, study_helper.next_interval(92, 80, 5))
        self.assertGreater(study_helper.next_interval(92, 95, 5, 2), 30)

    def test_markdown_tables_are_the_only_required_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "references").mkdir()
            (root / "progress").mkdir()
            (root / "sessions").mkdir()
            taxonomy = self.root / "references" / "taxonomy.md"
            (root / "references" / "taxonomy.md").write_text(taxonomy.read_text(encoding="utf-8"), encoding="utf-8")
            (root / "progress" / "terms.md").write_text(
                "| Term | Domain | Score | Last Studied | Attempts | Average | Last Level | Next Review | Related | Notes |\n"
                "|---|---|---:|---|---:|---:|---:|---|---|---|\n",
                encoding="utf-8",
            )
            self.assertTrue(study_helper.load_catalog(root))
            self.assertEqual({}, study_helper.load_terms(root))


if __name__ == "__main__":
    unittest.main()
