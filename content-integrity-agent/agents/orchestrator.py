import sys
from agents.base import BaseAgent
from models.schemas import PipelineState, RouterAction
from typing import List


class OrchestratorAgent(BaseAgent):
    def __init__(self, agents: List[BaseAgent], verbose: bool = True):
        super().__init__("Orchestrator", verbose)
        self.agents = agents

    def run(self, state: PipelineState) -> PipelineState:
        total = len(self.agents)
        for idx, agent in enumerate(self.agents, 1):
            self._print_progress(idx, total, agent.name)
            try:
                state = agent.run(state)
            except Exception as exc:
                self.log(f"ERROR in {agent.name}: {exc}")
                state.log(
                    self.name,
                    f"{agent.name.upper()}_FAILED",
                    f"agent={agent.name}",
                    f"error={exc}",
                )
            self._print_complete(idx, total, agent.name, state)

        self._print_summary(state)
        return state

    def _print_progress(self, current: int, total: int, name: str):
        bar = self._bar(current, total, 20)
        print(f"\r{bar} [{current}/{total}] Running {name}...", end="", flush=True)

    def _print_complete(self, current: int, total: int, name: str, state: PipelineState):
        bar = self._bar(current, total, 20, fill=True)
        count = self._state_count(name, state)
        detail = f" ({count})" if count else ""
        print(f"\r{bar} [{current}/{total}] {name} complete{detail}    ")

    def _bar(self, current: int, total: int, width: int, fill: bool = False) -> str:
        filled = int(width * current / total) if total else width
        if fill:
            filled = width
        return f"[{'█' * filled}{'░' * (width - filled)}]"

    def _state_count(self, name: str, state: PipelineState) -> str:
        counts = {
            "Discovery": f"{len(state.failures)} failures",
            "Resolver": f"{len(state.page_meta)} pages",
            "OwnerResolver": f"{len(state.owners)} owners",
            "Suggestion": f"{sum(len(v) for v in state.suggestions.values())} suggestions",
            "Router": f"{len(state.notifications)} notifications",
            "Notifier": "delivered",
        }
        return counts.get(name, "")

    def _print_summary(self, state: PipelineState):
        print()
        print("=" * 50)
        print("PIPELINE SUMMARY")
        print("=" * 50)
        print(f"Broken links discovered: {len(state.failures)}")
        print(f"Pages resolved:         {len(state.page_meta)}")
        print(f"Owners identified:      {len(state.owners)}")
        print(f"Notifications drafted:  {len(state.notifications)}")
        print()

        by_action = {}
        for n in state.notifications:
            action = n.action_taken.value
            by_action.setdefault(action, []).append(n)

        for action, notifications in by_action.items():
            print(f"{action}: {len(notifications)} notification(s)")
            for n in notifications:
                count = len(n.related_failures)
                print(f"   → {n.recipient.display_name}: {count} issue(s)")
            print()

        for n in state.notifications:
            print(n.to_console())

        print()
        print("AUDIT TRAIL")
        print("-" * 50)
        for entry in state.audit_log:
            conf = f" conf={entry.confidence:.2f}" if entry.confidence is not None else ""
            print(f"[{entry.timestamp}] {entry.agent_name}/{entry.action}: "
                  f"{entry.input_summary} → {entry.output_summary}{conf}")
