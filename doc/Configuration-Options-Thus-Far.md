# Configuration Options Thus Far

## dialect
- mode: implemented
- strict_keywords: implemented

## layout
- column_limit: implemented
- indent_width: implemented
- continuation_indent: implemented
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
- bin_pack: implemented
- align_after_open_paren: implemented
- break_after_comma: implemented
- leading_commas: implemented
- trailing_comma_in_select: implemented
- wrap_after: implemented

## clauses
- break.select: implemented
- break.from: implemented
- break.where: implemented
- break.group_by: implemented
- break.having: implemented
- break.order_by: implemented
- break.window: implemented
- break.join: implemented
- break.on: implemented
- break.with: implemented
- break.values: implemented
- blank_lines.before_with: implemented
- blank_lines.before_create: implemented
- blank_lines.before_block: implemented

## joins
- join_on_new_line: implemented
- align_on_under_join: implemented
- prefer_explicit: implemented

## predicates
- layout: implemented

## case_expr
- indent_when_then: implemented
- align_then: implemented
- end_align_with_case: implemented

## cte
- one_per_line: implemented
- blank_line_between: implemented
- trailing_comma_style: implemented

## subqueries
- open_paren_same_line: implemented
- body_indent: implemented
- close_paren_align_with_open: implemented
- prefer_keyword_on_newline: implemented

## blocks
- begin_same_line: implemented
- end_own_line: implemented
- align_end_with_opener: implemented
- label_column: implemented

## declarations
- one_per_line: implemented
- align_types: implemented
- align_assignment: implemented

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
- break_after_select: not implemented
- keep_short_select_items_together: not implemented
- break_before_first_select_item: not implemented
- break_before_from: not implemented
- break_before_where: not implemented
- break_in_boolean_chain: not implemented
- over_column_limit: not implemented

## safety
- no_reorder_semantics: not implemented
- dry_run: not implemented
- idempotent_check: not implemented

## experimental
- sort_ctes: not implemented
- sort_columns: not implemented
