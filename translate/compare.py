"""
Compare translations from different models
Usage: uv run translate/compare.py inferno/01
Output: translate/comparison/inferno/01.md
"""

import sys
import argparse
import re
from pathlib import Path
from dantetool import common
from dantetool.option import directories

def extract_lines(result):
    """Extract line number and text from result"""
    if not result:
        return []
    lines = []
    for line in result.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        # Match line number at start: "123 text" or "123"
        m = re.match(r"(\d+)\s*(.*)", line)
        if m:
            num = int(m.group(1))
            text = m.group(2)
            lines.append((num, text))
    return lines

def group_by_three(lines):
    """Group lines by 3"""
    groups = {}
    for num, text in lines:
        group_num = ((num - 1) // 3) * 3 + 1
        if group_num not in groups:
            groups[group_num] = {}
        groups[group_num][num] = text
    return groups

def collect_translations(base_dir, rel_path, it_dir):
    """Collect translations from all subdirectories"""
    translations = {}

    # First, collect original Italian text from it/
    # Convert .xml to .txt for it directory
    it_path = Path(rel_path)
    it_rel_path = it_path.parent / (it_path.stem + ".txt")
    it_file = it_dir / it_rel_path
    if it_file.exists():
        try:
            with open(it_file, "r", encoding="utf-8") as f:
                all_lines = []
                line_num = 1
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    # Italian text doesn't have line numbers, so we add them
                    all_lines.append((line_num, line))
                    line_num += 1
                if all_lines:
                    translations["Dante"] = group_by_three(all_lines)
        except Exception as e:
            print(f"Warning: Failed to read {it_file}: {e}", file=sys.stderr)

    # Then collect translations from subdirectories
    for subdir in sorted(base_dir.iterdir()):
        if not subdir.is_dir():
            continue
        if subdir.name in ["comparison"]:
            continue

        xml_file = subdir / rel_path
        if not xml_file.exists():
            continue

        try:
            queries = common.read_queries(str(xml_file))
            all_lines = []
            for q in queries:
                if q.result:
                    all_lines.extend(extract_lines(q.result))

            if all_lines:
                translations[subdir.name] = group_by_three(all_lines)
        except Exception as e:
            print(f"Warning: Failed to read {xml_file}: {e}", file=sys.stderr)

    return translations

def format_table(translations, group_num):
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
        group = translations[model].get(group_num, {})
        if not group:
            continue

        # Get line numbers and texts
        line_nums = sorted(group.keys())
        if not line_nums:
            continue

        # Format line numbers
        line_num_str = "<br>".join(str(n) for n in line_nums)

        # Format text lines
        text_lines = [group[n] for n in line_nums]
        text_str = "<br>\n".join(text_lines)

        rows.append(f'<tr><td>{model}</td><td align="right">{line_num_str}</td><td>\n{text_str}\n</td></tr>')

    if rows:
        rows.append('<tr><td></td><td></td><td></td></tr>')

    return rows

def write_comparison(output_file, translations, title):
    """Write comparison markdown file"""
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Get all group numbers
    all_groups = set()
    for model_groups in translations.values():
        all_groups.update(model_groups.keys())

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write("<table>\n")

        for group_num in sorted(all_groups):
            rows = format_table(translations, group_num)
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
    rel_path = f"{cantica}/{canto_num}.xml"

    # Paths
    base_dir = script_dir
    it_dir = script_dir.parent / "it"
    output_file = script_dir / "comparison" / cantica / f"{canto_num}.md"

    # Collect translations
    translations = collect_translations(base_dir, rel_path, it_dir)

    if not translations:
        print(f"No translations found for {rel_path}")
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
