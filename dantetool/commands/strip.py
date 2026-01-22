import sys
import re
import argparse
from pathlib import Path
from dantetool import common

def add_args(parser):
    parser.add_argument("targets", nargs="+", type=str,
                        help="target XML files to strip")
    parser.add_argument("--strict", action="store_true",
                        help="disallow automatic column adjustment")
    parser.add_argument("--validate-tokens", action="store_true",
                        help="validate Word column against tokenize/ reference data")
    parser.add_argument("--replace-prompt", action="store_true",
                        help="replace prompt numbered lines with canonical canto text from tokenize/")

def extract_cantica_canto(target_path):
    """Extract cantica name and canto number from file path.

    Expected path format: .../cantica/canto.xml
    Example: word/gemini1-it/inferno/22.xml -> ("inferno", 22)

    Returns:
        tuple[str, int] | None: (cantica, canto_no) or None if cannot parse
    """
    p = Path(target_path)
    try:
        cantica = p.parent.name  # e.g. "inferno"
        canto_no = int(p.stem)    # e.g. 22 from "22.xml"
        if cantica in ["inferno", "purgatorio", "paradiso"]:
            return cantica, canto_no
    except (ValueError, AttributeError):
        pass
    return None

def find_tokenize_dir(start_path):
    """Find tokenize/ directory by walking up from start_path.

    Searches parent directories for a "tokenize" directory.

    Returns:
        Path | None: Path to tokenize/ directory or None if not found
    """
    current = Path(start_path).resolve()
    # Walk up to 5 levels (should be enough for any reasonable project structure)
    for _ in range(5):
        current = current.parent
        tokenize_dir = current / "tokenize"
        if tokenize_dir.is_dir():
            return tokenize_dir
    return None

def load_tokenized_canto(target_path):
    """Load tokenized reference data for a given XML file.

    Returns:
        list[list[str]] | None: Tokenized canto data or None if unavailable
    """
    location = extract_cantica_canto(target_path)
    if not location:
        return None

    cantica, canto_no = location
    tokenize_dir = find_tokenize_dir(target_path)
    if not tokenize_dir:
        return None

    token_path = tokenize_dir / cantica / f"{canto_no:02d}.txt"
    try:
        return common.read_tokenized_source(str(token_path))
    except FileNotFoundError:
        return None

def fix_token(token):
    """Normalize token text for comparison.

    The reference tokens under tokenize/ are produced from the original Italian
    text, where U+2019 (RIGHT SINGLE QUOTATION MARK, ') can appear in two roles:

    - Apostrophe used for elision (e.g. l', com')
    - Closing quotation mark (paired with an opening quote)

    These two roles are visually similar and are often represented by the same
    code point in the source. To compare LLM-generated tokens (which typically
    use ASCII apostrophe) with the pre-tokenized reference, we normalize U+2019
    to ASCII apostrophe.
    """
    return token.replace("\u2019", "'")

def replace_prompt_in_query(q, canto):
    """Replace numbered lines in prompt with canonical canto text.

    Args:
        q: Query object with prompt field
        canto: Tokenized canto data (list of lines, each split by '|')

    Returns:
        bool: True if any replacement occurred, False otherwise
    """
    new_prompt_lines = []
    has_numbered_lines = False

    for raw in q.prompt.split("\n"):
        if m := re.match(r"(\d+)\s+(.*)", raw):
            has_numbered_lines = True
            line_no = int(m.group(1))
            if 1 <= line_no <= len(canto):
                canto_text = canto[line_no - 1][0]
                new_prompt_lines.append(f"{line_no} {canto_text}")
            else:
                new_prompt_lines.append(raw)
        else:
            new_prompt_lines.append(raw)

    if not has_numbered_lines:
        # Fallback: try to extract line numbers from query.info
        parsed = common.parse_info(q.info or "")
        if not parsed:
            print(f"Error: no numbered lines found in prompt for {q.info}", file=sys.stderr)
            return False
        # Extract line numbers from info and build prompt with canonical text
        _, _, line_no, total_lines = parsed
        line_numbers = list(range(line_no, min(line_no + 2, total_lines) + 1))
        new_prompt_lines = []
        for ln in line_numbers:
            if 1 <= ln <= len(canto):
                canto_text = canto[ln - 1][0]
                new_prompt_lines.append(f"{ln} {canto_text}")

    new_prompt = "\n".join(new_prompt_lines)
    if new_prompt != q.prompt:
        q.prompt = new_prompt
        return True

    return False

def validate_table_with_tokens(numbered_lines, table, canto):
    """Validate a fixed word table against tokenized reference data.

    Args:
        numbered_lines:
            Output of common.extract_numbered_lines(q.prompt): a list of
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
    """
    # Extract target tokens (Word column values; header rows skipped)
    # Tokens are expected to be normalized already by fix_token().
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

