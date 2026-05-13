"""
OwnerResolverAgent: Resolves copydoc URLs → Google Doc owner → Directory user.
ENGINEER B: Implement this agent.
"""

from agents.base import BaseAgent
from models.schemas import PipelineState


class OwnerResolverAgent(BaseAgent):
    """Looks up page owners via copydoc → Google Doc → Directory API chain."""

    def __init__(self, doc_api, directory_api, verbose: bool = True):
        super().__init__("OwnerResolver", verbose)
        self.doc_api = doc_api
        self.directory = directory_api

    def run(self, state: PipelineState) -> PipelineState:
        raise NotImplementedError("Engineer B: Implement owner resolution chain")
