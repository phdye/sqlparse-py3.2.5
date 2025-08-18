#!/usr/bin/env python3

"""
shift-ext-to-end — move an inlined extension to the end of filenames.

Usage:
  shift-ext-to-end [options] <ext> [<target-dir>]

Arguments:
  <ext>         The file extension to shift (without the leading dot), e.g. "txt".
  <target-dir>  Directory to walk. Defaults to current directory '.' if omitted.

Options:
  -n, --dry-run     Show planned changes without renaming anything.
  -v, --verbose     Print extra details about matches and decisions.
  -q, --quiet       Only print warnings and errors.
  --overwrite       Allow overwriting an existing destination file.
  -i, --ignore-case Match the extension case-insensitively.

Description:
  Walk the directory tree (top-down). For any file whose name contains
  ".<ext>" not at the end (i.e., followed by a non-word separator then more
  characters), rename it from:

      <before>.<ext>\W<after>

  to:

      <before><after>.<ext>

  where \W is any non-word character (as in Python regex): [^A-Za-z0-9_].

Examples:
  "report.txt~backup"  ->  "report~backup.txt"
  "log.TXT-2024" (with -i) -> "log-2024.TXT"
"""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from typing import Optional, Tuple


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="shift-ext-to-end",
        description="Move an inlined extension to the end of filenames.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        add_help=True,
        usage="shift-ext-to-end [options] <ext> [<target-dir>]",
    )

    parser.add_argument("ext", help="Target extension without leading dot (e.g., 'txt')")
    parser.add_argument(
        "target_dir",
        nargs="?",
        default=Path("."),
        type=Path,
        help="Directory to walk (searched top-down)",
    )

    opts = parser.add_argument_group("options")
    opts.add_argument("-n", "--dry-run", action="store_true", help="Do not perform changes")
    opts.add_argument("-v", "--verbose", action="count", default=0, help="Increase verbosity (-vv for more)")
    opts.add_argument("-q", "--quiet", action="store_true", help="Suppress non-error output")
    opts.add_argument("--overwrite", action="store_true", help="Overwrite existing destination if it exists")
    opts.add_argument("-i", "--ignore-case", action="store_true", help="Case-insensitive extension match")

    return parser


def compile_pattern(ext: str, ignore_case: bool) -> re.Pattern[str]:
    # Match any filename containing ".ext" followed by a non-word char and then more text (not at end)
    # Capture groups: before, after. We use a greedy 'before' so we move the *last* such occurrence.
    flags = re.IGNORECASE if ignore_case else 0
    ext_esc = re.escape(ext)
    pattern = rf"^(?P<before>.*)\.{ext_esc}(?P<sep>\W)(?P<after>.+)$"
    return re.compile(pattern, flags)


def plan_new_name(name: str, ext: str, pat: re.Pattern[str]) -> Optional[Tuple[str, str]]:
    """Return (old_name, new_name) if a rename is needed, else None."""
    m = pat.search(name)
    if not m:
        return None
    before = m.group("before")
    after = m.group("after")
    new_name = f"{before}{after}.{ext}"
    if new_name == name:
        return None
    return name, new_name


def log(msg: str, *, quiet: bool, verbose: int, level: int = 0) -> None:
    if quiet:
        return
    if verbose >= level:
        print(msg)


def rename_file(src: Path, dst: Path, *, dry_run: bool, overwrite: bool) -> None:
    dst_parent = dst.parent
    dst_parent.mkdir(parents=True, exist_ok=True)
    if dry_run:
        print(f"DRY-RUN: {src} -> {dst}")
        return
    if overwrite:
        os.replace(src, dst)  # atomic where possible; overwrites if needed
    else:
        if dst.exists():
            raise FileExistsError(f"Destination exists: {dst}")
        src.rename(dst)


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    ext = args.ext.lstrip(".")  # tolerate accidental leading dot
    target_dir: Path = args.target_dir.resolve()

    if not target_dir.exists() or not target_dir.is_dir():
        parser.error(f"Target directory does not exist or is not a directory: {target_dir}")

    pat = compile_pattern(ext, args.ignore_case)

    total_examined = 0
    total_matched = 0
    total_renamed = 0
    total_skipped = 0

    log(f"Walking (top-down) under: {target_dir}", quiet=args.quiet, verbose=args.verbose, level=0)

    for root, _dirs, files in os.walk(target_dir, topdown=True):
        root_path = Path(root)
        for fname in files:
            total_examined += 1
            plan = plan_new_name(fname, ext, pat)
            if not plan:
                continue
            total_matched += 1
            old_name, new_name = plan

            src = root_path / old_name
            dst = root_path / new_name

            log(f"Match: {src.name}  ->  {dst.name}", quiet=args.quiet, verbose=args.verbose, level=0)

            try:
                rename_file(src, dst, dry_run=args.dry_run, overwrite=args.overwrite)
                total_renamed += 1
            except FileExistsError as e:
                total_skipped += 1
                print(f"WARNING: {e}")
            except OSError as e:
                total_skipped += 1
                print(f"ERROR: Could not rename {src} -> {dst}: {e}")

    if not args.quiet:
        print(
            "\nSummary: examined={}, matched={}, renamed={}, skipped={}".format(
                total_examined, total_matched, total_renamed, total_skipped
            )
        )

    return 0 if total_skipped == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
