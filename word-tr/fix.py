#!/usr/bin/env python3
"""Fix prompts in 1-error.xml by replacing table columns with current source data."""

import sys
import os
import argparse

from dantetool import common

def replace_table_columns(prompt, source_table, source_columns):
    """Replace prompt table columns with source table data.

    Args:
        prompt: Original prompt containing a table
        source_table: Source table (list of rows) with correct data
        source_columns: List of source column indices to copy from.
                       These will be written to destination columns 0, 1, 2, ... in order.

    Returns:
        Updated prompt with replaced columns
    """
    # Parse prompt table
    prompt_table = common.read_table(prompt)
    if not prompt_table or len(prompt_table) < 3:
        return None

    # Skip header rows in source (rows 0,1 are header and separator)
    source_data = source_table[2:]
    prompt_data = prompt_table[2:]

    if len(source_data) != len(prompt_data):
        return None

    # Replace columns: source_columns[i] -> destination column i
    for i, (prompt_row, source_row) in enumerate(zip(prompt_data, source_data)):
        for dest_col, src_col in enumerate(source_columns):
            if dest_col < len(prompt_row) and src_col < len(source_row):
                prompt_table[i + 2][dest_col] = source_row[src_col]

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
    new_table = common.table_to_string(prompt_table)
    before = '\n'.join(lines[:table_start])
    after = '\n'.join(lines[table_end:])

    parts = []
    if before:
        parts.append(before)
    parts.append(new_table)
    if after:
        parts.append(after)

    return '\n'.join(parts)

def main():
    parser = argparse.ArgumentParser(
        description="Fix prompts in error file by replacing table columns with source data."
    )
    parser.add_argument("error_file", help="Error file to fix (e.g., 1-error.xml)")
    parser.add_argument("source_dir", help="Source directory (e.g., ../word/gemma3-it)")
    parser.add_argument(
        "-c", "--columns", required=True,
        help="Source columns to copy (comma-separated, e.g., '0,1'). "
             "These will fill destination columns starting from 0."
    )
    args = parser.parse_args()

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

if __name__ == "__main__":
    main()
