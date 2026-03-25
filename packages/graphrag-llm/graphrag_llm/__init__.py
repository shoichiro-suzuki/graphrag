# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""GraphRAG LLM Package."""

try:
    import nest_asyncio2
except ImportError:  # pragma: no cover - optional runtime dependency
    try:
        import nest_asyncio as nest_asyncio2
    except ImportError:  # pragma: no cover - optional runtime dependency
        nest_asyncio2 = None

if nest_asyncio2 is not None:
    nest_asyncio2.apply()  # noqa: RUF067
