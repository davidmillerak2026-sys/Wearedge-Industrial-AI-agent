from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jetson.agent_poc_validation import format_agent_poc_markdown, run_agent_golden_validations, run_agent_poc_validations


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the five WearEdge M400 agent POC scenarios.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of markdown.")
    parser.add_argument("--golden", action="store_true", help="Run the expanded golden scenario matrix.")
    args = parser.parse_args()

    results = run_agent_golden_validations() if args.golden else run_agent_poc_validations()
    label = "golden scenario" if args.golden else "five-agent POC"
    passed = sum(1 for result in results if result.passed)
    payload = {
        "ok": passed == len(results),
        "passed": passed,
        "total": len(results),
        "results": [result.as_dict() for result in results],
    }

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"WearEdge {label} validation: {passed}/{len(results)} passed")
        print()
        print(format_agent_poc_markdown(results))
        failed = [result for result in results if not result.passed]
        if failed:
            print()
            for result in failed:
                print(f"{result.mode} failures:")
                for failure in result.failures:
                    print(f"- {failure}")

    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
