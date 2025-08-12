Got it — here’s a tight, implementation‑ready spec for the **first set of options** we discussed, plus **`align_longest_keyword`**. I’ve grouped them by feature area and included types, defaults, behavior, precedence, and examples.

# Scope

These options control:

1. Identifier list layout (e.g., `SELECT a, b, c`)
2. Width rules specific to identifier lists
3. Clause keyword alignment (e.g., `SELECT/INTO/FROM/WHERE`)
4. Where identifiers start relative to the keyword line
5. A new cross‑keyword alignment enhancer: `align_longest_keyword`

All keys are lower\_snake\_case. Unknown keys MUST be ignored (forward compatibility). Invalid values MUST fall back to defaults and emit a formatter warning.

---

# 1) Identifier list layout

## id\_layout

* **Type:** enum
* **Allowed:** `single_line` | `vertical` | `hanging` | `wrap_by_comma` | `grid` | `preserve_input_breaks`
* **Default:** `single_line`
* **Behavior:**

  * `single_line`: Keep all identifiers on one line if width allows; otherwise wrap (see §2 for wrapping).
  * `vertical`: One identifier per line after the first line break opportunity.
  * `hanging`: First identifier shares the keyword line; subsequent identifiers wrap one-per-line using a hanging indent (§4).
  * `wrap_by_comma`: Break only at commas; multiple identifiers can share wrapped lines (not strictly one-per-line).
  * `grid`: Pack identifiers into rows trying to keep visually even column widths; commas appear at natural positions; respects width.
  * `preserve_input_breaks`: Maintain author’s line breaks; only reflow if a line exceeds configured width (see §2).
* **Notes:** Actual wrap points and indentation on wrap are further governed by §2 and §4.

## break\_after\_n

* **Type:** integer ≥ 1
* **Default:** unset (disabled)
* **Behavior:** If set and the identifier count ≥ `break_after_n`, force a vertical-style layout (like `vertical`) regardless of `id_layout`.

## group\_by\_alias

* **Type:** boolean
* **Default:** `false`
* **Behavior:** Prefer breaking *before* identifiers that introduce `AS alias` (or implicit alias), so alias groups begin on new lines. Applies to `wrap_by_comma`, `hanging`, and `grid`.

---

# 2) Width rules for identifier lines

## id\_line\_width

* **Type:** integer ≥ 20
* **Default:** unset (use global `line_width`)
* **Behavior:** Overrides global line width for *identifier list* lines only (SELECT/INTO column lists, function arg lists if desired). When unset, use global `line_width`.

## soft\_wrap\_ids

* **Type:** boolean
* **Default:** `true`
* **Behavior:** When `true`, allow a slight overrun (≤ 10% of the chosen width) before wrapping identifier lists; when `false`, wrap strictly at or before `id_line_width`/`line_width`.

## id\_count\_limit

* **Type:** integer ≥ 1
* **Default:** unset (disabled)
* **Behavior:** When identifier count exceeds this number, force wrapping (according to `id_layout`) regardless of measured width.

## measure\_with\_alias

* **Type:** boolean
* **Default:** `true`
* **Behavior:** When measuring width, include `AS alias` (or implicit alias) in the length calculation. If `false`, measure only the bare identifier token.

## continuation\_indent\_mult

* **Type:** number (float) ≥ 0.0
* **Default:** `1.0`
* **Behavior:** Multiplier applied to the base indent for wrapped identifier lines (see §4). E.g., base indent 4, mult 1.5 → 6 spaces.

## align\_comma\_on\_wrap

* **Type:** enum
* **Allowed:** `after` | `before`
* **Default:** `after`
* **Behavior:** Trailing-comma (`after`) vs leading-comma (`before`) style on wrapped lines. Only meaningful when wrapping occurs.

---

# 3) Keyword alignment

## keyword\_align

