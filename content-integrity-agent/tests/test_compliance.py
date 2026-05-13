import os
import tempfile
import pytest
from unittest.mock import MagicMock
from agents.compliance import ComplianceAgent
from models.schemas import PipelineState, ComplianceFinding


def _make_html(text="Hello world"):
    return f"<html><head><title>Test</title></head><body><p>{text}</p></body></html>"


def _make_state():
    return PipelineState()


def test_compliance_agent_returns_state():
    doc_fetcher = MagicMock()
    doc_fetcher.get_document_text.return_value = "Use sentence case."
    llm = MagicMock()
    llm.check_compliance.return_value = []

    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        f.write(_make_html())
        fixture_path = f.name

    try:
        agent = ComplianceAgent(
            doc_fetcher=doc_fetcher,
            llm_client=llm,
            page_url="https://canonical.com/data",
            fixture_path=fixture_path,
            standard_doc_ids={"UX Standards": "doc123"},
            verbose=False,
        )
        result = agent.run(_make_state())
        assert isinstance(result, PipelineState)
    finally:
        os.unlink(fixture_path)


def test_compliance_agent_populates_findings():
    doc_fetcher = MagicMock()
    doc_fetcher.get_document_text.return_value = "Use sentence case."
    llm = MagicMock()
    llm.check_compliance.return_value = [
        {
            "rule": "Headings must use sentence case",
            "severity": "error",
            "location": "H1: 'Get Started'",
            "explanation": "Title case detected",
            "standard_source": "UX Standards",
        }
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        f.write(_make_html())
        fixture_path = f.name

    try:
        agent = ComplianceAgent(
            doc_fetcher=doc_fetcher,
            llm_client=llm,
            page_url="https://canonical.com/data",
            fixture_path=fixture_path,
            standard_doc_ids={"UX Standards": "doc123"},
            verbose=False,
        )
        result = agent.run(_make_state())

        assert "https://canonical.com/data" in result.compliance_findings
        findings = result.compliance_findings["https://canonical.com/data"]
        assert len(findings) == 1
        assert findings[0].rule == "Headings must use sentence case"
        assert findings[0].severity == "error"
        assert findings[0].standard_source == "UX Standards"
    finally:
        os.unlink(fixture_path)


def test_compliance_agent_checks_multiple_standards():
    doc_fetcher = MagicMock()
    doc_fetcher.get_document_text.return_value = "Standard text."
    llm = MagicMock()
    llm.check_compliance.return_value = [
        {
            "rule": "rule1", "severity": "warning",
            "location": "loc1", "explanation": "exp1",
            "standard_source": "UX Standards",
        }
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        f.write(_make_html())
        fixture_path = f.name

    try:
        agent = ComplianceAgent(
            doc_fetcher=doc_fetcher,
            llm_client=llm,
            page_url="https://canonical.com/data",
            fixture_path=fixture_path,
            standard_doc_ids={
                "UX Standards": "doc1",
                "Copy Style Guide": "doc2",
            },
            verbose=False,
        )
        result = agent.run(_make_state())

        assert llm.check_compliance.call_count == 2
        findings = result.compliance_findings["https://canonical.com/data"]
        assert len(findings) == 2
    finally:
        os.unlink(fixture_path)


def test_compliance_agent_no_fixture():
    doc_fetcher = MagicMock()
    llm = MagicMock()

    agent = ComplianceAgent(
        doc_fetcher=doc_fetcher,
        llm_client=llm,
        page_url="https://canonical.com/nonexistent",
        fixture_path="/tmp/does_not_exist.html",
        standard_doc_ids={"UX Standards": "doc123"},
        verbose=False,
    )
    result = agent.run(_make_state())

    assert llm.check_compliance.call_count == 0
    assert "https://canonical.com/nonexistent" not in result.compliance_findings


def test_compliance_agent_handles_llm_exception():
    doc_fetcher = MagicMock()
    doc_fetcher.get_document_text.return_value = "Standard text."
    llm = MagicMock()
    llm.check_compliance.side_effect = Exception("API down")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        f.write(_make_html())
        fixture_path = f.name

    try:
        agent = ComplianceAgent(
            doc_fetcher=doc_fetcher,
            llm_client=llm,
            page_url="https://canonical.com/data",
            fixture_path=fixture_path,
            standard_doc_ids={"UX Standards": "doc123"},
            verbose=False,
        )
        result = agent.run(_make_state())
        assert isinstance(result, PipelineState)
    finally:
        os.unlink(fixture_path)


def test_compliance_agent_logs_audit():
    doc_fetcher = MagicMock()
    doc_fetcher.get_document_text.return_value = "Standard text."
    llm = MagicMock()
    llm.check_compliance.return_value = []

    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        f.write(_make_html())
        fixture_path = f.name

    try:
        agent = ComplianceAgent(
            doc_fetcher=doc_fetcher,
            llm_client=llm,
            page_url="https://canonical.com/data",
            fixture_path=fixture_path,
            standard_doc_ids={"UX Standards": "doc123"},
            verbose=False,
        )
        result = agent.run(_make_state())
        assert len(result.audit_log) > 0
        assert any("Compliance" in entry.agent_name for entry in result.audit_log)
    finally:
        os.unlink(fixture_path)


def test_compliance_agent_handles_doc_fetcher_failure():
    doc_fetcher = MagicMock()
    doc_fetcher.get_document_text.return_value = ""
    llm = MagicMock()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        f.write(_make_html())
        fixture_path = f.name

    try:
        agent = ComplianceAgent(
            doc_fetcher=doc_fetcher,
            llm_client=llm,
            page_url="https://canonical.com/data",
            fixture_path=fixture_path,
            standard_doc_ids={"UX Standards": "doc123"},
            verbose=False,
        )
        result = agent.run(_make_state())
        assert llm.check_compliance.call_count == 0
    finally:
        os.unlink(fixture_path)
