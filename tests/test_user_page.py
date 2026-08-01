#!/usr/bin/env python3
"""大運動会2026 ユーザー向けページ（daiundokaihp_user.html）のセルフチェック。

キャスト向けページ用の test_event_page.py とは検査契約が異なるため別ファイルにしている。
主な違い:
  - キャスト専用情報（PV音声収録・Discord窓口・運営リーダー・キャスト向け注記）が
    「あってはならない」側に回る
  - JavaScript とキャスト詳細モーダルを前提とする（静的HTMLのみではない）

使い方:
    python3 test_user_page.py
Chrome があればモーダル・ディープリンク・タブの実動作まで検査する。無ければ SKIP。
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

HTML_PATH = _find_html("index.html", "daiundokaihp_user.html")
PAGE_URL = "https://backstage-unei.github.io/undokai2026-page/"



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
    for p in sorted(Path.home().glob("Library/Caches/ms-playwright/chromium*/chrome-mac/*.app/Contents/MacOS/*")):
        if p.exists():
            return str(p)
    return None


raw = HTML_PATH.read_text(encoding="utf-8")
text = visible_text(raw)

# ── 1. キャスト専用・内部情報が載っていないこと ─────────────────────────
LEAKS = {
    "運営リーダー": "運営リーダーの肩書",
    "木村": "運営スタッフ実名", "小松": "運営スタッフ実名", "室井": "運営スタッフ実名",
    "野崎": "運営スタッフ実名", "田中烈": "運営スタッフ実名", "暮林": "運営スタッフ実名",
    "PV音声": "キャスト専用のPV収録案内",
    "Discord": "キャスト向け窓口",
    "forms.gle": "キャスト提出フォーム",
    "h_sawa": "担当者メールアドレス",
    "予算": "内部の金額情報", "報酬": "内部の金額情報",
    "チーム分けアルゴリズム": "チーム編成の内幕",
    "本ページは参加キャスト向け": "キャスト向けページの注記",
}
for term, why in LEAKS.items():
    result(f"掲載禁止: {term}（{why}）", raw.count(term) == 0, f"{raw.count(term)}件")

# ── 2. ルールが確定値と一致すること ────────────────────────────────
for term in ("のべ", "延べ", "1人1日1カウント", "12人"):
    result(f"旧ルール表記なし: {term}", raw.count(term) == 0, f"{raw.count(term)}件")

RULES = {
    "30人": "通話人数の確定基準値",
    "合計接客人数": "M2のカウント方法",
    "1日12時間まで": "稼働タイムの個人上限",
    "無料通話": "無料通話もカウント対象である旨",
    "1分以上の通話": "カウント条件",
    "3ヶ月": "はじめまして・おかえりの条件",
    "10pt": "脱落ライン",
    "閉会式": "閉会式の案内",
    "変更になる場合があります": "数値変更の注記（7/18裁定J）",
    "運営スタッフが1名": "各チームの運営スタッフ（7/18裁定K）",
}
for term, why in RULES.items():
    result(f"必須記載: {term}（{why}）", term in text, "見つからない" if term not in text else "")

result("変更注記は基準値と配点の2箇所",
       text.count("変更になる場合があります") == 2, f"{text.count('変更になる場合があります')}箇所")

# ── 3. 特典の表現上限 ─────────────────────────────────────────
result("特典: 掲出条件の注記あり", "今秋・約1ヶ月間" in text)
result("特典: 「コラボ」表現を使っていない", "コラボ" not in text, f"{text.count('コラボ')}件")

# ── 4. head / SEO ────────────────────────────────────────────
head = raw[:raw.index("</head>")]
for tag in ('name="description"', 'rel="canonical"', 'property="og:title"',
            'property="og:image"', 'property="og:url"', 'name="twitter:card"', 'rel="icon"'):
    result(f"head: {tag}", tag in head)
result("head: og:url が公開URL", f'content="{PAGE_URL}"' in head)
result("h1 がちょうど1つ", raw.count("<h1") == 1, f"{raw.count('<h1')}個")
result("lang=ja", '<html lang="ja">' in raw)
result("viewport 指定", 'name="viewport"' in head)

# ── 5. 外部リソース ───────────────────────────────────────────
urls = set(re.findall(r'https?://[^\s"\'<>()]+', raw))
allowed_hosts = {"backstage-unei.github.io", "back-stage.app", "x.com",
                 "fonts.googleapis.com", "fonts.gstatic.com", "www.w3.org"}
bad = sorted(u for u in urls if re.match(r"https?://([^/]+)", u).group(1) not in allowed_hosts)
result("外部URLは許可ホストのみ", not bad, ", ".join(bad[:4]))
result("外部スクリプト読み込みなし", not re.search(r"<script[^>]+\ssrc=", raw))
result("画像はすべてインライン（外部画像なし）",
       not re.search(r'<img[^>]+src="https?://', raw))

# ── 6. 参加者一覧の静的レンダリング ────────────────────────────────
cards = re.findall(r'<a class="cast-card"[^>]*>', raw)
result("キャストカード54枚", len(cards) == 54, f"{len(cards)}枚")
panels = re.findall(r'<div class="cast-grid"[^>]*>', raw)
result("チームパネル6枚", len(panels) == 6, f"{len(panels)}枚")
result("初期表示は1パネルのみ",
       sum(1 for p in panels if " hidden" not in p) == 1,
       f"{sum(1 for p in panels if ' hidden' not in p)}枚が表示")
result("JS無効フォールバック（noscriptで全パネル表示）",
       ".cast-grid[hidden]{display:grid!important}" in raw)
result("[hidden] が効くCSS定義あり", "[hidden]{display:none!important}" in raw)

xs = re.findall(r'data-x="([^"]*)"', raw)
bad_x = [u for u in xs if not re.fullmatch(r"https://x\.com/[A-Za-z0-9_]{1,15}", u)]
result("Xリンクの形式が正しい", not bad_x, f"不正{len(bad_x)}件 {bad_x[:3]}")
result("Xリンクが40件以上", len(xs) >= 40, f"{len(xs)}件")

kws = re.findall(r'data-kw="([^"]*)"', raw)
result("意気込みが20件以上", len(kws) >= 20, f"{len(kws)}件")
result("意気込みにプレースホルダーが混ざっていない",
       not any(k.strip() in ("準備中", "") for k in kws))
result("モーダルに「準備中」が残っていない", "<p>準備中</p>" not in raw)
result("自己紹介欄は撤去済み", "自己紹介" not in raw)

# ── 7. 導線 ─────────────────────────────────────────────────
result("キャスト向けページへの導線", 'href="cast.html"' in raw)
nav_block = re.search(r'<nav class="event-nav".*?</nav>', raw, re.S).group(0)
navs = re.findall(r'<a href="(#event-[a-z-]+)">', nav_block.split("</a>", 1)[1])
result("ナビ6本（タイトルリンクを除く）", len(navs) == 6, f"{len(navs)}本 {navs}")
for nav_id in navs:
    result(f"ナビ先が存在: {nav_id}", f'id="{nav_id[1:]}"' in raw)

# ── 8. 実ブラウザ ────────────────────────────────────────────
browser = find_browser()
if not browser:
    result("実ブラウザ: モーダル・ディープリンク・タブ", None, "Chromeが見つからない")
else:
    HARNESS = """
