# Main準拠モバイル・トグル対応 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `main`由来の全情報とデザインを維持したまま、11セクションのトグル、ハンバーガーからの直接移動、優勝賞品Discordリンクを追加する。

**Architecture:** 現在の3つのHTMLは単一ファイル構成とbyte-identical同期を維持する。既存セクションのHTMLは書き直さず、ページ末尾のJavaScriptが各`section`の既存子要素を標準`details`へ移動して包むプログレッシブエンハンスメントとし、JavaScriptなしでは元ページどおり全内容を表示する。

**Tech Stack:** HTML5、CSS3、Vanilla JavaScript、Python 3の既存セルフチェック、GitHub Pages

## Global Constraints

- `main`の青・白・濃紺・注意用オレンジの配色と運動会モチーフを維持する。
- ABOUT、TEAMS、RULE 01〜04、SCHEDULE、PRIZE、PV VOICE、FAQ、CONTACTの11分類を統合しない。
- 本文、数値、表、図解、54名の画像・名前、PVセリフ・ファイル名を削除・要約しない。
- 初期表示はイベント概要だけを開き、ほかのトグルは閉じる。
- 複数トグルを同時に開ける。
- JavaScriptなしでは元ページと同じ全展開表示にする。
- 390px、768px、1280pxで横スクロールを発生させない。
- 3つのHTMLを常にbyte-identicalに保つ。
- 外部依存を追加しない。

---

## File Map

- `index.html`: 公開本体。既存本文、インラインCSS、インラインJavaScriptを保持し、賞品リンクとトグル機能を追加する。
- `イベント概要_大運動会2026.html`: `index.html`と同一内容を維持する互換ページ。
- `undo-kai.html`: `index.html`と同一内容を維持する互換ページ。
- `tests/test_event_page.py`: 内容保持、賞品リンク、トグル構造、ハッシュ連動、レスポンシブ契約を検証する。

---

### Task 1: 優勝賞品Discordリンク

**Files:**
- Modify: `tests/test_event_page.py:224-260`
- Modify: `tests/test_event_page.py:425-470`
- Modify: `index.html:4404-4492`
- Modify: `イベント概要_大運動会2026.html`
- Modify: `undo-kai.html`

**Interfaces:**
- Consumes: 既存の`section_block(text, "prize")`とURL allowlist。
- Produces: `PRIZE_DETAIL_URL`で表す優勝賞品詳細リンク。後続タスクはこのHTMLを変更しない。

- [ ] **Step 1: 賞品リンクの失敗テストを追加する**

`tests/test_event_page.py`の定数へ追加する。

```python
PRIZE_DETAIL_URL = (
    "https://discord.com/channels/1138387287986679879/"
    "1528011762572595231/1529844197350309939"
)
```

`allowed_urls`へ`PRIZE_DETAIL_URL`を追加し、`prize_block = section_block(text, "prize")`と既存の`prize_missing`検査の直後へ次を追加する。

```python
prize_detail_ok = (
    prize_block.count(PRIZE_DETAIL_URL) == 1
    and "優勝賞品の詳細をDiscordで確認" in visible_text(prize_block)
    and 'target="_blank"' in prize_block
    and 'rel="noopener noreferrer"' in prize_block
)
ok &= print_result(
    "優勝賞品: Discord詳細リンク",
    "PASS" if prize_detail_ok else "FAIL",
)
```

- [ ] **Step 2: テストが指定リンク未実装で失敗することを確認する**

Run:

```bash
python3 tests/test_event_page.py
```

Expected: `FAIL: 優勝賞品: Discord詳細リンク`。既存項目はPASS。

- [ ] **Step 3: 優勝賞品カードへリンクを追加する**

`index.html`の優勝賞品カード内、賞品説明の後へ次を追加する。

