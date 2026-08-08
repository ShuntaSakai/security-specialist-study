# 出題分類と概念カタログ

## 使い方

- `Domain` は `progress/domains.md` と完全一致させる。
- `Track` は `B`（科目B中心）、`A/B`（両方）、`A`（主に科目A）を表す。
- `Importance` は1〜5。頻出性、科目Bでの説明必要性、他概念の前提度を合わせた値。
- `Entry Level` は未学習者へ最初に出す難易度。
- `Diagnostic` が `yes` の概念は初回診断で優先する。
- 新しい概念は、前提が未評価・低理解なら前提と組み合わせるか、難易度を下げる。

## 分野構造

| Domain | 主な到達目標 |
|---|---|
| Webセキュリティ | HTTP上の攻撃成立条件を読み、実装・運用双方の対策を説明する |
| 認証・認可 / IAM | 本人確認、セッション、権限判断、ID連携を区別して設計する |
| 暗号 | 機密性・完全性・真正性に合うプリミティブと運用を選ぶ |
| PKI・証明書 | 信頼連鎖、検証、失効確認、TLSでの役割を説明する |
| ネットワークセキュリティ | 通信、境界、経路、トンネル、検知・遮断をログと構成から読む |
| DNS | 名前解決、キャッシュ、委任、DNSSECと代表攻撃を説明する |
| メールセキュリティ | SMTPの弱点とSPF・DKIM・DMARCの判定を追う |
| マルウェア | 侵入、実行、永続化、C2、横展開、封じ込めを関連付ける |
| インシデントレスポンス | 検知から復旧・再発防止まで証拠を保ちながら判断する |
| ログ分析・監視 | 複数ログを時刻・主体・イベントで相関し、仮説を検証する |
| OSセキュリティ | 権限、プロセス、永続化、監査、ハードニングを説明する |
| クラウドセキュリティ | 責任共有、IAM、公開設定、鍵、ログ、ワークロードを守る |
| セキュアプログラミング | 入力・出力・状態・秘密情報・依存関係を安全に扱う |
| 脆弱性管理 | 発見、評価、優先順位、修正、例外、再確認を回す |
| リスク・ガバナンス | 資産・脅威・脆弱性・影響を基に対策と残存リスクを説明する |
| サプライチェーン | 開発・依存物・委託先・更新経路の信頼を検証する |
| ゼロトラスト | 継続的検証、最小権限、端末状態、分離を設計へ落とす |
| フォレンジック | 証拠保全、収集順序、タイムライン、完全性を説明する |

## 概念カタログ

`Related` は `/` 区切りです。表は補助スクリプトからも読み取るため、列名を変更しないでください。

