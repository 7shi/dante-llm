import sys, os, re, common, xml7shi

def get_sample(xml, n=1):
    if not os.path.exists(xml):
        return "", [], []
    with open(xml, "r", encoding="utf-8") as f:
        xml = f.read()
    xr = xml7shi.reader(xml)
    texts1 = []
    texts2 = []
    for _ in range(n):
        q = common.parse(xr)
        if not (q.result and (m := re.search(r"into (.*)\.", q.prompt))):
            continue
        lang = m.group(1)
        if m := re.search(r" and (.*)", lang):
            lang = m.group(1)
        it = q.prompt.split("\n")[2:]
        if not (m := re.match(r"(\d+ )", it[0])):
            continue
        ln = m.group(1)
        lines = q.result.split("\n")
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].startswith(ln):
                break
        if texts1:
            texts1.append("")
            texts2.append("")
        texts1 += it
        texts2 += lines[i : i + len(it)]
    return lang, texts1, texts2

def type1(topdir, filename):
    tdir = os.path.join(topdir, "translate")
    texts = []
    it = []

    for d in os.listdir(tdir):
        lang, it, ts = get_sample(f"{tdir}/{d}/{filename}", 2)
        if lang:
            texts.append((lang, ts))

    texts.sort(key=lambda lang: lang)
    print("<table>")
    print("<tr><th>Language</th><th>Text</th></tr>")
    print("<tr><td>Italian</td><td>", "<br>".join(it), "</td></tr>", sep="")
    for lang, text in texts:
        attrs = ' dir="rtl" align="right"' if lang in ["Arabic", "Hebrew"] else ''
        print(f"<tr><td>{lang}</td><td{attrs}>", "<br>".join(text), "</td></tr>", sep="")
    print("</table>")

def type2(topdir, filename):
    dirs = [os.path.join(topdir, d) for d in ["word", "word-tr", "etymology"]]
    langs = {}
    for lc in os.listdir(dirs[0]):
        mk = os.path.join(dirs[0], lc, "Makefile")
        if not os.path.exists(mk):
            continue
        lang = common.read_defs(mk).get("LANG")
        if not lang:
            print(f"no LANG in {mk}", file=sys.stderr)
            continue
        print(lc, lang, file=sys.stderr)
        files = [f"{d}/{lc}/{filename}" for d in dirs]
        index = 1 if lc == "eo" else 0
        it = common.read_tables(*files, index)
        info, lines, table = next(it)
        header = table[0]
        tables = common.split_table(info, lines, table)
        langs[lang] = (lc, lines, header, tables)
    sp = ["Italian", "English", "Hindi", "Chinese"]
    for lang in sp + sorted(set(langs) - set(sp)):
        lc, lines, header, tables = langs[lang]
        print()
        print("###", lang)
        for i in range(3 if lang in sp else 1):
            print()
            print(common.write_md(lines[i], header, tables[i]), end="")
        print()
        print(f"[Read More](https://github.com/7shi/dante-gemini/blob/main/gallery/{lc}/inferno/01.md)")

def type3(topdir, lc, filename):
    dirs = [os.path.join(topdir, d) for d in ["word", "word-tr", "etymology"]]
    files = [f"{d}/{lc}/{filename}" for d in dirs]
    index = 1 if lc == "eo" else 0
    first = True
    for info, lines, table in common.read_tables(*files, index):
        header = table[0]
        tables = common.split_table(info, lines, table)
        for i, line in enumerate(lines):
            if first:
                first = False
            else:
                print()
            print(common.write_md(line, header, tables[i]), end="")

if __name__ == "__main__":
    args = sys.argv[1:]
    filename = "inferno/01.xml"
    lc = ""
    while args:
        if len(args) > 1 and args[0] == "-l":
            lc = args[1]
            args = args[2:]
        elif len(args) > 1 and args[0] == "-f":
            filename = args[1]
            args = args[2:]
        else:
            break
    if len(args) != 1:
        print(f"Usage: python {sys.argv[0]} [-l lc] [-f dir/xml] top-dir", file=sys.stderr)
        sys.exit(1)
    if lc:
        type3(args[0], lc, filename)
    else:
        type2(args[0], filename)
