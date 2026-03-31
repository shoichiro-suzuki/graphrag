#!/usr/bin/env python
# Copyright (c) 2026 Microsoft Corporation.
# Licensed under the MIT License

from __future__ import annotations

import argparse
import locale
import hashlib
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
PROFILES_ROOT = REPO_ROOT / "graphrag_quickstart" / "profiles"
QUERY_SETS_ROOT = PROFILES_ROOT / "query_sets"
QUERY_RUNS_ROOT = PROFILES_ROOT / "query_runs"

ALLOWED_METHODS = {"global", "local", "drift", "basic"}
DEFAULT_COMMUNITY_LEVEL = 2
DEFAULT_RESPONSE_TYPE = "Multiple Paragraphs"


@dataclass(slots=True)
class QuerySpec:
    id: str
    prompt: str
    method: str
    community_level: int | None = None
    response_type: str | None = None
    streaming: bool | None = None


def safe_name(value: str) -> str:
    cleaned = []
    for char in value.strip():
        cleaned.append(char if (char.isalnum() or char in {"-", "_", "."}) else "_")
    return "".join(cleaned).strip("._") or "query"


def iso_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def resolve_profile_root(profile_name: str) -> Path:
    profile_name = profile_name.strip()
    if not profile_name:
        raise ValueError("profile 名は必須です。")
    if Path(profile_name).name != profile_name or profile_name in {".", ".."}:
        raise ValueError("profile 名は単一のディレクトリ名で指定してください。")
    profile_root = (PROFILES_ROOT / profile_name).resolve()
    if not profile_root.is_dir():
        raise FileNotFoundError(f"profile が見つかりません: {profile_root}")
    if not profile_root.is_relative_to(PROFILES_ROOT.resolve()):
        raise ValueError(f"profile は {PROFILES_ROOT.resolve()} 配下に置いてください。")
    return profile_root


def resolve_query_set_path(value: str | Path) -> Path:
    raw_path = Path(value)
    candidates = [raw_path]
    if not raw_path.suffix:
        candidates.append(raw_path.with_suffix(".yaml"))
    if not raw_path.is_absolute():
        candidates.extend(
            [
                QUERY_SETS_ROOT / raw_path,
                QUERY_SETS_ROOT / raw_path.with_suffix(".yaml"),
            ]
        )
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise FileNotFoundError(f"query set が見つかりません: {value}")


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "1", "on"}:
            return True
        if normalized in {"false", "no", "0", "off"}:
            return False
    raise ValueError(f"boolean 値として解釈できません: {value!r}")


def parse_query_entry(entry: Any, index: int) -> QuerySpec:
    if not isinstance(entry, dict):
        raise ValueError(f"queries[{index}] は mapping で指定してください。")
    query_id = str(entry.get("id") or "").strip()
    if not query_id:
        raise ValueError(f"queries[{index}] に id がありません。")
    prompt = str(entry.get("prompt") or "").strip()
    if not prompt:
        raise ValueError(f"queries[{index}] ({query_id}) の prompt が空です。")
    method = str(entry.get("method") or "").strip().lower()
    if method not in ALLOWED_METHODS:
        raise ValueError(f"queries[{index}] ({query_id}) の method が不正です: {method}")
    community_level = entry.get("community_level")
    response_type = entry.get("response_type")
    streaming = entry.get("streaming")
    return QuerySpec(
        id=query_id,
        prompt=prompt,
        method=method,
        community_level=None if community_level is None else int(community_level),
        response_type=None if response_type is None else str(response_type).strip() or None,
        streaming=None if streaming is None else _bool(streaming),
    )