```html
<a
  class="prize-detail-link"
  href="https://discord.com/channels/1138387287986679879/1528011762572595231/1529844197350309939"
  target="_blank"
  rel="noopener noreferrer"
>
  優勝賞品の詳細をDiscordで確認
</a>
```

既存`<style>`へ、元のロイヤルブルーと黄色だけを使うリンクスタイルを追加する。

```css
.prize-detail-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 44px;
  margin-top: 12px;
  padding: 10px 16px;
  border: 2px solid var(--royal);
  border-radius: 999px;
  color: var(--royal-deep);
  background: var(--white);
  font-weight: 800;
  text-decoration: none;
}

.prize-detail-link:hover,
.prize-detail-link:focus-visible {
  color: var(--white);
  background: var(--royal);
}
```

- [ ] **Step 4: 3つのHTMLを同期し、テストを通す**

Run:

```bash
cp index.html イベント概要_大運動会2026.html
cp index.html undo-kai.html
python3 tests/test_event_page.py
```

Expected: `PASS: 優勝賞品: Discord詳細リンク`を含み、Chrome不在による既存SKIP以外は全PASS。

- [ ] **Step 5: コミットする**

```bash
git add tests/test_event_page.py index.html イベント概要_大運動会2026.html undo-kai.html
git commit -m "feat: link confidential prize details"
```

---

### Task 2: 既存11セクションのプログレッシブなトグル化

**Files:**
- Modify: `tests/test_event_page.py:20-38`
- Modify: `tests/test_event_page.py:330-410`
- Modify: `tests/test_event_page.py:800-850`
- Modify: `index.html:1-360`
- Modify: `index.html:4750-4800`
- Modify: `イベント概要_大運動会2026.html`
- Modify: `undo-kai.html`

**Interfaces:**
- Consumes: ID付き既存セクション11件。
- Produces: `SECTION_TOGGLE_CONFIG`相当のJavaScript配列、`enhanceSectionToggles(): Map<string, HTMLDetailsElement>`、`.section-toggle`、`.section-toggle-summary`、`.section-toggle-content`。

- [ ] **Step 1: トグル契約の失敗テストを追加する**

`tests/test_event_page.py`の`REQUIRED_IDS`を次へ置き換える。

```python
TOGGLE_SECTIONS = [
    ("about", "イベント概要"),
    ("teams", "チーム発表"),
    ("rules", "デイリーミッション"),
    ("points", "ポイントのしくみ"),
    ("half-time", "中間発表クイズ"),
    ("survival", "脱落ルール"),
    ("schedule", "スケジュール"),
    ("prize", "優勝・準優勝賞品"),
    ("pv-voice", "PV音声収録"),
    ("faq", "FAQ"),
    ("contact", "お問い合わせ"),
]
REQUIRED_IDS = [section_id for section_id, _ in TOGGLE_SECTIONS]
```

`main()`のモバイルメニューテスト後へ、静的なプログレッシブエンハンスメント契約を追加する。

```python
toggle_script_terms = [
    "const sectionToggleConfig =",
    "const enhanceSectionToggles = () =>",
    'document.createElement("details")',
    'document.createElement("summary")',
    'document.createElement("h2")',
    'details.className = "section-toggle"',
    'summary.className = "section-toggle-summary"',
    'content.className = "section-toggle-content"',
    "while (section.firstChild)",
    "content.append(section.firstChild)",
    "details.open = open",
]
toggle_config_failures = [
    section_id
    for section_id, label in TOGGLE_SECTIONS
    if f'id: "{section_id}", label: "{label}"' not in text
]
toggle_contract_ok = (
    all(term in text for term in toggle_script_terms)
    and not toggle_config_failures
)
ok &= print_result(
    "セクショントグル: 既存DOMを保持する11分類",
    "PASS" if toggle_contract_ok else "FAIL",
    ", ".join(toggle_config_failures),
)
```

`dump_rendered_dom()`成功時の検査へ、描画後DOMの確認を追加する。

