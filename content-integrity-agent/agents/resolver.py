"""
ResolverAgent: Fetches page HTML and extracts <meta name="copydoc">.
ENGINEER B: Implement this agent.
"""

from agents.base import BaseAgent
from models.schemas import PipelineState


class ResolverAgent(BaseAgent):
    """Fetches source pages and extracts copydoc metadata."""

    def __init__(self, http_client, verbose: bool = True):
        super().__init__("Resolver", verbose)
        self.http = http_client

    def run(self, state: PipelineState) -> PipelineState:
        raise NotImplementedError("Engineer B: Implement HTML meta extraction")
