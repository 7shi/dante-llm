"""Fix prompts in error files by replacing table columns with current source data."""

import sys
import os
import argparse
from dantetool import common


def replace_table_columns(prompt, source_table, source_columns):
    """Replace prompt table data rows with source table data.

    Args:
        prompt: Original prompt containing a table
        source_table: Source table (list of rows) with correct data
        source_columns: List of source column indices to copy from.
                       These will be written to destination columns 0, 1, 2, ... in order.

    Returns:
        Updated prompt with replaced table data
    """
    # Parse prompt table (only need header structure)
    prompt_table = common.read_table(prompt)
    if not prompt_table or len(prompt_table) < 2:
        return None

    # Keep header and separator from prompt, rebuild data from source
    new_table = [prompt_table[0], prompt_table[1]]
    num_columns = len(prompt_table[0])

    # Build data rows from source columns
    source_data = source_table[2:]
    for source_row in source_data:
        new_row = [""] * num_columns
        for dest_col, src_col in enumerate(source_columns):
            if dest_col < num_columns and src_col < len(source_row):
                new_row[dest_col] = source_row[src_col]
        new_table.append(new_row)

    # Find table start/end in original prompt and replace only table part
    lines = prompt.split('\n')
    table_start = None
    table_end = None
    for i, line in enumerate(lines):
        if line.startswith('|'):
            if table_start is None:
                table_start = i
            table_end = i + 1

    if table_start is None:
        return None

    # Build new prompt preserving text before and after table
    new_table_str = common.table_to_string(new_table)
    before = '\n'.join(lines[:table_start])
    after = '\n'.join(lines[table_end:])

    parts = []
    if before:
        parts.append(before)
    parts.append(new_table_str)
    if after:
        parts.append(after)

    return '\n'.join(parts)


def add_args(parser):
    parser.add_argument("-c", "--columns", required=True,
                        help="Source columns to copy (comma-separated, e.g., '0,1'). "
                             "These will fill destination columns starting from 0.")
    parser.add_argument("error_file", help="Error file to fix (e.g., 1-error.xml)")
    parser.add_argument("source_dir", help="Source directory (e.g., ../word/gemma3-it)")


def main_func(args):
    error_file = args.error_file
    source_dir = args.source_dir
    source_columns = [int(c.strip()) for c in args.columns.split(",")]

    # Read error queries
    error_qs = common.read_queries(error_file)

    # Build source query lookup: info -> query
    source_lookup = {}
    for cantica in ["inferno", "purgatorio", "paradiso"]:
        cantica_dir = os.path.join(source_dir, cantica)
        if not os.path.isdir(cantica_dir):
            continue
        for filename in os.listdir(cantica_dir):
            if not filename.endswith(".xml"):
                continue
            filepath = os.path.join(cantica_dir, filename)
            qs = common.read_queries(filepath)
            for q in qs:
                if q.info and q.result:
                    source_lookup[q.info] = q

    # Update prompts in error queries
    modified = False
    for q in error_qs:
        if not q.info:
            continue

        if q.info not in source_lookup:
            print(f"Warning: No source found for {q.info}", file=sys.stderr)
            continue

        source_q = source_lookup[q.info]
        source_table = common.read_table(source_q.result)
        if not source_table:
            print(f"Warning: Could not parse source table for {q.info}", file=sys.stderr)
            continue

        new_prompt = replace_table_columns(q.prompt, source_table, source_columns)
        if new_prompt is None:
            print(f"Warning: Could not update prompt for {q.info}", file=sys.stderr)
            continue

        if new_prompt != q.prompt:
            print(f"Updating prompt for {q.info}")
            q.prompt = new_prompt
            modified = True

    # Write back
    if modified:
        common.write_queries(error_file, error_qs, count=len(error_qs))
        print(f"Updated {error_file}")
    else:
        print("No changes needed")

    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Fix prompts in error file by replacing table columns with source data."
    )
    add_args(parser)
    args = parser.parse_args(argv)
    return main_func(args)


if __name__ == "__main__":
    sys.exit(main())
