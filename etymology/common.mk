TOPDIR  ?= ../..
SCRIPTS  = $(TOPDIR)/scripts
SRCDIR   = $(TOPDIR)/word-tr/$(LCODE)
OPTIONS ?=
FIXES   ?=

all: run check

run:
	python $(SCRIPTS)/etymology.py $(OPTIONS) $(LANG) $(SRCDIR) . $(FIXES)

check:
	python $(SCRIPTS)/pickup.py 1-error.xml */*.xml
