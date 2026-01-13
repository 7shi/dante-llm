import re
import argparse
from dantetool import common, option

parser = argparse.ArgumentParser(
    description="Create word tables using Gemini",
    formatter_class=argparse.RawDescriptionHelpFormatter)

option.interval = 5
option.parse(parser)
args = parser.parse_args()
option.apply(args)

init_qs = common.read_queries(option.init)
history = common.unzip(init_qs)

from dantetool import gemini

gemini.generation_config["max_length"] = 8192

MAX_CONSECUTIVE_ERRORS = 3
error_count = 0

def query(prompt, info):
    global error_count
    q = gemini.query(prompt, info, option.show, option.retry)
    if q.result:
        error_count = 0
    else:
        error_count += 1
        if error_count >= MAX_CONSECUTIVE_ERRORS:
            raise Exception(f"Maximum consecutive errors reached: {MAX_CONSECUTIVE_ERRORS}")
    return q

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
            gemini.init(option.model, history, think=option.think)
        info = f"[{option.info}] {m.group(1)}/{lmax}"
        q = query("Create a word table.\n\n" + text, info)
        if q:
            qs.append(q)
    common.write_queries(xml, qs, count=len(qs))
