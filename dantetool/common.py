import sys, os, re, xml7shi

def escape(s):
    return s.replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")

class query:
    def __init__(self):
        self.prompt = None
        self.info   = None
        self.result = None
        self.error  = None
        self.retry  = False

    def __str__(self):
        s = "<query>\n"
        if self.info:
            s += f"<info>{escape(self.info)}</info>\n"
        attrs = ' retry="true"' if self.retry else ''
        s += f"<prompt{attrs}>\n{escape(self.prompt)}\n</prompt>\n"
        if self.error:
            attrs = ' result="true"' if self.result else ''
            s += f"<error{attrs}>\n{escape(self.error)}\n</error>\n"
        if self.result:
            s += f"<result>\n{escape(self.result)}\n</result>\n"
        return s + "</query>\n"

def parse(xr: xml7shi.reader):
    q = query()
    while xr.read():
        if xr.tag == "prompt":
            q.retry = xr.get("retry") == "true"
            if xr.read():
                q.prompt = xr.text.strip()
        elif xr.tag == "info" and xr.read():
            q.info = xr.text.strip()
        elif xr.tag == "error" and xr.read():
            q.error = xr.text.strip()
        elif xr.tag == "result" and xr.read():
            q.result = xr.text.strip()
        elif xr.tag == "/query":
            break
    return q

def read_queries(file):
    with open(file, "r", encoding="utf-8") as f:
        xml = f.read()
    xr = xml7shi.reader(xml)
    qs = []
    while xr.read():
        if xr.tag == "query":
            qs.append(parse(xr))
    return qs

def write(f, text="", end="\n"):
    f.write((str(text) + end).encode("utf_8"))

def write_queries(file, qs, **root_attrs):
    tmp_file = file + ".tmp"
    with open(tmp_file, "wb") as f:
        write(f, xml7shi.declaration)
        attrs = "".join(f' {k}="{v}"' for k, v in root_attrs.items())
        write(f, f"<queries{attrs}>")
        for q in qs:
            write(f, q, end="")
        write(f, "</queries>")
    os.replace(tmp_file, file)

def unzip(qs):
    ret = []
    for q in qs:
        ret.append(q.prompt)
        ret.append(q.result)
    return ret

# table

def read_table(src):
    ret = []
    rowlen = 0
    for line in src.splitlines():
        if line.startswith("|"):
            row = [t.strip() for t in line.split("|")[1:-1]]
            if not ret:
                rowlen = len(row)
            elif rowlen > len(row):
                row += [""] * (rowlen - len(row))
            elif rowlen < len(row):
                if all(cell == "" for cell in row[rowlen:]):
                    row = row[:rowlen]
                else:
                    return None
            ret.append(row)
        elif ret:
            break
    if len(ret) < 3:
        return None

    ret1 = []
    for cell in ret[1]:
        if "---" in cell:
            ret1.append(re.sub(r"-+", "---", cell))
        else:
            return None
    ret[1] = ret1
    return ret

abbrevs = {
    "singular": "sg.", "plural": "pl.",
    "masculine": "m.", "feminine": "f.", "neuter": "n.",
    "first": "1", "second": "2", "third": "3",
    "1st": "1", "2nd": "2", "3rd": "3",
}

def fix_cell(cell):
    cell = cell.strip()
    if cell in ["-", "n/a", "N/A"]:
        return ""
    ab = abbrevs.get(cell.lower())
    if ab:
        return ab
    if m := re.fullmatch(r"([^*]+)\*", cell):
        return m.group(1).strip()
    if m := re.fullmatch(r"\*\*([^*]+)\*\*", cell):
        return m.group(1).strip()
    return cell

def fix_table(text=None, table=None):
    if not table:
        table = read_table(text)
    if not table:
        return None

    output = []
    for i, row in enumerate(table):
        if i == 1:
            # Keep separator row as is
            output.append("|" + "|".join(row) + "|")
        else:
            # Apply fix_cell to non-separator rows
            fixed_row = [fix_cell(cell) for cell in row]
            row = "| " + " | ".join(fixed_row) + " |"
            row = row.replace("|  ", "| ")
            output.append(row)
    return "\n".join(output)

# source

