import sys, re
import argparse
from dantetool import common

def add_args(parser):
    parser.add_argument("fix", type=str,
                        help="fix XML file (e.g., 1-error-ok.xml)")
    parser.add_argument("targets", nargs="+", type=str,
                        help="target XML files to update")

def main_func(args):
    fixes = common.read_fixes(args.fix)
    for arg in args.targets:
        fix = 0
        qs = []
        ignore = ""
        for q in common.read_queries(arg):
            if ignore:
                if q.info.startswith(ignore):
                    continue
                else:
                    ignore = ""
            info = q.info
            if m := re.search(r"\+\d$", info):
                info = info[:-2]
            if info in fixes:
                fix += 1
                qs += fixes.pop(q.info)
                if m:
                    ignore = info
            else:
                qs.append(q)
        if fix:
            print("fixed:", arg, fix, "/", len(qs), file=sys.stderr)
            common.write_queries(arg, qs, count=len(qs))
    if fixes:
        print("unfixed:", arg, len(fixes), list(fixes), file=sys.stderr)
    return 0

def main(argv=None):
    parser = argparse.ArgumentParser(description="Replace queries in target files with fixes")
    add_args(parser)
    args = parser.parse_args(argv)
    return main_func(args)

if __name__ == "__main__":
    sys.exit(main())
