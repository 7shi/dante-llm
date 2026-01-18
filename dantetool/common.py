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

def parse_info(info: str) -> tuple[str, int, int, int] | None:
    """Parse something like: "[Inferno Canto 7] 1/136"."""
    m = re.search(r"\[(Inferno|Purgatorio|Paradiso)\s+Canto\s+(\d+)\]\s+(\d+)/(\d+)", info)
    if not m:
        return None
    cantica = m.group(1).lower()
    canto_no = int(m.group(2))
    line_no = int(m.group(3))
    total_lines = int(m.group(4))
    return cantica, canto_no, line_no, total_lines

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

def table_to_string(table):
    output = []
    for i, row in enumerate(table):
        if i == 1:
            output.append("|" + "|".join(row) + "|")
        else:
            row_s = "| " + " | ".join(row) + " |"
            output.append(row_s.replace("|  ", "| "))
    return "\n".join(output)

abbrevs = {
    "number": {"singular": "sg.", "plural": "pl."},
    "gender": {"masculine": "m.", "feminine": "f.", "neuter": "n."},
    "person": {"first": "1", "1st": "1", "second": "2", "2nd": "2", "third": "3", "3rd": "3"},
}

def fix_cell(header, cell):
    cell = cell.strip()
    if cell in ["-", "n/a", "N/A"]:
        return ""
    ab = abbrevs.get(header.lower(), {}).get(cell.lower())
    if ab:
        return ab
    if m := re.fullmatch(r"([^*]+)\*", cell):
        return m.group(1).strip()
    if m := re.fullmatch(r"\*\*([^*]+)\*\*", cell):
        return m.group(1).strip()
    return cell

def fix_table_rows(table):
    rows = []
    header = table[0]
    for i, row in enumerate(table):
        if i == 1:
            # Keep separator row as is
            rows.append(row)
        else:
            # Apply fix_cell to non-separator rows
            rows.append([fix_cell(header[j], cell) for j, cell in enumerate(row)])
    return rows

def fix_table(text):
    table = read_table(text)
    if table:
        return table_to_string(fix_table_rows(table))
    else:
        return None

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

def read_tokenized_source(path: str) -> list[list[str]]:
    """Read one tokenized source file.

    The tokenized files are produced by tokenize/tokenizer.py.

    Line format:
        original_line|token1|token2|...

    Args:
        path:
            Path to a single tokenized file.

    Returns:
        list[list[str]]:
            Each line split by '|':
                [original_line, token1, token2, ...]
    """
    with open(path, "r", encoding="utf-8") as f:
        return [line.rstrip().split("|") for line in f]

def extract_numbered_lines(prompt: str) -> list[tuple[int, str, str]]:
    """Extract numbered lines from a prompt.

    The prompt format is expected to include lines like:
        "67 Qualche testo..."

    Returns:
        List of (line_no, text, raw_line).
    """
    ret = []
    for raw in prompt.split("\n"):
        if m := re.match(r"(\d+)\s+(.*)", raw):
            ret.append((int(m.group(1)), m.group(2), raw))
    return ret

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

def has_alpha(text):
    """
    Check if the text contains any alphabetic characters.
    """
    return any(c.isalpha() for c in text)