def load_query_set(query_set_path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(query_set_path.read_text(encoding="utf-8"))
    if raw is None:
        raise ValueError(f"query set が空です: {query_set_path}")
    if isinstance(raw, list):
        metadata: dict[str, Any] = {}
        query_entries = raw
    elif isinstance(raw, dict):
        metadata = raw
        query_entries = raw.get("queries")
    else:
        raise ValueError("query set は YAML の list か mapping で定義してください。")
    if not isinstance(query_entries, list) or not query_entries:
        raise ValueError("query set には 1 件以上の queries が必要です。")

    defaults = metadata.get("defaults") or {}
    if not isinstance(defaults, dict):
        raise ValueError("defaults は mapping で指定してください。")

    queries: list[QuerySpec] = []
    seen_ids: set[str] = set()
    for index, entry in enumerate(query_entries, start=1):
        query = parse_query_entry(entry, index)
        if query.id in seen_ids:
            raise ValueError(f"query id が重複しています: {query.id}")
        seen_ids.add(query.id)
        queries.append(query)

    return {
        "name": str(metadata.get("name") or query_set_path.stem).strip() or query_set_path.stem,
        "description": str(metadata.get("description") or "").strip(),
        "defaults": defaults,
        "queries": queries,
        "source_path": query_set_path.resolve(),
    }


def effective_community_level(query: QuerySpec, defaults: dict[str, Any]) -> int | None:
    if query.method == "basic":
        return None
    if query.community_level is not None:
        return query.community_level
    return int(defaults.get("community_level", DEFAULT_COMMUNITY_LEVEL))


def effective_response_type(query: QuerySpec, defaults: dict[str, Any]) -> str:
    return query.response_type or str(defaults.get("response_type") or DEFAULT_RESPONSE_TYPE)


def effective_streaming(query: QuerySpec, defaults: dict[str, Any]) -> bool:
    if query.streaming is not None:
        return query.streaming
    if "streaming" in defaults:
        return _bool(defaults["streaming"])
    return False


def build_query_command(query: QuerySpec, defaults: dict[str, Any]) -> list[str]:
    command = [
        sys.executable,
        "-m",
        "graphrag",
        "query",
        query.prompt,
        "--root",
        ".",
        "--method",
        query.method,
    ]
    community_level = effective_community_level(query, defaults)
    if community_level is not None:
        command.extend(["--community-level", str(community_level)])
    command.extend(["--response-type", effective_response_type(query, defaults)])
    if effective_streaming(query, defaults):
        command.append("--streaming")
    else:
        command.append("--no-streaming")
    return command


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


def count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    return len(path.read_text(encoding="utf-8").splitlines())


def load_recent_cost_record(cost_path: Path, starting_line_count: int) -> dict[str, Any] | None:
    if not cost_path.exists():
        return None
    latest = None
    for line in cost_path.read_text(encoding="utf-8").splitlines()[starting_line_count:]:
        line = line.strip()
        if not line:
            continue
        record = json.loads(line)
        if str(record.get("command")) == "graphrag query":
            latest = record
    return latest


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def profile_artifact_path(run_dir: Path, profile_name: str, query_index: int, query_id: str, suffix: str) -> Path:
    return run_dir / "profiles" / profile_name / f"{query_index:03d}__{safe_name(query_id)}{suffix}"


def run_profile_queries(
    run_meta: dict[str, Any],
    profile_root: Path,
    runner: Any = subprocess.run,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    results_path = run_meta["output_dir"] / "results.jsonl"
    cost_path = profile_root / "output" / "command_costs.jsonl"
    results_lock = run_meta.get("results_lock")
    for query_index, query in enumerate(run_meta["query_set"]["queries"], start=1):
        stdout_path = profile_artifact_path(run_meta["output_dir"], profile_root.name, query_index, query.id, ".txt")
        stderr_path = profile_artifact_path(run_meta["output_dir"], profile_root.name, query_index, query.id, ".stderr.txt")
        previous_lines = count_lines(cost_path)
        started_at = iso_now()
        started_clock = datetime.now().astimezone()
        command = build_query_command(query, run_meta["query_set"]["defaults"])
        try:
            completed = runner(
                command,
                cwd=profile_root,
                capture_output=True,
                check=False,
            )
            stdout = decode_process_output(completed.stdout)
            stderr = decode_process_output(completed.stderr)
            exit_code = completed.returncode
        except Exception as exc:  # noqa: BLE001
            stdout = ""
            stderr = f"{type(exc).__name__}: {exc}"
            exit_code = None
        finished_at = iso_now()
        duration_seconds = round((datetime.now().astimezone() - started_clock).total_seconds(), 3)
        write_text(stdout_path, stdout)
        write_text(stderr_path, stderr)

        cost_record = load_recent_cost_record(cost_path, previous_lines)
        record = {
            "run_id": run_meta["run_id"],
            "profile_name": profile_root.name,
            "profile_root": str(profile_root),
            "query_set_name": run_meta["query_set"]["name"],
            "query_index": query_index,
            "query_id": query.id,
            "prompt": query.prompt,
            "method": query.method,
            "community_level": effective_community_level(query, run_meta["query_set"]["defaults"]),
            "response_type": effective_response_type(query, run_meta["query_set"]["defaults"]),
            "streaming": effective_streaming(query, run_meta["query_set"]["defaults"]),
            "status": "succeeded" if exit_code == 0 else "failed",
            "exit_code": exit_code,
            "started_at": started_at,
            "finished_at": finished_at,
            "duration_seconds": duration_seconds,
            "stdout_path": str(stdout_path.relative_to(run_meta["output_dir"])),
            "stderr_path": str(stderr_path.relative_to(run_meta["output_dir"])),
            "response_hash": hashlib.sha256(stdout.encode("utf-8")).hexdigest(),
            "stdout_bytes": len(stdout.encode("utf-8")),
            "stderr_bytes": len(stderr.encode("utf-8")),
            "cost_record": cost_record,
            "prompt_tokens": None if cost_record is None else cost_record.get("prompt_tokens"),
            "completion_tokens": None if cost_record is None else cost_record.get("completion_tokens"),
            "total_cost": None if cost_record is None else cost_record.get("total_cost"),
        }
        if results_lock is None:
            append_jsonl(results_path, record)
        else:
            with results_lock:
                append_jsonl(results_path, record)
        results.append(record)
    return results


def decode_process_output(value: Any) -> str:
    """Decode subprocess output robustly across Windows locales."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if not isinstance(value, (bytes, bytearray)):
        return str(value)

    raw = bytes(value)
    encodings = []
    preferred = locale.getpreferredencoding(False)
    if preferred:
        encodings.append(preferred)
    encodings.extend(["cp932", "utf-8"])

    for encoding in dict.fromkeys(encodings):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def build_manifest(run_meta: dict[str, Any], results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "run_id": run_meta["run_id"],
        "query_set": {
            "name": run_meta["query_set"]["name"],
            "description": run_meta["query_set"]["description"],
            "source_path": str(run_meta["query_set"]["source_path"]),
            "defaults": run_meta["query_set"]["defaults"],
            "queries": [asdict(query) for query in run_meta["query_set"]["queries"]],
        },
        "profiles": [str(profile) for profile in run_meta["profiles"]],
        "output_dir": str(run_meta["output_dir"]),
        "started_at": run_meta["started_at"],
        "finished_at": run_meta["finished_at"],
        "max_profile_workers": run_meta["max_profile_workers"],
        "results_path": str(run_meta["results_path"]),
        "summary_path": str(run_meta["summary_path"]),
        "result_counts": {
            "total": len(results),
            "succeeded": sum(1 for result in results if result["status"] == "succeeded"),
            "failed": sum(1 for result in results if result["status"] != "succeeded"),
        },
    }


def render_summary(run_meta: dict[str, Any], results: list[dict[str, Any]]) -> str:
    query_order = {query.id: index for index, query in enumerate(run_meta["query_set"]["queries"])}
    profile_order = {profile.name: index for index, profile in enumerate(run_meta["profiles"])}
    grouped: dict[str, list[dict[str, Any]]] = {}
    for result in results:
        grouped.setdefault(result["query_id"], []).append(result)

    lines = ["# クエリ比較サマリー", "", "## 実行概要", ""]
    lines.append(f"- run_id: `{run_meta['run_id']}`")
    lines.append(f"- query set: `{run_meta['query_set']['name']}`")
    lines.append(f"- query set path: `{run_meta['query_set']['source_path']}`")
    lines.append(f"- profiles: {', '.join(f'`{profile.name}`' for profile in run_meta['profiles'])}")
    lines.append(f"- started_at: `{run_meta['started_at']}`")
    lines.append(f"- finished_at: `{run_meta['finished_at']}`")
    lines.append(f"- max_profile_workers: `{run_meta['max_profile_workers']}`")
    lines.append(f"- total results: `{len(results)}`")
    lines.append(f"- succeeded: `{sum(1 for result in results if result['status'] == 'succeeded')}`")
    lines.append(f"- failed: `{sum(1 for result in results if result['status'] != 'succeeded')}`")
    lines.append("")

    for query in sorted(run_meta["query_set"]["queries"], key=lambda item: query_order[item.id]):
        lines.append(f"## {query.id}")
        lines.append("")
        lines.append(f"- method: `{query.method}`")
        lines.append(f"- prompt: {query.prompt}")
        lines.append(f"- response_type: `{effective_response_type(query, run_meta['query_set']['defaults'])}`")
        community_level = effective_community_level(query, run_meta["query_set"]["defaults"])
        if community_level is not None:
            lines.append(f"- community_level: `{community_level}`")
        lines.append(f"- streaming: `{effective_streaming(query, run_meta['query_set']['defaults'])}`")
        lines.append("")

        rows = sorted(grouped.get(query.id, []), key=lambda item: profile_order[item["profile_name"]])
        if not rows:
            lines.append("_この query の結果はありません。_")
            lines.append("")
            continue

        hashes = {row["response_hash"] for row in rows if row["status"] == "succeeded"}
        if len(hashes) == 1 and all(row["status"] == "succeeded" for row in rows):
            lines.append("- 一致判定: 全 profile で応答ハッシュが一致")
        elif any(row["status"] != "succeeded" for row in rows):
            lines.append("- 一致判定: 失敗を含むため未判定")
        else:
            lines.append("- 一致判定: 応答ハッシュが不一致")
        lines.append("")

        lines.extend(
            render_table(
                ["profile", "status", "exit", "duration(s)", "prompt_tokens", "completion_tokens", "total_cost", "response_hash", "stdout"],
                [
                    [
                        row["profile_name"],
                        row["status"],
                        "" if row["exit_code"] is None else str(row["exit_code"]),
                        f"{float(row['duration_seconds']):.3f}",
                        "" if row["prompt_tokens"] is None else str(row["prompt_tokens"]),
                        "" if row["completion_tokens"] is None else str(row["completion_tokens"]),
                        "" if row["total_cost"] is None else f"{float(row['total_cost']):.6f}",
                        short_hash(row["response_hash"]),
                        row["stdout_path"],
                    ]
                    for row in rows
                ],
            )
        )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def short_hash(value: str | None) -> str:
    return "" if not value else value[:12]


def render_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    def fmt(row: list[str]) -> str:
        return "| " + " | ".join(cell.ljust(widths[index]) for index, cell in enumerate(row)) + " |"

    output = [fmt(headers), "| " + " | ".join("-" * width for width in widths) + " |"]
    output.extend(fmt(row) for row in rows)
    return output


def create_query_set_template(name: str) -> str:
    name = safe_name(name)
    return (
        f'name: "{name}"\n'
        "description: \"比較用のクエリセット\"\n"
        "defaults:\n"
        f"  community_level: {DEFAULT_COMMUNITY_LEVEL}\n"
        f"  response_type: \"{DEFAULT_RESPONSE_TYPE}\"\n"
        "  streaming: false\n"
        "queries:\n"
        "  - id: global_theme\n"
        "    method: global\n"
        "    prompt: \"What are the top themes in this story?\"\n"
        "  - id: local_relationships\n"
        "    method: local\n"
        "    prompt: \"Who is Scrooge and what are his main relationships?\"\n"
        "  - id: drift_development\n"
        "    method: drift\n"
        "    prompt: \"How does the story develop?\"\n"
        "  - id: basic_memory\n"
        "    method: basic\n"
        "    prompt: \"What does the document say about memory?\"\n"
    )


def write_query_set_template(path: Path, name: str, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"query set は既に存在します: {path}")
    write_text(path, create_query_set_template(name))


def resolve_run_dir(value: str | Path) -> Path:
    raw = Path(value)
    candidates = [raw]
    if not raw.is_absolute():
        candidates.append(QUERY_RUNS_ROOT / raw)
    for candidate in candidates:
        if candidate.is_dir():
            return candidate.resolve()
    raise FileNotFoundError(f"run ディレクトリが見つかりません: {value}")


def run_matrix(run_meta: dict[str, Any], worker_count: int | None = None) -> list[dict[str, Any]]:
    output_dir = run_meta["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)
    run_meta["results_path"] = output_dir / "results.jsonl"
    run_meta["summary_path"] = output_dir / "summary.md"
    run_meta["results_lock"] = Lock()
    worker_count = max(1, min(worker_count or len(run_meta["profiles"]), len(run_meta["profiles"])))
    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        future_map = {executor.submit(run_profile_queries, run_meta, profile): profile for profile in run_meta["profiles"]}
        for future in as_completed(future_map):
            profile = future_map[future]
            try:
                results.extend(future.result())
            except Exception as exc:  # noqa: BLE001
                error_path = output_dir / "profiles" / profile.name / "__profile_error__.stderr.txt"
                write_text(error_path, f"{type(exc).__name__}: {exc}")
                error_record = {
                    "run_id": run_meta["run_id"],
                    "profile_name": profile.name,
                    "profile_root": str(profile),
                    "query_set_name": run_meta["query_set"]["name"],
                    "query_index": 0,
                    "query_id": "__profile_error__",
                    "prompt": "",
                    "method": "",
                    "community_level": None,
                    "response_type": None,
                    "streaming": None,
                    "status": "failed",
                    "exit_code": None,
                    "started_at": iso_now(),
                    "finished_at": iso_now(),
                    "duration_seconds": 0.0,
                    "stdout_path": "",
                    "stderr_path": str(error_path.relative_to(output_dir)),
                    "response_hash": None,
                    "stdout_bytes": 0,
                    "stderr_bytes": 0,
                    "cost_record": None,
                    "prompt_tokens": None,
                    "completion_tokens": None,
                    "total_cost": None,
                }
                with run_meta["results_lock"]:
                    append_jsonl(run_meta["results_path"], error_record)
                results.append(
                    error_record
                )
    run_meta["finished_at"] = iso_now()
    if run_meta["results_path"] is not None and not run_meta["results_path"].exists():
        write_text(run_meta["results_path"], "")
    if run_meta["summary_path"] is not None:
        write_text(run_meta["summary_path"], render_summary(run_meta, results))
    write_json(output_dir / "manifest.json", build_manifest(run_meta, results))
    return results


def build_manifest(run_meta: dict[str, Any], results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "run_id": run_meta["run_id"],
        "query_set": {
            "name": run_meta["query_set"]["name"],
            "description": run_meta["query_set"]["description"],
            "source_path": str(run_meta["query_set"]["source_path"]),
            "defaults": run_meta["query_set"]["defaults"],
            "queries": [asdict(query) for query in run_meta["query_set"]["queries"]],
        },
        "profiles": [str(profile) for profile in run_meta["profiles"]],
        "output_dir": str(run_meta["output_dir"]),
        "started_at": run_meta["started_at"],
        "finished_at": run_meta["finished_at"],
        "max_profile_workers": run_meta["max_profile_workers"],
        "results_path": str(run_meta["results_path"]),
        "summary_path": str(run_meta["summary_path"]),
        "result_counts": {
            "total": len(results),
            "succeeded": sum(1 for result in results if result["status"] == "succeeded"),
            "failed": sum(1 for result in results if result["status"] != "succeeded"),
        },
    }


def run_init_set(args: argparse.Namespace) -> int:
    QUERY_SETS_ROOT.mkdir(parents=True, exist_ok=True)
    query_set_name = safe_name(args.name)
    target_path = QUERY_SETS_ROOT / f"{query_set_name}.yaml"
    write_query_set_template(target_path, query_set_name, bool(args.force))
    print(f"query set の雛形を作成しました: {target_path}")
    return 0


def run_run(args: argparse.Namespace) -> int:
    query_set_path = resolve_query_set_path(args.query_set)
    query_set = load_query_set(query_set_path)
    profiles = [resolve_profile_root(profile) for profile in args.profile]
    output_dir = Path(args.output_dir).resolve() / f"{datetime.now().astimezone().strftime('%Y%m%d-%H%M%S')}__{safe_name(query_set['name'])}"
    run_meta = {
        "run_id": output_dir.name,
        "query_set": query_set,
        "profiles": profiles,
        "output_dir": output_dir,
        "started_at": iso_now(),
        "finished_at": None,
        "max_profile_workers": args.max_profile_workers,
        "results_path": output_dir / "results.jsonl",
        "summary_path": output_dir / "summary.md",
    }
    results = run_matrix(run_meta, worker_count=args.max_profile_workers)
    failures = sum(1 for result in results if result["status"] != "succeeded")
    print(f"実行が完了しました: {run_meta['output_dir']}")
    print(f"summary: {run_meta['summary_path']}")
    print(f"結果件数: {len(results)} / 失敗件数: {failures}")
    return 1 if failures else 0


def run_report(args: argparse.Namespace) -> int:
    run_dir = resolve_run_dir(args.run_dir)
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"manifest.json が見つかりません: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    query_set = manifest["query_set"]
    run_meta = {
        "run_id": manifest.get("run_id") or run_dir.name,
        "query_set": {
            "name": query_set.get("name") or run_dir.name,
            "description": query_set.get("description") or "",
            "defaults": query_set.get("defaults") or {},
            "queries": [
                QuerySpec(
                    id=str(query.get("id") or ""),
                    prompt=str(query.get("prompt") or ""),
                    method=str(query.get("method") or ""),
                    community_level=query.get("community_level"),
                    response_type=query.get("response_type"),
                    streaming=query.get("streaming"),
                )
                for query in query_set.get("queries") or []
            ],
            "source_path": Path(query_set.get("source_path")) if query_set.get("source_path") else None,
        },
        "profiles": [Path(profile) for profile in manifest.get("profiles") or []],
        "output_dir": run_dir,
        "started_at": manifest.get("started_at") or "",
        "finished_at": manifest.get("finished_at") or "",
        "max_profile_workers": manifest.get("max_profile_workers"),
        "results_path": run_dir / "results.jsonl",
        "summary_path": Path(args.output).resolve() if args.output else run_dir / "summary.md",
    }
    results = read_jsonl(run_meta["results_path"])
    write_text(run_meta["summary_path"], render_summary(run_meta, results))
    print(f"summary を作成しました: {run_meta['summary_path']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="複数 profile の query 結果を比較する制御スクリプト。")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init-set", help="query set の雛形を作成します。")
    init_parser.add_argument("name", help="作成する query set 名。")
    init_parser.add_argument("--force", action="store_true", help="既存ファイルを上書きします。")
    init_parser.set_defaults(func=run_init_set)

    run_parser = subparsers.add_parser("run", help="query set を複数 profile で実行します。")
    run_parser.add_argument("--query-set", required=True, help="query set の YAML パス、または query_sets 配下の名前。")
    run_parser.add_argument("--profile", action="append", required=True, help="実行対象 profile 名。複数回指定できます。")
    run_parser.add_argument("--output-dir", default=str(QUERY_RUNS_ROOT), help="実行結果の出力先ディレクトリ。")
    run_parser.add_argument("--max-profile-workers", type=int, default=None, help="同時に実行する profile 数の上限。")
    run_parser.set_defaults(func=run_run)

    report_parser = subparsers.add_parser("report", help="既存の run ディレクトリからレポートを作成します。")
    report_parser.add_argument("run_dir", help="run ディレクトリ、または query_runs 配下の run_id。")
    report_parser.add_argument("--output", default=None, help="summary.md の出力先。省略時は run_dir/summary.md。")
    report_parser.set_defaults(func=run_report)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
