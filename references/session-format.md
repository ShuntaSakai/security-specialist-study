# セッションMarkdown形式

## 新規セッション

ファイル名は `sessions/YYYY-MM-DD.md`。同日のファイルがあれば最大のSession番号へ1を足して追記する。

```md
# 2026-08-09 セキスペ学習

## Session 1

- Created: 2026-08-09
- Status: awaiting_answers
- Mode: diagnosis
- Question Count: 8
- Subject B Target: 70–85%

### Q1

- Domain: Webセキュリティ
- Primary Terms:
  - `SQLインジェクション`
- Related Terms:
  - `プレースホルダ`
- Level: 2
- Track: B

### 問題

問題文を書く。Markdownのレンダリングでも表示される。

### 回答

<!-- この行の下に回答を書いてください -->
```

問題文は、メタデータの直後に置く `### 問題` 見出しの下へ通常のMarkdownとして書く。各Qには `### 問題`、`### 回答`、採点後は `### 採点` を一つずつ置く。Domain、Primary Terms、Related Terms、Level、Trackは適応処理に必要なので可視メタデータとして残す。語句名自体に `/` を含められるよう、Primary TermsとRelated Termsは必ず上例のような**1語句1行のコード表記リスト**にする。区切り文字で1行へ連結しない。

`Primary Terms` には、その問題で独立に採点する中心概念だけを書く。比較問題で両方を十分に問う場合は複数でもよいが、同じSession内で同じPrimary Termを2問へ割り当てない。補助的に触れるだけの概念は `Related Terms` へ分ける。カタログ掲載語句は `taxonomy.md` の綴りと完全一致させる。問題文には曖昧な「説明せよ」だけでなく、評価する観点を列挙する。

## 採点後

全回答を確認したら `Status` を `grading` へ変更し、各回答の直後へ採点を追記する。`graded` は3つのprogress更新がすべて完了した最後にだけ設定する。

```md
### 採点

Score: 72 / 100

#### 良かった点

- ...

#### 足りない点・誤解

- ...

#### 模範的な説明

...

#### 次回確認する観点

- ...
```

採点を書き終えたら、補助スクリプトの `record` コマンドでprogress更新とSession Summaryの確定を行う。

```bash
python3 skills/security-specialist-trainer/scripts/study_helper.py record \
  --root . --date 2026-08-09 --session 1
```

コマンドは `Applied Sessions` と履歴のDate/Sessionを使って冪等に更新する。同じコマンドを再実行してもAttemptsや履歴行を重複させない。共通するPrimary Termを含む複数Sessionは古い順に記録する。更新が完了すると、セッション末尾は次の形式になりStatusが `graded` へ変わる。

```md
## Session 1 Summary

- Average: 72 / 100
- Strong points: ...
- Weak points: ...
- Recommended next review: 2026-08-11
- Progress updated: terms.md / domains.md / history.md
```

## 状態判定

- `awaiting_answers`: 一つ以上の回答が未記入。記入済みだけを勝手に部分採点しない。
- `ready_for_grading`: 任意。ユーザーまたはSkillが全回答記入を確認した状態。
- `grading`: 問題別採点は存在するが、progress更新が途中または未確認。`record` を再実行して復旧できる。
- `graded`: 問題別採点とprogress更新が完了。
- `cancelled`: ユーザーが明示的に中止した場合だけ使う。

「採点して」では日付指定がなければ、まず `grading` のSessionを復旧対象にし、その後で日付降順・Session番号降順の `awaiting_answers` または `ready_for_grading` を使う。`graded` と `cancelled` は対象外。複数ある場合は対象ファイルとSession番号をチャットで明示する。