def process_file_with_token_validation(target, canto, replace_prompt=False):
    """Process a single XML file: normalize tables and validate against tokens.

    Args:
        target: Path to XML file
        canto: Tokenized canto data
        replace_prompt: Whether to replace prompts with canonical text

    Returns:
        A list of (q.info, errors) tuples.
        - errors is a list of TokenError records returned by validate_table_with_tokens().
    """
    qs = common.read_queries(target)
    all_errors = []
    modified = False

    def error(q, message=None):
        """Mark a query as error by moving result to error."""
        nonlocal modified
        if message:
            print(f"Error: {message} {q.info}")
        q.error = q.result
        q.result = None
        modified = True

    for q in qs:
        if not q.result:
            continue

        # Extract numbered lines from prompt
        numbered_lines = common.extract_numbered_lines(q.prompt)
        if not numbered_lines:
            # Fallback: try to extract line numbers from query.info
            parsed = common.parse_info(q.info or "")
            if not parsed:
                error(q, "no numbered lines found in prompt for")
                continue
            # Extract line numbers from info: [Cantica Canto N] line_no/total_lines
            _, _, line_no, total_lines = parsed
            line_numbers = list(range(line_no, min(line_no + 2, total_lines) + 1))
            # Build numbered_lines from canonical canto text
            numbered_lines = []
            for ln in line_numbers:
                if 1 <= ln <= len(canto):
                    canto_text = canto[ln - 1][0]
                    numbered_lines.append((ln, canto_text, f"{ln} {canto_text}"))

        # Replace prompt with canonical canto text if requested
        if replace_prompt:
            new_prompt_lines = []
            for raw in q.prompt.split("\n"):
                if m := re.match(r"(\d+)\s+(.*)", raw):
                    line_no = int(m.group(1))
                    if 1 <= line_no <= len(canto):
                        canto_text = canto[line_no - 1][0]
                        new_prompt_lines.append(f"{line_no} {canto_text}")
                    else:
                        new_prompt_lines.append(raw)
                else:
                    new_prompt_lines.append(raw)

            new_prompt = "\n".join(new_prompt_lines)
            if new_prompt != q.prompt:
                q.prompt = new_prompt
                modified = True

        # Parse table
        parsed_table = common.read_table(q.result)
        if not parsed_table:
            error(q, "could not parse table in")
            continue

        # Fix table format
        fixed_table = common.fix_table_rows(table=parsed_table)

        # Filter: remove non-alpha rows, apply fix_token
        table = []
        for i, row in enumerate(fixed_table):
            if i < 2:
                # Keep header and separator rows as is
                table.append(row)
            else:
                row[0] = fix_token(row[0])
                if common.has_alpha(row[0]):
                    table.append(row)

        # Update result
        orig_result = q.result
        orig_error = q.error
        q.result = common.table_to_string(table)
        q.error = None
        if q.result != orig_result or q.error != orig_error:
            modified = True

        # Validate tokens
        errors = validate_table_with_tokens(numbered_lines, table, canto)
        if errors is not None:
            error(q)
            all_errors.append((q.info, errors))

    # Write back if modified
    if modified:
        common.write_queries(target, qs, count=len(qs))

    return all_errors

def main_func(args):
    error_count = 0

    for target in args.targets:
        # Check if tokenize data is needed
        needs_tokenize = args.validate_tokens or args.replace_prompt

        if needs_tokenize:
            # Load tokenized reference data
            canto = load_tokenized_canto(target)
            if canto is None:
                # User preference: error if tokenize-dependent flag specified but data not found
                flag_name = "--validate-tokens" if args.validate_tokens else "--replace-prompt"
                print(f"Error: {flag_name} specified but no tokenized data for {target}",
                      file=sys.stderr)
                return 1  # Exit with error

            if args.validate_tokens:
                # Token validation mode (may also include prompt replacement)
                errors = process_file_with_token_validation(target, canto,
                                                           replace_prompt=args.replace_prompt)
                for info, token_errors in errors:
                    for token_error in token_errors:
                        print(f"{target} {info}: {token_error}", file=sys.stderr)
                    error_count += len(token_errors)
            elif args.replace_prompt:
                # Prompt replacement only (no token validation)
                qs = common.read_queries(target)
                modified = False
                for q in qs:
                    if q.result and replace_prompt_in_query(q, canto):
                        modified = True
                if modified:
                    common.write_queries(target, qs, count=len(qs))
        else:
            # Basic format validation (existing behavior)
            qs = common.read_queries(target)
            for q in qs:
                if q.result:
                    table = common.fix_table(q.result, strict=args.strict)
                    if table:
                        q.result = table
                        q.error = None
                    else:
                        print(f"Error: could not parse table in {q.info}")
                        q.error = q.result
                        q.result = None
            common.write_queries(target, qs, count=len(qs))

    if error_count:
        print(f"Total word position errors: {error_count}", file=sys.stderr)

    return 0

def main(argv=None):
    parser = argparse.ArgumentParser(description="Strip table content from XML files")
    add_args(parser)
    args = parser.parse_args(argv)
    return main_func(args)

if __name__ == "__main__":
    sys.exit(main())
