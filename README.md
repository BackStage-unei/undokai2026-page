# BackStage 大運動会2026 — 案内ページ

大運動会2026（2026/8/17〜8/23）の案内ページを共有管理するリポジトリです。
**ユーザー向け**と**キャスト向け**の2ページを、同じデザイン基盤で公開します。

## ページ構成

| ファイル | 公開URL | 読み手 | 内容 |
|---|---|---|---|
| `index.html` | `/undokai2026-page/` | 一般ユーザー | イベント紹介・ルール・参加キャスト・特典・FAQ |
| `cast.html` | `/undokai2026-page/cast.html` | 参加キャスト | 上記＋運営リーダー・判定条件・PV音声収録・Discord窓口 |

2ページは同じCSS・ローダー・チームタブ・キャスト詳細モーダルを共有しています。
`cast.html` は `noindex,nofollow` を付けて検索避けしていますが、**技術的な閲覧制限はありません**
（public リポジトリ＋GitHub Pages のため、URLを知っていれば誰でも見られます）。

### 出し分けの原則

`cast.html` にだけ載せてよいもの:
運営リーダー名／PV音声収録の依頼・提出フォーム・提出先メール／Discordチャンネルへのリンク／
ミッションの判定条件の詳細／「本ページは参加キャスト向けの案内です」の注記。

**どちらにも載せてはいけないもの**:
予算・報酬額・内部の必要売上／チーム分けアルゴリズム／運営担当者の実名（`cast.html` の運営リーダーを除く）／
データ分析の内部指標／未確定の具体数値。

## その他のファイル

| パス | 内容 |
|---|---|
| `assets/pv-preview/pv-preview-0N.png` | `cast.html` のPVプレビュー画像（相対参照） |
| `assets/ogp-undokai2026.jpg` | `index.html` のOGP画像（1200×675） |
| `tests/test_user_page.py` | `index.html` のセルフチェック |
| `tests/test_cast_page.py` | `cast.html` のセルフチェック |

## 実装方針

- HTML・CSS・JavaScript・キャスト画像（base64）を1ファイル内に保持する
- 例外は `assets/` 配下の2種類だけ。PVプレビュー画像は相対パス参照、OGP画像はメタタグからの絶対URL参照
- 外部リソースの読み込みは Google Fonts のみ（`Dela Gothic One` / `LINE Seed JP`）。
  日本語フォントの埋め込みは現実的でないため許容している
- 参加キャスト一覧は**静的HTMLとして出力済み**。JavaScript はタブ切り替えと詳細モーダルの制御のみで、
  JavaScript無効でも54名すべてが表示される
- **サブディレクトリを作らないこと**。`assets/pv-preview/...` の相対参照が壊れる

## テストの実行

```bash
python3 tests/test_user_page.py
python3 tests/test_cast_page.py
```

Chrome があればモーダル・ディープリンク・タブ切り替え・PV収録チェックの保存まで検査します。
無い場合はその項目だけ SKIP になります。

## 編集時の注意

- base64の画像データ行を手作業で編集しない
- **編集元は Obsidian Vault 側**（`work_ob/10_イベント/大運動会2026/daiundokaihp_user.html` と
  `daiundokaihp_cast.html`）。そちらを直してから同期する
- ルールの数値を変えるときは2ページとも直す。テストが両方で同じ確定値を検査している
- 「のべ」「延べ」は使わない。**「合計接客人数」**に統一する
- 外部リソースを追加する場合は、テストの許可ホストリストを確認する
- push 前に両方のテストを通す。`main` へのマージ＝GitHub Pages への即時公開
