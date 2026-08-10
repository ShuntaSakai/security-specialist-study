---
name: security-specialist-trainer
description: Markdown-based adaptive trainer for Japan's Registered Information Security Specialist exam (情報処理安全確保支援士・セキスペ), emphasizing written explanations and Subject B scenarios. Use when the user asks to create or customize セキスペ practice questions (問題作って、今日の問題、復習、科目B、特定分野), grade or review answers (採点、答え合わせ、レビュー), or report mastery, strengths, weaknesses, and due reviews (理解度、今日の結果、弱点).
---

# Security Specialist Trainer

Build recall and explanation skill from Markdown history. Treat the repository containing this skill as the study root: from this file, resolve `../..` as the root. Keep `sessions/` and `progress/` as the source of truth; never replace them with JSON state.

## Route the request

Choose one workflow:

- Create questions: follow **Generate a session**.
- Grade answers: follow **Grade a session**.
- Show results or mastery: follow **Report progress**.
- Combine requests only when the user clearly asks for both; finish grading before generating later adaptive questions.

Read [session-format.md](../../references/session-format.md) before writing or grading a session. Read [scoring-rules.md](../../references/scoring-rules.md) before selecting adaptive questions or assigning scores. Read [taxonomy.md](../../references/taxonomy.md) when introducing concepts, checking prerequisites, or resolving domains and related terms.

## Generate a session

Perform these steps in order:

1. Obtain the actual local date as `YYYY-MM-DD`; do not infer it from an old session filename.
2. Read every file under `progress/`.
3. Read the latest three session files, including every session in those files. Read more only when notes or related weaknesses require it.
4. Inspect domain scores, term scores, last-study dates, attempts, averages, recent difficulty, next-review dates, and recent domain mix.
5. Estimate forgetting and priority using `../../references/scoring-rules.md`.
6. Run the deterministic planner unless it is unavailable:

   ```bash
   python3 skills/security-specialist-trainer/scripts/study_helper.py plan \
     --root . --date YYYY-MM-DD
   ```

   Add `--count N`, `--focus 'Webセキュリティ'`, or `--mode weak|new|subject-b|light` to reflect the request. Use the planner as a candidate plan, not as permission to ignore prerequisites or recent question wording.
7. Select questions with approximately 40% weak, 25% due, 20% new, and 15% strong/challenge slots. Keep Subject B material around 70–85%. Honor explicit count, focus, or style over default ratios.
8. Write the questions to `sessions/YYYY-MM-DD.md` using the next Session number. Create the file heading if absent; otherwise append without changing earlier sessions.

Use eight cross-domain Level 2–3 questions for an unassessed first session unless the user specifies a count or asks for light practice. For the default eight, use exactly one question from each of Web, network, cryptography, authentication, PKI, DNS, email, and malware; do not substitute another domain. Use five questions normally and three for light practice.

For each question:

- Add a `### 問題` heading directly below the metadata, then write the question text as regular Markdown below that heading. Do not put question text inside an HTML comment.
- Keep Domain, Primary Terms, Related Terms, Level, and Track visible as metadata. Write Primary Terms and Related Terms as one backtick-wrapped concept per nested Markdown list item; never join terms with `/` or another delimiter. Put only independently scored concepts in Primary Terms, use exact taxonomy spelling, and put supporting context in Related Terms.
- Add an empty `### 回答` area with the standard placeholder comment.
- Ask for explanation, causality, conditions, application, or comparison. Avoid pure term-to-definition recall unless Level 1 is justified.
- Match Level 1–3 to weak concepts and Level 4–6 to demonstrated mastery.
- Move strong concepts toward short logs, traffic, settings, incident narratives, competing controls, and residual risk.
- Avoid repeating materially identical wording from recent sessions.
- Do not include answers or leading hints in the question file.

After writing, verify the file, question count, unique numbering, metadata, one `### 問題` heading per question, visible question text, and answer placeholders. In chat, respond briefly with the absolute clickable session path, question count, and any requested emphasis. Do not duplicate all question text in chat.

## Grade a session

Perform these steps in order:

