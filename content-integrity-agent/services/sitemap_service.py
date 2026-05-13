"""
SitemapService: In-memory URL index with Jaccard similarity matching.
"""

import re
from urllib.parse import urlparse


class SitemapService:
    """Builds an in-memory index of known site URLs for similarity matching."""

    def __init__(self, http_client, url_index: set = None):
        self.http = http_client
        self._url_index = url_index or set()

    def _get_path_segments(self, url: str) -> set:
        parsed = urlparse(url)
        path = parsed.path.strip("/")
        if not path:
            return set()
        segments = []
        for part in path.split("/"):
            segments.extend(part.split("-"))
        return set(segments)

    def _jaccard_similarity(self, set1: set, set2: set) -> float:
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0

    def find_similar(self, broken_url: str, top_k: int = 5) -> list:
        broken_segments = self._get_path_segments(broken_url)
        scored = []
        for url in self._url_index:
            candidate_segments = self._get_path_segments(url)
            score = self._jaccard_similarity(broken_segments, candidate_segments)
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