```python
rendered_toggle_ids = re.findall(
    r'<details class="section-toggle" data-section-id="([^"]+)"',
    render_html,
)
rendered_open_ids = re.findall(
    r'<details class="section-toggle" data-section-id="([^"]+)" open',
    render_html,
)
ok &= print_result(
    "セクショントグル: 描画後11件・概要のみ初期展開",
    "PASS"
    if rendered_toggle_ids == REQUIRED_IDS and rendered_open_ids == ["about"]
    else "FAIL",
    f"all={rendered_toggle_ids}, open={rendered_open_ids}",
)
```

- [ ] **Step 2: テストがトグル未実装で失敗することを確認する**

Run:

```bash
python3 tests/test_event_page.py
```

Expected: `FAIL: セクショントグル: 既存DOMを保持する11分類`。

- [ ] **Step 3: 11分類とDOM変換関数を実装する**

`index.html`末尾の既存IIFE内で、チーム画像複製処理の後、メニュー処理の前へ追加する。

```js
const sectionToggleConfig = [
  { id: "about", label: "イベント概要", open: true },
  { id: "teams", label: "チーム発表", open: false },
  { id: "rules", label: "デイリーミッション", open: false },
  { id: "points", label: "ポイントのしくみ", open: false },
  { id: "half-time", label: "中間発表クイズ", open: false },
  { id: "survival", label: "脱落ルール", open: false },
  { id: "schedule", label: "スケジュール", open: false },
  { id: "prize", label: "優勝・準優勝賞品", open: false },
  { id: "pv-voice", label: "PV音声収録", open: false },
  { id: "faq", label: "FAQ", open: false },
  { id: "contact", label: "お問い合わせ", open: false },
];

const enhanceSectionToggles = () => {
  const toggles = new Map();

  sectionToggleConfig.forEach(({ id, label, open }) => {
    const section = document.getElementById(id);
    if (!section) {
      return;
    }

    const details = document.createElement("details");
    const summary = document.createElement("summary");
    const summaryTitle = document.createElement("h2");
    const content = document.createElement("div");
    const originalHeading = section.querySelector("h2");
    const originalHeadingGroup =
      originalHeading?.closest(".inline-head, .prize-heading-row")
      ?? originalHeading;
    const originalKicker = section.querySelector(".mini-kicker");

    details.className = "section-toggle";
    details.dataset.sectionId = id;
    details.open = open;
    summary.className = "section-toggle-summary";
    summaryTitle.className = "section-toggle-title";
    summaryTitle.textContent = label;
    content.className = "section-toggle-content";
    originalHeadingGroup?.classList.add("section-toggle-original-heading");
    originalKicker?.classList.add("section-toggle-original-kicker");

    while (section.firstChild) {
      content.append(section.firstChild);
    }

    summary.append(summaryTitle);
    details.append(summary, content);
    section.append(details);
    section.classList.add("section-toggle-host");
    toggles.set(id, details);
  });

  return toggles;
};

const sectionToggles = enhanceSectionToggles();
```

この関数は既存の子要素を`append()`で移動するだけにし、`innerHTML`、文字列テンプレート、本文複製を使わない。

- [ ] **Step 4: mainの配色でトグルCSSを追加する**

既存`<style>`のモバイルメニュー規則の後へ追加する。

