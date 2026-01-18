import sys, os, re, common, option

derived = "Latin, Greek, Germanic"
fields = [1]

def parse(i, args):
    global derived, fields
    if args[i] == "-e" and len(args) > i + 1:
        args.pop(i)
        derived = args.pop(i)
    elif args[i] == "-f" and len(args) > i + 1:
        args.pop(i)
        fields = [int(f) for f in args.pop(i).split(",")]

if not option.parse(parse):
    print(f"Usage: python {sys.argv[0]} language word-tr-dir output-dir [fix ...]", file=sys.stderr)
    print("  -e: specify etymology language(s)", file=sys.stderr)
    print("  -f: specify field to column 2 (0-based, comma separated)", file=sys.stderr)
    option.show()
    sys.exit(1)

fixes = common.read_fixes(*option.args)

import gemini

prompt_template = " ".join([
    'For each row in the table, look up the etymology of the word.',
    f'In the "Derived" column, write {derived}, etc.',
    'In the "Etymology" column, fill in the corresponding word in Greek, Latin, or others,',
    'but leave blank if unknown.'
])

def send(query):
    prompt = prompt_template
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
            head = " | " + " | ".join(rowf[1:]) if len(rowf) > 1 else ""
            table.append(f"| {option.language}{head} | Derived | Etymology |")
        elif i == 1:
            table.append("|" + "---|" * (len(fields) + 2))
        else:
            table.append(f"| " + " | ".join(rowf) + " | | |")
    prompt += "\n\n"
    prompt += "\n".join(table)
    return gemini.query(prompt, query.info, option.show, option.retry)

if os.path.exists(option.init):
    init_qs = common.read_queries(option.init)
    prompt_template = init_qs[0].prompt.split("\n")[0]
else:
    print(f"making {option.init}...")
    gemini.init()
    inferno1 = common.read_queries(os.path.join(option.srcdir, option.directories[0], "01.xml"))
    q = send(inferno1[0])
    if not q.result:
        print("Abort.", file=sys.stderr)
        sys.exit(1)
    init_qs = [q]
    common.write_queries(option.init, init_qs, count=len(init_qs))
history = common.unzip(init_qs)

@option.proc
def proc(src, xml):
    queries = common.read_queries(src)
    qs = []
    for query in queries:
        if not (0 <= gemini.chat_count < option.interval):
            gemini.init(history)
        if not query.result and query.info in fixes:
            for q in fixes[query.info]:
                qs.append(send(q))
        else:
            qs.append(send(query))
    common.write_queries(xml, qs, count=len(qs))
