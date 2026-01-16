# dante-llm

Dante's Divine Comedy translation project using Large Language Models (LLMs)

This project uses the following Italian text source:

- [La Divina Commedia di Dante: Complete by Dante Alighieri | Project Gutenberg](https://www.gutenberg.org/ebooks/1000)

## Overview

This project provides tools for translating Dante's Divine Comedy using various Large Language Models. Specifically, this project uses:

- **Gemini 1.0 Pro** (copied from previous project; model now discontinued)
- **Gemma 3 27B** (via Gemini API)
- **GPT-OSS 120B** (via Ollama API)

This project aims to verify that locally-runnable models like Gemma 3 27B and GPT-OSS 120B can match the quality of Gemini 1.0 Pro, which was SOTA (state-of-the-art) at the time.

Side-by-side comparison documents showing the original Italian text alongside translations from all models are available:

- [translate/comparison](translate/comparison) - All 100 cantos (Inferno 34 + Purgatorio 33 + Paradiso 33)

This project is a rewrite of code from the Gemini 1.0 Pro era. The generated outputs labeled as "gemini1" are sourced from the following project:

- [dante-gemini](https://github.com/7shi/dante-gemini) - A multilingual exploration of Dante's Divine Comedy using Gemini 1.0 Pro, featuring detailed linguistic analysis of the opening lines in Italian, English, Hindi, Chinese, Ancient Greek, Arabic, Bengali and other languages with word-by-word breakdowns, grammatical details, and etymologies.

The Gemini API and Ollama API are abstracted through the following library, making model switching straightforward.

- [llm7shi](https://github.com/7shi/llm7shi) - A simplified Python library for interacting with large language models (Gemini, OpenAI, Ollama)

## XML Format

The tools work with a custom XML format (handled by `common.py`) that stores translation queries and results. This format is designed with three key considerations:

1. **Human-readable as logs**: Easy to review translation progress and errors
2. **Hand-editable**: Can be manually corrected when automated retries fail
3. **Machine-readable**: Standard XML format ensures reliable parsing

Example structure:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<queries count="44">
<query>
<info>[Inferno Canto 4] 51/151</info>
<prompt>
Please translate each line literally into English.

51 E quei che 'ntese il mio parlar coverto,
</prompt>
<result>
51 And he who heard my hidden speech,
</result>
</query>
</queries>
```

Files like `1-error.xml`, `1-error-ok.xml`, and `1-error-ng.xml` follow this format, making the workflow transparent and maintainable.

This project uses the following library for XML parsing:

- [xml7shi](https://github.com/7shi/xml7shi) - A pull-based simple and permissive XML parser for Python

## dantetool

`dantetool` is a Python package that provides command-line tools for managing translation queries and handling errors.

### Installation

```bash
# Install in development mode
uv sync
```

### Commands

#### concat - Concatenate XML Files

Concatenate multiple XML query files into a single output file:

```bash
uv run dantetool concat -o <output.xml> <input-files...>
```

Example:
```bash
uv run dantetool concat -o combined.xml file1.xml file2.xml file3.xml
```

#### pickup - Extract Error Queries

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

#### redo - Retry Failed Queries

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

#### replace - Apply Fixes

Replace queries in target files with fixed versions:

```bash
uv run dantetool replace <fix.xml> <target-files...>
```

Example:
```bash
uv run dantetool replace 1-error-ok.xml inferno/*.xml purgatorio/*.xml paradiso/*.xml
```

#### strip - Clean Up and Validate Word Tables

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

## Workflows

- [translate/](translate/): Translation workflow. Provides `translate.py` for translating Italian text into various target languages with automated error recovery and retry mechanisms.
- [tokenize/](tokenize/): Italian tokenizer and pre-tokenized corpus. Provides apostrophe-aware tokenization with U+2019 normalization for accurate word table validation.
- [word/](word/): Word table generation workflow. Provides `init.py` and `word.py` for creating linguistic analysis tables with lemmas, parts of speech, and grammatical information for Italian text.

## License

Script files are released under CC0 (public domain). However, Gemini's outputs are subject to [Gemini API Additional Terms of Service](https://ai.google.dev/gemini-api/terms), which prohibit use for machine learning training purposes. No LICENSE file is intentionally provided to avoid potential misunderstanding about the restrictions on AI-generated content.

## Related Previous Projects

- [dante-gemini-25](https://github.com/7shi/dante-gemini-25) - A complete translation of Dante's Divine Comedy using Gemini 2.5 Pro, focusing specifically on English and Japanese translations across the three canticles. This project also includes illustrations generated using Nano Banana (Gemini 2.5 Flash Image Preview) in a classical Renaissance art style inspired by Gustave Doré.
- [dante-la-el](https://github.com/7shi/dante-la-el) - Originally started as a project to transcribe historical Latin and Ancient Greek translations of Dante's Divine Comedy, but evolved into an early LLM experimentation project when AI became the primary focus, exploring computational linguistic analysis methods.
