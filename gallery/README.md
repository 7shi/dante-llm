# Gallery - Model Comparison

Side-by-side comparison of word tables, etymology, and translations for Dante's Divine Comedy from multiple models:

- **gemini1-it**: Gemini 1.0 Pro
- **gemma3-it**: Gemma 3 27B
- **gptoss-it**: GPT-OSS 120B

Each comparison shows the original Italian line followed by translations and word tables from all models.

## 1. Inferno

[Canto 1](inferno/01.md) | [Canto 2](inferno/02.md) | [Canto 3](inferno/03.md) | [Canto 4](inferno/04.md) | [Canto 5](inferno/05.md) | [Canto 6](inferno/06.md) | [Canto 7](inferno/07.md) | [Canto 8](inferno/08.md) | [Canto 9](inferno/09.md) | [Canto 10](inferno/10.md) | [Canto 11](inferno/11.md) | [Canto 12](inferno/12.md) | [Canto 13](inferno/13.md) | [Canto 14](inferno/14.md) | [Canto 15](inferno/15.md) | [Canto 16](inferno/16.md) | [Canto 17](inferno/17.md) | [Canto 18](inferno/18.md) | [Canto 19](inferno/19.md) | [Canto 20](inferno/20.md) | [Canto 21](inferno/21.md) | [Canto 22](inferno/22.md) | [Canto 23](inferno/23.md) | [Canto 24](inferno/24.md) | [Canto 25](inferno/25.md) | [Canto 26](inferno/26.md) | [Canto 27](inferno/27.md) | [Canto 28](inferno/28.md) | [Canto 29](inferno/29.md) | [Canto 30](inferno/30.md) | [Canto 31](inferno/31.md) | [Canto 32](inferno/32.md) | [Canto 33](inferno/33.md) | [Canto 34](inferno/34.md)

## 2. Purgatorio

[Canto 1](purgatorio/01.md) | [Canto 2](purgatorio/02.md) | [Canto 3](purgatorio/03.md) | [Canto 4](purgatorio/04.md) | [Canto 5](purgatorio/05.md) | [Canto 6](purgatorio/06.md) | [Canto 7](purgatorio/07.md) | [Canto 8](purgatorio/08.md) | [Canto 9](purgatorio/09.md) | [Canto 10](purgatorio/10.md) | [Canto 11](purgatorio/11.md) | [Canto 12](purgatorio/12.md) | [Canto 13](purgatorio/13.md) | [Canto 14](purgatorio/14.md) | [Canto 15](purgatorio/15.md) | [Canto 16](purgatorio/16.md) | [Canto 17](purgatorio/17.md) | [Canto 18](purgatorio/18.md) | [Canto 19](purgatorio/19.md) | [Canto 20](purgatorio/20.md) | [Canto 21](purgatorio/21.md) | [Canto 22](purgatorio/22.md) | [Canto 23](purgatorio/23.md) | [Canto 24](purgatorio/24.md) | [Canto 25](purgatorio/25.md) | [Canto 26](purgatorio/26.md) | [Canto 27](purgatorio/27.md) | [Canto 28](purgatorio/28.md) | [Canto 29](purgatorio/29.md) | [Canto 30](purgatorio/30.md) | [Canto 31](purgatorio/31.md) | [Canto 32](purgatorio/32.md) | [Canto 33](purgatorio/33.md)

## 3. Paradiso

[Canto 1](paradiso/01.md) | [Canto 2](paradiso/02.md) | [Canto 3](paradiso/03.md) | [Canto 4](paradiso/04.md) | [Canto 5](paradiso/05.md) | [Canto 6](paradiso/06.md) | [Canto 7](paradiso/07.md) | [Canto 8](paradiso/08.md) | [Canto 9](paradiso/09.md) | [Canto 10](paradiso/10.md) | [Canto 11](paradiso/11.md) | [Canto 12](paradiso/12.md) | [Canto 13](paradiso/13.md) | [Canto 14](paradiso/14.md) | [Canto 15](paradiso/15.md) | [Canto 16](paradiso/16.md) | [Canto 17](paradiso/17.md) | [Canto 18](paradiso/18.md) | [Canto 19](paradiso/19.md) | [Canto 20](paradiso/20.md) | [Canto 21](paradiso/21.md) | [Canto 22](paradiso/22.md) | [Canto 23](paradiso/23.md) | [Canto 24](paradiso/24.md) | [Canto 25](paradiso/25.md) | [Canto 26](paradiso/26.md) | [Canto 27](paradiso/27.md) | [Canto 28](paradiso/28.md) | [Canto 29](paradiso/29.md) | [Canto 30](paradiso/30.md) | [Canto 31](paradiso/31.md) | [Canto 32](paradiso/32.md) | [Canto 33](paradiso/33.md)

---

This directory contains the gallery comparison tool for Dante's Divine Comedy. It generates comparison files that display word tables and translations from multiple models side by side.

## gallery.py

The main script that generates comparison gallery files.

### Usage

```bash
uv run gallery.py <canto>...
```

Example:
```bash
uv run gallery.py inferno/01
uv run gallery.py inferno/01 inferno/02 purgatorio/01
```

### Generate All Cantos

```bash
make
```

This generates comparison files for all 100 cantos (Inferno 1-34, Purgatorio 1-33, Paradiso 1-33).

## Data Sources

The script automatically collects data from:

| Directory | Content |
|-----------|---------|
| `word/` | Word analysis tables (auto-detects model directories) |
| `word-tr/` | Word translation tables |
| `etymology/` | Etymology tables |
| `translate/` | Line translations (matched by model prefix) |
| `it/` | Original Italian text |

### Model Detection

Models are auto-detected from subdirectories in `word/` that contain the requested canto file. For example, if `word/gemini1-it/inferno/01.xml` exists, `gemini1-it` is included.

### Translation Matching

Translations are matched by model prefix:
- `gemini1-it` → `translate/gemini1-en/`, `translate/gemini1-ja/`
- `gemma3-it` → `translate/gemma3-en/`, `translate/gemma3-ja/`

## Output Format

Output files are written to `gallery/{cantica}/{canto}.md`.

Each file contains:
- Title (e.g., "Inferno - Canto 1")
- For each line:
  - Line number and original Italian text
  - For each model:
    - Model name
    - Translations (if available)
    - Word table with etymology (if available)

### Example Output

```markdown
# Inferno - Canto 1

### 1 Nel mezzo del cammin di nostra vita

**gemini1-it**
- **gemini1-en**: In the middle of the journey of our life
- **gemini1-ja**: 我々の人生の中間点で
<table>
<tr><th>Word</th><td>Nel</td><td>mezzo</td><td>del</td>...</tr>
...
</table>

**gemma3-it**
- **gemma3-en**: In the middle of the path of our life
- **gemma3-ja**: 我らの人生の道の半ばで
<table>
...
</table>
```

## Differences from Other Comparison Tools

| Tool | Purpose | Output |
|------|---------|--------|
| `dantetool compare` | Compare word tables only | `comparison/` |
| `translate/compare.py` | Compare translations only | `translate/comparison/` |
| `gallery/gallery.py` | Combined view with translations + word tables | `gallery/` |
