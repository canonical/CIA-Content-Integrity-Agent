"""
Stubbed agents for future features.
ENGINEER C: Implement these stubs.
"""

from agents.base import BaseAgent
from models.schemas import PipelineState


class RedirectChainDetector(BaseAgent):
    def __init__(self, verbose: bool = True):
        super().__init__("RedirectChainDetector", verbose)

    def run(self, state: PipelineState) -> PipelineState:
        raise NotImplementedError("Engineer C: Implement redirect chain detection stub")


class ContentDecayScorer(BaseAgent):
    def __init__(self, verbose: bool = True):
        super().__init__("ContentDecayScorer", verbose)

    def run(self, state: PipelineState) -> PipelineState:
        raise NotImplementedError("Engineer C: Implement content decay scoring stub")


class CrossPageConsistencyAgent(BaseAgent):
    def __init__(self, verbose: bool = True):
        super().__init__("CrossPageConsistency", verbose)

    def run(self, state: PipelineState) -> PipelineState:
        raise NotImplementedError("Engineer C: Implement cross-page consistency stub")