```css
.section-toggle-host {
  scroll-margin-top: 84px;
}

.section-toggle {
  width: 100%;
}

.section-toggle-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 64px;
  padding: 14px 18px;
  border: 2px solid var(--card-line);
  border-radius: 18px;
  color: var(--royal-deep);
  background: var(--white);
  cursor: pointer;
  font-weight: 900;
  list-style: none;
}

.section-toggle-summary::-webkit-details-marker {
  display: none;
}

.section-toggle-summary::after {
  content: "＋";
  flex: 0 0 auto;
  margin-left: 12px;
  color: var(--royal);
  font-size: 1.35rem;
  line-height: 1;
}

.section-toggle[open] > .section-toggle-summary {
  border-color: var(--royal);
  border-bottom-right-radius: 8px;
  border-bottom-left-radius: 8px;
}

.section-toggle[open] > .section-toggle-summary::after {
  content: "−";
}

.section-toggle-title {
  margin: 0;
  color: inherit;
  font-size: clamp(1.2rem, 5vw, 1.65rem);
  line-height: 1.35;
  text-align: left;
}

.section-toggle-content {
  padding-top: 24px;
}

.section-toggle-original-heading,
.section-toggle-original-kicker {
  display: none;
}

.section.inverse .section-toggle-summary {
  border-color: rgba(255, 255, 255, 0.72);
  color: var(--white);
  background: var(--royal-deep);
}

.section.inverse .section-toggle-summary::after {
  color: var(--yellow);
}
```

非表示にするのは、トグル見出しと重複する元の`h2`・`mini-kicker`だけとする。既存のミッションカード、表彰台、得点例、脱落フロー、画像、PVカードのCSSは変更しない。JavaScriptが動かない場合はクラスが付かないため、元見出しを含む全内容が従来どおり表示される。

- [ ] **Step 5: HTMLを同期し、静的テストを通す**

Run:

```bash
cp index.html イベント概要_大運動会2026.html
cp index.html undo-kai.html
python3 tests/test_event_page.py
```

Expected: Chrome不在時の描画後トグル検査はSKIP。`PASS: セクショントグル: 既存DOMを保持する11分類`を含み、その他は全PASS。

- [ ] **Step 6: コミットする**

```bash
git add tests/test_event_page.py index.html イベント概要_大運動会2026.html undo-kai.html
git commit -m "feat: progressively collapse event sections"
```

---

### Task 3: ハンバーガー・URLハッシュ・トグルの連動

**Files:**
- Modify: `tests/test_event_page.py:330-410`
- Modify: `index.html:4750-4830`
- Modify: `イベント概要_大運動会2026.html`
- Modify: `undo-kai.html`

**Interfaces:**
- Consumes: Task 2の`sectionToggles: Map<string, HTMLDetailsElement>`。
- Produces: `openSection(sectionId: string, options?: {scroll?: boolean, focus?: boolean}): boolean`、`openSectionFromHash(): boolean`。

- [ ] **Step 1: 連動動作の失敗テストを追加する**

モバイルメニューのJavaScript検査へ次を追加する。

```python
toggle_navigation_terms = [
    "const openSection = (sectionId, options = {}) =>",
    "const openSectionFromHash = () =>",
    "sectionToggles.get(sectionId)",
    "details.open = true",
    "section.scrollIntoView",
    'window.addEventListener("hashchange", openSectionFromHash)',
    "openSectionFromHash()",
    "const targetId = link.hash.slice(1)",
    "openSection(targetId",
]
missing_toggle_navigation = [
    term for term in toggle_navigation_terms if term not in text
]
ok &= print_result(
    "メニュー・ハッシュ・トグル連動",
    "PASS" if not missing_toggle_navigation else "FAIL",
    ", ".join(missing_toggle_navigation),
)
```

- [ ] **Step 2: テストが連動関数未実装で失敗することを確認する**

Run:

```bash
python3 tests/test_event_page.py
```

Expected: `FAIL: メニュー・ハッシュ・トグル連動`。

- [ ] **Step 3: 対象トグルを開く共通関数を実装する**

Task 2の`sectionToggles`定義直後へ追加する。

```js
const openSection = (sectionId, options = {}) => {
  const { scroll = false, focus = false } = options;
  const details = sectionToggles.get(sectionId);
  const section = document.getElementById(sectionId);

  if (!details || !section) {
    return false;
  }

  details.open = true;

  if (scroll) {
    requestAnimationFrame(() => {
      section.scrollIntoView({ block: "start", behavior: "smooth" });
      if (focus) {
        details.querySelector(".section-toggle-summary")?.focus({
          preventScroll: true,
        });
      }
    });
  }

  return true;
};

const openSectionFromHash = () => {
  const sectionId = window.location.hash.slice(1);
  return sectionId ? openSection(sectionId, { scroll: true }) : false;
};
```

