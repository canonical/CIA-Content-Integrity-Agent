import json
import threading
from dataclasses import asdict
from html.parser import HTMLParser
from typing import Callable, Optional
from urllib.parse import urljoin, urlparse

from models.schemas import (
    PipelineState,
    LinkFailure,
    FailureSeverity,
)
from services.http_client import HTTPClient
from services.llm_client import LLMClient
from services.sitemap_service import SitemapService
from services.mock_google_doc_api import MockGoogleDocAPI
from services.mock_directory_api import MockDirectoryAPI
from agents.resolver import ResolverAgent
from agents.owner_resolver import OwnerResolverAgent
from agents.suggestion import SuggestionAgent
from agents.confidence_router import RouterAgent
from agents.notifier import NotifierAgent


class _LinkExtractor(HTMLParser):
    def __init__(self, page_url: str):
        super().__init__()
        self.page_url = page_url
        self.links = []

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        href = None
        if tag == "a" and "href" in attr_dict:
            href = attr_dict["href"]
        elif tag == "img" and "src" in attr_dict:
            href = attr_dict["src"]
        elif tag == "link" and "href" in attr_dict:
            href = attr_dict["href"]
        elif tag == "script" and "src" in attr_dict:
            href = attr_dict["src"]

        if href:
            absolute = urljoin(self.page_url, href)
            self.links.append(absolute)


class PipelineService:
    AGENT_NAMES = [
        "Crawler",
        "Resolver",
        "OwnerResolver",
        "Suggestion",
        "Router",
        "Notifier",
    ]

    def __init__(self, settings=None):
        if settings is None:
            from config.settings import Settings
            settings = Settings.from_env()

        self.settings = settings
        self.http = HTTPClient()
        self.llm = LLMClient(api_key=settings.openrouter_api_key, model=settings.openrouter_model)
        self.doc_api = MockGoogleDocAPI()
        self.directory_api = MockDirectoryAPI()
        self.sitemap = SitemapService(self.http)

    def run_scan(self, route_url: str, scan_id: int, on_progress: Optional[Callable] = None) -> dict:
        state = PipelineState()

        try:
            self._crawl(route_url, state, on_progress, scan_id)
            self._run_pipeline(state, on_progress, scan_id)
        except Exception as exc:
            if on_progress:
                on_progress(scan_id, "failed", 0, None, str(exc))
            raise

        return self._serialize_state(state)

    def _crawl(self, route_url: str, state: PipelineState, on_progress, scan_id: int):
        if on_progress:
            on_progress(scan_id, "crawling", 10, "Crawler", None)

        try:
            html = self.http.get(route_url)
        except Exception as exc:
            raise RuntimeError(f"Failed to fetch {route_url}: {exc}")

        extractor = _LinkExtractor(route_url)
        extractor.feed(html)

        for link_url in extractor.links:
            if not link_url.startswith(("http://", "https://")):
                continue

            severity = FailureSeverity.UNKNOWN
            status_code = None
            error_message = None

            try:
                resp = self.http.session.head(link_url, timeout=10, allow_redirects=True)
                status_code = resp.status_code
                if status_code >= 400:
                    if status_code == 404:
                        severity = FailureSeverity.CRITICAL_404
                        error_message = f"{status_code} Not Found"
                    else:
                        error_message = f"{status_code} Error"
                elif 300 <= status_code < 400:
                    severity = FailureSeverity.REDIRECT_CHAIN
                    error_message = "Redirect"
                else:
                    continue
            except Exception as exc:
                error_message = str(exc)
                if "timeout" in error_message.lower() or "connection" in error_message.lower():
                    severity = FailureSeverity.TIMEOUT

            state.failures.append(LinkFailure(
                source_page=route_url,
                broken_url=link_url,
                status_code=status_code,
                error_message=error_message,
                severity=severity,
            ))

        if on_progress:
            on_progress(scan_id, "analyzing", 15, "Crawler", None)

    def _run_pipeline(self, state: PipelineState, on_progress, scan_id: int):
        agents = [
            ResolverAgent(http_client=self.http, verbose=False),
            OwnerResolverAgent(doc_api=self.doc_api, directory_api=self.directory_api, verbose=False),
            SuggestionAgent(http_client=self.http, llm_client=self.llm, sitemap=self.sitemap, verbose=False),
            RouterAgent(verbose=False),
            NotifierAgent(dry_run=True, verbose=False),
        ]

        total = len(agents)
        for idx, agent in enumerate(agents):
            agent_name = agent.name
            progress = 20 + int(75 * (idx / total))

            if on_progress:
                on_progress(scan_id, "analyzing", progress, agent_name, None)

            try:
                state = agent.run(state)
            except Exception as exc:
                state.log("PipelineService", f"{agent_name.upper()}_FAILED",
                          f"agent={agent_name}", f"error={exc}")

        if on_progress:
            on_progress(scan_id, "complete", 100, None, None)

    def _serialize_state(self, state: PipelineState) -> dict:
        def _default(obj):
            if hasattr(obj, "__dict__"):
                return obj.__dict__
            if hasattr(obj, "value"):
                return obj.value
            return str(obj)

        return json.loads(json.dumps(asdict(state), default=_default))