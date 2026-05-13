import pytest
from datetime import datetime, timedelta, timezone
from agents.stubs import RedirectChainDetector, ContentDecayScorer, CrossPageConsistencyAgent
from models.schemas import (
    PipelineState, LinkFailure, PageMeta, FailureSeverity,
)


def _failure(broken="https://canonical.com/old-data-docs",
             source="https://canonical.com/data",
             severity=FailureSeverity.REDIRECT_CHAIN,
             error="Too many redirects"):
    return LinkFailure(
        source_page=source, broken_url=broken,
        severity=severity, error_message=error,
    )


def test_redirect_chain_detector_returns_state():
    agent = RedirectChainDetector(verbose=False)
    result = agent.run(PipelineState())
    assert isinstance(result, PipelineState)


def test_redirect_chain_detector_counts(capsys):
    state = PipelineState()
    state.failures = [
        _failure(severity=FailureSeverity.REDIRECT_CHAIN, error="Too many redirects"),
        _failure(broken="https://canonical.com/other", severity=FailureSeverity.REDIRECT_CHAIN, error="Redirect loop"),
        _failure(broken="https://canonical.com/404", severity=FailureSeverity.CRITICAL_404, error="404"),
    ]
    agent = RedirectChainDetector(verbose=False)
    agent.run(state)
    captured = capsys.readouterr()
    assert "2" in captured.out


def test_content_decay_scorer_returns_state():
    agent = ContentDecayScorer(verbose=False)
    result = agent.run(PipelineState())
    assert isinstance(result, PipelineState)


def test_content_decay_scorer_prints(capsys):
    state = PipelineState()
    old_date = (datetime.now(timezone.utc) - timedelta(days=365)).isoformat()
    state.page_meta = {
        "https://canonical.com/data": PageMeta(
            url="https://canonical.com/data",
            last_modified=old_date,
        ),
    }
    agent = ContentDecayScorer(verbose=False)
    agent.run(state)
    captured = capsys.readouterr()
    assert "decay" in captured.out.lower() or "STUB" in captured.out


def test_cross_page_consistency_returns_state():
    agent = CrossPageConsistencyAgent(verbose=False)
    result = agent.run(PipelineState())
    assert isinstance(result, PipelineState)


def test_cross_page_consistency_detects_duplicates(capsys):
    state = PipelineState()
    state.failures = [
        _failure(broken="https://canonical.com/shared-broken", source="https://canonical.com/page1"),
        _failure(broken="https://canonical.com/shared-broken", source="https://canonical.com/page2"),
        _failure(broken="https://canonical.com/unique", source="https://canonical.com/page1"),
    ]
    agent = CrossPageConsistencyAgent(verbose=False)
    agent.run(state)
    captured = capsys.readouterr()
    assert "2" in captured.out
