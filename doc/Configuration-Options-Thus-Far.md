# Configuration Options Thus Far

## dialect
- mode: implemented
- strict_keywords: not implemented

## layout
- column_limit: implemented
- indent_width: implemented
- continuation_indent: not implemented
- use_tab: implemented
- newline_at_eof: implemented

## spacing
- spaces_in_parens: implemented
- spaces_in_brackets: implemented
- space_before_call_paren: implemented
- space_around_operators: implemented
- compact_bool_not: not implemented

## keywords
- case: implemented
- reserved_only: not implemented

## identifiers
- case: implemented
- quote_style: not implemented
- keep_quoted_case: not implemented

## lists
- bin_pack: not implemented
- align_after_open_paren: not implemented
- break_after_comma: not implemented
- leading_commas: not implemented
- trailing_comma_in_select: not implemented
- wrap_after: not implemented

## clauses
- break.select: not implemented
- break.from: not implemented
- break.where: not implemented
- break.group_by: not implemented
- break.having: not implemented
- break.order_by: not implemented
- break.window: not implemented
- break.join: not implemented
- break.on: not implemented
- break.with: not implemented
- break.values: not implemented
- blank_lines.before_with: not implemented
- blank_lines.before_create: not implemented
- blank_lines.before_block: not implemented

## joins
- join_on_new_line: not implemented
- align_on_under_join: not implemented
- prefer_explicit: not implemented

## predicates
- layout: not implemented

## case_expr
- indent_when_then: not implemented
- align_then: not implemented
- end_align_with_case: not implemented

## cte
- one_per_line: not implemented
- blank_line_between: not implemented
- trailing_comma_style: not implemented

## subqueries
- open_paren_same_line: not implemented
- body_indent: not implemented
- close_paren_align_with_open: not implemented
- prefer_keyword_on_newline: not implemented

## blocks
- begin_same_line: not implemented
- end_own_line: not implemented
- align_end_with_opener: not implemented
- label_column: not implemented

## declarations
- one_per_line: not implemented
- align_types: not implemented
- align_assignment: not implemented

## create_table
- align_columns: not implemented
- comma_last: not implemented
- one_column_per_line: not implemented

## comments
- reflow_block_comments: not implemented
- keep_trailing_line_comment_with_code: not implemented
- pragma_freeze_directives: not implemented
- preserve_comment_position: not implemented

## penalties
- break_after_select: implemented
- keep_short_select_items_together: implemented
- break_before_first_select_item: implemented
- break_before_from: implemented
- break_before_where: implemented
- break_in_boolean_chain: implemented
- over_column_limit: not implemented

## safety
- no_reorder_semantics: not implemented
- dry_run: not implemented
- idempotent_check: not implemented

## experimental
- sort_ctes: not implemented
- sort_columns: not implemented
