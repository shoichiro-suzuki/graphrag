# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""Summarize GraphRAG command cost history from a JSONL ledger."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


@dataclass
class Totals:
    """Token and cost totals."""

    runs: int = 0
    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    total_tokens: int = 0
    input_cost: float = 0.0
    output_cost: float = 0.0
    total_cost: float = 0.0

    def add_record(self, record: dict[str, Any]) -> None:
        self.runs += 1
        self.calls += _to_int(record.get("calls"))
        self.prompt_tokens += _to_int(record.get("prompt_tokens"))
        self.completion_tokens += _to_int(record.get("completion_tokens"))
        self.reasoning_tokens += _to_int(record.get("reasoning_tokens"))
        self.total_tokens += _to_int(record.get("total_tokens"))
        self.input_cost += _to_float(record.get("input_cost"))
        self.output_cost += _to_float(record.get("output_cost"))
        self.total_cost += _to_float(record.get("total_cost"))

    def add_totals(self, other: "Totals") -> None:
        self.runs += other.runs
        self.calls += other.calls
        self.prompt_tokens += other.prompt_tokens
        self.completion_tokens += other.completion_tokens
        self.reasoning_tokens += other.reasoning_tokens
        self.total_tokens += other.total_tokens
        self.input_cost += other.input_cost
        self.output_cost += other.output_cost
        self.total_cost += other.total_cost


@dataclass
class ScopeNode:
    """Recursive scope breakdown."""

    totals: Totals = field(default_factory=Totals)
    model_breakdown: dict[str, Totals] = field(default_factory=dict)
    scope_breakdown: dict[str, "ScopeNode"] = field(default_factory=dict)


@dataclass
class CommandSummary:
    """Aggregated data for a command."""

    totals: Totals = field(default_factory=Totals)
    model_breakdown: dict[str, Totals] = field(default_factory=dict)
    scope_breakdown: dict[str, ScopeNode] = field(default_factory=dict)
    runs: list[dict[str, Any]] = field(default_factory=list)


def load_records(path: Path) -> list[dict[str, Any]]:
    """Load JSONL records from a command cost ledger."""
    records: list[dict[str, Any]] = []
    if not path.exists():
        return records

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        records.append(json.loads(line))
    return records


def summarize_records(records: Iterable[dict[str, Any]]) -> dict[str, CommandSummary]:
    """Group records by command and aggregate totals."""
    grouped: dict[str, CommandSummary] = defaultdict(CommandSummary)
    for record in records:
        command = str(record.get("command") or "unknown")
        summary = grouped[command]
        summary.totals.add_record(record)
        summary.runs.append(
            {
                "timestamp": record.get("timestamp", ""),
                "model_id": record.get("model_id", ""),
                "calls": _to_int(record.get("calls")),
                "prompt_tokens": _to_int(record.get("prompt_tokens")),
                "completion_tokens": _to_int(record.get("completion_tokens")),
                "total_cost": _to_float(record.get("total_cost")),
            }
        )

        _merge_model_breakdown(summary.model_breakdown, record.get("model_breakdown", {}))
        _merge_scope_breakdown(summary.scope_breakdown, record.get("scope_breakdown", {}))
    return grouped


def render_summary(summary: dict[str, CommandSummary]) -> str:
    """Render a human-readable markdown summary."""
    lines: list[str] = ["# Command Cost Summary"]
    for command in sorted(summary):
        command_summary = summary[command]
        lines.append("")
        lines.append(f"## {command}")
        lines.append("")
        lines.extend(_render_totals_table(command_summary.totals))
        if command_summary.runs:
            lines.append("")
            lines.append("### Runs")
            lines.append("")
            lines.extend(
                _render_table(
                    headers=["timestamp", "model_id", "calls", "prompt_tokens", "completion_tokens", "total_cost"],
                    rows=[
                        [
                            run["timestamp"],
                            run["model_id"],
                            str(run["calls"]),
                            _format_int(run["prompt_tokens"]),
                            _format_int(run["completion_tokens"]),
                            _format_float(run["total_cost"]),
                        ]
                        for run in command_summary.runs
                    ],
                )
            )
        if command_summary.model_breakdown:
            lines.append("")
            lines.append("### Models")
            lines.append("")
            lines.extend(
                _render_table(
                    headers=[
                        "model_id",
                        "runs",
                        "calls",
                        "prompt_tokens",
                        "completion_tokens",
                        "output_cost",
                        "total_cost",
                    ],
                    rows=[
                        [
                            model_id,
                            str(totals.runs),
                            str(totals.calls),
                            _format_int(totals.prompt_tokens),
                            _format_int(totals.completion_tokens),
                            _format_float(totals.output_cost),
                            _format_float(totals.total_cost),
                        ]
                        for model_id, totals in sorted(command_summary.model_breakdown.items())
                    ],
                )
            )
        if command_summary.scope_breakdown:
            lines.append("")
            lines.append("### Scopes")
            lines.append("")
            lines.extend(_render_scope_section(command_summary.scope_breakdown))
    return "\n".join(lines).rstrip() + "\n"


