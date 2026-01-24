# dantetool

`dantetool` is a Python package that provides command-line tools for managing translation queries and handling errors.

## Installation

```bash
# Install in development mode
uv sync
```

## Commands

### compare - Compare Word Tables

Compare word tables from different models and generate a markdown comparison file:

```bash
uv run dantetool compare <rel-paths...>
```

Options:
- `-t, --use-tokens` - Use tokenized words as first column for matching

Example:
```bash
uv run dantetool compare inferno/01 inferno/02
```

Output:
- `comparison/inferno/01.md` - Markdown file with side-by-side comparison of word tables from all models

### concat - Concatenate XML Files

Concatenate multiple XML query files into a single output file:

```bash
uv run dantetool concat -o <output.xml> <input-files...>
```

Example:
```bash
uv run dantetool concat -o combined.xml file1.xml file2.xml file3.xml
```

### fix - Fix Error Prompts with Source Data

Update prompts in error files by replacing table columns with current source data:

```bash
uv run dantetool fix -c <columns> <error-file> <source-dir>
```

Options:
- `-c, --columns` (required): Source columns to copy (comma-separated). These fill destination columns starting from 0.

Examples:
```bash
# Copy source columns 0,1 to destination columns 0,1
uv run dantetool fix -c 0,1 1-error.xml ../word/gemma3-it

# Copy source column 1 to destination column 0
uv run dantetool fix -c 1 1-error.xml ../word/gemma3-it
```

How it works:
1. Reads error queries from the specified error file
2. Loads source word tables from the source directory
3. For each error query, matches by `info` field and copies specified source columns to destination columns (starting from 0)
4. Writes back the updated error file

### pickup - Extract Error Queries

Extract failed or incomplete queries from translation XML files:

```bash
uv run dantetool pickup <output.xml> <input-files...>
```

Options:
- `-t` - Check table format

Example:
```bash
uv run dantetool pickup 1-error.xml inferno/*.xml purgatorio/*.xml paradiso/*.xml
```

### redo - Retry Failed Queries

Retry error queries with the LLM:

```bash
uv run dantetool redo -m <model> [-s <system-prompt-file>] <input.xml>
```

Options:
- `-i INIT_XML` - Specify init.xml file (default: init.xml)
- `-m MODEL` - Specify model name (required)
- `-s SYSTEM_PROMPT` - Specify system prompt file
- `-1` - Split 3-line queries into separate 1-line queries
- `--no-think` - Don't include thoughts in response

Example:
```bash
uv run dantetool redo -s translate/system.txt -m gemini-2.0-flash-exp 1-error.xml
```

Output:
- `1-error-ok.xml` - Successfully retried queries
- `1-error-ng.xml` - Queries that still failed

### replace - Apply Fixes

Replace queries in target files with fixed versions:

```bash
uv run dantetool replace <fix.xml> <target-files...>
```

Example:
```bash
uv run dantetool replace 1-error-ok.xml inferno/*.xml purgatorio/*.xml paradiso/*.xml
```

### show - Show Translation

Display translation lines from XML files:

```bash
uv run dantetool show <file.xml>
```

Example:
```bash
uv run dantetool show translate/gemini1-en/inferno/01.xml
```

Output: Lines starting with line numbers from the `<result>` tags are printed to stdout.

### strip - Clean Up and Validate Word Tables

Strip and validate table content from XML files. This command parses table results, validates their format, and cleans up any malformed entries:

```bash
uv run dantetool strip <target-files...>
```

Example:
```bash
uv run dantetool strip word/gemma3-it/*.xml
```

The command processes each file in-place:
- Valid tables are preserved in the `result` field
- Invalid tables are moved to the `error` field with an error message