<script>
(() => {
  const out = {};
  setTimeout(() => {
    try {
      const root = document.getElementById("undokai-user-page");
      const panels = Array.from(root.querySelectorAll(".cast-grid"));
      const tabs = Array.from(root.querySelectorAll(".team-tabs button"));
      const view = root.querySelector(".cast-detail-view");
      tabs[4].click();
      out.tab = panels.findIndex(p => !p.hidden) === 4;
      tabs[0].click();
      const card = panels[0].querySelector("a.cast-card[data-kw]");
      card.click();
      out.open = view.classList.contains("is-open");
      out.name = view.querySelector(".cast-detail-name").textContent === card.querySelector("strong").textContent;
      out.kw = view.querySelector(".cast-profile-kw p").textContent === card.dataset.kw
               && !view.querySelector(".cast-profile-kw").hidden;
      out.x = view.querySelector(".cast-detail-x").getAttribute("href") === card.dataset.x;
      out.hash = location.hash.startsWith("#cast-red-");
      view.querySelector(".cast-detail-back").click();
      setTimeout(() => {
        out.closed = !view.classList.contains("is-open");
        const el = document.createElement("output");
        el.id = "r"; el.textContent = JSON.stringify(out); document.body.appendChild(el);
      }, 60);
    } catch (e) {
      const el = document.createElement("output");
      el.id = "r"; el.textContent = JSON.stringify({error: String(e)}); document.body.appendChild(el);
    }
  }, 2200);
})();
</script>"""

    def dump(source: str, frag: str = "") -> str:
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False,
                                         encoding="utf-8", dir=tempfile.gettempdir()) as f:
            f.write(source)
            path = f.name
        try:
            proc = subprocess.run(
                [browser, "--headless", "--disable-gpu", "--use-mock-keychain", "--no-first-run",
                 "--virtual-time-budget=12000", "--dump-dom", "file://" + path + frag],
                capture_output=True, text=True, timeout=180)
            return proc.stdout
        except subprocess.TimeoutExpired:
            return ""
        finally:
            os.unlink(path)

    dom = dump(raw.replace("</body>", HARNESS + "</body>", 1))
    m = re.search(r'<output id="r">(.*?)</output>', dom, re.S)
    if not m:
        result("実ブラウザ: モーダル・タブ", False, "結果を取得できなかった")
    else:
        got = json.loads(m.group(1))
        result("実ブラウザ: タブ切り替え", got.get("tab") is True)
        result("実ブラウザ: モーダルが開く", got.get("open") is True)
        result("実ブラウザ: 氏名が一致", got.get("name") is True)
        result("実ブラウザ: 意気込みが一致", got.get("kw") is True)
        result("実ブラウザ: Xリンクが一致", got.get("x") is True)
        result("実ブラウザ: ハッシュ付与", got.get("hash") is True)
        result("実ブラウザ: モーダルが閉じる", got.get("closed") is True)

    DEEP = """
