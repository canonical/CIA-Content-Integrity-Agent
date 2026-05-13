# Content Integrity Agent - Makefile
# Quick commands for hackathon workflow

.PHONY: demo test install clean lint help

# Default target
demo:
	@echo "🔍 Content Integrity Agent - Running Demo"
	@python cli.py --input fixtures/linkchecker-output.txt --verbose --dry-run

test:
	@echo "🧪 Running contract tests..."
	@python -m pytest tests/test_contracts.py -v
	@echo ""
	@echo "🧪 Running compliance tests..."
	@python -m pytest tests/test_compliance.py -v
	@echo ""
	@echo "🧪 Running Google Doc fetcher tests..."
	@python -m pytest tests/test_google_doc_fetcher.py -v
	@echo ""
	@echo "🧪 Running end-to-end test..."
	@python tests/test_e2e.py

install:
	@echo "📦 No pip install needed - using stdlib only"
	@echo "✅ Ready to run (requires Python 3.10+)"

clean:
	@rm -rf .cache
	@find . -type d -name __pycache__ -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete

lint:
	@echo "🔍 Checking imports..."
	@python -c "from agents.discovery import DiscoveryAgent; print('✅ DiscoveryAgent OK')"
	@python -c "from agents.resolver import ResolverAgent; print('✅ ResolverAgent OK')"
	@python -c "from agents.owner_resolver import OwnerResolverAgent; print('✅ OwnerResolverAgent OK')"
	@python -c "from agents.suggestion import SuggestionAgent; print('✅ SuggestionAgent OK')"
	@python -c "from agents.compliance import ComplianceAgent; print('✅ ComplianceAgent OK')"
	@python -c "from agents.confidence_router import RouterAgent; print('✅ RouterAgent OK')"
	@python -c "from agents.notifier import NotifierAgent; print('✅ NotifierAgent OK')"
	@python -c "from agents.orchestrator import OrchestratorAgent; print('✅ OrchestratorAgent OK')"
	@python -c "from services.google_doc_fetcher import GoogleDocFetcher; print('✅ GoogleDocFetcher OK')"

help:
	@echo "Available targets:"
	@echo "  make demo    - Run full pipeline demo"
	@echo "  make test    - Run all tests"
	@echo "  make install - Check dependencies (no-op, stdlib only)"
	@echo "  make clean   - Remove cache and pyc files"
	@echo "  make lint    - Verify all imports work"
	@echo "  make help    - Show this help message"