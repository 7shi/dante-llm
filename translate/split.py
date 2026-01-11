import sys, re

args = sys.argv[1:]
check_type = 0

if len(args) > 1 and args[0] == "-c":
    check_type = int(args[1])
    args = args[2:]

if not args:
    print(f"usage: python {sys.argv[0]} [-c type] xml1 [xml2 ...]", file=sys.stderr)
    sys.exit(1)

import common

def split_lines(text):
    if not text:
        return [], [], []
    lines = [line.strip() for line in text.strip().split("\n")]
    s1 = 0
    for i in range(len(lines)):
        if re.match(r"\*\*.+\*\*$", lines[i]):
            s1 = i
    s2 = -1
    for i in range(s1, len(lines)):
        if re.match("\d+ [^ ]", lines[i]):
            s2 = i
            break
    if s2 < 0:
        return "", [], []
    lnums = []
    lnum  = []
    texts = []
    text  = []
    for i in range(s2, len(lines)):
        if m := re.match("(\d+) [^ ]", lines[i]):
            lnum.append(int(m.group(1)))
            text.append(lines[i])
        elif lnum:
            lnums.append(lnum)
            texts.append("\n".join(text))
            lnum = []
            text = []
    if lnum:
        lnums.append(lnum)
        texts.append("\n".join(text))
    return "\n".join(lines[:s2]), lnums, texts

def equals(a, b):
    if len(a) != len(b):
        return False
    return all(a[i] == b[i] for i in range(len(a)))

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

def set_lines(lines, text):
    for line in text.split("\n"):
        if m := re.match(r"(\d+) ", line):
            lines[int(m.group(1))] = line

def set_langs(langs, text, info):
    sp = separate(text)
    if not sp:
        return False
    if len(sp) > 2:
        for inf, _ in sp[2:]:
            print("ignore:", inf, "@", info, file=sys.stderr)
    if not langs[1][0]:
        langs[1][0] = sp[0][0]
        if len(sp) >= 2:
            langs[2][0] = sp[1][0]
    for i in range(min(2, len(sp))):
        set_lines(langs[i + 1][1], sp[i][1])

def save_result(arg, dst):
    error = sum(1 for q in dst if not q.result)
    print(f"{arg}: error={error}/{len(dst)}")
    common.write_queries(arg, dst, error=error, count=len(dst))

def split3(arg):
    src = common.read_queries(arg)
    if not (m := re.match(r"(\[.+\])", src[0].info)):
        print(f"invalid info @ {src[0].info}", file=sys.stderr)
        return
    info = m.group(1)
    prompt = src[0].prompt.split("\n")[0] + "\n\n"
    langs = [["", {}], ["", {}], ["", {}]]
    for q in src:
        set_lines(langs[0][1], q.prompt)
        if q.error and q.error.startswith("**"):
            set_langs(langs, q.error, q.info)
            if q.result:
                set_lines(langs[2][1], q.result)
        elif q.result:
            if not set_langs(langs, q.result, q.info):
                set_lines(langs[2][1], q.result)
    length = max(langs[0][1].keys())
    dst = []
    for ln in range(1, length + 1, 3):
        texts = ["", "", ""]
        end = min(3, length + 1 - ln)
        ok = True
        for j in range(end):
            for k in range(3):
                if ln + j in langs[k][1]:
                    if texts[k]:
                        texts[k] += "\n"
                    texts[k] += langs[k][1][ln + j]
                elif k == 0:
                    print(f"no source line {ln + j} @ {info}", file=sys.stderr)
                elif k == 2:
                    ok = False
        q = common.query()
        q.info = f"{info} {ln}/{length}"
        q.prompt = prompt + texts[0]
        if ok:
            q.result = texts[2]
            if texts[1]:
                q.error = langs[1][0] + "\n" + texts[1]
        else:
            q.error = "(no result)"
        dst.append(q)
    save_result(arg, dst)

def check_lines1(arg):
    src = common.read_queries(arg)
    dst = []
    for q in src:
        if not (m := re.match(r"(.+) (\d+)/(\d+)$", q.info)):
            print(f"invalid format @ {q.info}", file=sys.stderr)
            dst.append(q)
            continue
        info1 = m.group(1)
        info2 = int(m.group(2))
        info3 = int(m.group(3))
        ppre, pln, ptx = split_lines(q.prompt)
        if not pln:
            print(f"no lines found @ {q.info}", file=sys.stderr)
            if q.result:
                q.error = q.result
                q.result = None
            dst.append(q)
            continue
        if info2 != pln[0][0]:
            print(f"line not match: {pln[0][0]} @ {q.info}", file=sys.stderr)
            if q.result:
                q.error = q.result
                q.result = None
            dst.append(q)
            continue
        rpre, rln, rtx = split_lines(q.result)
        if not q.result or not rln:
            for i in range(len(pln)):
                q1 = common.query()
                q1.info = f"{info1} {pln[i][0]}/{info3}"
                q1.prompt = f"{ppre}\n{ptx[i]}"
                if i == 0 and q.result:
                    q1.error = q.result
                elif i == 0 and q.error:
                    q1.error = q.error
                else:
                    q1.error = "(no result)"
                dst.append(q1)
            continue
        for i in range(len(pln)):
            q1 = common.query()
            q1.info = f"{info1} {pln[i][0]}/{info3}"
            q1.prompt = f"{ppre}\n{ptx[i]}"
            if i >= len(rln):
                if i == 0:
                    q1.error = q.result
                else:
                    q1.error = "(no result)"
            elif not equals(pln[i], rln[i]):
                if i == 0 and rpre:
                    q1.error = f"{rpre}\n{rtx[i]}"
                else:
                    q1.error = rtx[i]
            else:
                if i == 0 and rpre:
                    q1.error = rpre.strip()
                q1.result = rtx[i]
            dst.append(q1)
    save_result(arg, dst)

def check_lines2(arg):
    src = common.read_queries(arg)
    dst = []
    for q in src:
        pln = split_lines(q.prompt)[1]
        rln = split_lines(q.result)[1]
        if ok := (pln and rln and len(pln) == len(rln)):
            for i in range(len(pln)):
                if not equals(pln[i], rln[i]):
                    ok = False
                    break
        if not ok:
            print(f"error @ {q.info}", file=sys.stderr)
            if q.result:
                q.error = q.result
                q.result = None
        dst.append(q)
    save_result(arg, dst)

for arg in args:
    if check_type == 1:
        check_lines1(arg)
    elif check_type == 2:
        check_lines2(arg)
    else:
        split3(arg)
