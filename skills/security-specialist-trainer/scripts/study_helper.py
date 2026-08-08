#!/usr/bin/env python3
"""Build a deterministic, human-reviewable adaptive study selection plan.

The script reads Markdown only and never mutates the learning record. Codex uses
the plan as input when authoring questions; semantic grading remains model-led.
"""

from __future__ import annotations

import argparse
import hashlib
import math
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable, Optional


DIAGNOSTIC_DOMAIN_ORDER = [
    "Webセキュリティ",
    "ネットワークセキュリティ",
    "暗号",
    "認証・認可 / IAM",
    "PKI・証明書",
    "DNS",
    "メールセキュリティ",
    "マルウェア",
]


@dataclass(frozen=True)
class CatalogItem:
    term: str
    domain: str
    track: str
    importance: int
    entry_level: int
    diagnostic: bool
    prerequisites: str
    related: str


@dataclass(frozen=True)
class TermRecord:
    term: str
    domain: str
    score: int
    last_studied: Optional[date]
    attempts: int
    average: int
    last_level: int
    next_review: Optional[date]
    related: str
    notes: str


@dataclass(frozen=True)
class Candidate:
    item: CatalogItem
    priority: float
    weakness: float
    forgetting: float
    unseen: bool
    due: bool
    challenge: bool
    suggested_level: int
    reason: str


def split_markdown_row(line: str) -> list[str]:
    """Split the simple pipe tables used by this repository."""
    escaped = "\u0000"
    line = line.strip().replace("\\|", escaped)
    return [cell.strip().replace(escaped, "|") for cell in line.strip("|").split("|")]


def read_table(path: Path, required_first_column: str) -> list[dict[str, str]]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if not line.lstrip().startswith("|"):
            continue
        headers = split_markdown_row(line)
        if not headers or headers[0] != required_first_column:
            continue
        rows: list[dict[str, str]] = []
        for row_line in lines[index + 2 :]:
            if not row_line.lstrip().startswith("|"):
                break
            values = split_markdown_row(row_line)
            if len(values) != len(headers):
                continue
            rows.append(dict(zip(headers, values)))
        return rows
    return []