| Term | Domain | Track | Importance | Entry Level | Diagnostic | Prerequisites | Related |
|---|---|---|---:|---:|---|---|---|
| SQLインジェクション | Webセキュリティ | B | 5 | 2 | yes | SQL / HTTPパラメータ | プレースホルダ / 二次SQLインジェクション / WAF |
| XSS | Webセキュリティ | B | 5 | 2 | no | HTML / JavaScript / Cookie | CSP / HttpOnly / SameSite / CSRF |
| CSRF | Webセキュリティ | B | 5 | 3 | no | Cookie / セッション管理 | CSRFトークン / SameSite / XSS |
| SSRF | Webセキュリティ | B | 4 | 3 | no | HTTP / 名前解決 | メタデータサービス / URL検証 / ネットワーク分離 |
| ディレクトリトラバーサル | Webセキュリティ | B | 4 | 2 | no | ファイルパス | 正規化 / allowlist / 権限分離 |
| セッション管理 | 認証・認可 / IAM | B | 5 | 2 | yes | HTTP / Cookie | セッション固定 / Cookie属性 / 再認証 |
| 多要素認証 | 認証・認可 / IAM | A/B | 5 | 2 | no | 認証要素 | フィッシング耐性 / WebAuthn / リスクベース認証 |
| OAuth 2.0 / OIDC | 認証・認可 / IAM | B | 5 | 3 | no | HTTP / 認証と認可の違い | 認可コード / PKCE / IDトークン |
| SAML | 認証・認可 / IAM | B | 4 | 3 | no | XML署名 / IdP / SP | Assertion / SSO / OAuth 2.0 |
| RBAC / ABAC | 認証・認可 / IAM | A/B | 4 | 3 | no | 最小権限 | IAM / 職務分離 / Policy |
| 共通鍵暗号と公開鍵暗号 | 暗号 | A/B | 5 | 2 | yes | 機密性 | ハイブリッド暗号 / 鍵配送 / TLS |
| ハッシュとMAC | 暗号 | A/B | 5 | 2 | no | 完全性 | HMAC / 電子署名 / パスワードハッシュ |
| AEAD | 暗号 | B | 4 | 3 | no | 共通鍵暗号 / MAC | AES-GCM / nonce / 認証タグ |
| 電子署名 | 暗号 | A/B | 5 | 3 | no | ハッシュ / 公開鍵暗号 | 否認防止 / 証明書 / タイムスタンプ |
| パスワードハッシュ | 暗号 | B | 5 | 3 | no | ハッシュ | salt / pepper / Argon2 / ストレッチング |
| 証明書チェーン検証 | PKI・証明書 | B | 5 | 3 | yes | 電子署名 / CA | ルートCA / 中間CA / ホスト名検証 |
| CRL / OCSP | PKI・証明書 | B | 5 | 3 | no | 証明書チェーン検証 | 証明書失効 / OCSP stapling / soft-fail |
| CSRと証明書発行 | PKI・証明書 | A/B | 3 | 2 | no | 公開鍵暗号 / CA | 秘密鍵 / SAN / 所有確認 |
| TLSハンドシェイク | PKI・証明書 | B | 5 | 4 | no | 証明書チェーン / 鍵共有 | SNI / Forward Secrecy / セッション再開 |
| ファイアウォールと状態管理 | ネットワークセキュリティ | A/B | 5 | 2 | yes | TCP/IP / ポート | ACL / ステートフル検査 / NAT |
| IDS / IPS | ネットワークセキュリティ | B | 4 | 3 | no | パケット / シグネチャ | 誤検知 / NIDS / 暗号化通信 |
| VPN（IPsec） | ネットワークセキュリティ | B | 5 | 3 | no | IP / 暗号 / 認証 | ESP / AH / IKE / トンネルモード |
| プロキシ / リバースプロキシ | ネットワークセキュリティ | B | 4 | 3 | no | HTTP / DNS | WAF / TLS終端 / Forwarded header |
| TCPの状態と代表攻撃 | ネットワークセキュリティ | A/B | 4 | 3 | no | 3-way handshake | SYN flood / sequence number / RST |
| DNSキャッシュポイズニング | DNS | B | 5 | 3 | yes | 再帰問い合わせ / キャッシュ | TXID / source port / DNSSEC |
| DNSSEC | DNS | B | 5 | 3 | no | DNS委任 / 電子署名 | RRSIG / DNSKEY / DS / 信頼の連鎖 |
| ゾーン転送と委任 | DNS | A/B | 4 | 2 | no | 権威DNS / NS | AXFR / glue record / lame delegation |
| DNSリバインディング | DNS | B | 3 | 4 | no | DNS / same-origin policy | TTL / SSRF / private network access |
| SPF | メールセキュリティ | B | 5 | 2 | yes | SMTP / DNS | DKIM / DMARC / envelope-from |
| DKIM | メールセキュリティ | B | 5 | 3 | no | 電子署名 / DNS | selector / header署名 / DMARC |
| DMARC | メールセキュリティ | B | 5 | 4 | no | SPF / DKIM | alignment / policy / aggregate report |
| SMTPリレーとSTARTTLS | メールセキュリティ | B | 4 | 3 | no | SMTP | オープンリレー / MTA-STS / downgrade |
| ランサムウェア | マルウェア | B | 5 | 3 | yes | マルウェア基礎 / バックアップ | 初期侵入 / 横展開 / C2 / 復旧 |
| C2通信 | マルウェア | B | 5 | 3 | no | DNS / HTTP | beaconing / DGA / EDR / sinkhole |
| 永続化と権限昇格 | マルウェア | B | 4 | 3 | no | OS権限 / プロセス | service / scheduled task / credential dumping |
| サンドボックス回避 | マルウェア | B | 3 | 4 | no | 仮想化 / 動的解析 | sleep / environment check / 難読化 |
| インシデント対応ライフサイクル | インシデントレスポンス | B | 5 | 3 | no | ログ / リスク | 検知 / 封じ込め / 根絶 / 復旧 |
| 証拠保全と初動 | インシデントレスポンス | B | 5 | 4 | no | 揮発性 / ハッシュ | chain of custody / 隔離 / メモリ取得 |
| プレイブックとエスカレーション | インシデントレスポンス | B | 4 | 3 | no | インシデント分類 | CSIRT / 連絡体制 / 判断基準 |
| Webアクセスログ分析 | ログ分析・監視 | B | 5 | 4 | no | HTTP / 時刻同期 | SQLi / traversal / status code |
| SIEM相関分析 | ログ分析・監視 | B | 5 | 4 | no | 複数ログ / 正規化 | use case / false positive / UEBA |
| EDRテレメトリ | ログ分析・監視 | B | 4 | 4 | no | プロセス / ネットワーク | process tree / hash / isolation |
| 時刻同期とログ完全性 | ログ分析・監視 | B | 4 | 3 | no | NTP / ハッシュ | タイムライン / 改ざん防止 / 保管期間 |
| Linux権限とsudo | OSセキュリティ | B | 4 | 3 | no | UID / permission | setuid / least privilege / auditd |
| Windows認証とイベントログ | OSセキュリティ | B | 4 | 4 | no | AD / Kerberos | Event ID / NTLM / credential dumping |
| OSハードニング | OSセキュリティ | A/B | 4 | 3 | no | 最小機能 / パッチ | CIS benchmark / service / audit |
| 責任共有モデル | クラウドセキュリティ | A/B | 5 | 2 | no | IaaS / PaaS / SaaS | IAM / 構成管理 / CSPM |
| クラウドIAMと一時資格情報 | クラウドセキュリティ | B | 5 | 4 | no | IAM / トークン | role / metadata service / least privilege |
| オブジェクトストレージ公開設定 | クラウドセキュリティ | B | 4 | 3 | no | ACL / policy | public access block / logging / encryption |
| 入力検証と出力エンコーディング | セキュアプログラミング | B | 5 | 3 | no | データフロー | XSS / SQLi / allowlist |
| TOCTOU | セキュアプログラミング | B | 3 | 4 | no | 並行処理 / ファイル権限 | race condition / atomic operation / symlink |
| シークレット管理 | セキュアプログラミング | B | 4 | 3 | no | 暗号鍵 / 環境変数 | vault / rotation / source repository |
| CVSSとリスクベース優先順位 | 脆弱性管理 | A/B | 5 | 3 | no | 脅威 / 影響 | EPSS / KEV / 資産重要度 |
| 脆弱性管理ライフサイクル | 脆弱性管理 | B | 4 | 3 | no | 資産管理 | scan / triage / remediation / verification |
| リスク対応 | リスク・ガバナンス | A/B | 5 | 2 | no | 資産 / 脅威 / 脆弱性 | 回避 / 低減 / 移転 / 受容 |
| ISMSとリスクアセスメント | リスク・ガバナンス | A/B | 4 | 3 | no | PDCA / 管理策 | リスク基準 / 残存リスク / SoA |
| SBOMと依存関係リスク | サプライチェーン | B | 4 | 3 | no | パッケージ管理 | SCA / 署名 / provenance / VEX |
| CI/CDパイプライン保護 | サプライチェーン | B | 4 | 4 | no | IAM / シークレット | artifact signing / runner / branch protection |
| ゼロトラスト原則 | ゼロトラスト | A/B | 4 | 3 | no | IAM / 端末管理 | 継続的検証 / microsegmentation / device posture |
| デジタルフォレンジック手順 | フォレンジック | B | 4 | 4 | no | 証拠保全 / ハッシュ | 揮発性順序 / disk image / timeline |

## 関連概念の扱い

弱い概念の `Related` は、そのまま新規候補にせず、前提関係を確認する。例:

- SPFが弱い: envelope-fromとDNS参照を確認してからDKIM・DMARCへ進む。
- OCSPが弱い: 証明書チェーンと失効の目的を確認し、CRL・OCSP staplingを比較する。
- XSSが弱い: 出力エンコーディングを核に、CSP、HttpOnly、SameSiteの「防げるもの・防げないもの」を区別する。
- 高得点の概念: 定義問題を繰り返さず、関連概念を混ぜた設定・ログ・判断問題へ移す。
