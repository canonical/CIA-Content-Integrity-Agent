"""
SuggestionAgent: Uses LLM reasoning to suggest fixes for broken links.
ENGINEER C: Implement this agent.
"""

from agents.base import BaseAgent
from models.schemas import PipelineState


class SuggestionAgent(BaseAgent):
    """Intelligent fix suggestion using LLM reasoning."""

    def __init__(self, http_client, llm_client, sitemap, verbose: bool = True):
        super().__init__("Suggestion", verbose)
        self.http = http_client
        self.llm = llm_client
        self.sitemap = sitemap

    def run(self, state: PipelineState) -> PipelineState:
        raise NotImplementedError("Engineer C: Implement LLM suggestion logic")
