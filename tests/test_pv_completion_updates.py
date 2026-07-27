#!/usr/bin/env python3
"""Focused browser check for the PV completion, footer, and mobile rule updates."""

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


PROJECT_ROOT = Path(__file__).resolve().parent.parent
HTML_PATH = PROJECT_ROOT / "index.html"


def discover_browser() -> Path | None:
    candidates: list[str | None] = [
        os.environ.get("EVENT_PAGE_BROWSER"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        shutil.which("google-chrome"),
        shutil.which("chromium"),
    ]
    candidates.extend(
        str(path)
        for path in sorted(
            (Path.home() / "Library/Caches/ms-playwright").glob(
                "chromium_headless_shell-*/chrome-headless-shell-mac*/chrome-headless-shell"
            ),
            reverse=True,
        )
    )
    for value in candidates:
        if not value:
            continue
        candidate = Path(value)
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    return None


def run_focused_browser_check() -> tuple[bool, dict[str, bool] | str]:
    browser = discover_browser()
    if browser is None:
        return False, "Chromium系ブラウザが見つかりません"

    harness = r"""
  <output id="pv-update-test-results" hidden></output>
  <script>
    (() => {
      const output = document.getElementById("pv-update-test-results");
      const checks = [
        ...document.querySelectorAll("#pv-voice .pv-completion-check"),
      ];
      const url = new URL(window.location.href);
      const phase = url.searchParams.get("phase");

      if (phase !== "restored" && checks.length === 5) {
        checks[0].click();
        url.searchParams.set("phase", "restored");
        window.location.replace(url.href);
        return;
      }

      const footer = document.querySelector(".footer-note");
      const footerText = footer?.innerText.replace(/\s+/g, " ").trim() ?? "";
      const drop = document.querySelector(".flow-branch.drop");
      const groups = [...(drop?.children ?? [])];
      const firstCard = checks[0]?.closest(".pv-say-card");
      const firstCardStyle = firstCard ? getComputedStyle(firstCard) : null;
      const lines = checks.map((check) => check.dataset.pvLine);
      const completionControlLayouts = checks.map((check) => {
        const label = check.closest(".pv-completion-label");
        const head = check.closest(".pv-say-head");
        const labelRect = label?.getBoundingClientRect();
        const headRect = head?.getBoundingClientRect();
        return {
          inputOnly:
            label?.children.length === 1
            && label?.textContent.trim() === "",
          atRight:
            getComputedStyle(label).position === "absolute"
            && Math.abs(headRect.right - labelRect.right) <= 16,
        };
      });
      const results = {
        fiveCompletionChecks:
          checks.length === 5
          && JSON.stringify(lines) === JSON.stringify(["1", "2", "3", "4", "5"]),
        completionControlIsSecondary:
          completionControlLayouts.every((layout) =>
            layout.inputOnly && layout.atRight
          ),
        completionTurnsGreen:
          checks[0]?.checked === true
          && firstCard?.classList.contains("is-complete") === true
          && firstCardStyle?.borderTopColor === "rgb(43, 122, 76)",
        completionPersists:
          phase === "restored"
          && checks[0]?.checked === true
          && checks.slice(1).every((check) => !check.checked),
        footerCopy:
          footerText ===
            "本ページは参加キャスト向けの案内です。外部への共有はしないでください。 " +
            "一部調整中の項目がありますので、最新情報は運営からの連絡をご確認ください。適宜本ページも更新します。",
        mobileRuleGroups:
          groups.length === 2
          && groups[0].textContent.trim() === "10pt未満 → 脱落"
          && groups[1].textContent.trim() === "（中間発表に不参加）"
          && [...drop.childNodes].every((node) =>
            node.nodeType === Node.ELEMENT_NODE
            || node.textContent.trim() === ""
          )
          && groups.every((group) =>
            getComputedStyle(group).whiteSpace === "nowrap"
            && group.getClientRects().length === 1
          ),
        noHorizontalOverflow:
          document.documentElement.scrollWidth <= window.innerWidth,
      };
      output.textContent = JSON.stringify(results);
    })();
  </script>
"""

    source = HTML_PATH.read_text(encoding="utf-8")
    runtime_source = source.replace("</body>", f"{harness}\n</body>")

    with tempfile.TemporaryDirectory(prefix="pv-completion-test-") as temp_dir:
        temp_root = Path(temp_dir)
        runtime_path = temp_root / "runtime.html"
        runtime_path.write_text(runtime_source, encoding="utf-8")
        result = subprocess.run(
            [
                str(browser),
                "--headless",
                "--no-sandbox",
                "--disable-gpu",
                "--disable-dev-shm-usage",
                f"--user-data-dir={temp_root / 'profile'}",
                "--window-size=320,700",
                "--virtual-time-budget=4000",
                "--dump-dom",
                runtime_path.as_uri(),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )

    if result.returncode != 0:
        return False, (result.stderr or result.stdout).strip()[:500]

    match = re.search(
        r'<output\b(?=[^>]*\bid="pv-update-test-results")[^>]*>(.*?)</output>',
        result.stdout,
        re.S,
    )
    if not match:
        return False, "ブラウザから検証結果を取得できませんでした"

    try:
        results = json.loads(html.unescape(match.group(1)))
    except json.JSONDecodeError as exc:
        return False, f"検証結果が不正です: {exc}"
    return all(results.values()), results


def main() -> int:
    ok, detail = run_focused_browser_check()
    status = "PASS" if ok else "FAIL"
    print(f"{status}: PV完了チェック・フッター・スマホ脱落表示")
    if isinstance(detail, dict):
        for name, passed in detail.items():
            print(f"  {'PASS' if passed else 'FAIL'}: {name}")
    elif detail:
        print(f"  {detail}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
