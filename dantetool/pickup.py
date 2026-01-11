import sys
import argparse
from dantetool import common

def add_args(parser):
    parser.add_argument("-t", dest="check_table", action="store_true",
                        help="check table format")
    parser.add_argument("output", type=str,
                        help="output XML file")
    parser.add_argument("files", nargs="+", type=str,
                        help="input XML files")

def main_func(args):
    output = args.output
    check_table = args.check_table

    whole = 0
    queries = []
    for f in args.files:
        for q in common.read_queries(f):
            whole += 1
            if check_table:
                if q.result:
                    if "||---" in q.result or not common.read_table(q.result):
                        queries.append(q)
            elif not q.result:
                queries.append(q)

    print(f"error {len(queries)}/{whole}", file=sys.stderr)
    common.write_queries(output, queries, count=len(queries), whole=whole)
    return 0

def main(argv=None):
    parser = argparse.ArgumentParser(description="Pick up error queries from XML files")
    add_args(parser)
    args = parser.parse_args(argv)
    return main_func(args)

if __name__ == "__main__":
    sys.exit(main())
