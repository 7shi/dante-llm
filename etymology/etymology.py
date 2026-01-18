import sys
import os
import argparse
from dantetool import option

parser = argparse.ArgumentParser(
    description="Look up etymology using Gemini",
    formatter_class=argparse.RawDescriptionHelpFormatter)

option.interval = 1
option.parse(parser)

parser.add_argument("-e", "--derived", default="Latin, Greek, Germanic",
                    help="specify etymology language(s)")
parser.add_argument("-f", "--fields", default="1",
                    help="fields for columns (0-based, comma separated)")
parser.add_argument("--init", dest="do_init", action="store_true",
                    help="create init.xml and exit")
parser.add_argument("--fix", dest="fix_files", action="append", default=[],
                    help="fix file (can be specified multiple times)")

args = parser.parse_args()
option.apply(args)

derived = args.derived
fields = [int(f) for f in args.fields.split(",")]

from dantetool import common, gemini

fixes = common.read_fixes(*args.fix_files)

prompt_template = " ".join([
    'For each row in the table, look up the etymology of the word.',
    f'In the "Derived" column, write {derived}, etc.',
    'In the "Etymology" column, fill in the corresponding word in Greek, Latin, or others,',
    'but leave blank if unknown.'
])

def send(query, extra_prompt=""):
    prompt = prompt_template + extra_prompt
    if not query.result:
        q = common.query()
        q.info = query.info
        q.prompt = prompt
        q.error = "(skip)"
        return q
    table = []
    for i, row in enumerate(common.read_table(query.result)):
        m = max(fields)
        if len(row) <= m:
            print(f"Warning: {len(row)} <= {m} @ {query.info}", file=sys.stderr)
            continue
        rowf = [row[f] for f in fields]
        if i == 0:
            table.append([option.language, *rowf[1:], "Derived", "Etymology"])
        elif i == 1:
            table.append(["---"] * (len(fields) + 2))
        else:
            table.append([*rowf, "", ""])
    prompt += "\n\n"
    prompt += common.table_to_string(table)
    return gemini.query(prompt, query.info, option.show, option.retry)

if args.do_init:
    # If --init is specified: create init.xml and exit
    print(f"making {option.init}...")
    gemini.init(option.model, history=[], think=option.think)
    inferno1 = common.read_queries(os.path.join(option.srcdir, option.directories[0], "01.xml"))
    q = send(inferno1[0], "\nProvide only the etymology table without any additional explanations or commentary outside the table.")
    if not q.result:
        print("Abort.", file=sys.stderr)
        sys.exit(1)
    init_qs = [q]
    common.write_queries(option.init, init_qs, count=len(init_qs))
    print(f"{option.init} created successfully.")
    sys.exit(0)
elif not os.path.exists(option.init):
    print(f"Error: {option.init} not found. Please run with --init first.", file=sys.stderr)
    sys.exit(1)

init_qs = common.read_queries(option.init)
history = common.unzip(init_qs)

@option.proc
def proc(src, xml):
    queries = common.read_queries(src)
    qs = []
    for query in queries:
        if not (0 <= gemini.chat_count < option.interval):
            gemini.init(option.model, history, think=option.think)
        if not query.result and query.info in fixes:
            for q in fixes[query.info]:
                qs.append(send(q))
        else:
            qs.append(send(query))
    common.write_queries(xml, qs, count=len(qs))
