# 大運動会2026 キャスト向け案内ページ改修 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 参加キャストがモバイルから必要な情報へすぐ移動でき、集計時間・賞品・PV音声収録・問い合わせ先を誤解なく確認できるGitHub Pagesを作る。

**Architecture:** `イベント概要_大運動会2026.html`を編集元とし、CSS・画像・JavaScriptを1ファイル内に保持する。モバイルメニューはネイティブ`dialog`と小さなインラインJavaScriptで実装し、PVのチーム画像は既存名簿画像を実行時に複製してbase64データの二重埋め込みを避ける。完成後に`index.html`と`undo-kai.html`へ機械的に同期する。

**Tech Stack:** HTML5、インラインCSS、Vanilla JavaScript、Python 3セルフチェック、GitHub Pages、Chrome Headless

## Global Constraints

- モバイル閲覧を主対象とする。
- 既存のイベントルール、数値、54名の名簿、画像順序を変更しない。
- 収録対象は「全員共通3つ＋自分のチーム2つ＝計5つ」とする。
- 8/20の集計は0:00〜20:00、8/23の集計は0:00〜21:00とする。
- 賞品は優勝賞品と準優勝賞品の2種類として表示する。
- 外部JavaScript、UIライブラリ、追加画像を導入しない。
- 既存画像のbase64データ行を手作業で編集しない。
- 3つのHTMLは最終的にバイト単位で同一にする。
- ハンバーガーメニューはキーボード、スクリーンリーダー、Escape、外側タップに対応する。
- 固定ヘッダーはセーフエリアを考慮し、横スクロールを発生させない。
- 文言変更は設計仕様書で承認された範囲に限定する。

---

## File Structure

- `イベント概要_大運動会2026.html`: 編集元。ページ構造、CSS、インラインJavaScript、本文を持つ。
- `index.html`: GitHub Pagesのエントリーポイント。完成した編集元をそのまま同期する。
- `undo-kai.html`: 互換用の同一コピー。完成した編集元をそのまま同期する。
- `tests/test_event_page.py`: 静的HTML契約、3ファイル一致、Chromeレンダリング、主要文言を検査する。
- `README.md`: キャスト向けGitHub Pagesであること、JavaScript利用、編集・公開手順を説明する。

### Task 1: モバイルメニューと問い合わせ導線

**Files:**
- Modify: `tests/test_event_page.py:1-360`
- Modify: `イベント概要_大運動会2026.html:1-360,3298-3350,4313-4353`

**Interfaces:**
- Consumes: 既存セクションID `about`, `teams`, `rules`, `points`, `half-time`, `survival`, `schedule`, `prize`, `pv-voice`, `faq`
- Produces: `#menu-toggle`, `#mobile-menu`, `#menu-close`, `#contact`、11項目の`.mobile-menu-link`

- [ ] **Step 1: ハンバーガーメニュー契約の失敗テストを書く**

`tests/test_event_page.py`で、既存の「`<script>`が0件」という判定を外部スクリプト禁止へ変更し、`main()`内へ次を追加する。

```python
mobile_nav = re.search(
    r'<dialog\b[^>]*\bid="mobile-menu"[^>]*>(.*?)</dialog>',
    text,
    re.S | re.I,
)
mobile_nav_html = mobile_nav.group(1) if mobile_nav else ""
mobile_nav_hrefs = [
    "#about",
    "#teams",
    "#rules",
    "#points",
    "#half-time",
    "#survival",
    "#schedule",
    "#prize",
    "#pv-voice",
    "#faq",
    "#contact",
]
mobile_nav_failures = []
for selector in ['id="menu-toggle"', 'id="mobile-menu"', 'id="menu-close"']:
    if selector not in text:
        mobile_nav_failures.append(selector)
for href in mobile_nav_hrefs:
    if f'href="{href}"' not in mobile_nav_html:
        mobile_nav_failures.append(href)
for js_term in [
    "showModal()",
    "menuDialog.close()",
    'menuDialog.addEventListener("close"',
    "event.target === menuDialog",
]:
    if js_term not in text:
        mobile_nav_failures.append(js_term)
external_scripts = re.findall(r'<script\b[^>]*\bsrc\s*=', text, re.I)
if external_scripts:
    mobile_nav_failures.append("外部script")
ok &= print_result(
    "モバイルメニュー: dialog・11リンク・閉じる操作",
    "PASS" if not mobile_nav_failures else "FAIL",
    ", ".join(mobile_nav_failures),
)

contact_html = section_block(text, "contact")
discord_url = "https://discord.com/channels/1138387287986679879/1475808380453916682"
contact_ok = (
    "運営への依頼窓口" in visible_text(contact_html)
    and contact_html.count(discord_url) == 1
    and 'rel="noopener noreferrer"' in contact_html
)
ok &= print_result("お問い合わせ: Discord窓口", "PASS" if contact_ok else "FAIL")
```

