import sys, re
import argparse
from dantetool import common, option

parser = argparse.ArgumentParser(
    description="Create word tables using Gemini",
    formatter_class=argparse.RawDescriptionHelpFormatter)

option.parse(parser)
args = parser.parse_args()
option.apply(args)

init_qs = common.read_queries(option.init)
history = common.unzip(init_qs)

from dantetool import gemini

gemini.generation_config["max_length"] = 8192

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
            gemini.init(option.model, history, think=option.think)
        info = f"[{option.info}] {m.group(1)}/{lmax}"
        q = send(text, info)
        if q:
            qs.append(q)
    common.write_queries(xml, qs, count=len(qs))
