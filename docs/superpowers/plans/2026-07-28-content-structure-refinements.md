# Content Structure Refinements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 合意済みの7項目を、既存デザインとデータを維持しながらモバイル向けに整理する。

**Architecture:** `index.html` を正本とし、文章・配置はHTMLで更新する。チーム発表とPVチーム切替は、既存DOMを入力にした段階的強化として既存スクリプトへ追加し、完成後に同一内容を配布用HTML 2ファイルへ同期する。

**Tech Stack:** HTML5、CSS、Vanilla JavaScript、Pythonによる既存の静的検査、ブラウザによる局所確認

## Global Constraints

- GitHub Pagesで動作する静的サイトとする。
- モバイル閲覧を優先する。
- 既存のチーム画像、セリフ、ファイル名、配色は維持する。
- 全テストは実行せず、変更箇所だけを確認する。

---

### Task 1: 集計案内と賞品の情報順を整理

**Files:**
- Modify: `index.html`
- Test: `tests/test_event_page.py`

**Interfaces:**
- Consumes: `#rules`、`#schedule`、`#prize` の既存DOM
- Produces: 重複しない集計案内と、順位別賞品を先に読めるDOM

- [ ] **Step 1: 静的検査を更新**

`#rules` の集計案内が1箇所であること、`#schedule` の集計カードと末尾注記がないこと、4日目に「20:00締め」があること、賞品名が補足より先にあることを検査する。

- [ ] **Step 2: 変更前HTMLで対象検査が失敗することを確認**

既存HTMLを対象に、重複要素と文言順を抽出して差分を記録する。

- [ ] **Step 3: HTMLを最小変更**

デイリーミッションとスケジュールの重複カードを削除し、末尾案内・4日目表示・賞品カードの文章順を仕様どおりに更新する。

- [ ] **Step 4: 対象検査を再実行**

変更した文言の出現数とDOM順だけを確認する。

### Task 2: チーム発表を組別トグル化

**Files:**
- Modify: `index.html`
- Test: `tests/test_event_page.py`

**Interfaces:**
- Consumes: `#teams .team-card` 6件
- Produces: `enhanceTeamRosterToggles()` が生成する `details.team-card-toggle` 6件

- [ ] **Step 1: ブラウザ検査条件を追加**

6件が `details` であり、初期状態が閉じ、summaryクリックで9名を表示する条件を追加する。

- [ ] **Step 2: 変更前画面で条件が未達であることを確認**

現状の `.team-card` が常時展開されていることを確認する。

- [ ] **Step 3: CSSとJavaScriptを追加**

既存カードのチーム名をsummaryへ、メンバー一覧をdetails本文へ移し、44px以上の操作領域とチーム色を維持する。

- [ ] **Step 4: 390px幅で局所確認**

6組が閉じ、1組を開くと9名が表示され、横スクロールが発生しないことを確認する。

### Task 3: PVセリフ4・5をチーム切替カードへ変更

**Files:**
- Modify: `index.html`
- Test: `tests/test_event_page.py`

**Interfaces:**
- Consumes: `.pv-team-grid [data-team-index]` 6件と各 `.pv-team-line` 2件
- Produces: `enhancePvTeamBranches()` が生成する `.pv-branch-card` 2件、各6ボタン・6パネル

- [ ] **Step 1: ブラウザ検査条件を追加**

セリフ4・5のカード数が2、各カードのチームボタンが6、表示パネルが1、表示画像が9であることを検査する。

- [ ] **Step 2: 変更前画面で条件が未達であることを確認**

現状が6チームの常時表示であり、セリフ4・5の独立カードがないことを確認する。

- [ ] **Step 3: CSSとJavaScriptを追加**

既存チームカードから2つのカードを生成し、ボタン操作で `aria-selected` と各パネルの `hidden` を同期する。元の一覧はJavaScript成功後だけ非表示にする。

- [ ] **Step 4: 390px幅で局所確認**

赤組から青組へ切り替え、セリフ・ファイル名・9名の画像が更新されることと横スクロールがないことを確認する。

### Task 4: 録音方法を再構成

**Files:**
- Modify: `index.html`
- Test: `tests/test_event_page.py`

**Interfaces:**
- Consumes: `.pv-recording-tips`、`.pv-route-a`、`.pv-route-b`、`.pv-submit`
- Produces: 録音のコツ→Route A→Route Bの順序と、Route A内の提出フォーム

- [ ] **Step 1: DOM順の静的検査を追加**

録音のコツがRoute Aより前、Route AがRoute Bより前、提出フォームがRoute Aの子孫であることを検査する。

- [ ] **Step 2: 変更前HTMLで順序条件が失敗することを確認**

現在の録音のコツと独立提出欄の位置を抽出する。

- [ ] **Step 3: HTMLと余白CSSを更新**

録音のコツを先頭へ移動し、提出説明とボタンをRoute Aへ移し、独立見出しを削除する。

- [ ] **Step 4: 対象箇所をブラウザ確認**

順序、左揃え、フォームリンク、Route Bメール案内が読みやすいことを確認する。

### Task 5: 配布用HTML同期と局所検証

**Files:**
- Modify: `undo-kai.html`
- Modify: `イベント概要_大運動会2026.html`

**Interfaces:**
- Consumes: 完成した `index.html`
- Produces: 同一内容の配布用HTML 2ファイル

- [ ] **Step 1: 3ファイルを同期**

`index.html` の完成内容を2つの配布用HTMLへ反映する。

- [ ] **Step 2: 差分と構文を確認**

3ファイルが一致し、`git diff --check` が成功することを確認する。

- [ ] **Step 3: 変更箇所のみブラウザ確認**

デイリーミッション、スケジュール、特典、PV音声収録、チーム発表を確認し、全テストは実行しない。

- [ ] **Step 4: コミット**

対象HTML、テスト、設計・計画文書だけをステージし、変更を保存する。
