import argparse

parser = argparse.ArgumentParser()
parser.add_argument("filenames", nargs="+", help="file paths")
args = parser.parse_args()

from pathlib import Path
from dantetool import common

script_dir = Path(__file__).resolve().parent
base_dir = script_dir.parent
dirs = [base_dir / d for d in ["word", "word-tr", "etymology"]]
translate_dir = base_dir / "translate"

def read_translations(prefix, filename):
    """Read translations from translate/{prefix}-* directories"""
    translations = {}  # line_no -> {lang: text}
    for subdir in sorted(translate_dir.iterdir()):
        if not subdir.is_dir() or not subdir.name.startswith(prefix + "-"):
            continue
        lang = subdir.name[len(prefix) + 1:]  # e.g., "ja" from "gemini1-ja"
        file = str(subdir / filename) + ".xml"
        srcs, _ = common.read_source(file)
        for group in srcs:
            for line in group:
                parts = line.split(" ", 1)
                if len(parts) == 2 and parts[0].isdigit():
                    line_no = int(parts[0])
                    translations.setdefault(line_no, {})[lang] = parts[1]
    return translations

for filename in args.filenames:
    # Auto-detect langcodes from word directory
    word_dir = base_dir / "word"
    directories = sorted([
        d.name for d in word_dir.iterdir()
        if d.is_dir() and (d / (filename + ".xml")).exists()
    ])
    if not directories:
        print(f"Error [{filename}]: No language codes found")
        continue

    # Read original lines from it/ directory
    it_file = base_dir / "it" / (filename + ".txt")
    with open(it_file, "r", encoding="utf-8") as f:
        original_lines = [line.rstrip() for line in f]

    # Collect translations for each prefix
    # translations_by_prefix: prefix -> {line_no: {lang: text}}
    translations_by_prefix = {}
    for directory in directories:
        prefix = directory.rsplit("-", 1)[0]  # e.g., "gemini1-it" -> "gemini1"
        if prefix not in translations_by_prefix:
            translations_by_prefix[prefix] = read_translations(prefix, filename)

    # Collect data for each langcode (model)
    # line_model_tables: line_no -> {directory: (header, rows)}
    line_model_tables = {}

    for directory in directories:
        files = [str(d / directory / (filename + ".xml")) for d in dirs]
        for info, lines, table in common.read_tables(*files, 0):
            header = table[0]
            tables = common.split_table(f"{directory} {info}", lines, table)
            for i, line in enumerate(lines):
                # Extract line number from line (format: "123 text")
                parts = line.split(" ", 1)
                if len(parts) == 2 and parts[0].isdigit():
                    line_no = int(parts[0])
                    line_model_tables.setdefault(line_no, {})[directory] = (header, tables[i])

    # Parse filename for title
    parts = Path(filename).parts
    if len(parts) >= 2:
        cantica = parts[0]
        canto_no = parts[1]
        title = f"{cantica.title()} - Canto {int(canto_no)}"
    else:
        title = filename

    # Write output
    output_path = script_dir / (filename + ".md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        print(f"# {title}", file=f)

        for line_no in range(1, len(original_lines) + 1):
            model_tables = line_model_tables.get(line_no, {})
            line = original_lines[line_no - 1]

            # Check if there's any data (table or translation) for this line
            has_data = bool(model_tables)
            if not has_data:
                for prefix, translations in translations_by_prefix.items():
                    if line_no in translations:
                        has_data = True
                        break
            if not has_data:
                continue

            print(file=f)
            print(f"### {line_no} {line}", file=f)

            for directory in directories:
                prefix = directory.rsplit("-", 1)[0]
                has_table = directory in model_tables
                has_trans = prefix in translations_by_prefix and line_no in translations_by_prefix[prefix]

                if not has_table and not has_trans:
                    continue

                print(file=f)
                print(f"**{directory}**", file=f)

                # Print translations for this langcode's prefix
                if has_trans:
                    trans = translations_by_prefix[prefix][line_no]
                    for lang in sorted(trans.keys()):
                        print(f"- **{prefix}-{lang}**: {trans[lang]}", file=f)

                if has_table:
                    header, rows = model_tables[directory]
                    print(common.write_md("", header, rows).lstrip(), end="", file=f)

    print(f"Written: {output_path}")
