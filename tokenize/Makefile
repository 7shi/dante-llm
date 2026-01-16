.PHONY: all test chars

all:
	@echo "Default target (does nothing)"

test:
	uv run pytest test.py -v

chars:
	uv run chars.py

## Manually edited, so commented out
# quote_cases.txt: ../it/*/*.txt
# 	grep -h $$'[\u2018]' $^ | grep $$'[\u2019]' > $@
# check_quotes: quote_cases.txt
# 	uv run python check_quotes.py -m groq:openai/gpt-oss-120b $<

tokenize:
	uv run tokenizer.py