既存のURL禁止判定は、許可URLを明示する次の判定へ置き換える。

```python
allowed_urls = {
    "https://forms.gle/SMoTKsQ16n4mtEuE9",
    "https://discord.com/channels/1138387287986679879/1475808380453916682",
}
found_urls = set(re.findall(r'https?://[^"\s<]+', strip_data_uris(text)))
unexpected_urls = sorted(found_urls - allowed_urls)
ok &= print_result(
    "外部URLは提出フォームとDiscordのみ",
    "PASS" if not unexpected_urls else "FAIL",
    ", ".join(unexpected_urls),
)
```

- [ ] **Step 2: テストが期待どおり失敗することを確認する**

Run:

```bash
python3 tests/test_event_page.py
```

Expected: `FAIL: モバイルメニュー: dialog・11リンク・閉じる操作`と`FAIL: お問い合わせ: Discord窓口`。既存項目はこの2件以外PASS。

- [ ] **Step 3: 固定ヘッダー、ハンバーガーボタン、dialogを実装する**

`イベント概要_大運動会2026.html`の`.topbar`周辺へ次のCSS契約を追加する。

```css
.topbar {
  position: sticky;
  top: 0;
  z-index: 50;
  padding-top: env(safe-area-inset-top);
  background: var(--sky-deep);
}

.topbar-inner {
  display: flex;
  min-height: 64px;
  align-items: center;
  justify-content: space-between;
  padding: 10px 0;
}

.menu-toggle,
.menu-close {
  display: inline-flex;
  min-width: 44px;
  min-height: 44px;
  align-items: center;
  justify-content: center;
  border: 2px solid rgba(255, 255, 255, 0.72);
  border-radius: 999px;
  color: var(--white);
  background: transparent;
  cursor: pointer;
}

.menu-dialog {
  width: 100%;
  max-width: none;
  height: 100dvh;
  max-height: none;
  margin: 0;
  padding: 0;
  border: 0;
  color: var(--ink);
  background: transparent;
}

.menu-dialog::backdrop {
  background: rgba(20, 35, 72, 0.62);
}

.menu-panel {
  width: min(88vw, 380px);
  min-height: 100dvh;
  margin-left: auto;
  padding:
    max(18px, env(safe-area-inset-top))
    20px
    max(24px, env(safe-area-inset-bottom));
  background: var(--white);
  box-shadow: -8px 0 24px rgba(31, 56, 110, 0.18);
}

.mobile-menu-links {
  display: grid;
  gap: 8px;
  margin: 20px 0 0;
  padding: 0;
  list-style: none;
}

.mobile-menu-link {
  display: flex;
  min-height: 44px;
  align-items: center;
  padding: 9px 12px;
  border-bottom: 1px solid var(--card-line);
  color: var(--royal-deep);
  font-weight: 700;
}

body.menu-open {
  overflow: hidden;
}

@media (min-width: 720px) {
  .menu-toggle,
  .menu-dialog {
    display: none;
  }
}

@media (max-width: 719px) {
  .anchor-nav {
    display: none;
  }
}
```

上部バー内の現行`topbar-logo`と`event-label`はバイト単位で維持し、その直後へ次のボタンを追加する。ハンバーガーの3本線は装飾用`span`とし、ボタン自体に名前を持たせる。

```html
<button
  class="menu-toggle"
  id="menu-toggle"
  type="button"
  aria-label="ページメニューを開く"
  aria-controls="mobile-menu"
  aria-expanded="false"
>
  <span class="menu-icon" aria-hidden="true"><span></span><span></span><span></span></span>
</button>
```

`</header>`の直後へdialogを追加する。

```html
<dialog class="menu-dialog" id="mobile-menu" aria-labelledby="mobile-menu-title">
  <div class="menu-panel">
    <div class="menu-panel-head">
      <p id="mobile-menu-title">ページメニュー</p>
      <button class="menu-close" id="menu-close" type="button" aria-label="ページメニューを閉じる">×</button>
    </div>
    <nav aria-label="モバイル用ページ内ナビゲーション">
      <ul class="mobile-menu-links">
        <li><a class="mobile-menu-link" href="#about">イベント概要</a></li>
        <li><a class="mobile-menu-link" href="#teams">チーム発表</a></li>
        <li><a class="mobile-menu-link" href="#rules">デイリーミッション</a></li>
        <li><a class="mobile-menu-link" href="#points">ポイントのしくみ</a></li>
        <li><a class="mobile-menu-link" href="#half-time">中間発表クイズ</a></li>
        <li><a class="mobile-menu-link" href="#survival">脱落ルール</a></li>
        <li><a class="mobile-menu-link" href="#schedule">スケジュール</a></li>
        <li><a class="mobile-menu-link" href="#prize">特典</a></li>
        <li><a class="mobile-menu-link" href="#pv-voice">PV音声収録</a></li>
        <li><a class="mobile-menu-link" href="#faq">FAQ</a></li>
        <li><a class="mobile-menu-link" href="#contact">お問い合わせ</a></li>
      </ul>
    </nav>
  </div>
</dialog>
```

