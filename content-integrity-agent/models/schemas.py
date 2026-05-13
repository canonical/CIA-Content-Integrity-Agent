"""
Core data structures for the Content Integrity Agent.
All agents communicate via these shared types.
FROZEN after hour 0 — modifications require Engineer A approval.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime


class FailureSeverity(str, Enum):
    """Classification of broken link severity."""
    CRITICAL_404 = "critical_404"
    TIMEOUT = "timeout"
    REDIRECT_CHAIN = "redirect_chain"
    SOFT_404 = "soft_404"
    UNKNOWN = "unknown"


class RouterAction(str, Enum):
    """Decision the agentic router makes for each failure."""
    AUTO_FIX = "auto_fix"
    NOTIFY_WITH_SUGGESTION = "notify_with_suggestion"
    NOTIFY_INVESTIGATE = "notify_investigate"
    ESCALATE_OPS = "escalate_ops"
    SUPPRESS_FALSE_ALARM = "suppress_false_alarm"


@dataclass
class LinkFailure:
    """A single broken link found by linkchecker."""
    source_page: str
    broken_url: str
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    severity: FailureSeverity = FailureSeverity.UNKNOWN
    line_number: Optional[int] = None

    def unique_id(self) -> str:
        return f"{self.source_page}::{self.broken_url}"


@dataclass
class PageMeta:
    """Metadata extracted from a web page's <head>."""
    url: str
    copydoc_url: Optional[str] = None
    title: Optional[str] = None
    page_owner_email: Optional[str] = None
    last_modified: Optional[str] = None


@dataclass
class Owner:
    """A content owner resolved from the Directory API."""
    email: str
    display_name: str
    team: str
    department: str
    mattermost_username: Optional[str] = None


@dataclass
class FixSuggestion:
    """LLM-generated fix suggestion for a broken link."""
    original_url: str
    suggested_url: Optional[str] = None
    suggestion_text: str = ""
    confidence: float = 0.0
    reasoning: str = ""


@dataclass
class AgentAuditLog:
    """Immutable log of every agent decision."""
    timestamp: str
    agent_name: str
    action: str
    input_summary: str
    output_summary: str
    confidence: Optional[float] = None


@dataclass
class Notification:
    """Final output to the owner (or ops team)."""
    recipient: Owner
    subject: str
    body: str
    email_preview: str
    action_taken: RouterAction
    related_failures: List[LinkFailure] = field(default_factory=list)
    suggestions: List[FixSuggestion] = field(default_factory=list)
    audit_log: List[AgentAuditLog] = field(default_factory=list)

    def to_console(self) -> str:
        lines = [
            "─" * 50,
            f"📧 NOTIFICATION ({self.action_taken.value})",
            f"   To: {self.recipient.display_name} <{self.recipient.email}>",
            f"   Subject: {self.subject}",
            "",
            "   " + self.body.replace("\n", "\n   "),
            "─" * 50,
        ]
        return "\n".join(lines)


@dataclass
class PipelineState:
    """Shared mutable state passed between agents in the orchestrator."""
    failures: List[LinkFailure] = field(default_factory=list)
    page_meta: Dict[str, PageMeta] = field(default_factory=dict)
    owners: Dict[str, Owner] = field(default_factory=dict)
    suggestions: Dict[str, List[FixSuggestion]] = field(default_factory=dict)
    notifications: List[Notification] = field(default_factory=list)
    audit_log: List[AgentAuditLog] = field(default_factory=list)

    def log(self, agent_name: str, action: str, input_summary: str,
            output_summary: str, confidence: Optional[float] = None):
        self.audit_log.append(AgentAuditLog(
            timestamp=datetime.utcnow().isoformat() + "Z",
            agent_name=agent_name,
            action=action,
            input_summary=input_summary,
            output_summary=output_summary,
            confidence=confidence,
        ))