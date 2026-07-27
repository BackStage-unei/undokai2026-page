# BackStage 大運動会2026 — キャスト向け案内ページ

大運動会2026（2026/8/17〜8/23）の参加キャスト向け案内ページを共有管理するリポジトリです。GitHub Pagesでは`index.html`を公開します。

## ファイル構成

| ファイル | 内容 |
|---|---|
| `イベント概要_大運動会2026.html` | 編集元となるページ本体 |
| `index.html` | GitHub Pagesで公開するページ |
| `undo-kai.html` | 同内容の予備ファイル |
| `tests/test_event_page.py` | 文言、構造、画像数、3ファイルの一致などを検査するセルフチェック |

## 実装方針

- HTML・CSS・画像・JavaScriptをHTMLファイル内に保持
- 外部JavaScript・外部CSS・外部画像の読み込みなし
- モバイル用メニューとチーム画像の再利用に小さなインラインJavaScriptを使用
- `イベント概要_大運動会2026.html`を編集元とし、`index.html`と`undo-kai.html`へ同期

## GitHub Pagesへの反映

1. `イベント概要_大運動会2026.html`を編集
2. `index.html`と`undo-kai.html`へ同じ内容を同期
3. `python3 tests/test_event_page.py`を実行
4. 3ファイル一致と全テスト成功を確認してpush

## テストの実行

```bash
python3 tests/test_event_page.py
```

Chromeがない環境では、Chromeを使う画面描画項目のみ`SKIP`になります。

## 編集時の注意

- base64の画像データ行を手作業で編集しない
- 外部リソースを追加する場合は、公開範囲とテストの許可リストを確認する
- 掲載禁止: 予算・報酬額・内部の必要売上・チーム分けアルゴリズム・運営担当者名・未確定の具体数値
- 直接編集した場合も、同期とテストを完了してからpushする
