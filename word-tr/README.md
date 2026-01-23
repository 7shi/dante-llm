# Word Table Translation Workflow

This directory contains the word table translation workflow for Dante's Divine Comedy. It takes existing word tables (with grammatical analysis) and adds multi-language translation columns.

## word-tr.py

The main script that translates word tables into multiple languages using the Gemini API.

### Initial Setup

Before translating word tables, create an `init.xml` file with example translations:

```bash
uv run word-tr.py --init -m <model> "<language>" <srcdir> .
```

Example:
```bash
uv run word-tr.py --init -m gemini-2.0-flash-exp "Italian" ../../word/gemini1-it .
```

### Running Word Table Translation

Once `init.xml` exists:

```bash
uv run word-tr.py -m <model> "<language>" <srcdir> .
```

Example:
```bash
uv run word-tr.py -m gemini-2.0-flash-exp "Italian" ../../word/gemini1-it .
```

### Options

- `-m MODEL` - Specify the Gemini model (required)
- `-t, --translate LANGS` - Languages to translate (comma separated, default: "English,Italian")
- `-f, --fields FIELDS` - Fields for columns (0-based, comma separated, use + for multiple, default: "0,1")
- `--init` - Create init.xml and exit
- `--fix FILES` - Fix file (can be specified multiple times)
- `-n INTERVAL` - Chat session reset interval (default: 3)
- `-1` - Process only one canto
- `--no-retry` - Don't retry failed queries
- `--no-show` - Don't show queries and responses
- `--no-think` - Don't include AI thoughts

### Translation Table Format

The generated translation tables include the following columns:
- **Italian**: The word as it appears in the text
- **Lemma**: The dictionary form
- **English**: English translation
- **Latin**: Latin translation
- **Interlingua**: Interlingua translation
- **French**: French translation
- **Spanish**: Spanish translation
- **Portuguese**: Portuguese translation
- **Romanian**: Romanian translation
- **Esperanto**: Esperanto translation

## Processing Flow

### 1. Initialization (init)

`make init` creates training examples for the LLM by generating example translations.

- Reads the first query from the source word table
- Creates example translation for the first line
- Saves training examples to `init.xml`

### 2. Initial Translation (run)

`make run` processes the source word tables and generates translations for each text unit.

- Reads word tables from the source files
- For each unit, adds translation columns
- Saves results to XML files in the output directory

### 3. Error Checking (check)

After generation, check for errors and collect failed queries:

```bash
make check
```

This extracts all failed queries into `1-error.xml`.

### 4. Retry Errors (redo)

Retry the failed queries:

```bash
make redo MODEL=model-name
```

Results are saved to `1-error-ok.xml` (successful) and `1-error-ng.xml` (still failed).

### 5. Replace Fixed Queries (replace)

Apply the successfully retried queries back to the original files:

```bash
make replace
```

## Complete Workflow (common.mk)

### Basic Workflow

The typical workflow follows this pattern:

```bash
# 1. Initial setup and translation
make init MODEL=model-name LANG="Language"
make                           # Equivalent to: make run check
```

`make` (without arguments) executes `make run check`:
- **make run**: Translates word tables for all text units
- **make check**: Extracts errors into `1-error.xml`

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
| `make` | Translate word tables + check errors | Same as `make run check` |
| `make run` | Translate word tables | Initial translation |
| `make check` | Extract errors | Creates `1-error.xml` |
| `make redo` | Retry errors | Regenerates failed queries |
| `make replace` | Apply fixes to source files | Writes back `1-error-ok.xml` |

### Automated Temperature Sweeping

For stubborn errors that persist across multiple manual retries:

```bash
make redo-sweep MODEL=model-name
```

Automatically retries with gradually increasing temperature from 0.1 to 1.0.

## fix.py

A utility script to update prompts in `1-error.xml` by replacing table columns with current source data.

### Purpose

When source word tables are updated after error collection, the prompts in `1-error.xml` may contain outdated table data. This script synchronizes those columns with the current source files.

### Usage

```bash
uv run fix.py -c <columns> <error-file> <source-dir>
```

Options:
- `-c, --columns` (required): Source columns to copy (comma-separated). These fill destination columns starting from 0.

Examples:
```bash
# For word-tr: copy source columns 0,1 to destination columns 0,1
uv run ../fix.py -c 0,1 1-error.xml ../../word/gemma3-it

# For etymology: copy source column 1 to destination column 0
uv run ../fix.py -c 1 1-error.xml ../../word/gemma3-it
```

### How It Works

1. Reads error queries from the specified error file (e.g., `1-error.xml`)
2. Loads source word tables from the source directory
3. For each error query:
   - Matches it to the corresponding source query by `info` field
   - Extracts the table from the source query
   - Copies specified source columns to destination columns (starting from 0)
4. Writes back the updated error file

### When to Use

Use this script when:
- Source word tables have been updated after error collection
- You want to retry errors with the latest source data
- Columns in error prompts are out of sync with source files

### Integration with Workflow

This script is typically used between error collection and retry:

```bash
make check                                              # Extract errors to 1-error.xml
uv run ../fix.py -c 0,1 1-error.xml ../../word/gemma3-it  # Sync with source
make redo MODEL=model-name                              # Retry with updated prompts
```

## Compare Word Tables

Compare translation tables from different models (gemini1-it, gemma3-it, gptoss-it) line by line:

```bash
make compare
```

This command:
- Runs `dantetool compare` for all cantos
- Generates comparison files in `comparison/{cantica}/{canto}.md`
- Each line is followed by translation table rows from all models

The comparison helps identify:
- Translation differences between models
- Consistency in lemmatization across languages
- Common patterns in translation choices

## Differences from Word Table Generation

The word table translation workflow differs from word table generation in several ways:

1. **Input**: Uses existing word tables (with grammatical analysis) as input
2. **Purpose**: Adds multi-language translation columns instead of grammatical analysis
3. **Output Format**: Extended tables with translation columns (English, Latin, Interlingua, French, Spanish, Portuguese, Romanian, Esperanto)
4. **Processing**: Translates the "Word" and "Lemma" columns into multiple languages
