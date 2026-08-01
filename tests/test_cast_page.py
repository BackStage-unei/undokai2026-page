#!/usr/bin/env python3
"""大運動会2026 キャスト向けページ（daiundokaihp_cast.html）のセルフチェック。

ユーザー向け（test_user_page.py）と対になる検査。契約の違い:
  - PV音声収録・Discord窓口・運営リーダー・キャスト向け注記が「必須」側
  - 検索避け（noindex）が必須
  - ユーザー向け専用の要素（CP還元ティーザー・アプリDL固定ボタン）は無いこと

使い方: python3 test_cast_page.py
"""
from __future__ import annotations

import html as H
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

def _find_html(*names):
    """repo（index.html / cast.html）と Vault（daiundokaihp_*.html）の両方で動くようにする。"""
    base = Path(__file__).resolve().parent.parent
    for name in names:
        candidate = base / name
        if candidate.exists():
            return candidate.resolve()
    raise SystemExit(f"対象HTMLが見つかりません: {names} (探索先: {base})")

ROOT = Path(__file__).resolve().parent.parent
HTML_PATH = _find_html("cast.html", "daiundokaihp_cast.html")



passed = failed = skipped = 0


def result(name: str, ok: bool | None, detail: str = "") -> bool:
    global passed, failed, skipped
    tag = "SKIP" if ok is None else ("PASS" if ok else "FAIL")
    if ok is None:
        skipped += 1
    elif ok:
        passed += 1
    else:
        failed += 1
    print(f"{tag}: {name}" + (f" - {detail}" if detail else ""))
    return bool(ok)


def visible_text(raw: str) -> str:
    t = re.sub(r"<script.*?</script>", " ", raw, flags=re.S)
    t = re.sub(r"<style.*?</style>", " ", t, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", H.unescape(t))


def find_browser() -> str | None:
    for env in ("EVENT_PAGE_BROWSER", "CHROME_PATH", "CHROME_BIN"):
        p = os.environ.get(env)
        if p and Path(p).exists():
            return p
    for p in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "/Applications/Chromium.app/Contents/MacOS/Chromium"):
        if Path(p).exists():
            return p
    return None


raw = HTML_PATH.read_text(encoding="utf-8")
text = visible_text(raw)

# ── 1. キャスト向けに必須の情報 ─────────────────────────────────
REQUIRED = {
    "運営リーダー：小松": "赤組の運営リーダー",
    "運営リーダー：田中烈": "紫組の運営リーダー",
    "PV音声収録": "PV収録の依頼",
    "https://forms.gle/SMoTKsQ16n4mtEuE9": "PV提出フォーム",
    "h_sawa@virtualidol.info": "PV提出先メール",
    "discord.com/channels/1138387287986679879/1475808380453916682": "運営への依頼窓口",
    "discord.com/channels/1138387287986679879/1528011762572595231": "優勝賞品の詳細",
    "本ページは参加キャスト向けの案内です": "外部共有しない旨の注記",
    'href="index.html"': "ユーザー向けページへの導線",
}
for term, why in REQUIRED.items():
    result(f"必須: {why}", term in raw, "見つからない" if term not in raw else "")

result("運営リーダーは6チーム分", raw.count('class="team-leader"') == 6,
       f"{raw.count('class=\"team-leader\"')}件")
result("検索避け noindex", 'content="noindex,nofollow"' in raw)

# ── 2. ルールが確定値と一致すること（ユーザー版と同じ契約）────────────
for term in ("のべ", "延べ", "1人1日1カウント", "12人"):
    result(f"旧ルール表記なし: {term}", raw.count(term) == 0, f"{raw.count(term)}件")

RULES = {
    "30人": "通話人数の確定基準値",
    "合計接客人数": "M2のカウント方法",
    "1日12時間まで": "稼働タイムの個人上限",
    "無料通話": "無料通話もカウント対象",
    "3ヶ月": "はじめまして・おかえりの条件",
    "10pt": "脱落ライン",
    "閉会式": "閉会式",
    "変更になる場合があります": "数値変更の注記",
    "今秋・約1ヶ月間": "特典の掲出条件",
}
for term, why in RULES.items():
    result(f"必須記載: {term}（{why}）", term in text, "見つからない" if term not in text else "")
result("「コラボ」表現を使っていない", "コラボ" not in text)

# ── 3. ユーザー向け専用要素が混ざっていないこと ──────────────────
for term, why in {
    "ユーザーのみなさま向けのお楽しみ": "CP還元ティーザー（ユーザー版専用）",
    '<a class="app-download-fixed"': "アプリDL固定ボタン（ユーザー版専用）",
    'href="cast.html"': "自分自身へのリンク",
    "<p>準備中</p>": "プレースホルダー",
    "自己紹介": "撤去済みのはずの欄",
}.items():
    result(f"混入なし: {why}", term not in raw, f"{raw.count(term)}件")

# ── 4. PV収録セクション ─────────────────────────────────────
result("PVプレビュー画像4枚", len(re.findall(r'src="assets/pv-preview/pv-preview-0\d\.png"', raw)) == 4)
result("共通セリフ3つに収録チェックあり", raw.count('class="pv-check"') == 3,
       f"{raw.count('class=\"pv-check\"')}個")
result("チーム別セリフ6チーム分", raw.count('class="pv-team"') == 6,
       f"{raw.count('class=\"pv-team\"')}個")
