# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""Command-level LLM cost recording utilities."""

from __future__ import annotations

import json
import logging
import threading
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator, Sequence

from graphrag_llm.model_cost_registry import model_cost_registry

if TYPE_CHECKING:
    from graphrag_llm.types import Metrics

logger = logging.getLogger(__name__)

_current_scope_path: ContextVar[tuple[str, ...]] = ContextVar(
    "graphrag_command_cost_scope_path",
    default=(),
)


@dataclass
class CostTotals:
    """Token and cost totals for a scope."""

    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    total_tokens: int = 0
    input_cost: float = 0.0
    output_cost: float = 0.0
    total_cost: float = 0.0


@dataclass
class CostScopeNode:
    """Nested scope breakdown for a command run."""

    totals: CostTotals = field(default_factory=CostTotals)
    model_breakdown: dict[str, CostTotals] = field(default_factory=dict)
    scope_breakdown: dict[str, "CostScopeNode"] = field(default_factory=dict)


@dataclass
class CommandCostRun:
    """In-memory state for a single command execution."""

    command: str
    output_dir: Path
    metadata: dict[str, Any] = field(default_factory=dict)
    started_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc).astimezone()
    )
    root: CostScopeNode = field(default_factory=CostScopeNode)
    model_ids: set[str] = field(default_factory=set)
    lock: threading.RLock = field(default_factory=threading.RLock)

    @property
    def timestamp(self) -> str:
        """Return the run start timestamp in ISO 8601 format."""
        return self.started_at.isoformat()

    @property
    def output_path(self) -> Path:
        """Return the JSONL output path."""
        return self.output_dir / "command_costs.jsonl"


