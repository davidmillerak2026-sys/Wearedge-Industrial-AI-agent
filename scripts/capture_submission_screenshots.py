from __future__ import annotations

import argparse
import html
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "submission-assets" / "screenshots"
DEFAULT_RENDER_DIR = REPO_ROOT / "submission-assets" / "rendered-pages"


@dataclass(frozen=True)
class CaptureSpec:
    name: str
    title: str
    source_path: Path | None
    kind: str
    output_name: str


DOCUMENT_SPECS = (
    CaptureSpec("readme", "Repository README", REPO_ROOT / "README.md", "markdown", "01-local-readme.png"),
    CaptureSpec(
        "offline-eval-report",
        "Competition Offline Evaluation Report",
        REPO_ROOT / "docs" / "competition-offline-eval-report.md",
        "markdown",
        "03-offline-eval-report.png",
    ),
    CaptureSpec(
        "wfc-payload",
        "Workflow Canvas PoC Payload",
        REPO_ROOT / "workflows" / "wearedge_wfc_poc_payload.json",
        "json",
        "05-wfc-payload.png",
    ),
    CaptureSpec(
        "dashboard-mock",
        "Workflow Canvas Decision Dashboard Mock",
        REPO_ROOT / "docs" / "submission" / "dashboard-mock.html",
        "html",
        "06-dashboard-mock.png",
    ),
    CaptureSpec(
        "api-schema",
        "Workflow Canvas API Schema",
        REPO_ROOT / "docs" / "workflow-canvas-api-schema.md",
        "markdown",
        "07-api-schema.png",
    ),
    CaptureSpec(
        "registration-fields",
        "Registration Fields",
        REPO_ROOT / "docs" / "submission" / "registration-fields.md",
        "markdown",
        "10-registration-fields.png",
    ),
    CaptureSpec(
        "co-creation-onepager",
        "Siemens Xcelerator Co-Creation One-Pager",
        REPO_ROOT / "docs" / "siemens-xcelerator-co-creation-onepager.md",
        "markdown",
        "11-co-creation-onepager.png",
    ),
)


