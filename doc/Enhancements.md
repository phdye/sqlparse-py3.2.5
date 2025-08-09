# Functional differences between standard and enhanced sqlparse

This document compares the standard `sqlparse` package found in `./sqlparse` with the enhanced version located at `sub/python-3.2.5-pkgs-as-installed/site-packages/sqlparse`. Differences related solely to backporting for Python 3.2.5 are ignored.

## Top-level API
- The enhanced package exposes a new `config` module and adds it to the public exports, while the standard version lacks this module.

## Configuration system
- `config.py` introduces default formatting options, predefined styles, and routines to load configuration files or inline YAML. It also supports dumping the effective configuration.

## CLI enhancements
- New command-line options `--style` and `--dump-config` allow applying preset styles, loading styles from files or inline YAML, and printing the computed configuration.
- Formatting options default to `None` so that settings from configuration files can override them. The CLI merges command-line arguments with configuration values before validating and formatting.

## Additional scripts
- The enhanced package ships a `bin` directory providing a `sqlformat` entry-point script and several Emacs helpers for formatting embedded SQL blocks.