<script>setTimeout(() => {
  const v = document.querySelector(".cast-detail-view");
  const o = document.createElement("output"); o.id = "r";
  o.textContent = JSON.stringify({open: v.classList.contains("is-open"),
    num: v.querySelector(".cast-detail-number").textContent,
    team: v.querySelector(".cast-detail-team").textContent});
  document.body.appendChild(o);
}, 2200);</script>"""
    dom2 = dump(raw.replace("</body>", DEEP + "</body>", 1), "#cast-purple-09")
    m2 = re.search(r'<output id="r">(.*?)</output>', dom2, re.S)
    if not m2:
        result("実ブラウザ: ディープリンク復元", False, "結果を取得できなかった")
    else:
        got2 = json.loads(m2.group(1))
        result("実ブラウザ: ディープリンク復元",
               got2.get("open") is True and got2.get("num") == "CAST 09" and got2.get("team") == "紫組",
               json.dumps(got2, ensure_ascii=False))

    dom3 = dump(raw)  # JS有効のまま静的マークアップの存在を確認
    result("JS無効相当: カードがHTMLに存在", dom3.count('class="cast-card"') == 54,
           f"{dom3.count('class=\"cast-card\"')}枚")

print(f"\n合計: PASS {passed} / FAIL {failed} / SKIP {skipped}")
sys.exit(1 if failed else 0)
