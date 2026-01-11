TOPDIR  ?= ../..
SCRIPTS  = $(TOPDIR)/scripts
SRCDIR  ?= $(TOPDIR)/translate/$(LCODE)
INITOPT ?=
OPTIONS ?=

all: run check

init: init.xml

init.xml:
	python $(SCRIPTS)/init.py $(INITOPT) "$(LANG)" $(SRCDIR)

test: init.xml
	python $(SCRIPTS)/init.py -t "$(LANG)" $(SRCDIR)

run: init.xml
	python $(SCRIPTS)/word.py $(OPTIONS) "$(LANG)" $(SRCDIR) .

check:
	python $(SCRIPTS)/pickup.py 1-error.xml */*.xml

fix:
	python $(SCRIPTS)/word-fix.py

redo:
	python $(SCRIPTS)/redo.py 1-error.xml

replace:
	python $(SCRIPTS)/replace.py 1-error-ok.xml */*.xml