def _render_scope_section(scopes: dict[str, ScopeNode], indent: int = 0) -> list[str]:
    lines: list[str] = []
    pad = "  " * indent
    for scope_name in sorted(scopes):
        scope = scopes[scope_name]
        lines.append(f"{pad}- {scope_name}:")
        lines.append(f"{pad}  - runs: {scope.totals.runs}")
        lines.append(f"{pad}  - calls: {scope.totals.calls}")
        lines.append(f"{pad}  - prompt_tokens: {_format_int(scope.totals.prompt_tokens)}")
        lines.append(f"{pad}  - completion_tokens: {_format_int(scope.totals.completion_tokens)}")
        lines.append(f"{pad}  - output_cost: {_format_float(scope.totals.output_cost)}")
        lines.append(f"{pad}  - total_cost: {_format_float(scope.totals.total_cost)}")
        if scope.model_breakdown:
            lines.append(f"{pad}  - models:")
            for model_id, totals in sorted(scope.model_breakdown.items()):
                lines.append(
                    f"{pad}    - {model_id}: calls={totals.calls}, prompt_tokens={_format_int(totals.prompt_tokens)}, "
                    f"completion_tokens={_format_int(totals.completion_tokens)}, total_cost={_format_float(totals.total_cost)}"
                )
        if scope.scope_breakdown:
            lines.extend(_render_scope_section(scope.scope_breakdown, indent=indent + 1))
    return lines


def _render_totals_table(totals: Totals) -> list[str]:
    return _render_table(
        headers=["metric", "value"],
        rows=[
            ["runs", str(totals.runs)],
            ["calls", str(totals.calls)],
            ["prompt_tokens", _format_int(totals.prompt_tokens)],
            ["completion_tokens", _format_int(totals.completion_tokens)],
            ["reasoning_tokens", _format_int(totals.reasoning_tokens)],
            ["total_tokens", _format_int(totals.total_tokens)],
            ["input_cost", _format_float(totals.input_cost)],
            ["output_cost", _format_float(totals.output_cost)],
            ["total_cost", _format_float(totals.total_cost)],
        ],
    )


def _render_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    def fmt_row(row: list[str]) -> str:
        return "| " + " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)) + " |"

    lines = [fmt_row(headers)]
    lines.append("| " + " | ".join("-" * width for width in widths) + " |")
    lines.extend(fmt_row(row) for row in rows)
    return lines


def _merge_model_breakdown(target: dict[str, Totals], source: dict[str, Any]) -> None:
    for model_id, data in source.items():
        totals = target.setdefault(model_id, Totals())
        totals.runs += 1
        totals.calls += _to_int(data.get("calls"))
        totals.prompt_tokens += _to_int(data.get("prompt_tokens"))
        totals.completion_tokens += _to_int(data.get("completion_tokens"))
        totals.reasoning_tokens += _to_int(data.get("reasoning_tokens"))
        totals.total_tokens += _to_int(data.get("total_tokens"))
        totals.input_cost += _to_float(data.get("input_cost"))
        totals.output_cost += _to_float(data.get("output_cost"))
        totals.total_cost += _to_float(data.get("total_cost"))


def _merge_scope_breakdown(target: dict[str, ScopeNode], source: dict[str, Any]) -> None:
    for scope_name, data in source.items():
        node = target.setdefault(scope_name, ScopeNode())
        node.totals.runs += 1
        node.totals.calls += _to_int(data.get("calls"))
        node.totals.prompt_tokens += _to_int(data.get("prompt_tokens"))
        node.totals.completion_tokens += _to_int(data.get("completion_tokens"))
        node.totals.reasoning_tokens += _to_int(data.get("reasoning_tokens"))
        node.totals.total_tokens += _to_int(data.get("total_tokens"))
        node.totals.input_cost += _to_float(data.get("input_cost"))
        node.totals.output_cost += _to_float(data.get("output_cost"))
        node.totals.total_cost += _to_float(data.get("total_cost"))
        _merge_model_breakdown(node.model_breakdown, data.get("model_breakdown", {}))
        _merge_scope_breakdown(node.scope_breakdown, data.get("scope_breakdown", {}))


def _format_int(value: int) -> str:
    return f"{value:,}"


def _format_float(value: float) -> str:
    return f"{value:.6f}"


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "ledger",
        nargs="?",
        default=Path("graphrag_quickstart") / "output" / "command_costs.jsonl",
        type=Path,
        help="Path to command_costs.jsonl.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Optional path to write the rendered summary.",
    )
    args = parser.parse_args()

    records = load_records(args.ledger)
    summary = summarize_records(records)
    rendered = render_summary(summary)

    if args.output is not None:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
