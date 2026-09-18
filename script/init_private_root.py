#!/usr/bin/env python3
"""Create the private data root and its account/ directory.

Reads paths.private_data_root from config/config.toml and creates that directory
plus an account/ subdirectory for credential files.

This script only creates directories. It never creates, reads, or prints the
contents of any file under the private data root.

Idempotent: running it again on an already-initialized root changes nothing.

Exit codes: 0 = ok, 2 = configuration or safety precondition failed.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tomllib
from pathlib import Path

CONFIG_REL = Path("config") / "config.toml"
EXAMPLE_REL = Path("config") / "config.example.toml"
ACCOUNT_DIRNAME = "account"
GUARD_TEXT = "# Never track anything under the private data root.\n*\n"
MARKER_NAME = ".ai-career-private-root"
MARKER_TEXT = (
    "This directory is an ai-career private data root. Files in it are private,\n"
    "and files under account/ are credential files (see rules/common.toml).\n"
)


def die(message: str, hint: str | None = None) -> None:
    print(f"error: {message}", file=sys.stderr)
    if hint:
        print(f"hint:  {hint}", file=sys.stderr)
    raise SystemExit(2)


def repo_root() -> Path:
    """Locate the repo root from this script's own location, not the cwd."""
    here = Path(__file__).resolve().parent
    try:
        out = subprocess.run(
            ["git", "-C", str(here), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        if out:
            return Path(out).resolve()
    except (OSError, subprocess.CalledProcessError):
        pass
    return here.parent


def read_private_data_root(config_path: Path) -> str:
    if not config_path.is_file():
        die(
            f"config file not found: {config_path}",
            f"copy {EXAMPLE_REL} to {CONFIG_REL} and set paths.private_data_root",
        )
    try:
        raw = config_path.read_bytes()
    except OSError as exc:
        die(f"cannot read {config_path}: {exc}")
    try:
        # utf-8-sig tolerates the BOM that PowerShell's Out-File writes.
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        die(
            f"{config_path} is not valid UTF-8: {exc}",
            "re-save it as UTF-8, e.g. Set-Content -Encoding utf8",
        )
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        die(f"{config_path} is not valid TOML: {exc}")

    paths = data.get("paths")
    if not isinstance(paths, dict) or "private_data_root" not in paths:
        die(
            f"paths.private_data_root is missing from {config_path}",
            "add it under a [paths] table",
        )
    value = paths["private_data_root"]
    if not isinstance(value, str) or not value.strip():
        die(
            f"paths.private_data_root is empty in {config_path}",
            r"set it to an absolute path, e.g. private_data_root = 'D:\ai-career\private'",
        )
    return value.strip()


def is_git_ignored(root: Path, target: Path) -> bool:
    """Ask git whether target is ignored. Dies if git cannot answer.

    The trailing separator matters: it tells git the path is a directory, so a
    directory-only rule such as `/private/` still matches on a fresh clone where
    the directory does not exist on disk yet.
    """
    probe = str(target) + os.sep
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "check-ignore", "--quiet", probe],
            capture_output=True, text=True,
        )
    except OSError as exc:
        die(
            f"could not run git to check ignore rules: {exc}",
            "install git, or move the private data root outside the repository",
        )
    if result.returncode in (0, 1):
        return result.returncode == 0
    die(
        f"git check-ignore failed (exit {result.returncode}): {result.stderr.strip()}",
        "the ignore status of the private data root could not be verified",
    )


def nearest_existing(path: Path) -> Path | None:
    for candidate in (path, *path.parents):
        if candidate.exists():
            return candidate
    return None


def ensure_dir(path: Path, dry_run: bool) -> str:
    """Create path if absent. Returns 'created', 'exists' or 'would create'."""
    if path.is_dir():
        return "exists"
    if path.exists():
        die(f"{path} exists but is not a directory")
    if dry_run:
        if nearest_existing(path) is None:
            die(f"cannot create {path}: its drive or root does not exist")
        return "would create"
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        die(f"could not create {path}: {exc}")
    return "created"


def ensure_guard(data_root: Path, dry_run: bool) -> str:
    """Write an ignore-everything .gitignore inside the private data root.

    Written unconditionally: if the root ever ends up inside a repository, or if
    the containment check below was wrong, this still keeps the contents untracked.
    """
    guard = data_root / ".gitignore"
    if guard.is_file():
        return "exists"
    if dry_run:
        return "would create"
    try:
        guard.write_text(GUARD_TEXT, encoding="utf-8")
    except OSError as exc:
        die(f"could not write {guard}: {exc}")
    return "created"


def ensure_marker(data_root: Path, dry_run: bool) -> str:
    """Mark the directory as a private data root.

    The marker keeps the directory recognizable as private after the config changes
    or breaks: rules/common.toml treats any directory holding it as a private area.
    """
    marker = data_root / MARKER_NAME
    if marker.is_file():
        return "exists"
    if dry_run:
        return "would create"
    try:
        marker.write_text(MARKER_TEXT, encoding="utf-8")
    except OSError as exc:
        die(f"could not write {marker}: {exc}")
    return "created"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="report what would happen, create nothing"
    )
    args = parser.parse_args()

    root = repo_root()
    config_path = root / CONFIG_REL
    raw_value = read_private_data_root(config_path)

    data_root = Path(raw_value)
    if not data_root.is_absolute():
        die(
            f"paths.private_data_root must be an absolute path, got {raw_value!r}",
            r"on Windows an absolute path includes the drive, e.g. 'C:\my\ai-career\private'",
        )

    # resolve(), not abspath(): both sides must be normalized the same way, or a
    # junction, symlink, subst drive or 8.3 short name would make a path inside the
    # repository look like it is outside, skipping the ignore check below.
    data_root = data_root.resolve()

    in_repo = (root / ".git").exists()
    inside_repo = in_repo and (data_root == root or data_root.is_relative_to(root))

    # A root equal to the repository, or containing it, would put the whole public
    # repository inside the private area.
    if root == data_root or root.is_relative_to(data_root):
        die("paths.private_data_root must not be the repository or a directory that contains it")

    # Everything under an account/ directory is a credential file (rules/common.toml),
    # so a root there would make the guard and marker files credential files too.
    if any(part.lower() == ACCOUNT_DIRNAME for part in data_root.parts):
        die(
            f"paths.private_data_root must not be, or be inside, a directory named '{ACCOUNT_DIRNAME}': {data_root}",
            "account directories hold only credential files",
        )

    # The private data root holds credentials and the repo is public, so a root
    # inside the working tree must already be ignored before anything is created.
    if inside_repo and not is_git_ignored(root, data_root):
        die(
            f"{data_root} is inside the repository but is not git-ignored",
            "add it to .gitignore before initializing; this directory will hold credentials",
        )

    account_dir = data_root / ACCOUNT_DIRNAME
    root_state = ensure_dir(data_root, args.dry_run)
    account_state = ensure_dir(account_dir, args.dry_run)
    guard_state = ensure_guard(data_root, args.dry_run)
    marker_state = ensure_marker(data_root, args.dry_run)

    location = "inside the repository" if inside_repo else "outside the repository"
    print(f"private_data_root  {data_root}  [{root_state}] ({location})")
    print(f"account directory  {account_dir}  [{account_state}]")
    print(f"ignore guard       {data_root / '.gitignore'}  [{guard_state}]")
    print(f"root marker        {data_root / MARKER_NAME}  [{marker_state}]")
    print()
    print("Put credential files in the account directory yourself.")
    print("This script does not create or read them, and they are stored unencrypted")
    print("unless you encrypt them.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
