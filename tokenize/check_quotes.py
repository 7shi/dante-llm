import argparse

parser = argparse.ArgumentParser(
    description="Check quotation marks vs apostrophes using LLM",
    formatter_class=argparse.RawDescriptionHelpFormatter)

parser.add_argument("-t", dest="testonly", action="store_true",
                    help="test only (use existing init.xml)")
parser.add_argument("-m", dest="model",
                    help="model to use")
parser.add_argument("--no-think", dest="think", action="store_false", default=None,
                    help="don't include thoughts in response")
parser.add_argument("input_file", help="input file with quote cases")

args = parser.parse_args()

if not args.testonly and not args.model:
    parser.error("the -m/--model argument is required unless -t/--testonly is specified")

import os
import sys
from dantetool import common

# Read input lines
with open(args.input_file, "r", encoding="utf-8") as f:
    lines = [line.rstrip() for line in f]

# Replace U+2018 (') with " and U+2019 (') with '
def convert_quotes(text):
    return text.replace("\u2018", '"').replace("\u2019", "'")

prompt_template = """
The following line is Italian text.
- Double quotes (") are opening quotation marks.
- Single quotes (') can be either closing quotation marks or apostrophes (elision).

Your task: If a single quote is a closing quotation mark (paired with an opening double quote), replace it with a double quote.
Leave apostrophes (elision) as single quotes.

Return ONLY the converted line, nothing else.

Line: {line}
""".strip()

converted_file = os.path.splitext(args.input_file)[0] + "_converted.txt"

if args.testonly:
    with open(converted_file, "r", encoding="utf-8") as f:
        converted_lines = [line.rstrip() for line in f]
else:
    from dantetool import gemini
    gemini.init(args.model, think=args.think)
    converted_lines = []
    qs = []
    error_count = 0
    for i, line in enumerate(lines):
        converted = convert_quotes(line)
        prompt = prompt_template.format(line=converted)
        print(f"\n=== Line {i+1}/{len(lines)} ===")
        q = gemini.query(prompt, show=True, retry=False)
        if q.result:
            converted_lines.append(q.result.strip())
        else:
            converted_lines.append(f"ERROR: {line}")
            error_count += 1
        qs.append(q)

    # Save results
    common.write_queries("quote_cases.xml", qs, error=error_count, whole=len(qs))
    with open(converted_file, "w", encoding="utf-8") as f:
        print("\n".join(converted_lines), file=f)
    print(f"\nResults saved to quote_cases.xml and {converted_file}")

if len(lines) != len(converted_lines):
    print("Error: number of input lines and converted lines differ.", file=sys.stderr)
    sys.exit(1)

for i in range(len(lines)):
    original = lines[i].replace("\u2018", "'").replace("\u2019", "'")
    converted = converted_lines[i].replace('"', "'")
    if original != converted:
        print(f"Error [{i+1}]: {lines[i]}")
