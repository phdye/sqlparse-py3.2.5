#!/usr/bin/env python

"""
shift-ext-to-end — move an inlined extension to the end of filenames.

Usage:
  shift-ext-to-end [options] <ext> [<target-dir>...]

Arguments:
  <ext>         The file extension to shift (without the leading dot), e.g. "txt".
  <target-dir>  One or more directories to walk. Defaults to current directory '.' if omitted.

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
  "log.TXT-2012" (with -i) -> "log-2012.TXT"
"""

import argparse
import os
import re
import sys
from os.path import abspath, exists, isdir, join


def build_parser():
    parser = argparse.ArgumentParser(
        prog="shift-ext-to-end",
        description="Move an inlined extension to the end of filenames.",
        usage="shift-ext-to-end [options] <ext> [<target-dir>...]",
    )

    parser.add_argument("ext", help="Target extension without leading dot (e.g., 'txt')")
    parser.add_argument(
        "target_dir",
        nargs="*",
        default=["."],
        help="Directories to walk (searched top-down)",
    )

    parser.add_argument("-n", "--dry-run", action="store_true", help="Do not perform changes")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase verbosity (-vv for more)")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress non-error output")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing destination if it exists")
    parser.add_argument("-i", "--ignore-case", action="store_true", help="Case-insensitive extension match")

    return parser


def compile_pattern(ext, ignore_case):
    flags = re.IGNORECASE if ignore_case else 0
    ext_esc = re.escape(ext)
    pattern = r"^(?P<before>.*)\." + ext_esc + r"(?P<sep>\W)(?P<after>.+)$"
    return re.compile(pattern, flags)


def plan_new_name(name, ext, pat):
    m = pat.search(name)
    if not m:
        return None
    before = m.group("before")
    after = m.group("after")
    new_name = "%s%s.%s" % (before, after, ext)
    if new_name == name:
        return None
    return (name, new_name)


def log(msg, quiet, verbose, level=0):
    if quiet:
        return
    if verbose >= level:
        print(msg)


def rename_file(src, dst, dry_run, overwrite):
    if dry_run:
        print("DRY-RUN: %s -> %s" % (src, dst))
        return
    if overwrite:
        if os.path.exists(dst):
            if os.path.isdir(dst):
                raise OSError("Destination is a directory: %s" % dst)
            os.remove(dst)
        os.rename(src, dst)
    else:
        if os.path.exists(dst):
            raise OSError("Destination exists: %s" % dst)
        os.rename(src, dst)


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    ext = args.ext.lstrip(".")
    target_dirs = [abspath(p) for p in (args.target_dir if args.target_dir else ["."])]

    for td in target_dirs:
        if not exists(td) or not isdir(td):
            parser.error("Target directory does not exist or is not a directory: %s" % td)

    pat = compile_pattern(ext, args.ignore_case)

    total_examined = 0
    total_matched = 0
    total_renamed = 0
    total_skipped = 0

    for td in target_dirs:
        log("Walking (top-down) under: %s" % td, args.quiet, args.verbose, level=0)
        for root, _dirs, files in os.walk(td, topdown=True):
            for fname in files:
                total_examined += 1
                plan = plan_new_name(fname, ext, pat)
                if not plan:
                    continue
                total_matched += 1
                old_name, new_name = plan

                src = join(root, old_name)
                dst = join(root, new_name)

                log("Match: %s -> %s" % (old_name, new_name), args.quiet, args.verbose, level=0)

                try:
                    rename_file(src, dst, args.dry_run, args.overwrite)
                    total_renamed += 1
                except OSError as e:
                    total_skipped += 1
                    print("WARNING: Could not rename %s -> %s: %s" % (src, dst, e))

    if not args.quiet:
        print("\nSummary: examined=%d, matched=%d, renamed=%d, skipped=%d" % (
            total_examined, total_matched, total_renamed, total_skipped))

    return 0 if total_skipped == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
