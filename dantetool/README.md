# dantetool

`dantetool` is a Python package that provides command-line tools for managing translation queries and handling errors.

## Installation

```bash
# Install in development mode
uv sync
```

## Commands

### concat - Concatenate XML Files

Concatenate multiple XML query files into a single output file:

```bash
uv run dantetool concat -o <output.xml> <input-files...>
```

Example:
```bash
uv run dantetool concat -o combined.xml file1.xml file2.xml file3.xml
```

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
