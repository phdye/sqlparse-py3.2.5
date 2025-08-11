sweet — here’s a **complete YAML spec** plus **clear, step‑by‑step directions** for implementing an sqlparse-powered SQL/PL‑SQL formatter that feels like clang‑format.

# YAML schema (v1)

```yaml
# sqlformat.yaml — versioned, portable config for SQL + procedural SQL
version: 1

dialect:
  mode: ansi            # ansi | postgres | mysql | tsql | oracle | sqlite | snowflake | bigquery
  strict_keywords: true # if true, only dialect keywords get keyword casing

layout:
  column_limit: 100           # hard wrap column
  indent_width: 2             # spaces per indent
  continuation_indent: 4      # extra indent for wrapped lines
  use_tab: never              # never | for_indent | always
  newline_at_eof: true

spacing:
  spaces_in_parens: false
  spaces_in_brackets: false     # T‑SQL [ident]
  space_before_call_paren: false
  space_around_operators: true  # = <> <= >= + - * / || AND OR, etc.
  compact_bool_not: true        # NOT x -> NOT x (true) vs NOT  x (false)

keywords:
  case: upper          # upper | lower | capitalize
  reserved_only: true  # if true, only reserved keywords get cased; functions/udfs preserved

identifiers:
  case: preserve       # upper | lower | capitalize | preserve
  quote_style: preserve  # preserve | double | single | backtick | bracket (dialect-aware)
  keep_quoted_case: true  # quoted identifiers keep their original case

lists:
  bin_pack: false            # if wrap needed, put one item per line
  align_after_open_paren: true
  break_after_comma: true    # vs break_before_comma (SQL allows leading commas; see below)
  leading_commas: false      # experimental: use leading commas when wrapping
  trailing_comma_in_select: false  # no-op for SQL; kept to mirror clang‑format knobs
  wrap_after: auto           # auto | N (int). If auto, use column_limit

clauses:
  # How to break the major clauses once line length is exceeded
  break:
    select: after            # before | after | inline
    from:   after
    where:  after
    group_by: after
    having: after
    order_by: after
    window: after            # OVER (...)
    join:   after            # JOIN placement policy (see joins below)
    on:     after
    with:   after            # WITH cte AS (...)
    values: after
  blank_lines:
    before_with: 0           # blank lines to insert before section
    before_create: 0
    before_block: 0          # procedural BEGIN/END blocks

joins:
  join_on_new_line: true     # put JOIN on new line (if wrapping starts)
  align_on_under_join: true  # ON aligned under J of JOIN
  prefer_explicit: false     # (formatting only) warn when using old-style join commas

predicates:
  layout: one_per_line       # compact | one_per_line | heuristic
  # heuristic = keep short chains inline; break long ones by AND/OR groups

case_expr:
  indent_when_then: true
  align_then: true           # align THEN with WHEN for columnar look
  end_align_with_case: true

cte:
  one_per_line: true         # WITH a AS (...), b AS (...)
  blank_line_between: false
  trailing_comma_style: trailing  # trailing | leading (leading comma style for CTEs)

subqueries:
  open_paren_same_line: true
  body_indent: plus_one      # under_open | plus_one
  close_paren_align_with_open: true
  prefer_keyword_on_newline: true  # e.g., WHERE ( \n   SELECT ... )

blocks:   # PL/pgSQL, T‑SQL, PL/SQL
  begin_same_line: true      # e.g., IF ... THEN BEGIN
  end_own_line: true
  align_end_with_opener: true
  label_column: 0            # keep <<label>> at column 0

declarations:
  one_per_line: true         # DECLARE section items
  align_types: true          # align var type column
  align_assignment: true     # align := or = in DECLARE section

create_table:
  align_columns: true        # align name, type, constraints
  comma_last: true           # trailing comma style
  one_column_per_line: true

comments:
  reflow_block_comments: true
  keep_trailing_line_comment_with_code: true
  pragma_freeze_directives:
    - '/* format: off */'
    - '/* format: on */'
    - '-- format: off'
    - '-- format: on'
  preserve_comment_position: true

penalties:                   # cost model (advanced users)
  break_after_select: 50
  keep_short_select_items_together: 30
  break_before_first_select_item: 10
  break_before_from: 25
  break_before_where: 25
  break_in_boolean_chain: 5
  over_column_limit: 1000    # strong push to wrap

safety:
  no_reorder_semantics: true # formatter must not reorder tokens with potential semantic effect
  dry_run: false             # if true, only report diffs, don’t change
  idempotent_check: true     # assert formatting(command(output)) == output

experimental:
  sort_ctes: off             # off | alpha | by_dependency (non‑default, risky)
  sort_columns: off          # off | alpha (risky; keep off)
```

