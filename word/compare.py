"""
Compare word tables from different models
Usage: uv run word/compare.py inferno/01
Output: word/comparison/inferno/01.md
"""
import sys
import argparse
from pathlib import Path
from dantetool import common
from dantetool.option import directories

def process_one(script_dir, rel_path):
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
    base_dir = script_dir.parent
    tokenized_file = base_dir / "tokenize" / cantica / f"{canto_no}.txt"
    output_file = script_dir / "comparison" / cantica / f"{canto_no}.md"

    # Read normalized lines from tokenized source
    normalized_lines = [data[0] for data in common.read_tokenized_source(tokenized_file)]

    # Collect word tables from all models
    models = {}
    for subdir in sorted(script_dir.iterdir()):
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

            # Extract lines from prompt
            numbered_lines = common.extract_numbered_lines(q.prompt)
            if not numbered_lines:
                print(f"Error [{model} {q.info}]: no numbered lines found in prompt", file=sys.stderr)
                continue

            # Read table from result
            table = common.read_table(q.result)
            if not table:
                print(f"Error [{model} {q.info}]: could not parse table in result", file=sys.stderr)
                continue

            # Split table into lines
            lines = [raw for _, _, raw in numbered_lines]
            splitted_rows = common.split_table(f"{model} {q.info}", lines, table)
            if len(lines) != len(splitted_rows):
                print(f"Error [{model} {q.info}]: mismatch in number of lines after split", file=sys.stderr)
                continue

            # Map line number to (header, rows)
            for (line_no, _, _), rows in zip(numbered_lines, splitted_rows):
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
                table = [header, ["---"] * len(header)] + rows
                print(common.table_to_string(table), file=f)

    print(f"Written: {output_file}")
    return True

def main():
    parser = argparse.ArgumentParser(
        description="Compare word tables from different models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  uv run word/compare.py inferno/01\n  uv run word/compare.py inferno/01 inferno/02 purgatorio/01"
    )
    parser.add_argument("rel_paths", nargs="+", help="relative path(s) without extension (e.g., inferno/01)")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    for rel_path in args.rel_paths:
        if not process_one(script_dir, rel_path):
            return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
