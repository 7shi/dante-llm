"""
Collect and enumerate all characters used in Italian text files.
Usage: uv run tokenize/chars.py inferno/01
"""
import sys
import re
from pathlib import Path
from dantetool import common
from dantetool.option import directories

def read_all(base_dir):
    """
    Read all Italian text files from the Divine Comedy and collect lines.

    Iterates over all three canticas (Inferno, Purgatorio, Paradiso) and
    reads each canto file, extracting the text content without line numbers.

    Args:
        base_dir (str or Path): Base directory containing cantica subdirectories
                                (inferno/, purgatorio/, paradiso/).

    Returns:
        dict: Mapping from cantica name to list of canto lines.
              e.g., {"inferno": [[lines...], ...], "purgatorio": [...], ...}
    """
    path = Path(base_dir)
    result = {}

    # Iterate over each cantica (inferno, purgatorio, paradiso)
    for i, cantica in enumerate(directories):
        cantica_dir = path / cantica
        result[cantica] = []
        # Inferno has 34 cantos, others have 33
        for j in range(1, (34 if i == 0 else 33) + 1):
            _, src_lines = common.read_source(str(cantica_dir / f"{j:02d}"))
            if not src_lines:
                break
            # Extract text content, removing line number prefix (e.g., "1 Nel mezzo...")
            lines = []
            for ln in range(1, max(src_lines.keys()) + 1):
                if m := re.match(r"\d+ (.*)", src_lines[ln]):
                    lines.append(m.group(1))
            result[cantica].append(lines)

    return result

def main():
    # Path to the it/ directory
    it_dir = Path(__file__).parent.parent / "it"

    # Read all lines from Italian text files
    data = read_all(it_dir)
    lines = [line for cantica in data.values() for canto in cantica for line in canto]

    # Unified set of all characters across all files
    all_chars = set()
    for line in lines:
        all_chars.update(line)

    # Sort characters for display
    sorted_chars = sorted(all_chars)

    # Print unified results
    print(f"Total unique characters: {len(sorted_chars)}")
    print()
    for ch in sorted_chars:
        print(f"U+{ord(ch):04X}: {repr(ch)}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
