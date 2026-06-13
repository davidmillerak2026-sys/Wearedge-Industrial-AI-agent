from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable


SOURCE_TERMS = (
    "CallWearedgeDecisionApi",
    "Language.Python.1",
)
TARGET_TERMS = (
    "System.UpdateDataTable.1",
    "更新数据表.1",
    "UpdateDataTable",
)
REQUIRED_FIELDS = (
    "selected_direction",
    "priority",
    "recommended_action",
    "approval_status",
)
OUTPUT_TERMS = ("output1", "output_1", "out1", "输出1")
INPUT_TERMS = ("input", "input1", "输入", "输入1")
EDGE_KEY_HINTS = (
    "edge",
    "edges",
    "link",
    "links",
    "line",
    "lines",
    "wire",
    "wires",
    "connection",
    "connections",
)
SOURCE_KEY_HINTS = ("source", "src", "from", "start")
TARGET_KEY_HINTS = ("target", "dst", "to", "end")
ID_KEY_HINTS = ("id", "uuid", "key", "name", "displayname", "fbid", "blockid", "nodeid")


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path} is not valid JSON: {exc}") from exc


def iter_nodes(value: Any, path: str = "$") -> Iterable[tuple[str, Any]]:
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from iter_nodes(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from iter_nodes(child, f"{path}[{index}]")


def normalize(value: Any) -> str:
    if isinstance(value, (dict, list)):
        try:
            return json.dumps(value, ensure_ascii=False, sort_keys=True).lower()
        except TypeError:
            return str(value).lower()
    return str(value).lower()


def has_any(text: str, terms: Iterable[str]) -> bool:
    lowered_terms = [term.lower() for term in terms]
    return any(term in text for term in lowered_terms)


def compact(value: Any, limit: int = 500) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def extract_identity_values(objects: list[dict[str, Any]], seed_terms: Iterable[str]) -> set[str]:
    identities = {term for term in seed_terms}
    for obj in objects:
        for key, value in obj.items():
            if isinstance(value, (str, int, float)):
                lowered_key = str(key).lower()
                value_text = str(value)
                if any(hint in lowered_key for hint in ID_KEY_HINTS):
                    identities.add(value_text)
                if has_any(value_text.lower(), seed_terms):
                    identities.add(value_text)
    return {item for item in identities if item}


def find_matching_objects(root: Any, terms: Iterable[str]) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    seen: set[int] = set()
    for _path, value in iter_nodes(root):
        if not isinstance(value, dict):
            continue
        text = normalize(value)
        if has_any(text, terms) and id(value) not in seen:
            matches.append(value)
            seen.add(id(value))
    return matches


def looks_edge_like(path: str, obj: dict[str, Any]) -> bool:
    path_lower = path.lower()
    keys = {str(key).lower() for key in obj}
    if any(hint in path_lower for hint in EDGE_KEY_HINTS):
        return True
    has_source_key = any(any(hint in key for hint in SOURCE_KEY_HINTS) for key in keys)
    has_target_key = any(any(hint in key for hint in TARGET_KEY_HINTS) for key in keys)
    return has_source_key and has_target_key


def find_candidate_connections(
    root: Any,
    source_identities: set[str],
    target_identities: set[str],
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for path, value in iter_nodes(root):
        if not isinstance(value, dict):
            continue
        text = normalize(value)
        if not looks_edge_like(path, value):
            continue
        source_hit = has_any(text, source_identities)
        target_hit = has_any(text, target_identities)
        if not (source_hit and target_hit):
            continue
        output_hit = has_any(text, OUTPUT_TERMS)
        input_hit = has_any(text, INPUT_TERMS)
        data_hint = has_any(text, ("data", "数据", "dashed", "虚线", "port", "ports"))
        candidates.append(
            {
                "path": path,
                "source_hit": source_hit,
                "target_hit": target_hit,
                "output_port_hit": output_hit,
                "input_port_hit": input_hit,
                "data_hint": data_hint,
                "confirmed": output_hit and input_hit,
                "preview": compact(value),
            }
        )
    return candidates


def find_required_fields(root: Any) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {field: [] for field in REQUIRED_FIELDS}
    for path, value in iter_nodes(root):
        if isinstance(value, (dict, list)):
            text = normalize(value)
        else:
            text = str(value).lower()
        for field in REQUIRED_FIELDS:
            if field.lower() in text:
                found[field].append(path)
    return {field: paths[:8] for field, paths in found.items() if paths}


def analyze_workflow(root: Any) -> dict[str, Any]:
    source_objects = find_matching_objects(root, SOURCE_TERMS)
    target_objects = find_matching_objects(root, TARGET_TERMS)
    source_identities = extract_identity_values(source_objects, SOURCE_TERMS)
    target_identities = extract_identity_values(target_objects, TARGET_TERMS)
    candidates = find_candidate_connections(root, source_identities, target_identities)
    required_fields = find_required_fields(root)
    confirmed = [candidate for candidate in candidates if candidate["confirmed"]]

    return {
        "ok": True,
        "source_block_found": bool(source_objects),
        "target_block_found": bool(target_objects),
        "source_identity_values": sorted(source_identities),
        "target_identity_values": sorted(target_identities),
        "required_fields_found": sorted(required_fields),
        "required_fields_missing": [field for field in REQUIRED_FIELDS if field not in required_fields],
        "candidate_connection_count": len(candidates),
        "confirmed_python_output_to_update_table": bool(confirmed),
        "candidate_connections": candidates[:20],
        "boundary": (
            "This is a local JSON structure analysis only. It does not call Gongyi Mofang, "
            "does not modify WFC, and does not prove live execution by itself."
        ),
    }


def render_text(result: dict[str, Any]) -> str:
    status = "PASS" if result["confirmed_python_output_to_update_table"] else "REVIEW"
    lines = [
        f"status={status}",
        f"source_block_found={result['source_block_found']}",
        f"target_block_found={result['target_block_found']}",
        f"required_fields_found={', '.join(result['required_fields_found']) or 'none'}",
        f"required_fields_missing={', '.join(result['required_fields_missing']) or 'none'}",
        f"candidate_connection_count={result['candidate_connection_count']}",
        f"confirmed_python_output_to_update_table={result['confirmed_python_output_to_update_table']}",
    ]
    for candidate in result["candidate_connections"][:5]:
        lines.append(
            "candidate "
            f"path={candidate['path']} "
            f"confirmed={candidate['confirmed']} "
            f"output={candidate['output_port_hit']} "
            f"input={candidate['input_port_hit']}"
        )
    lines.append(f"boundary={result['boundary']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Analyze a local Gongyi Mofang WFC workflow JSON for Wearedge data-table bindings."
    )
    parser.add_argument("workflow_json", type=Path, help="Path to a local workflow.json or exported WFC project JSON.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument(
        "--require-confirmed",
        action="store_true",
        help="Exit non-zero unless Python output to UpdateDataTable is confirmed.",
    )
    args = parser.parse_args(argv)

    try:
        result = analyze_workflow(load_json(args.workflow_json))
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else render_text(result))
    if args.require_confirmed and not result["confirmed_python_output_to_update_table"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