1. Resume the newest `grading` Session first. Otherwise find the newest `awaiting_answers` or `ready_for_grading` Session, unless the user names a date or Session number. Never select `graded` or `cancelled`.
2. Read every question, its metadata, and the user's full answer. Ignore HTML placeholder comments.
3. If any answer is blank, do not fabricate or partially finalize scores. Identify the unanswered question numbers and leave progress unchanged.
4. Score each answer from 0 to 100 for conceptual meaning. Select only applicable rubric dimensions: definition, principle, conditions, scenario/application, countermeasures with reasons, comparison/limits. Normalize applicable weights to 100.
5. Change the Session Status to `grading`. Upsert concise feedback under each answer: score, good points, missing or mistaken points, a short model explanation, and one next-review focus. On recovery, replace an existing grading block instead of appending a duplicate.
6. For each graded answer, decide whether a Mermaid diagram would make a difficult flow materially easier to review. Create one only for concepts involving multiple actors, ordered processing steps, branching conditions, trust/key/data movement, or incident/control sequences; do not create diagrams for isolated definitions or relationships that a short sentence makes clear.
   - Before creating anything, inspect every Markdown file under `復習用/`. If an existing diagram already covers the same learning goal and flow (including a more detailed version), reuse it and do not create a duplicate.
   - For a genuinely new diagram, create `復習用/<topic>.md` with a descriptive, stable topic name and a fenced `mermaid` diagram. Use the diagram type that best fits the flow (`flowchart`, `sequenceDiagram`, or `stateDiagram-v2`), label actors, inputs, conditions, and outcomes clearly, and keep it compact enough for review.
   - When a flow involves actors, make the subject, recipient, and object explicit. Prefer `sequenceDiagram` for exchanges between actors; otherwise write edge labels as “who does what to whom/what,” such as “ブラウザがWebサーバへサーバ証明書を要求する.” Do not use ambiguous labels such as “送付” or “接続” by themselves. Use short labels and avoid HTML line-break tags when a renderer may not support them.
   - Treat these diagrams as durable review notes: make them technically correct and standalone, and do not alter an existing diagram merely to cover an unrelated question.
7. Run the idempotent recorder only after every question has one valid score:

   ```bash
   python3 skills/security-specialist-trainer/scripts/study_helper.py record \
     --root . --date YYYY-MM-DD --session N
   ```

8. Let the recorder update `terms.md`, recompute `domains.md`, upsert `history.md`, append or replace the Session Summary, and change Status to `graded` last. It uses `Applied Sessions` to avoid double-counting after interruption. Record overlapping Primary Terms in chronological Session order.
9. If the recorder fails, leave Status as `grading`, report the error, and retry after correcting it. Never claim progress was updated and never set `graded` manually before all three progress files succeed.

Use `../../references/scoring-rules.md` as the arithmetic authority. Update only Primary Terms numerically; Related Terms remain context until directly assessed. Keep all three progress files mutually consistent: the same date, domain name, question count, average, and next-review conclusions must agree. If the recorder is unavailable, reproduce its ordering and idempotency rules manually and mark `graded` only as the final write.

After editing, reread the graded Session and the three progress files. Confirm one score per question, a correct arithmetic average, no duplicate term row, and no duplicate history row. If a new review diagram was created, render or otherwise verify that its Mermaid syntax is valid before reporting it. In chat, report the session average, strongest point, most important gap, next review date, and links to any newly created review diagrams; link the session file.

## Report progress

Read all files under `progress/` and enough recent sessions to explain the current estimates. Report concisely:

1. Overall weighted picture and whether evidence is still provisional.
2. Domain scores and levels.
3. Especially weak terms.
4. Especially strong terms, including the highest level actually demonstrated.
5. Terms due now or soon and the reason.

Never calculate an overall score by treating `Unassessed` domains as zero. Distinguish current mastery from lifetime average. For “today's result,” summarize today's latest graded session and mention whether progress files were updated.

## Preserve learning quality

- Assess the user's own explanation, not keyword overlap with a model answer.
- Treat a correct conclusion with faulty reasoning as incomplete.
- Require why a countermeasure works and note its limits when the question asks for them.
- Do not permanently retire a 100-point concept. Schedule it later and raise its problem form.
- Introduce related terms through prerequisites and clusters, not random novelty.
- Keep model explanations compact enough that the next attempt still requires retrieval.
- Ask a concise clarification only when multiple ungraded sessions make the target genuinely ambiguous and the user's wording does not select one.
