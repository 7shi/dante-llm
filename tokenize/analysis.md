# Tokenization Analysis of it/inferno/01.txt

## Overview

This document provides a detailed tokenization analysis of the first canto of Dante's Inferno (`it/inferno/01.txt`). The analysis focuses on tokenization patterns, apostrophe handling, and special cases that must be addressed for accurate Italian tokenization.

## Text Source

The text is obtained through `read_all()` in `tokenize/chars.py`, which reads all Italian text files from the `it/` directory on a per-line basis.

## Tokenization Rules

### 1. Basic Tokenization

1. Split by spaces first
2. Separate punctuation marks (`,`, `.`, `!`, `;`, `:`, `?`, `«`, `»`, etc.)
3. Handle apostrophe cases (see below)
4. Preserve special characters (e.g., `ï` in `Ilïón`, `sapïenza`)
5. **Critical**: Spaces must be preserved as separate tokens for exact reconstruction

### 2. Apostrophe Handling

Apostrophes in Italian text appear in various positions and must be handled carefully:

| Position | Example | Treatment | Notes |
|----------|---------|-----------|-------|
| End of word | `Tant’` | Keep with preceding word | Elision of `tanto` |
| Middle of word | `ch’i’`, `v’ho` | Keep as part of word | Elision of `che io`, `vi ho` |
| Beginning of word | `l’altre` | Keep with following word | Elision of `le altre` |
| Beginning of word | `’mpediva`, `’l`, `’n` | Keep as part of word | Elision of `impediva`, `il`, `in` |

### 3. Punctuation

All punctuation marks should be separated as individual tokens:

- `,` (comma)
- `.` (period)
- `!` (exclamation mark)
- `;` (semicolon)
- `:` (colon)
- `?` (question mark)
- `«` (opening guillemet)
- `»` (closing guillemet)

### 4. Character Set

Based on analysis of `tokenize/chars.txt`, the following character categories are used:

#### Punctuation and Symbols
- Space (U+0020)
- Exclamation mark `!` (U+0021)
- Left parenthesis `(` (U+0028)
- Right parenthesis `)` (U+0029)
- Comma `,` (U+002C)
- Hyphen `-` (U+002D)
- Period `.` (U+002E)
- Colon `:` (U+003A)
- Semicolon `;` (U+003B)
- Question mark `?` (U+003F)
- Left guillemet `«` (U+00AB)
- Right guillemet `»` (U+00BB)
- Em dash `—` (U+2014)

#### Quotation Marks
- Left single quotation mark `‘` (U+2018)
- Right single quotation mark `’` (U+2019)
- Left double quotation mark `“` (U+201C)
- Right double quotation mark `”` (U+201D)

#### Apostrophes (Ambiguous Characters)

The following characters serve as apostrophes in Italian text:

- Right single quotation mark `’` (U+2019) - **Ambiguous**: Can function as both apostrophe (elision) and closing quotation mark
  - Example: `‘Tu m’appaghe’` - Here `’` serves as closing quotation mark
  - Example: `Tant’` - Here `’` (or similar) serves as apostrophe for elision

**Tokenization Strategy**:
1. When `’` (U+2019) appears after a word (e.g., `Tant’`), treat as apostrophe/elision
2. When `’` (U+2019) appears as closing quote (e.g., after `‘`), treat as punctuation
3. Context matters: Use surrounding characters to determine function

#### Special Characters (within words)
- `È` (E with grave, U+00C8)
- `Ë` (E with diaeresis, U+00CB)
- `Ï` (I with diaeresis, U+00CF)
- `à` (a with grave, U+00E0)
- `ä` (a with diaeresis, U+00E4)
- `è` (e with grave, U+00E8)
- `é` (e with acute, U+00E9)
- `ë` (e with diaeresis, U+00EB)
- `ì` (i with grave, U+00EC)
- `ï` (i with diaeresis, U+00EF) - **Important**: Appears in `Ilïón`, `sapïenza`
- `ò` (o with grave, U+00F2)
- `ó` (o with acute, U+00F3)
- `ö` (o with diaeresis, U+00F6)
- `ù` (u with grave, U+00F9)
- `ü` (u with diaeresis, U+00FC)

**Note**: Alphabetic characters (A-Z, a-z) are not listed individually for brevity.

## Tokenization Examples

### Simple Cases

Line 1: `Nel mezzo del cammin di nostra vita`
- Tokens: `["Nel", " ", "mezzo", " ", "del", " ", "cammin", " ", "di", " ", "nostra", " ", "vita"]`

Line 2: `mi ritrovai per una selva oscura,`
- Tokens: `["mi", " ", "ritrovai", " ", "per", " ", "una", " ", "selva", " ", "oscura", ","]`

### Apostrophe at End

Line 7: `Tant' è amara che poco è più morte;`
- Tokens: `["Tant'", " ", "è", " ", "amara", " ", "che", " ", "poco", " ", "è", " ", "più", " ", "morte", ";"]`

