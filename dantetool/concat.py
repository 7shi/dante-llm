import sys
import argparse
from dantetool import common

def add_args(parser):
    parser.add_argument("-o", "--output", type=str, required=True,
                        help="output XML file")
    parser.add_argument("inputs", nargs="+", type=str,
                        help="input XML files to concatenate")

def main_func(args):
    qs = []
    for input_file in args.inputs:
        qs += common.read_queries(input_file)
    common.write_queries(args.output, qs, count=len(qs))
    return 0

def main(argv=None):
    parser = argparse.ArgumentParser(description="Concatenate XML query files")
    add_args(parser)
    args = parser.parse_args(argv)
    return main_func(args)

if __name__ == "__main__":
    sys.exit(main())
