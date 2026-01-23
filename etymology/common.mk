TOPDIR  ?= ../..
SUBDIR  ?= ..
SRCDIR  ?= $(TOPDIR)/word-tr/$(LCODE)
DIRSM   ?= {inferno,purgatorio,paradiso}
OPTIONS ?=
FIXES   ?=


# Basic workflow

## Run etymology lookup + check (default)
all: run check

## Create init.xml
init: init.xml

init.xml:
	uv run $(SUBDIR)/etymology.py --init $(OPTIONS) -m $(MODEL) "$(LANG)" $(SRCDIR) . $(FIXES)

## Run etymology lookup
run: init.xml
	uv run $(SUBDIR)/etymology.py $(OPTIONS) -m $(MODEL) "$(LANG)" $(SRCDIR) . $(FIXES)

## Validate and extract errors
check:
	rm -f 1-error-{ok,ng}.xml
	uv run dantetool strip --strict --validate-source $(SRCDIR) --validate-column 1 $(DIRSM)/*.xml
	uv run dantetool pickup 1-error.xml $(DIRSM)/*.xml


# Error recovery

## Retry errors (1-error.xml)
redo:
	uv run dantetool redo $(OPTIONS) -n 1 -m $(MODEL) 1-error.xml

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
