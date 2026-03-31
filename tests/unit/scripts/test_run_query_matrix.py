# Copyright (c) 2026 Microsoft Corporation.
# Licensed under the MIT License

"""Tests for the query matrix runner script."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
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


def test_load_query_set_and_validate_entries() -> None:
    module = _load_module(
        "test_run_query_matrix_module_loader",
        Path(__file__).resolve().parents[3] / "scripts" / "run_query_matrix.py",
    )
    temp_root = Path.cwd() / "_tmp_run_query_matrix_test"
    shutil.rmtree(temp_root, ignore_errors=True)
    temp_root.mkdir(parents=True, exist_ok=True)
    try:
        query_set_path = temp_root / "sample.yaml"
        query_set_path.write_text(
            """
name: sample
description: 比較用
defaults:
  community_level: 2
  response_type: Multiple Paragraphs
  streaming: false
queries:
  - id: theme
    method: global
    prompt: What are the themes?
  - id: detail
    method: local
    prompt: Who is Scrooge?
""".strip(),
            encoding="utf-8",
        )

        query_set = module.load_query_set(query_set_path)
        assert query_set["name"] == "sample"
        assert len(query_set["queries"]) == 2
        assert query_set["queries"][0].method == "global"
        assert query_set["queries"][1].prompt == "Who is Scrooge?"

        invalid_cases = [
            (
                """
queries:
  - id: duplicated
    method: global
    prompt: Q1
  - id: duplicated
    method: local
    prompt: Q2
""",
                "重複",
            ),
            (
                """
queries:
  - id: missing_method
    prompt: Q
""",
                "method",
            ),
            (
                """
queries:
  - id: empty_prompt
    method: basic
    prompt: "   "
""",
                "prompt",
            ),
            (
                """
queries:
  - id: unknown_method
    method: other
    prompt: Q
