# TLS 1.3ハンドシェイク

この図は、Forward Secrecyを得るECDHE鍵共有を使う典型的なTLS 1.3の流れです。TLS 1.2以前とはメッセージの順序や暗号化される範囲が異なります。

```mermaid
sequenceDiagram
    participant Browser as ブラウザ
    participant Server as Webサーバ
    participant Store as ブラウザの信頼ストア

    Browser->>Server: ブラウザがClientHelloを送る（対応TLS版・暗号方式・SNI・一時公開鍵）
    Server->>Browser: WebサーバがServerHelloを返す（選択した方式・一時公開鍵）
    Note over Browser,Server: 両者は自分の一時秘密鍵と相手の一時公開鍵から同じ共有秘密を計算する
    Note over Browser,Server: ServerHello以降のハンドシェイクメッセージは、共有秘密から得た鍵で暗号化される

    Server->>Browser: WebサーバがEncryptedExtensionsを送る
    Server->>Browser: WebサーバがCertificateを送る
    Server->>Browser: WebサーバがCertificateVerifyを送る（証明書に対応する秘密鍵で署名）
    Server->>Browser: WebサーバがFinishedを送る

    Browser->>Store: ブラウザが信頼済みルートCA証明書を取得する
    Browser->>Browser: ブラウザが証明書チェーン・有効期限・SAN・失効状態を確認する
    Browser->>Browser: ブラウザがCertificateVerifyの署名を検証し、Webサーバの秘密鍵保持を確認する
    Browser->>Browser: ブラウザがWebサーバのFinishedを検証する

    alt 証明書またはFinishedの検証に失敗
        Browser-->>Server: ブラウザが接続を中止する
    else すべての検証に成功
        Browser->>Server: ブラウザがFinishedを送る
        Note over Browser,Server: ハンドシェイク完了。以後は別途導出したアプリケーションデータ用鍵を使う
        Browser->>Server: ブラウザが暗号化したHTTPリクエストを送る
        Server->>Browser: Webサーバが暗号化したHTTPレスポンスを返す
    end

    Note over Browser,Server: 一時秘密鍵は通信後に破棄する。後から長期秘密鍵が漏えいしても、記録済み通信の復号を困難にする（Forward Secrecy）
```

- `SNI` は、ブラウザが接続したいホスト名をWebサーバへ知らせる拡張である。
- `CertificateVerify` は、Webサーバが証明書内の公開鍵に対応する秘密鍵を実際に持つことを示す。
- `Finished` は、それまでのハンドシェイク内容を基に検証し、途中で改ざんされていないことを確認する。