`prefers-reduced-motion`利用者にはsmooth scrollを使わないよう、関数の上へ追加する。

```js
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
```

`scrollIntoView`の`behavior`を次へ変更する。

```js
behavior: reduceMotion.matches ? "auto" : "smooth",
```

- [ ] **Step 4: メニュー選択時に対象を開いて移動する**

既存の`menuLinks.forEach`一行を次へ置き換える。

```js
menuLinks.forEach((link) => {
  link.addEventListener("click", (event) => {
    const targetId = link.hash.slice(1);
    if (!sectionToggles.has(targetId)) {
      return;
    }

    event.preventDefault();
    closeMenu();
    window.history.replaceState(null, "", link.hash);
    openSection(targetId, { scroll: true, focus: true });
  });
});
```

初期化末尾へ追加する。

```js
window.addEventListener("hashchange", openSectionFromHash);
openSectionFromHash();
```

- [ ] **Step 5: HTMLを同期し、テストを通す**

Run:

```bash
cp index.html イベント概要_大運動会2026.html
cp index.html undo-kai.html
python3 tests/test_event_page.py
```

Expected: `PASS: メニュー・ハッシュ・トグル連動`を含み、Chrome不在による既存SKIP以外は全PASS。

- [ ] **Step 6: コミットする**

```bash
git add tests/test_event_page.py index.html イベント概要_大運動会2026.html undo-kai.html
git commit -m "feat: connect navigation to section toggles"
```

---

### Task 4: 内容保持の回帰契約

**Files:**
- Modify: `tests/test_event_page.py:500-790`

**Interfaces:**
- Consumes: 既存の`section_block()`と`visible_text()`。
- Produces: `PRESERVED_SECTION_TERMS: dict[str, list[str]]`。後続の視覚調整で内容を落とさないための固定契約。

- [ ] **Step 1: 11分類の内容フィンガープリントを追加する**

定数へ追加する。

```python
PRESERVED_SECTION_TERMS = {
    "about": [
        "待望の第2回",
        "7日間",
        "チーム分けは運営が実施",
    ],
    "teams": ["赤組", "青組", "黄組", "緑組", "橙組", "紫組"],
    "rules": ["12時間", "12人", "3人", "1日12時間まで", "3ヶ月以上"],
    "points": [
        "1本クリア = 1pt",
        "最大 12pt",
        "重点ミッション",
        "14時間30分",
        "13時間50分",
        "14人",
        "13人",
        "あと1人",
        "11pt",
        "9pt",
        "5pt",
    ],
    "half-time": ["早押しクイズ大会", "+8pt", "+6pt", "+4pt", "+2pt"],
    "survival": ["累積10pt以上ある？", "10pt未満", "3pt×4日＝12pt"],
    "schedule": ["8/20", "集計 0:00〜20:00", "8/23", "集計 0:00〜21:00"],
    "prize": ["優勝賞品", "準優勝賞品", "集合SDイラスト", "集合立ち絵ポスター"],
    "pv-voice": [
        "全員共通の3つ＋自分のチームの2つ、あわせて5つです",
        "TitleCall01_ORG.wav",
        "TeamShout02_ORG.wav",
    ],
    "faq": ["ミッションは毎日変わりますか？", "最終結果が同点だったら？"],
    "contact": ["運営への依頼窓口"],
}
```

`main()`へ追加する。

