# 組名コール読み仮名・運営リーダー表示 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** PVの組名コールへ読み仮名を付け、チーム発表で各チームの運営リーダーを確認できるようにする。

**Architecture:** `index.html`を正本として、組名コールにはネイティブHTMLの`ruby`/`rt`を使用する。チーム見出し内にはチーム名と運営リーダーをまとめるラッパーを追加し、既存JavaScriptが`h3`の子要素をトグル見出しへ移動しても表示が維持されるようにする。完了後、正本を残り2つのHTML成果物へ機械的に同期する。

**Tech Stack:** HTML5、CSS、既存のVanilla JavaScript、Python 3による対象限定の静的確認

## Global Constraints

- 読み仮名は、赤組＝あかぐみ、青組＝あおぐみ、黄組＝きぐみ、緑組＝みどりぐみ、橙組＝おれんじぐみ、紫組＝むらさきぐみとする。
- 運営リーダーは、赤組＝小松、青組＝木村、黄組＝代表田中、緑組＝室井、橙組＝野崎、紫組＝田中烈とする。
- 運営リーダーは「チーム発表」にだけ表示し、PV音声収録欄には表示しない。
- 既存の配色、カード構造、トグル動作を維持する。
- `index.html`、`undo-kai.html`、`イベント概要_大運動会2026.html`を同一内容に揃える。
- 全テストは実行せず、今回追加する対象限定テストだけを実行する。

---

### Task 1: 組名コールとチーム発表を更新する

**Files:**
- Create: `tests/test_team_pronunciation_and_leaders.py`
- Modify: `index.html:967-1012`
- Modify: `index.html:4234-4380`
- Modify: `index.html:5112-5245`
- Modify: `undo-kai.html`
- Modify: `イベント概要_大運動会2026.html`

**Interfaces:**
- Consumes: 既存の`.team-card`、`.team-card-summary`、`.pv-team-line`と、`enhanceTeamRosterToggles()`および`enhancePvTeamBranches()`のDOM変換
- Produces: `.team-heading-copy`、`.team-name`、`.team-leader`の表示要素と、6つの`ruby > rt`読み仮名

- [ ] **Step 1: 対象限定の失敗するテストを書く**

`tests/test_team_pronunciation_and_leaders.py`を次の内容で作成する。

```python
#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
HTML_FILES = [
    ROOT / "index.html",
    ROOT / "undo-kai.html",
    ROOT / "イベント概要_大運動会2026.html",
]

READINGS = {
    "赤組": "あかぐみ",
    "青組": "あおぐみ",
    "黄組": "きぐみ",
    "緑組": "みどりぐみ",
    "橙組": "おれんじぐみ",
    "紫組": "むらさきぐみ",
}

LEADERS = {
    "赤組": "小松",
    "青組": "木村",
    "黄組": "代表田中",
    "緑組": "室井",
    "橙組": "野崎",
    "紫組": "田中烈",
}


def main() -> int:
    sources = [path.read_text(encoding="utf-8") for path in HTML_FILES]
    assert sources[0] == sources[1] == sources[2], "3つのHTML成果物が一致していません"
    source = sources[0]

    assert ".team-heading-copy" in source
    assert ".team-leader" in source

    teams_start = source.index('<section class="section" id="teams"')
    teams_end = source.index('<section class="section"', teams_start + 1)
    teams_section = source[teams_start:teams_end]
    pv_start = source.index('<section class="section" id="pv-voice"')
    pv_end = source.index('<section class="section"', pv_start + 1)
    pv_section = source[pv_start:pv_end]

    for team, reading in READINGS.items():
        expected = f"「<ruby>{team}<rt>{reading}</rt></ruby>！」"
        assert expected in pv_section, f"{team}の読み仮名がありません"

    for team, leader in LEADERS.items():
        assert f'<span class="team-name">{team}</span>' in teams_section
        assert (
            f'<span class="team-leader">運営リーダー：{leader}</span>'
            in teams_section
        )

    assert "運営リーダー：" not in pv_section
    print("PASS: 組名コール読み仮名・運営リーダー表示")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: テストが期待どおり失敗することを確認する**

Run:

```bash
python3 tests/test_team_pronunciation_and_leaders.py
```

Expected: `AssertionError`。変更前には`.team-heading-copy`と読み仮名・運営リーダー表示が存在しないため失敗する。

- [ ] **Step 3: チーム見出しの補助スタイルを追加する**

`index.html`の`.team-card h3`付近へ次を追加する。

```css
.team-heading-copy {
  display: grid;
  gap: 2px;
  text-align: left;
}

.team-name {
  line-height: 1.25;
}

.team-leader {
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
  line-height: 1.35;
}
```

既存の`h3`と`.team-card-summary`はラッパーを子要素として中央配置し、ラッパー内部だけを左揃えにする。

- [ ] **Step 4: 6チームの見出しへ運営リーダーを追加する**

各`h3`を次の構造へ置き換え、チームごとの氏名をGlobal Constraintsの対応表どおりに設定する。

```html
<h3>
  <span class="team-swatch" aria-hidden="true"></span>
  <span class="team-heading-copy">
    <span class="team-name">赤組</span>
    <span class="team-leader">運営リーダー：小松</span>
  </span>
</h3>
```

既存の`enhanceTeamRosterToggles()`は`h3`の全子要素を`summary`へ移動するため、JavaScriptは変更しない。

- [ ] **Step 5: 6つの組名コールへルビを追加する**

各チームのセリフ4を次の形式へ置き換える。

```html
<p>「<ruby>赤組<rt>あかぐみ</rt></ruby>！」</p>
```

赤、青、黄、緑、橙、紫の順にGlobal Constraintsの読み仮名を使用する。`enhancePvTeamBranches()`はセリフ行を`cloneNode(true)`で複製するため、JavaScriptは変更しない。

- [ ] **Step 6: 3つのHTML成果物を同期する**

`index.html`の完成内容を`undo-kai.html`と`イベント概要_大運動会2026.html`へ同一内容として反映する。

- [ ] **Step 7: 対象限定テストを実行して通過を確認する**

Run:

```bash
python3 tests/test_team_pronunciation_and_leaders.py
```

Expected:

```text
PASS: 組名コール読み仮名・運営リーダー表示
```

- [ ] **Step 8: 差分の整合性を確認する**

Run:

```bash
cmp -s index.html undo-kai.html
cmp -s index.html イベント概要_大運動会2026.html
git diff --check
```

Expected: すべて終了コード0。余分な空白エラーがなく、3つのHTMLが一致する。

- [ ] **Step 9: 実装をコミットする**

```bash
git add tests/test_team_pronunciation_and_leaders.py index.html undo-kai.html イベント概要_大運動会2026.html
git commit -m "feat: add team readings and operations leaders"
```
