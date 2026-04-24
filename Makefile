ROLE ?= backend-dev
WINDOW ?= 90
BIN = .venv/bin

.PHONY: setup init-db ingest link score extract cluster synthesize validate all trace clean

setup:
	python -m venv .venv
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -e ".[dev]"
	$(BIN)/distill-init-db

init-db:
	$(BIN)/distill-init-db

ingest:
	$(BIN)/distill-ingest-gitlab --window $(WINDOW)
	$(BIN)/distill-ingest-jira --window $(WINDOW)
	$(BIN)/distill-ingest-confluence --window $(WINDOW)

link:
	$(BIN)/distill-link

score:
	$(BIN)/distill-score --role $(ROLE)

extract:
	$(BIN)/distill-extract --role $(ROLE)

cluster:
	$(BIN)/distill-cluster --role $(ROLE)

synthesize:
	$(BIN)/distill-synthesize --role $(ROLE)

validate:
	$(BIN)/distill-validate --role $(ROLE)

all: ingest link score extract cluster synthesize validate
	@echo "Pack ready: packs/$(ROLE)/v0.1/"

trace:
	$(BIN)/distill-trace --module $(MODULE)

clean:
	rm -f data/distill.db
	rm -rf data/blobs/gitlab data/blobs/jira data/blobs/confluence