`</body>`直前に次のインラインJavaScriptを追加する。

```html
<script>
  (() => {
    const menuButton = document.querySelector("#menu-toggle");
    const menuDialog = document.querySelector("#mobile-menu");
    const closeButton = document.querySelector("#menu-close");
    const menuLinks = menuDialog.querySelectorAll(".mobile-menu-link");

    const openMenu = () => {
      menuDialog.showModal();
      document.body.classList.add("menu-open");
      menuButton.setAttribute("aria-expanded", "true");
      closeButton.focus();
    };

    const closeMenu = () => {
      if (menuDialog.open) menuDialog.close();
    };

    menuButton.addEventListener("click", openMenu);
    closeButton.addEventListener("click", closeMenu);
    menuLinks.forEach((link) => link.addEventListener("click", closeMenu));
    menuDialog.addEventListener("click", (event) => {
      if (event.target === menuDialog) closeMenu();
    });
    menuDialog.addEventListener("close", () => {
      document.body.classList.remove("menu-open");
      menuButton.setAttribute("aria-expanded", "false");
      menuButton.focus();
    });
  })();
</script>
```

FAQの後へ問い合わせセクションを追加し、ヒーロー内のデスクトップナビにも`#about`と`#contact`を追加する。

```html
<section class="section" id="contact" aria-labelledby="contact-title">
  <p class="mini-kicker">CONTACT</p>
  <h2 class="bar-title" id="contact-title">お問い合わせ</h2>
  <p>ご不明点や運営へのご相談は、Discord内の「運営への依頼窓口」からご連絡ください。</p>
  <p>
    <a
      class="contact-link"
      href="https://discord.com/channels/1138387287986679879/1475808380453916682"
      target="_blank"
      rel="noopener noreferrer"
    >Discord「運営への依頼窓口」を開く</a>
  </p>
</section>
```

- [ ] **Step 4: メニューと問い合わせテストを通す**

Run:

```bash
python3 tests/test_event_page.py
```

Expected: Task 1で追加した2項目がPASS。既存項目もPASS。

- [ ] **Step 5: Task 1をコミットする**

```bash
git add tests/test_event_page.py イベント概要_大運動会2026.html
git commit -m "feat: add mobile navigation and contact"
```

### Task 2: キャスト向け文言、集計時間、賞品2種類

**Files:**
- Modify: `tests/test_event_page.py:280-620`
- Modify: `イベント概要_大運動会2026.html:3311-3378,3470-3540,3951-4161,4345-4350`

**Interfaces:**
- Consumes: `section_block()`, `visible_text()`、既存`#rules`, `#schedule`, `#prize`
- Produces: `.collection-window-grid`、`.collection-window-card`、優勝賞品・準優勝賞品の明示

- [ ] **Step 1: 文言・時間・賞品の失敗テストを書く**

`main()`へ次を追加する。

```python
cast_copy_required = [
    "日々の待機・通話実績が、チームの得点になります",
    "チームで力を合わせて勝利を目指しましょう",
    "自分のチームとメンバーを確認してください",
    "本ページは参加キャスト向けの案内です",
]
cast_copy_forbidden = [
    "あなたの通話が、チームの得点になる",
    "キャストと共に勝利をつかめ",
    "推しのチームを応援しよう",
]
copy_ok = all(item in rendered_text for item in cast_copy_required) and not any(
    item in rendered_text for item in cast_copy_forbidden
)
ok &= print_result("参加キャスト向け文言", "PASS" if copy_ok else "FAIL")

rules_text = visible_text(section_block(text, "rules"))
schedule_text = visible_text(section_block(text, "schedule"))
collection_terms = ["8/20(木)", "0:00〜20:00", "8/23(日・最終日)", "0:00〜21:00"]
collection_ok = all(term in rules_text for term in collection_terms) and all(
    term in schedule_text for term in collection_terms
)
ok &= print_result(
    "集計時間: デイリーミッションとスケジュール",
    "PASS" if collection_ok else "FAIL",
)

prize_text = visible_text(section_block(text, "prize"))
prize_terms = [
    "賞品は優勝・準優勝の2種類",
    "優勝賞品",
    "準優勝賞品",
    "集合SDイラスト",
    "集合立ち絵ポスター",
]
ok &= print_result(
    "賞品2種類の明示",
    "PASS" if all(term in prize_text for term in prize_terms) else "FAIL",
)
```

