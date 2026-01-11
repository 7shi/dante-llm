# Translation Workflow

This directory contains the translation workflow for Dante's Divine Comedy using LLM.

## translate.py

The main translation script that uses the Gemini API to translate Italian text into various target languages.

### Initial Setup

Before running translations, create an `init.xml` file with example translations:

```bash
uv run translate.py -m <model> --init "<language>" <srcdir> <outdir>
```

Example:
```bash
uv run translate.py -m gemini-2.0-flash-exp --init "English" it .
```

### Running Translations

Once `init.xml` exists:

```bash
uv run translate.py -m <model> "<language>" <srcdir> <outdir>
```

### Options

- `-m MODEL` - Specify the Gemini model (required)
- `--init` - Create init.xml and exit
- `-d DIRECTORIES` - Specify subdirectories (default: inferno purgatorio paradiso)
- `-i INIT` - Specify init.xml path (default: init.xml)
- `-n INTERVAL` - Chat session reset interval (default: 10)
- `-r RANGEMAX` - Maximum canto range (default: 35)
- `-1` - Process only one canto
- `--no-retry` - Don't retry failed queries
- `--no-show` - Don't show queries and responses
- `--no-think` - Don't include AI thoughts
- `--need-space` - Require at least one space per line
- `-3` - Always send 3 lines at a time

### System Prompt

Translation behavior is controlled by `system.txt`:

```
Provide only the translated text without any explanations, notes, or commentary.
Include the line numbers exactly as they appear in the source text.
```

## split.py

A utility script for splitting queries and checking line number consistency in translation XML files.

### Usage

```bash
uv run split.py [-c <check-type>] <files...>
```

### Check Types

- `-c 0` (default): Split queries into 3-line units
- `-c 1`: Check line consistency and split into individual lines
- `-c 2`: Check line number consistency only (used by `make check`)

### Examples

```bash
# Split queries into 3-line units
uv run split.py inferno/*.xml

# Check line number consistency
uv run split.py -c 2 inferno/*.xml
```

## compare.py

A utility script for generating comparison documents that show the original Italian text alongside translations from multiple models.

### Usage

```bash
uv run compare.py <path> [<path> ...]
```

The path should be specified without extension (e.g., `inferno/01` instead of `inferno/01.xml`).

### Output

Generates markdown files in `comparison/` with HTML tables comparing:
1. Original Italian text (Dante)
2. English translations (*-en models)
3. Japanese translations (*-ja models)

Lines are grouped by 3 for easier comparison.

### Examples

```bash
# Single canto
uv run compare.py inferno/01

# Multiple cantos
uv run compare.py inferno/01 inferno/02 purgatorio/01

# All cantos (via Makefile)
make compare
```

Output: `comparison/inferno/01.md`, etc.

## Overview

The translation process is divided into several stages to handle errors and improve translation quality.

## Processing Flow

### 1. Initial Translation (translate.py)

`translate.py` automatically divides the source text into queries based on **sentence boundaries (periods)**.

- By default, it attempts to include up to 3 lines per query
- If the 3rd line doesn't end with a period, it continues adding lines until it finds a period
- This ensures queries are divided at natural sentence boundaries

**Example:**
```
Query 1: Lines 1-3 (ends with period)
Query 2: Lines 4-9 (continues until line 9 ends with period)
Query 3: Lines 10-12 (ends with period)
```

### 2. Error Checking (check)

After translation, check line number consistency and collect errors:

```bash
make check
```

This performs two steps:
1. **Line number validation** (`split.py -c 2`): Checks if prompt and result have matching line numbers. Queries with mismatched line numbers are marked as errors.
2. **Error collection** (`dantetool pickup`): Extracts all failed queries into `1-error.xml`.

The combined result is `1-error.xml` containing all queries that failed, have no results, or have line number mismatches.

### 3. Retry Errors (redo)

Retry the failed queries while **maintaining the original query boundaries**:

```bash
make redo
```

- The `redo` process preserves the sentence-based divisions created by translate.py
- This maintains consistency and context
- Results are saved to `1-error-ok.xml` (successful) and `1-error-ng.xml` (still failed)

### 4. Replace Fixed Queries (replace)

Apply the successfully retried queries back to the original files:

```bash
make replace
```

## Complete Workflow (common.mk)

### Design Philosophy

This workflow may appear complex, but it follows a simple principle: **extract problematic queries for isolated fixing rather than constantly rewriting the entire source files**.

Continuously rewriting source files makes editing difficult. Instead, this workflow:
1. Identifies errors and extracts them into `1-error.xml`
2. Fixes only the problematic queries
3. Writes back only the fixed queries to source files

