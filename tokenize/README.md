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

### Phase 4: Auto-correction

1. Classify mismatch patterns
2. Generate correction candidates
3. Auto-correct based on confidence

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
