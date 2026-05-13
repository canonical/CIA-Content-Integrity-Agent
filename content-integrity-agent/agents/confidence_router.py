"""
RouterAgent: Makes agentic routing decisions per failure and batches by owner.
"""

from typing import List, Tuple

from agents.base import BaseAgent
from models.schemas import (
    PipelineState, LinkFailure, FailureSeverity, RouterAction,
    FixSuggestion, Notification, Owner, PageMeta,
)
from services.http_client import HTTPClient


class RouterAgent(BaseAgent):
    """Makes agentic routing decisions per failure."""

    def __init__(self, verbose: bool = True):
        super().__init__("Router", verbose)

    def run(self, state: PipelineState) -> PipelineState:
        decisions: List[Tuple[LinkFailure, RouterAction, str]] = []

        for failure in state.failures:
            action, reason = self._decide(failure, state)
            decisions.append((failure, action, reason))

        owner_groups: dict[str, List[Tuple[LinkFailure, RouterAction]]] = {}
        for failure, action, reason in decisions:
            owner_email = self._get_owner_email(failure, state)
            key = owner_email or "__no_owner__"
            owner_groups.setdefault(key, []).append((failure, action))

        for key, items in owner_groups.items():
            if key == "__no_owner__":
                recipient = Owner(
                    email="ops@canonical.com",
                    display_name="Operations Team",
                    team="Operations",
                    department="Operations",
                )
            else:
                recipient = state.owners.get(key, Owner(
                    email=key, display_name=key, team="Unknown", department="Unknown",
                ))

            failures_for_owner = [f for f, _ in items]
            actions_for_owner = [a for _, a in items]

            dominant = self._dominant_action(actions_for_owner)

            suggestions_for_owner: List[FixSuggestion] = []
            for f in failures_for_owner:
                uid = f.unique_id()
                if uid in state.suggestions:
                    suggestions_for_owner.extend(state.suggestions[uid])

            subject = self._subject_line(dominant, len(failures_for_owner))
            body = self._build_body(recipient, failures_for_owner, suggestions_for_owner, state)

            notification = Notification(
                recipient=recipient,
                subject=subject,
                body=body,
                email_preview=subject,
                action_taken=dominant,
                related_failures=failures_for_owner,
                suggestions=suggestions_for_owner,
            )
            state.notifications.append(notification)

        for failure, action, reason in decisions:
            state.log(
                self.name, action.value,
                f"failure={failure.unique_id()}",
                reason,
            )

        return state

    def _decide(self, failure: LinkFailure, state: PipelineState) -> Tuple[RouterAction, str]:
        # 1. Self-validation: re-check broken link if timeout
        if failure.severity == FailureSeverity.TIMEOUT:
            try:
                if HTTPClient().is_link_alive(failure.broken_url):
                    return (RouterAction.SUPPRESS_FALSE_ALARM,
                            "Link is now alive - transient timeout")
            except Exception:
                pass

        owner_email = self._get_owner_email(failure, state)

        if not owner_email:
            return (RouterAction.ESCALATE_OPS, "No copydoc or owner found")

        if failure.severity == FailureSeverity.REDIRECT_CHAIN:
            return (RouterAction.NOTIFY_INVESTIGATE, "Redirect chains require human review")

        suggestions = state.suggestions.get(failure.unique_id(), [])
        if not suggestions:
            return (RouterAction.NOTIFY_INVESTIGATE, "No fix suggestions generated")

        top = suggestions[0]
        if top.confidence >= 0.90 and top.suggested_url:
            return (RouterAction.AUTO_FIX, f"High confidence ({top.confidence:.2f}) replacement found")
        elif top.confidence >= 0.60 and top.suggested_url:
            return (RouterAction.NOTIFY_WITH_SUGGESTION, f"Moderate confidence ({top.confidence:.2f})")
        else:
            return (RouterAction.NOTIFY_INVESTIGATE, f"Low confidence ({top.confidence:.2f}) - needs human review")

    def _get_owner_email(self, failure: LinkFailure, state: PipelineState) -> str | None:
        meta = state.page_meta.get(failure.source_page)
        if meta and meta.page_owner_email:
            return meta.page_owner_email
        return None

    def _dominant_action(self, actions: List[RouterAction]) -> RouterAction:
        if all(a == RouterAction.AUTO_FIX for a in actions):
            return RouterAction.AUTO_FIX
        if any(a in (RouterAction.AUTO_FIX, RouterAction.NOTIFY_WITH_SUGGESTION) for a in actions):
            return RouterAction.NOTIFY_WITH_SUGGESTION
        if any(a == RouterAction.NOTIFY_INVESTIGATE for a in actions):
            return RouterAction.NOTIFY_INVESTIGATE
        if all(a == RouterAction.SUPPRESS_FALSE_ALARM for a in actions):
            return RouterAction.SUPPRESS_FALSE_ALARM
        return RouterAction.ESCALATE_OPS

    def _subject_line(self, action: RouterAction, count: int) -> str:
        if action == RouterAction.AUTO_FIX:
            return f"Auto-fix available for {count} broken link(s) on your page(s)"
        elif action == RouterAction.NOTIFY_WITH_SUGGESTION:
            return f"Broken link suggestions ready — {count} issue(s) to review"
        elif action == RouterAction.NOTIFY_INVESTIGATE:
            return f"Content health check: {count} issue(s) need your attention"
        elif action == RouterAction.ESCALATE_OPS:
            return f"Escalated: {count} content issue(s) on canonical.com"
        return f"Content integrity: {count} issue(s)"

    def _build_body(
        self, recipient: Owner, failures: List[LinkFailure],
        suggestions: List[FixSuggestion], state: PipelineState,
    ) -> str:
        suggestion_map: dict[str, str | None] = {}
        for s in suggestions:
            suggestion_map[s.original_url] = s.suggested_url

        lines = [f"Hi {recipient.display_name},", ""]
        lines.append("Our Content Integrity Agent scanned canonical.com and found issues on pages you own:")
        lines.append("")

        for f in failures:
            suggested_url = suggestion_map.get(f.broken_url)
            lines.append(f"• **{f.broken_url}** on `{f.source_page}`")
            lines.append(f"  → Status: {f.error_message}")
            if suggested_url:
                lines.append(f"  → 💡 Suggestion: Did you mean `{suggested_url}`?")
            lines.append("")

        copydoc_urls = []
        for f in failures:
            meta = state.page_meta.get(f.source_page)
            if meta and meta.copydoc_url:
                copydoc_urls.append(meta.copydoc_url)
        copydoc_urls = list(dict.fromkeys(copydoc_urls))

        if copydoc_urls:
            lines.append("You can update the content via your copydoc(s):")
            for url in copydoc_urls:
                lines.append(url)
        else:
            lines.append("You can update the content via your copydoc(s):")
            lines.append("(no copydoc URL found)")

        lines.append("")
        lines.append("— Content Integrity Agent 🤖")

        return "\n".join(lines)
