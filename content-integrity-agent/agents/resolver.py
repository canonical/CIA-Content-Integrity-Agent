"""
ResolverAgent: Fetches page HTML and extracts <meta name="copydoc">.
Supports fetching from a sitemap (list of URLs), a single path, or deriving
source pages from state.failures if neither is provided.
"""
import os
from typing import Optional, List, Union

from agents.base import BaseAgent
from models.schemas import PipelineState, PageMeta
from utils.html_parser import extract_page_meta


FIXTURE_MAP = {
    "https://canonical.com/data": "fixtures/pages/data.html",
    "https://canonical.com/kubernetes": "fixtures/pages/kubernetes.html",
    "https://canonical.com/microk8s": "fixtures/pages/microk8s.html",
    "https://canonical.com/openstack": "fixtures/pages/openstack.html",
}


class ResolverAgent(BaseAgent):
    """Fetches source pages and extracts copydoc metadata."""

    def __init__(self, http_client, pages: Union[str, List[str], None] = None,
                 verbose: bool = True):
        super().__init__("Resolver", verbose)
        self.http = http_client
        self.pages = pages

    def _resolve_path(self, rel_path: str) -> str:
        if os.path.isfile(rel_path):
            return rel_path
        alt = os.path.join("content-integrity-agent", rel_path)
        if os.path.isfile(alt):
            return alt
        return rel_path

    def _source_urls(self, state: PipelineState) -> List[str]:
        if self.pages:
            if isinstance(self.pages, str):
                return [self.pages]
            return self.pages
        seen = set()
        for f in state.failures:
            if f.source_page not in seen:
                seen.add(f.source_page)
        return list(seen)

    def _fetch_html(self, url: str) -> str:
        if url in FIXTURE_MAP:
            path = self._resolve_path(FIXTURE_MAP[url])
            with open(path, "r") as fh:
                html = fh.read()
            self.log(f"Loaded fixture {path}")
            return html
        html = self.http.get(url)
        self.log(f"Fetched {url}")
        return html

    def run(self, state: PipelineState) -> PipelineState:
        for url in self._source_urls(state):
            try:
                html = self._fetch_html(url)
            except Exception:
                html = ""
                self.log(f"Fetch failed for {url}, storing empty PageMeta")

            meta = extract_page_meta(html) if html else {}
            state.page_meta[url] = PageMeta(
                url=url,
                copydoc_url=meta.get("copydoc_url"),
                title=meta.get("title"),
            )

        self.log(f"Resolved {len(state.page_meta)} page(s)")
        state.log("Resolver", "FETCH", f"urls={len(state.page_meta)}",
                  f"meta={len(state.page_meta)}")
        return state
