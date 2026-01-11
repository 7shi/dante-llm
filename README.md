# dante-llm

Dante's Divine Comedy translation project using Large Language Models (LLMs)

This project uses the following Italian text source:

- [La Divina Commedia di Dante: Complete by Dante Alighieri | Project Gutenberg](https://www.gutenberg.org/ebooks/1000)

## Overview

This project provides tools for translating Dante's Divine Comedy using various Large Language Models. Specifically, this project uses:

- **Gemini 1.0 Pro** (copied from previous project; model now discontinued)

This project is a rewrite of code from the Gemini 1.0 Pro era. The generated outputs labeled as "gemini1" are sourced from the following project:

- [dante-gemini](https://github.com/7shi/dante-gemini) - A multilingual exploration of Dante's Divine Comedy using Gemini 1.0 Pro, featuring detailed linguistic analysis of the opening lines in Italian, English, Hindi, Chinese, Ancient Greek, Arabic, Bengali and other languages with word-by-word breakdowns, grammatical details, and etymologies.

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

## License

Script files are released under CC0 (public domain). However, Gemini's outputs are subject to [Gemini API Additional Terms of Service](https://ai.google.dev/gemini-api/terms), which prohibit use for machine learning training purposes. No LICENSE file is intentionally provided to avoid potential misunderstanding about the restrictions on AI-generated content.

## Related Previous Projects

- [dante-gemini-25](https://github.com/7shi/dante-gemini-25) - A complete translation of Dante's Divine Comedy using Gemini 2.5 Pro, focusing specifically on English and Japanese translations across the three canticles. This project also includes illustrations generated using Nano Banana (Gemini 2.5 Flash Image Preview) in a classical Renaissance art style inspired by Gustave Doré.
- [dante-la-el](https://github.com/7shi/dante-la-el) - Originally started as a project to transcribe historical Latin and Ancient Greek translations of Dante's Divine Comedy, but evolved into an early LLM experimentation project when AI became the primary focus, exploring computational linguistic analysis methods.