- [ ] **Step 2: 新しいテストが3件失敗することを確認する**

Run:

```bash
python3 tests/test_event_page.py
```

Expected: `参加キャスト向け文言`、`集計時間: デイリーミッションとスケジュール`、`賞品2種類の明示`がFAIL。

- [ ] **Step 3: 承認済み文言へ置き換える**

次の5箇所を設計仕様書どおり置換する。

```html
<p class="lead">チームで挑む、7日間の大運動会。日々の待機・通話実績が、チームの得点になります。</p>
<div class="catch">待機も通話もすべてが勝負。チームで力を合わせて勝利を目指しましょう！</div>
<li><span class="zekken">03</span><span>ユーザーのみなさんとの通話と応援が、<strong class="kw">そのままチームの得点に</strong>なります。</span></li>
<p>全6チーム・各9名。自分のチームとメンバーを確認してください。</p>
<p class="footer-note">本ページは参加キャスト向けの案内です。一部調整中の項目がありますので、最新情報は運営からの連絡をご確認ください。</p>
```

- [ ] **Step 4: 集計時間の注意カードを追加する**

`#rules`の導入文直後と`#schedule .tally-table`の直前へ、同じ情報を次の構造で配置する。

```html
<div class="collection-window-grid" aria-label="通常と異なる集計時間">
  <div class="collection-window-card">
    <strong>8/20(木)</strong>
    <span>集計 0:00〜20:00</span>
    <small>20:00締め／21:00中間発表</small>
  </div>
  <div class="collection-window-card">
    <strong>8/23(日・最終日)</strong>
    <span>集計 0:00〜21:00</span>
    <small>21:00締め／21:00最終結果発表</small>
  </div>
</div>
```

通常日の説明として次を添える。

```html
<p class="collection-window-note">通常日は0:00〜23:59で集計します。8/20と最終日のみ締め時間が異なります。</p>
```

カードはモバイル1列、720px以上で2列にする。時間は`font-variant-numeric: tabular-nums`を使用し、黄色背景・濃紺文字で既存の注意枠と区別する。

スケジュールの2項目を次の文言へ更新する。

```html
<span class="timeline-item-text">20:00集計締め／21:00〜<span class="nw">中間発表</span>クイズ配信</span>
<span class="timeline-item-text">最終日・21:00集計締め／21:00〜<span class="nw">最終結果発表</span></span>
```

- [ ] **Step 5: 賞品を2種類として再構成する**

特典本文の冒頭に次を置く。

```html
<p class="prize-main">賞品は<strong>優勝・準優勝の2種類</strong>です。</p>
```

2枚のカードは次の見出しと内容にする。

```html
<div class="prize-rank-card prize-rank-gold">
  <p class="prize-rank-label">優勝賞品</p>
  <ul class="prize-rank-list">
    <li>チームメンバー全員の描き下ろし<strong>集合SDイラスト</strong>を制作</li>
    <li>集合SDイラストを店舗に<strong>パネル設置</strong></li>
    <li>店内ブース席に<strong>チームのブースPOPを掲出</strong></li>
  </ul>
</div>
<div class="prize-rank-card prize-rank-silver">
  <p class="prize-rank-label">準優勝賞品</p>
  <ul class="prize-rank-list">
    <li>既存立ち絵を使用した<strong>集合立ち絵ポスター</strong>を制作</li>
    <li>ブースPOPとして店内ブース席に掲出</li>
  </ul>
</div>
```

カードの直前に、自遊空間、東京都内、今秋、約1ヶ月間の既存説明を残す。

- [ ] **Step 6: 文言・時間・賞品テストを通す**

Run:

```bash
python3 tests/test_event_page.py
```

Expected: Task 2の3項目を含め全項目PASS。

- [ ] **Step 7: Task 2をコミットする**

```bash
git add tests/test_event_page.py イベント概要_大運動会2026.html
git commit -m "feat: clarify cast guidance and event timing"
```

### Task 3: PV音声収録を5セリフへ再構成

**Files:**
- Modify: `tests/test_event_page.py:1-330`
- Modify: `イベント概要_大運動会2026.html:2465-2965,4163-4311,末尾script`

**Interfaces:**
- Consumes: `#teams .team-card`内の6チーム×9名の`img`
- Produces: `.pv-common-grid`の3カード、6個の`[data-team-index]`、`.pv-team-members`、正確な5種類のファイル名

- [ ] **Step 1: PV契約を5セリフ用の失敗テストへ更新する**

旧`CAST_ONLY_PV_EXPECTED`分岐と一時削除マーカー検査を削除し、`pv_block = section_block(text, "pv-voice")`へ一本化する。

