import sys, os, common, option

translate = ["English", "Italian"]
fields = [[0], [1]]
init_prompt = False

def parse(i, args):
    global translate, fields, init_prompt
    if args[i] == "-t" and len(args) > i + 1:
        args.pop(i)
        translate = [l.strip() for l in args.pop(i).split(",")]
    elif args[i] == "-f" and len(args) > i + 1:
        args.pop(i)
        fields = [[int(f) for f in fs.split("+")] for fs in args.pop(i).split(",")]
    elif args[i] == "--init-prompt":
        args.pop(i)
        init_prompt = True

if not option.parse(parse):
    print(f"Usage: python {sys.argv[0]} language word-dir output-dir [fix ...]", file=sys.stderr)
    print("  -t: specify language to translate (comma separated)", file=sys.stderr)
    print("  -f: specify field to column 2 (0-based, comma separated)", file=sys.stderr)
    print("  --init-prompt: force init", file=sys.stderr)
    option.show()
    sys.exit(1)

fixes = common.read_fixes(*option.args)

import gemini

def send(query):
    global fields
    flen = len(fields)
    colnum = ", ".join(str(flen + c + 1) for c in range(len(translate)))
    prompt = f"For each row in the table, fill in columns {colnum} with the direct translation of column 1."
    if not query.result:
        q = common.query()
        q.info = query.info
        q.prompt = prompt
        q.error = "(skip)"
        return q
    table = []
    for i, row in enumerate(common.read_table(query.result)):
        if i == 1:
            table.append("|" + "---|" * (flen + len(translate)))
            continue
        m = max(max(fs) for fs in fields)
        if len(row) <= m:
            print(f"Warning: {len(row)} <= {m} @ {query.info}", file=sys.stderr)
            continue
        rowf = [" ".join(row[f].strip() for f in fs) for fs in fields]
        if i == 0:
            cells = " | ".join([option.language, *rowf[1:]])
            table.append("| " + cells + " | " + " | ".join(translate) + " |")
        else:
            cells = " | ".join(rowf)
            if cells.upper() != cells.lower():
                table.append("| " + cells + " |" * (len(translate) + 1))
    prompt += "\n\n"
    prompt += "\n".join(table)
    return gemini.query(prompt, query.info, option.show, option.retry)

if os.path.exists(option.init):
    init_qs = common.read_queries(option.init)
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
init_ps = [history[0]] if init_prompt else None

@option.proc
def proc(src, xml):
    queries = common.read_queries(src)
    qs = []
    for query in queries:
        if not (0 <= gemini.chat_count < option.interval):
            gemini.init(history, init_ps)
        if not query.result and query.info in fixes:
            for q in fixes[query.info]:
                qs.append(send(q))
        else:
            qs.append(send(query))
    common.write_queries(xml, qs, count=len(qs))
