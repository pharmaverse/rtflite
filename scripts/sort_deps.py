"""Sort pyproject.toml dependencies by re-adding them with uv.

This script reads dependency declarations from pyproject.toml, removes them with
`uv remove`, and re-adds them with `uv add` so uv's automatic sorting is applied.
"""

from __future__ import annotations

import argparse
import re
import shlex
import subprocess
import sys
from pathlib import Path

try:
    import tomllib
except ImportError as exc:  # pragma: no cover - tomllib is Python 3.11+
    print("This script requires Python 3.11+ (tomllib).", file=sys.stderr)
    raise SystemExit(1) from exc


NAME_RE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")


def load_pyproject(path: Path) -> dict:
    """Load a pyproject.toml file into a dict.

    Args:
        path: Path to pyproject.toml.

    Returns:
        Parsed TOML content.
    """
    if not path.is_file():
        raise FileNotFoundError(f"pyproject.toml not found: {path}")
    with path.open("rb") as handle:
        return tomllib.load(handle)


def ensure_string_list(value: object, location: str) -> list[str]:
    """Validate a TOML value is a list of strings.

    Args:
        value: Value to validate.
        location: Friendly location string for error messages.

    Returns:
        The original list, typed as list[str].

    Raises:
        TypeError: If the value is not a list of strings.
    """
    if value is None:
        return []
    if not isinstance(value, list):
        raise TypeError(f"Expected {location} to be a list of strings.")
    for item in value:
        if not isinstance(item, str):
            raise TypeError(f"Expected {location} to contain only strings.")
    return value


def ensure_mapping(value: object, location: str) -> dict[str, list[str]]:
    """Validate a TOML table of dependency groups.

    Args:
        value: Value to validate.
        location: Friendly location string for error messages.

    Returns:
        Mapping of group name to dependency list.

    Raises:
        TypeError: If the value is not a string-keyed mapping of lists.
    """
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise TypeError(f"Expected {location} to be a table of lists.")
    result: dict[str, list[str]] = {}
    for key, entries in value.items():
        if not isinstance(key, str):
            raise TypeError(f"Expected {location} keys to be strings.")
        result[key] = ensure_string_list(entries, f"{location}.{key}")
    return result


def extract_name(requirement: str) -> str:
    """Extract the package name from a requirement string.

    Args:
        requirement: PEP 508-style requirement string.

    Returns:
        The package name.

    Raises:
        ValueError: If the requirement cannot be parsed.
    """
    match = NAME_RE.match(requirement)
    if not match:
        raise ValueError(f"Unable to parse dependency name from: {requirement!r}")
    return match.group(1)


def unique_in_order(items: list[str]) -> list[str]:
    """Return unique items while preserving first-seen order.

    Args:
        items: Items to de-duplicate.

    Returns:
        Unique items in their original order.
    """
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def run_uv(command: list[str], cwd: Path, dry_run: bool) -> None:
    """Run a uv command, or print it when in dry-run mode.

    Args:
        command: Command and arguments to execute.
        cwd: Working directory for the uv invocation.
        dry_run: When true, print the command without executing it.
    """
    printable = shlex.join(command)
    if dry_run:
        print(f"[dry-run] {printable}")
        return
    print(f"[run] {printable}")
    subprocess.run(command, cwd=cwd, check=True)


def remove_and_add(
    *,
    requirements: list[str],
    remove_flags: list[str],
    add_flags_prefix: list[str],
    add_flags_suffix: list[str],
    cwd: Path,
    dry_run: bool,
) -> None:
    """Remove and re-add requirements using uv with the given flags.

    Args:
        requirements: Requirement strings to manage.
        remove_flags: Flags passed to `uv remove`.
        add_flags_prefix: Flags placed before requirements in `uv add`.
        add_flags_suffix: Flags placed after requirements in `uv add`.
        cwd: Working directory for uv commands.
        dry_run: When true, print commands without executing them.
    """
    if not requirements:
        return
    names = unique_in_order([extract_name(req) for req in requirements])
    if names:
        run_uv(["uv", "remove", *remove_flags, *names], cwd=cwd, dry_run=dry_run)
    run_uv(
        ["uv", "add", *add_flags_prefix, *requirements, *add_flags_suffix],
        cwd=cwd,
        dry_run=dry_run,
    )


def reset_python_version_markers(path: Path, *, dry_run: bool) -> None:
    """Replace python_full_version markers with python_version in pyproject.toml.

    Args:
        path: Path to pyproject.toml.
        dry_run: When true, print the change without writing the file.
    """
    content = path.read_text(encoding="utf-8")
    updated = content.replace("python_full_version", "python_version")
    if updated == content:
        return
    if dry_run:
        print(f"[dry-run] replace python_full_version markers in {path}")
        return
    path.write_text(updated, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the script."""
    default_pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    parser = argparse.ArgumentParser(
        description="Re-add dependencies with uv to sort them in pyproject.toml."
    )
    parser.add_argument(
        "--pyproject",
        type=Path,
        default=default_pyproject,
        help="Path to pyproject.toml (default: repo root).",
    )
    parser.add_argument(
        "--no-sync",
        action="store_true",
        help="Pass --no-sync to uv commands.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print uv commands without executing them.",
    )
    return parser.parse_args()


def main() -> int:
    """Entry point for sorting dependencies via uv."""
    args = parse_args()
    pyproject_path = args.pyproject
    if pyproject_path.is_dir():
        pyproject_path = pyproject_path / "pyproject.toml"
    data = load_pyproject(pyproject_path)
    root = pyproject_path.parent
    no_sync = ["--no-sync"] if args.no_sync else []

    project = data.get("project", {})
    dependencies = ensure_string_list(
        project.get("dependencies"), "project.dependencies"
    )
    optional_dependencies = ensure_mapping(
        project.get("optional-dependencies"), "project.optional-dependencies"
    )
    dependency_groups = ensure_mapping(
        data.get("dependency-groups"), "dependency-groups"
    )

    remove_and_add(
        requirements=dependencies,
        remove_flags=no_sync,
        add_flags_prefix=no_sync,
        add_flags_suffix=[],
        cwd=root,
        dry_run=args.dry_run,
    )

    for group, requirements in dependency_groups.items():
        add_suffix: list[str]
        if group == "dev":
            remove_flags = [*no_sync, "--dev"]
            add_prefix = [*no_sync, "--dev"]
            add_suffix = []
        else:
            remove_flags = [*no_sync, "--group", group]
            add_prefix = [*no_sync, "--group", group]
            add_suffix = []
        remove_and_add(
            requirements=requirements,
            remove_flags=remove_flags,
            add_flags_prefix=add_prefix,
            add_flags_suffix=add_suffix,
            cwd=root,
            dry_run=args.dry_run,
        )

    for group, requirements in optional_dependencies.items():
        remove_flags = [*no_sync, "--optional", group]
        add_prefix = [*no_sync]
        add_suffix = ["--optional", group]
        remove_and_add(
            requirements=requirements,
            remove_flags=remove_flags,
            add_flags_prefix=add_prefix,
            add_flags_suffix=add_suffix,
            cwd=root,
            dry_run=args.dry_run,
        )

    reset_python_version_markers(pyproject_path, dry_run=args.dry_run)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
