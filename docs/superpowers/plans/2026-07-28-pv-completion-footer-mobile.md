# PV Completion, Footer, and Mobile Rule Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add persistent completion checks to PV lines 1–5, replace the cast-only footer notice, and prevent the elimination condition from breaking at character boundaries on narrow phones.

**Architecture:** Keep the existing single-file page architecture. Add a reusable client-side enhancer that runs after lines 4 and 5 are generated, stores five boolean states in `localStorage`, and reflects completion through a card class. Make the mobile rule text wrap only between two semantic spans and synchronize the finished HTML to all three deliverables.

**Tech Stack:** Static HTML, CSS, vanilla JavaScript, Python standard-library focused browser test.

## Global Constraints

- Preserve the existing visual language and all unrelated content.
- Store completion state in the same browser across reloads.
- Lines 4 and 5 have one completion state per line, not per team.
- The footer must use the two sentences supplied by the user.
- At narrow widths, the elimination text may wrap only between semantic groups.
- Do not run the full project test suite; run only the focused test for this change.

---

### Task 1: Focused regression test

**Files:**
- Create: `tests/test_pv_completion_updates.py`

**Interfaces:**
- Consumes: `index.html` as a complete browser-renderable page.
- Produces: a focused executable test that verifies five checkboxes, green completion state, reload persistence, exact footer copy, and narrow mobile wrapping.

- [ ] **Step 1: Write the failing test**

Create a standard-library test that injects a runtime harness after the existing page script. The harness clicks line 1, reloads with the same browser profile, then emits these real DOM assertions:

```javascript
results.fiveCompletionChecks = checks.length === 5;
results.completionTurnsGreen =
  checks[0].checked
  && checks[0].closest(".pv-say-card").classList.contains("is-complete");
results.completionPersists = checks[0].checked;
results.footerCopy =
  footer.textContent.includes("外部への共有はしないでください。")
  && footer.textContent.includes("適宜本ページも更新します。");
results.mobileRuleGroups =
  drop.querySelectorAll(":scope > span").length === 2
  && [...drop.children].every((span) =>
    getComputedStyle(span).whiteSpace === "nowrap"
  );
```

- [ ] **Step 2: Run the focused test to verify it fails**

Run:

```bash
python3 tests/test_pv_completion_updates.py
```

Expected: `FAIL`, because completion controls and grouped elimination spans do not exist and the footer copy is old.

### Task 2: Implement completion checks and copy/layout fixes

**Files:**
- Modify: `index.html`

**Interfaces:**
- Consumes: `.pv-say-card` cards created statically for lines 1–3 and dynamically for lines 4–5.
- Produces: `enhancePvCompletionChecks()`; five checkboxes with `data-pv-line`; persisted JSON under `backstage-undokai-2026-pv-completion`; `.is-complete` card state.

- [ ] **Step 1: Add minimal completion styles**

Add a compact label inside each card header and style `.pv-say-card.is-complete` with a pale green background and green border. Keep checked, focus-visible, and reduced-motion states readable.

- [ ] **Step 2: Add the reusable completion enhancer**

After `enhancePvTeamBranches()` has produced lines 4 and 5:

```javascript
const PV_COMPLETION_STORAGE_KEY = "backstage-undokai-2026-pv-completion";

const enhancePvCompletionChecks = () => {
  const cards = [...document.querySelectorAll("#pv-voice .pv-say-card")];
  // Resolve line number, create one labeled checkbox per line,
  // restore saved state, toggle is-complete, and save booleans.
};
```

Wrap `localStorage` reads and writes in `try/catch` so private or restricted browsing never blocks checkbox interaction.

- [ ] **Step 3: Replace the footer copy**

Use two visible lines:

```html
<p class="footer-note">
  本ページは参加キャスト向けの案内です。外部への共有はしないでください。<br>
  一部調整中の項目がありますので、最新情報は運営からの連絡をご確認ください。適宜本ページも更新します。
</p>
```

- [ ] **Step 4: Group the elimination text semantically**

Replace the current inline fragments with:

```html
<div class="flow-node flow-branch drop">
  <span>10pt未満 → 脱落</span>
  <span>（中間発表に不参加）</span>
</div>
```

Allow the container to wrap while applying `white-space: nowrap` to each child.

- [ ] **Step 5: Run the focused test to verify it passes**

Run:

```bash
python3 tests/test_pv_completion_updates.py
```

Expected: `PASS`.

### Task 3: Synchronize deliverables and visually confirm

**Files:**
- Modify: `undo-kai.html`
- Modify: `イベント概要_大運動会2026.html`

**Interfaces:**
- Consumes: verified `index.html`.
- Produces: three byte-identical HTML deliverables.

- [ ] **Step 1: Synchronize the verified source**

Copy `index.html` to the other two deliverables.

- [ ] **Step 2: Check only the changed behavior**

At 390px and desktop width, confirm:

- lines 1–5 each show one completion checkbox;
- clicking a checkbox turns only its card green;
- reload restores it;
- the footer contains the new two-line notice;
- at 320px, the red elimination pill uses one or two balanced lines without character-by-character wrapping.

- [ ] **Step 3: Run final focused verification**

Run:

```bash
python3 tests/test_pv_completion_updates.py
git diff --check
git status --short
```

Expected: focused test passes, no whitespace errors, and only planned files are modified.

- [ ] **Step 4: Commit**

```bash
git add tests/test_pv_completion_updates.py index.html undo-kai.html イベント概要_大運動会2026.html docs/superpowers/plans/2026-07-28-pv-completion-footer-mobile.md
git commit -m "feat: add persistent pv completion checks"
```
