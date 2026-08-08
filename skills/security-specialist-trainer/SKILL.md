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

- Put only the question text inside an HTML comment.
- Keep Domain, Primary Terms, Related Terms, Level, and Track visible as metadata. Put only independently scored concepts in Primary Terms; put supporting context in Related Terms.
- Add an empty `### 回答` area with the standard placeholder comment.
- Ask for explanation, causality, conditions, application, or comparison. Avoid pure term-to-definition recall unless Level 1 is justified.
- Match Level 1–3 to weak concepts and Level 4–6 to demonstrated mastery.
- Move strong concepts toward short logs, traffic, settings, incident narratives, competing controls, and residual risk.
- Avoid repeating materially identical wording from recent sessions.
- Do not include answers or leading hints in the question file.

After writing, verify the file, question count, unique numbering, metadata, hidden question comments, and answer placeholders. In chat, respond briefly with the absolute clickable session path, question count, and any requested emphasis. Do not duplicate all question text in chat.

## Grade a session

Perform these steps in order:

1. Find the newest session whose Status is not `graded`, unless the user names a date or Session number.
2. Read every question, its metadata, and the user's full answer. Ignore HTML placeholder comments.
3. If any answer is blank, do not fabricate or partially finalize scores. Identify the unanswered question numbers and leave progress unchanged.
4. Score each answer from 0 to 100 for conceptual meaning. Select only applicable rubric dimensions: definition, principle, conditions, scenario/application, countermeasures with reasons, comparison/limits. Normalize applicable weights to 100.
5. Append concise feedback under each answer: score, good points, missing or mistaken points, a short model explanation, and one next-review focus.
6. Change that Session Status to `graded` and append its summary.
7. Update `progress/terms.md` using difficulty caps and the weighted mastery formula. Treat `Primary Terms` as central concepts. Do not numerically update `Related Terms` unless the answer independently demonstrated them; if it did, use half update weight and do not increment Attempts or Average as though they were central.
8. Update `progress/domains.md` from term mastery (70%) and the latest five answers in that domain (30%). Do not count unassessed terms as zero.
9. Append one row to `progress/history.md`. Include average, Subject B ratio, weak/strong domains, next focus, and the relative session link.
10. Set each assessed term's Next Review using current mastery, answer score, difficulty, and stable high performance.

Use `../../references/scoring-rules.md` as the arithmetic authority. Preserve existing manual notes unless replacing them with more specific evidence. Keep all three progress files mutually consistent: the same date, domain name, question count, average, and next-review conclusions must agree.

After editing, reread the graded Session and the three progress files. Confirm one score per question, a correct arithmetic average, no duplicate term row, and no duplicate history row. In chat, report the session average, strongest point, most important gap, and next review date; link the session file.

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
