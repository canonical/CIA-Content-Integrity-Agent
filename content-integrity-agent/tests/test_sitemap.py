import pytest
from services.sitemap_service import SitemapService


class FakeHTTPClient:
    pass


def test_find_similar_returns_list():
    svc = SitemapService(FakeHTTPClient())
    result = svc.find_similar("https://canonical.com/old-data-docs")
    assert isinstance(result, list)


def test_find_similar_finds_data_docs():
    svc = SitemapService(FakeHTTPClient())
    result = svc.find_similar("https://canonical.com/old-data-docs")
    assert any("data/docs" in u for u in result)


def test_find_similar_respects_top_k():
    svc = SitemapService(FakeHTTPClient())
    result = svc.find_similar("https://canonical.com/old-data-docs", top_k=1)
    assert len(result) <= 1


def test_find_similar_returns_empty_for_no_match():
    svc = SitemapService(FakeHTTPClient())
    result = svc.find_similar("https://totally-different.com/nothing")
    assert result == []


def test_get_page_context_returns_string():
    svc = SitemapService(FakeHTTPClient())
    html = '<html><body><a href="https://canonical.com/old-data-docs">Old docs</a></body></html>'
    result = svc.get_page_context(html, "https://canonical.com/old-data-docs")
    assert isinstance(result, str)


def test_get_page_context_contains_surrounding_text():
    svc = SitemapService(FakeHTTPClient())
    html = '<html><body><p>Check out our <a href="https://canonical.com/old-data-docs">old docs</a> for details.</p></body></html>'
    result = svc.get_page_context(html, "https://canonical.com/old-data-docs")
    assert "old docs" in result.lower() or "old-docs" in result.lower()


def test_get_page_context_fallback_when_not_found():
    svc = SitemapService(FakeHTTPClient())
    html = '<html><head><title>Test</title></head><body><p>No links here.</p></body></html>'
    result = svc.get_page_context(html, "https://canonical.com/nonexistent")
    assert isinstance(result, str)
    assert len(result) > 0
