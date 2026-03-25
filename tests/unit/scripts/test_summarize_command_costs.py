# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""Tests for the command cost summarizer script."""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path


def _load_module(module_name: str, module_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_summarize_command_costs_groups_by_command_and_scope() -> None:
    """The summarizer should aggregate per command and keep model/scope breakdowns."""
    module = _load_module(
        "test_summarize_command_costs_module",
        Path(__file__).resolve().parents[3] / "scripts" / "summarize_command_costs.py",
    )
    output_dir = Path.cwd() / "_tmp_summarize_command_costs_test"
    shutil.rmtree(output_dir, ignore_errors=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        ledger_path = output_dir / "command_costs.jsonl"
        ledger_path.write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "command": "graphrag index",
                            "timestamp": "2026-03-25T13:41:31.715338+09:00",
                            "calls": 2,
                            "prompt_tokens": 10,
                            "completion_tokens": 20,
                            "reasoning_tokens": 0,
                            "total_tokens": 30,
                            "input_cost": 0.01,
                            "output_cost": 0.02,
                            "total_cost": 0.03,
                            "model_breakdown": {
                                "azure/gpt-5-nano": {
                                    "calls": 2,
                                    "prompt_tokens": 10,
                                    "completion_tokens": 20,
                                    "reasoning_tokens": 0,
                                    "total_tokens": 30,
                                    "input_cost": 0.01,
                                    "output_cost": 0.02,
                                    "total_cost": 0.03,
                                }
                            },
                            "scope_breakdown": {
                                "extract_graph": {
                                    "calls": 2,
                                    "prompt_tokens": 10,
                                    "completion_tokens": 20,
                                    "reasoning_tokens": 0,
                                    "total_tokens": 30,
                                    "input_cost": 0.01,
                                    "output_cost": 0.02,
                                    "total_cost": 0.03,
                                    "model_breakdown": {
                                        "azure/gpt-5-nano": {
                                            "calls": 2,
                                            "prompt_tokens": 10,
                                            "completion_tokens": 20,
                                            "reasoning_tokens": 0,
                                            "total_tokens": 30,
                                            "input_cost": 0.01,
                                            "output_cost": 0.02,
                                            "total_cost": 0.03,
                                        }
                                    },
                                    "scope_breakdown": {},
                                }
                            },
                        }
                    ),
                    json.dumps(
                        {
                            "command": "graphrag query",
                            "timestamp": "2026-03-25T14:01:31.715338+09:00",
                            "calls": 1,
                            "prompt_tokens": 5,
                            "completion_tokens": 7,
                            "reasoning_tokens": 0,
                            "total_tokens": 12,
                            "input_cost": 0.005,
                            "output_cost": 0.007,
                            "total_cost": 0.012,
                            "model_breakdown": {
                                "azure/gpt-5.4-mini": {
                                    "calls": 1,
                                    "prompt_tokens": 5,
                                    "completion_tokens": 7,
                                    "reasoning_tokens": 0,
                                    "total_tokens": 12,
                                    "input_cost": 0.005,
                                    "output_cost": 0.007,
                                    "total_cost": 0.012,
                                }
                            },
                            "scope_breakdown": {},
                        }
                    ),
                ]
            ),
            encoding="utf-8",
        )

        records = module.load_records(ledger_path)
        summary = module.summarize_records(records)

        assert set(summary) == {"graphrag index", "graphrag query"}
        assert summary["graphrag index"].totals.calls == 2
        assert summary["graphrag index"].totals.total_cost == 0.03
        assert summary["graphrag index"].model_breakdown["azure/gpt-5-nano"].total_cost == 0.03
        assert summary["graphrag index"].scope_breakdown["extract_graph"].totals.total_cost == 0.03
        assert summary["graphrag query"].totals.prompt_tokens == 5

        rendered = module.render_summary(summary)
        assert "graphrag index" in rendered
        assert "graphrag query" in rendered
        assert "extract_graph" in rendered
        assert "azure/gpt-5-nano" in rendered
    finally:
        shutil.rmtree(output_dir, ignore_errors=True)
