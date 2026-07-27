#!/usr/bin/env python3
"""Self-check for the 大運動会2026 event page."""

from __future__ import annotations

import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parent.parent
HTML_PATH = (PROJECT_ROOT / "イベント概要_大運動会2026.html").resolve()
HTML_COPIES = [
    HTML_PATH,
    (PROJECT_ROOT / "index.html").resolve(),
    (PROJECT_ROOT / "undo-kai.html").resolve(),
]
SCRATCHPAD = Path(
    "/private/tmp/claude-501/-Users-kh-Documents-work-ob/"
    "bb78e0a7-a76e-437b-954a-05c7adc6dd90/scratchpad"
)
REQUIRE_BROWSER_TESTS = os.environ.get("REQUIRE_BROWSER_TESTS") == "1"
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
PRIZE_DETAIL_URL = (
    "https://discord.com/channels/1138387287986679879/"
    "1528011762572595231/1529844197350309939"
)
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
EXPECTED_MEMBERS = [
    "言乃葩和", "魔法少女ぴょん", "夜狩うる", "7_ko", "境内リカ", "まいくま", "ブルーローズアイス", "冬月シオン", "わたあめ",
    "玉木瑶", "あまタクシー", "紫月ほたる", "目黒れる", "山岸紫苑", "Nico", "スイ・カウハ", "紗衣", "オイエ・ナイスガイ",
    "千里香", "赤絲こゆび", "旅乃とき", "かずさ", "ミラ・エトワール", "沙耶", "おめがまる", "焦赤緋色", "ルカ・ミント",
    "蔦ヰ田リウ", "はちみつ", "プルミエール・エトワール", "微々", "雪織みみ", "水野ゆか", "西那てまり", "月詠くるみ", "ゆうり",
    "こぐま もる", "白猫にゃる", "小向なのか", "MUZU", "桜咲はるね", "白浪しおん", "めぐるん", "黒川水晶", "シン・クラーク",
    "黒柴えいら", "超絶はおちー", "蒼羽れいな", "三毒ローパ", "呑田くれい", "奈夢夛", "六華ミル", "海鈴なぎ", "木ノ崎叶和",
]


def browser_candidates() -> list[Path]:
    candidates: list[Path] = []
    for variable in ["EVENT_PAGE_BROWSER", "CHROME_PATH", "CHROME_BIN"]:
        value = os.environ.get(variable)
        if value:
            candidates.append(Path(value).expanduser())

    candidates.extend(
        Path(path)
        for path in [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
        ]
    )
    for executable in [
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
        "chrome",
    ]:
        resolved = shutil.which(executable)
        if resolved:
            candidates.append(Path(resolved))

    cache_roots = [
        Path.home() / "Library/Caches/ms-playwright",
        Path.home() / ".cache/ms-playwright",
        PROJECT_ROOT / "node_modules/playwright-core/.local-browsers",
    ]
    playwright_patterns = [
        "chromium-*/chrome-mac*/Chromium.app/Contents/MacOS/Chromium",
        "chromium-*/chrome-mac*/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing",
        "chromium-*/chrome-linux*/chrome",
        "chromium_headless_shell-*/chrome-headless-shell-mac*/chrome-headless-shell",
        "chromium_headless_shell-*/chrome-headless-shell-linux*/chrome-headless-shell",
    ]
    for root in cache_roots:
        for pattern in playwright_patterns:
            candidates.extend(sorted(root.glob(pattern), reverse=True))

    return list(dict.fromkeys(path.resolve() for path in candidates))


def discover_browser() -> Path | None:
    for candidate in browser_candidates():
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    return None


BROWSER = discover_browser()


def strip_data_uris(text: str) -> str:
    return re.sub(r"data:image/[^\"']+", "data:image/STRIPPED", text)


def style_block(text: str) -> str:
    match = re.search(r"<style>\s*(.*?)\s*</style>", text, re.S | re.I)
    return match.group(1) if match else ""


def at_rule_body(css: str, header_pattern: str) -> str:
    match = re.search(header_pattern, css, re.I)
    if not match:
        return ""
    opening = css.find("{", match.end())
    if opening < 0:
        return ""
    depth = 1
    cursor = opening + 1
    while cursor < len(css) and depth:
        if css[cursor] == "{":
            depth += 1
        elif css[cursor] == "}":
            depth -= 1
        cursor += 1
    return css[opening + 1 : cursor - 1] if depth == 0 else ""


def css_rule_bodies(css: str, target_selector: str) -> list[str]:
    bodies = []
    for selector_text, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css, re.S):
        selectors = []
        start = 0
        depth = 0
        for index, character in enumerate(selector_text):
            if character == "(":
                depth += 1
            elif character == ")":
                depth = max(0, depth - 1)
            elif character == "," and depth == 0:
                selectors.append(selector_text[start:index].strip())
                start = index + 1
        selectors.append(selector_text[start:].strip())
        if target_selector in selectors:
            bodies.append(body)
    return bodies


def last_font_size_px(css: str, target_selector: str) -> float | None:
    sizes = []
    for body in css_rule_bodies(css, target_selector):
        sizes.extend(
            float(value)
            for value in re.findall(r"font-size\s*:\s*([0-9.]+)px\b", body)
        )
    return sizes[-1] if sizes else None


def css_color(css: str, custom_property: str) -> str:
    match = re.search(
        rf"--{re.escape(custom_property)}\s*:\s*(#[0-9A-Fa-f]{{6}})\b",
        css,
    )
    return match.group(1) if match else ""


