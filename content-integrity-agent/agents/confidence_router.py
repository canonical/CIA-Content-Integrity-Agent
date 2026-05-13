"""
RouterAgent: Makes agentic routing decisions per failure.
ENGINEER C: Implement this agent.
"""

from agents.base import BaseAgent
from models.schemas import PipelineState


class RouterAgent(BaseAgent):
    """Makes agentic routing decisions per failure."""

    def __init__(self, verbose: bool = True):
        super().__init__("Router", verbose)

    def run(self, state: PipelineState) -> PipelineState:
        raise NotImplementedError("Engineer C: Implement confidence-based routing")
