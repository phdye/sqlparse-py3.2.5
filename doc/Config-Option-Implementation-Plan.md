# Config Option Implementation Plan

This plan outlines the remaining configuration options from
`issue/clang-style-parameters.md` that are not yet implemented in sqlparse.
To enable multiple contributors to work concurrently, each phase is scoped to a
standalone formatter plugin. Plugins are registered via
`sqlparse/plugins/__init__.py` (see `Formatting-Plugin-Architecture.md`) so that
teams can implement phases in parallel without touching shared modules. Each
phase targets a body of work achievable within a single development session.

## Phase 1: Dialect strictness and continuation indent
- Deliverable plugin: `sqlparse/plugins/dialect_strictness.py`
- Support `dialect.strict_keywords` to control keyword casing scope.
- Implement `layout.continuation_indent` for wrapped line indentation.
- Update configuration parsing, formatter behavior, and tests.

## Phase 2: Spacing and casing enhancements
- Deliverable plugin: `sqlparse/plugins/spacing_casing.py`
- Add `spacing.compact_bool_not` to control spacing after `NOT`.
- Implement `keywords.reserved_only` to restrict keyword casing to reserved terms.
- Add identifier options `identifiers.quote_style` and `identifiers.keep_quoted_case`.
- Extend parser, formatter rules, and tests.

## Phase 3: List formatting controls
- Deliverable plugin: `sqlparse/plugins/list_controls.py`
- Implement `lists.bin_pack`, `lists.align_after_open_paren`, and `lists.break_after_comma`.
- Map `lists.leading_commas` and `lists.wrap_after` to existing comma and wrap mechanics.
- Support `lists.trailing_comma_in_select` for parity with other formatters.
- Cover parsing, formatting logic, and tests.

## Phase 4: Clause breaks and blank lines
- Deliverable plugin: `sqlparse/plugins/clauses.py`
- Implement `clauses.break.*` policies for major clauses.
- Add `clauses.blank_lines.*` options to insert blank lines before sections.
- Update formatter to honor these rules and add tests.

## Phase 5: Join handling
- Deliverable plugin: `sqlparse/plugins/joins.py`
- Support `joins.join_on_new_line` and `joins.align_on_under_join` for JOIN placement.
- Implement `joins.prefer_explicit` to warn on comma joins during formatting.
- Adjust parser and formatter; create tests.

## Phase 6: Predicate layout
- Deliverable plugin: `sqlparse/plugins/predicates.py`
- Implement `predicates.layout` options (`compact`, `one_per_line`, `heuristic`).
- Add logic for breaking boolean chains accordingly and test coverage.

## Phase 7: CASE expression formatting
- Deliverable plugin: `sqlparse/plugins/case_expr.py`
- Support `case_expr.indent_when_then`, `case_expr.align_then`, and `case_expr.end_align_with_case`.
- Update formatter to structure CASE blocks and add tests.

## Phase 8: Common table expressions
- Deliverable plugin: `sqlparse/plugins/cte.py`
- Implement `cte.one_per_line`, `cte.blank_line_between`, and `cte.trailing_comma_style`.
- Enhance formatting of WITH clauses and provide tests.

## Phase 9: Subquery formatting
- Deliverable plugin: `sqlparse/plugins/subqueries.py`
- Support `subqueries.open_paren_same_line`, `subqueries.body_indent`, `subqueries.close_paren_align_with_open`, and `subqueries.prefer_keyword_on_newline`.
- Modify formatter and extend tests.

## Phase 10: Blocks and declarations
- Deliverable plugin: `sqlparse/plugins/blocks.py`
- Implement block options `blocks.begin_same_line`, `blocks.end_own_line`, `blocks.align_end_with_opener`, and `blocks.label_column`.
- Add declaration controls `declarations.one_per_line`, `declarations.align_types`, and `declarations.align_assignment`.
- Update formatter and tests accordingly.

## Phase 11: CREATE TABLE formatting
- Deliverable plugin: `sqlparse/plugins/create_table.py`
- Support `create_table.align_columns`, `create_table.comma_last`, and `create_table.one_column_per_line`.
- Add table-definition specific alignment and tests.

## Phase 12: Comment and pragma handling
- Deliverable plugin: `sqlparse/plugins/comments.py`
- Implement `comments.reflow_block_comments` and `comments.keep_trailing_line_comment_with_code`.
- Support `comments.pragma_freeze_directives` and `comments.preserve_comment_position`.
- Update parsing, formatting, and tests to respect comment controls.

## Phase 13: Penalty tuning
- Deliverable plugin: `sqlparse/plugins/penalties.py`
- Add support for penalty options (`penalties.break_after_select`, `penalties.keep_short_select_items_together`, `penalties.break_before_first_select_item`, `penalties.break_before_from`, `penalties.break_before_where`, `penalties.break_in_boolean_chain`, `penalties.over_column_limit`).
- Integrate penalties into cost model and provide tests demonstrating wrap behavior.

---

Each phase should add its formatter logic as a plugin in `sqlparse/plugins`,
update documentation, and ensure compatibility with Python 3.2.5, Cygwin
1.7.29, and Oracle 12c environments.
