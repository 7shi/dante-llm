TOPDIR  ?= ../..
SCRIPTS  = $(TOPDIR)/scripts
SRCDIR   = $(TOPDIR)/word/$(LCODE)
OPTIONS ?=
FIXES   ?=

all: run check

run:
	python $(SCRIPTS)/word-tr.py $(OPTIONS) "$(LANG)" $(SRCDIR) . $(FIXES)

check:
	python $(SCRIPTS)/pickup.py 1-error.xml */*.xml