---

# Example style profiles

**Google‑ish SQL**

```yaml
version: 1
dialect: { mode: ansi, strict_keywords: true }
layout: { column_limit: 100, indent_width: 2, continuation_indent: 4, use_tab: never }
keywords: { case: upper, reserved_only: true }
identifiers: { case: preserve, quote_style: preserve, keep_quoted_case: true }
lists: { bin_pack: false, align_after_open_paren: true, break_after_comma: true }
clauses: { break: { select: after, from: after, where: after, group_by: after, order_by: after } }
joins: { join_on_new_line: true, align_on_under_join: true }
predicates: { layout: one_per_line }
case_expr: { indent_when_then: true, align_then: true, end_align_with_case: true }
cte: { one_per_line: true, blank_line_between: false, trailing_comma_style: trailing }
subqueries: { open_paren_same_line: true, body_indent: plus_one, close_paren_align_with_open: true }
blocks: { begin_same_line: true, end_own_line: true, align_end_with_opener: true, label_column: 0 }
comments: { reflow_block_comments: true, keep_trailing_line_comment_with_code: true }
safety: { no_reorder_semantics: true, idempotent_check: true }
```

**Compact analytics**

```yaml
version: 1
dialect: { mode: bigquery }
layout: { column_limit: 120, indent_width: 2, continuation_indent: 2 }
lists: { bin_pack: true, break_after_comma: true, align_after_open_paren: false }
predicates: { layout: heuristic }
joins: { join_on_new_line: false, align_on_under_join: false }
```

---

# Minimal valid file

```yaml
version: 1
dialect: { mode: ansi }
```

All unspecified fields must fall back to the defaults shown in the full schema above.

---

# Directives for “ChatGPT Codex” (implementation plan)

## 1) Parsing and tokenization

* Use `sqlparse` to lex statements into tokens.
* Augment with a **dialect layer** that tags dialect‑specific keywords (`JOIN`, `QUALIFY`, `CONNECT BY`, `LIMIT`, `TOP`, bracketed identifiers).
* Build a light AST for:

  * Statement
  * Clauses: WITH, SELECT, FROM, WHERE, GROUP BY, HAVING, WINDOW, ORDER BY, LIMIT/OFFSET, VALUES, INSERT …, UPDATE …, DELETE …
  * Lists: select items, function args, column defs, CTEs
  * Blocks: `BEGIN … END`, `IF/ELSE`, `LOOP`, `EXCEPTION`, `TRY/CATCH`
  * Expressions: boolean chains (AND/OR), CASE expressions
  * Comments (line and block), with attachment points to nearest tokens

## 2) Formatting pipeline

**Two passes**:

1. **Normalization pass**

   * Keyword/identifier case according to `keywords.case`, `identifiers.case`.
   * Spacing normalization (operators, parentheses, brackets).
   * Quote normalization per `identifiers.quote_style` (dialect‑aware).
   * Do **not** change token order (respect `safety.no_reorder_semantics`).

