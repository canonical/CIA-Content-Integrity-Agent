"""
Abstract base class for all CIA agents.
Every agent implements run(state) -> state and can access shared services.
"""

from abc import ABC, abstractmethod
from models.schemas import PipelineState


class BaseAgent(ABC):
    """All agents inherit from BaseAgent for consistent lifecycle and logging."""

    def __init__(self, name: str, verbose: bool = True):
        self.name = name
        self.verbose = verbose

    def log(self, message: str):
        if self.verbose:
            print(f"[{self.name.upper()}] {message}")

    @abstractmethod
    def run(self, state: PipelineState) -> PipelineState:
        """Execute the agent's logic and return updated state."""
        pass