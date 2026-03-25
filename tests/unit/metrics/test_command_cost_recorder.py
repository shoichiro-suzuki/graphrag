# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""Tests for command-level cost recording."""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import types
from pathlib import Path

import pytest


def _load_module(module_name: str, module_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _install_model_cost_registry_stub() -> None:
    graphrag_pkg = types.ModuleType("graphrag_llm")
    graphrag_pkg.__path__ = []  # type: ignore[attr-defined]
    registry_mod = types.ModuleType("graphrag_llm.model_cost_registry")

    class _Registry:
        def get_model_costs(self, model: str):
            if model in {"gpt-5.4-mini", "openai/gpt-5.4-mini"}:
                return {
                    "input_cost_per_token": 0.750 / 1_000_000,
                    "output_cost_per_token": 4.500 / 1_000_000,
                }
            return None

    registry_mod.model_cost_registry = _Registry()
    sys.modules["graphrag_llm"] = graphrag_pkg
    sys.modules["graphrag_llm.model_cost_registry"] = registry_mod


def test_command_cost_recorder_writes_scope_and_model_breakdowns(
) -> None:
    """Recorder should aggregate per command, scope, and model."""
    _install_model_cost_registry_stub()
    module = _load_module(
        "test_command_cost_recorder_module",
        Path(__file__).resolve().parents[3]
        / "packages"
        / "graphrag-llm"
        / "graphrag_llm"
        / "metrics"
        / "command_cost_recorder.py",
    )
    recorder = module.command_cost_recorder
    output_dir = Path.cwd() / "_tmp_command_cost_recorder_test"
    shutil.rmtree(output_dir, ignore_errors=True)
    try:
        with recorder.command_run(
            command="graphrag update",
            output_dir=output_dir,
            method="drift",
        ):
            with recorder.scope("create_entities"):
                recorder.record_metrics(
                    model_id="openai/gpt-5.4-mini",
                    metrics={
                        "prompt_tokens": 100,
                        "completion_tokens": 20,
                        "reasoning_tokens": 5,
                    },
                )

            with recorder.scope("finalize_graph"):
                recorder.record_metrics(
                    model_id="custom/model",
                    metrics={
                        "prompt_tokens": 10,
                        "completion_tokens": 4,
                        "reasoning_tokens": 1,
                        "input_cost": 0.1,
                        "output_cost": 0.2,
                        "total_cost": 0.3,
                    },
                )

        record_path = output_dir / "command_costs.jsonl"
        record = json.loads(record_path.read_text(encoding="utf-8").strip())

        assert record["command"] == "graphrag update"
        assert record["model_id"] == "multiple"
        assert record["prompt_tokens"] == 110
        assert record["completion_tokens"] == 24
        assert record["reasoning_tokens"] == 6
        assert record["total_tokens"] == 134
        assert record["input_cost"] == pytest.approx(0.100075)
        assert record["output_cost"] == pytest.approx(0.20009)
        assert record["total_cost"] == pytest.approx(0.300165)
        assert record["method"] == "drift"

        assert record["scope_breakdown"]["create_entities"]["prompt_tokens"] == 100
        assert record["scope_breakdown"]["create_entities"]["model_breakdown"][
            "openai/gpt-5.4-mini"
        ]["total_cost"] == pytest.approx(0.000165)
        assert record["scope_breakdown"]["finalize_graph"]["model_breakdown"][
            "custom/model"
        ]["total_cost"] == pytest.approx(0.3)
    finally:
        shutil.rmtree(output_dir, ignore_errors=True)
