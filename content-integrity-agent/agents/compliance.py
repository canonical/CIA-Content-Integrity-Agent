"""
ComplianceAgent: Checks page content against UX standards and style guides.
"""

import os

from agents.base import BaseAgent
from models.schemas import ComplianceFinding, PipelineState
from utils.html_parser import extract_visible_text


class ComplianceAgent(BaseAgent):
    """Checks page content against Google Doc standards via LLM analysis."""

    def __init__(self, doc_fetcher, llm_client, page_url: str,
                 fixture_path: str, standard_doc_ids: dict, verbose: bool = True):
        super().__init__("Compliance", verbose)
        self.doc_fetcher = doc_fetcher
        self.llm = llm_client
        self.page_url = page_url
        self.fixture_path = fixture_path
        self.standard_doc_ids = standard_doc_ids

    def run(self, state: PipelineState) -> PipelineState:
        try:
            page_text = self._load_page_text()
            if not page_text:
                self.log(f"No content found for {self.page_url}")
                state.log(self.name, "SKIP", f"url={self.page_url}", "no content")
                return state

            all_findings = []
            for standard_name, doc_id in self.standard_doc_ids.items():
                try:
                    standards_text = self.doc_fetcher.get_document_text(doc_id)
                    if not standards_text:
                        self.log(f"Could not fetch standard: {standard_name}")
                        continue

                    raw_findings = self.llm.check_compliance(
                        page_text, standards_text, standard_name
                    )
                    for f in raw_findings:
                        all_findings.append(ComplianceFinding(
                            rule=f["rule"],
                            severity=f["severity"],
                            location=f["location"],
                            explanation=f["explanation"],
                            standard_source=f["standard_source"],
                        ))
                except Exception as exc:
                    self.log(f"Error checking {standard_name}: {exc}")
                    state.log(
                        self.name, "error",
                        f"standard={standard_name}",
                        str(exc),
                    )

            state.compliance_findings[self.page_url] = all_findings

            errors = sum(1 for f in all_findings if f.severity == "error")
            warnings = sum(1 for f in all_findings if f.severity == "warning")
            self.log(
                f"Compliance check complete for {self.page_url}: "
                f"{errors} error(s), {warnings} warning(s)"
            )
            state.log(
                self.name, "CHECK",
                f"url={self.page_url}",
                f"findings={len(all_findings)} errors={errors} warnings={warnings}",
            )
        except Exception as exc:
            self.log(f"Compliance check failed: {exc}")
            state.log(self.name, "FAILED", f"url={self.page_url}", str(exc))

        return state

    def _load_page_text(self) -> str:
        if os.path.exists(self.fixture_path):
            with open(self.fixture_path, "r") as f:
                html = f.read()
            return extract_visible_text(html)
        return ""
