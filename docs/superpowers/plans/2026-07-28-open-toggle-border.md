# Open Toggle Border Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the heavy outer frame from an opened section toggle while retaining a clearly visible, accessible focus indicator inside the summary control.

**Architecture:** Add one CSS regression contract to the existing Python self-check, then make the smallest CSS-only change in the canonical `index.html`. Synchronize the two published HTML copies byte-for-byte and verify the result with the existing real-browser suite plus a 390px visual inspection.

**Tech Stack:** Static HTML, embedded CSS, Python 3 self-check, Chromium headless browser.

## Global Constraints

- Closed toggle borders, colors, and corner radii remain unchanged.
- Open toggle summaries use a transparent outer border.
- The 3px keyboard focus outline remains visible and moves inside the summary with a negative `outline-offset`.
- Existing light and inverse-section focus colors remain unchanged.
- Layout, spacing, toggle behavior, and content remain unchanged.
- `index.html`, `undo-kai.html`, and `イベント概要_大運動会2026.html` remain byte-identical.
- No new dependency or asset file is introduced.

---

### Task 1: Remove the opened-toggle outer frame

**Files:**
- Modify: `tests/test_event_page.py:997`
- Modify: `index.html:380-402`
- Modify: `undo-kai.html:380-402`
- Modify: `イベント概要_大運動会2026.html:380-402`

**Interfaces:**
- Consumes: `css_rule_bodies(css: str, target_selector: str) -> list[str]` from `tests/test_event_page.py`
- Produces: the CSS contract “open border is transparent and focus outline is inset”

- [ ] **Step 1: Write the failing regression test**

Insert this check immediately after the existing focus-contrast result in `tests/test_event_page.py`:

```python
    open_toggle_bodies = css_rule_bodies(
        css,
        ".section-toggle[open] > .section-toggle-summary",
    )
    toggle_focus_bodies = css_rule_bodies(
        css,
        ".section-toggle-summary:focus-visible",
    )
    open_border_transparent = any(
        re.search(r"border-color\s*:\s*transparent\b", body)
        for body in open_toggle_bodies
    )
    focus_outline_inset = any(
        re.search(r"outline-offset\s*:\s*-[1-9][0-9]*(?:\.[0-9]+)?px\b", body)
        for body in toggle_focus_bodies
    )
    ok &= print_result(
        "トグル: 展開時の外枠なし・フォーカス内側表示",
        "PASS" if open_border_transparent and focus_outline_inset else "FAIL",
        (
            f"open-border={open_border_transparent}, "
            f"focus-inset={focus_outline_inset}"
        ),
    )
```

- [ ] **Step 2: Run the test and verify RED**

Run:

```bash
python3 tests/test_event_page.py
```

Expected: exit code 1 with:

```text
FAIL: トグル: 展開時の外枠なし・フォーカス内側表示 - open-border=False, focus-inset=False
```

Existing browser checks may print `SKIP` when a Chromium executable is unavailable; the new CSS contract must still fail.

- [ ] **Step 3: Apply the minimal CSS change**

In `index.html`, change only these declarations:

```css
    .section-toggle-summary:focus-visible {
      outline: 3px solid var(--royal);
      outline-offset: -5px;
    }

    .section-toggle[open] > .section-toggle-summary {
      border-color: transparent;
      border-bottom-right-radius: 8px;
      border-bottom-left-radius: 8px;
    }
```

Do not change the inverse-section focus selector or any closed-state rule.

- [ ] **Step 4: Synchronize all published HTML files**

Run:

```bash
cp index.html undo-kai.html
cp index.html イベント概要_大運動会2026.html
```

- [ ] **Step 5: Run the full automated suite and verify GREEN**

Run:

```bash
REQUIRE_BROWSER_TESTS=1 python3 tests/test_event_page.py
cmp -s index.html undo-kai.html
cmp -s index.html イベント概要_大運動会2026.html
git diff --check
```

Expected:

- All static and real-browser checks print `PASS`.
- `トグル: 展開時の外枠なし・フォーカス内側表示` reports `open-border=True, focus-inset=True`.
- Both `cmp` commands and `git diff --check` exit 0.

- [ ] **Step 6: Verify the 390px appearance**

Open `http://localhost:8000/index.html` at 390×844, expand `#points`, and verify:

- No blue outline appears outside the summary.
- The summary retains its title and “−” indicator.
- Keyboard focus remains visible inside the summary.
- `document.documentElement.scrollWidth <= document.documentElement.clientWidth`.

- [ ] **Step 7: Commit**

```bash
git add tests/test_event_page.py index.html undo-kai.html イベント概要_大運動会2026.html
git commit -m "fix: remove open toggle outer frame"
```
