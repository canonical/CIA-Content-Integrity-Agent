#!/usr/bin/env python3
"""
Full pipeline test using inline mock agents.
This lets us verify the orchestrator, CLI wiring, and all shared infrastructure
works end-to-end WITHOUT touching Engineer B or C's files.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base import BaseAgent
from agents.orchestrator import OrchestratorAgent
from models.schemas import (
    PipelineState, LinkFailure, PageMeta, Owner, FixSuggestion,
    Notification, FailureSeverity, RouterAction,
)
from utils.html_parser import extract_page_meta


FIXTURE_PAGES = {
    "https://canonical.com/data": "fixtures/pages/data.html",
    "https://canonical.com/kubernetes": "fixtures/pages/kubernetes.html",
    "https://canonical.com/microk8s": "fixtures/pages/microk8s.html",
    "https://canonical.com/openstack": "fixtures/pages/openstack.html",
}

SITEMAP_URLS = {
    "https://canonical.com/data",
    "https://canonical.com/data/docs",
    "https://canonical.com/kubernetes",
    "https://canonical.com/kubernetes/docs",
    "https://canonical.com/microk8s",
    "https://canonical.com/microk8s/docs",
    "https://canonical.com/openstack",
    "https://canonical.com/openstack/pricing",
}


def _load_copydoc(doc_url: str) -> dict:
    match = re.search(r"/d/([^/]+)/", doc_url)
    if not match:
        return None
    doc_id = match.group(1)
    for fname in os.listdir("fixtures/copydocs"):
        if fname.startswith("doc_") and doc_id.startswith(fname[4:-5]):
            with open(os.path.join("fixtures/copydocs", fname)) as f:
                return json.load(f)
    return None


def _load_directory() -> dict:
    with open("fixtures/directory.json") as f:
        data = json.load(f)
    return {u["email"]: u for u in data["users"]}


class MockDiscoveryAgent(BaseAgent):
    def __init__(self, input_path: str, verbose: bool = True):
        super().__init__("Discovery", verbose)
        self.input_path = input_path

    def run(self, state: PipelineState) -> PipelineState:
        with open(self.input_path) as f:
            text = f.read()
        blocks = re.split(r"\n\s*\n", text.strip())
        failures = []
        for block in blocks:
            url_m = re.search(r"URL\s+(.*)", block)
            parent_m = re.search(r"Parent URL\s+([^,]+)(?:,\s*line\s+(\d+))?", block)
            error_m = re.search(r"Error\s+(.*)", block)
            if not (url_m and parent_m and error_m):
                continue
            broken_url = url_m.group(1).strip()
            source_page = parent_m.group(1).strip()
            line_number = int(parent_m.group(2)) if parent_m.group(2) else None
            error_message = error_m.group(1).strip()
            status_match = re.search(r"\b(\d{3})\b", error_message)
            status_code = int(status_match.group(1)) if status_match else None
            if "404" in error_message:
                severity = FailureSeverity.CRITICAL_404
            elif "timeout" in error_message.lower() or "connection" in error_message.lower():
                severity = FailureSeverity.TIMEOUT
            elif "redirect" in error_message.lower():
                severity = FailureSeverity.REDIRECT_CHAIN
            else:
                severity = FailureSeverity.UNKNOWN
            failures.append(LinkFailure(
                source_page=source_page, broken_url=broken_url,
                status_code=status_code, error_message=error_message,
                severity=severity, line_number=line_number,
            ))
        state.failures = failures
        state.log("Discovery", "PARSE_LINKCHECKER", f"file={self.input_path}", f"count={len(failures)}")
        self.log(f"Parsed {len(failures)} broken links")
        return state


class MockResolverAgent(BaseAgent):
    def __init__(self, verbose: bool = True):
        super().__init__("Resolver", verbose)

    def run(self, state: PipelineState) -> PipelineState:
        source_urls = {f.source_page for f in state.failures}
        for url in source_urls:
            fixture_path = FIXTURE_PAGES.get(url)
            if fixture_path and os.path.exists(fixture_path):
                with open(fixture_path) as f:
                    html = f.read()
                meta = extract_page_meta(html)
                state.page_meta[url] = PageMeta(
                    url=url, copydoc_url=meta["copydoc_url"], title=meta["title"],
                )
            else:
                state.page_meta[url] = PageMeta(url=url)
        state.log("Resolver", "RESOLVE_PAGES", f"urls={len(source_urls)}", f"resolved={len(state.page_meta)}")
        self.log(f"Resolved {len(state.page_meta)} pages")
        return state


class MockOwnerResolverAgent(BaseAgent):
    def __init__(self, verbose: bool = True):
        super().__init__("OwnerResolver", verbose)
        self._directory = _load_directory()

    def run(self, state: PipelineState) -> PipelineState:
        for url, pm in state.page_meta.items():
            if not pm.copydoc_url:
                pm.page_owner_email = "ops-team@canonical.com"
                continue
            doc = _load_copydoc(pm.copydoc_url)
            if not doc:
                pm.page_owner_email = "ops-team@canonical.com"
                continue
            owner_email = doc.get("owner_email", "ops-team@canonical.com")
            pm.page_owner_email = owner_email
            user = self._directory.get(owner_email)
            if user:
                state.owners[owner_email] = Owner(
                    email=user["email"], display_name=user["display_name"],
                    team=user["team"], department=user["department"],
                    mattermost_username=user.get("mattermost_username"),
                )
            else:
                state.owners.setdefault("ops-team@canonical.com", Owner(
                    email="ops-team@canonical.com", display_name="Content Ops Team",
                    team="Web Operations", department="Marketing",
                    mattermost_username="content-ops",
                ))
        state.log("OwnerResolver", "RESOLVE_OWNERS", f"pages={len(state.page_meta)}", f"owners={len(state.owners)}")
        self.log(f"Resolved {len(state.owners)} owners")
        return state


def _jaccard(a: str, b: str) -> float:
    sa = set(a.strip("/").split("/"))
    sb = set(b.strip("/").split("/"))
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


class MockSuggestionAgent(BaseAgent):
    def __init__(self, verbose: bool = True):
        super().__init__("Suggestion", verbose)

    def run(self, state: PipelineState) -> PipelineState:
        for failure in state.failures:
            scored = []
            for candidate in SITEMAP_URLS:
                score = _jaccard(failure.broken_url, candidate)
                if score > 0.1:
                    scored.append((score, candidate))
            scored.sort(reverse=True)
            best_score, best_url = scored[0] if scored else (0.0, None)
            confidence = min(best_score * 0.5, 0.5)
            suggestion = FixSuggestion(
                original_url=failure.broken_url,
                suggested_url=best_url if best_score > 0.1 else None,
                confidence=confidence,
                reasoning=f"Jaccard similarity={best_score:.2f} with {best_url}",
                suggestion_text="Fallback suggestion based on URL similarity" if best_url else "No similar URL found",
            )
            state.suggestions[failure.unique_id()] = [suggestion]
        state.log("Suggestion", "GENERATE_SUGGESTIONS", f"failures={len(state.failures)}", f"suggestions={len(state.suggestions)}")
        self.log(f"Generated {len(state.suggestions)} suggestions")
        return state


class MockRouterAgent(BaseAgent):
    def __init__(self, verbose: bool = True):
        super().__init__("Router", verbose)

    def run(self, state: PipelineState) -> PipelineState:
        decisions = {}
        for failure in state.failures:
            pm = state.page_meta.get(failure.source_page)
            owner_email = pm.page_owner_email if pm else None
            if not owner_email:
                decisions[failure.unique_id()] = (RouterAction.ESCALATE_OPS, "No owner found")
                continue
            if failure.severity == FailureSeverity.REDIRECT_CHAIN:
                decisions[failure.unique_id()] = (RouterAction.NOTIFY_INVESTIGATE, "Redirect chains require human review")
                continue
            suggestions = state.suggestions.get(failure.unique_id(), [])
            if not suggestions:
                decisions[failure.unique_id()] = (RouterAction.NOTIFY_INVESTIGATE, "No fix suggestions")
                continue
            top = suggestions[0]
            if top.confidence >= 0.90 and top.suggested_url:
                decisions[failure.unique_id()] = (RouterAction.AUTO_FIX, f"High confidence ({top.confidence:.2f})")
            elif top.confidence >= 0.60 and top.suggested_url:
                decisions[failure.unique_id()] = (RouterAction.NOTIFY_WITH_SUGGESTION, f"Moderate confidence ({top.confidence:.2f})")
            else:
                decisions[failure.unique_id()] = (RouterAction.NOTIFY_INVESTIGATE, f"Low confidence ({top.confidence:.2f})")

        by_owner = {}
        for failure in state.failures:
            pm = state.page_meta.get(failure.source_page)
            owner_email = pm.page_owner_email if pm else "ops-team@canonical.com"
            by_owner.setdefault(owner_email, []).append(failure)

        for owner_email, failures in by_owner.items():
            owner = state.owners.get(owner_email, Owner(
                email="ops-team@canonical.com", display_name="Content Ops Team",
                team="Web Operations", department="Marketing",
                mattermost_username="content-ops",
            ))
            actions = {decisions[f.unique_id()][0] for f in failures}
            if RouterAction.AUTO_FIX in actions:
                dominant = RouterAction.AUTO_FIX
            elif RouterAction.NOTIFY_WITH_SUGGESTION in actions:
                dominant = RouterAction.NOTIFY_WITH_SUGGESTION
            elif RouterAction.NOTIFY_INVESTIGATE in actions:
                dominant = RouterAction.NOTIFY_INVESTIGATE
            else:
                dominant = RouterAction.ESCALATE_OPS

            subject_map = {
                RouterAction.AUTO_FIX: f"Auto-fix available for {len(failures)} broken link(s)",
                RouterAction.NOTIFY_WITH_SUGGESTION: f"Broken link suggestions ready — {len(failures)} issue(s)",
                RouterAction.NOTIFY_INVESTIGATE: f"Content health check: {len(failures)} issue(s) need attention",
                RouterAction.ESCALATE_OPS: f"Escalated: {len(failures)} content issue(s)",
            }

            related_suggestions = []
            for f in failures:
                related_suggestions.extend(state.suggestions.get(f.unique_id(), []))

            body_lines = [f"Hi {owner.display_name},", ""]
            body_lines.append("Our Content Integrity Agent found issues on pages you own:")
            body_lines.append("")
            for f in failures:
                s = state.suggestions.get(f.unique_id(), [None])[0]
                sug = f" → Suggestion: {s.suggested_url}" if s and s.suggested_url else ""
                body_lines.append(f"  • {f.broken_url} on {f.source_page}{sug}")
            body_lines.append("")
            copydoc_urls = [state.page_meta[f.source_page].copydoc_url for f in failures if state.page_meta.get(f.source_page)]
            if copydoc_urls:
                body_lines.append("You can update the content via your copydoc(s):")
                for cu in set(copydoc_urls):
                    body_lines.append(f"  {cu}")
            body_lines.append("")
            body_lines.append("— Content Integrity Agent")

            state.notifications.append(Notification(
                recipient=owner,
                subject=subject_map[dominant],
                body="\n".join(body_lines),
                email_preview=f"{len(failures)} issue(s) for {owner.display_name}",
                action_taken=dominant,
                related_failures=failures,
                suggestions=related_suggestions,
            ))

        state.log("Router", "ROUTE_DECISIONS", f"failures={len(state.failures)}", f"notifications={len(state.notifications)}")
        self.log(f"Created {len(state.notifications)} notifications")
        return state


class MockNotifierAgent(BaseAgent):
    def __init__(self, dry_run: bool = True, verbose: bool = True):
        super().__init__("Notifier", verbose)
        self.dry_run = dry_run

    def run(self, state: PipelineState) -> PipelineState:
        for idx, notification in enumerate(state.notifications, 1):
            if self.dry_run:
                print(f"[DRY RUN - Email #{idx}]")
            print(notification.to_console())
        state.log("Notifier", "SEND_NOTIFICATIONS", f"count={len(state.notifications)}", "delivered")
        self.log(f"Delivered {len(state.notifications)} notifications")
        return state


def test_pipeline_with_mock_agents():
    agents = [
        MockDiscoveryAgent(input_path="fixtures/linkchecker-output.txt", verbose=False),
        MockResolverAgent(verbose=False),
        MockOwnerResolverAgent(verbose=False),
        MockSuggestionAgent(verbose=False),
        MockRouterAgent(verbose=False),
        MockNotifierAgent(dry_run=True, verbose=False),
    ]
    pipeline = OrchestratorAgent(agents=agents, verbose=True)
    state = PipelineState()
    state = pipeline.run(state)

    assert len(state.failures) == 6, f"Expected 6 failures, got {len(state.failures)}"
    assert len(state.page_meta) == 4, f"Expected 4 page_meta, got {len(state.page_meta)}"
    assert len(state.owners) >= 3, f"Expected >=3 owners, got {len(state.owners)}"
    assert len(state.notifications) >= 1, f"Expected >=1 notification, got {len(state.notifications)}"
    assert len(state.audit_log) >= 6, f"Expected >=6 audit entries, got {len(state.audit_log)}"

    for n in state.notifications:
        assert n.recipient.email, "Notification missing recipient email"
        assert n.subject, "Notification missing subject"
        assert n.body, "Notification missing body"

    print("\nALL MOCK PIPELINE TESTS PASSED")


if __name__ == "__main__":
    test_pipeline_with_mock_agents()
