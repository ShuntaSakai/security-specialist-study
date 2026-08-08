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
- Primary Terms: SQLインジェクション
- Related Terms: プレースホルダ
- Level: 2
- Track: B

<!--
問題文を書く。Markdownのレンダリングでは隠れるが、ソースを開けば読める。
-->

### 回答

<!-- この行の下に回答を書いてください -->
```

問題文だけをコメント内へ置く。Domain、Primary Terms、Related Terms、Level、Trackは適応処理に必要なので可視メタデータとして残す。`Primary Terms` には、その問題で独立に採点する中心概念だけを書く。比較問題で両方を十分に問う場合は複数でもよい。補助的に触れるだけの概念は `Related Terms` へ分ける。問題文には曖昧な「説明せよ」だけでなく、評価する観点を列挙する。

## 採点後

`Status` を `graded` へ変更し、各回答の直後へ追記する。

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

セッション末尾にも次を追記する。

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
- `graded`: 問題別採点とprogress更新が完了。
- `cancelled`: ユーザーが明示的に中止した場合だけ使う。

「採点して」では日付指定がなければ、日付降順・Session番号降順で最初の未採点セッションを使う。複数ある場合は対象ファイルとSession番号をチャットで明示する。
