# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = source
BUILDDIR      = build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

VENV = .venv
export VIRTUAL_ENV := $(abspath ${VENV})
export PATH := ${VIRTUAL_ENV}/bin:${PATH}
export GIT_COMMIT := $(shell git rev-parse --short HEAD)
export GITURL := $(shell git config remote.origin.url)
export BRANCH_NAME := $(shell git rev-parse --abbrev-ref HEAD)
# TODO: update the proper git URL here:
ifneq "$(GITURL)" "git@github.com:jantman/machine-access-control.git"
	export GIT_COMMIT := ${GIT_COMMIT} (branch '${BRANCH_NAME}' from $(GITURL))
endif

${VENV}:
	python3 -mvenv $@;

setup: ${VENV}
    # pin docutils due to bug: https://stackoverflow.com/questions/67542699/readthedocs-sphinx-not-rendering-bullet-list-from-rst-file
	. .venv/bin/activate; python3 -m pip install -r requirements.txt

ghp: setup
	# WARNING - there aren't any checks to prevent someone with appropriate permissions
	# from pushing their local build directly to the live docs. Don't copy this pattern!
	@echo giturl is $(GITURL)
	cd build/dirhtml && \
		git init && \
		git remote add origin $(GITURL) && \
		git checkout -b gh-pages && \
		git add --all && \
		git commit -m "local docs build" && \
		git push -f origin HEAD:gh-pages

.PHONY: help setup all

html: setup
	. .venv/bin/activate; python3 -msphinx "$(SOURCEDIR)" "$(BUILDDIR)/html" -b html -E -W

all: clean html

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: all
