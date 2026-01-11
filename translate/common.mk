TOPDIR    ?= ../..
TRANSLATE  = ..
SCRIPTS    = $(TOPDIR)/dantetool
SRCDIR     = $(TOPDIR)/it
DIRSM      = {inferno,purgatorio,paradiso}
OPTIONS   ?=

all: run check

run:
	uv run $(TRANSLATE)/translate.py $(OPTIONS) "$(LANG)" $(SRCDIR) .

check:
	uv run $(SCRIPTS)/pickup.py 1-error.xml $(DIRSM)/*.xml

split:
	uv run $(TRANSLATE)/split.py $(DIRSM)/*.xml

redo:
	uv run $(SCRIPTS)/redo.py 1-error.xml

redo1:
	uv run $(SCRIPTS)/redo.py -1 1-error.xml

redo-fix:
	uv run $(TRANSLATE)/split.py -c 2 1-error-ok.xml

replace:
	uv run $(SCRIPTS)/replace.py 1-error-ok.xml $(DIRSM)/*.xml

split3:
	uv run $(TRANSLATE)/split.py -c 2 $(DIRSM)/*.xml
	uv run $(TRANSLATE)/split.py $(DIRSM)/*.xml
