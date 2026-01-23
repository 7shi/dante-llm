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

Side-by-side comparison documents showing outputs from all models are available:

- [translate/comparison](translate/comparison) - Italian original with English translations from all models
- [word/comparison](word/comparison) - Word tables with lemmas, parts of speech, and grammatical analysis from all models
- [word-tr/comparison](word-tr/comparison) - Word tables with multi-language translations from all models
- [etymology/comparison](etymology/comparison) - Etymology tables with word origins and etymological roots from all models
- [gallery](gallery) - Combined view with translations, word tables, and etymology from all models

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

`dantetool` is a Python package that provides command-line tools for managing translation queries and handling errors. See [dantetool/README.md](dantetool/README.md) for details.

## Workflows

- [translate/](translate/): Translation workflow. Provides `translate.py` for translating Italian text into various target languages with automated error recovery and retry mechanisms.
- [tokenize/](tokenize/): Italian tokenizer and pre-tokenized corpus. Provides apostrophe-aware tokenization with U+2019 normalization for accurate word table validation.
- [word/](word/): Word table generation workflow. Provides `init.py` and `word.py` for creating linguistic analysis tables with lemmas, parts of speech, and grammatical information for Italian text.
- [word-tr/](word-tr/): Word table translation workflow. Provides `word-tr.py` for translating word tables into multiple languages (English, Latin, Interlingua, French, Spanish, Portuguese, Romanian, Esperanto).
- [etymology/](etymology/): Etymology lookup workflow. Provides `etymology.py` for looking up word origins (Latin, Greek, Germanic) and their etymological roots from word translation tables.
- [gallery/](gallery/): Model comparison gallery. Provides `gallery.py` for generating combined comparison files with word tables, etymology, and translations from all models side by side.

## License

Script files are released under CC0 (public domain). However, Gemini's outputs are subject to [Gemini API Additional Terms of Service](https://ai.google.dev/gemini-api/terms), which prohibit use for machine learning training purposes. No LICENSE file is intentionally provided to avoid potential misunderstanding about the restrictions on AI-generated content.

## Related Previous Projects

- [dante-gemini-25](https://github.com/7shi/dante-gemini-25) - A complete translation of Dante's Divine Comedy using Gemini 2.5 Pro, focusing specifically on English and Japanese translations across the three canticles. This project also includes illustrations generated using Nano Banana (Gemini 2.5 Flash Image Preview) in a classical Renaissance art style inspired by Gustave Doré.
- [dante-la-el](https://github.com/7shi/dante-la-el) - Originally started as a project to transcribe historical Latin and Ancient Greek translations of Dante's Divine Comedy, but evolved into an early LLM experimentation project when AI became the primary focus, exploring computational linguistic analysis methods.