* **Type:** enum
* **Allowed:** `left` | `right` | `center` | `none`
* **Default:** `left`
* **Behavior:** Alignment of **clause keywords** (e.g., `SELECT`, `INTO`, `FROM`, `WHERE`) within their alignment scope (§3.2). Alignment sets a “gutter” column target for the keyword text.

## align\_scope

* **Type:** enum
* **Allowed:** `statement` | `block`
* **Default:** `statement`
* **Behavior:**

  * `statement`: Only align keywords within a single SQL statement.
  * `block`: Align keywords across a contiguous block (e.g., all statements under the same `EXEC SQL` header).
* **Note:** Scope also affects how `align_longest_keyword` computes the max length (see §5).

## keyword\_gutter\_col

* **Type:** integer ≥ 0 | unset
* **Default:** unset
* **Behavior:** When set, the **right edge** of the keyword (for `right`), **left edge** (for `left`), or **center** is placed at this absolute column (0-based). Overrides auto-calculated gutters and `align_longest_keyword`.

## pad\_after\_keyword

* **Type:** integer ≥ 0
* **Default:** `2`
* **Behavior:** Fixed spaces to insert after the keyword before non-keyword tokens (e.g., before the first identifier). Independent of indent level; applies even when `keyword_align = none`.

## align\_clause\_groups

* **Type:** enum | list
* **Allowed:** `major` | `all` | `custom:<comma-separated-keywords>`
* **Default:** `major`
* **Behavior:**

  * `major`: Align only major clauses — `SELECT`, `INTO`, `FROM`, `WHERE`, `GROUP BY`, `HAVING`, `ORDER BY`, `JOIN` family.
  * `all`: Align every recognized clause keyword (including `AND`, `OR`, `ON`, etc.).
  * `custom:<...>`: Align exactly the listed keywords (case-insensitive), e.g., `custom:select,into,from,where`.

---

# 4) Where identifiers begin (relative to the keyword line)

## id\_start

* **Type:** enum
* **Allowed:** `next_indent` | `after_gutter` | `after_keyword_plus_n`
* **Default:** `after_keyword_plus_n`
* **Behavior:**

  * `next_indent`: Start identifiers at the next standard indent level after the keyword line.
  * `after_gutter`: Start at the column immediately **after** the computed keyword gutter (post-alignment).
  * `after_keyword_plus_n`: Start `n` spaces after the end of the keyword token (see `id_start_n`).

## id\_start\_n

* **Type:** integer ≥ 0
* **Default:** `2`
* **Behavior:** Number of spaces used by `after_keyword_plus_n`.

## hanging\_under\_first\_token

* **Type:** boolean
* **Default:** `false`
* **Behavior:** On wrap, align subsequent lines under the first *non-keyword* token (e.g., under the first identifier). Applies to `hanging`, `wrap_by_comma`, `grid`.

## paren\_anchor

* **Type:** boolean
* **Default:** `true`
* **Behavior:** If a list is parenthesized, align wrapped lines under the opening `(` when this produces a more stable anchor than the keyword gutter.

## continuation\_indent

* **Type:** integer ≥ 0
* **Default:** unset
* **Behavior:** Explicit number of spaces for continuation lines (overrides `continuation_indent_mult`). If unset, use the product of base indent × `continuation_indent_mult`.

## align\_on\_comma

* **Type:** boolean
* **Default:** `false`
* **Behavior:** When wrapping by commas, align subsequent lines under the comma position of the previous line. Only applies when `align_comma_on_wrap = after`.

---

# 5) Cross‑keyword right‑edge alignment

## align\_longest\_keyword

* **Type:** boolean
* **Default:** `true` **when** `keyword_align = right` **and** `keyword_gutter_col` unset; otherwise `false`
* **Behavior:** When enabled, the aligner performs a **two‑pass scan** over the alignment **scope** (§3.2) to determine the **maximum keyword length** among the clauses considered by `align_clause_groups`. It then adjusts padding so **all keyword right edges** land in the same column (i.e., “right‑gutter” alignment).
* **Precedence:**

  * If `keyword_gutter_col` is set, it **overrides** `align_longest_keyword`.
  * If `keyword_align ≠ right`, this option is **ignored** (no effect on `left`/`center`/`none`).
  * If `align_scope = block`, the max length is computed across the entire block; if `statement`, per statement.
