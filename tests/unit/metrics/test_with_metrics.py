# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""Tests for metrics middleware."""

from __future__ import annotations

import asyncio
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace


def _load_module(module_name: str, module_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class _RecordingMetricsProcessor:
    def __init__(self) -> None:
        self.process_metrics_calls: list[dict[str, object]] = []
        self.process_completion_usage_calls: list[dict[str, object]] = []

    def process_metrics(self, **kwargs: object) -> None:
        self.process_metrics_calls.append(kwargs)

    def process_completion_usage(self, **kwargs: object) -> None:
        self.process_completion_usage_calls.append(kwargs)
        metrics = kwargs["metrics"]
        assert isinstance(metrics, dict)
        metrics["completion_usage_recorded"] = 1


def test_async_stream_records_completion_usage_on_final_chunk() -> None:
    """Streaming completion usage should be recorded when the iterator is consumed."""
    module = _load_module(
        "test_with_metrics_module",
        Path(__file__).resolve().parents[3]
        / "packages"
        / "graphrag-llm"
        / "graphrag_llm"
        / "middleware"
        / "with_metrics.py",
    )

    metrics: dict[str, float] = {}
    processor = _RecordingMetricsProcessor()
    model_config = SimpleNamespace(model_provider="azure", model="gpt-5.4-mini")

    async def async_middleware(**kwargs: object):
        assert kwargs["stream"] is True

        async def _stream():
            yield SimpleNamespace(
                usage=None,
                choices=[SimpleNamespace(delta=SimpleNamespace(content="hello"))],
            )
            yield SimpleNamespace(
                usage=SimpleNamespace(
                    prompt_tokens=42,
                    completion_tokens=100,
                    completion_tokens_details=SimpleNamespace(reasoning_tokens=7),
                ),
                choices=[SimpleNamespace(delta=SimpleNamespace(content=" world"))],
            )

        return _stream()

    _, wrapped_async = module.with_metrics(
        model_config=model_config,
        sync_middleware=lambda **kwargs: None,
        async_middleware=async_middleware,
        metrics_processor=processor,
    )

    async def _consume() -> list[object]:
        response = await wrapped_async(stream=True, metrics=metrics)
        chunks: list[object] = []
        async for chunk in response:
            chunks.append(chunk)
        return chunks

    chunks = asyncio.run(_consume())

    assert len(chunks) == 2
    assert processor.process_metrics_calls == []
    assert len(processor.process_completion_usage_calls) == 1
    call = processor.process_completion_usage_calls[0]
    assert call["prompt_tokens"] == 42
    assert call["completion_tokens"] == 100
    assert call["reasoning_tokens"] == 7
    assert metrics["completion_usage_recorded"] == 1
    assert metrics["streaming_responses"] == 1
    assert metrics["compute_duration_seconds"] >= 0
