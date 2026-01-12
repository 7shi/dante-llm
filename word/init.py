import argparse

parser = argparse.ArgumentParser(
    description="Initialize word table generation using Gemini",
    formatter_class=argparse.RawDescriptionHelpFormatter)

parser.add_argument("-t", dest="testonly", action="store_true",
                    help="test only (use existing init.xml)")
parser.add_argument("-n", dest="crasis", action="store_false", default=True,
                    help="disable crasis (contractions) prompt")
parser.add_argument("-c", dest="columns",
                    default="Word, Lemma, Part of Speech, Gender, Number, Person, Tense, Mood and Note",
                    help="specify table columns")
parser.add_argument("-i", dest="init_xml", default="init.xml",
                    help="init.xml file path")
parser.add_argument("-d", dest="subdir", default="inferno",
                    help="subdirectory to process")
parser.add_argument("-m", dest="model", required=True,
                    help="model to use")
parser.add_argument("--no-think", dest="think", action="store_false", default=None,
                    help="don't include thoughts in response")
parser.add_argument("language", help="target language")
parser.add_argument("srcdir", help="source directory")

args = parser.parse_args()

testonly = args.testonly
crasis = args.crasis
columns = args.columns
init_xml = args.init_xml
subdir = args.subdir.split()[0]
model = args.model
think = args.think
language = args.language
srcdir = args.srcdir

from dantetool import gemini, common

gemini.generation_config["max_length"] = 8192

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
* Provide only the word table without any additional explanations or commentary outside the table.

""".lstrip()

if not testonly:
    qs = []
    gemini.init(model, think=think)
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

gemini.init(model, common.unzip(init_qs), think=think)

qs = []
if init_qs[0].prompt[:8] in ["This tex", "Create a"]:
    qs.append(query(init_qs[0].prompt))
else:
    qs.append(query(init_qs[1].prompt))
for lines in srcs[:3]:
    qs.append(query("Create a word table." + "\n\n" + "\n".join(lines)))

common.write_queries("test.xml", qs, count=len(qs))