This approach minimizes disruption to successfully translated content and makes manual intervention easier when needed.

### Basic Workflow

The typical workflow follows this pattern:

```bash
# 1. Initial setup and translation
make init MODEL=model-name LANG="Target Language"
make                           # Equivalent to: make run check
```

`make` (without arguments) executes `make run check`:
- **make run**: Translates text divided by sentence boundaries (periods)
- **make check**: Validates line numbers and extracts errors into `1-error.xml`

### Error Recovery Workflow

When `make check` finds errors, retry them and apply fixes:

```bash
# 2. Retry errors and apply fixes
make redo MODEL=model-name     # Retries 1-error.xml → generates 1-error-ok.xml
make replace                   # Writes 1-error-ok.xml back to source files
make check                     # Verify no errors remain
```

**Alternative verification:** Use `make redo-fix` to check `1-error-ok.xml` for errors without writing back to source files.

Repeat this cycle until errors are minimized.

### Advanced: Handling Persistent Errors

If repeated `make redo` cycles fail to resolve errors, use finer-grained splitting:

#### Option 1: Split into 3-line units (Restructures source files)

```bash
make split                     # Restructures source files into 3-line units
make redo MODEL=model-name
make replace
make check
```

**Important:** `make split` **restructures the source files** by dividing queries into 3-line units regardless of sentence boundaries. This increases success rate by using smaller units, but may cause contextual issues due to unnatural splitting points.

#### Option 2: Force 1-line translation (Splits error processing only)

```bash
make redo1 MODEL=model-name    # Forces 1-line-at-a-time translation of 1-error.xml
make replace
make check
```

**Key difference:** `make redo1` **splits the processing of 1-error.xml** into individual lines but **does not restructure the source files**. This is less intrusive than `make split`.

### Workflow Summary

| Command | Action | Notes |
|---------|--------|-------|
| `make` | Run translation + check errors | Same as `make run check` |
| `make run` | Translate by sentence boundaries | Initial translation |
| `make check` | Validate line numbers, extract errors | Creates `1-error.xml` |
| `make redo` | Retry errors | Preserves sentence boundaries |
| `make replace` | Apply fixes to source files | Writes back `1-error-ok.xml` |
| `make redo-sweep` | Auto-retry with increasing temperature | 0.1→1.0, stops when errors clear |
| `make redo-loop` | Auto-retry up to 10 times at temp 1.0 | High variation, stops when errors clear |
| `make split` | **Restructure source files** into 3-line units | Higher success rate, potential context issues |
| `make redo1` | **Split error processing** into 1-line units | Does not restructure source files |
| `make redo-fix` | Check fixes without writing back | Validates `1-error-ok.xml` only |

### Best Practices

1. Start with `make` (sentence-based translation)
2. Use `make redo` → `make replace` cycles for error recovery
3. Only use `make split` when repeated `make redo` fails (last resort)
4. Consider `make redo1` before `make split` if you want to avoid restructuring source files

### Advanced Tips

#### Manual Editing

`1-error-ok.xml` is designed to support manual editing when automated retries fail. You can directly edit the XML file to correct translations before running `make replace`.

#### Adjusting Temperature

The default temperature is set to 0.1 in `gemini.py` for reproducibility. If repeated retries produce identical errors, increase the temperature to introduce more variation:

```bash
# Increase temperature to 0.5 for more creative translations
make redo OPTIONS="-t 0.5" MODEL=model-name

# Higher temperature for very stubborn errors
make redo OPTIONS="-t 1.0" MODEL=model-name
```

Higher temperature values make the LLM output more varied but potentially less consistent. Use this technique when the same error occurs repeatedly at low temperature.

#### Automated Temperature Sweeping

For stubborn errors that persist across multiple manual retries, use automated retry strategies:

**Temperature Sweep (redo-sweep):**
```bash
make redo-sweep MODEL=model-name
```

Automatically retries with gradually increasing temperature from 0.1 to 1.0:
- Starts at 0.1 (reproducible, consistent)
- Increments by 0.1 each iteration
- Stops when all errors are resolved (`count="0"`)
- Useful when you're unsure what temperature will work

**High-Temperature Loop (redo-loop):**
```bash
make redo-loop MODEL=model-name
```

Retries up to 10 times with temperature fixed at 1.0:
- Maximum variation to escape repetitive error patterns
- Each iteration may produce different results
- Stops when all errors are resolved
- Useful when errors persist even at high temperatures

Both commands automatically run the `redo → replace → check` cycle and stop as soon as errors are cleared.
