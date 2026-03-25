# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""Tests for the default metrics processor."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest


def _load_module(module_name: str, module_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _install_graphrag_llm_stubs() -> None:
    graphrag_pkg = types.ModuleType("graphrag_llm")
    graphrag_pkg.__path__ = []  # type: ignore[attr-defined]
    metrics_pkg = types.ModuleType("graphrag_llm.metrics")
    metrics_pkg.__path__ = []  # type: ignore[attr-defined]
    metrics_processor_mod = types.ModuleType("graphrag_llm.metrics.metrics_processor")

    class MetricsProcessor:
        pass

    metrics_processor_mod.MetricsProcessor = MetricsProcessor

    model_cost_registry_mod = types.ModuleType("graphrag_llm.model_cost_registry")

    class _Registry:
        def get_model_costs(self, model: str):
            if model in {"gpt-5.4-mini", "openai/gpt-5.4-mini"}:
                return {
                    "input_cost_per_token": 0.750 / 1_000_000,
                    "output_cost_per_token": 4.500 / 1_000_000,
                }
            return None

    model_cost_registry_mod.model_cost_registry = _Registry()

    types_mod = types.ModuleType("graphrag_llm.types")

    class LLMCompletionResponse:
        pass

    class LLMEmbeddingResponse:
        pass

    types_mod.LLMCompletionResponse = LLMCompletionResponse
    types_mod.LLMEmbeddingResponse = LLMEmbeddingResponse

    sys.modules["graphrag_llm"] = graphrag_pkg
    sys.modules["graphrag_llm.metrics"] = metrics_pkg
    sys.modules["graphrag_llm.metrics.metrics_processor"] = metrics_processor_mod
    sys.modules["graphrag_llm.model_cost_registry"] = model_cost_registry_mod
    sys.modules["graphrag_llm.types"] = types_mod


def test_chat_completion_reasoning_tokens_are_counted_as_output() -> None:
    """Reasoning tokens should be counted on the output side."""
    _install_graphrag_llm_stubs()
    module = _load_module(
        "test_default_metrics_processor_module",
        Path(__file__).resolve().parents[3]
        / "packages"
        / "graphrag-llm"
        / "graphrag_llm"
        / "metrics"
        / "default_metrics_processor.py",
    )

    processor = module.DefaultMetricsProcessor()
    metrics: dict[str, float] = {}
    model_config = SimpleNamespace(model_provider="openai", model="gpt-5.4-mini")
    response = SimpleNamespace(
        usage=SimpleNamespace(
            prompt_tokens=100,
            completion_tokens=20,
            completion_tokens_details=SimpleNamespace(reasoning_tokens=5),
        )
    )

    processor._process_lm_chat_completion(  # noqa: SLF001
        model_config=model_config,
        metrics=metrics,
        input_args={},
        response=response,
    )

    assert metrics["responses_with_tokens"] == 1
    assert metrics["prompt_tokens"] == 100
    assert metrics["completion_tokens"] == 20
    assert metrics["reasoning_tokens"] == 5
    assert metrics["total_tokens"] == 120
    assert metrics["responses_with_cost"] == 1
    assert metrics["input_cost"] == pytest.approx(0.000075)
    assert metrics["output_cost"] == pytest.approx(0.00009)
    assert metrics["total_cost"] == pytest.approx(0.000165)
