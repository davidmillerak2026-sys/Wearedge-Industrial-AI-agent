from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HTML = REPO_ROOT / "docs" / "submission" / "dashboard-mock.html"
DEFAULT_OUTPUT = REPO_ROOT / "submission-assets" / "screenshots" / "06-dashboard-mock.png"


def capture_dashboard_mock(html_path: Path, output_path: Path, browser_path: Path | None = None) -> dict[str, Any]:
    browser = _find_browser(browser_path)
    if browser is None:
        return {
            "ok": False,
            "error": "No Chrome or Edge executable found. Open docs/submission/dashboard-mock.html manually.",
        }

    html_path = html_path.resolve()
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    command = [
        str(browser),
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--window-size=1440,1000",
        f"--screenshot={output_path}",
        html_path.as_uri(),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=60)
    exists = output_path.exists() and output_path.stat().st_size > 0
    return {
        "ok": completed.returncode == 0 and exists,
        "browser": str(browser),
        "html": str(html_path),
        "screenshot": str(output_path),
        "bytes": output_path.stat().st_size if exists else 0,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Capture the submission dashboard mock screenshot.")
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--browser", type=Path, default=None, help="Optional explicit Chrome or Edge executable.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable output.")
    args = parser.parse_args(argv)

    result = capture_dashboard_mock(args.html, args.output, args.browser)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"ok={result['ok']}")
        if result.get("screenshot"):
            print(f"screenshot={result['screenshot']}")
            print(f"bytes={result['bytes']}")
        if result.get("error"):
            print(f"error={result['error']}")
    return 0 if result["ok"] else 1


def _find_browser(explicit: Path | None) -> Path | None:
    candidates: list[Path] = []
    if explicit is not None:
        candidates.append(explicit)
    env_browser = os.environ.get("CHROME_BIN") or os.environ.get("EDGE_BIN")
    if env_browser:
        candidates.append(Path(env_browser))
    candidates.extend(
        [
            Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
            Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
            Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
            Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        ]
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


if __name__ == "__main__":
    raise SystemExit(main())
