# Tokenize - Italian Tokenizer

## Purpose

Create an Italian tokenizer for accurate validation of word tables in `word/`.

## Background

The current `split_table` uses simple string search to find words, which has the following issues:

- Apostrophe variations (`’l` vs `l’`)
- Ambiguous word boundary recognition
- Difficult error correction

## Plan

### Phase 1: Tokenizer Implementation

Create a function to split Italian text into tokens:

- Words (alphabetic characters + apostrophes)
- Numbers
- Punctuation
- Whitespace

**Status**: Completed.
- `tokenizer.py`: Implemented (apostrophe-aware tokenization + U+2019 normalization via `convert_apostrophe`)
- `test.py`: 23 tests from analysis.md; `make test` passes

### Phase 2: Line-by-Line Analysis of Italian Source Texts

Analyze each line of the Italian sources in `it/` from a tokenization perspective only
(initial focus was `it/inferno/01.txt`):

1. Identify tokenization patterns and boundaries
2. Document apostrophe variations and elision cases
3. Note any exceptional patterns or difficult cases
4. Create examples of tokenization rules

**Status**: Completed.
- `analysis.md`: Tokenization rules/examples/character-set notes; analysis covers all Italian source texts

### Phase 3: Improved Table Validation

1. Tokenize prompt lines
2. Tokenize table words
3. Compare at token level
   - Exact match
   - Partial match (for elisions)

**Status**: Completed.
- Implemented in `word/check.py` (token-level validation against `tokenize/<cantica>/<canto:02d>.txt`).
- Measured mismatch rates (table-level failures):
   - gemma3-it: 934 / 4811 (19.4%)
   - gptoss-it: 1395 / 4811 (29.0%)

### Phase 4: Table Re-run (Regeneration)

When the mismatch rate is relatively low (e.g. well below 1/3 of rows), it is
often more effective to re-run the LLM with a stricter, table-in-prompt format
than to build a complex heuristic auto-fixer.

1. Re-run failed queries by embedding the expected output table format in the prompt
   (similar to how word-tr/word-tr.py includes a markdown table in the prompt)
2. Constrain the model to output the full table in the exact same structure/format
   (table-level re-generation; do not attempt row-level patching)
3. Re-validate with the tokenizer-based checker and iterate until clean

Note:
    A heuristic auto-fixer can still be added later, but it should be treated as
    an optional optimization rather than the primary recovery path.

## File Structure

```
tokenize/
├── README.md
├── Makefile
├── analysis.md
├── test.py                       # Tokenizer tests (23 test cases)
├── tokenizer.py                  # Tokenizer + apostrophe normalization
│   ├── inferno/{01..34}.txt      # Generated token lists
│   ├── purgatorio/{01..33}.txt   # Generated token lists
│   ├── paradiso/{01..33}.txt     # Generated token lists
│   ├── quote_cases.txt           # Input for U+2019 disambiguation
│   └── quote_cases_converted.txt # Used by `convert_apostrophe`
├── chars.py                      # Character enumeration utility
│   └── chars.txt                 # Generated character list (saved output)
└── check_quotes.py               # Generate/validate quote-case conversion via LLM
   ├── quote_cases.txt
   ├── quote_cases_converted.txt
   └── quote_cases.xml
```

## References

- Current implementation: `split_table` in `dantetool/common.py`
- Usage: `word/check.py`
- Text source: `read_all()` in `tokenize/chars.py`
