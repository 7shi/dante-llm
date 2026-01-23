# Etymology Lookup Workflow

This directory contains the etymology lookup workflow for Dante's Divine Comedy. It takes word translation tables and adds etymology information columns.

## etymology.py

The main script that looks up word etymologies using the Gemini API.

### Initial Setup

Before looking up etymologies, create an `init.xml` file with example lookups:

```bash
uv run etymology.py --init -m <model> "<language>" <srcdir> .
```

Example:
```bash
uv run etymology.py --init -m gemini-2.0-flash-exp "Italian" ../../word-tr/gemini1-it .
```

### Running Etymology Lookup

Once `init.xml` exists:

```bash
uv run etymology.py -m <model> "<language>" <srcdir> .
```

Example:
```bash
uv run etymology.py -m gemini-2.0-flash-exp "Italian" ../../word-tr/gemini1-it .
```

### Options

- `-m MODEL` - Specify the Gemini model (required)
- `-e, --derived LANGS` - Etymology language(s) to look for (default: "Latin, Greek, Germanic")
- `-f, --fields FIELDS` - Fields for columns (0-based, comma separated, default: "1")
- `--init` - Create init.xml and exit
- `--fix FILES` - Fix file (can be specified multiple times)
- `-n INTERVAL` - Chat session reset interval (default: 1)
- `-1` - Process only one canto
- `--no-retry` - Don't retry failed queries
- `--no-show` - Don't show queries and responses
- `--no-think` - Don't include AI thoughts

### Etymology Table Format

The generated etymology tables include the following columns:
- **Italian**: The lemma form of the word
- **Derived**: The origin language (Latin, Greek, Germanic, etc.)
- **Etymology**: The original word in the source language

## Processing Flow

### 1. Initialization (init)

`make init` creates training examples for the LLM by generating example etymology lookups.

- Reads the first query from the source word translation table
- Creates example etymology lookup for the first line
- Saves training examples to `init.xml`

### 2. Initial Lookup (run)

`make run` processes the source word translation tables and generates etymology information for each text unit.

- Reads word tables from the source files
- For each unit, adds etymology columns (Derived, Etymology)
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
# 1. Initial setup and etymology lookup
make init MODEL=model-name LANG="Language"
make                           # Equivalent to: make run check
```

`make` (without arguments) executes `make run check`:
- **make run**: Looks up etymologies for all text units
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
| `make` | Look up etymologies + check errors | Same as `make run check` |
| `make run` | Look up etymologies | Initial lookup |
| `make check` | Extract errors | Creates `1-error.xml` |
| `make redo` | Retry errors | Regenerates failed queries |
| `make replace` | Apply fixes to source files | Writes back `1-error-ok.xml` |

### Automated Temperature Sweeping

For stubborn errors that persist across multiple manual retries:

```bash
make redo-sweep MODEL=model-name
```

Automatically retries with gradually increasing temperature from 0.1 to 1.0.

## Fixing Error Prompts

When source word translation tables are updated after error collection, use `make fix` to sync prompts with current source data:

```bash
make check               # Extract errors to 1-error.xml
make fix                 # Sync column 1 (Lemma) with source
make redo MODEL=model-name  # Retry with updated prompts
```

See `dantetool/README.md` for full documentation of the `fix` command.

## Compare Etymology Tables

Compare etymology tables from different models (gemini1-it, gemma3-it, gptoss-it) line by line:

```bash
make compare
```

This command:
- Runs `dantetool compare --use-tokens` for all cantos
- Generates comparison files in `comparison/{cantica}/{canto}.md`
- Each line is followed by etymology table rows from all models

The comparison helps identify:
- Etymology differences between models
- Consistency in identifying word origins
- Variations in etymological derivations

## Differences from Word Table Translation

The etymology lookup workflow differs from word table translation in several ways:

1. **Input**: Uses word translation tables (with lemmas) as input
2. **Purpose**: Adds etymology information instead of translations
3. **Output Format**: Extended tables with etymology columns (Derived, Etymology)
4. **Processing**: Looks up the etymology of words from the "Lemma" column
