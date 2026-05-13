import pytest
from services.sitemap_service import SitemapService


class FakeHTTPClient:
    pass


SAMPLE_URL_INDEX = {
    "https://canonical.com/data",
    "https://canonical.com/data/docs",
    "https://canonical.com/kubernetes",
    "https://canonical.com/kubernetes/docs",
    "https://canonical.com/microk8s",
    "https://canonical.com/microk8s/docs",
    "https://canonical.com/openstack",
    "https://canonical.com/openstack/pricing",
}


def test_find_similar_returns_list():
    svc = SitemapService(FakeHTTPClient(), url_index=SAMPLE_URL_INDEX)
    result = svc.find_similar("https://canonical.com/old-data-docs")
    assert isinstance(result, list)


def test_find_similar_finds_data_docs():
    svc = SitemapService(FakeHTTPClient(), url_index=SAMPLE_URL_INDEX)
    result = svc.find_similar("https://canonical.com/old-data-docs")
    assert any("data/docs" in u for u in result)


def test_find_similar_respects_top_k():
    svc = SitemapService(FakeHTTPClient(), url_index=SAMPLE_URL_INDEX)
    result = svc.find_similar("https://canonical.com/old-data-docs", top_k=1)
    assert len(result) <= 1


def test_find_similar_returns_empty_for_no_match():
    svc = SitemapService(FakeHTTPClient(), url_index=SAMPLE_URL_INDEX)
    result = svc.find_similar("https://totally-different.com/nothing")
    assert result == []


def test_find_similar_empty_index():
    svc = SitemapService(FakeHTTPClient(), url_index=set())
    result = svc.find_similar("https://canonical.com/old-data-docs")
    assert result == []


def test_find_similar_custom_index():
    custom = {"https://example.com/foo", "https://example.com/foo-bar"}
    svc = SitemapService(FakeHTTPClient(), url_index=custom)
    result = svc.find_similar("https://example.com/old-foo")
    assert any("foo" in u for u in result)


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
