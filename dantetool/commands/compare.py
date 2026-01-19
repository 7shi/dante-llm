"""
Compare word tables from different models
Usage: uv run dantetool compare inferno/01
Output: comparison/inferno/01.md (in current directory)
"""
import sys
from pathlib import Path
from dantetool import common
from dantetool.option import directories

def add_args(parser):
    parser.add_argument("rel_paths", nargs="+", help="relative path(s) without extension (e.g., inferno/01)")
    parser.add_argument("--use-tokens", "-t", action="store_true",
                        help="use tokenized words as first column for matching")

def process_one(base_dir, rel_path, use_tokens=False):
    """Process a single word table comparison"""
    # Parse path components
    parts = Path(rel_path).parts
    if len(parts) < 2:
        print(f"Error: Path must be like 'inferno/01', got: {rel_path}")
        return False

    cantica = parts[0]  # inferno, purgatorio, paradiso
    canto_no = parts[1]  # 01, ...

    # Validate cantica
    if cantica not in directories:
        print(f"Error: Unknown cantica '{cantica}'. Must be one of: {', '.join(directories)}")
        return False
    title = f"{cantica.title()} - Canto {int(canto_no)}"

    # Paths
    tokenized_file = base_dir / "tokenize" / cantica / f"{canto_no}.txt"
    curdir = Path(".")
    output_file = curdir / "comparison" / cantica / f"{canto_no}.md"

    # Read tokenized source (line, tokens...)
    tokenized_data = common.read_tokenized_source(tokenized_file)
    normalized_lines = [data[0] for data in tokenized_data]

    # Collect word tables from all models
    models = {}
    for subdir in sorted(curdir.iterdir()):
        if subdir.is_dir() and subdir.name not in ("comparison", "__pycache__"):
            file = subdir / cantica / (canto_no + ".xml")
            if not file.exists():
                continue
            qs = common.read_queries(file)
            models[subdir.name] = qs
    if not models:
        print(f"Error [{rel_path}]: No word table files found")
        return False

    # Build line_groups: for each line number, collect models' table rows
    line_model_tables = {}  # line_no -> {model: (header, rows)}
    for model, qs in models.items():
        for q in qs:
            if not q.result:
                continue

            # Parse info
            parsed = common.parse_info(q.info or "")
            if not parsed:
                print(f"Error [{model} {q.info}]: could not parse info", file=sys.stderr)
                continue

            # Extract line numbers
            line_no, total_lines = parsed[2:]
            line_numbers = list(range(line_no, min(line_no + 2, total_lines) + 1))

            # Read table from result
            table = common.read_table(q.result)
            if not table:
                print(f"Error [{model} {q.info}]: could not parse table in result", file=sys.stderr)
                continue

            # Prepend first column from tokenized data (if use_tokens is specified)
            has_first_col = False
            if use_tokens:
                # Collect tokens from all lines in line_numbers
                tokens = []
                for ln in line_numbers:
                    tokens.extend(tokenized_data[ln - 1][1:])
                # Build first column: header, separator, tokens...
                first_col = [table[0][0], "---"] + tokens
                if len(first_col) != len(table):
                    print(f"Error [{model} {q.info}]: row count mismatch "
                          f"(tokens={len(first_col)}, table={len(table)})", file=sys.stderr)
                    continue
                for i, row in enumerate(table):
                    row.insert(0, first_col[i])
                has_first_col = True

            for row in table:
                row[0] = row[0].replace("\u2019", "'")  # Normalize apostrophes

            # Split table into lines
            lines = [normalized_lines[ln - 1] for ln in line_numbers]
            splitted_rows = common.split_table(f"{model} {q.info}", lines, table)
            if len(lines) != len(splitted_rows):
                print(f"Error [{model} {q.info}]: mismatch in number of lines after split", file=sys.stderr)
                continue

            # Remove prepended column after split
            if has_first_col:
                for rows in splitted_rows:
                    for row in rows:
                        row.pop(0)
                table[0].pop(0)

            # Map line number to (header, rows)
            for line_no, rows in zip(line_numbers, splitted_rows):
                line_model_tables.setdefault(line_no, {})[model] = (table[0], rows)

    # Write output
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        print(f"# {title}", file=f)
        for line_no in range(1, len(normalized_lines) + 1):
            model_tables = line_model_tables.get(line_no)
            if not model_tables:
                print(f"Error [{rel_path}]: No data for line {line_no}", file=sys.stderr)
                continue

            print(file=f)
            print("###", line_no, normalized_lines[line_no - 1], file=f)

            for model, (header, rows) in model_tables.items():
                print(file=f)
                print(f"**{model}**", file=f)
                print(file=f)
                table = [header, ["---"] * len(header)] + rows
                print(common.table_to_string(table), file=f)

    print(f"Written: {output_file}")
    return True

def main_func(args):
    base_dir = Path(__file__).resolve().parent.parent.parent
    for rel_path in args.rel_paths:
        if not process_one(base_dir, rel_path, args.use_tokens):
            return 1
    return 0

def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description="Compare word tables from different models")
    add_args(parser)
    args = parser.parse_args(argv)
    return main_func(args)

if __name__ == "__main__":
    sys.exit(main())
