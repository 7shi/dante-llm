TOPDIR  ?= ../..
SUBDIR  ?= ..
SRCDIR  ?= $(TOPDIR)/translate/$(LCODE)
DIRSM   ?= {inferno,purgatorio,paradiso}
OPTIONS ?=


# Basic workflow

## Run translation + check (default)
all: run check

## Create init.xml
init:
	uv run $(SUBDIR)/translate.py $(OPTIONS) -m $(MODEL) --init "$(LANG)" $(SRCDIR) .

## Run translation only
run:
	uv run $(SUBDIR)/translate.py $(OPTIONS) -m $(MODEL) "$(LANG)" $(SRCDIR) .

## Validate and extract errors
check:
	rm -f 1-error-{ok,ng}.xml
	uv run $(SUBDIR)/split.py -c 2 $(DIRSM)/*.xml
	uv run dantetool pickup 1-error.xml $(DIRSM)/*.xml


# Error recovery

## Retry errors (1-error.xml)
redo:
	uv run dantetool redo $(OPTIONS) -s $(SUBDIR)/system.txt -m $(MODEL) 1-error.xml

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


# Advanced (for persistent errors)

## Restructure source into 3-line units
split:
	uv run $(SUBDIR)/split.py $(DIRSM)/*.xml

## Force 1-line-at-a-time retry
redo1:
	uv run dantetool redo $(OPTIONS) -s $(SUBDIR)/system.txt -m $(MODEL) -1 1-error.xml

## Check fixes without applying
redo-fix:
	uv run $(SUBDIR)/split.py -c 2 1-error-ok.xml
