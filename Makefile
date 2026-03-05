SHELL := /bin/bash
.PHONY: dev test lint fmt help

# ── Help ─────────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  NBAJinni — available commands"
	@echo ""
	@echo "  make dev      Start backend + frontend dev servers"
	@echo "  make test     Run all tests (backend + frontend)"
	@echo "  make lint     Run all linters (Python + TypeScript)"
	@echo "  make fmt      Auto-format all code (black + prettier)"
	@echo ""

# ── Dev servers ──────────────────────────────────────────────────────────────
dev:
	$(MAKE) -j2 dev-backend dev-frontend

dev-backend:
	cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

# ── Tests ─────────────────────────────────────────────────────────────────────
test:
	$(MAKE) test-backend
	$(MAKE) test-frontend

test-backend:
	cd backend && source .venv/bin/activate && pytest

test-frontend:
	cd frontend && npm run test

# ── Linting ──────────────────────────────────────────────────────────────────
lint:
	$(MAKE) lint-backend
	$(MAKE) lint-frontend

lint-backend:
	cd backend && source .venv/bin/activate && flake8 . && black --check . && isort --check .

lint-frontend:
	cd frontend && npm run lint && npx tsc --noEmit

# ── Formatting ───────────────────────────────────────────────────────────────
fmt:
	cd backend && source .venv/bin/activate && black . && isort .
	cd frontend && npx prettier --write .