```python
pv_text = visible_text(pv_block)
pv_required = [
    "イベントのPVを現在作成中です",
    "参加は強制ではありません",
    "8/1(土) 13:00ごろ",
    "この日の13:00ごろから本格的に作業を始める予定です",
    "全員共通の3つ＋自分のチームの2つ、あわせて5つです",
    "TitleCall01_ORG.wav",
    "TitleCall02_ORG.wav",
    "Start01_ORG.wav",
    "Start02_ORG.wav",
    "Cheering01_ORG.wav",
    "Cheering02_ORG.wav",
    "TeamName01_ORG.wav",
    "TeamName02_ORG.wav",
    "TeamShout01_ORG.wav",
    "TeamShout02_ORG.wav",
]
pv_forbidden = [
    "収録をお願いしたいセリフは4つ",
    "全員共通の2つ",
    "＋α（余裕があればぜひ！）",
    "こちらは必須ではありません",
]
pv_ok = all(term in pv_text for term in pv_required) and not any(
    term in pv_text for term in pv_forbidden
) and "CAST-ONLY:PV-VOICE" not in text
ok &= print_result("PV音声: 必須5セリフとファイル名", "PASS" if pv_ok else "FAIL")

team_color_prefixes = ["Red", "Blue", "Yellow", "Green", "Orange", "Purple"]
pv_team_contract = all(
    f'data-team-index="{index}"' in pv_block
    and f"{prefix}_{{CastName}}_TeamName01_ORG.wav" in pv_block
    and f"{prefix}_{{CastName}}_TeamName02_ORG.wav" in pv_block
    and f"{prefix}_{{CastName}}_TeamShout01_ORG.wav" in pv_block
    and f"{prefix}_{{CastName}}_TeamShout02_ORG.wav" in pv_block
    for index, prefix in enumerate(team_color_prefixes)
)
clone_script_ok = all(
    term in text
    for term in [
        'document.querySelectorAll("#teams .team-card")',
        'document.querySelectorAll("#pv-voice [data-team-index]")',
        "cloneNode(true)",
    ]
)
ok &= print_result(
    "PV音声: 6チームの命名と既存画像再利用",
    "PASS" if pv_team_contract and clone_script_ok else "FAIL",
)
```

録音方法の左揃え契約も追加する。

```python
pv_alignment_ok = all(
    term in css_compact
    for term in [
        "#pv-voice .pv-route-card",
        "#pv-voice .pv-steps",
        "#pv-voice .pv-detail-box",
        "text-align: left",
    ]
)
ok &= print_result("PV音声: 録音方法の左揃え", "PASS" if pv_alignment_ok else "FAIL")
```

`css_rule_failures()`の左揃え許可リストは、対象をPV録音手順だけに限定して次へ更新する。

```python
left_allowed = {
    "#points .rule-table td:nth-child(3)",
    ".timeline-item-text",
    "#pv-voice .pv-route-card",
    "#pv-voice .pv-route-card p",
    "#pv-voice .pv-route-card li",
    "#pv-voice .pv-steps",
    "#pv-voice .pv-detail-box",
    "#pv-voice .pv-recording-tips",
}
```

Chromeが利用可能な場合に実行後DOMの画像数も検査する。

```python
def dump_rendered_dom() -> tuple[bool, str]:
    result = subprocess.run(
        [str(CHROME), "--headless", "--disable-gpu", "--dump-dom", HTML_PATH.as_uri()],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return result.returncode == 0, result.stdout


chrome_available, chrome_detail = chrome_probe()
if chrome_available:
    render_ok, render_html = dump_rendered_dom()
    if not render_ok:
        raise RuntimeError("Chrome DOM dump failed")
    rendered_pv = section_block(render_html, "pv-voice")
    pv_member_groups = re.findall(
        r'<div class="pv-team-members"[^>]*>(.*?)</div>',
        rendered_pv,
        re.S,
    )
    pv_member_counts = [
        len(re.findall(r"<img\b", group, re.I)) for group in pv_member_groups
    ]
    ok &= print_result(
        "PV音声: 描画後6チーム×9画像",
        "PASS" if pv_member_counts == [9, 9, 9, 9, 9, 9] else "FAIL",
        str(pv_member_counts),
    )
else:
    ok &= print_result("PV音声: 描画後6チーム×9画像", "SKIP", chrome_detail)
```

- [ ] **Step 2: PVの新規3テストが失敗することを確認する**

Run:

```bash
python3 tests/test_event_page.py
```

Expected: `PV音声: 必須5セリフとファイル名`、`PV音声: 6チームの命名と既存画像再利用`、`PV音声: 録音方法の左揃え`がFAIL。

- [ ] **Step 3: 導入文・期限・5セリフ構成へ変更する**