* **Rationale:** Makes shorter keywords (e.g., `FROM`) receive extra leading spaces so they **right‑align** with longer ones (e.g., `WHERE`) — exactly the behavior you want.

---

# Precedence & Interaction Rules (summary)

1. **Explicit gutter beats everything:** If `keyword_gutter_col` is set, it defines the anchor; `align_longest_keyword` is ignored.
2. **Right‑edge logic only when `keyword_align = right`:** Otherwise `align_longest_keyword` is ignored.
3. **Scope matters:** `align_scope` governs which keywords are included in the two‑pass max-length computation.
4. **Clause inclusion:** `align_clause_groups` defines which keywords participate in alignment (and thus the max).
5. **Identifier placement:** `id_start` (and `id_start_n`) determines where the first identifier begins; wraps then use `continuation_indent` or `continuation_indent_mult`, modulated by `hanging_under_first_token`, `paren_anchor`, and `align_on_comma`.
6. **Wrapping choice:** `id_layout` chooses the general style; `id_line_width`, `soft_wrap_ids`, `id_count_limit`, and `break_after_n` force or relax wrapping.

---

# Worked Example (matches your target style)

**Config**

```ini
# Keyword alignment
keyword_align = right
align_scope = statement
align_clause_groups = major
# Let the aligner decide a shared right edge:
align_longest_keyword = true
pad_after_keyword = 2

# Identifier list layout & widths
id_layout = hanging
id_line_width = 60
soft_wrap_ids = true
id_count_limit = 9999
measure_with_alias = true

# Where identifiers begin
id_start = after_keyword_plus_n
id_start_n = 2
continuation_indent_mult = 1.0
paren_anchor = true
align_comma_on_wrap = after
```

**Input**

```
EXEC SQL
SELECT first_name,
       last_name
INTO :firstName,
     :lastName
FROM employees
WHERE
  employee_id = :id;
```

**Output**

```
EXEC SQL
    SELECT  first_name, last_name
      INTO  :firstName, :lastName 
      FROM  employees 
      WHERE  employee_id = :id;
```

Why this works:

* `keyword_align = right` + `align_longest_keyword = true` → all clause keywords share a common right edge; since `WHERE` is longer than `FROM`, `FROM` receives one extra leading space, producing the stacked look you expect.
* `pad_after_keyword = 2` → two spaces between the keyword and the first non‑keyword token.
* `id_layout = hanging` + `id_start = after_keyword_plus_n` → first identifier stays on the same line, subsequent wraps (if any) hang underneath according to continuation indent (not used here since width fits).

---

# Validation & Errors

* If `id_layout = grid` but `id_line_width` < 20, fall back to `wrap_by_comma` with a warning.
* If `keyword_gutter_col` is smaller than the base indent already consumed, clamp to base indent (no negative backspacing).
* If `align_clause_groups = custom:<…>` contains unknown tokens, ignore those tokens and warn.

---

# Implementation Notes

* **Two‑pass keyword scan:** Required when `align_longest_keyword = true` and `keyword_gutter_col` unset. Pass 1: collect candidate keywords per `align_scope` and `align_clause_groups`, compute `max_len`. Pass 2: emit, padding so each keyword’s right edge is aligned to the same column (relative to the chosen base indent for the statement/block).
* **Determinism:** All alignment computations should be pure functions of the token stream + config. Avoid layout depending on incidental whitespace in the input unless `preserve_input_breaks` is chosen.
* **Extensibility:** Keep the set of “major clauses” configurable in code so vendors can add dialect keywords without changing the spec.

---

If you want, I can turn this into a concrete `issue/example.sqlparse` (INI or toml) and note any minimal formatter hooks you’d need to add (e.g., the two‑pass keyword scan and the `grid` packer).