for i, (team, ruby) in enumerate(zip(("赤組", "青組", "黄組", "緑組", "橙組", "紫組"),
                                     ("あかぐみ", "あおぐみ", "きぐみ", "みどりぐみ",
                                      "おれんじぐみ", "むらさきぐみ"))):
    result(f"組名コールのルビ: {team}", f"<ruby>{team}<rt>{ruby}</rt></ruby>" in raw)
    result(f"ルビの二重表示なし: {team}", f"{team}<ruby>{team}" not in raw)
for color in ("Red", "Blue", "Yellow", "Green", "Orange", "Purple"):
    result(f"ファイル名の雛形: {color}", f"{color}_{{CastName}}_TeamName01_ORG.wav" in raw)
result("PV完了チェックの保存キー", "undokai2026-pv-recorded" in raw)

# ── 5. 共通構造（ユーザー版と同じデザイン基盤）──────────────────
result("h1 がちょうど1つ", raw.count("<h1") == 1, f"{raw.count('<h1')}個")
result("キャストカード54枚", raw.count('class="cast-card"') == 54)
result("チームパネル6枚", len(re.findall(r'<div class="cast-grid"[^>]*>', raw)) == 6)
result("[hidden] が効くCSS定義あり", "[hidden]{display:none!important}" in raw)
result("JS無効フォールバック", ".cast-grid[hidden]{display:grid!important}" in raw)

nav_block = re.search(r'<nav class="event-nav".*?</nav>', raw, re.S).group(0)
navs = re.findall(r'<a href="(#event-[a-z-]+)">', nav_block.split("</a>", 1)[1])
result("ナビ6本", len(navs) == 6, f"{len(navs)}本 {navs}")
for nav_id in navs:
    result(f"ナビ先が存在: {nav_id}", f'id="{nav_id[1:]}"' in raw)

urls = set(re.findall(r'https?://[^\s"\'<>()]+', raw))
allowed = {"back-stage.app", "x.com", "fonts.googleapis.com", "fonts.gstatic.com",
           "www.w3.org", "discord.com", "forms.gle", "backstage-unei.github.io"}
bad = sorted(u for u in urls if re.match(r"https?://([^/]+)", u).group(1) not in allowed)
result("外部URLは許可ホストのみ", not bad, ", ".join(bad[:4]))
result("外部スクリプト読み込みなし", not re.search(r"<script[^>]+\ssrc=", raw))

# ── 6. 実ブラウザ: PV収録チェックの保存・復元 ────────────────────
browser = find_browser()
if not browser:
    result("実ブラウザ: PV収録チェックの保存", None, "Chromeが見つからない")
else:
    HARNESS = """
<script>
(() => {
  setTimeout(() => {
    const out = {};
    try {
      const boxes = [...document.querySelectorAll(".pv-check input[data-pv-line]")];
      out.count = boxes.length;
      boxes[0].checked = true;
      boxes[0].dispatchEvent(new Event("change"));
      out.marked = boxes[0].closest(".pv-say-card").classList.contains("is-done");
      out.saved = JSON.parse(localStorage.getItem("undokai2026-pv-recorded") || "{}");
      boxes[0].checked = false;
      boxes[0].dispatchEvent(new Event("change"));
      out.unmarked = !boxes[0].closest(".pv-say-card").classList.contains("is-done");
      out.savedAfter = JSON.parse(localStorage.getItem("undokai2026-pv-recorded") || "{}");
      const teams = [...document.querySelectorAll("details.pv-team")];
      out.teams = teams.length;
      teams[0].open = true;
      out.teamOpens = teams[0].open;
      out.leaderVisible = !!document.querySelector(".cast-grid:not([hidden]) .team-leader");
    } catch (e) { out.error = String(e); }
    const el = document.createElement("output");
    el.id = "r"; el.textContent = JSON.stringify(out); document.body.appendChild(el);
  }, 2200);
})();
</script>"""
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8",
                                     dir=str(ROOT)) as f:
        f.write(raw.replace("</body>", HARNESS + "</body>", 1))
        tmp = f.name
    try:
        proc = subprocess.run(
            [browser, "--headless", "--disable-gpu", "--use-mock-keychain", "--no-first-run",
             "--virtual-time-budget=12000", "--dump-dom", "file://" + tmp],
            capture_output=True, text=True, timeout=180)
        m = re.search(r'<output id="r">(.*?)</output>', proc.stdout, re.S)
    except subprocess.TimeoutExpired:
        m = None
    finally:
        os.unlink(tmp)

    if not m:
        result("実ブラウザ: PV収録チェック", False, "結果を取得できなかった")
    else:
        got = json.loads(m.group(1))
        result("実ブラウザ: チェックボックス3個", got.get("count") == 3, str(got.get("count")))
        result("実ブラウザ: チェックでカードが完了表示", got.get("marked") is True)
        result("実ブラウザ: localStorage へ保存", got.get("saved", {}).get("1") is True,
               json.dumps(got.get("saved"), ensure_ascii=False))
        result("実ブラウザ: 解除で完了表示が外れる", got.get("unmarked") is True)
        result("実ブラウザ: 解除も保存される", got.get("savedAfter", {}).get("1") is False)
        result("実ブラウザ: チーム別セリフ6件", got.get("teams") == 6, str(got.get("teams")))
        result("実ブラウザ: 運営リーダーが表示される", got.get("leaderVisible") is True)

print(f"\n合計: PASS {passed} / FAIL {failed} / SKIP {skipped}")
sys.exit(1 if failed else 0)