def read_source(path, language=None):
    src_lines = {}

    if (file := path).endswith(".txt") or os.path.exists(file := f"{path}.txt"):
        # Build src_lines from .txt file
        with open(file, "r", encoding="utf-8") as f:
            ln = 0
            for line in f:
                line = line.strip()
                if line:
                    ln += 1
                    src_lines[ln] = f"{ln} {line}"
            last = ln
    elif (file := path).endswith(".xml") or os.path.exists(file := f"{path}.xml"):
        # Build src_lines from .xml file
        last = 0
        qs = read_queries(file)
        for q in qs:
            if not q.result:
                continue
            r = q.result
            if language and language in r:
                r = r[r.find("\n", r.find(language)):]
            for line in r.strip().split("\n"):
                if line and (m := re.match(r"(\d+)", line)):
                    lnstr = m.group(1)
                    ln = int(lnstr)
                    if line == lnstr:
                        line += " "
                    src_lines[ln] = line
                    if last < ln:
                        last = ln
        if qs and (m := re.search(r"/(\d+)", qs[0].info)):
            last = int(m.group(1))
    else:
        print(f"no source files found in {path}", file=sys.stderr)
        return [], {}

    # Build srcs from src_lines (group by 3)
    srcs = []
    lines = []
    for ln in range(1, last + 1):
        line = src_lines.setdefault(ln, f"{ln} ")
        lines.append(line)
        if len(lines) == 3:
            srcs.append(lines)
            lines = []
    if lines:
        srcs.append(lines)

    return srcs, src_lines

# fix

def read_fixes(*fix_files):
    ret = {}
    for f in fix_files:
        for q in read_queries(f):
            info = q.info
            if re.search(r"\+\d$", info):
                info = info[:-2]
            if info not in ret:
                ret[info] = []
            ret[info].append(q)
    return ret

# Makefile

def read_defs(mk):
    ret = {}
    with open(mk, "r", encoding="utf-8") as f:
        for line in f:
            if m := re.match(r"(\w+)\s*=\s*(.+)", line):
                ret[m.group(1)] = m.group(2)
    return ret

# unify

def fix_length(lst, info, title):
    first = True
    length = len(lst[0])
    for i in lst[1:]:
        if length != len(i):
            if first:
                # print(f"{info} | length mismatch ({title}): {length} {lst[0]}", file=sys.stderr)
                first = False
            # print(f"    {len(i)} {i}", file=sys.stderr)
            while length > len(i):
                i.append("")

def read_tables(word, word_tr, etymology, index=0):
    qs0 = read_queries(word)
    qs1 = read_queries(word_tr)
    qs2 = read_queries(etymology) if os.path.exists(etymology) else None
    qi1 = {q.info: q for q in qs1}
    qi2 = {q.info: q for q in qs2} if qs2 else None
    for q0 in qs0:
        if not q0.result:
            continue
        q1 = qi1.get(q0.info)
        if not q1 or not q1.result:
            continue
        q2 = qi2.get(q0.info) if qi2 else None
        if qi2 and (not q2 or not q2.result):
            continue
        if not (m := re.search(r"columns (\d+)", q1.prompt)):
            print("no columns count:", q0.info, file=sys.stderr)
            continue
        col = int(m.group(1)) - 1
        ts0 = read_table(q0.result)
        tsp = read_table(q1.prompt)
        ts1 = read_table(q1.result)
        ts2 = read_table(q2.result) if q2 else None
        if len(ts0) == 0 or len(ts1) == 0:
            print(q0.info, "| empty table (error):", len(ts0), len(ts1), file=sys.stderr)
            continue
        fix_length(ts0, q0.info, "word")
        fix_length(tsp, q1.info, "word-tr.prompt")
        fix_length(ts1, q1.info, "word-tr")
        fix_length(ts2, q2.info, "etymology") if ts2 else None
        length = len(ts1)
        # if length != len(tsp):
        #     print(q0.info, "(word-tr) | length mismatch:", len(tsp), "!=", length, file=sys.stderr)
        if ts2 and length != len(ts2):
            print(q0.info, "(etymology) | length mismatch (error):", length, "!=", len(ts2), file=sys.stderr)
            continue
        table = []
        for i, r0 in enumerate(ts0):
            r = len(table)
            if r >= length:
                break
            if i > 1 and r0[index] != tsp[r][0]:
                # print(q0.info, "| word mismatch:", r0[index], "!=", tsp[r][0], file=sys.stderr)
                continue
            row = r0 + ts1[r][col:]
            if ts2:
                row += ts2[r][-2:]
            table.append(row)
        if length != len(table):
            words = " ".join(r[0] for r in tsp[len(table):])
            print(q0.info, "| unused words (error):", words, file=sys.stderr)
            continue
        lines = [line for line in q0.prompt.split("\n")[1:] if line]
        yield q0.info, lines, table

