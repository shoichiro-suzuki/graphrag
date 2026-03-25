#!/usr/bin/env python
# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""Create a GraphRAG profile by copying the template profile."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PROFILES_ROOT = REPO_ROOT / "graphrag_quickstart" / "profiles"
TEMPLATE_PROFILE = PROFILES_ROOT / "_template"


def copy_profile(
    template_dir: Path,
    target_dir: Path,
    force: bool = False,
    profiles_root: Path | None = None,
) -> None:
    """Copy a template profile into a new profile directory."""
    template_dir = template_dir.resolve()
    target_dir = target_dir.resolve()

    if not template_dir.is_dir():
        msg = f"Template profile not found: {template_dir}"
        raise FileNotFoundError(msg)

    profiles_root = (profiles_root or PROFILES_ROOT).resolve()
    if not target_dir.is_relative_to(profiles_root):
        msg = f"Profile target must be under {profiles_root}: {target_dir}"
        raise ValueError(msg)

    if target_dir.exists():
        if not force:
            msg = f"Target profile already exists: {target_dir}"
            raise FileExistsError(msg)
        shutil.rmtree(target_dir)

    shutil.copytree(template_dir, target_dir)

    env_example = target_dir / ".env.example"
    env_file = target_dir / ".env"
    if env_example.is_file():
        env_file.write_text(env_example.read_text(encoding="utf-8"), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Create a GraphRAG profile from the shipped template profile.",
    )
    parser.add_argument(
        "profile_name",
        help="Profile directory name to create under graphrag_quickstart/profiles.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the target profile if it already exists.",
    )
    return parser


def main() -> int:
    """Run the profile bootstrapper."""
    args = build_parser().parse_args()

    profile_name = args.profile_name.strip()
    if not profile_name:
        raise ValueError("Profile name is required.")

    profile_path = Path(profile_name)
    if profile_path.name != profile_name or profile_name in {".", ".."}:
        raise ValueError("Profile name must be a single directory name.")
    if profile_name.startswith("_"):
        raise ValueError("Profile names starting with '_' are reserved.")

    target_dir = PROFILES_ROOT / profile_name
    copy_profile(TEMPLATE_PROFILE, target_dir, force=bool(args.force))
    print(f"Created profile: {target_dir}")
    print("Next: edit prompts/settings.yaml if needed, then run graphrag index/query with --root.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
