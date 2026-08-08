from __future__ import annotations

import importlib.util
import shutil
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
            "プレースホルダ",
            "Webセキュリティ",
            35,
            date(2026, 8, 9),
            1,
            35,
            2,
            date(2026, 8, 10),
            "SQLインジェクション",
            "",
            track="A",
        )
        merged = study_helper.merge_uncatalogued_terms(self.catalog, {record.term: record})
        merged_by_term = {item.term: item for item in merged}
        self.assertEqual("A", merged_by_term["プレースホルダ"].track)

    def test_same_day_penalty_uses_last_score_not_lifetime_average(self) -> None:
        item = next(item for item in self.catalog if item.term == "SQLインジェクション")
        failed = study_helper.TermRecord(
            item.term,
            item.domain,
            57,
            date(2026, 8, 9),
            10,
            85,
            5,
            date(2026, 8, 10),
            item.related,
            "",
            track="B",
            last_score=20,
        )
        passed = study_helper.TermRecord(
            item.term,
            item.domain,
            57,
            date(2026, 8, 9),
            10,
            85,
            5,
            date(2026, 8, 10),
            item.related,
            "",
            track="B",
            last_score=80,
        )
        failed_priority = study_helper.build_candidates(
            [item], {item.term: failed}, date(2026, 8, 9), {}
        )[0].priority
        passed_priority = study_helper.build_candidates(
            [item], {item.term: passed}, date(2026, 8, 9), {}
        )[0].priority
        self.assertEqual(30, failed_priority - passed_priority)

    def test_older_session_cannot_overwrite_newer_term_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "progress").mkdir()
            existing = study_helper.TermRecord(
                "SQLインジェクション",
                "Webセキュリティ",
                70,
                date(2026, 8, 9),
                1,
                70,
                2,
                date(2026, 8, 14),
                "プレースホルダ",
                "",
                track="B",
                last_score=70,
                last_session="2026-08-09#2",
                applied_sessions=("2026-08-09#2",),
            )
            terms_path = root / "progress" / "terms.md"
            terms_path.write_text(
                study_helper.render_terms({existing.term: existing}),
                encoding="utf-8",
            )
            question = study_helper.GradedQuestion(
                number=1,
                domain="Webセキュリティ",
                track="B",
                level=2,
                primary_terms=("SQLインジェクション",),
                related_terms=("プレースホルダ",),
                score=80,
                good_point="",
                review_focus="",
            )
            with self.assertRaisesRegex(ValueError, "record sessions chronologically"):
                study_helper.update_term_records(root, date(2026, 8, 9), 1, [question], [])
            self.assertEqual(1, study_helper.load_terms(root)[existing.term].attempts)

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

    def test_record_is_idempotent_and_drives_next_day_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "references").mkdir()
            (root / "progress").mkdir()
            (root / "sessions").mkdir()
            shutil.copy(self.root / "references" / "taxonomy.md", root / "references" / "taxonomy.md")
            shutil.copy(self.root / "progress" / "terms.md", root / "progress" / "terms.md")
            shutil.copy(self.root / "progress" / "domains.md", root / "progress" / "domains.md")
            shutil.copy(self.root / "progress" / "history.md", root / "progress" / "history.md")
            session_path = root / "sessions" / "2026-08-09.md"
            session_path.write_text(
                """# 2026-08-09 セキスペ学習

## Session 1

- Created: 2026-08-09
- Status: grading
- Mode: diagnosis
- Question Count: 3
- Subject B Target: 70–85%

### Q1

- Domain: PKI・証明書
- Primary Terms:
  - `CRL / OCSP`
- Related Terms:
  - `証明書失効`
- Level: 3
- Track: B

<!-- CRLとOCSPを比較してください。 -->

### 回答

回答済み。

### 採点

Score: 45 / 100

#### 良かった点

- 失効確認という目的は説明できた

#### 次回確認する観点

- pull型と問い合わせ方式の違い

### Q2

- Domain: リスク・ガバナンス
- Primary Terms:
  - `リスク対応`
- Related Terms:
  - `リスク受容`
- Level: 2
- Track: A/B

<!-- リスク対応を説明してください。 -->

### 回答

回答済み。

### 採点

Score: 100 / 100

#### 良かった点

- 四つの対応を区別できた

#### 次回確認する観点

- 残存リスクの承認

### Q3

- Domain: リスク・ガバナンス
- Primary Terms:
  - `独自A概念`
- Related Terms:
  - `リスク対応`
- Level: 2
- Track: A

<!-- 独自A概念を説明してください。 -->

### 回答

回答済み。

### 採点

Score: 70 / 100

#### 良かった点

- 基本を説明できた

#### 次回確認する観点

- 応用例
""",
                encoding="utf-8",
            )

            _, parsed_questions = study_helper.parse_graded_session(
                session_path.read_text(encoding="utf-8"), 1
            )
            partial_records = study_helper.update_term_records(
                root,
                date(2026, 8, 9),
                1,
                parsed_questions,
                study_helper.load_catalog(root),
            )
            self.assertEqual(1, partial_records["CRL / OCSP"].attempts)
            self.assertIn("- Status: grading", session_path.read_text(encoding="utf-8"))
            self.assertEqual([], study_helper.read_table(root / "progress" / "history.md", "Date"))

            first = study_helper.record_progress(root, date(2026, 8, 9), 1)
            records = study_helper.load_terms(root)
            self.assertEqual(3, first["questions"])
            self.assertIn("- Status: graded", session_path.read_text(encoding="utf-8"))
            self.assertEqual({"CRL / OCSP", "リスク対応", "独自A概念"}, set(records))
            self.assertEqual("A", records["独自A概念"].track)
            self.assertEqual(45, records["CRL / OCSP"].last_score)
            self.assertEqual("2026-08-09#1", records["CRL / OCSP"].last_session)
            self.assertEqual(("2026-08-09#1",), records["CRL / OCSP"].applied_sessions)
            self.assertEqual(1, records["CRL / OCSP"].attempts)

            second = study_helper.record_progress(root, date(2026, 8, 9), 1)
            records_after_retry = study_helper.load_terms(root)
            history = study_helper.read_table(root / "progress" / "history.md", "Date")
            self.assertEqual(first["average"], second["average"])
            self.assertEqual(1, records_after_retry["CRL / OCSP"].attempts)
            self.assertEqual(1, len(history))
            self.assertEqual(0o644, (root / "progress" / "terms.md").stat().st_mode & 0o777)

            catalog = study_helper.merge_uncatalogued_terms(
                study_helper.load_catalog(root), records_after_retry
            )
            candidates = study_helper.build_candidates(
                catalog,
                records_after_retry,
                date(2026, 8, 10),
                study_helper.recent_domain_counts(root),
            )
            plan = study_helper.adaptive_plan(candidates, 5)
            self.assertIn("CRL / OCSP", {candidate.item.term for _, candidate in plan})


if __name__ == "__main__":
    unittest.main()
