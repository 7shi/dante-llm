TOPDIR  ?= ../..
SUBDIR   = ..
SRCDIR  ?= $(TOPDIR)/translate/$(LCODE)
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
	uv run dantetool pickup 1-error.xml */*.xml


# Error recovery

## Retry errors (1-error.xml)
redo:
	uv run dantetool redo $(OPTIONS) -m $(MODEL) 1-error.xml

## Apply fixes (1-error-ok.xml) to source
replace:
	uv run dantetool replace 1-error-ok.xml */*.xml
