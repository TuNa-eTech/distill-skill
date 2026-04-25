ROLE ?= mobile-dev
SINCE ?= 2026-01-01
UNTIL ?= $(shell python -c "from datetime import date; cutoff = date(2026, 12, 31); today = date.today(); print((today if today < cutoff else cutoff).isoformat())")
WINDOW ?= $(shell python -c "from datetime import date; start = date(2026, 1, 1); cutoff = date(2026, 12, 31); end = date.today(); end = end if end < cutoff else cutoff; print(max(1, (end - start).days + 1))")
BIN = .venv/bin
WEB_DIR = apps/web

.PHONY: setup init-db ingest link score extract cluster synthesize validate all trace clean web-install web-api web-dev web-build

define RUN_INGEST
	@if $(BIN)/$(1) --help 2>&1 | grep -q -- "--since"; then \
		$(BIN)/$(1) --since $(SINCE) --until $(UNTIL); \
	else \
		echo "[ops] $(1) still uses legacy --window $(WINDOW) fallback for 2026-local ingest."; \
		$(BIN)/$(1) --window $(WINDOW); \
	fi
endef

setup:
	python -m venv .venv
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -e ".[dev]"
	$(BIN)/distill-init-db

init-db:
	$(BIN)/distill-init-db

ingest:
	$(call RUN_INGEST,distill-ingest-gitlab)
	$(call RUN_INGEST,distill-ingest-jira)
	$(call RUN_INGEST,distill-ingest-confluence)

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

web-install:
	cd $(WEB_DIR) && yarn install

web-api:
	$(BIN)/distill-web-serve

web-dev:
	cd $(WEB_DIR) && yarn dev

web-build:
	cd $(WEB_DIR) && yarn build
