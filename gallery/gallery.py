import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-l", dest="langcode", required=True, help="language code")
parser.add_argument("-f", dest="filename", default="inferno/01.xml", help="file path")
parser.add_argument("topdir", help="top directory")
args = parser.parse_args()

from pathlib import Path
from dantetool import common

topdir = Path(args.topdir)
dirs = [topdir / d for d in ["word", "word-tr", "etymology"]]
files = [str(d / args.langcode / args.filename) for d in dirs]
index = 1 if args.langcode == "eo" else 0
first = True
for info, lines, table in common.read_tables(*files, index):
    header = table[0]
    tables = common.split_table(info, lines, table)
    for i, line in enumerate(lines):
        if first:
            first = False
        else:
            print()
        print(common.write_md(line, header, tables[i]), end="")
