"""
LLMClient: OpenRouter client for LLM-powered reasoning.
ENGINEER C: Implement this service.
"""

class LLMClient:
    """Client for OpenRouter API."""

    def __init__(self, api_key=None, model=None):
        self.api_key = api_key
        self.model = model or "openai/gpt-4o-mini"

    def suggest_fix(self, broken_url: str, source_page: str, page_context: str,
                    candidate_urls: list) -> dict:
        raise NotImplementedError("Engineer C: Implement LLM suggestion call")

    def draft_email(self, owner_name: str, failure_count: int, suggestions: list,
                    action: str) -> str:
        raise NotImplementedError("Engineer C: Implement LLM email drafting")
