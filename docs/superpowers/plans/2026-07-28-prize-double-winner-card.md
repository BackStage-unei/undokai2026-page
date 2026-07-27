# Prize Double Winner Card Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 賞品欄に金色の「優勝チーム」カードを2つ表示し、集合SDイラスト制作と店舗掲出特典を別々のカードに分ける。

**Architecture:** 現在の賞品欄のHTML構造だけを変更し、既存の `.prize-rank-card` と `.prize-rank-gold` のスタイルを再利用する。正本の `index.html` を変更後、同内容を2つの配布用HTMLへ同期する。

**Tech Stack:** 静的HTML、CSS、ネイティブ `<details>`、ブラウザー表示確認

## Global Constraints

- 上段の金色カードには集合SDイラスト制作の文章だけを表示する。
- 上段の金色カードの直後に、自遊空間への掲出予定と掲出期間を表示する。
- 下段の金色カードにはパネル設置とブースPOP掲出だけを表示する。
- 準優勝カード、Discordリンク、注記、ほかのセクションは変更しない。
- 全体テストは実行せず、賞品欄の構造確認と390px幅の表示確認だけを行う。

---

### Task 1: 優勝チームの賞品を2つの金色カードへ分割

**Files:**
- Modify: `index.html`
- Modify: `undo-kai.html`
- Modify: `イベント概要_大運動会2026.html`
- Modify: `tests/test_event_page.py`

**Interfaces:**
- Consumes: 既存の `.prize-rank-grid`、`.prize-rank-card`、`.prize-rank-gold`、`.prize-rank-list`
- Produces: `.prize-rank-gold` が2要素あり、1つ目に `.prize-main`、2つ目に2件の `.prize-rank-list li` を持つ賞品欄

- [x] **Step 1: 構造チェックを2枠仕様へ更新する**

`tests/test_event_page.py` の賞品欄ランタイム確認を次の条件へ変更する。

```javascript
const goldCards = prizeSection.querySelectorAll(".prize-rank-gold");
const illustrationCard = goldCards[0];
const placementCard = goldCards[1];

results.prizeSummaryFirst =
  goldCards.length === 2
  && illustrationCard.querySelector(".prize-main")?.textContent.includes(
    "優勝チームには、チームメンバー全員の描き下ろし「集合SDイラスト」を制作します。"
  )
  && illustrationCard.querySelectorAll(".prize-rank-list li").length === 0
  && placementCard.querySelectorAll(".prize-rank-list li").length === 2
  && silverBenefits.length === 1;
```

- [x] **Step 2: 現状が2枠条件を満たさないことを確認する**

ブラウザーの賞品欄で次を評価する。

```javascript
document.querySelectorAll(
  '[data-section-id="prize"] .prize-rank-gold'
).length
```

Expected: `1`

- [x] **Step 3: 集合SDイラスト制作を独立した金色カードへ分ける**

`index.html` の `.prize-rank-grid` 冒頭を次の構成にする。

```html
<div class="prize-rank-card prize-rank-gold">
  <p class="prize-rank-label">優勝チーム</p>
  <p class="prize-main">優勝チームには、チームメンバー全員の描き下ろし「<strong>集合SDイラスト</strong>」を制作します。</p>
</div>
<div class="prize-rank-card prize-rank-gold">
  <p class="prize-rank-label">優勝チーム</p>
  <ul class="prize-rank-list">
    <li>集合SDイラストを店舗に<strong>パネル設置</strong></li>
    <li>店内ブース席に<strong>チームのブースPOPを掲出</strong></li>
  </ul>
</div>
```

- [x] **Step 4: 配布用HTMLを同期する**

`index.html` と同じ内容を `undo-kai.html`、`イベント概要_大運動会2026.html` に反映し、3ファイルが一致することを `cmp -s` で確認する。

- [x] **Step 5: 賞品欄だけをモバイル確認する**

`http://localhost:8000/index.html?v=double-winner-card` を390px幅で開き、次を確認する。

```javascript
({
  goldCards: document.querySelectorAll(
    '[data-section-id="prize"] .prize-rank-gold'
  ).length,
  overflow:
    document.documentElement.scrollWidth >
    document.documentElement.clientWidth
})
```

Expected:

```javascript
{ goldCards: 2, overflow: false }
```

- [x] **Step 6: 変更をコミットする**

```bash
git add tests/test_event_page.py index.html undo-kai.html イベント概要_大運動会2026.html
git commit -m "fix: split winner prizes into two cards"
```