```python
preservation_failures = []
for section_id, required_terms in PRESERVED_SECTION_TERMS.items():
    section_text = visible_text(section_block(text, section_id))
    missing = [term for term in required_terms if term not in section_text]
    if missing:
        preservation_failures.append(f"{section_id}: {', '.join(missing)}")

ok &= print_result(
    "main情報分類・詳細内容の保持",
    "PASS" if not preservation_failures else "FAIL",
    "; ".join(preservation_failures),
)
```

- [ ] **Step 2: 現在のHTMLが保持契約を通ることを確認する**

Run:

```bash
python3 tests/test_event_page.py
```

Expected: `PASS: main情報分類・詳細内容の保持`。

- [ ] **Step 3: トグル変換が本文を複製・置換しないことを検査する**

Task 2のテストへ追加する。

```python
destructive_toggle_terms = [
    ".innerHTML =",
    ".outerHTML =",
    "section.replaceChildren",
]
destructive_hits = [term for term in destructive_toggle_terms if term in text]
ok &= print_result(
    "トグル変換: 既存本文の文字列置換なし",
    "PASS" if not destructive_hits else "FAIL",
    ", ".join(destructive_hits),
)
```

- [ ] **Step 4: テストを再実行する**

Run:

```bash
python3 tests/test_event_page.py
```

Expected: 新しい2項目を含め、Chrome不在による既存SKIP以外は全PASS。

- [ ] **Step 5: コミットする**

```bash
git add tests/test_event_page.py
git commit -m "test: lock full event guide content"
```

---

### Task 5: モバイル表示とアクセシビリティの最終調整

**Files:**
- Modify: `tests/test_event_page.py:90-137`
- Modify: `tests/test_event_page.py:780-850`
- Modify: `index.html:1-360`
- Modify: `イベント概要_大運動会2026.html`
- Modify: `undo-kai.html`

**Interfaces:**
- Consumes: Task 2のトグルクラス、Task 3のハッシュ移動。
- Produces: 390px・768px・1280pxで横スクロールがなく、44px以上の操作領域と明瞭なフォーカスを持つ完成UI。

- [ ] **Step 1: トグルのモバイルCSS契約をテストへ追加する**

`main()`のCSS検査へ追加する。

```python
toggle_css_terms = [
    ".section-toggle-summary",
    "min-height: 64px",
    "cursor: pointer",
    ".section-toggle-summary:focus-visible",
    "@media (max-width: 719px)",
    "overflow-wrap: anywhere",
]
missing_toggle_css = [term for term in toggle_css_terms if term not in css_compact]
ok &= print_result(
    "トグル: モバイル操作・折り返しCSS",
    "PASS" if not missing_toggle_css else "FAIL",
    ", ".join(missing_toggle_css),
)
```

- [ ] **Step 2: テストが不足するCSSを示して失敗することを確認する**

Run:

```bash
python3 tests/test_event_page.py
```

Expected: `FAIL: トグル: モバイル操作・折り返しCSS`。

- [ ] **Step 3: フォーカスと狭幅表示を追加する**

Task 2のトグルCSSへ追加する。

```css
.section-toggle-summary:focus-visible {
  outline: 3px solid var(--yellow);
  outline-offset: 3px;
}

.section-toggle-title {
  overflow-wrap: anywhere;
}

.section-toggle-content,
.section-toggle-content > *,
.section-toggle-content .cards,
.section-toggle-content .mission-example-grid,
.section-toggle-content .team-scores,
.section-toggle-content .tally-table,
.section-toggle-content .pv-team-block {
  min-width: 0;
  max-width: 100%;
}

.section-toggle-content .pv-filename,
.section-toggle-content code {
  overflow-wrap: anywhere;
  word-break: break-word;
}

@media (max-width: 719px) {
  .section-toggle-summary {
    min-height: 64px;
    padding: 12px 14px;
    border-radius: 14px;
    font-size: 1rem;
  }

  .section-toggle-content {
    padding-top: 18px;
  }

  .section-toggle[open] > .section-toggle-summary {
    margin-bottom: 4px;
  }
}
```