ヒーローナビとPVセクションを囲んでいる4個の`CAST-ONLY:PV-VOICE`コメントを削除し、PV音声収録をキャスト向けページの通常セクションとして扱う。

導入を次の構造へ変更する。

```html
<p class="lead">イベントのPVを現在作成中です。その中で、キャストのみなさんの声を映像内で使用したいと考えています。<br>もし参加可能な方がいらっしゃいましたら、下記セリフを期限までにご提出いただけると嬉しいです！</p>
<p class="notice pv-notice"><strong>参加は強制ではありません。</strong>お時間に余裕のある方は、ぜひご協力をお願いします！</p>
<div class="pv-deadline" aria-label="提出期限 8月1日土曜日 13時ごろ">
  <span class="pv-deadline-label">提出期限</span>
  <span class="pv-deadline-time">8/1(土) 13:00ごろ</span>
  <span class="pv-deadline-note">この日の13:00ごろから本格的に作業を始める予定です。</span>
</div>
<h3 class="pv-section-heading">収録をお願いしたいセリフは5つ</h3>
<p class="pv-structure">全員共通の3つ＋自分のチームの2つ、あわせて5つです。</p>
```

全員共通カードを3枚にし、各カードへ2つの完全なファイル名を追加する。

```html
<div class="cards pv-common-grid">
  <article class="pv-say-card">
    <div class="pv-say-head">
      <span class="pv-say-num">セリフ 1</span>
      <span class="pv-say-title">タイトルコール</span>
      <span class="pv-say-time">目安 約3秒</span>
    </div>
    <p class="pv-say-quote">「BackStage大運動会！」</p>
    <div class="pv-file-names" aria-label="タイトルコールのファイル名">
      <code>{TeamColor}_{CastName}_TitleCall01_ORG.wav</code>
      <code>{TeamColor}_{CastName}_TitleCall02_ORG.wav</code>
    </div>
  </article>
  <article class="pv-say-card">
    <div class="pv-say-head">
      <span class="pv-say-num">セリフ 2</span>
      <span class="pv-say-title">スタートの掛け声</span>
      <span class="pv-say-time">目安 約2秒</span>
    </div>
    <p class="pv-say-quote">「よーい、どん！」</p>
    <div class="pv-file-names" aria-label="スタートのファイル名">
      <code>{TeamColor}_{CastName}_Start01_ORG.wav</code>
      <code>{TeamColor}_{CastName}_Start02_ORG.wav</code>
    </div>
  </article>
  <article class="pv-say-card">
    <div class="pv-say-head">
      <span class="pv-say-num">セリフ 3</span>
      <span class="pv-say-title">応援の声</span>
      <span class="pv-say-time">目安なし</span>
    </div>
    <p class="pv-say-note">「○○組がんばれー！」「いけー！！！」など、自分のチームを応援する元気な掛け声をお願いします。</p>
    <div class="pv-file-names" aria-label="応援の声のファイル名">
      <code>{TeamColor}_{CastName}_Cheering01_ORG.wav</code>
      <code>{TeamColor}_{CastName}_Cheering02_ORG.wav</code>
    </div>
  </article>
</div>
```

- [ ] **Step 4: チーム別カードへ正確なファイル名と画像コンテナを追加する**

見出しを「セリフ4・5 — チーム別セリフ」とする。6カードには次の値を使用する。

| `data-team-index` | 色 | 組名 | 組名セリフ | 掛け声 | ファイル名接頭辞 |
|---:|---|---|---|---|---|
| 0 | `#E53935` | 赤組 | 「赤組！」 | 「よっしゃ行くぞ〜！」 | `Red` |
| 1 | `#1E88E5` | 青組 | 「青組！」 | 「最高のイベントにしよう！」 | `Blue` |
| 2 | `#FDD835` | 黄組 | 「黄組！」 | 「みんな、お祭りだー！！」 | `Yellow` |
| 3 | `#43A047` | 緑組 | 「緑組！」 | 「全力で楽しもう〜！」 | `Green` |
| 4 | `#FB8C00` | 橙組 | 「橙組！」 | 「ぜったい勝つぞ〜！」 | `Orange` |
| 5 | `#8E24AA` | 紫組 | 「紫組！」 | 「準備はいいか〜！？」 | `Purple` |

各カードは次の構造を使用し、上表の値をそのまま入れる。

