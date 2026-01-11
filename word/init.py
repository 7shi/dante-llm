import sys

args = sys.argv[1:]

testonly = False
crasis = True
columns = "Word, Lemma, Part of Speech, Gender, Number, Person, Tense, Mood and Note"
init_xml = "init.xml"
subdir = "inferno"

while args:
    if args[0] == "-t":
        testonly = True
        args = args[1:]
    elif args[0] == "-n":
        crasis = False
        args = args[1:]
    elif args[0] == "-c" and len(args) > 1:
        columns = args[1]
        args = args[2:]
    elif args[0] == "-i" and len(args) > 1:
        init_xml = args[1]
        args = args[2:]
    elif args[0] == "-d" and len(args) > 1:
        subdir = args[1].split()[0]
        args = args[2:]
    else:
        break

if len(args) != 2:
    print(f"usage: python {sys.argv[0]} [-t] [-n] [-c columns] [-i init] [-d dir] language src-dir", file=sys.stderr)
    sys.exit(1)

language, srcdir = args

import gemini, common

def query(prompt):
    return gemini.query(prompt, show=True, retry=False)

srcs, src_lines = common.read_source(f"{srcdir}/{subdir}/01", language)

prompt_table = f"""
This text is written in {language}.
Create a word table showing the Lemma for each word.
The entries in the table are {columns}.

* Decompose the contraction in Lemma.
* Leave blank if not applicable.
* Words linked by an apostrophe should be separated.
* The Note should be writtern in brief, e.g. archaic.
* Quotation marks should be excluded. Apostrophes in contractions are not quotation marks.
* If the verb and the other word are combined, they should be separated by Lemma.
  In such cases, only the verb information should be written in the other columns.

""".lstrip()

if not testonly:
    qs = []
    gemini.init()
    if crasis:
        prompt = " ".join([
            f"Show contractions of preposition and article in {language}.",
            "No examples are needed."
        ])
        qs.append(query(prompt))

    prompt = prompt_table
    for ln in [1, 9, 28, 67]:
        if ln in src_lines:
            prompt += src_lines[ln] + "\n"
    q = query(prompt.rstrip())
    if q.result:
        q.result = common.fix_table(q.result)
    qs.append(q)

    common.write_queries(init_xml, qs, count=len(qs))
    init_qs = qs
else:
    init_qs = common.read_queries(init_xml)

gemini.init(common.unzip(init_qs))

qs = []
if init_qs[0].prompt[:8] in ["This tex", "Create a"]:
    qs.append(query(init_qs[0].prompt))
else:
    qs.append(query(init_qs[1].prompt))
for lines in srcs[:3]:
    qs.append(query("Create a word table." + "\n\n" + "\n".join(lines)))

common.write_queries("test.xml", qs, count=len(qs))
