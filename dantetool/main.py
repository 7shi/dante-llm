import sys
import argparse
from dantetool import concat, pickup, redo, replace, strip

def main():
    parser = argparse.ArgumentParser(
        prog="dantetool",
        description="Tools for Dante's Divine Comedy translation project"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # concat subcommand
    concat_parser = subparsers.add_parser("concat", help="Concatenate XML query files")
    concat.add_args(concat_parser)
    concat_parser.set_defaults(func=concat.main_func)

    # pickup subcommand
    pickup_parser = subparsers.add_parser("pickup", help="Pick up error queries from XML files")
    pickup.add_args(pickup_parser)
    pickup_parser.set_defaults(func=pickup.main_func)

    # redo subcommand
    redo_parser = subparsers.add_parser("redo", help="Redo error queries")
    redo.add_args(redo_parser)
    redo_parser.set_defaults(func=redo.main_func)

    # replace subcommand
    replace_parser = subparsers.add_parser("replace", help="Replace queries in target files with fixes")
    replace.add_args(replace_parser)
    replace_parser.set_defaults(func=replace.main_func)

    # strip subcommand
    strip_parser = subparsers.add_parser("strip", help="Strip table content from XML files")
    strip.add_args(strip_parser)
    strip_parser.set_defaults(func=strip.main_func)

    args = parser.parse_args()

    if hasattr(args, "func"):
        return args.func(args)
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())
