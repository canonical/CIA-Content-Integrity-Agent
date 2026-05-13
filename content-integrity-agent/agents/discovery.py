"""
DiscoveryAgent: Parses linkchecker output into structured LinkFailure objects.
"""

import os
import re

from agents.base import BaseAgent
from models.schemas import PipelineState, LinkFailure, FailureSeverity


class DiscoveryAgent(BaseAgent):
    """Parses linkchecker console output into structured failures."""

    def __init__(self, input_path: str, verbose: bool = True):
        super().__init__("Discovery", verbose)
        self.input_path = input_path

    def _resolve_path(self) -> str:
        if os.path.isfile(self.input_path):
            return self.input_path
        alt = os.path.join("content-integrity-agent", self.input_path)
        if os.path.isfile(alt):
            return alt
        return self.input_path

    def _parse(self, text: str):
        failures = []
        blocks = text.strip().split("\n\n")
        for block in blocks:
            url_match = re.search(r"URL\s+(.*)", block)
            parent_match = re.search(r"Parent URL\s+([^,]+)(?:,\s*line\s+(\d+))?", block)
            error_match = re.search(r"Error\s+(.*)", block)
            if not url_match or not parent_match:
                continue
            source_page = parent_match.group(1).strip()
            line_raw = parent_match.group(2)
            line_number = int(line_raw) if line_raw else None
            error_message = error_match.group(1).strip() if error_match else None
            status_code = None
            if error_message:
                code_match = re.search(r"(\d{3})", error_message)
                if code_match:
                    status_code = int(code_match.group(1))
            severity = FailureSeverity.UNKNOWN
            if error_message:
                lower = error_message.lower()
                if "404" in lower:
                    severity = FailureSeverity.CRITICAL_404
                elif "timeout" in lower or "connection" in lower:
                    severity = FailureSeverity.TIMEOUT
                elif "redirect" in lower:
                    severity = FailureSeverity.REDIRECT_CHAIN
            failures.append(LinkFailure(
                source_page=source_page,
                broken_url=url_match.group(1).strip(),
                status_code=status_code,
                error_message=error_message,
                severity=severity,
                line_number=line_number,
            ))
        return failures

    def run(self, state: PipelineState) -> PipelineState:
        path = self._resolve_path()
        with open(path, "r") as fh:
            text = fh.read()
        state.failures = self._parse(text)
        self.log(f"Parsed {len(state.failures)} link failures from {path}")
        state.log("Discovery", "PARSE", f"file={self.input_path}", f"count={len(state.failures)}")
        return state
