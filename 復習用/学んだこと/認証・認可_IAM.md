# 認証・認可 / IAM

## 2026-08-21

### SAMLによる認証連携

- SAMLは、IdP（Identity Provider）が認証した利用者の情報を含むSAML Assertionを、SP（Service Provider）へ渡してシングルサインオンを実現するXMLベースの認証連携標準である。
- SPはAssertionをそのまま信用せず、IdPの署名、発行者、宛先、対象者、有効期限などを検証する。IdPが利用者を認証し、SPが検証済みAssertionに基づいて利用を許可する役割分担を押さえる。