class CommandCostRecorder:
    """Record command-level LLM usage and cost information.

    This recorder is intentionally process-global for CLI runs. It is not safe
    for concurrent command executions in the same process; if the application
    becomes multi-command or multi-tenant, replace it with an explicit per-run
    recorder instance.
    """

    _active_run: CommandCostRun | None = None
    _active_run_lock: threading.RLock

    def __init__(self) -> None:
        self._active_run_lock = threading.RLock()

    @property
    def active_run(self) -> CommandCostRun | None:
        """Get the active command run, if any."""
        return self._active_run

    def has_active_run(self) -> bool:
        """Return True when a command run is active."""
        return self._active_run is not None

    @contextmanager
    def command_run(
        self,
        *,
        command: str,
        output_dir: str | Path,
        **metadata: Any,
    ) -> Iterator[CommandCostRun]:
        """Record costs for a single command execution."""
        if self._active_run is not None:
            msg = "A command cost run is already active."
            raise RuntimeError(msg)

        run = CommandCostRun(
            command=command,
            output_dir=Path(output_dir).resolve(),
            metadata=metadata,
        )
        run.output_dir.mkdir(parents=True, exist_ok=True)

        self._active_run = run
        scope_token = _current_scope_path.set((command,))
        try:
            yield run
        finally:
            _current_scope_path.reset(scope_token)
            self._active_run = None
            self._flush_run(run)

    @contextmanager
    def scope(self, name: str) -> Iterator[tuple[str, ...]]:
        """Record LLM usage under a nested scope."""
        current = _current_scope_path.get()
        new_scope = (*current, name) if current else (name,)
        token = _current_scope_path.set(new_scope)
        try:
            yield new_scope
        finally:
            _current_scope_path.reset(token)

    def current_scope_path(self) -> tuple[str, ...]:
        """Get the current scope path."""
        return _current_scope_path.get()

    def record_metrics(
        self,
        *,
        model_id: str,
        metrics: "Metrics",
        scope_path: Sequence[str] | None = None,
    ) -> None:
        """Record a single LLM request under the current command scope."""
        run = self._active_run
        if run is None:
            return

        resolved_scope = self._resolve_scope_path(run.command, scope_path)
        totals = self._build_totals(model_id=model_id, metrics=metrics)
        if totals.calls == 0:
            return

        with run.lock:
            run.model_ids.add(model_id)
            node = run.root
            self._accumulate_node(node, model_id=model_id, totals=totals)

            for scope_name in resolved_scope[1:]:
                node = node.scope_breakdown.setdefault(scope_name, CostScopeNode())
                self._accumulate_node(node, model_id=model_id, totals=totals)

    def snapshot(self) -> dict[str, Any]:
        """Return the current command run as a serializable dictionary."""
        run = self._active_run
        if run is None:
            return {}
        with run.lock:
            return self._serialize_run(run)

    def _resolve_scope_path(
        self,
        command: str,
        scope_path: Sequence[str] | None,
    ) -> tuple[str, ...]:
        if scope_path:
            resolved = tuple(scope_path)
        else:
            resolved = _current_scope_path.get()

        if not resolved:
            return (command,)

        if resolved[0] != command:
            return (command, *resolved)

        return resolved

    def _build_totals(self, *, model_id: str, metrics: "Metrics") -> CostTotals:
        prompt_tokens = _to_int(metrics.get("prompt_tokens"))
        completion_tokens = _to_int(metrics.get("completion_tokens"))
        reasoning_tokens = _to_int(metrics.get("reasoning_tokens"))
        total_tokens = prompt_tokens + completion_tokens

        model_costs = model_cost_registry.get_model_costs(model_id)
        if model_costs is not None:
            input_cost = prompt_tokens * model_costs["input_cost_per_token"]
            output_cost = completion_tokens * model_costs["output_cost_per_token"]
            total_cost = input_cost + output_cost
        else:
            input_cost = float(metrics.get("input_cost", 0.0))
            output_cost = float(metrics.get("output_cost", 0.0))
            total_cost = float(metrics.get("total_cost", input_cost + output_cost))

        calls = 1 if total_tokens > 0 or total_cost > 0.0 else 0
        return CostTotals(
            calls=calls,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            reasoning_tokens=reasoning_tokens,
            total_tokens=total_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
        )

    def _accumulate_node(
        self,
        node: CostScopeNode,
        *,
        model_id: str,
        totals: CostTotals,
    ) -> None:
        self._accumulate_totals(node.totals, totals)
        model_totals = node.model_breakdown.setdefault(model_id, CostTotals())
        self._accumulate_totals(model_totals, totals)

    def _accumulate_totals(self, target: CostTotals, source: CostTotals) -> None:
        target.calls += source.calls
        target.prompt_tokens += source.prompt_tokens
        target.completion_tokens += source.completion_tokens
        target.reasoning_tokens += source.reasoning_tokens
        target.total_tokens += source.total_tokens
        target.input_cost += source.input_cost
        target.output_cost += source.output_cost
        target.total_cost += source.total_cost

    def _serialize_run(self, run: CommandCostRun) -> dict[str, Any]:
        model_id = self._summarize_model_id(run.model_ids)
        record: dict[str, Any] = {
            "command": run.command,
            "timestamp": run.timestamp,
            "model_id": model_id,
            **asdict(run.root.totals),
        }
        record.update(run.metadata)
        record["model_breakdown"] = self._serialize_model_breakdown(
            run.root.model_breakdown
        )
        record["scope_breakdown"] = self._serialize_scope_breakdown(
            run.root.scope_breakdown
        )
        return record

    def _serialize_scope_breakdown(
        self, scopes: dict[str, CostScopeNode]
    ) -> dict[str, Any]:
        ordered: dict[str, Any] = {}
        for name in sorted(scopes):
            node = scopes[name]
            ordered[name] = {
                **asdict(node.totals),
                "model_breakdown": self._serialize_model_breakdown(
                    node.model_breakdown
                ),
                "scope_breakdown": self._serialize_scope_breakdown(
                    node.scope_breakdown
                ),
            }
        return ordered

    def _serialize_model_breakdown(
        self, models: dict[str, CostTotals]
    ) -> dict[str, Any]:
        ordered: dict[str, Any] = {}
        for model_id in sorted(models):
            ordered[model_id] = asdict(models[model_id])
        return ordered

    def _summarize_model_id(self, model_ids: set[str]) -> str:
        if not model_ids:
            return ""
        if len(model_ids) == 1:
            return next(iter(model_ids))
        return "multiple"

    def _flush_run(self, run: CommandCostRun) -> None:
        record = self._serialize_run(run)
        try:
            with run.output_path.open("a", encoding="utf-8") as file:
                json.dump(record, file, ensure_ascii=False)
                file.write("\n")
        except OSError:
            logger.warning(
                "Failed to persist command cost record to %s.",
                run.output_path,
                exc_info=True,
            )


def _to_int(value: Any) -> int:
    if value is None:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


command_cost_recorder = CommandCostRecorder()
