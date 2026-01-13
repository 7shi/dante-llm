SCRIPT = make -C
MODELS = gemma3 gptoss
LANGUAGES = it

all:
	@for m in $(MODELS); do for l in $(LANGUAGES); do $(SCRIPT) $$m-$$l; done; done

check:
	grep count */1-error.xml | grep -v '"0"'
