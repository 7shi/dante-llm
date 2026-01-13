# Word Table Generation Workflow

This directory contains the word table generation workflow for Dante's Divine Comedy using LLM.

## init.py

Initialize word table generation by creating example word tables for training the model.

### Initial Setup

Before generating word tables, create an `init.xml` file with example word tables:

```bash
uv run init.py -m <model> "<language>" <srcdir>
```

Example:
```bash
uv run init.py -m gemini-2.0-flash-exp "Italian" ../../translate/it
```

### Options

- `-m MODEL` - Specify the Gemini model (required)
- `-t` - Test only (use existing init.xml)
- `-n` - Disable crasis (contractions) prompt
- `-c COLUMNS` - Specify table columns (default: "Word, Lemma, Part of Speech, Gender, Number, Person, Tense, Mood and Note")
- `-i INIT` - Specify init.xml path (default: init.xml)
- `-d SUBDIR` - Specify subdirectory to process (default: inferno)
- `--no-think` - Don't include AI thoughts

### How It Works

`init.py` creates training examples by:
1. Reading the first canto from the specified subdirectory
2. Optionally querying for contractions (if crasis is enabled)
3. Creating example word tables for selected lines (1, 9, 28, 67)
4. Generating test queries for the first 3 text units
5. Saving results to `init.xml` and `test.xml`

## word.py

The main word table generation script that uses the Gemini API to create word tables for Italian text.

### Running Word Table Generation

Once `init.xml` exists:

```bash
uv run word.py -m <model> "<language>" <srcdir> <outdir>
```

Example:
```bash
uv run word.py -m gemini-2.0-flash-exp "Italian" ../../translate/it .
```

### Options

- `-m MODEL` - Specify the Gemini model (required)
- `-d DIRECTORIES` - Specify subdirectories (default: inferno purgatorio paradiso)
- `-i INIT` - Specify init.xml path (default: init.xml)
- `-n INTERVAL` - Chat session reset interval (default: 10)
- `-r RANGEMAX` - Maximum canto range (default: 35)
- `-1` - Process only one canto
- `--no-retry` - Don't retry failed queries
- `--no-show` - Don't show queries and responses
- `--no-think` - Don't include AI thoughts

### Word Table Format

The generated word tables include the following columns:
- **Word**: The word as it appears in the text
- **Lemma**: The dictionary form (contractions decomposed)
- **Part of Speech**: Noun, verb, adjective, etc.
- **Gender**: Masculine/feminine (if applicable)
- **Number**: Singular/plural (if applicable)
- **Person**: 1st/2nd/3rd person (for verbs)
- **Tense**: Present, past, future, etc. (for verbs)
- **Mood**: Indicative, subjunctive, imperative, etc. (for verbs)
- **Note**: Additional notes (e.g., archaic)

## Overview

The word table generation process follows a similar workflow to translation, but focuses on creating linguistic analysis tables.

## Processing Flow

### 1. Initial Word Table Generation (word.py)

`word.py` processes the source text and generates word tables for each text unit.

- Reads text units from the source files
- For each unit, creates a detailed word table with lemmas and grammatical information
- Saves results to XML files in the output directory

### 2. Error Checking (check)

After generation, check for errors and collect failed queries:

```bash
make check
```

This command performs two steps:
1. **Strip**: Cleans up word tables by removing extraneous content after table ends and marking broken tables (those containing `||---`)
2. **Pickup**: Extracts all failed queries into `1-error.xml`

### 3. Retry Errors (redo)

Retry the failed queries:

```bash
make redo MODEL=model-name
```

Results are saved to `1-error-ok.xml` (successful) and `1-error-ng.xml` (still failed).

### 4. Replace Fixed Queries (replace)

Apply the successfully retried queries back to the original files:

```bash
make replace
```

## Complete Workflow (common.mk)

### Design Philosophy

This workflow follows the same principle as the translation workflow: **extract problematic queries for isolated fixing rather than constantly rewriting the entire source files**.

### Basic Workflow

The typical workflow follows this pattern:

```bash
# 1. Initial setup and word table generation
make init MODEL=model-name LANG="Language"
make                           # Equivalent to: make run check
```

`make` (without arguments) executes `make run check`:
- **make run**: Generates word tables for all text units
- **make check**: Validates and extracts errors into `1-error.xml`

### Error Recovery Workflow

When `make check` finds errors, retry them and apply fixes:

```bash
# 2. Retry errors and apply fixes
make redo MODEL=model-name     # Retries 1-error.xml → generates 1-error-ok.xml
make replace                   # Writes 1-error-ok.xml back to source files
make check                     # Verify no errors remain
```

Repeat this cycle until errors are minimized.

### Workflow Summary

| Command | Action | Notes |
|---------|--------|-------|
| `make init` | Create init.xml | Sets up training examples |
| `make test` | Test init.xml | Validates initialization |
| `make` | Generate word tables + check errors | Same as `make run check` |
| `make run` | Generate word tables | Initial generation |
| `make check` | Strip tables and extract errors | Cleans up tables, creates `1-error.xml` |
| `make redo` | Retry errors | Regenerates failed queries |
| `make replace` | Apply fixes to source files | Writes back `1-error-ok.xml` |

### Best Practices

1. Start with `make init` to create training examples
2. Use `make` for initial word table generation
3. Use `make redo` → `make replace` cycles for error recovery
4. Monitor the quality of word tables, especially lemma decomposition

### Advanced Tips

#### Manual Editing

`1-error-ok.xml` is designed to support manual editing when automated retries fail. You can directly edit the XML file to correct word tables before running `make replace`.

#### Adjusting Temperature

If repeated retries produce identical errors, increase the temperature to introduce more variation:

```bash
# Increase temperature to 0.5 for more creative analysis
make redo OPTIONS="-t 0.5" MODEL=model-name

# Higher temperature for very stubborn errors
make redo OPTIONS="-t 1.0" MODEL=model-name
```

Higher temperature values make the LLM output more varied but potentially less consistent.

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

This command automatically runs the `redo → replace → check` cycle and stops as soon as errors are cleared.

## Differences from Translation Workflow

The word table generation workflow differs from translation in several ways:

1. **Purpose**: Creates linguistic analysis tables instead of translations
2. **Output Format**: Structured tables with grammatical information
3. **Processing Units**: Uses pre-segmented text units from source files
4. **Training Data**: Requires language-specific examples for lemma and grammar rules