既存のポイント表、チーム画像、PVファイル名、脱落フローの本文・数値・ラベルは変更しない。上記の幅制約と折り返しだけを追加する。

- [ ] **Step 4: 自動テストを通す**

Run:

```bash
cp index.html イベント概要_大運動会2026.html
cp index.html undo-kai.html
python3 tests/test_event_page.py
```

Expected: `PASS: トグル: モバイル操作・折り返しCSS`を含み、Chrome不在による既存SKIP以外は全PASS。

- [ ] **Step 5: 390pxでブラウザ確認する**

ブラウザで`index.html`を390×844相当で開き、次を確認する。

1. 初期状態はイベント概要だけ開いている。
2. 11項目すべてが画面幅内に収まる。
3. ポイントを開くと、得点式、3ミッション別例、チームA〜C得点内訳がすべて残る。
4. 脱落ルールを開くと、判定フロー、10pt未満、`3pt×4日＝12pt`が残る。
5. チーム発表で54名の画像と名前が欠けない。
6. PV音声収録で共通3つ、選択組2つ、全ファイル名が読める。
7. 横スクロールがない。
8. コンソールエラーがない。

- [ ] **Step 6: 768pxと1280pxでブラウザ確認する**

768×1024と1280×900で次を確認する。

1. mainの白いカード、青背景、ロイヤルブルー、注意用オレンジが維持される。
2. デスクトップで既存のカード・表彰台・タイムラインが不必要に1列化されない。
3. ハンバーガーとアンカーナビが重ならない。
4. ハッシュURLを再読み込みすると対象トグルが開く。

- [ ] **Step 7: コミットする**

```bash
git add tests/test_event_page.py index.html イベント概要_大運動会2026.html undo-kai.html
git commit -m "fix: polish mobile section toggles"
```

---

### Task 6: 最終検証と引き渡し

**Files:**
- Verify: `index.html`
- Verify: `イベント概要_大運動会2026.html`
- Verify: `undo-kai.html`
- Verify: `tests/test_event_page.py`

**Interfaces:**
- Consumes: Tasks 1〜5の完成物。
- Produces: 内容保持、操作、レスポンシブ、Git差分が確認済みのブランチ。

- [ ] **Step 1: 3つのHTML同期と自動テストを確認する**

Run:

```bash
cmp -s index.html イベント概要_大運動会2026.html
cmp -s index.html undo-kai.html
python3 tests/test_event_page.py
```

Expected: 2つの`cmp`が終了コード0。Chrome不在による既存SKIP以外は全PASS。

- [ ] **Step 2: 差分に情報削除がないことを確認する**

Run:

```bash
git diff main..HEAD --stat
git diff --check
git status --short
```

Expected: 空白エラーなし。未コミットファイルなし。HTMLの変更は賞品リンク、トグルCSS、トグルJavaScript、既承認の①〜⑨に限定される。

- [ ] **Step 3: 外部リンクを確認する**

ブラウザで次の2リンクを確認する。

1. 優勝賞品詳細: Discordメッセージ`1529844197350309939`
2. お問い合わせ: Discordチャンネル`1475808380453916682`

Expected: どちらも新しいタブで開き、HTMLに`rel="noopener noreferrer"`がある。

- [ ] **Step 4: 作業ツリーがクリーンであることを確認する**

Run:

```bash
git status --short
```

Expected: 出力なし。差分が残っている場合は、該当するTaskのテスト・修正・コミット手順へ戻ってから再実行する。

- [ ] **Step 5: 実装結果を報告する**

報告へ次を含める。

1. mainの全11分類と詳細情報を保持したこと。
2. 11トグルとハンバーガー・ハッシュ連動を追加したこと。
3. 優勝賞品Discordリンクを追加したこと。
4. ①〜⑨の既存修正が回帰テストで維持されたこと。
5. 自動テスト結果と、ブラウザで確認した幅。
