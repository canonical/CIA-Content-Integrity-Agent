#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

case "${1:-help}" in
    demo)
        echo "Running Content Integrity Agent Demo..."
        python3 cli.py --input fixtures/linkchecker-output.txt --verbose --dry-run
        ;;
    test)
        echo "Running contract tests..."
        python3 -c "
from agents.discovery import DiscoveryAgent; print('✅ DiscoveryAgent OK')
from agents.resolver import ResolverAgent; print('✅ ResolverAgent OK')
from agents.owner_resolver import OwnerResolverAgent; print('✅ OwnerResolverAgent OK')
from agents.suggestion import SuggestionAgent; print('✅ SuggestionAgent OK')
from agents.confidence_router import RouterAgent; print('✅ RouterAgent OK')
from agents.notifier import NotifierAgent; print('✅ NotifierAgent OK')
from agents.orchestrator import OrchestratorAgent; print('✅ OrchestratorAgent OK')
from services.http_client import HTTPClient; print('✅ HTTPClient OK')
from services.llm_client import LLMClient; print('✅ LLMClient OK')
from services.sitemap_service import SitemapService; print('✅ SitemapService OK')
from services.mock_google_doc_api import MockGoogleDocAPI; print('✅ MockGoogleDocAPI OK')
from services.mock_directory_api import MockDirectoryAPI; print('✅ MockDirectoryAPI OK')
from utils.decorators import retry; print('✅ retry OK')
from utils.cache import SimpleCache; print('✅ SimpleCache OK')
from utils.logger import StructuredLogger; print('✅ StructuredLogger OK')
from utils.html_parser import extract_page_meta; print('✅ extract_page_meta OK')
"
        echo ""
        echo "Running e2e test..."
        python3 tests/test_e2e.py
        ;;
    lint)
        echo "Checking imports..."
        python3 -c "from agents.discovery import DiscoveryAgent; print('✅ DiscoveryAgent OK')"
        python3 -c "from agents.resolver import ResolverAgent; print('✅ ResolverAgent OK')"
        python3 -c "from agents.owner_resolver import OwnerResolverAgent; print('✅ OwnerResolverAgent OK')"
        python3 -c "from agents.suggestion import SuggestionAgent; print('✅ SuggestionAgent OK')"
        python3 -c "from agents.confidence_router import RouterAgent; print('✅ RouterAgent OK')"
        python3 -c "from agents.notifier import NotifierAgent; print('✅ NotifierAgent OK')"
        python3 -c "from agents.orchestrator import OrchestratorAgent; print('✅ OrchestratorAgent OK')"
        ;;
    install)
        echo "No pip install needed - using stdlib only"
        echo "✅ Ready to run (requires Python 3.10+)"
        ;;
    clean)
        rm -rf .cache
        find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
        find . -type f -name "*.pyc" -delete 2>/dev/null || true
        echo "✅ Cleaned"
        ;;
    help|*)
        echo "Usage: ./run.sh <command>"
        echo ""
        echo "Commands:"
        echo "  demo    - Run full pipeline demo"
        echo "  test    - Run all tests"
        echo "  lint    - Verify all imports work"
        echo "  install - Check dependencies (no-op)"
        echo "  clean   - Remove cache and pyc files"
        echo "  help    - Show this help message"
        ;;
esac
