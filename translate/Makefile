SCRIPT = echo

all:

check:
	grep count */1-error.xml | grep -v '"0"'

_done:
	$(SCRIPT) gemini1-en English
	$(SCRIPT) gemini1-ja Japanese
