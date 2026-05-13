"""
Stubbed agents for future features.
"""

from datetime import datetime, timezone
from collections import Counter
from agents.base import BaseAgent
from models.schemas import PipelineState


class RedirectChainDetector(BaseAgent):
    def __init__(self, verbose: bool = True):
        super().__init__("RedirectChainDetector", verbose)

    def run(self, state: PipelineState) -> PipelineState:
        count = sum(
            1 for f in state.failures
            if f.error_message and "redirect" in f.error_message.lower()
        )
        print(f"[STUB] Found {count} redirect chain(s) — future 404 risk")
        return state


class ContentDecayScorer(BaseAgent):
    def __init__(self, verbose: bool = True):
        super().__init__("ContentDecayScorer", verbose)

    def run(self, state: PipelineState) -> PipelineState:
        now = datetime.now(timezone.utc)
        for url, meta in state.page_meta.items():
            if meta.last_modified:
                try:
                    last_mod = datetime.fromisoformat(meta.last_modified.replace("Z", "+00:00"))
                    days_old = (now - last_mod.replace(tzinfo=None)).days
                    score = days_old / 365
                    status = "stale" if score > 0.5 else "fresh"
                    print(f"[STUB] {url} decay score: {score:.2f} ({status})")
                except (ValueError, TypeError):
                    print(f"[STUB] {url} decay score: unknown (invalid date)")
        return state


class CrossPageConsistencyAgent(BaseAgent):
    def __init__(self, verbose: bool = True):
        super().__init__("CrossPageConsistency", verbose)

    def run(self, state: PipelineState) -> PipelineState:
        url_counts = Counter(f.broken_url for f in state.failures)
        for url, count in url_counts.items():
            if count > 1:
                print(f"[STUB] Site-wide: {url} on {count} pages")
        return state
