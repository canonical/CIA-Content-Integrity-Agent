"""
NotifierAgent: Outputs notifications to console (mock email delivery).
ENGINEER C: Implement this agent.
"""

from agents.base import BaseAgent
from models.schemas import PipelineState


class NotifierAgent(BaseAgent):
    """Prints notifications to console as mock email delivery."""

    def __init__(self, dry_run: bool = True, verbose: bool = True):
        super().__init__("Notifier", verbose)
        self.dry_run = dry_run

    def run(self, state: PipelineState) -> PipelineState:
        raise NotImplementedError("Engineer C: Implement console notification output")
