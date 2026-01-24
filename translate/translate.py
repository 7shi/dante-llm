import sys, os, re
import argparse
from dantetool import common, option

needsp  = False
always3 = False

parser = argparse.ArgumentParser(
    description="Translate text using Gemini",
    formatter_class=argparse.RawDescriptionHelpFormatter)

option.parse(parser)
parser.add_argument("--need-space", dest="needsp", action="store_true",
                    help="require at least one space in each line")
parser.add_argument("-3", dest="always3", action="store_true",
                    help="always send 3 lines")
parser.add_argument("--init", dest="do_init", action="store_true",
                    help="create init.xml and exit")

args = parser.parse_args()

option.apply(args)
needsp = args.needsp
always3 = args.always3
do_init = args.do_init

checklen = 6 if " and " in option.language else 3

from dantetool import gemini

# Read system prompt from system.txt
script_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(script_dir, "system.txt"), "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read().strip()

text = []
current = 0

def send_lines(line_count, *plines):
    global current
    diru = option.directory[0].upper() + option.directory[1:]
    info = f"[{diru} Canto {option.canto}] {current + 1}/{len(text)}"
    prompt = " ".join(plines)
    for i in range(line_count):
        if i == 0 or current % 3 == 0:
            prompt += "\n"
        line = f"{current + 1} {text[current]}"
        prompt += "\n" + line
        current += 1
    def check(r):
        if len(r) > len(prompt) * checklen:
            return f"Response too long: ({len(r)} > {len(prompt) * checklen})"
        if needsp:
            for line in r.split("\n"):
                if m := re.match(r"(\d+)", line):
                    t = line[m.end():]
                    if not t.startswith(" ") or " " not in t[1:]:
                        return f"Too few spaces: {repr(r)}"
        return None
    return gemini.query(prompt, info, option.show, option.retry, check)

prompt = f"Please translate each line literally into {option.language}."

if do_init:
    # If --init is specified: create init.xml and exit
    print(f"making {option.init}...")
    gemini.init(option.model, system=SYSTEM_PROMPT, think=option.think)
    option.directory = option.directories[0]
    option.canto = 1
    file = os.path.join(option.srcdir, option.directory, f"01.txt")
    with open(file, "r", encoding="utf-8") as f:
        text = [l.split("|")[0] for line in f if (l := line.strip())]
    init_qs = []
    for length in [3, 3, 3] if always3 else [3, 6]:
        q = send_lines(length, prompt)
        if not q.result:
            print("Abort.", file=sys.stderr)
            sys.exit(1)
        init_qs.append(q)
    common.write_queries(option.init, init_qs, count=len(init_qs))
    print(f"{option.init} created successfully.")
    sys.exit(0)
elif os.path.exists(option.init):
    # If init.xml exists: load it
    init_qs = common.read_queries(option.init)
else:
    # If init.xml does not exist and --init is not specified: error
    print(f"Error: {option.init} not found. Please run with --init first.", file=sys.stderr)
    sys.exit(1)

history = common.unzip(init_qs)

@option.proc
def proc(src, xml):
    global text, current
    with open(src, "r", encoding="utf-8") as f:
        text = [l.split("|")[0] for line in f if (l := line.strip())]
    current = 0
    qs = []
    while current < len(text):
        if not (0 <= gemini.chat_count < option.interval):
            gemini.init(option.model, history, system=SYSTEM_PROMPT, think=option.think)
        length = min(3, len(text) - current)
        if not always3:
            while current + length < len(text) and not text[current + length - 1].endswith("."):
                length += 1
        qs.append(send_lines(length, prompt))
    common.write_queries(xml, qs, count=len(qs))