def check_skip(text):
    """
    Check if the text contains any alphabetic characters.
    """
    return any(c.isalpha() for c in text)

def split_table(info, lines, table, errors=None):
    """
    Split table rows into buckets based on which line in 'lines' each row's word belongs to.

    Algorithm:
        For each row in the table, use the first column as a search word 'w'.
        Scan through 'lines' from left to right using two pointers (ln, start).
        If 'w' is found in the current or next line, assign the row to that line's bucket.

    Example:
        lines = ["Nel mezzo del cammin di nostra vita", "mi ritrovai per una selva oscura"]
        table = [
            ["cammin", "walk"],
            ["vita", "life"],
            ["selva", "forest"]
        ]

        # Process:
        # - "cammin": found at lines[0] -> bucket 0
        # - "vita": found at lines[0] -> bucket 0
        # - "selva": found at lines[1] -> bucket 1

        # Result:
        # [[["cammin","walk"], ["vita","life"]], [["selva","forest"]]]

    Args:
        info (str): Identifier for error messages.
        lines (list of str): List of text lines to search in.
        table (list of list): 2D list where table[0] is header.
        errors (list, optional): If provided, error tuples are appended here.
            Each tuple: (type, row_index, word, skipped_or_remaining)

    Returns:
        list of list: A list where ret[i] contains table rows assigned to lines[i].
    """
    ret = [[] for _ in lines]

    # Skip the table header
    rows = table[1:]

    # Skip the separator row (e.g., starts with "---") if it exists
    if rows and rows[0][0].startswith("---"):
        rows = rows[1:]

    ln = 0
    start = 0

    def report_error(err_type, row_idx, word, text):
        if err_type == "not_found":
            print(f"{info} | word not found: {repr(word)} in {repr(text)}", file=sys.stderr)
        else:
            print(f"{info} | possible skip: {repr(text)} before {repr(word)}", file=sys.stderr)
        if errors is not None:
            errors.append((err_type, row_idx, word, text))

    for row_idx, row in enumerate(rows):
        w = row[0]
        i = -1  # Found index (initialized to -1)

        # Main search logic
        if ln < len(lines):
            # Try searching in the current line starting from 'start'
            i = lines[ln].find(w, start)

            # If not found, try searching in the next line from the beginning (lookahead)
            if i < 0 and ln + 1 < len(lines):
                i = lines[ln + 1].find(w, 0)
                if i >= 0:
                    # Check for skipped content at the end of the previous line
                    skipped_at_end = lines[ln][start:]
                    if check_skip(skipped_at_end):
                        report_error("skip_line_end", row_idx, w, skipped_at_end)

                    # Move pointer to the next line since the word was found there
                    ln += 1
                    start = 0

        if i >= 0:
            # Check for skipped alphabetic characters between the last match and current match
            skipped_text = lines[ln][start:i]
            if check_skip(skipped_text):
                report_error("skip", row_idx, w, skipped_text)
            # Word successfully found: add row to the corresponding bucket
            ret[ln].append(row)
            # Update the start position for the next word search
            start = i + len(w)
        else:
            # Word not found
            remaining = lines[ln][start:] if ln < len(lines) else ""
            report_error("not_found", row_idx, w, remaining)

    return ret

def write_md(line, header, table):
    ret = line + "\n\n"
    ret += "<table>\n"
    for i, h in enumerate(header):
        cells = [row[i] for row in table]
        if sum(map(len, cells)) == 0:
            continue
        row = "".join(f"<td>{td}</td>" for td in cells)
        if h == "Etymology":
            row = row.replace("<td>*", "<td><sup>*</sup>").replace("*</td>", "</td>")
        ret += f"<tr><th>{h}</th>{row}</tr>\n"
    ret += "</table>\n"
    return ret
