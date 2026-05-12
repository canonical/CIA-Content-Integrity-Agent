"""
OrchestratorAgent: The director that runs all specialist agents sequentially.
ENGINEER A: Implement this agent.
"""

from agents.base import BaseAgent
from models.schemas import PipelineState
from typing import List


class OrchestratorAgent(BaseAgent):
    """Runs the full agent pipeline end-to-end."""

    def __init__(self, agents: List[BaseAgent], verbose: bool = True):
        super().__init__("Orchestrator", verbose)
        self.agents = agents

    def run(self, state: PipelineState) -> PipelineState:
        raise NotImplementedError("Engineer A: Implement orchestrator logic")
