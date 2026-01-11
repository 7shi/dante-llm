import sys, re, common, option

if not option.parse() or option.args:
    print(f"Usage: python {sys.argv[0]} language source-dir output-dir", file=sys.stderr)
    option.show()
    sys.exit(1)

init_qs = common.read_queries(option.init)
history = common.unzip(init_qs)
if init_qs[0].prompt[:8] in ["This tex", "Create a"]:
    init_ps = [init_qs[0].prompt]
else:
    init_ps = [init_qs[1].prompt]

import gemini

def send(text, info):
    prompt = "Create a word table.\n\n" + text
    return gemini.query(prompt, info, option.show, option.retry)

@option.proc
def proc(src, xml):
    srcs, src_lines = common.read_source(src, option.language)
    lmax = max(src_lines)
    qs = []
    for lines in srcs:
        text = "\n".join(lines)
        if not (m := re.match(r"(\d+) ", text)):
            continue
        if not (0 <= gemini.chat_count < option.interval):
            gemini.init(history, init_ps)
        info = f"[{option.info}] {m.group(1)}/{lmax}"
        q = send(text, info)
        if q:
            qs.append(q)
    common.write_queries(xml, qs, count=len(qs))
