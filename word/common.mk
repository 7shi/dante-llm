TOPDIR  ?= ../..
SUBDIR  ?= ..
SRCDIR  ?= $(TOPDIR)/translate/$(LCODE)
DIRSM   ?= {inferno,purgatorio,paradiso}
INITOPT ?=
OPTIONS ?=


# Basic workflow

## Run word table generation + check (default)
all: run check

## Create init.xml
init: init.xml

init.xml:
	uv run $(SUBDIR)/init.py $(INITOPT) -m $(MODEL) "$(LANG)" $(SRCDIR)

## Test init.xml
test: init.xml
	uv run $(SUBDIR)/init.py -t -m $(MODEL) "$(LANG)" $(SRCDIR)

## Run word table generation
run: init.xml
	uv run $(SUBDIR)/word.py $(OPTIONS) -m $(MODEL) "$(LANG)" $(SRCDIR) .

## Validate and extract errors
check:
	rm -f 1-error-{ok,ng}.xml
	uv run $(SUBDIR)/check.py $(DIRSM)/*.xml
	uv run dantetool pickup 1-error.xml $(DIRSM)/*.xml


# Error recovery

## Retry errors (1-error.xml)
redo:
	uv run $(SUBDIR)/fix.py $(OPTIONS) -m $(MODEL) 1-error.xml

## Apply fixes (1-error-ok.xml) to source
replace:
	uv run dantetool replace 1-error-ok.xml $(DIRSM)/*.xml

## Automatically retry with increasing temperature (0.1 to 1.0)
redo-sweep:
	@for t in 0.{1..9} 1.0; do \
		echo "Retrying with temperature $$t..."; \
		$(MAKE) redo OPTIONS="-t $$t" || exit 1; \
		$(MAKE) replace check; \
		if grep -q 'count="0"' 1-error.xml; then \
			echo "No errors remaining at temperature $$t"; \
			break; \
		fi; \
	done
