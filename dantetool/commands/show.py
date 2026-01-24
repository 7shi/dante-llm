import re
import argparse
from dantetool import common

def add_args(parser):
    parser.add_argument("file", help="XML file to read")

def main_func(args):
    qs = common.read_queries(args.file)

    for q in qs:
        if not q.result:
            continue
        for line in q.result.splitlines():
            if re.match(r"^\d+\s", line):
                print(line)

    return 0

def main(argv=None):
    parser = argparse.ArgumentParser(description="Show translation from XML file")
    add_args(parser)
    args = parser.parse_args(argv)
    return main_func(args)

if __name__ == "__main__":
    import sys
    sys.exit(main())
