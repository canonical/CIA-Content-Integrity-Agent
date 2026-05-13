"""
Integration test: Engineer C's services and agents working together
with manually-constructed PipelineState (no dependency on Engineer B).
"""
import pytest
from unittest.mock import MagicMock
from services.sitemap_service import SitemapService
from services.llm_client import LLMClient
from agents.suggestion import SuggestionAgent
from agents.confidence_router import RouterAgent
from agents.notifier import NotifierAgent
from models.schemas import (
    PipelineState, LinkFailure, PageMeta, Owner, FailureSeverity,
)


def test_c_pipeline_smoke():
    """Smoke test: suggestion → router → notifier with mock data."""
    # Construct state as if Engineer B's agents already ran
    state = PipelineState()

    failure = LinkFailure(
        source_page="https://canonical.com/data",
        broken_url="https://canonical.com/old-data-docs",
        status_code=404,
        error_message="404 Not Found",
        severity=FailureSeverity.CRITICAL_404,
        line_number=42,
    )
    state.failures = [failure]

    state.page_meta = {
        "https://canonical.com/data": PageMeta(
            url="https://canonical.com/data",
            copydoc_url="https://docs.google.com/document/d/1QKc7tHZZSJttrPOziK_w_9yKLLgoC4Vcufke9dSvQ-g/edit",
            title="Data Solutions",
            page_owner_email="alice.chen@canonical.com",
        ),
    }

    state.owners = {
        "alice.chen@canonical.com": Owner(
            email="alice.chen@canonical.com",
            display_name="Alice Chen",
            team="Data Platform Engineering",
            department="Engineering",
        ),
    }

    # Mock HTTP client
    http = MagicMock()
    http.get.return_value = '<html><body><a href="https://canonical.com/old-data-docs">Old docs</a></body></html>'

    # Use real sitemap service with URL index
    url_index = {
        "https://canonical.com/data",
        "https://canonical.com/data/docs",
        "https://canonical.com/kubernetes",
        "https://canonical.com/kubernetes/docs",
        "https://canonical.com/microk8s",
        "https://canonical.com/microk8s/docs",
        "https://canonical.com/openstack",
        "https://canonical.com/openstack/pricing",
    }
    sitemap = SitemapService(http, url_index=url_index)

    # Mock LLM client (no API key -> fallback)
    llm = LLMClient(api_key=None)

    # Run SuggestionAgent
    suggestion_agent = SuggestionAgent(http_client=http, llm_client=llm, sitemap=sitemap, verbose=False)
    state = suggestion_agent.run(state)
    assert len(state.suggestions) == 1

    # Run RouterAgent
    router_agent = RouterAgent(verbose=False)
    state = router_agent.run(state)
    assert len(state.notifications) >= 1

    # Run NotifierAgent
    notifier_agent = NotifierAgent(dry_run=True, verbose=False)
    state = notifier_agent.run(state)

    # Verify full audit trail
    assert len(state.audit_log) >= 3  # suggestion + router + notifier
    agent_names = {entry.agent_name for entry in state.audit_log}
    assert "Suggestion" in agent_names
    assert "Router" in agent_names
    assert "Notifier" in agent_names