def as_int(value: str, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def as_date(value: str) -> Optional[date]:
    if not value or value == "—":
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def load_catalog(root: Path) -> list[CatalogItem]:
    rows = read_table(root / "references" / "taxonomy.md", "Term")
    result = []
    for row in rows:
        result.append(
            CatalogItem(
                term=row["Term"],
                domain=row["Domain"],
                track=row["Track"],
                importance=as_int(row["Importance"], 3),
                entry_level=as_int(row["Entry Level"], 2),
                diagnostic=row["Diagnostic"].lower() == "yes",
                prerequisites=row["Prerequisites"],
                related=row["Related"],
            )
        )
    return result


def load_terms(root: Path) -> dict[str, TermRecord]:
    rows = read_table(root / "progress" / "terms.md", "Term")
    result: dict[str, TermRecord] = {}
    for row in rows:
        score = as_int(row.get("Score", ""), -1)
        if score < 0:
            continue
        result[row["Term"]] = TermRecord(
            term=row["Term"],
            domain=row["Domain"],
            score=max(0, min(100, score)),
            last_studied=as_date(row.get("Last Studied", "")),
            attempts=as_int(row.get("Attempts", "0")),
            average=as_int(row.get("Average", str(score)), score),
            last_level=as_int(row.get("Last Level", "1"), 1),
            next_review=as_date(row.get("Next Review", "")),
            related=row.get("Related", ""),
            notes=row.get("Notes", ""),
        )
    return result


def merge_uncatalogued_terms(catalog: list[CatalogItem], terms: dict[str, TermRecord]) -> list[CatalogItem]:
    """Keep hand-added progress terms eligible even when absent from taxonomy."""
    merged = list(catalog)
    known = {item.term for item in merged}
    for record in terms.values():
        if record.term in known:
            continue
        merged.append(
            CatalogItem(
                term=record.term,
                domain=record.domain,
                track="B",
                importance=3,
                entry_level=target_level(record.score),
                diagnostic=False,
                prerequisites="",
                related=record.related,
            )
        )
    return merged


def base_interval(score: int) -> int:
    if score < 40:
        return 1
    if score < 60:
        return 2
    if score < 75:
        return 5
    if score < 90:
        return 12
    return 30


def target_level(score: Optional[int], entry_level: int = 2) -> int:
    if score is None:
        return max(1, min(3, entry_level))
    if score < 40:
        return 1
    if score < 60:
        return 2
    if score < 75:
        return 3
    if score < 88:
        return 4
    if score < 95:
        return 5
    return 6


def level_cap(level: int) -> int:
    return {1: 70, 2: 80, 3: 88, 4: 94, 5: 100, 6: 100}.get(level, 100)


def updated_mastery(old_score: Optional[int], attempts: int, answer_score: int, level: int) -> int:
    evidence = min(max(answer_score, 0), level_cap(level))
    if old_score is None or attempts <= 0:
        return evidence
    alpha = 0.45 if attempts <= 2 else 0.35 if attempts <= 5 else 0.30
    if answer_score < 40:
        alpha += 0.10
    return round(old_score * (1 - alpha) + evidence * alpha)


def next_interval(score: int, answer_score: int, level: int, stable_high_count: int = 0) -> int:
    interval = float(base_interval(score))
    if answer_score < 60:
        interval = max(1.0, interval / 2)
    elif answer_score >= 90 and level >= 4:
        interval *= 1.25
    if answer_score >= 90 and level >= 5 and stable_high_count >= 2:
        interval = max(interval, base_interval(score) * 1.5)
    return max(1, round(interval))


def recent_domain_counts(root: Path, limit_sessions: int = 5) -> dict[str, int]:
    session_files = sorted((root / "sessions").glob("*.md"), reverse=True)
    counts: dict[str, int] = {}
    sessions_seen = 0
    for path in session_files:
        text = path.read_text(encoding="utf-8")
        sections = re.split(r"(?=^## Session \d+\s*$)", text, flags=re.MULTILINE)
        for section in reversed(sections[1:]):
            for domain in re.findall(r"^- Domain:\s*(.+?)\s*$", section, flags=re.MULTILINE):
                counts[domain] = counts.get(domain, 0) + 1
            sessions_seen += 1
            if sessions_seen >= limit_sessions:
                return counts
    return counts


def tie_break(term: str, today: date) -> float:
    digest = hashlib.sha256(f"{today.isoformat()}|{term}".encode()).hexdigest()
    return int(digest[:6], 16) / 0xFFFFFF


def build_candidates(
    catalog: Iterable[CatalogItem],
    terms: dict[str, TermRecord],
    today: date,
    recent_counts: dict[str, int],
    focus: str = "",
    mode: str = "standard",
) -> list[Candidate]:
    focus_tokens = [token.strip().lower() for token in re.split(r"[,/、]", focus) if token.strip()]
    weak_names = {name for name, record in terms.items() if record.score < 60}
    candidates: list[Candidate] = []

    for item in catalog:
        record = terms.get(item.term)
        subject_b = 15 if item.track == "B" else 10 if item.track == "A/B" else 3
        balance = max(0, 10 - 2 * recent_counts.get(item.domain, 0))
        focus_bonus = 0
        haystack = f"{item.term} {item.domain} {item.related}".lower()
        if focus_tokens and any(token in haystack for token in focus_tokens):
            focus_bonus = 30

        relation = 0
        relation_text = f"{item.related} {item.prerequisites}"
        if any(name in relation_text for name in weak_names):
            relation = 10

        if record is None:
            weakness = 0.0
            forgetting = 0.0
            unseen_bonus = 20
            recent_penalty = 0
            due = False
            challenge = False
            level = target_level(None, item.entry_level)
            reason = "未学習。頻出度と前提関係を見て導入"
        else:
            weakness = 0.45 * (100 - record.score)
            elapsed = (today - record.last_studied).days if record.last_studied else base_interval(record.score)
            elapsed = max(0, elapsed)
            forgetting = min(40.0, 35.0 * elapsed / base_interval(record.score))
            unseen_bonus = 0
            due = bool(record.next_review and record.next_review <= today) or forgetting >= 30
            challenge = record.score >= 80
            recent_penalty = 30 if elapsed == 0 and record.average >= 60 else 0
            level = target_level(record.score, item.entry_level)
            if record.score < 60:
                reason = f"理解度{record.score}の弱点を再構成"
            elif due:
                reason = f"最終学習から{elapsed}日。復習期限が近い/超過"
            elif challenge:
                reason = f"理解度{record.score}。シナリオへ難化"
            else:
                reason = f"理解度{record.score}。関連知識を補強"

        priority = weakness + forgetting + subject_b + unseen_bonus + relation + balance + focus_bonus - recent_penalty
        if mode == "weak":
            priority += weakness * 0.5
        elif mode == "new" and record is None:
            priority += 30
        elif mode == "subject-b" and item.track == "B":
            priority += 25

        priority += item.importance * 1.5 + tie_break(item.term, today)
        candidates.append(
            Candidate(
                item=item,
                priority=priority,
                weakness=weakness,
                forgetting=forgetting,
                unseen=record is None,
                due=due,
                challenge=challenge,
                suggested_level=level,
                reason=reason,
            )
        )
    return candidates


def _take_balanced(pool: Iterable[Candidate], count: int, selected: list[tuple[str, Candidate]]) -> None:
    if count <= 0:
        return
    used_terms = {candidate.item.term for _, candidate in selected}
    domain_counts: dict[str, int] = {}
    for _, candidate in selected:
        domain_counts[candidate.item.domain] = domain_counts.get(candidate.item.domain, 0) + 1
    available = [candidate for candidate in pool if candidate.item.term not in used_terms]
    while available and count > 0:
        best = max(
            available,
            key=lambda candidate: candidate.priority - 12 * domain_counts.get(candidate.item.domain, 0),
        )
        selected.append(("", best))
        domain_counts[best.item.domain] = domain_counts.get(best.item.domain, 0) + 1
        available.remove(best)
        count -= 1


def diagnostic_plan(catalog: list[CatalogItem], count: int, focus: str = "") -> list[tuple[str, Candidate]]:
    by_domain = {item.domain: item for item in catalog if item.diagnostic}
    ordered = [by_domain[domain] for domain in DIAGNOSTIC_DOMAIN_ORDER if domain in by_domain]
    ordered.extend(item for item in catalog if item.diagnostic and item not in ordered)
    if len(ordered) < count:
        ordered.extend(item for item in catalog if item not in ordered)
    focus_tokens = [token.strip().lower() for token in re.split(r"[,/、]", focus) if token.strip()]
    if focus_tokens:
        focused = [
            item
            for item in catalog
            if any(token in f"{item.term} {item.domain} {item.related}".lower() for token in focus_tokens)
        ]
        focus_count = max(1, round(count * 0.40))
        ordered = focused[:focus_count] + [item for item in ordered if item not in focused]
        ordered.extend(item for item in catalog if item not in ordered)
    result = []
    for item in ordered[:count]:
        candidate = Candidate(
            item=item,
            priority=float(item.importance),
            weakness=0,
            forgetting=0,
            unseen=True,
            due=False,
            challenge=False,
            suggested_level=max(2, min(3, item.entry_level)),
            reason="初回診断。分野横断で基礎〜中級を確認",
        )
        result.append(("診断", candidate))
    return result


def adaptive_plan(candidates: list[Candidate], count: int, mode: str = "standard") -> list[tuple[str, Candidate]]:
    if mode == "weak":
        weak_count, due_count, new_count = round(count * 0.60), round(count * 0.20), round(count * 0.10)
    elif mode == "new":
        weak_count, due_count, new_count = round(count * 0.25), round(count * 0.15), round(count * 0.50)
    else:
        weak_count, due_count, new_count = round(count * 0.40), round(count * 0.25), round(count * 0.20)
    challenge_count = max(0, count - weak_count - due_count - new_count)
    selected: list[tuple[str, Candidate]] = []

    buckets = [
        ("弱点", (c for c in candidates if not c.unseen and c.weakness >= 13.5), weak_count),
        ("復習期", (c for c in candidates if not c.unseen and c.due), due_count),
        ("新規", (c for c in candidates if c.unseen), new_count),
        ("発展", (c for c in candidates if c.challenge), challenge_count),
    ]
    for label, pool, quota in buckets:
        before = len(selected)
        _take_balanced(pool, quota, selected)
        for index in range(before, len(selected)):
            selected[index] = (label, selected[index][1])

    if len(selected) < count:
        before = len(selected)
        _take_balanced(candidates, count - len(selected), selected)
        for index in range(before, len(selected)):
            selected[index] = ("優先度補完", selected[index][1])
    selected = selected[:count]
    if count >= 4 and mode != "subject-b":
        minimum_b = math.ceil(count * 0.70)
        maximum_b = math.floor(count * 0.85)
        used = {candidate.item.term for _, candidate in selected}

        def same_bucket(label: str, candidate: Candidate) -> bool:
            return {
                "弱点": not candidate.unseen and candidate.weakness >= 13.5,
                "復習期": not candidate.unseen and candidate.due,
                "新規": candidate.unseen,
                "発展": candidate.challenge,
            }.get(label, True)

        while sum(candidate.item.track == "B" for _, candidate in selected) > maximum_b:
            replaceable = [(index, c) for index, (_, c) in enumerate(selected) if c.item.track == "B"]
            if not replaceable:
                break
            index, removed = min(replaceable, key=lambda pair: pair[1].priority)
            label = selected[index][0]
            replacements = [
                c for c in candidates if c.item.track != "B" and c.item.term not in used and same_bucket(label, c)
            ]
            if not replacements:
                replacements = [c for c in candidates if c.item.track != "B" and c.item.term not in used]
            if not replacements:
                break
            replacement = max(replacements, key=lambda c: c.priority)
            used.remove(removed.item.term)
            used.add(replacement.item.term)
            selected[index] = (label, replacement)

        while sum(candidate.item.track == "B" for _, candidate in selected) < minimum_b:
            replaceable = [(index, c) for index, (_, c) in enumerate(selected) if c.item.track != "B"]
            if not replaceable:
                break
            index, removed = min(replaceable, key=lambda pair: pair[1].priority)
            label = selected[index][0]
            replacements = [
                c for c in candidates if c.item.track == "B" and c.item.term not in used and same_bucket(label, c)
            ]
            if not replacements:
                replacements = [c for c in candidates if c.item.track == "B" and c.item.term not in used]
            if not replacements:
                break
            replacement = max(replacements, key=lambda c: c.priority)
            used.remove(removed.item.term)
            used.add(replacement.item.term)
            selected[index] = (label, replacement)
    return selected


def suggested_form(level: int) -> str:
    return {
        1: "定義",
        2: "原理",
        3: "対策・比較",
        4: "短いシナリオ",
        5: "科目B相当のログ・設定・判断",
        6: "科目B発展・制約と残存リスク",
    }[level]


def render_plan(plan: list[tuple[str, Candidate]], phase: str, today: date) -> str:
    b_count = sum(1 for _, candidate in plan if candidate.item.track == "B")
    b_ratio = round(100 * b_count / len(plan)) if plan else 0
    lines = [
        "# Adaptive selection plan",
        "",
        f"- Date: {today.isoformat()}",
        f"- Phase: {phase}",
        f"- Questions: {len(plan)}",
        f"- Strict Track-B ratio: {b_ratio}% (A/B concepts are counted separately)",
        "",
        "| Slot | Bucket | Term | Domain | Track | Level | Form | Priority | Reason |",
        "|---:|---|---|---|---|---:|---|---:|---|",
    ]
    for slot, (bucket, candidate) in enumerate(plan, 1):
        item = candidate.item
        lines.append(
            f"| {slot} | {bucket} | {item.term} | {item.domain} | {item.track} | "
            f"{candidate.suggested_level} | {suggested_form(candidate.suggested_level)} | "
            f"{candidate.priority:.1f} | {candidate.reason} |"
        )
    return "\n".join(lines)


def default_root() -> Path:
    return Path(__file__).resolve().parents[3]


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan adaptive security-specialist study topics from Markdown history.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    plan_parser = subparsers.add_parser("plan", help="Print a Markdown selection plan without changing files.")
    plan_parser.add_argument("--root", type=Path, default=default_root())
    plan_parser.add_argument("--date", type=as_date, default=date.today())
    plan_parser.add_argument("--count", type=int)
    plan_parser.add_argument("--focus", default="")
    plan_parser.add_argument("--mode", choices=["standard", "weak", "new", "subject-b", "light"], default="standard")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    root = args.root.resolve()
    catalog = load_catalog(root)
    if not catalog:
        print(f"error: no concept catalog found under {root / 'references' / 'taxonomy.md'}", file=sys.stderr)
        return 2
    terms = load_terms(root)
    catalog = merge_uncatalogued_terms(catalog, terms)
    today = args.date
    if today is None:
        print("error: --date must use YYYY-MM-DD", file=sys.stderr)
        return 2
    if args.count is not None and not 1 <= args.count <= 30:
        print("error: --count must be between 1 and 30", file=sys.stderr)
        return 2

    assessed = any(record.attempts > 0 for record in terms.values())
    if not assessed:
        count = args.count if args.count is not None else (3 if args.mode == "light" else 8)
        plan = diagnostic_plan(catalog, count, args.focus)
        phase = "diagnosis"
    else:
        count = args.count if args.count is not None else (3 if args.mode == "light" else 5)
        candidates = build_candidates(catalog, terms, today, recent_domain_counts(root), args.focus, args.mode)
        plan = adaptive_plan(candidates, count, args.mode)
        phase = "adaptive"
    print(render_plan(plan, phase, today))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