def split_table(info, lines, table):
    """
    Split table rows into buckets based on which line in 'lines' each row's word belongs to.

    This function is designed for LLM-produced word tables, where the "Word" column may
    contain hallucinated duplicates or slightly transformed tokens (which won't match the
    source line via exact substring search). Instead of failing hard or requiring external
    correction, `split_table` resolves ambiguity internally using two commit rules:

    Terms:
        - Anchor: a table word `w` that can be found as an exact substring in the source.
        - pending: a FIFO list of table rows whose word couldn't be matched ("not_found").

    Commit rules:
        (A) Line-end commit:
            After committing a matched word on the current line, advance
            `start = i + len(w)`. If the remaining tail `lines[ln][start:]` contains no
            alphabetic characters, we consider the current line committed (A holds).

        (B) Next-line transition commit:
            If a word is not found in the current line but is found in the next line,
            we transition to the next line (B event). At this moment we must resolve
            `pending` deterministically:

            - If we had A since the last commit on the previous line (A→B), `pending`
              is treated as hallucination/extra and dropped.

            - If A did NOT hold (B without prior A), `pending` is salvaged to the previous line
              (`salvage_prev`). This covers the corner case where the last source token
              of the previous line was transformed by the LLM, preventing A.

            Additional corner case (next-line head transformed):
                If A→B but the next line has an alphabetic prefix before the matched word
                (i.e. `skipped_text = lines[next_ln][0:i]` has alpha), then we salvage
                only the *most recent* pending row into the next line (`salvage_next`).
                If multiple consecutive head tokens are transformed, we salvage only one
                and drop the rest.

        (Inline salvage on same-line anchor):
            If we are still on the same line (no B transition) and an anchor match occurs,
            any accumulated `pending` rows are assumed to belong to the current line
            before the matched anchor word. They are salvaged in FIFO order *before*
            appending the matched row. This recovers simple typos like "eterno" vs
            source "etterno" while preserving table order.

        (Final-line mode):
            Once the cursor reaches the final source line, the remainder of the table is
            deterministically assigned to that final line and processing stops (no further
            searching / transitions). This avoids dropping leftovers when there is no
            future line transition to trigger salvage decisions.

    Observability:
        Skips/drops/salvages are logged to stderr with a stable one-line format:
            info | <event> | ln=<n> | word=<...> | evidence=<...>

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

    Returns:
        list of list: A list where ret[i] contains table rows assigned to lines[i].
    """
    ret = [[] for _ in lines]

    def log(event: str, ln: int | None = None, word: str | None = None, evidence: str | None = None, count: int | None = None):
        parts = [str(info), "|", event]
        if ln is not None:
            parts.append(f"| ln={ln}")
        if word is not None:
            parts.append(f"| word={word!r}")
        if count is not None:
            parts.append(f"| count={count}")
        if evidence is not None and evidence != "":
            # Keep evidence short-ish for log readability
            ev = evidence
            if len(ev) > 120:
                ev = ev[:117] + "..."
            parts.append(f"| evidence={ev!r}")
        print(" ".join(parts), file=sys.stderr)

    def pending_words(pending_rows: list[list[str]]) -> str:
        # pending rows are table rows like [word, lemma, ...]
        words = [r[0] for r in pending_rows if r]
        return " ".join(words)

    # Preprocess rows: skip header and non-alphabetic rows
    rows = []
    for row_idx, row in enumerate(table[1:]):
        if row_idx == 0 and "---" in row[0]:
            # Skip separator row
            continue
        elif has_alpha(row[0]):
            rows.append([-1, *row])

    last_ln = len(lines) - 1

    # Fast path: single-line source => everything belongs to that line.
    if len(lines) <= 1:
        if len(lines) == 1:
            assigned = [r[1:] for r in rows]
            ret[0].extend(assigned)
        return ret

    ln = 0
    start = 0
    pending: list[list[str]] = []
    a_holds = False

    for row_idx, row in enumerate(rows):
        w = row[1]
        i = -1  # Found index (initialized to -1)
        found_in_next = False

        # Main search logic
        if ln < len(lines):
            # Try searching in the current line starting from 'start'
            i = lines[ln].find(w, start)

            # If not found, try searching in the next line from the beginning (lookahead)
            if i < 0 and ln + 1 < len(lines):
                i = lines[ln + 1].find(w, 0)
                if i >= 0:
                    found_in_next = True

        # Handle next-line transition (B)
        if found_in_next:
            prev_ln = ln
            next_ln = ln + 1

            # Log/record source tail of previous line if it contains alphabetic text
            skipped_at_end = lines[prev_ln][start:]
            if has_alpha(skipped_at_end):
                log("skip_line_end", ln=prev_ln, word=w, evidence=skipped_at_end)

            # Decide how to resolve pending at the moment of B
            next_prefix = lines[next_ln][0:i]
            has_next_prefix_alpha = has_alpha(next_prefix)

            if a_holds:
                # A -> B: drop pending, but optionally salvage one into the next line
                if pending and has_next_prefix_alpha:
                    salvaged = pending.pop()  # salvage only the most recent one
                    ret[next_ln].append(salvaged)
                    log("salvage_next", ln=next_ln, word=salvaged[0] if salvaged else None, evidence=next_prefix)
                if pending:
                    log("drop", ln=prev_ln, count=len(pending), evidence=pending_words(pending))
                    pending.clear()
            else:
                # B without prior A: salvage everything to the previous line
                if pending:
                    for p in pending:
                        ret[prev_ln].append(p)
                    log("salvage_prev", ln=prev_ln, count=len(pending), evidence=pending_words(pending))
                    pending.clear()

            # Transition to next line
            ln = next_ln
            start = 0
            a_holds = False

            # Log/record next-line prefix skip (source gap)
            if has_next_prefix_alpha:
                log("skip", ln=next_ln, word=w, evidence=next_prefix)

            # Final-line mode: once we reach the final source line, assign the rest and stop.
            if ln == last_ln:
                assigned = [r[1:] for r in rows[row_idx:]]
                ret[ln].extend(assigned)
                break

        if i >= 0:
            # Check for skipped alphabetic characters between the last match and current match
            # (in the current line after any B transition handling)
            skipped_text = lines[ln][start:i]
            if has_alpha(skipped_text):
                log("skip", ln=ln, word=w, evidence=skipped_text)

            # Inline salvage: if we found an anchor on the current line, treat any pending
            # as belonging to this line before the anchor, preserving order.
            if pending:
                for p in pending:
                    ret[ln].append(p)
                log("salvage_inline", ln=ln, count=len(pending), evidence=pending_words(pending))
                pending.clear()

            # Word successfully found: add row to the corresponding bucket
            row[0] = ln
            ret[ln].append(row[1:])
            # Update the start position for the next word search
            start = i + len(w)
            # A: line-end commit check
            a_holds = not has_alpha(lines[ln][start:])
        else:
            # Word not found: keep as pending (may be dropped/salvaged at next B)
            pending.append(row[1:])
            remaining = lines[ln][start:] if ln < len(lines) else ""
            log("not_found", ln=ln if ln < len(lines) else None, word=w, evidence=remaining)

    # End-of-input: drop any remaining pending (no future B to salvage against).
    # Final-line mode stops processing as soon as the final line is reached.
    if pending:
        log("drop", ln=ln if ln < len(lines) else None, count=len(pending), evidence=pending_words(pending))

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
