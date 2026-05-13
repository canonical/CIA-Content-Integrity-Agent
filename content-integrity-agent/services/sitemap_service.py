"""
SitemapService: In-memory URL index with Jaccard similarity matching.
"""

import re

from utils.url_similarity import get_path_segments, jaccard_similarity


class SitemapService:
    """Builds an in-memory index of known site URLs for similarity matching."""

    def __init__(self, http_client, url_index: set = None):
        self.http = http_client
        self._url_index = url_index or set()

    def find_similar(self, broken_url: str, top_k: int = 5) -> list:
        broken_segments = get_path_segments(broken_url)
        scored = []
        for url in self._url_index:
            candidate_segments = get_path_segments(url)
            score = jaccard_similarity(broken_segments, candidate_segments)
            if score > 0.1:
                scored.append((url, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [url for url, _ in scored[:top_k]]

    def get_page_context(self, html: str, broken_url: str) -> str:
        pattern = re.compile(
            r'<a\s[^>]*href=["\']' + re.escape(broken_url) + r'["\'][^>]*>.*?</a>',
            re.IGNORECASE | re.DOTALL,
        )
        match = pattern.search(html)
        if not match:
            body_start = html.find("<body>")
            body_end = html.find("</body>")
            if body_start != -1 and body_end != -1:
                return html[body_start + 6:body_end][:1000]
            return html[:1000]
        start = max(0, match.start() - 200)
        end = min(len(html), match.end() + 200)
        return html[start:end]