2. **Layout pass**

   * Compute breakpoints per `layout.column_limit` using a cost model with `penalties`.
   * Apply clause break policy (`clauses.break`), list wrapping (`lists.*`), join alignment, predicate layout, CASE layout, subquery indentation, CTE spacing.
   * Perform indentation: base indent = `indent_width`; continuation = base + `continuation_indent`.
   * Ensure `newline_at_eof`.
   * Respect **freeze pragmas** in `comments.pragma_freeze_directives`: between “off” and “on” keep raw text.

**Idempotence**: if `safety.idempotent_check` true, re-run on output and assert byte‑equality; otherwise emit a diagnostic.

## 3) Wrapping & alignment rules (essentials)

* **Clause heads**: treat “SELECT”, “FROM”, “WHERE”, … as breakable heads. If line would exceed `column_limit`, apply policy:

  * `after`: keep keyword at line start; wrap content to next line and indent by `continuation_indent`.
  * `before`: move keyword to new line (rare for SQL).
  * `inline`: try keeping clause head and short content inline; otherwise degrade to `after`.

* **Lists**:

  * If no wrap required: keep inline (subject to `bin_pack`).
  * If wrap required:

    * `bin_pack=false`: one item per line; place comma as per `break_after_comma` or `leading_commas`.
    * `align_after_open_paren=true`: indent such that items align with first element after `(` when inside parentheses; elsewhere, align under clause body.

* **Joins**:

  * If `join_on_new_line=true` and wrapping started, start `JOIN` on a new line.
  * If `align_on_under_join=true`, align `ON` under the J of `JOIN`.

* **Predicates**:

  * `one_per_line`: break before each `AND/OR`; indent continued predicates.
  * `compact`: keep chain inline unless `column_limit` forces wrap; when wrapping, break *before* operator so operator starts the line (readability win).
  * `heuristic`: if the chain length <= 2 and short, keep inline; else fall back to `one_per_line`.

* **CASE**:

  * `indent_when_then=true`: each WHEN, THEN, ELSE on its own line indented by one level from CASE.
  * `align_then=true`: align THEN with WHEN by extra spaces.
  * `end_align_with_case=true`: `END` aligned with `CASE`.

* **Subqueries**:

  * If multiline: open paren on same line (`open_paren_same_line=true`), body starts next line, indented by `plus_one` or `under_open`.
  * Close paren: align to open paren column if `close_paren_align_with_open`.

* **CTEs**:

  * `one_per_line=true`: each `name AS (...)` on its own line, commas at end (`trailing`), or start if `leading`.
  * Optional blank line between per `cte.blank_line_between`.

* **CREATE TABLE**:

  * `one_column_per_line=true`: each column def per line.
  * `align_columns=true`: align type and constraint columns in a simple two/three‑column table layout.
  * Trailing commas per `comma_last`.

## 4) Spacing rules (quick table)

| Construct         | Rule                                                                  |
| ----------------- | --------------------------------------------------------------------- |
| Function call     | `name(args)` unless `spacing.space_before_call_paren=true`            |
| Unary NOT         | `NOT expr` with single space if `compact_bool_not`                    |
| Binary ops        | One space around if `space_around_operators`                          |
| Parens/brackets   | Inner spaces controlled by `spaces_in_parens`, `spaces_in_brackets`   |
| Trailing comments | Keep on same line; if line wraps, move code and keep comment attached |

## 5) Safety & semantics

* **Never reorder** columns, predicates, CTEs, JOINs, or `SELECT DISTINCT` position.
* **Never split** string literals unless a dialect‑safe concatenation is guaranteed; default `false`.
* **Never introduce** or remove parentheses that could change precedence.
* Provide a `dry_run` diff mode that reports would‑be changes.

## 6) CLI interop (sqlparse/sqlformat)

* Map existing flags:

  * `--keywords` ↔ `keywords.case`
  * `--identifiers` ↔ `identifiers.case`
  * `--reindent` ↔ enable layout pass with defaults
  * `--indent_width` ↔ `layout.indent_width`
  * Add new flag: `--config sqlformat.yaml` (this file), and `--dialect`.
