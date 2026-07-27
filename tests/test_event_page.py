#!/usr/bin/env python3
"""Self-check for the 大運動会2026 event page."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve()
HTML_PATH = (SCRIPT_PATH.parent / ".." / "イベント概要_大運動会2026.html").resolve()
SCRATCHPAD = Path(
    "/private/tmp/claude-501/-Users-kh-Documents-work-ob/"
    "bb78e0a7-a76e-437b-954a-05c7adc6dd90/scratchpad"
)
CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
CAST_ONLY_PV_EXPECTED = True
CAST_ONLY_PV_START = "<!-- CAST-ONLY:PV-VOICE START"
CAST_ONLY_PV_END = "<!-- CAST-ONLY:PV-VOICE END -->"
CAST_ONLY_PV_PATTERN = re.compile(
    r"<!-- CAST-ONLY:PV-VOICE START.*?CAST-ONLY:PV-VOICE END -->",
    re.S,
)
REQUIRED_IDS = [
    "about",
    "teams",
    "rules",
    "points",
    "half-time",
    "survival",
    "support",
    "schedule",
    "prize",
    "faq",
]


def strip_data_uris(text: str) -> str:
    return re.sub(r"data:image/[^\"']+", "data:image/STRIPPED", text)


def style_block(text: str) -> str:
    match = re.search(r"<style>\s*(.*?)\s*</style>", text, re.S | re.I)
    return match.group(1) if match else ""


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
    left_allowed = {"#points .rule-table td:nth-child(3)", ".timeline-item-text"}
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


def chrome_probe() -> tuple[bool, str]:
    try:
        result = subprocess.run(
            [str(CHROME), "--headless", "--disable-gpu", "--dump-dom", "about:blank"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except Exception as exc:  # noqa: BLE001
        return False, f"Chrome起動失敗: {exc}"
    if result.returncode != 0:
        message = (result.stderr or result.stdout).strip()
        if not message:
            message = f"Chrome headless returned {result.returncode}"
        return False, message[:500]
    return True, "ok"


def run_chrome(width: int, height: int, output: Path) -> tuple[str, bool, str]:
    cmd = [
        str(CHROME),
        "--headless",
        "--disable-gpu",
        f"--screenshot={output}",
        f"--window-size={width},{height}",
        HTML_PATH.as_uri(),
    ]
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=60)
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

    text = HTML_PATH.read_text(encoding="utf-8")
    css = style_block(text)
    rendered_text = visible_text(strip_data_uris(text))
    ok = True

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

    no_script = len(re.findall(r"<script", text, re.I)) == 0
    public_text = CAST_ONLY_PV_PATTERN.sub("", strip_data_uris(text))
    no_url = len(re.findall(r"https?://", public_text, re.I)) == 0
    ok &= print_result("<script と http(s) URL 0件", "PASS" if no_script and no_url else "FAIL")

    pv_matches = CAST_ONLY_PV_PATTERN.findall(text)
    pv_block = next((m for m in pv_matches if 'id="pv-voice"' in m), "")
    pv_nav_block = next((m for m in pv_matches if 'href="#pv-voice"' in m), "")
    pv_form_url = "https://forms.gle/SMoTKsQ16n4mtEuE9"
    pv_email = "h_sawa@virtualidol.info"
    pv_team_shouts = [
        "よっしゃ行くぞ〜！",
        "最高のイベントにしよう！",
        "みんな、お祭りだー！！",
        "全力で楽しもう〜！",
        "ぜったい勝つぞ〜！",
        "準備はいいか〜！？",
    ]
    if CAST_ONLY_PV_EXPECTED:
        pv_failures = []
        if text.count(CAST_ONLY_PV_START) != 2:
            pv_failures.append(f"START={text.count(CAST_ONLY_PV_START)}（本体＋ナビの2ペア想定）")
        if text.count(CAST_ONLY_PV_END) != 2:
            pv_failures.append(f"END={text.count(CAST_ONLY_PV_END)}（本体＋ナビの2ペア想定）")
        if 'id="pv-voice"' not in pv_block:
            pv_failures.append("pv-voiceなし")
        if 'href="#pv-voice"' not in pv_nav_block:
            pv_failures.append("ナビのPV収録リンクなし（CAST-ONLY内）")
        if pv_block.count(pv_form_url) != 1 or text.count(pv_form_url) != 1:
            pv_failures.append(f"フォームURL={pv_block.count(pv_form_url)}/{text.count(pv_form_url)}")
        for phrase in ["8/1", "13:00", "有志", *pv_team_shouts]:
            if phrase not in pv_block:
                pv_failures.append(f"{phrase}なし")
        for heading in ["録音方法", "提出方法"]:
            if f'<h3 class="pv-section-heading">{heading}</h3>' not in pv_block:
                pv_failures.append(f"見出し{heading}なし")
        for route in ["ROUTE A", "ROUTE B"]:
            if route not in pv_block:
                pv_failures.append(f"{route}なし")
        for phrase in ["セリフは4つ", "収録は強制ではありません", "＋α（余裕があればぜひ！）"]:
            if phrase not in pv_block:
                pv_failures.append(f"{phrase}なし")
        if "1人5つ" in pv_block:
            pv_failures.append("旧文言「1人5つ」が残存")
        if pv_email not in pv_block or text.count(pv_email) != 1:
            pv_failures.append(f"メール={pv_block.count(pv_email)}/{text.count(pv_email)}")
    else:
        pv_forbidden = [
            CAST_ONLY_PV_START,
            CAST_ONLY_PV_END,
            'id="pv-voice"',
            'href="#pv-voice"',
            pv_form_url,
            pv_email,
        ]
        pv_failures = [
            f"{item}={text.count(item)}"
            for item in pv_forbidden
            if text.count(item) != 0
        ]
    ok &= print_result(
        "PV収録セクション（キャスト向け・公開前削除）",
        "PASS" if not pv_failures else "FAIL",
        ", ".join(pv_failures),
    )

    prize_block = section_block(text, "prize")
    prize_needed = ["自遊空間", "掲出予定", "調整中", "優勝チーム", "準優勝チーム", "パネル設置", "ブースPOP", "集合立ち絵ポスター"]
    prize_missing = [term for term in prize_needed if term not in prize_block]
    ok &= print_result(
        "特典: 自遊空間掲出（優勝/準優勝の内訳）",
        "PASS" if not prize_missing else "FAIL",
        ", ".join(prize_missing),
    )

    css_compact = re.sub(r"\s+", " ", css)
    auto_phrase_ok = "word-break: auto-phrase" in css_compact
    pretty_ok = "text-wrap: pretty" in css_compact
    ok &= print_result(
        "文節折り返しCSS",
        "PASS" if auto_phrase_ok and pretty_ok else "FAIL",
        f"auto-phrase={auto_phrase_ok}, pretty={pretty_ok}",
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

    expected_members = [
        "言乃葩和", "魔法少女ぴょん", "夜狩うる", "7_ko", "境内リカ", "まいくま", "ブルーローズアイス", "冬月シオン", "わたあめ",
        "玉木瑶", "あまタクシー", "紫月ほたる", "目黒れる", "山岸紫苑", "Nico", "スイ・カウハ", "紗衣", "オイエ・ナイスガイ",
        "千里香", "赤絲こゆび", "旅乃とき", "かずさ", "ミラ・エトワール", "沙耶", "おめがまる", "焦赤緋色", "ルカ・ミント",
        "蔦ヰ田リウ", "はちみつ", "プルミエール・エトワール", "微々", "雪織みみ", "水野ゆか", "西那てまり", "月詠くるみ", "ゆうり",
        "こぐま もる", "白猫にゃる", "小向なのか", "MUZU", "桜咲はるね", "白浪しおん", "めぐるん", "黒川水晶", "シン・クラーク",
        "黒柴えいら", "超絶はおちー", "蒼羽れいな", "三毒ローパ", "呑田くれい", "奈夢夛", "六華ミル", "海鈴なぎ", "木ノ崎叶和",
    ]
    teams_html = section_block(text, "teams")
    actual_members = re.findall(r'<div class="member-photo"[^>]*>(?:<img [^>]*alt="([^"]+)"|<svg)', teams_html)
    actual_members = [m for m in actual_members if m]
    leader_count = teams_html.count("運営リーダー：")
    ok &= print_result(
        "チームごとの運営リーダー行 6件",
        "PASS" if leader_count == 6 else "FAIL",
        f"{leader_count}件",
    )
    ok &= print_result(
        "チームメンバー表記・並び順",
        "PASS" if actual_members == expected_members else "FAIL",
        f"{len(actual_members)}名",
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

    if not CHROME.exists():
        ok &= print_result("Chromeヘッドレスレンダリング", "SKIP", f"Chromeなし: {CHROME}")
    else:
        chrome_ok, chrome_detail = chrome_probe()
        if not chrome_ok:
            ok &= print_result("Chromeヘッドレスレンダリング", "SKIP", chrome_detail)
        else:
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