```html
<div class="pv-team-say" style="--tc: #E53935;" data-team-index="0">
  <p class="pv-team-name">赤組</p>
  <div class="pv-team-members" aria-label="赤組のキャスト"></div>
  <div class="pv-team-line">
    <span class="pv-team-label">セリフ4・組名コール（約1秒）</span>
    <p>「赤組！」</p>
    <div class="pv-file-names">
      <code>Red_{CastName}_TeamName01_ORG.wav</code>
      <code>Red_{CastName}_TeamName02_ORG.wav</code>
    </div>
  </div>
  <div class="pv-team-line">
    <span class="pv-team-label">セリフ5・チームの掛け声（約2秒）</span>
    <p>「よっしゃ行くぞ〜！」</p>
    <div class="pv-file-names">
      <code>Red_{CastName}_TeamShout01_ORG.wav</code>
      <code>Red_{CastName}_TeamShout02_ORG.wav</code>
    </div>
  </div>
</div>
```

`.pv-team-members`は3列、画像は正方形、既存チームカラー枠を使う。ファイル名は横にはみ出さないようにする。

```css
#pv-voice .pv-team-members {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 6px;
  max-width: 180px;
  margin: 0 auto 14px;
}

#pv-voice .pv-team-members img {
  display: block;
  width: 100%;
  aspect-ratio: 1;
  object-fit: cover;
  border: 2px solid var(--tc);
  border-radius: 50%;
}

#pv-voice .pv-file-names {
  display: grid;
  gap: 4px;
  margin-top: 10px;
}

#pv-voice .pv-file-names code {
  overflow-wrap: anywhere;
  word-break: break-word;
  white-space: normal;
}
```

- [ ] **Step 5: 既存名簿画像をPVカードへ複製する**

Task 1のIIFE内へ次を追加する。base64データURIはHTMLソースへ再記載しない。

```javascript
const teamCards = document.querySelectorAll("#teams .team-card");
const pvTeamCards = document.querySelectorAll("#pv-voice [data-team-index]");

pvTeamCards.forEach((pvTeamCard) => {
  const teamIndex = Number(pvTeamCard.dataset.teamIndex);
  const sourceImages = teamCards[teamIndex]?.querySelectorAll(".member img") ?? [];
  const target = pvTeamCard.querySelector(".pv-team-members");
  sourceImages.forEach((image) => target.append(image.cloneNode(true)));
});
```

- [ ] **Step 6: 録音手順を左揃えにする**

```css
#pv-voice .pv-route-card {
  text-align: left;
}

#pv-voice .pv-route-card p,
#pv-voice .pv-route-card li,
#pv-voice .pv-steps,
#pv-voice .pv-detail-box,
#pv-voice .pv-recording-tips {
  text-align: left;
}

#pv-voice .pv-route-card p,
#pv-voice .pv-steps,
#pv-voice .pv-detail-box {
  margin-left: 0;
  margin-right: 0;
}
```

セクション見出し、`PV音声収録`のタイトル、提出ボタンは中央揃えを維持する。旧「＋α」カードは削除する。

- [ ] **Step 7: PVテストを通す**

Run:

```bash
python3 tests/test_event_page.py
```

Expected: Task 3の3項目を含め全項目PASS。JPEG base64は55件、PNG base64は1件のまま。

- [ ] **Step 8: Task 3をコミットする**

```bash
git add tests/test_event_page.py イベント概要_大運動会2026.html
git commit -m "feat: expand PV voice submission guide"
```

### Task 4: 3ファイル同期とREADME更新

**Files:**
- Modify: `tests/test_event_page.py:1-80`
- Modify: `index.html`
- Modify: `undo-kai.html`
- Modify: `README.md`

**Interfaces:**
- Consumes: 完成した`イベント概要_大運動会2026.html`
- Produces: バイト単位で同一の3HTML、GitHub Pages向け運用説明

- [ ] **Step 1: 3ファイル一致の失敗テストを書く**

定数を次のように変更する。

```python
PROJECT_ROOT = SCRIPT_PATH.parent.parent
HTML_PATH = (PROJECT_ROOT / "イベント概要_大運動会2026.html").resolve()
HTML_COPIES = [
    HTML_PATH,
    (PROJECT_ROOT / "index.html").resolve(),
    (PROJECT_ROOT / "undo-kai.html").resolve(),
]
```

`main()`冒頭へ次を追加する。

```python
copy_contents = [path.read_bytes() for path in HTML_COPIES if path.exists()]
copies_ok = len(copy_contents) == 3 and len(set(copy_contents)) == 1
ok &= print_result(
    "3つのHTMLが同一内容",
    "PASS" if copies_ok else "FAIL",
    ", ".join(path.name for path in HTML_COPIES),
)
```

- [ ] **Step 2: 一致テストが失敗することを確認する**

Run:

```bash
python3 tests/test_event_page.py
```

Expected: `FAIL: 3つのHTMLが同一内容`。ほかはPASS。

- [ ] **Step 3: 完成HTMLを2ファイルへ同期する**

base64を含む約4,000行を手作業で再編集せず、編集元を機械的にコピーする。

```bash
cp イベント概要_大運動会2026.html index.html
cp イベント概要_大運動会2026.html undo-kai.html
```