def contrast_ratio(first: str, second: str) -> float:
    def luminance(color: str) -> float:
        channels = [int(color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [
            value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
            for value in channels
        ]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    lighter, darker = sorted([luminance(first), luminance(second)], reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def visible_text(text: str) -> str:
    stripped = re.sub(r"<style\b[^>]*>.*?</style>", "", text, flags=re.S | re.I)
    stripped = re.sub(r"<wbr\s*/?>", "", stripped, flags=re.I)
    stripped = re.sub(r"<[^>]+>", "", stripped)
    return re.sub(r"\s+", " ", stripped)


def section_block(text: str, section_id: str) -> str:
    pattern = rf'<section\b[^>]*\bid="{re.escape(section_id)}"[^>]*>(.*?)</section>'
    match = re.search(pattern, text, re.S | re.I)
    return match.group(1) if match else ""


def has_auto_margin(body: str) -> bool:
    compact = re.sub(r"\s+", " ", body)
    if re.search(r"margin\s*:\s*[^;]*\bauto\b", compact):
        return True
    if re.search(r"margin-inline\s*:\s*[^;]*\bauto\b", compact):
        return True
    return bool(
        re.search(r"margin-left\s*:\s*auto\b", compact)
        and re.search(r"margin-right\s*:\s*auto\b", compact)
    )


def strip_media_blocks(css: str) -> str:
    cleaned: list[str] = []
    i = 0
    while i < len(css):
        media = re.match(r"\s*@media\b[^{]*\{", css[i:])
        if not media:
            cleaned.append(css[i])
            i += 1
            continue
        i += media.end()
        depth = 1
        while i < len(css) and depth:
            if css[i] == "{":
                depth += 1
            elif css[i] == "}":
                depth -= 1
            i += 1
    return "".join(cleaned)


def css_rule_failures(css: str) -> list[str]:
    failures: list[str] = []
    left_allowed = {
        "#points .rule-table td:nth-child(3)",
        ".timeline-item-text",
        "#pv-voice .pv-route-card",
        "#pv-voice .pv-route-card p",
        "#pv-voice .pv-route-card li",
        "#pv-voice .pv-steps",
        "#pv-voice .pv-detail-box",
        "#pv-voice .pv-recording-tips",
        ".section-toggle-title",
    }
    base_css = strip_media_blocks(css)

    if re.search(r"justify-content\s*:\s*flex-start\b", base_css):
        failures.append("justify-content:flex-start が残っています")

    for raw in base_css.split("}"):
        if "{" not in raw:
            continue
        selector, body = raw.rsplit("{", 1)
        selector = selector.strip()
        body = body.strip()
        if not selector or not body:
            continue

        if "max-width" in body:
            if selector == ".wrap":
                pass
            elif re.search(r"max-width\s*:\s*100%", body):
                pass
            elif re.search(r"max-width\s*:\s*none\b", body):
                pass
            elif "::" in selector:
                pass
            elif not has_auto_margin(body):
                failures.append(f"{selector}: max-width と auto margin が同居していません")

        if re.search(r"text-align\s*:\s*left\b", body):
            selectors = [item.strip() for item in selector.split(",")]
            bad = [item for item in selectors if item not in left_allowed]
            if bad:
                failures.append(f"{selector}: text-align:left は許可外です")

    return failures


def browser_probe() -> tuple[bool, str]:
    global BROWSER
    executable_candidates = [
        candidate
        for candidate in browser_candidates()
        if candidate.is_file() and os.access(candidate, os.X_OK)
    ]
    if not executable_candidates:
        return False, "Chromium系ブラウザが見つかりません"
    failures = []
    for candidate in executable_candidates:
        try:
            with tempfile.TemporaryDirectory(prefix="event-page-browser-probe-") as profile:
                result = subprocess.run(
                    [
                        str(candidate),
                        "--headless",
                        "--no-sandbox",
                        "--disable-gpu",
                        "--disable-dev-shm-usage",
                        f"--user-data-dir={profile}",
                        "--dump-dom",
                        "about:blank",
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{candidate.name}: {exc}")
            continue
        if result.returncode == 0:
            BROWSER = candidate
            return True, str(candidate)
        message = (result.stderr or result.stdout).strip().splitlines()
        failures.append(
            f"{candidate.name}: "
            f"{message[-1] if message else f'exit {result.returncode}'}"
        )
    return False, "; ".join(failures)[:500]


def dump_rendered_dom() -> tuple[bool, str]:
    if BROWSER is None:
        return False, ""
    with tempfile.TemporaryDirectory(prefix="event-page-render-") as profile:
        result = subprocess.run(
            [
                str(BROWSER),
                "--headless",
                "--no-sandbox",
                "--disable-gpu",
                "--disable-dev-shm-usage",
                f"--user-data-dir={profile}",
                "--dump-dom",
                HTML_PATH.as_uri(),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
    return result.returncode == 0, result.stdout


def dump_no_js_dom() -> tuple[bool, str]:
    if BROWSER is None:
        return False, ""
    with tempfile.TemporaryDirectory(prefix="event-page-no-js-") as profile:
        result = subprocess.run(
            [
                str(BROWSER),
                "--headless",
                "--no-sandbox",
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--disable-javascript",
                f"--user-data-dir={profile}",
                "--dump-dom",
                HTML_PATH.as_uri(),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
    return result.returncode == 0, result.stdout


def run_runtime_assertions(source_html: str) -> tuple[bool, dict[str, bool] | str]:
    if BROWSER is None:
        return False, "Chromium系ブラウザが見つかりません"
    harness = """
  <output id="runtime-test-results" hidden></output>
  <script>
    (() => {
      const results = {};
      const output = document.getElementById("runtime-test-results");
      output.textContent = JSON.stringify({ harnessStarted: true });
      const toggles = [...document.querySelectorAll(".section-toggle")];
      const summaries = toggles.map((details) => details.querySelector("summary"));
      const teams = document.querySelector('[data-section-id="teams"]');
      const points = document.querySelector('[data-section-id="points"]');

      results.keyboardNativeDetails =
        toggles.length === 11
        && summaries.every((summary) => summary?.tagName === "SUMMARY" && summary.tabIndex === 0);
      teams.querySelector("summary").click();
      points.querySelector("summary").click();
      results.nativeSummaryActivation = teams.open && points.open;
      const openedSummary = points.querySelector("summary");
      openedSummary.focus();
      const openedSummaryStyle = getComputedStyle(openedSummary);
      const openedSummaryTitleStyle = getComputedStyle(
        openedSummary.querySelector(".section-toggle-title")
      );
      const everyClosedToggleHasTransparentBorder = toggles.every((details) => {
        const style = getComputedStyle(details.querySelector("summary"));
        return [
          style.borderTopColor,
          style.borderRightColor,
          style.borderBottomColor,
          style.borderLeftColor,
        ].every((color) => color === "rgba(0, 0, 0, 0)");
      });
      const everyOpenedToggleHasTransparentBorder = toggles.every((details) => {
        details.open = true;
        const style = getComputedStyle(details.querySelector("summary"));
        return [
          style.borderTopColor,
          style.borderRightColor,
          style.borderBottomColor,
          style.borderLeftColor,
        ].every((color) => color === "rgba(0, 0, 0, 0)");
      });
      const everyOpenedSectionFrameIsPresent = toggles.every((details) => {
        const style = getComputedStyle(details.closest(".section"));
        return parseFloat(style.borderTopLeftRadius) > 0
          && style.boxShadow !== "none";
      });
      results.openToggleBorderlessWithTextFocus = points.open
        && everyClosedToggleHasTransparentBorder
        && everyOpenedToggleHasTransparentBorder
        && openedSummary.matches(":focus-visible")
        && openedSummaryStyle.outlineStyle === "none"
        && openedSummaryTitleStyle.textDecorationLine.includes("underline");
      results.openSectionFramePresent = everyOpenedSectionFrameIsPresent;
      results.multipleToggles = teams.open && points.open
        && document.querySelector('[data-section-id="about"]').open;

      const dialog = document.getElementById("mobile-menu");
      document.getElementById("menu-toggle").click();
      results.menuOpened = dialog.open
        && document.getElementById("menu-toggle").getAttribute("aria-expanded") === "true"
        && document.activeElement === document.getElementById("menu-close");
      document.getElementById("menu-close").click();

      setTimeout(() => {
        results.menuDismissalFocus = !dialog.open
          && document.activeElement === document.getElementById("menu-toggle");
        document.getElementById("menu-toggle").click();
        dialog.querySelector('a[href="#prize"]').click();

        setTimeout(() => {
        const prize = document.querySelector('[data-section-id="prize"]');
        results.menuNavigation = !dialog.open
          && window.location.hash === "#prize"
          && prize.open;

          window.history.replaceState(null, "", "#faq");
          window.dispatchEvent(new HashChangeEvent("hashchange"));
          results.hashNavigation =
            document.querySelector('[data-section-id="faq"]').open;
          const rosters = [...document.querySelectorAll(".pv-team-members")];
          results.enhancedRosters = rosters.length === 6
            && rosters.every((roster) =>
              roster.querySelectorAll("img").length === 9
              && roster.querySelectorAll(
                ".pv-team-members-fallback:not([hidden]) li"
              ).length === 0
            );
          toggles.forEach((details) => {
            details.open = true;
          });
          const labelSelectors = [
            ".mission-rank",
            ".mission-status",
            ".score-scale",
            ".tally-axis-labels",
            ".tally-date small",
            ".tally-broadcast-label",
          ];
          results.mobileType = parseFloat(getComputedStyle(document.body).fontSize) >= 16
            && labelSelectors.every((selector) =>
              parseFloat(getComputedStyle(document.querySelector(selector)).fontSize) >= 13
            );
          results.noHorizontalOverflow =
            document.documentElement.scrollWidth <= window.innerWidth;
          output.textContent = JSON.stringify(results);
        }, 250);
      }, 250);
    })();
  </script>
"""
    with tempfile.TemporaryDirectory(prefix="event-page-runtime-") as temp_dir:
        runtime_path = Path(temp_dir) / "runtime.html"
        runtime_path.write_text(
            source_html.replace("</body>", f"{harness}\n</body>"),
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                str(BROWSER),
                "--headless",
                "--no-sandbox",
                "--disable-gpu",
                "--disable-dev-shm-usage",
                f"--user-data-dir={temp_dir}/profile",
                "--window-size=390,900",
                "--virtual-time-budget=2000",
                "--dump-dom",
                runtime_path.as_uri(),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
    if result.returncode != 0:
        return False, (result.stderr or result.stdout).strip()[:500]
    match = re.search(
        r'<output\b(?=[^>]*\bid="runtime-test-results")[^>]*>(.*?)</output>',
        result.stdout,
        re.S,
    )
    if not match:
        return False, "runtime results were not emitted"
    try:
        return True, json.loads(html.unescape(match.group(1)))
    except json.JSONDecodeError as exc:
        return False, f"runtime results were invalid: {exc}"


def run_chrome(width: int, height: int, output: Path) -> tuple[str, bool, str]:
    if BROWSER is None:
        return ("FAIL", False, "Chromium系ブラウザが見つかりません")
    cmd = [
        str(BROWSER),
        "--headless",
        "--no-sandbox",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        f"--screenshot={output}",
        f"--window-size={width},{height}",
        HTML_PATH.as_uri(),
    ]
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="event-page-screenshot-") as profile:
            result = subprocess.run(
                [*cmd[:-1], f"--user-data-dir={profile}", cmd[-1]],
                check=False,
                capture_output=True,
                text=True,
                timeout=60,
            )
    except Exception as exc:  # noqa: BLE001
        return ("FAIL", False, f"Chrome起動失敗: {exc}")
    if result.returncode != 0:
        stderr = (result.stderr or result.stdout).strip()
        return ("FAIL", False, stderr[:500])
    if not output.exists():
        return ("FAIL", False, f"スクリーンショット未生成: {output}")
    size = output.stat().st_size
    if size <= 10 * 1024:
        return ("FAIL", False, f"スクリーンショットが小さすぎます: {size} bytes")
    return ("PASS", True, f"{output} ({size} bytes)")


def print_result(label: str, status: str, detail: str = "") -> bool:
    suffix = f" - {detail}" if detail else ""
    print(f"{status}: {label}{suffix}")
    return status in {"PASS", "SKIP"}


def main() -> int:
    if not HTML_PATH.exists():
        print_result("HTMLファイル存在", "FAIL", str(HTML_PATH))
        return 1

    copy_contents = [path.read_bytes() for path in HTML_COPIES if path.exists()]
    copies_ok = len(copy_contents) == 3 and len(set(copy_contents)) == 1
    copy_test_ok = print_result(
        "3つのHTMLが同一内容",
        "PASS" if copies_ok else "FAIL",
        ", ".join(path.name for path in HTML_COPIES),
    )

    text = HTML_PATH.read_text(encoding="utf-8")
    css = style_block(text)
    rendered_text = visible_text(strip_data_uris(text))
    ok = copy_test_ok

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

    ok &= print_result("応援枠 0件", "PASS" if text.count("応援枠") == 0 else "FAIL", f"{text.count('応援枠')}件")

    forbidden_terms = [
        "運営稼働pt",
        "9人チームになったため",
        "予算",
        "報酬額",
        "チーム分けアルゴリズム",
        "担当者名",
    ]
    found_forbidden_terms = [term for term in forbidden_terms if term in rendered_text]
    ok &= print_result(
        "掲載禁止語 0件",
        "PASS" if not found_forbidden_terms else "FAIL",
        ", ".join(found_forbidden_terms),
    )

    emoji_hits = re.findall(r"[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F]", text)
    ok &= print_result("絵文字 0件", "PASS" if not emoji_hits else "FAIL", f"{len(emoji_hits)}件")

    allowed_urls = {
        "https://forms.gle/SMoTKsQ16n4mtEuE9",
        "https://discord.com/channels/1138387287986679879/1475808380453916682",
        PRIZE_DETAIL_URL,
    }
    found_urls = set(re.findall(r'https?://[^"\s<]+', strip_data_uris(text)))
    unexpected_urls = sorted(found_urls - allowed_urls)
    external_scripts = re.findall(r'<script\b[^>]*\bsrc\s*=', text, re.I)
    ok &= print_result(
        "外部URLは提出フォームとDiscordのみ・外部scriptなし",
        "PASS" if not unexpected_urls and not external_scripts else "FAIL",
        ", ".join(unexpected_urls),
    )

    pv_block = section_block(text, "pv-voice")
    pv_text = visible_text(pv_block)
    pv_form_url = "https://forms.gle/SMoTKsQ16n4mtEuE9"
    pv_email = "h_sawa@virtualidol.info"
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
        "{TeamColor}は自分のチーム色",
        "{CastName}は可能であれば半角英字",
    ]
    pv_forbidden = [
        "収録をお願いしたいセリフは4つ",
        "全員共通の2つ",
        "＋α（余裕があればぜひ！）",
        "こちらは必須ではありません",
    ]
    pv_ok = (
        all(term in pv_text for term in pv_required)
        and not any(term in pv_text for term in pv_forbidden)
        and "CAST-ONLY:PV-VOICE" not in text
        and pv_block.count(pv_form_url) == 1
        and pv_email in pv_block
    )
    ok &= print_result(
        "PV音声: 必須5セリフとファイル名",
        "PASS" if pv_ok else "FAIL",
    )
    pv_form_link_match = re.search(
        rf'<a\b[^>]*\bhref="{re.escape(pv_form_url)}"[^>]*>',
        pv_block,
        re.I,
    )
    pv_form_link = pv_form_link_match.group(0) if pv_form_link_match else ""
    pv_form_rel_match = re.search(r'\brel="([^"]*)"', pv_form_link, re.I)
    pv_form_rel = set(pv_form_rel_match.group(1).split()) if pv_form_rel_match else set()
    pv_form_link_ok = (
        'target="_blank"' in pv_form_link
        and {"noopener", "noreferrer"}.issubset(pv_form_rel)
    )
    ok &= print_result(
        "PV音声: 提出フォームの外部リンク保護",
        "PASS" if pv_form_link_ok else "FAIL",
    )

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

    nav_match = re.search(r'<nav class="anchor-nav".*?</nav>', text, re.S)
    nav_html = nav_match.group(0) if nav_match else ""
    nav_expected = [
        ('#teams', "チーム発表"),
        ('#rules', "デイリーミッション"),
        ('#points', "ポイントのしくみ"),
        ('#half-time', "中間発表クイズ"),
        ('#survival', "脱落ルール"),
        ('#schedule', "スケジュール"),
        ('#prize', "特典"),
        ('#pv-voice', "PV音声収録"),
        ('#faq', "FAQ"),
    ]
    nav_missing = [label for href, label in nav_expected if f'<a href="{href}">{label}</a>' not in nav_html]
    ok &= print_result(
        "目次: セクションタイトルと一致（9リンク）",
        "PASS" if not nav_missing else "FAIL",
        ", ".join(nav_missing),
    )

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
    close_button_match = re.search(r'<button\b[^>]*\bid="menu-close"[^>]*>(.*?)</button>', text, re.S)
    close_button_html = close_button_match.group(1) if close_button_match else ""
    if 'fill="none"' not in close_button_html or 'stroke="currentColor"' not in close_button_html:
        mobile_nav_failures.append("閉じるアイコンの線")
    menu_dialog_rule = re.search(r"\.menu-dialog\s*\{(?P<body>.*?)\}", css, re.S)
    menu_dialog_body = menu_dialog_rule.group("body") if menu_dialog_rule else ""
    if not re.search(r"max-width\s*:\s*none\b", menu_dialog_body):
        mobile_nav_failures.append("dialog max-width:none")
    if not re.search(r"max-height\s*:\s*none\b", menu_dialog_body):
        mobile_nav_failures.append("dialog max-height:none")
    html_rule = re.search(r"\bhtml\s*\{(?P<body>.*?)\}", css, re.S)
    html_rule_body = html_rule.group("body") if html_rule else ""
    if not re.search(r"scroll-padding-top\s*:", html_rule_body):
        mobile_nav_failures.append("sticky header scroll offset")
    for href in mobile_nav_hrefs:
        if f'href="{href}"' not in mobile_nav_html:
            mobile_nav_failures.append(href)
    mobile_nav_labels = {
        href: visible_text(label)
        for href, label in re.findall(
            r'<a\b[^>]*\bhref="(#[^"]+)"[^>]*>(.*?)</a>',
            mobile_nav_html,
            re.S | re.I,
        )
    }
    for section_id, expected_label in TOGGLE_SECTIONS:
        href = f"#{section_id}"
        if mobile_nav_labels.get(href) != expected_label:
            mobile_nav_failures.append(
                f"{href}={mobile_nav_labels.get(href)!r} (expected {expected_label!r})"
            )
    if '<nav aria-label="モバイル用ページ内ナビゲーション">' not in mobile_nav_html:
        mobile_nav_failures.append("モバイルnavランドマーク")
    for js_term in [
        "showModal()",
        "menuDialog.close()",
        'menuDialog.addEventListener("close"',
        "event.target === menuDialog",
        'window.matchMedia("(min-width: 720px)")',
        'desktopMedia.addEventListener("change"',
        "if (event.matches)",
    ]:
        if js_term not in text:
            mobile_nav_failures.append(js_term)
    if external_scripts:
        mobile_nav_failures.append("外部script")
    ok &= print_result(
        "モバイルメニュー: dialog・11リンク・閉じる操作",
        "PASS" if not mobile_nav_failures else "FAIL",
        ", ".join(mobile_nav_failures),
    )

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

    contact_html = section_block(text, "contact")
    discord_url = "https://discord.com/channels/1138387287986679879/1475808380453916682"
    contact_ok = (
        "ご不明点や運営へのご相談は、Discord内の「運営への依頼窓口」からご連絡ください。" in visible_text(contact_html)
        and contact_html.count(discord_url) == 1
        and 'rel="noopener noreferrer"' in contact_html
    )
    ok &= print_result("お問い合わせ: Discord窓口", "PASS" if contact_ok else "FAIL")

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
    rules_notice_match = re.search(r'<p class="notice">(.*?)</p>', section_block(text, "rules"), re.S)
    rules_notice_text = visible_text(rules_notice_match.group(1)) if rules_notice_match else ""
    collection_ok = (
        collection_ok
        and "8/20は20:00締め" in rules_notice_text
        and "8/23は21:00締め" in rules_notice_text
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

    teams_block = section_block(text, "teams")
    leader_ok = (
        "運営リーダーの割り当ては後日発表" in teams_block
        and "運営リーダー：（仮）" not in text
        and "チーム発表" in teams_block
    )
    ok &= print_result("チーム発表: リーダー後日発表の注記", "PASS" if leader_ok else "FAIL")

    prize_block = section_block(text, "prize")
    prize_needed = ["自遊空間", "掲出予定", "調整中", "優勝賞品", "準優勝賞品", "パネル設置", "ブースPOP", "集合立ち絵ポスター"]
    prize_missing = [term for term in prize_needed if term not in prize_block]
    ok &= print_result(
        "特典: 自遊空間掲出（優勝/準優勝の内訳）",
        "PASS" if not prize_missing else "FAIL",
        ", ".join(prize_missing),
    )

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

    css_compact = re.sub(r"\s+", " ", css)
    reduced_motion_css = at_rule_body(
        css,
        r"@media\s*\(\s*prefers-reduced-motion\s*:\s*reduce\s*\)",
    )
    reduced_motion_ok = any(
        re.search(r"scroll-behavior\s*:\s*auto\b", body)
        for body in css_rule_bodies(reduced_motion_css, "html")
    )
    ok &= print_result(
        "モーション低減: CSSスムーズスクロール無効化",
        "PASS" if reduced_motion_ok else "FAIL",
    )

    light_focus_selectors = [
        "a:focus-visible",
        ".mobile-menu-link:focus-visible",
        ".contact-link:focus-visible",
        ".section-toggle-summary:focus-visible",
    ]
    dark_focus_selectors = [
        ".topbar :is(a, button):focus-visible",
        ".section.inverse .section-toggle-summary:focus-visible",
    ]
    light_focus_rules_ok = all(
        any("var(--royal)" in body for body in css_rule_bodies(css, selector))
        for selector in light_focus_selectors
    )
    dark_focus_rules_ok = all(
        any("var(--yellow)" in body for body in css_rule_bodies(css, selector))
        for selector in dark_focus_selectors
    )
    royal = css_color(css, "royal")
    yellow = css_color(css, "yellow")
    white = css_color(css, "white")
    royal_deep = css_color(css, "royal-deep")
    sky_deep = css_color(css, "sky-deep")
    focus_contrast_ok = (
        all([royal, yellow, white, royal_deep, sky_deep])
        and contrast_ratio(royal, white) >= 3
        and contrast_ratio(yellow, royal_deep) >= 3
        and contrast_ratio(yellow, sky_deep) >= 3
    )
    ok &= print_result(
        "フォーカス表示: 明背景・暗背景で3:1以上",
        "PASS"
        if light_focus_rules_ok and dark_focus_rules_ok and focus_contrast_ok
        else "FAIL",
        (
            f"light={light_focus_rules_ok}, dark={dark_focus_rules_ok}, "
            f"contrast={focus_contrast_ok}"
        ),
    )

    mobile_css = at_rule_body(css, r"@media\s*\(\s*max-width\s*:\s*560px\s*\)")
    mobile_label_selectors = [
        ".mission-rank",
        ".mission-status",
        ".mission-bonus",
        ".score-scale",
        ".tally-axis-labels",
        ".tally-date",
        ".tally-date small",
        ".tally-broadcast-label",
    ]
    body_font_size = last_font_size_px(strip_media_blocks(css), "body")
    undersized_mobile_labels = {
        selector: last_font_size_px(mobile_css, selector)
        for selector in mobile_label_selectors
        if (last_font_size_px(mobile_css, selector) or 0) < 13
    }
    mobile_type_ok = (
        body_font_size is not None
        and body_font_size >= 16
        and not undersized_mobile_labels
    )
    ok &= print_result(
        "390px文字サイズ: 本文16px・重要ラベル13px以上",
        "PASS" if mobile_type_ok else "FAIL",
        f"body={body_font_size}; labels={undersized_mobile_labels}",
    )

    pv_alignment_ok = all(
        re.search(
            rf"{re.escape(selector)}\s*\{{[^}}]*text-align\s*:\s*left\b",
            css,
            re.S,
        )
        for selector in [
            "#pv-voice .pv-route-card",
            "#pv-voice .pv-steps",
            "#pv-voice .pv-detail-box",
            "#pv-voice .pv-recording-tips",
        ]
    )
    ok &= print_result("PV音声: 録音方法の左揃え", "PASS" if pv_alignment_ok else "FAIL")

    auto_phrase_ok = "word-break: auto-phrase" in css_compact
    pretty_ok = "text-wrap: pretty" in css_compact
    ok &= print_result(
        "文節折り返しCSS",
        "PASS" if auto_phrase_ok and pretty_ok else "FAIL",
        f"auto-phrase={auto_phrase_ok}, pretty={pretty_ok}",
    )

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

    nw_rule_ok = bool(re.search(r"\.nw\s*\{[^}]*white-space\s*:\s*nowrap\b", css, re.S))
    nw_count = len(re.findall(r'class="nw"', text))
    ok &= print_result(
        ".nw nowrap定義と本文適用",
        "PASS" if nw_rule_ok and nw_count >= 10 else "FAIL",
        f"rule={nw_rule_ok}, count={nw_count}",
    )

    required_phrases = [
        "早押しクイズ大会を開催",
        "集合SDイラスト",
        "デイリーミッション",
        "中間発表前まで",
        "累積ポイントが10pt未満",
        "順位ボーナスの配点",
        "大運動会2026 — BackStage",
    ]
    missing_phrases = [phrase for phrase in required_phrases if phrase not in rendered_text]
    ok &= print_result(
        "主要文言維持",
        "PASS" if not missing_phrases else "FAIL",
        ", ".join(missing_phrases),
    )

    data_count = text.count("data:image/jpeg;base64,")
    hero_ok = 'alt="大運動会2026 開催決定"' in text
    member_imgs = re.findall(r'<div class="member-photo"[^>]*><img [^>]*alt="([^"]+)"', text)
    member_img_ok = len(member_imgs) == 54 and all(member_imgs)
    img_ok = data_count == 55 and hero_ok and member_img_ok
    ok &= print_result(
        "base64 JPEG 55件（hero1+メンバー54）かつalt付き",
        "PASS" if img_ok else "FAIL",
        f"jpeg={data_count} hero={hero_ok} member_img={len(member_imgs)}",
    )

    png_count = text.count("data:image/png;base64,")
    bs_logo_ok = png_count == 1 and 'alt="BackStage"' in text
    ok &= print_result("BackStageロゴ PNG 1件かつaltあり", "PASS" if bs_logo_ok else "FAIL", f"{png_count}件")

    mini_kicker_match = re.search(r"\.mini-kicker\s*\{(?P<body>.*?)\}", css, re.S)
    mini_kicker_body = mini_kicker_match.group("body") if mini_kicker_match else ""
    mini_kicker_ok = bool(re.search(r"margin\s*:\s*0\s+auto\b", re.sub(r"\s+", " ", mini_kicker_body)))
    ok &= print_result(".mini-kicker margin 0 auto", "PASS" if mini_kicker_ok else "FAIL")

    about_heading_count = text.count("これはなに？")
    ok &= print_result("これはなに？ 0件", "PASS" if about_heading_count == 0 else "FAIL", f"{about_heading_count}件")

    missing_ids = [section_id for section_id in REQUIRED_IDS if not re.search(rf'<section\b[^>]*\bid="{re.escape(section_id)}"', text)]
    ok &= print_result("必須section id", "PASS" if not missing_ids else "FAIL", ", ".join(missing_ids))

    member_photo_count = len(re.findall(r'class="member-photo"', text))
    ok &= print_result(
        "チームメンバー 54名",
        "PASS" if member_photo_count == 54 else "FAIL",
        f"{member_photo_count}件",
    )

    teams_html = section_block(text, "teams")
    actual_members = re.findall(r'<div class="member-photo"[^>]*>(?:<img [^>]*alt="([^"]+)"|<svg)', teams_html)
    actual_members = [m for m in actual_members if m]
    leader_count = teams_html.count("運営リーダー：")
    ok &= print_result(
        "チームごとの運営リーダー行 0件（注記に集約・7/28）",
        "PASS" if leader_count == 0 else "FAIL",
        f"{leader_count}件",
    )
    ok &= print_result(
        "チームメンバー表記・並び順",
        "PASS" if actual_members == EXPECTED_MEMBERS else "FAIL",
        f"{len(actual_members)}名",
    )

    pre_js_rosters = re.findall(
        r'<div class="pv-team-members"[^>]*>(.*?)</div>',
        pv_block,
        re.S | re.I,
    )
    pre_js_roster_names = []
    for roster in pre_js_rosters:
        image_names = re.findall(r'<img\b[^>]*\balt="([^"]+)"', roster, re.I)
        fallback_names = [
            visible_text(item)
            for item in re.findall(
                r'<li\b[^>]*>(.*?)</li>',
                roster,
                re.S | re.I,
            )
        ]
        pre_js_roster_names.append(image_names or fallback_names)
    expected_pv_rosters = [
        EXPECTED_MEMBERS[index : index + 9]
        for index in range(0, len(EXPECTED_MEMBERS), 9)
    ]
    ok &= print_result(
        "PV音声: JavaScript実行前も6チーム×9名",
        "PASS" if pre_js_roster_names == expected_pv_rosters else "FAIL",
        str([len(roster) for roster in pre_js_roster_names]),
    )

    old_team_size_count = text.count("1チーム 5〜10人")
    ok &= print_result(
        "旧チーム人数表記 0件",
        "PASS" if old_team_size_count == 0 else "FAIL",
        f"{old_team_size_count}件",
    )

    daily_limit_count = text.count("1日12時間まで")
    ok &= print_result(
        "M1計上上限12h注記あり（7/27採用）",
        "PASS" if daily_limit_count >= 1 else "FAIL",
        f"{daily_limit_count}件",
    )

    spotlight_ok = 'class="spotlight-banner"' in text
    ok &= print_result("重点ミッションバナー", "PASS" if spotlight_ok else "FAIL")

    team_names = ["赤組", "青組", "黄組", "緑組", "橙組", "紫組"]
    missing_team_names = [name for name in team_names if name not in rendered_text]
    ok &= print_result(
        "全6組名",
        "PASS" if not missing_team_names else "FAIL",
        ", ".join(missing_team_names),
    )

    member_img_contract = bool(
        re.search(
            r"\.member-photo\s+img\s*\{[^}]*"
            r"width\s*:\s*100%\s*;[^}]*"
            r"height\s*:\s*100%\s*;[^}]*"
            r"object-fit\s*:\s*cover\s*;[^}]*"
            r"border-radius\s*:\s*inherit\s*;[^}]*"
            r"display\s*:\s*block\s*;",
            css,
            re.S,
        )
    )
    ok &= print_result(
        ".member-photo img 画像差し込み契約",
        "PASS" if member_img_contract else "FAIL",
    )

    old_goal_notice_count = text.count("目標値は、イベント期間中に毎日発表")
    ok &= print_result(
        "旧目標値発表文言 0件",
        "PASS" if old_goal_notice_count == 0 else "FAIL",
        f"{old_goal_notice_count}件",
    )

    rules_html = section_block(text, "rules")
    fixed_goals = ["12時間", "12人", "3人"]
    missing_goals = [goal for goal in fixed_goals if goal not in rules_html]
    ok &= print_result(
        "#rules 固定目標値",
        "PASS" if not missing_goals else "FAIL",
        ", ".join(missing_goals),
    )
    goal_values = re.findall(r'<span class="goal-value">(.*?)</span>', rules_html, re.S)
    goal_value_text = visible_text(" ".join(goal_values))
    ok &= print_result(
        "#rules goal-value内に8時間なし",
        "PASS" if "8時間" not in goal_value_text else "FAIL",
    )

    welcome_back_count = rendered_text.count("はじめまして・おかえり")
    ok &= print_result(
        "はじめまして・おかえり 2件以上",
        "PASS" if welcome_back_count >= 2 else "FAIL",
        f"{welcome_back_count}件",
    )

    ok &= print_result(
        "#rules 3ヶ月以上あり",
        "PASS" if "3ヶ月以上" in visible_text(rules_html) else "FAIL",
    )

    survival_html = section_block(text, "survival")
    survival_text = visible_text(survival_html)
    ok &= print_result(
        "#survival 10pt未満あり",
        "PASS" if "10pt未満" in survival_html else "FAIL",
    )
    survival_half_time_block = (
        "中間発表（クイズ大会）には参加できません" in survival_text
        or "中間発表に不参加" in survival_text
    )
    ok &= print_result(
        "#survival 脱落チームは中間発表不参加",
        "PASS" if survival_half_time_block else "FAIL",
    )

    old_survival_count = text.count("1位に届か")
    ok &= print_result(
        "旧脱落文言 0件",
        "PASS" if old_survival_count == 0 else "FAIL",
        f"{old_survival_count}件",
    )

    undecided_schedule_count = text.count("日時は後日発表")
    ok &= print_result(
        "日時は後日発表 0件",
        "PASS" if undecided_schedule_count == 0 else "FAIL",
        f"{undecided_schedule_count}件",
    )

    schedule_html = section_block(text, "schedule")
    timeline_count_count = schedule_html.count("timeline-count")
    ok &= print_result(
        "#schedule ステッパー集計行 0件",
        "PASS" if timeline_count_count == 0 else "FAIL",
        f"{timeline_count_count}件",
    )

    tally_table_ok = 'class="tally-table"' in schedule_html
    tally_rows = len(re.findall(r'class="[^"]*\btally-row\b', schedule_html))
    tally_widths_ok = bool(re.search(r"--fill\s*:\s*83\.3(?:3)?%", schedule_html)) and "--fill: 87.5%;" in schedule_html
    tally_dates_ok = "8/20" in schedule_html and "8/23" in schedule_html
    ok &= print_result(
        "#schedule 日別集計テーブル",
        "PASS" if tally_table_ok and tally_rows == 7 and tally_dates_ok and tally_widths_ok else "FAIL",
        f"rows={tally_rows}, dates={tally_dates_ok}, widths={tally_widths_ok}",
    )

    schedule_count_times = ["集計 0:00〜20:00", "集計 0:00〜21:00"]
    missing_count_times = [item for item in schedule_count_times if item not in schedule_html]
    ok &= print_result(
        "#schedule 集計締め時間",
        "PASS" if not missing_count_times else "FAIL",
        ", ".join(missing_count_times),
    )

    points_html = section_block(text, "points")
    points_text = visible_text(points_html)
    mission_example_terms = [
        "14時間30分",
        "13時間50分",
        "14人",
        "13人",
        "あと1人",
        "基準 12時間",
        "基準 12人",
        "基準 3人",
    ]
    missing_mission_example_terms = [term for term in mission_example_terms if term not in points_text]
    ok &= print_result(
        "#points ミッション別例示",
        "PASS" if not missing_mission_example_terms else "FAIL",
        ", ".join(missing_mission_example_terms),
    )

    old_threshold_terms = ["10pt以下", "10ptを超え", "14pt"]
    threshold_ok = rendered_text.count("10pt") >= 2 and not any(
        term in rendered_text for term in old_threshold_terms
    )
    ok &= print_result(
        "10pt閾値と旧文言",
        "PASS" if threshold_ok else "FAIL",
        f"10pt={rendered_text.count('10pt')}件",
    )

    old_multipliers = ["×1.5", "×1.4", "×1.3", "×1.1"]
    fixed_quiz_points = ["+8pt", "+6pt", "+4pt", "+2pt"]
    quiz_points_ok = not any(term in rendered_text for term in old_multipliers) and all(
        term in rendered_text for term in fixed_quiz_points
    )
    ok &= print_result(
        "中間クイズ固定pt",
        "PASS" if quiz_points_ok else "FAIL",
    )

    new_point_terms = ["重点ミッション"]
    forbidden_supporter = "サポーターpt" in rendered_text
    missing_new_point_terms = [term for term in new_point_terms if term not in rendered_text]
    ok &= print_result(
        "重点ミッションあり・サポーターpt廃止",
        "PASS" if (not missing_new_point_terms and not forbidden_supporter) else "FAIL",
        ", ".join(missing_new_point_terms) + (" サポーターpt残存" if forbidden_supporter else ""),
    )

    mission_bonus_count = points_html.count('class="mission-bonus"')
    missing_mission_bonus_terms = [
        term for term in ["1位 +3pt", "2位 +2pt", "3位 +1pt"] if term not in points_text
    ]
    ok &= print_result(
        "#points ミッション順位ボーナス",
        "PASS" if mission_bonus_count == 9 and not missing_mission_bonus_terms else "FAIL",
        f"mission-bonus={mission_bonus_count}; " + ", ".join(missing_mission_bonus_terms),
    )

    rules_text = visible_text(rules_html)
    rules_notice_ok = "目標値は変更になる場合があります" in rules_text
    points_notice_ok = "例に使っている数値は変更になる場合があります" in points_text
    ok &= print_result(
        "注記文言更新",
        "PASS" if rules_notice_ok and points_notice_ok else "FAIL",
        f"#rules={rules_notice_ok}, #points={points_notice_ok}",
    )

    score_scales = re.findall(r'<div class="score-scale"[^>]*>(.*?)</div>', points_html, re.S)
    expected_score_labels = [str(i) for i in range(12)] + ["12pt"]
    score_scale_failures = []
    for index, scale_html in enumerate(score_scales, 1):
        labels = re.findall(r'<span class="score-scale-mark"[^>]*>\s*([^<]+?)\s*</span>', scale_html)
        if labels != expected_score_labels:
            score_scale_failures.append(f"{index}: {labels}")
    ok &= print_result(
        "#points スコア目盛り 13個",
        "PASS" if len(score_scales) == 3 and not score_scale_failures else "FAIL",
        f"bars={len(score_scales)}; " + "; ".join(score_scale_failures[:2]),
    )

    score_bars = re.findall(r'<div class="score-bar">(.*?)</div>', points_html, re.S)
    score_tick_failures = []
    for index, bar_html in enumerate(score_bars, 1):
        tick_count = len(re.findall(r'class="score-tick', bar_html))
        major_count = len(re.findall(r'class="score-tick major"', bar_html))
        required_positions = ["8.333%", "16.667%", "25%", "50%", "75%", "91.667%"]
        missing_positions = [position for position in required_positions if position not in bar_html]
        if tick_count != 11 or major_count != 3 or missing_positions:
            score_tick_failures.append(
                f"{index}: ticks={tick_count}, major={major_count}, missing={','.join(missing_positions)}"
            )
    ok &= print_result(
        "#points スコアバー 1ptヘアライン",
        "PASS" if len(score_bars) == 3 and not score_tick_failures else "FAIL",
        f"bars={len(score_bars)}; " + "; ".join(score_tick_failures[:2]),
    )

    score_max_count = text.count("/ 12pt")
    ok &= print_result(
        "/ 12pt 0件",
        "PASS" if score_max_count == 0 else "FAIL",
        f"{score_max_count}件",
    )

    css_failures = css_rule_failures(css)
    ok &= print_result("CSS中央揃え契約", "PASS" if not css_failures else "FAIL", "; ".join(css_failures[:8]))

    section_count_ok = text.count("<section") == text.count("</section>")
    div_count_ok = text.count("<div") == text.count("</div>")
    ok &= print_result(
        "HTML構文簡易検査",
        "PASS" if section_count_ok and div_count_ok else "FAIL",
        f"section {text.count('<section')}/{text.count('</section>')}, div {text.count('<div')}/{text.count('</div>')}",
    )

    if BROWSER is None:
        missing_status = "FAIL" if REQUIRE_BROWSER_TESTS else "SKIP"
        browser_detail = (
            "Chromium系ブラウザなし。EVENT_PAGE_BROWSER、CHROME_PATH、"
            "またはCHROME_BINで実行ファイルを指定できます"
        )
        ok &= print_result("Chromium系ブラウザ発見", missing_status, browser_detail)
        ok &= print_result(
            "実ブラウザ: details・メニュー・ハッシュ・複数展開・390px表示",
            missing_status,
            browser_detail,
        )
        ok &= print_result(
            "実ブラウザ: JavaScript無効でもPV 6チーム×9名",
            missing_status,
            browser_detail,
        )
    else:
        browser_ok, browser_detail = browser_probe()
        if not browser_ok:
            unavailable_status = "FAIL" if REQUIRE_BROWSER_TESTS else "SKIP"
            ok &= print_result("Chromium系ブラウザ発見", unavailable_status, browser_detail)
            ok &= print_result(
                "実ブラウザ: details・メニュー・ハッシュ・複数展開・390px表示",
                unavailable_status,
                browser_detail,
            )
            ok &= print_result(
                "実ブラウザ: JavaScript無効でもPV 6チーム×9名",
                unavailable_status,
                browser_detail,
            )
        else:
            ok &= print_result("Chromium系ブラウザ発見", "PASS", str(BROWSER))
            render_ok, render_html = dump_rendered_dom()
            if not render_ok:
                raise RuntimeError("Chromium DOM dump failed")
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

            runtime_ok, runtime_results = run_runtime_assertions(text)
            expected_runtime_keys = {
                "keyboardNativeDetails",
                "nativeSummaryActivation",
                "openToggleBorderlessWithTextFocus",
                "openSectionFramePresent",
                "multipleToggles",
                "menuOpened",
                "menuNavigation",
                "menuDismissalFocus",
                "hashNavigation",
                "enhancedRosters",
                "mobileType",
                "noHorizontalOverflow",
            }
            runtime_passed = (
                runtime_ok
                and isinstance(runtime_results, dict)
                and expected_runtime_keys.issubset(runtime_results)
                and all(runtime_results[key] for key in expected_runtime_keys)
            )
            ok &= print_result(
                "実ブラウザ: details・メニュー・ハッシュ・複数展開・390px表示",
                "PASS" if runtime_passed else "FAIL",
                str(runtime_results),
            )

            no_js_ok, no_js_html = dump_no_js_dom()
            no_js_pv = section_block(no_js_html, "pv-voice") if no_js_ok else ""
            no_js_rosters = re.findall(
                r'<div class="pv-team-members"[^>]*>(.*?)</div>',
                no_js_pv,
                re.S | re.I,
            )
            no_js_counts = [
                max(
                    len(re.findall(r"<img\b", roster, re.I)),
                    len(re.findall(r"<li\b", roster, re.I)),
                )
                for roster in no_js_rosters
            ]
            ok &= print_result(
                "実ブラウザ: JavaScript無効でもPV 6チーム×9名",
                "PASS" if no_js_counts == [9, 9, 9, 9, 9, 9] else "FAIL",
                str(no_js_counts),
            )

            screenshot_dir = SCRATCHPAD
            try:
                screenshot_dir.mkdir(parents=True, exist_ok=True)
                test_file = screenshot_dir / ".write_test"
                test_file.write_text("ok", encoding="utf-8")
                test_file.unlink()
            except OSError:
                screenshot_dir = HTML_PATH.parent

            for width, height, name in [
                (390, 9000, "render_390.png"),
                (1600, 7200, "render_1600.png"),
            ]:
                status, passed, detail = run_chrome(width, height, screenshot_dir / name)
                ok &= print_result(f"Chromeスクリーンショット {width}px", status, detail)

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
