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
    assert source.count(".team-leader {") == 1, "運営リーダーのCSSが重複しています"
    assert "運営リーダーの割り当ては後日発表します" not in source

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
