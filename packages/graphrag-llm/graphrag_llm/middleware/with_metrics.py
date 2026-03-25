# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Metrics middleware to process metrics using a MetricsProcessor."""

import logging
import time
from collections.abc import AsyncIterator, Iterator
from typing import TYPE_CHECKING, Any

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from graphrag_llm.config import ModelConfig
    from graphrag_llm.metrics import MetricsProcessor
    from graphrag_llm.types import (
        AsyncLLMFunction,
        LLMFunction,
        Metrics,
    )


def _extract_completion_usage(chunk: Any) -> tuple[int, int, int] | None:
    """Extract prompt, completion, and reasoning token counts from a streamed chunk."""
    usage = getattr(chunk, "usage", None)
    if usage is None:
        return None

    prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
    completion_tokens = getattr(usage, "completion_tokens", 0) or 0
    reasoning_tokens = 0
    completion_tokens_details = getattr(usage, "completion_tokens_details", None)
    if completion_tokens_details is not None:
        reasoning_tokens = getattr(completion_tokens_details, "reasoning_tokens", 0) or 0

    return prompt_tokens, completion_tokens, reasoning_tokens


def with_metrics(
    *,
    model_config: "ModelConfig",
    sync_middleware: "LLMFunction",
    async_middleware: "AsyncLLMFunction",
    metrics_processor: "MetricsProcessor",
) -> tuple[
    "LLMFunction",
    "AsyncLLMFunction",
]:
    """Wrap model functions with metrics middleware.

    Args
    ----
        model_config: ModelConfig
            The model configuration.
        sync_middleware: LLMFunction
            The synchronous model function to wrap.
            Either a completion function or an embedding function.
        async_middleware: AsyncLLMFunction
            The asynchronous model function to wrap.
            Either a completion function or an embedding function.
        metrics_processor: MetricsProcessor
            The metrics processor to use.

    Returns
    -------
        tuple[LLMFunction, AsyncLLMFunction]
            The synchronous and asynchronous model functions wrapped with metrics middleware.

    """

    def _metrics_middleware(
        **kwargs: Any,
    ):
        metrics: Metrics | None = kwargs.get("metrics")
        start_time = time.time()
        response = sync_middleware(**kwargs)
        end_time = time.time()

        if metrics is not None:
            if kwargs.get("stream") and isinstance(response, Iterator):
                def _wrapped_stream() -> Iterator[Any]:
                    last_usage: tuple[int, int, int] | None = None
                    try:
                        for chunk in response:
                            usage = _extract_completion_usage(chunk)
                            if usage is not None:
                                last_usage = usage
                            yield chunk
                    finally:
                        metrics["compute_duration_seconds"] = time.time() - start_time
                        metrics["streaming_responses"] = 1
                        if last_usage is not None:
                            try:
                                metrics_processor.process_completion_usage(
                                    model_config=model_config,
                                    metrics=metrics,
                                    prompt_tokens=last_usage[0],
                                    completion_tokens=last_usage[1],
                                    reasoning_tokens=last_usage[2],
                                )
                            except Exception:  # noqa: BLE001
                                logger.warning(
                                    "Failed to process streamed completion usage.",
                                    exc_info=True,
                                )

                return _wrapped_stream()

            metrics_processor.process_metrics(
                model_config=model_config,
                metrics=metrics,
                input_args=kwargs,
                response=response,
            )
            if kwargs.get("stream"):
                metrics["compute_duration_seconds"] = 0
                metrics["streaming_responses"] = 1
            else:
                metrics["compute_duration_seconds"] = end_time - start_time
                metrics["streaming_responses"] = 0
        return response

    async def _metrics_middleware_async(
        **kwargs: Any,
    ):
        metrics: Metrics | None = kwargs.get("metrics")

        start_time = time.time()
        response = await async_middleware(**kwargs)
        end_time = time.time()

        if metrics is not None:
            if kwargs.get("stream") and isinstance(response, AsyncIterator):
                async def _wrapped_stream() -> AsyncIterator[Any]:
                    last_usage: tuple[int, int, int] | None = None
                    try:
                        async for chunk in response:
                            usage = _extract_completion_usage(chunk)
                            if usage is not None:
                                last_usage = usage
                            yield chunk
                    finally:
                        metrics["compute_duration_seconds"] = time.time() - start_time
                        metrics["streaming_responses"] = 1
                        if last_usage is not None:
                            try:
                                metrics_processor.process_completion_usage(
                                    model_config=model_config,
                                    metrics=metrics,
                                    prompt_tokens=last_usage[0],
                                    completion_tokens=last_usage[1],
                                    reasoning_tokens=last_usage[2],
                                )
                            except Exception:  # noqa: BLE001
                                logger.warning(
                                    "Failed to process streamed completion usage.",
                                    exc_info=True,
                                )

                return _wrapped_stream()

            metrics_processor.process_metrics(
                model_config=model_config,
                metrics=metrics,
                input_args=kwargs,
                response=response,
            )
            if kwargs.get("stream"):
                metrics["compute_duration_seconds"] = 0
                metrics["streaming_responses"] = 1
            else:
                metrics["compute_duration_seconds"] = end_time - start_time
                metrics["streaming_responses"] = 0
        return response

    return (_metrics_middleware, _metrics_middleware_async)  # type: ignore
