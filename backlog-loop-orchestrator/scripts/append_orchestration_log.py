#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Append a structured entry to a markdown orchestration log.",
    )
    parser.add_argument("--log", required=True, help="Path to the markdown log file")
    parser.add_argument(
        "--iteration",
        required=True,
        help="Iteration identifier such as 001 or 014",
    )
    parser.add_argument(
        "--event",
        required=True,
        help="Stable event name such as slice-selected or committed",
    )
    parser.add_argument(
        "--slice",
        required=True,
        help="Short description of the current bounded slice",
    )
    parser.add_argument(
        "--summary",
        required=True,
        help="Short factual summary for this log entry",
    )
    parser.add_argument(
        "--field",
        action="append",
        default=[],
        help="Extra key=value field to append. Repeat as needed.",
    )
    parser.add_argument(
        "--title",
        default="Orchestration Log",
        help="Header to use when creating a new log file",
    )
    return parser.parse_args()


def iso_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def ensure_header(log_path: Path, title: str) -> None:
    if log_path.exists():
        return
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(f"# {title}\n", encoding="utf-8")


def parse_field(raw_field: str) -> tuple[str, str]:
    if "=" not in raw_field:
        raise SystemExit(f"Invalid --field value: {raw_field!r}. Use key=value.")
    key, value = raw_field.split("=", 1)
    key = key.strip()
    value = value.strip()
    if not key:
        raise SystemExit(f"Invalid --field value: {raw_field!r}. Key is empty.")
    return key, value


def main() -> None:
    args = parse_args()
    log_path = Path(args.log).expanduser()
    ensure_header(log_path, args.title)

    lines = [
        "",
        f"## Iteration {args.iteration} {args.event}",
        f"- timestamp: {iso_now()}",
        f"- iteration: {args.iteration}",
        f"- event: {args.event}",
        f"- slice: {args.slice}",
        f"- summary: {args.summary}",
    ]

    for raw_field in args.field:
        key, value = parse_field(raw_field)
        lines.append(f"- {key}: {value}")

    with log_path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
