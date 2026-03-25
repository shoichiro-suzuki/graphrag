# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""Tests for the GraphRAG profile bootstrapper."""

from __future__ import annotations

import importlib.util
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


def test_copy_profile_creates_env_and_copies_files() -> None:
    """The bootstrapper should copy the template profile and materialize .env."""
    module = _load_module(
        "test_create_graphrag_profile_module",
        Path(__file__).resolve().parents[3] / "scripts" / "create_graphrag_profile.py",
    )

    temp_root = Path.cwd() / "_tmp_create_graphrag_profile_test"
    shutil.rmtree(temp_root, ignore_errors=True)
    temp_root.mkdir(parents=True, exist_ok=True)
    try:
        template_dir = temp_root / "_template"
        target_dir = temp_root / "legal_profile"
        (template_dir / "prompts").mkdir(parents=True, exist_ok=True)
        (template_dir / "cache").mkdir(parents=True, exist_ok=True)
        (template_dir / "logs").mkdir(parents=True, exist_ok=True)
        (template_dir / "output").mkdir(parents=True, exist_ok=True)
        (template_dir / "prompts" / "extract_graph.txt").write_text(
            "prompt body",
            encoding="utf-8",
        )
        (template_dir / "settings.yaml").write_text(
            "input_storage:\n  base_dir: \"../../input\"\n",
            encoding="utf-8",
        )
        (template_dir / ".env.example").write_text(
            "GRAPHRAG_API_KEY=<API_KEY>",
            encoding="utf-8",
        )

        module.copy_profile(template_dir, target_dir, profiles_root=temp_root)

        assert (target_dir / "settings.yaml").is_file()
        assert (target_dir / "prompts" / "extract_graph.txt").read_text(encoding="utf-8") == "prompt body"
        assert (target_dir / ".env.example").is_file()
        assert (target_dir / ".env").read_text(encoding="utf-8") == "GRAPHRAG_API_KEY=<API_KEY>"
        assert (target_dir / "cache").is_dir()
        assert (target_dir / "logs").is_dir()
        assert (target_dir / "output").is_dir()
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)
