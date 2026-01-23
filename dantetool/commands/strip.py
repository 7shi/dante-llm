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

    # Validation options (mutually exclusive)
    validation_group = parser.add_mutually_exclusive_group()
    validation_group.add_argument("--validate-tokens", action="store_true",
                        help="validate Word column against tokenize/ reference data")
    validation_group.add_argument("--validate-source", type=str,
                        help="validate against source directory (e.g., '../word-tr/gemma3-it')")

    parser.add_argument("--validate-column", type=str, default=None,
                        help="column index to validate (0=Word, 1=Lemma, etc.). Comma-separated for multiple columns (e.g., '0,1'). Only valid with --validate-source")
    parser.add_argument("--replace-prompt", action="store_true",
                        help="replace prompt numbered lines with canonical canto text from tokenize/")

def parse_column_indices(column_spec):
    """Parse column specification string into list of integers.

    Args:
        column_spec: Column specification (e.g., '0', '0,1', '0,1,2')

    Returns:
        list[int]: List of column indices
    """
    try:
        return [int(c.strip()) for c in column_spec.split(',')]
    except ValueError:
        raise ValueError(f"Invalid column specification: {column_spec}")

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

def load_source_queries(target_path, source_dir):
    """Load source queries from a source directory (e.g., word-tr).

    Args:
        target_path: Path to the target XML file
        source_dir: Source directory containing reference data

    Returns:
        dict[str, Query] | None: Mapping from query.info to Query object
    """
    location = extract_cantica_canto(target_path)
    if not location:
        return None

    cantica, canto_no = location
    source_file = Path(source_dir) / cantica / f"{canto_no:02d}.xml"

    if not source_file.exists():
        return None

    # Read source queries and build info -> query mapping
    qs = common.read_queries(str(source_file))
    return {q.info: q for q in qs if q.result}

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

def load_reference_data(target, canto=None, source_queries=None, column_indices=None):
    """Load reference data and convert to common format.

    Args:
        target: Path to XML file
        canto: Tokenized canto data (for --validate-tokens)
        source_queries: Dict mapping info -> source Query (for --validate-source)
        column_indices: List of column indices to validate (e.g., [0, 1])

    Returns:
        dict[str, list[list[str]]]: Mapping from query.info to list of reference tokens for each column
    """
    if column_indices is None:
        column_indices = [0]
    # Read target queries to get all query.info
    qs = common.read_queries(target)
    reference_data = {}

    for q in qs:
        if not q.result:
            continue

        ref_tokens_per_column = []

        if source_queries is not None:
            # Extract from source query for each column
            source_q = source_queries.get(q.info)
            if not source_q:
                continue

            source_table = common.read_table(source_q.result)
            if not source_table or len(source_table) < 3:
                continue

            # Extract tokens for each column index
            for column_index in column_indices:
                col_tokens = []
                for row in source_table[2:]:  # Skip header and separator
                    if len(row) <= column_index:
                        continue
                    token = fix_token(row[column_index])
                    if common.has_alpha(token):
                        col_tokens.append(token)
                ref_tokens_per_column.append(col_tokens)

        elif canto is not None:
            # Extract from tokenize data (single column only - always column 0)
            # First, get numbered lines from prompt
            numbered_lines = common.extract_numbered_lines(q.prompt)
            if not numbered_lines:
                # Fallback: extract from query.info
                parsed = common.parse_info(q.info or "")
                if parsed:
                    _, _, line_no, total_lines = parsed
                    line_numbers = list(range(line_no, min(line_no + 2, total_lines) + 1))
                    numbered_lines = []
                    for ln in line_numbers:
                        if 1 <= ln <= len(canto):
                            canto_text = canto[ln - 1][0]
                            numbered_lines.append((ln, canto_text, f"{ln} {canto_text}"))

            col_tokens = []
            if numbered_lines:
                for line_no, _, _ in numbered_lines:
                    if not (1 <= line_no <= len(canto)):
                        continue
                    parts = canto[line_no - 1]
                    if not parts:
                        continue
                    # tokenize format: [original_line, token1, token2, ...]
                    col_tokens.extend(parts[1:])
            if col_tokens:
                ref_tokens_per_column.append(col_tokens)

        if ref_tokens_per_column:
            reference_data[q.info] = ref_tokens_per_column

    return reference_data

