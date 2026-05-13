import pytest
from unittest.mock import MagicMock
from agents.suggestion import SuggestionAgent
from models.schemas import (
    PipelineState, LinkFailure, PageMeta, FixSuggestion, FailureSeverity,
)


def _make_failure(broken_url="https://canonical.com/old-data-docs",
                  source_page="https://canonical.com/data"):
    return LinkFailure(
        source_page=source_page,
        broken_url=broken_url,
        status_code=404,
        error_message="404 Not Found",
        severity=FailureSeverity.CRITICAL_404,
        line_number=42,
    )


def _make_state(failures=None, page_meta=None):
    state = PipelineState()
    if failures:
        state.failures = failures
    if page_meta:
        state.page_meta = page_meta
    return state


def test_suggestion_agent_returns_state():
    http = MagicMock()
    http.get.return_value = "<html><body><a href='https://canonical.com/old-data-docs'>Old</a></body></html>"
    llm = MagicMock()
    llm.suggest_fix.return_value = {
        "suggested_url": "https://canonical.com/data/docs",
        "confidence": 0.85,
        "reasoning": "Path similarity",
        "user_facing_explanation": "Did you mean /data/docs?",
    }
    sitemap = MagicMock()
    sitemap.find_similar.return_value = ["https://canonical.com/data/docs"]
    sitemap.get_page_context.return_value = "Old docs context"

    agent = SuggestionAgent(http_client=http, llm_client=llm, sitemap=sitemap, verbose=False)
    state = _make_state(failures=[_make_failure()])
    result = agent.run(state)
    assert isinstance(result, PipelineState)


def test_suggestion_agent_populates_suggestions():
    http = MagicMock()
    http.get.return_value = "<html></html>"
    llm = MagicMock()
    llm.suggest_fix.return_value = {
        "suggested_url": "https://canonical.com/data/docs",
        "confidence": 0.85,
        "reasoning": "test",
        "user_facing_explanation": "try this",
    }
    sitemap = MagicMock()
    sitemap.find_similar.return_value = ["https://canonical.com/data/docs"]
    sitemap.get_page_context.return_value = "context"

    agent = SuggestionAgent(http_client=http, llm_client=llm, sitemap=sitemap, verbose=False)
    failure = _make_failure()
    state = _make_state(failures=[failure])
    result = agent.run(state)

    uid = failure.unique_id()
    assert uid in result.suggestions
    assert len(result.suggestions[uid]) == 1
    assert result.suggestions[uid][0].suggested_url == "https://canonical.com/data/docs"


def test_suggestion_agent_clamps_confidence():
    http = MagicMock()
    http.get.return_value = "<html></html>"
    llm = MagicMock()
    llm.suggest_fix.return_value = {
        "suggested_url": "https://canonical.com/data/docs",
        "confidence": 1.5,  # Out of range
        "reasoning": "test",
        "user_facing_explanation": "try",
    }
    sitemap = MagicMock()
    sitemap.find_similar.return_value = []
    sitemap.get_page_context.return_value = ""

    agent = SuggestionAgent(http_client=http, llm_client=llm, sitemap=sitemap, verbose=False)
    state = _make_state(failures=[_make_failure()])
    result = agent.run(state)

    uid = _make_failure().unique_id()
    assert result.suggestions[uid][0].confidence <= 1.0


def test_suggestion_agent_handles_llm_exception():
    http = MagicMock()
    http.get.return_value = "<html></html>"
    llm = MagicMock()
    llm.suggest_fix.side_effect = Exception("API down")
    sitemap = MagicMock()
    sitemap.find_similar.return_value = []
    sitemap.get_page_context.return_value = ""

    agent = SuggestionAgent(http_client=http, llm_client=llm, sitemap=sitemap, verbose=False)
    state = _make_state(failures=[_make_failure()])
    result = agent.run(state)
    # Should not crash; state should be returned
    assert isinstance(result, PipelineState)


def test_suggestion_agent_logs_audit():
    http = MagicMock()
    http.get.return_value = "<html></html>"
    llm = MagicMock()
    llm.suggest_fix.return_value = {
        "suggested_url": None, "confidence": 0.0,
        "reasoning": "none", "user_facing_explanation": "none",
    }
    sitemap = MagicMock()
    sitemap.find_similar.return_value = []
    sitemap.get_page_context.return_value = ""

    agent = SuggestionAgent(http_client=http, llm_client=llm, sitemap=sitemap, verbose=False)
    state = _make_state(failures=[_make_failure()])
    result = agent.run(state)
    assert len(result.audit_log) > 0
    assert any("Suggestion" in entry.agent_name for entry in result.audit_log)
