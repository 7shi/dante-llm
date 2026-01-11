SCRIPT = make -C
MODELS = gemma3 gptoss
LANGUAGES = en ja

all:
	@for m in $(MODELS); do for l in $(LANGUAGES); do $(SCRIPT) $$m-$$l; done; done

check:
	grep count */1-error.xml | grep -v '"0"'

compare:
	uv run compare.py inferno/{01..34} purgatorio/{01..33} paradiso/{01..33}
