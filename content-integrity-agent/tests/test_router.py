import pytest
from unittest.mock import patch
from agents.confidence_router import RouterAgent
from models.schemas import (
    PipelineState, LinkFailure, PageMeta, Owner, FixSuggestion,
    FailureSeverity, RouterAction,
)


def _owner(email="alice.chen@canonical.com"):
    return Owner(email=email, display_name="Alice Chen", team="Eng", department="Eng")


def _failure(broken="https://canonical.com/old-data-docs",
             source="https://canonical.com/data",
             severity=FailureSeverity.CRITICAL_404):
    return LinkFailure(
        source_page=source, broken_url=broken,
        status_code=404, error_message="404 Not Found",
        severity=severity, line_number=42,
    )


def _state_with(failures=None, suggestions=None, owners=None, page_meta=None):
    s = PipelineState()
    if failures:
        s.failures = failures
    if suggestions:
        s.suggestions = suggestions
    if owners:
        s.owners = owners
    if page_meta:
        s.page_meta = page_meta
    return s


def test_router_returns_state():
    agent = RouterAgent(verbose=False)
    result = agent.run(PipelineState())
    assert isinstance(result, PipelineState)


def test_router_creates_notification_for_high_confidence():
    f = _failure()
    owner = _owner()
    suggestion = FixSuggestion(
        original_url=f.broken_url,
        suggested_url="https://canonical.com/data/docs",
        confidence=0.95, reasoning="test", suggestion_text="try this",
    )
    state = _state_with(
        failures=[f],
        suggestions={f.unique_id(): [suggestion]},
        owners={owner.email: owner},
        page_meta={f.source_page: PageMeta(url=f.source_page, page_owner_email=owner.email)},
    )
    agent = RouterAgent(verbose=False)
    result = agent.run(state)
    assert len(result.notifications) >= 1


def test_router_auto_fix_action():
    f = _failure()
    owner = _owner()
    suggestion = FixSuggestion(
        original_url=f.broken_url,
        suggested_url="https://canonical.com/data/docs",
        confidence=0.95, reasoning="test", suggestion_text="try",
    )
    state = _state_with(
        failures=[f],
        suggestions={f.unique_id(): [suggestion]},
        owners={owner.email: owner},
        page_meta={f.source_page: PageMeta(url=f.source_page, page_owner_email=owner.email)},
    )
    agent = RouterAgent(verbose=False)
    result = agent.run(state)
    assert result.notifications[0].action_taken == RouterAction.AUTO_FIX


def test_router_notify_with_suggestion_for_medium_confidence():
    f = _failure()
    owner = _owner()
    suggestion = FixSuggestion(
        original_url=f.broken_url,
        suggested_url="https://canonical.com/data/docs",
        confidence=0.70, reasoning="test", suggestion_text="try",
    )
    state = _state_with(
        failures=[f],
        suggestions={f.unique_id(): [suggestion]},
        owners={owner.email: owner},
        page_meta={f.source_page: PageMeta(url=f.source_page, page_owner_email=owner.email)},
    )
    agent = RouterAgent(verbose=False)
    result = agent.run(state)
    assert result.notifications[0].action_taken == RouterAction.NOTIFY_WITH_SUGGESTION


def test_router_notify_investigate_for_low_confidence():
    f = _failure()
    owner = _owner()
    suggestion = FixSuggestion(
        original_url=f.broken_url,
        suggested_url=None,
        confidence=0.30, reasoning="test", suggestion_text="uncertain",
    )
    state = _state_with(
        failures=[f],
        suggestions={f.unique_id(): [suggestion]},
        owners={owner.email: owner},
        page_meta={f.source_page: PageMeta(url=f.source_page, page_owner_email=owner.email)},
    )
    agent = RouterAgent(verbose=False)
    result = agent.run(state)
    assert result.notifications[0].action_taken == RouterAction.NOTIFY_INVESTIGATE


def test_router_escalate_when_no_owner():
    f = _failure()
    state = _state_with(failures=[f], page_meta={})
    agent = RouterAgent(verbose=False)
    result = agent.run(state)
    assert len(result.notifications) >= 1
    assert result.notifications[0].action_taken == RouterAction.ESCALATE_OPS


