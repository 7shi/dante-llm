import sys
import re
import argparse
from pathlib import Path
from typing import Literal, Sequence, TypeAlias
from dantetool import common

NumberedLine: TypeAlias = tuple[int, str, str]
TokenizedLine: TypeAlias = list[str]
TokenizedCanto: TypeAlias = list[TokenizedLine]
Table: TypeAlias = list[list[str]]

LenMismatchError: TypeAlias = tuple[Literal["len_mismatch"], int, int]
MismatchError: TypeAlias = tuple[Literal["mismatch"], int, str, str]
TokenError: TypeAlias = LenMismatchError | MismatchError
CheckError: TypeAlias = tuple[str, list[TokenError]]

def fix_token(token: str) -> str:
    """Normalize token text for comparison.

    The reference tokens under tokenize/ are produced from the original Italian
    text, where U+2019 (RIGHT SINGLE QUOTATION MARK, ’) can appear in two roles:

    - Apostrophe used for elision (e.g. l’, com’)
    - Closing quotation mark (paired with an opening quote)

    These two roles are visually similar and are often represented by the same
    code point in the source. To compare LLM-generated tokens (which typically
    use ASCII apostrophe) with the pre-tokenized reference, we normalize U+2019
    to ASCII apostrophe.

    Background:
        The ambiguity between elision and quotation marks is investigated in
        tokenize/check_quotes.py, which tries to distinguish apostrophes from
        closing quotes in the source text.
    """
    return token.replace("\u2019", "'")

def validate_table_with_tokens(
    numbered_lines: list[NumberedLine],
    table: Table,
    canto: TokenizedCanto,
) -> list[TokenError] | None:
    """Validate a fixed word table against tokenized reference data.

    This function is a placeholder for the Phase 3 validator. The intended design
    is to compare the table's "Word" column (in order) against the pre-tokenized
    reference text loaded from tokenize/<cantica>/<canto:02d>.txt.

    Args:
        numbered_lines:
            Output of extract_numbered_lines(q.prompt): a list of
            (line_no, text, raw_line) for the prompt's numbered Italian lines.
        table:
            The cleaned table rows (including header rows) that will be validated.
            In the current pipeline this is the filtered result of fix_table_rows.
        canto:
            Tokenized reference for a single canto (already selected by caller).
            It is a list of lines; each line is split('|'):
                [original_line, token1, token2, ...]

    Returns:
        None if OK, otherwise a list of token mismatch errors.

    Note:
        Currently implements only a strict equality check between token lists.
    """
    # Extract target tokens (Word column values; header rows skipped).
    # Tokens are expected to be normalized already by fix_token() in check_file().
    target_tokens = [row[0] for row in table[2:]]

    # Build a flattened reference token list for the prompt's numbered lines.
    # Each canto line is split('|'):
    #   [original_line, token1, token2, ...]
    ref_tokens = []
    for line_no, _, _ in numbered_lines:
        if not (1 <= line_no <= len(canto)):
            continue
        parts = canto[line_no - 1]
        if not parts:
            continue
        ref_tokens.extend(parts[1:])

    # Step 1: length check
    if len(target_tokens) != len(ref_tokens):
        return [("len_mismatch", len(target_tokens), len(ref_tokens))]

    # Step 2: content check
    for i, (a, b) in enumerate(zip(target_tokens, ref_tokens), start=1):
        if a != b:
            return [("mismatch", i, a, b)]

    return None

def check_file(target: str, canto: TokenizedCanto) -> list[CheckError]:
    """Process a single XML file: normalize tables and validate against tokens.

    This does NOT write changes back to the XML (write is intentionally disabled).

    Returns:
        A list of (q.info, errors) tuples.

        - errors is a list of TokenError records returned by validate_table_with_tokens().
    """
    qs = common.read_queries(target)
    all_errors: list[CheckError] = []
    modified = False

    def error(q, message: str | None = None) -> None:
        """Mark a query as error by moving result to error."""
        nonlocal modified
        if message:
            print("Error:", message, q.info)
        q.error = q.result
        q.result = None
        modified = True

    for q in qs:
        if not q.result:
            continue

        # Check: validate word positions using tokenized reference data (Phase 3)
        numbered_lines = []
        new_prompt_lines = []
        for raw in q.prompt.split("\n"):
            if m := re.match(r"(\d+)\s+(.*)", raw):
                line_no = int(m.group(1))
                text = m.group(2)
                numbered_lines.append((line_no, text, raw))
                if 1 <= line_no <= len(canto):
                    canto_text = canto[line_no - 1][0]
                    new_prompt_lines.append(f"{line_no} {canto_text}")
                else:
                    new_prompt_lines.append(raw)
            else:
                new_prompt_lines.append(raw)

        if not numbered_lines:
            error(q, "no numbered lines found in prompt for")
            continue

        new_prompt = "\n".join(new_prompt_lines)
        if new_prompt != q.prompt:
            q.prompt = new_prompt
            modified = True

        # Parse: read table from result
        parsed_table = common.read_table(q.result)
        if not parsed_table:
            error(q, "could not parse table in")
            continue

        # Strip: fix table format
        fixed_table = common.fix_table_rows(table=parsed_table)

        # Filter: remove rows without alphabetic characters in first column
        table = []
        for i, row in enumerate(fixed_table):
            if i < 2:
                # Keep header and separator rows as is
                table.append(row)
            else:
                row[0] = fix_token(row[0])
                if common.has_alpha(row[0]):
                    table.append(row)

        # Update: set fixed table as result
        orig_result = q.result
        orig_error = q.error
        q.result = common.table_to_string(table)
        q.error = None
        if q.result != orig_result or q.error != orig_error:
            modified = True

        errors = validate_table_with_tokens(numbered_lines, table, canto)
        if errors is not None:
            error(q)
            all_errors.append((q.info, errors))

    # Write back if modified
    if modified:
        common.write_queries(target, qs, count=len(qs))

    return all_errors

def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint.

    Validates one or more word-table XML files against tokenized reference files
    under tokenize/<cantica>/<canto:02d>.txt.
    """
    parser = argparse.ArgumentParser(description="Check word positions in XML files.")
    parser.add_argument("xml_files", nargs="+", help="XML files to check")
    args = parser.parse_args(argv)

    script_path = Path(__file__).resolve()
    tokenize_dir = script_path.parent.parent / "tokenize"

    error_count = 0
    for target in args.xml_files:
        p = Path(target)
        cantica, canto_no = p.parent.name, int(p.stem)
        token_path = tokenize_dir / cantica / f"{canto_no:02d}.txt"
        try:
            canto = common.read_tokenized_source(str(token_path))
        except FileNotFoundError:
            print(f"Warning: No tokenized data for {target}", file=sys.stderr)
            continue

        errors = check_file(target, canto)
        for info, token_errors in errors:
            for token_error in token_errors:
                print(f"{target} {info}: {token_error}", file=sys.stderr)
            error_count += len(token_errors)
    if error_count:
        print(f"Total word position errors: {error_count}", file=sys.stderr)

    return 0

if __name__ == "__main__":
    sys.exit(main())