* Default behavior: if a yaml file present in CWD or ancestor (`sqlformat.yaml`), use it; otherwise defaults.

## 7) Tests (fixtures & golden files)

**Create these fixture sets (input → expected):**

1. **SELECT + joins + predicates**

* Short inline, long wraps, ON alignment, `one_per_line` vs `compact`.

2. **WITH CTEs**

* Multiple CTEs, trailing vs leading comma style, blank lines between.

3. **Subqueries**

* Nested subqueries, `under_open` vs `plus_one` indentation.

4. **CASE expressions**

* Searched and simple CASE, THEN alignment, END alignment.

5. **CREATE TABLE**

* Column alignment, constraints, commas, comments per column.

6. **Procedural blocks**

* PL/pgSQL `BEGIN … EXCEPTION … END`, T‑SQL `BEGIN TRY … END CATCH`, Oracle labels, DECLARE alignment.

7. **Comments & pragmas**

* Reflow block comments, preserve line comments, freeze regions.

8. **Dialect edge cases**

* BigQuery `QUALIFY`, Snowflake `IFF()`, T‑SQL `[brackets]`, Oracle quoted identifiers.

9. **Idempotence**

* Reformat expected output again → identical.

**Test harness**:

* Each test folder contains `input.sql`, `style.yaml` (optional), `expected.sql`.
* Run all dialects where applicable.
* Include a `max_line_length` torture test to exercise wrapping penalties.

## 8) Error reporting

* If pragma freeze region is unbalanced, emit a non‑fatal warning and skip formatting until EOF.
* If yaml `version` is unsupported, fail with actionable message.
* If `experimental.*` is enabled, print a “semantics risk” banner in dry‑run output.

## 9) Performance notes

* Batch tokenize once per statement; avoid quadratic rescans.
* Memoize column width computations for alignment blocks.
* Provide an opt‑in `--fast` that disables alignment passes for large files.

---

# Worked example (input → output)

**Input**

```sql
with a as(select 1 x,2 y), b as ( select x, y from a where x=1 and y=2 or x=3)
select a.x,b.y, coalesce(null, 0) z from a join b on a.x=b.x and a.y=b.y where (a.x+b.y)>10 and (a.y<100 or b.y is null);
```

**Config (excerpt)**

```yaml
version: 1
keywords: { case: upper }
predicates: { layout: one_per_line }
lists: { bin_pack: false, break_after_comma: true }
joins: { join_on_new_line: true, align_on_under_join: true }
layout: { column_limit: 80, indent_width: 2, continuation_indent: 4 }
cte: { one_per_line: true, trailing_comma_style: trailing }
```

**Expected**

```sql
WITH
  a AS (
    SELECT
      1 AS x,
      2 AS y
  ),
  b AS (
    SELECT
      x,
      y
    FROM
      a
    WHERE
      x = 1
      AND y = 2
      OR x = 3
  )
SELECT
  a.x,
  b.y,
  COALESCE(NULL, 0) AS z
FROM
  a
  JOIN b
    ON a.x = b.x
    AND a.y = b.y
WHERE
  (a.x + b.y) > 10
  AND (
    a.y < 100
    OR b.y IS NULL
  );
```

---

# Integration checklist (TL;DR for implementers)

1. Load YAML → validate (`version==1`, fill defaults).
2. Tokenize with `sqlparse`; augment tokens with dialect tags.
3. Normalize: casing, spaces, quotes.
4. Build clause/list/block scaffolding (no heavy AST required).
5. Compute soft breakpoints and costs; apply penalties; wrap.
6. Indent + align per config.
7. Respect comment pragmas (freeze).
8. Emit text; ensure EOF newline; run idempotence check if enabled.
9. Provide CLI flags `--config`, `--dialect`, `--dry-run`, `--fast`.
10. Run the golden tests; fail build if any differ.

If you want, I can generate a starter repository layout (tests + harness + reference implementations for the most common rules) next.
