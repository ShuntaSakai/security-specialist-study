# セッションMarkdown形式

## 新規セッション

理解・応用問題は `sessions/理解・応用問題/YYYY-MM-DD.md`、暗記語句問題は `sessions/暗記語句問題/YYYY-MM-DD.md` に保存する。同じ日付について両ディレクトリと旧パスにあるSession番号を確認し、全体の最大番号へ1を足す。これにより `Applied Sessions` とhistoryで使う `YYYY-MM-DD#Session番号` を一意に保つ。

旧 `sessions/YYYY-MM-DD.md`、`sessions/standard/YYYY-MM-DD.md`、`sessions/term-recall/YYYY-MM-DD.md` は読み込み・採点・progress再構築のため引き続き受け付けるが、新しいSessionは必ず日本語名のモード別ディレクトリへ書く。利用者が見るディレクトリ名と内部識別子は分離し、Sessionメタデータの `Mode: adaptive` / `Mode: term-recall` とCLIの `--mode standard` / `--mode term-recall` は変更しない。

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

ユーザーが明示できる問題数は、通常問題・暗記語句問題とも1〜30問とする。0以下または31以上は生成せず、範囲内の指定を求める。

`Question Count` は全Sessionで必須とし、1〜30の整数を1行だけ記載する。値は実際のQ見出し数と一致させ、Q見出しは `Q1` から重複・欠番なしの連番にする。`### Q` で始まる見出しはこの形式に完全一致させ、`QX`、`Q 2`、`Q01` のような数字以外・空白入り・先頭ゼロを許可しない。

`Primary Terms` には、その問題で独立に採点する中心概念だけを書く。比較問題で両方を十分に問う場合は複数でもよいが、同じSession内で同じPrimary Termを2問へ割り当てない。補助的に触れるだけの概念は `Related Terms` へ分ける。カタログ掲載語句は `taxonomy.md` の綴りと完全一致させる。問題文には曖昧な「説明せよ」だけでなく、評価する観点を列挙する。

## 暗記語句セッション

暗記語句問題は `sessions/暗記語句問題/YYYY-MM-DD.md` に書き、Sessionメタデータを次のようにする。

```md
## Session 2

- Created: 2026-08-12
- Status: awaiting_answers
- Mode: term-recall
- Question Count: 10
- Track A/B Target: 40% / 60%

### Q1

- Domain: Webセキュリティ
- Primary Terms:
  - `CSRF`
- Related Terms:
  - `CSRFトークン`
  - `SameSite`
- Level: 1
- Track: B

### 問題

CSRFとは何ですか？意味・目的・重要な特徴を簡潔に説明してください。

### 回答

<!-- この行の下に回答を書いてください -->
```

`Mode: term-recall` が暗記語句問題の判別子である。既存の `diagnosis`、`adaptive` などは通常説明問題として扱い、Mode自体がない旧Sessionも通常説明問題として読み込む。暗記語句問題はすべてLevel 1の短い語句説明形式とし、Trackによって長文化しない。各1問の `Primary Terms` は正確に1項目とし、1つのScoreで複数語句のRecall Scoreを更新しない。taxonomy上の複合名称は、1つのリスト項目として扱う。

現行の日本語名ディレクトリに保存するSessionは `Mode` を1行だけ必須とし、`diagnosis`、`adaptive`、`term-recall` 以外の値や重複を許可しない。`sessions/理解・応用問題/` は `diagnosis` または `adaptive`、`sessions/暗記語句問題/` は `term-recall` だけを許可し、ディレクトリとModeの不一致は拒否する。Modeなしを通常問題として扱うことや、配置によるMode制約を加えない後方互換は、旧直下と旧英語ディレクトリのSessionにだけ適用する。

問題数は指定がなければ10問。指定時は1〜30問の範囲とする。Aは `floor(問題数 × 0.40)`、Bは残り全部とし、10問ならA4/B6、5問ならA2/B3にする。taxonomyのTrack `B` はSessionでも `B`、Track `A` または `A/B` はこのモードの配分上 `A` として出題する。`progress/terms.md` のTrackはtaxonomyの値を維持する。

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
  --root . --date 2026-08-09 --session 1 --mode standard
```

暗記語句Sessionでは `--mode term-recall` を指定する。`--mode` は対象Sessionのモード検証に使い、省略時も日付・Session番号が一意なら自動解決する。新旧パスなど複数ファイルに同じ番号がある場合は、`Applied Sessions` のキー衝突を避けるため `--mode` の有無にかかわらず停止する。

`record` は全モードで、現行Sessionの `Mode` が1つの許可値であること、`Question Count` の必須性・一意性・1〜30の整数範囲、実際のQ見出し数との一致、Q番号が `Q1` から重複・欠番なしの連番であることを検証する。`### Q` で始まる形式外の見出しも見落とさず拒否する。自動補正は行わず、不一致があればprogressへ書き込む前に停止する。

暗記語句Sessionではさらに、各問のPrimary Termsが1項目、全問がLevel 1、TrackがリテラルのAまたはB、A/Bの実数が `A = floor(Question Count × 0.40)` / `B = 残り` であることも検証する。これにより、一つの回答で複数語句を評価したり、暗記問題を高難易度の証拠として誤反映したりすることを防ぐ。

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