- [ ] **Step 4: READMEをキャスト向けGitHub Pagesの説明へ更新する**

README冒頭と運用説明を次の内容へ更新する。

```markdown
# BackStage 大運動会2026 — キャスト向け案内ページ

大運動会2026（2026/8/17〜8/23）の参加キャスト向け案内ページを共有管理するリポジトリです。GitHub Pagesでは`index.html`を公開します。

## 実装方針

- HTML・CSS・画像・JavaScriptをHTMLファイル内に保持
- 外部JavaScript・外部CSS・外部画像の読み込みなし
- モバイル用メニューに小さなインラインJavaScriptを使用
- `イベント概要_大運動会2026.html`を編集元とし、`index.html`と`undo-kai.html`へ同期
```

「ユーザー向けルールページ」「JSなし」「公開前にPVセクションを削除」「GASデプロイ」の説明を削除し、次を記載する。

```markdown
## GitHub Pagesへの反映

1. `イベント概要_大運動会2026.html`を編集
2. `index.html`と`undo-kai.html`へ同じ内容を同期
3. `python3 tests/test_event_page.py`を実行
4. 3ファイル一致と全テスト成功を確認してpush
```

- [ ] **Step 5: 同期とREADMEを検証する**

Run:

```bash
python3 tests/test_event_page.py
shasum -a 256 イベント概要_大運動会2026.html index.html undo-kai.html
```

Expected: 全テストPASS。3つのSHA-256が一致。

- [ ] **Step 6: Task 4をコミットする**

```bash
git add README.md tests/test_event_page.py イベント概要_大運動会2026.html index.html undo-kai.html
git commit -m "docs: align GitHub Pages publishing workflow"
```

### Task 5: モバイル・デスクトップ表示と操作の最終検証

**Files:**
- Diagnose and modify only after a failing regression test: `イベント概要_大運動会2026.html`
- Sync if modified: `index.html`, `undo-kai.html`
- Modify if a regression is found: `tests/test_event_page.py`

**Interfaces:**
- Consumes: 完成した3HTML
- Produces: 390px、768px、1280pxで確認済みのページ

- [ ] **Step 1: 全自動テストを実行する**

Run:

```bash
python3 tests/test_event_page.py
```

Expected: 失敗0件。Chromeが利用可能な環境ではスクリーンショット検査もPASS。

- [ ] **Step 2: GitHub Pages相当のHTTP配信でページを開く**

Run:

```bash
python3 -m http.server 8000
```

ブラウザで`http://127.0.0.1:8000/index.html`を開く。検証終了後にサーバーを停止する。

- [ ] **Step 3: 390×844のモバイル表示を検証する**

次を確認する。

- 固定ヘッダーが本文を不自然に覆わない。
- ハンバーガーが44px以上で、開く・閉じる・外側タップ・Escapeが動作する。
- メニューを開くと閉じるボタンへ、閉じるとハンバーガーへフォーカスが戻る。
- 11リンクすべてが正しいセクションへ移動し、選択後にメニューが閉じる。
- メニュー表示中に背景がスクロールしない。
- 集計時間カード、賞品2種類、PVファイル名、Discordリンクが横にはみ出さない。
- 各PVチームカードに9名の画像が3×3で表示される。
- 録音手順が左揃えで読みやすい。

- [ ] **Step 4: 768pxと1280pxの表示を検証する**

768pxではカードの列切り替えと固定ヘッダー、1280pxでは既存ヒーローナビと本文の中央揃えを確認する。どちらも横スクロールがなく、画像・タイムライン・スコア図が崩れていないことを確認する。

- [ ] **Step 5: ブラウザエラーとリンクを検証する**

ブラウザコンソールにJavaScriptエラーがないことを確認する。次のリンク先が正しいことを確認する。

- 提出フォーム: `https://forms.gle/SMoTKsQ16n4mtEuE9`
- Discord: `https://discord.com/channels/1138387287986679879/1475808380453916682`

- [ ] **Step 6: 不具合があれば回帰テストを先に追加して修正する**

不具合ごとに`tests/test_event_page.py`へ失敗する検査を追加し、失敗理由を確認してから最小のHTML/CSS/JavaScript修正を行う。修正後に編集元を`index.html`と`undo-kai.html`へ再同期する。

- [ ] **Step 7: 最終検証を再実行する**

Run:

```bash
python3 tests/test_event_page.py
git diff --check
git status --short
```

Expected: テスト失敗0件、`git diff --check`出力なし。作業対象以外の変更なし。

- [ ] **Step 8: 最終修正がある場合のみコミットする**

```bash
git add tests/test_event_page.py イベント概要_大運動会2026.html index.html undo-kai.html
git commit -m "fix: polish responsive cast guide"
```
