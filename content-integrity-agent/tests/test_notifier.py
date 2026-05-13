import pytest
from agents.notifier import NotifierAgent
from models.schemas import (
    PipelineState, Notification, Owner, RouterAction,
)


def _notification():
    owner = Owner(email="alice@canonical.com", display_name="Alice", team="Eng", department="Eng")
    return Notification(
        recipient=owner,
        subject="Test subject",
        body="Test body",
        email_preview="test preview",
        action_taken=RouterAction.NOTIFY_WITH_SUGGESTION,
    )


def test_notifier_returns_state():
    agent = NotifierAgent(dry_run=True, verbose=False)
    result = agent.run(PipelineState())
    assert isinstance(result, PipelineState)


def test_notifier_prints_dry_run_prefix(capsys):
    state = PipelineState()
    state.notifications = [_notification()]
    agent = NotifierAgent(dry_run=True, verbose=False)
    agent.run(state)
    captured = capsys.readouterr()
    assert "DRY RUN" in captured.out


def test_notifier_no_dry_run_prefix_when_not_dry(capsys):
    state = PipelineState()
    state.notifications = [_notification()]
    agent = NotifierAgent(dry_run=False, verbose=False)
    agent.run(state)
    captured = capsys.readouterr()
    assert "DRY RUN" not in captured.out


def test_notifier_prints_notification_content(capsys):
    state = PipelineState()
    state.notifications = [_notification()]
    agent = NotifierAgent(dry_run=True, verbose=False)
    agent.run(state)
    captured = capsys.readouterr()
    assert "Alice" in captured.out
    assert "Test subject" in captured.out


def test_notifier_logs_audit():
    state = PipelineState()
    state.notifications = [_notification()]
    agent = NotifierAgent(dry_run=True, verbose=False)
    result = agent.run(state)
    assert len(result.audit_log) > 0
    assert any("Notifier" in entry.agent_name for entry in result.audit_log)


def test_notifier_handles_empty_notifications(capsys):
    agent = NotifierAgent(dry_run=True, verbose=False)
    result = agent.run(PipelineState())
    assert len(result.notifications) == 0
