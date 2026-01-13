import sys, os, re
import argparse
from dantetool import common, gemini

def add_args(parser):
    parser.add_argument("-i", dest="init_xml", type=str, default="init.xml",
                        help="specify init.xml file (default: init.xml)")
    parser.add_argument("-m", dest="model", type=str, required=True,
                        help="specify model name (required)")
    parser.add_argument("-n", dest="interval", type=int, default=5,
                        help=f"specify interval (default: 5)")
    parser.add_argument("-s", dest="system_prompt", type=str,
                        help="specify system prompt file")
    parser.add_argument("-t", dest="temperature", type=float,
                        help="specify temperature")
    parser.add_argument("-1", dest="per1", action="store_true",
                        help="split 3-line queries into separate 1-line queries")
    parser.add_argument("--no-think", dest="think", action="store_false", default=None,
                        help="don't include thoughts in response")
    parser.add_argument("input", type=str,
                        help="input XML file (e.g., 1-error.xml)")

def separate(result):
    lines = [line.strip() for line in result.strip().split("\n")]
    ret = []
    for line in lines:
        if re.match(r"\*\*.+\*\*$", line):
            ret.append([line, ""])
        elif ret and line and re.match(r"\d+ [^ ]", line):
            if ret[-1][1]:
                ret[-1][1] += "\n"
            ret[-1][1] += line
    return ret

def is_skip(q):
    return q.result or (q.error and q.error == "(skip)")

def main_func(args):
    if args.temperature is not None:
        gemini.generation_config["temperature"] = args.temperature

    # Read system prompt if specified
    if args.system_prompt:
        with open(args.system_prompt, "r", encoding="utf-8") as f:
            system_prompt = f.read().strip()
    else:
        system_prompt = None

    init_qs = common.read_queries(args.init_xml)
    history = common.unzip(init_qs)
    input_qs = common.read_queries(args.input)

    queries = []
    it = iter(input_qs)
    q = next(it, None)
    while q:
        if re.search(r"\+\d$", q.info):
            qs = [q]
            prefix = q.info[:-2]
            while q := next(it, None):
                if q.info.startswith(prefix):
                    qs.append(q)
                else:
                    break
            queries.append(qs)
            continue
        if args.per1:
            lines = q.prompt.strip().split("\n")
            if len(lines) == 5 and not lines[1]:
                qs = []
                for i in range(3):
                    qq = common.query()
                    qq.info = f"{q.info}+{i}"
                    qq.prompt = "\n".join([lines[0], "", lines[i + 2]])
                    qs.append(qq)
                queries.append(qs)
                q = next(it, None)
                continue
        queries.append([q])
        q = next(it, None)

    fn = os.path.splitext(args.input)[0]
    def save_ok():
        common.write_queries(f"{fn}-ok.xml", qs_ok, count=len(qs_ok))
    def save_ng():
        error = sum(1 for q in qs_ng if not q.result)
        common.write_queries(f"{fn}-ng.xml", qs_ng, error=error, count=len(qs_ng))

    qs_ok = []
    qs_ng = []
    i = 0
    count = sum(1 for qs1 in queries for q in qs1 if not is_skip(q))
    for qs1 in queries:
        qs2 = []
        ok = 0
        for q in qs1:
            if is_skip(q):
                qq = q
            else:
                i += 1
                if i > 1:
                    print()
                print(f"==== {i}/{count} ====", file=sys.stderr)
                if not (0 <= gemini.chat_count < args.interval):
                    gemini.init(args.model, history, system=system_prompt, think=args.think)
                qq = gemini.query(q.prompt, q.info, show=True, retry=False)
            qs2.append(qq)
            if qq.result:
                ok += 1
        if ok == 3:
            q = common.query()
            q.info = qs2[0].info[:-2]
            q.prompt = "\n".join(qs2[0].prompt.split("\n")[:2])
            q.result = ""
            for qq in qs2:
                q.prompt += "\n" + qq.prompt.split("\n")[2]
                if (sp := separate(qq.result)):
                    if len(sp) > 2:
                        for j in range(2, len(sp)):
                            print("ignore:", sp[j][0], "@", qq.info, file=sys.stderr)
                    if not q.error:
                        q.error = "\n".join(sp[0])
                    else:
                        q.error += "\n" + sp[0][1]
                    if len(sp) >= 2:
                        if q.result:
                            q.result += "\n"
                        q.result += sp[1][1]
                else:
                    line = qq.result.split("\n")[0]
                    if q.result:
                        q.result += "\n"
                    q.result += line
            qs_ok.append(q)
            save_ok()
        elif ok == len(qs2):
            qs_ok += qs2
            save_ok()
        else:
            qs_ng += qs2
            save_ng()

    all = sum(map(len, queries))
    print("OK:", len(qs_ok), ", NG:", len(qs_ng), ", ALL:", all, file=sys.stderr)

    return 0

def main(argv=None):
    parser = argparse.ArgumentParser(description="Redo error queries")
    add_args(parser)
    args = parser.parse_args(argv)
    return main_func(args)

if __name__ == "__main__":
    sys.exit(main())
