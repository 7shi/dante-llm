"""
Show translation from XML file
Usage: uv run translate/show.py translate/gemini1-en/inferno/01.xml
"""
import re
import argparse
from dantetool import common

parser = argparse.ArgumentParser(
    description="Show translation from XML file",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="Example:\n  uv run translate/show.py translate/gemini1-en/inferno/01.xml"
)
parser.add_argument("file", help="XML file to read")
args = parser.parse_args()

qs = common.read_queries(args.file)

for q in qs:
    if not q.result:
        continue
    for line in q.result.splitlines():
        if re.match(r"^\d+\s", line):
            print(line)
