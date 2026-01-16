import argparse
import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Iterable

from dantetool import common, gemini

@lru_cache(maxsize=256)
def read_tokenized_source(path: str) -> list[list[str]]:
    """Memoized wrapper for `common.read_tokenized_source()`."""
    return common.read_tokenized_source(path)

def is_skip(q: common.query) -> bool:
    """Match the redo-style skip semantics."""
    return bool(q.result) or (q.error is not None and q.error.strip() == "(skip)")

def iter_expected_tokens(
    numbered_lines: list[tuple[int, str, str]],
    tokenized_canto: list[list[str]],
) -> Iterable[str]:
    """Flatten the reference tokens for the numbered lines from tokenize/ output."""
    for line_no, _text, _raw in numbered_lines:
        if not (1 <= line_no <= len(tokenized_canto)):
            continue
        parts = tokenized_canto[line_no - 1]
        # parts: [original_line, token1, token2, ...]
        for tok in parts[1:]:
            yield tok

def build_skeleton_table(header: list[str], tokens: list[str]) -> str:
    """Build a skeleton word table with only the first column filled."""
    cols = len(header)
    rows: list[list[str]] = [header, ["---"] * cols]
    for tok in tokens:
        rows.append([tok] + [""] * (cols - 1))
    return common.table_to_string(rows)

def build_prompt(numbered_raw_lines: list[str], skeleton_table: str) -> str:
    return "\n\n".join([
        "Create a word table for the text below:",
        "\n".join(numbered_raw_lines),
        "Output format (fill in blank cells):",
        skeleton_table,
    ]).rstrip()

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Regenerate only Phase-3-token-mismatched word tables with a strict in-prompt table skeleton.",
    )
    parser.add_argument("-i", dest="init_xml", type=str, default="init.xml", help="init.xml (default: init.xml)")
    parser.add_argument("-m", dest="model", type=str, required=True, help="model name (required)")
    parser.add_argument("-n", dest="interval", type=int, default=5, help="chat reset interval (default: 5)")
    parser.add_argument("-t", dest="temperature", type=float, help="temperature")
    parser.add_argument("--no-think", dest="think", action="store_false", default=None, help="don't include thoughts")
    parser.add_argument("--no-show", dest="show", action="store_false", default=True, help="don't show prompts")
    parser.add_argument("--no-retry", dest="retry", action="store_false", default=True, help="don't retry")
    parser.add_argument("input", type=str, help="input XML file (e.g., 1-error.xml)")
    args = parser.parse_args(argv)

    if args.temperature is not None:
        gemini.generation_config["temperature"] = args.temperature

    gemini.generation_config["max_length"] = 8192

    init_qs = common.read_queries(args.init_xml)
    history = common.unzip(init_qs)
    header = common.read_table(history[-1])[0]

    in_qs = common.read_queries(args.input)

    fn = os.path.splitext(args.input)[0]
    ok_path = f"{fn}-ok.xml"
    ng_path = f"{fn}-ng.xml"

    tokenize_dir = Path(__file__).resolve().parent.parent / "tokenize"

    qs_ok: list[common.query] = []
    qs_ng: list[common.query] = []

    def error(q, msg=None):
        if msg:
            print(f"\nError {q.info}: {msg}", file=sys.stderr)
            if q.error is None:
                q.error = msg
        qs_ng.append(q)
        common.write_queries(ng_path, qs_ng, error=sum(1 for x in qs_ng if not x.result), count=len(qs_ng))

    count = sum(1 for q in in_qs if not is_skip(q))
    done = 0

    for q in in_qs:
        if is_skip(q):
            # Keep skips / already-ok entries as is.
            qs_ok.append(q)
            continue

        done += 1
        if done > 1:
            print(file=sys.stderr)
        print(f"==== {done}/{count} ====", file=sys.stderr)

        if not q.prompt:
            error(q, "missing prompt")
            continue

        numbered = common.extract_numbered_lines(q.prompt)
        if not numbered:
            error(q, "no numbered lines found in prompt")
            continue

        parsed = common.parse_cantica_and_canto(q.info or "")
        if not parsed:
            error(q, f"could not parse cantica/canto from info: {q.info!r}")
            continue

        cantica, canto_no = parsed
        token_path = tokenize_dir / cantica / f"{canto_no:02d}.txt"
        try:
            tokenized_canto = read_tokenized_source(str(token_path))
        except FileNotFoundError:
            error(q, f"missing tokenized reference: {token_path}")
            continue

        expected_tokens = list(iter_expected_tokens(numbered, tokenized_canto))
        if not expected_tokens:
            error(q, "no reference tokens for numbered lines")
            continue

        if not (0 <= gemini.chat_count < args.interval):
            gemini.init(args.model, history, think=args.think)

        skeleton = build_skeleton_table(header, expected_tokens)
        prompt = build_prompt([raw for _ln, _text, raw in numbered], skeleton)

        qq = gemini.query(
            prompt,
            info=q.info,
            show=args.show,
            retry=args.retry,
        )

        if qq.result:
            qq.result = common.fix_table(qq.result) or qq.result
            qq.error = None
            qs_ok.append(qq)
            common.write_queries(ok_path, qs_ok, count=len(qs_ok))
        else:
            error(qq)

    print(f"OK: {len(qs_ok)}, NG: {len(qs_ng)}", file=sys.stderr)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
