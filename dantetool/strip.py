import sys
import argparse
from dantetool import common

def add_args(parser):
    parser.add_argument("targets", nargs="+", type=str,
                        help="target XML files to strip")

def main_func(args):
    for target in args.targets:
        qs = common.read_queries(target)
        for q in qs:
            if q.result:
                table = common.fix_table(q.result)
                if table:
                    q.result = table
                    q.error = None
                else:
                    print(f"Error: could not parse table in {q.info}")
                    q.error = q.result
                    q.result = None
        common.write_queries(target, qs, count=len(qs))
    return 0

def main(argv=None):
    parser = argparse.ArgumentParser(description="Strip table content from XML files")
    add_args(parser)
    args = parser.parse_args(argv)
    return main_func(args)

if __name__ == "__main__":
    sys.exit(main())
