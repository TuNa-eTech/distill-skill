ROLE ?= backend-dev
WINDOW ?= 90
PY = .venv/bin/python

.PHONY: setup init-db ingest link score extract cluster synthesize validate all trace clean

setup:
	python -m venv .venv
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e .
	$(PY) scripts/init_db.py

init-db:
	$(PY) scripts/init_db.py

ingest:
	$(PY) scripts/ingest_gitlab.py --window $(WINDOW)
	$(PY) scripts/ingest_jira.py --window $(WINDOW)
	$(PY) scripts/ingest_confluence.py --window $(WINDOW)

link:
	$(PY) scripts/link.py

score:
	$(PY) scripts/score.py --role $(ROLE)

extract:
	$(PY) scripts/extract.py --role $(ROLE)

cluster:
	$(PY) scripts/cluster.py --role $(ROLE)

synthesize:
	$(PY) scripts/synthesize.py --role $(ROLE)

validate:
	$(PY) scripts/validate.py --role $(ROLE)

all: ingest link score extract cluster synthesize validate
	@echo "Pack ready: packs/$(ROLE)/v0.1/"

trace:
	$(PY) scripts/trace.py --module $(MODULE)

clean:
	rm -f data/distill.db
	rm -rf data/blobs/gitlab data/blobs/jira data/blobs/confluence