def capture_submission_screenshots(
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    render_dir: Path = DEFAULT_RENDER_DIR,
    browser_path: Path | None = None,
    python_executable: str = sys.executable,
    include_pytest: bool = True,
) -> dict[str, Any]:
    browser = find_browser(browser_path)
    if browser is None:
        return {
            "ok": False,
            "error": "No Chrome or Edge executable found.",
            "screenshots": [],
            "commands": [],
        }

    output_dir.mkdir(parents=True, exist_ok=True)
    render_dir.mkdir(parents=True, exist_ok=True)

    pages = _build_document_pages(render_dir)
    commands = _run_evidence_commands(python_executable, include_pytest)
    pages.extend(_build_command_pages(render_dir, commands))

    screenshots = []
    for page in pages:
        screenshots.append(_capture_page(browser, page["html_path"], output_dir / page["output_name"]))

    index = {
        "ok": all(item["ok"] for item in screenshots) and all(command["ok"] for command in commands),
        "browser": str(browser),
        "output_dir": str(output_dir.resolve()),
        "render_dir": str(render_dir.resolve()),
        "screenshots": screenshots,
        "commands": commands,
    }
    (output_dir / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return index


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Capture submission screenshot evidence pages.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--render-dir", type=Path, default=DEFAULT_RENDER_DIR)
    parser.add_argument("--browser", type=Path, default=None)
    parser.add_argument("--python", default=sys.executable, help="Python executable for evidence commands.")
    parser.add_argument("--skip-pytest", action="store_true", help="Skip the full pytest screenshot command.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable capture output.")
    args = parser.parse_args(argv)

    result = capture_submission_screenshots(
        output_dir=args.output_dir,
        render_dir=args.render_dir,
        browser_path=args.browser,
        python_executable=args.python,
        include_pytest=not args.skip_pytest,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"ok={result['ok']}")
        print(f"screenshot_count={len(result.get('screenshots', []))}")
        print(f"command_count={len(result.get('commands', []))}")
        print(f"output_dir={result.get('output_dir')}")
        if result.get("error"):
            print(f"error={result['error']}")
    return 0 if result["ok"] else 1


def find_browser(explicit: Path | None = None) -> Path | None:
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


def _build_document_pages(render_dir: Path) -> list[dict[str, Any]]:
    pages = []
    for spec in DOCUMENT_SPECS:
        assert spec.source_path is not None
        if spec.kind == "html":
            pages.append(
                {
                    "name": spec.name,
                    "title": spec.title,
                    "html_path": spec.source_path.resolve(),
                    "output_name": spec.output_name,
                }
            )
            continue

        raw_text = spec.source_path.read_text(encoding="utf-8")
        if spec.kind == "json":
            content = _render_code(_format_json(raw_text), "json")
        else:
            content = render_markdown(raw_text)
        html_path = render_dir / f"{spec.name}.html"
        html_path.write_text(_render_page(spec.title, content, source=str(spec.source_path.relative_to(REPO_ROOT))), encoding="utf-8")
        pages.append(
            {
                "name": spec.name,
                "title": spec.title,
                "html_path": html_path.resolve(),
                "output_name": spec.output_name,
            }
        )
    return pages


def _run_evidence_commands(python_executable: str, include_pytest: bool) -> list[dict[str, Any]]:
    commands = [
        (
            "competition-eval-cli",
            "Competition Offline Eval CLI",
            [python_executable, "scripts/run_competition_eval.py"],
            120,
            "02-competition-eval-cli.png",
        ),
        (
            "wfc-smoke-cli",
            "Workflow Canvas Smoke CLI",
            [python_executable, "scripts/smoke_workflow_canvas_decision.py"],
            120,
            "04-wfc-smoke.png",
        ),
        (
            "submission-verifier-cli",
            "Submission Package Verifier CLI",
            [python_executable, "scripts/verify_submission_package.py", "--write-manifest"],
            120,
            "08-submission-verifier.png",
        ),
    ]
    if include_pytest:
        commands.append(
            (
                "pytest-cli",
                "Full Pytest Output",
                [
                    python_executable,
                    "-m",
                    "pytest",
                    "--basetemp",
                    r"C:\tmp\wearedge-industrial-ai-agent-pytest",
                    "tests",
                    "industrial-rag-agent/tests",
                ],
                240,
                "09-pytest-output.png",
            )
        )

    results = []
    for name, title, command, timeout, output_name in commands:
        results.append(_run_command(name, title, command, timeout, output_name))
    return results


def _build_command_pages(render_dir: Path, commands: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pages = []
    for command in commands:
        body = _render_terminal(command)
        html_path = render_dir / f"{command['name']}.html"
        html_path.write_text(_render_page(command["title"], body, source="command output"), encoding="utf-8")
        pages.append(
            {
                "name": command["name"],
                "title": command["title"],
                "html_path": html_path.resolve(),
                "output_name": command["output_name"],
            }
        )
    return pages


def _run_command(name: str, title: str, command: list[str], timeout: int, output_name: str) -> dict[str, Any]:
    try:
        completed = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, timeout=timeout)
        stdout = completed.stdout.strip()
        stderr = completed.stderr.strip()
        return {
            "name": name,
            "title": title,
            "command": _display_command(command),
            "returncode": completed.returncode,
            "ok": completed.returncode == 0,
            "stdout": stdout,
            "stderr": stderr,
            "output_name": output_name,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "name": name,
            "title": title,
            "command": _display_command(command),
            "returncode": None,
            "ok": False,
            "stdout": (exc.stdout or "").strip() if isinstance(exc.stdout, str) else "",
            "stderr": f"Timed out after {timeout}s",
            "output_name": output_name,
        }


def _capture_page(browser: Path, html_path: Path, output_path: Path) -> dict[str, Any]:
    output_path = output_path.resolve()
    if output_path.exists():
        output_path.unlink()
    command = [
        str(browser),
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--window-size=1440,1200",
        f"--screenshot={output_path}",
        html_path.resolve().as_uri(),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=60)
    exists = output_path.exists() and output_path.stat().st_size > 0
    return {
        "ok": completed.returncode == 0 and exists,
        "html": str(html_path),
        "screenshot": str(output_path),
        "bytes": output_path.stat().st_size if exists else 0,
        "returncode": completed.returncode,
        "stderr": completed.stderr.strip(),
    }


def render_markdown(text: str) -> str:
    lines = text.splitlines()
    rendered: list[str] = []
    i = 0
    in_code = False
    code_lines: list[str] = []
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_code:
                rendered.append(_render_code("\n".join(code_lines), "text"))
                code_lines = []
                in_code = False
            else:
                in_code = True
            i += 1
            continue
        if in_code:
            code_lines.append(line)
            i += 1
            continue
        if not stripped:
            i += 1
            continue
        if stripped.startswith("|") and "|" in stripped[1:]:
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            rendered.append(_render_table(table_lines))
            continue
        heading = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if heading:
            level = min(len(heading.group(1)), 4)
            rendered.append(f"<h{level}>{_inline(heading.group(2))}</h{level}>")
            i += 1
            continue
        if stripped.startswith(("- ", "* ")):
            items = []
            while i < len(lines) and lines[i].strip().startswith(("- ", "* ")):
                items.append(f"<li>{_inline(lines[i].strip()[2:])}</li>")
                i += 1
            rendered.append("<ul>" + "".join(items) + "</ul>")
            continue
        rendered.append(f"<p>{_inline(stripped)}</p>")
        i += 1
    if code_lines:
        rendered.append(_render_code("\n".join(code_lines), "text"))
    return "\n".join(rendered)


def _render_page(title: str, body: str, source: str) -> str:
    return f"""<!doctype html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{html.escape(title)}</title>
  <style>
    :root {{ color-scheme: light; --ink: #17202a; --muted: #586574; --line: #d8e0e8; --blue: #155a9c; --bg: #eef3f7; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: \"Segoe UI\", Arial, sans-serif; color: var(--ink); background: var(--bg); }}
    header {{ padding: 22px 30px; background: #102a43; color: #fff; }}
    h1 {{ margin: 0 0 6px; font-size: 27px; line-height: 1.15; }}
    .source {{ color: #c9d6e2; font-size: 13px; }}
    main {{ width: min(1180px, calc(100vw - 40px)); margin: 22px auto 40px; background: #fff; border: 1px solid var(--line); border-radius: 8px; padding: 24px 28px; box-shadow: 0 1px 2px rgba(16, 42, 67, .06); }}
    h2 {{ margin: 24px 0 10px; font-size: 21px; color: #0f3557; }}
    h3 {{ margin: 20px 0 8px; font-size: 17px; color: #133f65; }}
    h4 {{ margin: 16px 0 8px; font-size: 15px; color: #25364a; }}
    p {{ margin: 8px 0; line-height: 1.55; }}
    ul {{ margin: 8px 0 14px 22px; padding: 0; }}
    li {{ margin: 5px 0; line-height: 1.45; }}
    table {{ width: 100%; border-collapse: collapse; margin: 12px 0 18px; font-size: 13px; }}
    th, td {{ border: 1px solid var(--line); padding: 8px 9px; text-align: left; vertical-align: top; }}
    th {{ background: #f2f6fa; color: #26384d; }}
    code {{ background: #eef5fb; color: #0f4778; border: 1px solid #d2e3f2; border-radius: 4px; padding: 1px 4px; }}
    pre {{ margin: 12px 0; padding: 15px; background: #0b1724; color: #eef6ff; border-radius: 8px; overflow: hidden; white-space: pre-wrap; word-break: break-word; line-height: 1.42; font-size: 12px; }}
    .terminal {{ background: #07111d; }}
    .status-ok {{ color: #16845c; font-weight: 700; }}
    .status-fail {{ color: #b42318; font-weight: 700; }}
  </style>
</head>
<body>
  <header>
    <h1>{html.escape(title)}</h1>
    <div class=\"source\">Source: {html.escape(source)}</div>
  </header>
  <main>{body}</main>
</body>
</html>
"""


def _render_terminal(command: dict[str, Any]) -> str:
    status_class = "status-ok" if command["ok"] else "status-fail"
    status_text = "PASS" if command["ok"] else "REVIEW"
    output = "\n".join(
        part
        for part in (
            f"> {command['command']}",
            "",
            command.get("stdout", ""),
            command.get("stderr", ""),
        )
        if part is not None
    ).strip()
    return (
        f"<p>Status: <span class=\"{status_class}\">{status_text}</span> "
        f"(return code: {html.escape(str(command.get('returncode')))}).</p>"
        f"{_render_code(output, 'terminal')}"
    )


def _render_table(lines: list[str]) -> str:
    rows = []
    for line in lines:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", cell or "") for cell in cells):
            continue
        rows.append(cells)
    if not rows:
        return ""
    header, *body = rows
    head_html = "".join(f"<th>{_inline(cell)}</th>" for cell in header)
    body_html = "".join("<tr>" + "".join(f"<td>{_inline(cell)}</td>" for cell in row) + "</tr>" for row in body)
    return f"<table><thead><tr>{head_html}</tr></thead><tbody>{body_html}</tbody></table>"


def _inline(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    return escaped


def _render_code(text: str, class_name: str) -> str:
    return f"<pre class=\"{html.escape(class_name)}\">{html.escape(text)}</pre>"


def _format_json(raw_text: str) -> str:
    return json.dumps(json.loads(raw_text), ensure_ascii=False, indent=2)


def _display_command(command: list[str]) -> str:
    display = ["python" if Path(command[0]).name.lower().startswith("python") else command[0], *command[1:]]
    return " ".join(_quote_if_needed(part) for part in display)


def _quote_if_needed(part: str) -> str:
    if " " in part or "\t" in part:
        return f'"{part}"'
    return part


if __name__ == "__main__":
    raise SystemExit(main())
