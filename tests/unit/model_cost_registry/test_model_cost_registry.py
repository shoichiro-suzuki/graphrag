# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""Tests for the model cost registry."""

from __future__ import annotations

import importlib.util
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


def _install_litellm_stub(model_cost: dict[str, dict[str, float]] | None = None) -> None:
    litellm_stub = types.ModuleType("litellm")
    litellm_stub.model_cost = model_cost or {}
    sys.modules["litellm"] = litellm_stub

    typing_extensions_stub = types.ModuleType("typing_extensions")
    typing_extensions_stub.Self = object
    sys.modules["typing_extensions"] = typing_extensions_stub


def test_gpt_54_mini_costs_are_registered() -> None:
    """gpt-5.4-mini should resolve with the expected costs."""
    _install_litellm_stub()
    module = _load_module(
        "test_model_cost_registry_module",
        Path(__file__).resolve().parents[3]
        / "packages"
        / "graphrag-llm"
        / "graphrag_llm"
        / "model_cost_registry"
        / "model_cost_registry.py",
    )

    costs = module.model_cost_registry.get_model_costs("gpt-5.4-mini")
    assert costs is not None
    assert costs["input_cost_per_token"] == pytest.approx(0.750 / 1_000_000)
    assert costs["output_cost_per_token"] == pytest.approx(4.500 / 1_000_000)


def test_prefixed_model_ids_fall_back_to_bare_model_name() -> None:
    """Provider-prefixed model ids should resolve via the bare model name."""
    _install_litellm_stub()
    module = _load_module(
        "test_model_cost_registry_module_prefixed",
        Path(__file__).resolve().parents[3]
        / "packages"
        / "graphrag-llm"
        / "graphrag_llm"
        / "model_cost_registry"
        / "model_cost_registry.py",
    )

    bare_costs = module.model_cost_registry.get_model_costs("gpt-5.4-mini")
    prefixed_costs = module.model_cost_registry.get_model_costs("openai/gpt-5.4-mini")

    assert prefixed_costs == bare_costs


def test_gpt_5_nano_costs_are_registered() -> None:
    """gpt-5-nano should resolve with the expected costs."""
    _install_litellm_stub(
        model_cost={
            "gpt-5-nano": {
                "input_cost_per_token": 0.050 / 1_000_000,
                "output_cost_per_token": 0.400 / 1_000_000,
            }
        }
    )
    module = _load_module(
        "test_model_cost_registry_module_nano",
        Path(__file__).resolve().parents[3]
        / "packages"
        / "graphrag-llm"
        / "graphrag_llm"
        / "model_cost_registry"
        / "model_cost_registry.py",
    )

    costs = module.model_cost_registry.get_model_costs("azure/gpt-5-nano")
    assert costs is not None
    assert costs["input_cost_per_token"] == pytest.approx(0.050 / 1_000_000)
    assert costs["output_cost_per_token"] == pytest.approx(0.400 / 1_000_000)
