import json
import pytest
from unittest.mock import patch, MagicMock
from services.llm_client import LLMClient


def test_suggest_fix_returns_dict():
    """Without API key, should return fallback dict."""
    client = LLMClient(api_key=None, model="test/model")
    result = client.suggest_fix(
        broken_url="https://canonical.com/old-data-docs",
        source_page="https://canonical.com/data",
        page_context="Some context about old docs",
        candidate_urls=["https://canonical.com/data/docs"],
    )
    assert isinstance(result, dict)
    assert "suggested_url" in result
    assert "confidence" in result
    assert "reasoning" in result
    assert "user_facing_explanation" in result


def test_suggest_fix_fallback_picks_best_candidate():
    """Fallback should pick the candidate with highest Jaccard similarity."""
    client = LLMClient(api_key=None)
    result = client.suggest_fix(
        broken_url="https://canonical.com/old-data-docs",
        source_page="https://canonical.com/data",
        page_context="context",
        candidate_urls=["https://canonical.com/data/docs", "https://canonical.com/kubernetes"],
    )
    # /data/docs has more path segment overlap with /old-data-docs than /kubernetes
    assert result["suggested_url"] == "https://canonical.com/data/docs"


def test_suggest_fix_fallback_confidence_capped():
    """Fallback confidence must be <= 0.5."""
    client = LLMClient(api_key=None)
    result = client.suggest_fix(
        broken_url="https://canonical.com/old-data-docs",
        source_page="https://canonical.com/data",
        page_context="context",
        candidate_urls=["https://canonical.com/data/docs"],
    )
    assert result["confidence"] <= 0.5


def test_suggest_fix_fallback_no_candidates():
    """Fallback with empty candidates should return null suggested_url."""
    client = LLMClient(api_key=None)
    result = client.suggest_fix(
        broken_url="https://canonical.com/old-data-docs",
        source_page="https://canonical.com/data",
        page_context="context",
        candidate_urls=[],
    )
    assert result["suggested_url"] is None
    assert result["confidence"] == 0.0


def test_parse_json_response_plain():
    """Test parsing plain JSON."""
    client = LLMClient(api_key="fake")
    result = client._parse_json_response('{"suggested_url": "https://example.com", "confidence": 0.9, "reasoning": "test", "user_facing_explanation": "try this"}')
    assert result["suggested_url"] == "https://example.com"
    assert result["confidence"] == 0.9


def test_parse_json_response_with_fences():
    """Test parsing JSON wrapped in markdown fences."""
    client = LLMClient(api_key="fake")
    raw = '```json\n{"suggested_url": "https://example.com", "confidence": 0.8, "reasoning": "test", "user_facing_explanation": "try"}\n```'
    result = client._parse_json_response(raw)
    assert result["suggested_url"] == "https://example.com"
    assert result["confidence"] == 0.8


def test_parse_json_response_invalid():
    """Test parsing invalid JSON returns error dict."""
    client = LLMClient(api_key="fake")
    result = client._parse_json_response("not json at all")
    assert result["confidence"] == 0.0
    assert "error" in result["reasoning"].lower() or "parse" in result["reasoning"].lower()


def test_suggest_fix_with_mock_api():
    """Test full suggest_fix with mocked requests.post."""
    client = LLMClient(api_key="sk-test-key", model="test/model")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "suggested_url": "https://canonical.com/data/docs",
                    "confidence": 0.85,
                    "reasoning": "Path similarity",
                    "user_facing_explanation": "Did you mean /data/docs?"
                })
            }
        }]
    }
    with patch("services.llm_client.requests.post", return_value=mock_response):
        result = client.suggest_fix(
            broken_url="https://canonical.com/old-data-docs",
            source_page="https://canonical.com/data",
            page_context="context",
            candidate_urls=["https://canonical.com/data/docs"],
        )
    assert result["suggested_url"] == "https://canonical.com/data/docs"
    assert result["confidence"] == 0.85


def test_suggest_fix_api_failure_falls_back():
    """If API call raises, should fall back to deterministic."""
    client = LLMClient(api_key="sk-test-key")
    with patch("services.llm_client.requests.post", side_effect=Exception("network error")):
        result = client.suggest_fix(
            broken_url="https://canonical.com/old-data-docs",
            source_page="https://canonical.com/data",
            page_context="context",
            candidate_urls=["https://canonical.com/data/docs"],
        )
    assert isinstance(result, dict)
    assert result["confidence"] <= 0.5


def test_draft_email_basic():
    """draft_email should produce a formatted email string."""
    client = LLMClient(api_key=None)
    result = client.draft_email("Alice", 2, [], "notify_investigate")
    assert "Alice" in result
    assert "2" in result
    assert "notify_investigate" in result
    assert "Content Integrity Agent" in result


def test_draft_email_with_suggestions():
    """draft_email should include suggestion details."""
    client = LLMClient(api_key=None)
    suggestions = [
        {"suggested_url": "https://canonical.com/data/docs", "user_facing_explanation": "Did you mean /data/docs?"},
        {"suggested_url": "https://canonical.com/kubernetes/docs", "user_facing_explanation": "Try /kubernetes/docs"},
    ]
    result = client.draft_email("Bob", 2, suggestions, "notify_with_suggestion")
    assert "data/docs" in result
    assert "kubernetes/docs" in result


def test_draft_email_with_string_suggestions():
    """draft_email should handle plain string suggestions."""
    client = LLMClient(api_key=None)
    result = client.draft_email("Charlie", 1, ["Check the URL manually"], "escalate_ops")
    assert "Check the URL manually" in result