def validate_table_with_reference(table, ref_tokens_per_column):
    """Validate a table against reference tokens for multiple columns.

    Args:
        table: The table to validate (including header rows)
        ref_tokens_per_column: List of reference tokens for each column

    Returns:
        None if OK, otherwise a list of token mismatch errors.
    """
    # Validate each column
    for col_idx, ref_tokens in enumerate(ref_tokens_per_column):
        # Extract target tokens for this column (header rows skipped)
        target_tokens = [row[col_idx] for row in table[2:]]

        # Step 1: length check
        if len(target_tokens) != len(ref_tokens):
            return [("len_mismatch", col_idx, len(target_tokens), len(ref_tokens))]

        # Step 2: content check
        for i, (a, b) in enumerate(zip(target_tokens, ref_tokens), start=1):
            if a != b:
                return [("mismatch", col_idx, i, a, b)]

    return None

def process_file_with_validation(target, reference_data, canto=None, replace_prompt=False):
    """Process a single XML file: normalize tables and validate against reference.

    Args:
        target: Path to XML file
        reference_data: Dict mapping query.info -> reference tokens
        canto: Tokenized canto data (only for --replace-prompt)
        replace_prompt: Whether to replace prompts with canonical text

    Returns:
        A list of (q.info, errors) tuples.
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

        # Replace prompt with canonical canto text if requested
        if replace_prompt and canto is not None:
            numbered_lines = common.extract_numbered_lines(q.prompt)
            if not numbered_lines:
                # Fallback: extract from query.info
                parsed = common.parse_info(q.info or "")
                if parsed:
                    _, _, line_no, total_lines = parsed
                    line_numbers = list(range(line_no, min(line_no + 2, total_lines) + 1))
                    numbered_lines = []
                    for ln in line_numbers:
                        if 1 <= ln <= len(canto):
                            canto_text = canto[ln - 1][0]
                            numbered_lines.append((ln, canto_text, f"{ln} {canto_text}"))

            if numbered_lines:
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

        # Validate against reference data
        errors = None
        ref_tokens = reference_data.get(q.info)

        if ref_tokens is None:
            # No reference data for this query
            errors = [("no_reference", f"No reference data for {q.info}")]
        else:
            # Validate
            errors = validate_table_with_reference(table, ref_tokens)

        if errors is not None:
            error(q)
            all_errors.append((q.info, errors))

    # Write back if modified
    if modified:
        common.write_queries(target, qs, count=len(qs))

    return all_errors

def main_func(args):
    error_count = 0

    # Validate argument combinations
    if args.validate_tokens and args.validate_column is not None:
        print("Error: --validate-column cannot be used with --validate-tokens", file=sys.stderr)
        return 1

    if args.validate_source is not None and args.validate_column is None:
        print("Error: --validate-column is required with --validate-source", file=sys.stderr)
        return 1

    # Parse column indices
    column_indices = None
    if args.validate_column is not None:
        try:
            column_indices = parse_column_indices(args.validate_column)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    for target in args.targets:
        # Determine operation mode
        validate_mode = args.validate_tokens or args.validate_source is not None

        if validate_mode:
            # Validation mode: load reference data
            canto = None
            source_queries = None

            if args.validate_source:
                # Load source queries for validation
                source_queries = load_source_queries(target, args.validate_source)
                if source_queries is None:
                    print(f"Error: --validate-source specified but no source data for {target}",
                          file=sys.stderr)
                    return 1
            elif args.validate_tokens:
                # Load tokenized canto data (always validates column 0 only)
                canto = load_tokenized_canto(target)
                if canto is None:
                    print(f"Error: --validate-tokens specified but no tokenized data for {target}",
                          file=sys.stderr)
                    return 1
                # Always use column 0 for tokenize validation
                column_indices = [0]

            # Convert to common reference data format
            reference_data = load_reference_data(
                target, canto=canto, source_queries=source_queries,
                column_indices=column_indices)

            # Process with validation
            errors = process_file_with_validation(
                target, reference_data, canto=canto, replace_prompt=args.replace_prompt)

            for info, token_errors in errors:
                for token_error in token_errors:
                    print(f"{target} {info}: {token_error}", file=sys.stderr)
                error_count += len(token_errors)

        elif args.replace_prompt:
            # Prompt replacement only (no validation)
            canto = load_tokenized_canto(target)
            if canto is None:
                print(f"Error: --replace-prompt specified but no tokenized data for {target}",
                      file=sys.stderr)
                return 1

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
