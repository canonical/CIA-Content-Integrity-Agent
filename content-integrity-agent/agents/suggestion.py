"""
SuggestionAgent: Uses LLM reasoning to suggest fixes for broken links.
"""

from models.schemas import FixSuggestion, PipelineState
from agents.base import BaseAgent


class SuggestionAgent(BaseAgent):
    """Intelligent fix suggestion using LLM reasoning."""

    def __init__(self, http_client, llm_client, sitemap, verbose: bool = True):
        super().__init__("Suggestion", verbose)
        self.http = http_client
        self.llm = llm_client
        self.sitemap = sitemap

    def run(self, state: PipelineState) -> PipelineState:
        for failure in state.failures:
            try:
                self._process_failure(state, failure)
            except Exception as exc:
                self.log(f"Error processing {failure.unique_id()}: {exc}")
                state.log(
                    self.name,
                    "error",
                    f"failure={failure.unique_id()}",
                    str(exc),
                )
        return state

    def _process_failure(self, state, failure):
        uid = failure.unique_id()

        candidates = self.sitemap.find_similar(failure.broken_url, top_k=5)

        html = self.http.get(failure.source_page)
        context = self.sitemap.get_page_context(html, failure.broken_url)
        page_context = context[:1000] if context else ""

        llm_result = self.llm.suggest_fix(
            broken_url=failure.broken_url,
            source_page=failure.source_page,
            page_context=page_context,
            candidate_urls=candidates,
        )

        confidence = max(0.0, min(1.0, float(llm_result.get("confidence", 0.0))))

        suggestion = FixSuggestion(
            original_url=failure.broken_url,
            suggested_url=llm_result.get("suggested_url"),
            suggestion_text=llm_result.get("user_facing_explanation", ""),
            confidence=confidence,
            reasoning=llm_result.get("reasoning", ""),
        )

        state.suggestions[uid] = [suggestion]

        state.log(
            self.name,
            "ANALYZE",
            f"failure={uid}",
            f"suggested={suggestion.suggested_url} confidence={confidence}",
            confidence=confidence,
        )

        self.log(f"Suggested fix for {failure.broken_url}: {suggestion.suggested_url} (confidence={confidence})")
