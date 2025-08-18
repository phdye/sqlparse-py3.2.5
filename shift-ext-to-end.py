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
  "log.TXT-2012" (with -i) -> "log-2012.TXT"

Notes for Python 3.2.5 compatibility:
  * No f-strings or type hints are used.
  * No pathlib; paths handled with os.path.
  * No os.replace; overwrite is implemented by removing an existing destination file when --overwrite is set.
"""

import argparse
import os
import re
import sys


def build_parser():
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
        default='.',
        help="Directory to walk (searched top-down)",
    )

    opts = parser.add_argument_group("options")
    opts.add_argument("-n", "--dry-run", action="store_true", help="Do not perform changes")
    opts.add_argument("-v", "--verbose", action="count", default=0, help="Increase verbosity (-vv for more)")
    opts.add_argument("-q", "--quiet", action="store_true", help="Suppress non-error output")
    opts.add_argument("--overwrite", action="store_true", help="Overwrite existing destination if it exists")
    opts.add_argument("-i", "--ignore-case", action="store_true", help="Case-insensitive extension match")

    return parser


def compile_pattern(ext, ignore_case):
    # Match any filename containing ".ext" followed by a non-word char and then more text (not at end)
    # Capture groups: before, after. We use a greedy 'before' so we move the *last* such occurrence.
    flags = re.IGNORECASE if ignore_case else 0
    ext_esc = re.escape(ext)
    pattern = r"^(?P<before>.*)\." + ext_esc + r"(?P<sep>\W)(?P<after>.+)$"
    return re.compile(pattern, flags)


def plan_new_name(name, ext, pat):
    """Return (old_name, new_name) if a rename is needed, else None."""
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
        sys.stdout.write(msg + "\n")
        sys.stdout.flush()


def ensure_parent_dir(path):
    parent = os.path.dirname(path)
    if parent and not os.path.exists(parent):
        os.makedirs(parent)


def rename_file(src, dst, dry_run, overwrite):
    ensure_parent_dir(dst)
    if dry_run:
        sys.stdout.write("DRY-RUN: %s -> %s\n" % (src, dst))
        return

    if os.path.exists(dst):
        if overwrite:
            # Only remove if it's a file; otherwise raise
            if os.path.isdir(dst):
                raise OSError("Destination is a directory: %s" % dst)
            try:
                os.remove(dst)
            except OSError as e:
                raise OSError("Could not remove existing destination %s: %s" % (dst, e))
        else:
            raise OSError("Destination exists: %s" % dst)

    try:
        os.rename(src, dst)
    except OSError as e:
        raise OSError("Could not rename %s -> %s: %s" % (src, dst, e))


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    ext = args.ext.lstrip('.')  # tolerate accidental leading dot
    target_dir = os.path.abspath(args.target_dir)

    if not os.path.isdir(target_dir):
        parser.error("Target directory does not exist or is not a directory: %s" % target_dir)

    pat = compile_pattern(ext, args.ignore_case)

    total_examined = 0
    total_matched = 0
    total_renamed = 0
    total_skipped = 0

    log("Walking (top-down) under: %s" % target_dir, args.quiet, args.verbose, level=0)

    for root, _dirs, files in os.walk(target_dir, topdown=True):
        for fname in files:
            total_examined += 1
            plan = plan_new_name(fname, ext, pat)
            if not plan:
                continue
            total_matched += 1
            old_name, new_name = plan

            src = os.path.join(root, old_name)
            dst = os.path.join(root, new_name)

            log("Match: %s  ->  %s" % (old_name, new_name), args.quiet, args.verbose, level=0)

            try:
                rename_file(src, dst, dry_run=args.dry_run, overwrite=args.overwrite)
                total_renamed += 1
            except OSError as e:
                total_skipped += 1
                sys.stderr.write("WARNING: %s\n" % (e,))
                sys.stderr.flush()

    if not args.quiet:
        sys.stdout.write(
            "\nSummary: examined=%d, matched=%d, renamed=%d, skipped=%d\n" % (
                total_examined, total_matched, total_renamed, total_skipped
            )
        )
        sys.stdout.flush()

    return 0 if total_skipped == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
