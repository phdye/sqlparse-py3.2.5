# SqlParse Processing Pipeline

This document describes how sqlparse transforms raw SQL text into formatted
statements.  It follows the journey from tokenization through the filter stack
and optional plug‑in hooks to the final serialized output.

## 1. Tokenization and Initial Setup

1. **Tokenize** – `lexer.tokenize(sql, encoding, dialect)` converts the input
   string into a stream of `(ttype, value)` tuples.  The `FilterStack` manages
   the dialect and optional semicolon stripping during construction.
2. **Build the stack** – `build_filter_stack` populates a `FilterStack` based on
   formatting options and registered plug‑ins.  Any option requiring structural
   analysis enables grouping automatically.

## 2. Filter Stack Processing

`FilterStack` maintains three ordered lists that stream tokens and statements
through the pipeline:

* **`preprocess`** – token‑level generators that run before statement
  splitting.
* **`stmtprocess`** – per‑statement filters that mutate the token tree after
  optional grouping.
* **`postprocess`** – final transforms such as serialization.

During `run()`, the stack sequentially applies each list: token filters,
`StatementSplitter`, grouping, statement filters, then post‑processing filters
before yielding each result.

## 3. Plug‑in Integration

sqlparse exposes a lightweight registry so independent modules can contribute
formatting features without touching shared code:

1. **Registration & discovery** – plug‑ins register under a unique name via
   `register_plugin` and are discovered lazily from bundled modules or entry
   points.
2. **Stack insertion** – `build_filter_stack` iterates over available plug‑ins
   and, when enabled via options, wraps each plug‑in in a `_PluginFilter`.  The
   wrapper is inserted at the start of `preprocess` and again at the end of
   `postprocess` so plug‑ins can participate both before and after the core
   formatter.
3. **Optional final pass** – after the stack yields formatted SQL, any enabled
   plug‑ins are run a third time on the final string to support full‑text
   transforms.

### Writing phase‑aware plug‑ins

`_PluginFilter` invokes a plug‑in's `format(stream, options)` in three
contexts, and plug‑ins are expected to inspect the type of `stream` so they act
only in the phases they care about:

* **Preprocess** – `stream` is a generator of `(ttype, value)` tuples.  A
  plug‑in that rewrites lexical tokens should iterate over the generator and
  yield new tuples.  If the plug‑in targets later phases, simply return the
  input generator unchanged.
* **Postprocess** – `stream` is a `Statement` instance representing a token
  tree.  Plug‑ins that manipulate the structure can mutate the tree and return
  it.  To skip this phase, detect the presence of a `token_next` attribute and
  immediately return the `Statement` unmodified.
* **Final pass** – `stream` is a string containing the fully formatted SQL.
  Plug‑ins that work on complete text can transform and return this string.
  Plug‑ins confined to earlier phases should check for `isinstance(stream, str)`
  and return the string unchanged.

By guarding on the received object type (or on plug‑in specific options), a
plug‑in avoids accidentally re‑running in stages where it is not applicable,
preventing redundant work or recursive invocation.

Plug‑ins that internally call `sqlparse.format()` should avoid re‑entering the
plug‑in system to prevent recursive invocation.

## 4. High‑level APIs

* **`parse` / `parsestream`** – build a stack configured for parsing and yield
  `Statement` objects.
* **`format`** – build a stack with formatting filters and return a formatted
  string, optionally running enabled plug‑ins again on the final output.
* **`split`** – return SQL strings by tokenizing and splitting without running
  statement filters.

## 5. End‑to‑End Flow

1. Tokenize the SQL input.
2. Run `preprocess` token filters.
3. Split into statements.
4. Optionally group tokens into hierarchical structures.
5. Apply `stmtprocess` filters.
6. Apply `postprocess` filters and serialize.
7. Perform any plug‑in post‑processing passes.

This modular pipeline allows sqlparse to be easily extended and configured while
keeping the core processing predictable and maintainable.