### Apostrophe in Middle

Line 8: `ma per trattar del ben ch'i' vi trovai,`
- Tokens: `["ma", " ", "per", " ", "trattar", " ", "del", " ", "ben", " ", "ch'", "i'", " ", "vi", " ", "trovai", ","]`

Line 9: `dirò de l'altre cose ch'i' v'ho scorte.`
- Tokens: `["dirò", " ", "de", " ", "l'", "altre", " ", "cose", " ", "ch'", "i'", " ", "v'", "ho", " ", "scorte", "."]`

### Multiple Apostrophes

Line 10: `Io non so ben ridir com' i' v'intrai,`
- Tokens: `["Io", " ", "non", " ", "so", " ", "ben", " ", "ridir", " ", "com'", " ", "i'", " ", "v'", "intrai", ","]`

### Apostrophe at Beginning

Line 13: `Ma poi ch'i' fui al piè d'un colle giunto,`
- Tokens: `["Ma", " ", "poi", " ", "ch'", "i'", " ", "fui", " ", "al", " ", "piè", " ", "d'", "un", " ", "colle", " ", "giunto", ","]`

Line 17: `vestite già de' raggi del pianeta`
- Tokens: `["vestite", " ", "già", " ", "de'", " ", "raggi", " ", "del", " ", "pianeta"]`

Line 24: `si volge a l'acqua perigliosa e guata,`
- Tokens: `["si", " ", "volge", " ", "a", " ", "l'", "acqua", " ", "perigliosa", " ", "e", " ", "guata", ","]`

Line 35: `anzi 'mpediva tanto il mio cammino,`
- Tokens: `["anzi", " ", "'mpediva", " ", "tanto", " ", "il", " ", "mio", " ", "cammino", ","]`

Line 38: `e 'l sol montava 'n sù con quelle stelle`
- Tokens: `["e", " ", "'l", " ", "sol", " ", "montava", " ", "'n", " ", "sù", " ", "con", " ", "quelle", " ", "stelle"]`

Line 45: `la vista che m'apparve d'un leone.`
- Tokens: `["la", " ", "vista", " ", "che", " ", "m'", "apparve", " ", "d'", "un", " ", "leone", "."]`

### Quotation Marks

Line 65: `«Miserere di me», gridai a lui,`
- Tokens: `["«", " ", "Miserere", " ", "di", " ", "me", " ", "»", ",", " ", "gridai", " ", "a", " ", "lui", ","]`

### Special Characters

Line 75: `poi che 'l superbo Ilïón fu combusto.`
- Tokens: `["poi", " ", "che", " ", "'l", " ", "superbo", " ", "Ilïón", " ", "fu", " ", "combusto", "."]`

Line 104: `ma sapïenza, amore e virtute,`
- Tokens: `["ma", " ", "sapïenza", ",", " ", "amore", " ", "e", " ", "virtute", ","]`

Line 110: `fin che l'avrà rimessa ne lo 'nferno,`
- Tokens: `["fin", " ", "che", " ", "l'", "avrà", " ", "rimessa", " ", "ne", " ", "lo", " ", "'nferno", ","]`

### Combined with quotation marks

Purgatorio Canto 15 Line 82: `Com' io voleva dicer \u2018Tu m'appaghe\u2019,`
- Tokens: `["Com'", " ", "io", " ", "voleva", " ", "dicer", " ", "\u2018", "Tu", " ", "m'", "appaghe", "\u2019", ","]`

## Key Tokenization Patterns

1. **Basic words**: Alphabetic characters separated by spaces
2. **Punctuation**: All punctuation marks should be separate tokens
3. **Elisions with apostrophe at end**: `Tant’` (elision of tanto)
4. **Elisions with apostrophe in middle**: `ch’i’` (elision of che io), `v’ho` (elision of vi ho)
5. **Elisions with apostrophe at beginning**: `l’altre` (elision of le altre), `’mpediva` (elision of impediva)
6. **Quotation marks**: `«` and `»` (guillemets) should be separate tokens
7. **Multiple apostrophes in sequence**: Each elision should be treated separately
8. **Special characters**: Preserve characters like `ï` within words

## Implementation Notes

1. **Space preservation**: Spaces must be preserved as separate tokens to allow exact reconstruction of the original text
2. **Token reconstruction**: The tokenizer should be verified by ensuring that simple concatenation of tokens (including spaces) reconstructs the original text
3. **Line-by-line processing**: Tokenization should be performed on a per-line basis, as specified by the text source format

## Summary

The tokenization of Italian text, particularly Dante's poetry, requires careful handling of:
- Apostrophes in various positions (end, middle, beginning of words)
- Punctuation marks (including guillemets)
- Special characters within words
- Space preservation for exact reconstruction

The tokenizer must be designed to handle these cases accurately to ensure correct word table validation in the `word/` directory.