""",
                "不正",
            ),
        ]
        for index, (content, expected) in enumerate(invalid_cases, start=1):
            path = temp_root / f"invalid_{index}.yaml"
            path.write_text(content.strip(), encoding="utf-8")
            try:
                module.load_query_set(path)
                raise AssertionError("ValueError が発生するはずです")
            except ValueError as exc:
                assert expected in str(exc)
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def test_build_query_command_uses_expected_flags() -> None:
    module = _load_module(
        "test_run_query_matrix_module_command",
        Path(__file__).resolve().parents[3] / "scripts" / "run_query_matrix.py",
    )
    command = module.build_query_command(
        module.QuerySpec(
            id="theme",
            prompt="What are the themes?",
            method="global",
        ),
        {"community_level": 3, "response_type": "Single Sentence", "streaming": True},
    )

    assert command[:4] == [sys.executable, "-m", "graphrag", "query"]
    assert "What are the themes?" in command
    assert "--method" in command
    assert "global" in command
    assert "--community-level" in command
    assert "3" in command
    assert "--response-type" in command
    assert "Single Sentence" in command
    assert "--streaming" in command


def test_run_profile_queries_records_artifacts_and_costs() -> None:
    module = _load_module(
        "test_run_query_matrix_module_worker",
        Path(__file__).resolve().parents[3] / "scripts" / "run_query_matrix.py",
    )
    temp_root = Path.cwd() / "_tmp_run_query_matrix_worker_test"
    shutil.rmtree(temp_root, ignore_errors=True)
    temp_root.mkdir(parents=True, exist_ok=True)
    try:
        profile_root = temp_root / "legacy"
        (profile_root / "output").mkdir(parents=True, exist_ok=True)
        (profile_root / "output" / "command_costs.jsonl").write_text("", encoding="utf-8")
        query_set = {
            "name": "sample",
            "description": "",
            "defaults": {"community_level": 2, "response_type": "Multiple Paragraphs", "streaming": False},
            "queries": [
                module.QuerySpec(id="theme", prompt="What are the themes?", method="global"),
                module.QuerySpec(id="detail", prompt="Who is Scrooge?", method="local"),
            ],
            "source_path": temp_root / "sample.yaml",
        }
        run_meta = {
            "run_id": "20260331-000000__sample",
            "query_set": query_set,
            "profiles": [profile_root],
            "output_dir": temp_root / "run",
            "started_at": "2026-03-31T00:00:00+09:00",
            "finished_at": None,
            "max_profile_workers": 1,
            "results_path": temp_root / "run" / "results.jsonl",
            "summary_path": temp_root / "run" / "summary.md",
        }

        def fake_run(command, cwd, capture_output, check):
            assert cwd == profile_root
            assert capture_output is True
            assert check is False
            query_text = command[4]
            cost_file = profile_root / "output" / "command_costs.jsonl"
            if query_text == "What are the themes?":
                cost_file.write_text(
                    json.dumps(
                        {
                            "command": "graphrag query",
                            "prompt_tokens": 10,
                            "completion_tokens": 20,
                            "total_cost": 0.03,
                        }
                    )
                    + "\n",
                    encoding="utf-8",
                )
                return subprocess.CompletedProcess(
                    command,
                    0,
                    stdout="図面管理の目的は、図面を適切に管理し、情報の流出を防ぐことです。\n".encode("cp932"),
                    stderr=b"",
                )
            cost_file.write_text(
                cost_file.read_text(encoding="utf-8")
                + json.dumps(
                    {
                        "command": "graphrag query",
                        "prompt_tokens": 5,
                        "completion_tokens": 7,
                        "total_cost": 0.012,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            return subprocess.CompletedProcess(
                command,
                1,
                stdout="社内図面は管理対象です。\n".encode("cp932"),
                stderr="エラーが発生しました。\n".encode("cp932"),
            )

        results = module.run_profile_queries(run_meta, profile_root, runner=fake_run)

        assert len(results) == 2
        assert results[0]["status"] == "succeeded"
        assert results[0]["prompt_tokens"] == 10
        assert results[0]["response_hash"] is not None
        assert results[1]["status"] == "failed"
        assert results[1]["exit_code"] == 1
        assert results[1]["total_cost"] == 0.012
        assert (
            temp_root / "run" / "profiles" / "legacy" / "001__theme.txt"
        ).read_text(encoding="utf-8") == "図面管理の目的は、図面を適切に管理し、情報の流出を防ぐことです。\n"
        assert len(module.read_jsonl(temp_root / "run" / "results.jsonl")) == 2
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def test_run_matrix_and_render_summary() -> None:
    module = _load_module(
        "test_run_query_matrix_module_matrix",
        Path(__file__).resolve().parents[3] / "scripts" / "run_query_matrix.py",
    )
    temp_root = Path.cwd() / "_tmp_run_query_matrix_matrix_test"
    shutil.rmtree(temp_root, ignore_errors=True)
    temp_root.mkdir(parents=True, exist_ok=True)
    try:
        profiles = []
        for name in ["legacy", "prompt_tuning_test_nano"]:
            profile_root = temp_root / name
            profile_root.mkdir(parents=True, exist_ok=True)
            profiles.append(profile_root)

        query_set = {
            "name": "sample",
            "description": "比較用",
            "defaults": {"community_level": 2, "response_type": "Multiple Paragraphs", "streaming": False},
            "queries": [module.QuerySpec(id="theme", prompt="What are the themes?", method="global")],
            "source_path": temp_root / "sample.yaml",
        }
        run_meta = {
            "run_id": "20260331-000000__sample",
            "query_set": query_set,
            "profiles": profiles,
            "output_dir": temp_root / "matrix_run",
            "started_at": "2026-03-31T00:00:00+09:00",
            "finished_at": None,
            "max_profile_workers": 2,
            "results_path": temp_root / "matrix_run" / "results.jsonl",
            "summary_path": temp_root / "matrix_run" / "summary.md",
        }

        def fake_worker(received_run, profile_root, profile_index):
            assert profile_index in {0, 1}
            return [
                {
                    "run_id": received_run["run_id"],
                    "profile_name": profile_root.name,
                    "profile_root": str(profile_root),
                    "query_set_name": received_run["query_set"]["name"],
                    "query_index": 1,
                    "query_id": "theme",
                    "prompt": "What are the themes?",
                    "method": "global",
                    "community_level": 2,
                    "response_type": "Multiple Paragraphs",
                    "streaming": False,
                    "status": "succeeded",
                    "exit_code": 0,
                    "started_at": "2026-03-31T00:00:00+09:00",
                    "finished_at": "2026-03-31T00:00:01+09:00",
                    "duration_seconds": 1.0,
                    "stdout_path": f"profiles/{profile_root.name}/001__theme.txt",
                    "stderr_path": f"profiles/{profile_root.name}/001__theme.stderr.txt",
                    "response_hash": "a" * 64,
                    "stdout_bytes": 12,
                    "stderr_bytes": 0,
                    "cost_record": {"command": "graphrag query"},
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "total_cost": 0.03,
                }
            ]

        results = module.run_matrix(run_meta, worker_count=2)

        assert len(results) == 2
        assert run_meta["summary_path"].is_file()
        summary = run_meta["summary_path"].read_text(encoding="utf-8")
        assert "クエリ比較サマリー" in summary
        assert "一致判定" in summary
        assert "legacy" in summary
        assert "prompt_tuning_test_nano" in summary
        manifest = json.loads((run_meta["output_dir"] / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["result_counts"]["total"] == 2
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)