def test_router_redirect_chain():
    f = _failure(severity=FailureSeverity.REDIRECT_CHAIN)
    owner = _owner()
    state = _state_with(
        failures=[f],
        suggestions={},
        owners={owner.email: owner},
        page_meta={f.source_page: PageMeta(url=f.source_page, page_owner_email=owner.email)},
    )
    agent = RouterAgent(verbose=False)
    result = agent.run(state)
    assert result.notifications[0].action_taken == RouterAction.NOTIFY_INVESTIGATE


def test_router_batches_by_owner():
    f1 = _failure(broken="https://canonical.com/old-data-docs", source="https://canonical.com/data")
    f2 = _failure(broken="https://canonical.com/deprecated-api/v1", source="https://canonical.com/kubernetes")
    owner = _owner()
    s1 = FixSuggestion(original_url=f1.broken_url, suggested_url="https://canonical.com/data/docs",
                       confidence=0.95, reasoning="test", suggestion_text="try")
    s2 = FixSuggestion(original_url=f2.broken_url, suggested_url="https://canonical.com/kubernetes/docs",
                       confidence=0.92, reasoning="test", suggestion_text="try")
    state = _state_with(
        failures=[f1, f2],
        suggestions={f1.unique_id(): [s1], f2.unique_id(): [s2]},
        owners={owner.email: owner},
        page_meta={
            f1.source_page: PageMeta(url=f1.source_page, page_owner_email=owner.email),
            f2.source_page: PageMeta(url=f2.source_page, page_owner_email=owner.email),
        },
    )
    agent = RouterAgent(verbose=False)
    result = agent.run(state)
    assert len(result.notifications) == 1
    assert len(result.notifications[0].related_failures) == 2


def test_router_logs_audit():
    f = _failure()
    owner = _owner()
    s = FixSuggestion(original_url=f.broken_url, suggested_url="https://canonical.com/data/docs",
                      confidence=0.95, reasoning="test", suggestion_text="try")
    state = _state_with(
        failures=[f],
        suggestions={f.unique_id(): [s]},
        owners={owner.email: owner},
        page_meta={f.source_page: PageMeta(url=f.source_page, page_owner_email=owner.email)},
    )
    agent = RouterAgent(verbose=False)
    result = agent.run(state)
    assert len(result.audit_log) > 0


def test_router_timeout_link_alive_suppressed():
    f = LinkFailure(
        source_page="https://canonical.com/data",
        broken_url="https://canonical.com/broken-timeout",
        severity=FailureSeverity.TIMEOUT,
        error_message="Connection timeout",
    )
    owner = _owner()
    state = _state_with(
        failures=[f],
        suggestions={},
        owners={owner.email: owner},
        page_meta={f.source_page: PageMeta(url=f.source_page, page_owner_email=owner.email)},
    )
    agent = RouterAgent(verbose=False)
    with patch("agents.confidence_router.HTTPClient") as mock_http:
        mock_http.return_value.is_link_alive.return_value = True
        result = agent.run(state)
    assert result.notifications[0].action_taken == RouterAction.SUPPRESS_FALSE_ALARM


def test_router_dominant_action_priority_mixed_batch():
    """When a batch has AUTO_FIX + NOTIFY_INVESTIGATE, dominant should be NOTIFY_WITH_SUGGESTION."""
    f1 = _failure(broken="https://canonical.com/old-data-docs", source="https://canonical.com/data")
    f2 = _failure(broken="https://canonical.com/deprecated-api/v1", source="https://canonical.com/kubernetes")
    owner = _owner()
    s1 = FixSuggestion(original_url=f1.broken_url, suggested_url="https://canonical.com/data/docs",
                       confidence=0.95, reasoning="test", suggestion_text="try")
    s2 = FixSuggestion(original_url=f2.broken_url, suggested_url=None,
                       confidence=0.30, reasoning="test", suggestion_text="uncertain")
    state = _state_with(
        failures=[f1, f2],
        suggestions={f1.unique_id(): [s1], f2.unique_id(): [s2]},
        owners={owner.email: owner},
        page_meta={
            f1.source_page: PageMeta(url=f1.source_page, page_owner_email=owner.email),
            f2.source_page: PageMeta(url=f2.source_page, page_owner_email=owner.email),
        },
    )
    agent = RouterAgent(verbose=False)
    result = agent.run(state)
    assert len(result.notifications) == 1
    # AUTO_FIX + NOTIFY_INVESTIGATE → NOTIFY_WITH_SUGGESTION per spec
    assert result.notifications[0].action_taken == RouterAction.NOTIFY_WITH_SUGGESTION
