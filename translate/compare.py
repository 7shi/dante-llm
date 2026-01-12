"""
Compare translations from different models
Usage: uv run translate/compare.py inferno/01
Output: translate/comparison/inferno/01.md
"""

import sys
import argparse
from pathlib import Path
from dantetool import common
from dantetool.option import directories

def collect_translations(base_dir, rel_path, it_dir):
    """Collect translations from all subdirectories"""
    translations = {}

    # First, collect original Italian text from it/
    it_file = str(it_dir / rel_path) + ".txt"
    srcs, _ = common.read_source(it_file)
    translations["Dante"] = srcs
    srcs_len = len(srcs)

    # Then collect translations from subdirectories
    ok = True
    for subdir in sorted(base_dir.iterdir()):
        if subdir.is_dir() and subdir.name != "comparison":
            file = str(subdir / rel_path) + ".xml"
            srcs, _ = common.read_source(file)
            translations[subdir.name] = srcs
            if len(srcs) != srcs_len:
                ok = False
    if ok:
        return translations
    
    print("Error:", rel_path, {k: len(v) for k, v in translations.items()}, file=sys.stderr)
    return None

def format_table(translations, group_index):
    """Format a single 3-line group as HTML table rows"""
    rows = []

    # Sort by language: Dante (it), *-en, *-ja
    def sort_key(model):
        if model == "Dante":
            return (0, "")
        elif model.endswith("-en"):
            return (1, model)
        elif model.endswith("-ja"):
            return (2, model)
        else:
            return (3, model)

    for model in sorted(translations.keys(), key=sort_key):
        srcs = translations[model]
        if group_index >= len(srcs):
            continue

        group = srcs[group_index]
        if not group:
            continue

        # Parse line numbers and texts from lines like "123 text"
        line_nums = []
        text_lines = []
        for line in group:
            parts = line.split(" ", 1)
            if len(parts) == 2:
                line_nums.append(int(parts[0]))
                text_lines.append(parts[1].strip())

        if not line_nums:
            continue

        # Format line numbers
        line_num_str = "<br>".join(str(n) for n in line_nums)

        # Format text lines
        text_str = "<br>\n".join(text_lines)

        rows.append(f'<tr><td>{model}</td><td align="right">{line_num_str}</td><td>\n{text_str}\n</td></tr>')

    if rows:
        rows.append('<tr><td></td><td></td><td></td></tr>')

    return rows

def write_comparison(output_file, translations, title):
    """Write comparison markdown file"""
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Get maximum number of groups
    max_groups = max(len(srcs) for srcs in translations.values())

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write("<table>\n")

        for group_index in range(max_groups):
            rows = format_table(translations, group_index)
            for row in rows:
                f.write(row + "\n")

        f.write("</table>\n")

def process_one(rel_path_input, script_dir):
    """Process a single translation comparison"""
    # Parse path components
    parts = Path(rel_path_input).parts
    if len(parts) < 2:
        print(f"Error: Path must be like 'inferno/01', got: {rel_path_input}")
        return False

    cantica = parts[0]  # inferno, purgatorio, paradiso
    canto_num = parts[1]  # 01, ...

    # Validate cantica
    if cantica not in directories:
        print(f"Error: Unknown cantica '{cantica}'. Must be one of: {', '.join(directories)}")
        return False
    title = f"{cantica.title()} - Canto {int(canto_num)}"

    # Add .xml extension for accessing files
    rel_path = f"{cantica}/{canto_num}"

    # Paths
    base_dir = script_dir
    it_dir = script_dir.parent / "it"
    output_file = script_dir / "comparison" / cantica / f"{canto_num}.md"

    # Collect translations
    translations = collect_translations(base_dir, rel_path, it_dir)
    if not translations:
        return False

    # Write output
    write_comparison(output_file, translations, title)
    print(f"Written: {output_file}")

    return True

def main():
    parser = argparse.ArgumentParser(
        description="Compare translations from different models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  uv run translate/compare.py inferno/01\n  uv run translate/compare.py inferno/01 inferno/02 purgatorio/01"
    )
    parser.add_argument("rel_paths", nargs="+", help="relative path(s) without extension (e.g., inferno/01)")

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    success_count = 0

    for rel_path_input in args.rel_paths:
        if process_one(rel_path_input, script_dir):
            success_count += 1

    if success_count == 0:
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
