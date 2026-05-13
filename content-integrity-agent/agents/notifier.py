"""
NotifierAgent: Outputs notifications to console (mock email delivery).
"""

from agents.base import BaseAgent
from models.schemas import PipelineState


class NotifierAgent(BaseAgent):
    """Prints notifications to console as mock email delivery."""

    def __init__(self, dry_run: bool = True, verbose: bool = True):
        super().__init__("Notifier", verbose)
        self.dry_run = dry_run

    def run(self, state: PipelineState) -> PipelineState:
        for idx, notification in enumerate(state.notifications, start=1):
            if self.dry_run:
                print(f"[DRY RUN - Email #{idx}]")
            print(notification.to_console())
            state.log(
                agent_name=self.name,
                action="notify",
                input_summary=f"Notification #{idx} for {notification.recipient.email}",
                output_summary=f"Printed notification ({notification.action_taken.value})",
            )
        return state