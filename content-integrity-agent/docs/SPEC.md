# Content Integrity Agent - Technical Specification

> **Version:** 0.1  
> **Purpose:** Multi-agentic system for autonomous broken link detection and content owner notification  
> **Target Site:** canonical.com (uses `<meta name="copydoc">` convention)  
> **Audience:** AI agents implementing this system  

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Data Model](#2-data-model)
3. [Agent Specifications](#3-agent-specifications)
4. [Service Specifications](#4-service-specifications)
5. [Fixture Data](#5-fixture-data)
6. [CLI Interface](#6-cli-interface)
7. [Error Handling](#7-error-handling)
8. [Testing Strategy](#8-testing-strategy)

---

## 1. System Overview

The Content Integrity Agent (CIA) is a multi-agent system that processes broken link reports from `linkchecker` and autonomously:

1. Parses broken links and classifies severity
2. Fetches source pages and extracts copydoc metadata
3. Resolves content owners via Google Doc → Directory API chain
4. Suggests fixes using LLM reasoning + sitemap similarity
5. Routes notifications based on confidence thresholds
6. Outputs contextual emails to console (mock delivery)

### Architecture Diagram

```
Input: fixtures/linkchecker-output.txt
  ↓
┌─────────────────┐
│ DiscoveryAgent  │ → Parse linkchecker output → List[LinkFailure]
└────────┬────────┘
         ↓
┌─────────────────┐
│  ResolverAgent  │ → Fetch HTML → Extract <meta name="copydoc">
└────────┬────────┘
         ↓
┌─────────────────────┐
│ OwnerResolverAgent  │ → copydoc URL → Google Doc API → Directory API → Owner
└────────┬────────────┘
         ↓
┌───────────────────┐
│  SuggestionAgent  │ → LLM reasoning + sitemap similarity → FixSuggestion
└────────┬──────────┘
         ↓
┌─────────────────────┐
│   RouterAgent       │ → Confidence-based routing → Notification
└────────┬────────────┘
         ↓
┌───────────────────┐
│  NotifierAgent     │ → Print contextual emails to console
└────────────────────┘
         ↓
Output: Console email previews + audit trail
```

### Agent Communication

All agents share a single `PipelineState` object. Each agent:
- Reads from `state` what previous agents produced
- Writes results back to `state`
- Appends to `state.audit_log` for every decision

This is **not** message-passing — it's shared mutable state with audit logging.

---

## 2. Data Model

### 2.1 Core Dataclasses

All defined in `models/schemas.py`. These are **frozen after hour 0**.

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict

class FailureSeverity(str, Enum):
    CRITICAL_404 = "critical_404"
    TIMEOUT = "timeout"
    REDIRECT_CHAIN = "redirect_chain"
    SOFT_404 = "soft_404"
    UNKNOWN = "unknown"

class RouterAction(str, Enum):
    AUTO_FIX = "auto_fix"
    NOTIFY_WITH_SUGGESTION = "notify_with_suggestion"
    NOTIFY_INVESTIGATE = "notify_investigate"
    ESCALATE_OPS = "escalate_ops"
    SUPPRESS_FALSE_ALARM = "suppress_false_alarm"

@dataclass
class LinkFailure:
    source_page: str        # e.g., "https://canonical.com/data"
    broken_url: str         # e.g., "https://canonical.com/old-data-docs"
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    severity: FailureSeverity = FailureSeverity.UNKNOWN
    line_number: Optional[int] = None

    def unique_id(self) -> str:
        return f"{self.source_page}::{self.broken_url}"

@dataclass
class PageMeta:
    url: str
    copydoc_url: Optional[str] = None      # e.g., "https://docs.google.com/document/d/1QKc7tHZZSJ.../edit"
    title: Optional[str] = None
    page_owner_email: Optional[str] = None
    last_modified: Optional[str] = None

@dataclass
class Owner:
    email: str
    display_name: str
    team: str
    department: str
    mattermost_username: Optional[str] = None

@dataclass
class FixSuggestion:
    original_url: str
    suggested_url: Optional[str] = None
    suggestion_text: str = ""             # User-facing explanation
    confidence: float = 0.0               # 0.0 to 1.0
    reasoning: str = ""                 # Internal reasoning for debug

@dataclass
class AgentAuditLog:
    timestamp: str                        # ISO8601, e.g., "2025-05-13T10:00:00Z"
    agent_name: str
    action: str
    input_summary: str
    output_summary: str
    confidence: Optional[float] = None

@dataclass
class Notification:
    recipient: Owner
    subject: str
    body: str
    email_preview: str                    # One-line summary
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
    failures: List[LinkFailure] = field(default_factory=list)
    page_meta: Dict[str, PageMeta] = field(default_factory=dict)
    owners: Dict[str, Owner] = field(default_factory=dict)
    suggestions: Dict[str, List[FixSuggestion]] = field(default_factory=dict)
    notifications: List[Notification] = field(default_factory=list)
    audit_log: List[AgentAuditLog] = field(default_factory=list)

    def log(self, agent_name: str, action: str, input_summary: str,
            output_summary: str, confidence: Optional[float] = None):
        from datetime import datetime
        self.audit_log.append(AgentAuditLog(
            timestamp=datetime.utcnow().isoformat() + "Z",
            agent_name=agent_name,
            action=action,
            input_summary=input_summary,
            output_summary=output_summary,
            confidence=confidence,
        ))
```

### 2.2 Configuration

```python
# config/settings.py
from dataclasses import dataclass
import os

@dataclass
class Settings:
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4o-mini"
    llm_temperature: float = 0.3
    auto_fix_threshold: float = 0.90
    notify_threshold: float = 0.60
    http_timeout: int = 15
    enable_llm: bool = True
    cache_dir: str = ".cache"
    fixtures_dir: str = "fixtures"
    dry_run: bool = True

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            openrouter_api_key=os.environ.get("OPENROUTER_API_KEY", ""),
            openrouter_model=os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
            llm_temperature=float(os.environ.get("LLM_TEMPERATURE", "0.3")),
            auto_fix_threshold=float(os.environ.get("AUTO_FIX_THRESHOLD", "0.90")),
            notify_threshold=float(os.environ.get("NOTIFY_THRESHOLD", "0.60")),
            http_timeout=int(os.environ.get("HTTP_TIMEOUT", "15")),
            enable_llm=os.environ.get("ENABLE_LLM", "true").lower() == "true",
            cache_dir=os.environ.get("CACHE_DIR", ".cache"),
            fixtures_dir=os.environ.get("FIXTURES_DIR", "fixtures"),
            dry_run=os.environ.get("DRY_RUN", "true").lower() == "true",
        )
```

---

## 3. Agent Specifications

### 3.1 Base Agent

**File:** `agents/base.py`

```python
from abc import ABC, abstractmethod
from models.schemas import PipelineState

class BaseAgent(ABC):
    def __init__(self, name: str, verbose: bool = True):
        self.name = name
        self.verbose = verbose

    def log(self, message: str):
        if self.verbose:
            print(f"[{self.name.upper()}] {message}")

    @abstractmethod
    def run(self, state: PipelineState) -> PipelineState:
        pass
```

**Rule:** Every agent MUST inherit from `BaseAgent` and implement `run()`.

---

### 3.2 DiscoveryAgent

**File:** `agents/discovery.py`  
**Owner:** Engineer B  
**Input:** `fixtures/linkchecker-output.txt`  
**Output:** Populates `state.failures`

**Parsing Rules:**

The input file follows `linkchecker` console output format:

```
URL        https://canonical.com/old-data-docs
Parent URL https://canonical.com/data, line 42
Error      404 Not Found
Result     Error
```

**Regex patterns to extract:**
- `URL\s+(.*)` → `broken_url`
- `Parent URL\s+([^,]+)(?:,\s*line\s+(\d+))?` → `source_page`, `line_number`
- `Error\s+(.*)` → `error_message`
- Extract any `\d{3}` from error message as `status_code`

**Severity Classification:**
- Error message contains "404" → `CRITICAL_404`
- Error message contains "timeout" or "connection" → `TIMEOUT`
- Error message contains "redirect" or "too many redirects" → `REDIRECT_CHAIN`
- Default → `UNKNOWN`

**Behavior:**
1. Read entire file as text
2. Parse into list of `LinkFailure` objects
3. Set `state.failures = parsed_failures`
4. Call `state.log("Discovery", "PARSE_LINKCHECKER", f"file={path}", f"parsed {n} links")`

---

### 3.3 ResolverAgent

**File:** `agents/resolver.py`  
**Owner:** Engineer B  
**Input:** `state.failures` (reads `source_page` URLs)  
**Output:** Populates `state.page_meta`

**Behavior:**
1. Collect unique `source_page` URLs from `state.failures`
2. For each URL:
   - If URL is `https://canonical.com/*` and we have a local fixture → load fixture HTML
   - Otherwise → `HTTPClient.get(url)` to fetch HTML
   - Extract `<meta name="copydoc" content="...">` using `utils/html_parser.extract_page_meta()`
   - Extract `<title>` tag content
3. Create `PageMeta(url=url, copydoc_url=..., title=...)`
4. Store in `state.page_meta[url] = page_meta`
5. Log to `state.audit_log`

**Error Handling:**
- If fetch fails → store `PageMeta(url=url)` (no copydoc)
- Never crash the pipeline

---

### 3.4 OwnerResolverAgent

**File:** `agents/owner_resolver.py`  
**Owner:** Engineer B  
**Input:** `state.page_meta` (reads `copydoc_url`)  
**Output:** Populates `state.owners`, updates `page_meta.page_owner_email`

**Resolution Chain:**

```
copydoc_url (e.g., "https://docs.google.com/document/d/1QKc7tHZZSJ.../edit")
  ↓ extract doc_id from /d/{id}/edit
  ↓ MockGoogleDocAPI.get_document_info(doc_id)
  ↓ Returns {"doc_id": "...", "title": "...", "owner_email": "alice@canonical.com", "last_modified": "..."}
  ↓ MockDirectoryAPI.lookup_user("alice@canonical.com")
  ↓ Returns {"email": "...", "display_name": "...", "team": "...", "department": "...", "mattermost_username": "..."}
  ↓ Create Owner(...)
```

**Behavior:**
1. Iterate `state.page_meta.values()`
2. If `copydoc_url` is None → log warning, skip
3. Call `MockGoogleDocAPI.get_document_info(copydoc_url)` → get `owner_email`
4. Call `MockDirectoryAPI.lookup_user(owner_email)` → get full user record
5. If both succeed:
   - Create `Owner(...)` from directory record
   - `state.owners[owner.email] = owner`
   - `page_meta.page_owner_email = owner.email`
6. If directory lookup fails → fallback to ops team: `ops-team@canonical.com`

**Mock API Specifications:**

`MockGoogleDocAPI` (`services/mock_google_doc_api.py`):
- `__init__(fixtures_dir="fixtures/copydocs")`
- `get_document_info(doc_url) -> Optional[dict]`
- Extracts doc_id from URL pattern: `/d/{id}/`
- Loads `fixtures/copydocs/doc_{doc_id}.json`
- Returns dict with keys: `doc_id`, `title`, `owner_email`, `last_modified`, `contributors`

`MockDirectoryAPI` (`services/mock_directory_api.py`):
- `__init__(fixtures_path="fixtures/directory.json")`
- `lookup_user(email) -> Optional[dict]`
- Loads `fixtures/directory.json` on init
- Returns dict with keys: `email`, `display_name`, `team`, `department`, `mattermost_username`

---

### 3.5 SuggestionAgent

**File:** `agents/suggestion.py`  
**Owner:** Engineer C  
**Input:** `state.failures`, `state.page_meta`  
**Output:** Populates `state.suggestions` (dict: `failure.unique_id()` → `List[FixSuggestion]`)

**Behavior:**
1. For each `failure` in `state.failures`:
   a. Call `SitemapService.find_similar(failure.broken_url, top_k=5)` → candidate URLs
   b. Fetch source page HTML via `HTTPClient.get(failure.source_page)`
   c. Extract HTML context around broken link via `SitemapService.get_page_context(html, failure.broken_url)`
   d. Call `LLMClient.suggest_fix(...)` with:
      - `broken_url`
      - `source_page`
      - `page_context` (HTML snippet, max 1000 chars)
      - `candidate_urls`
   e. Parse LLM response (JSON), create `FixSuggestion(...)`
   f. Clamp confidence to [0.0, 1.0]
   g. Store: `state.suggestions[failure.unique_id()] = [fix_suggestion]`
   h. Log to `state.audit_log`

**LLM Prompt (must return strict JSON):**

```
System: You are a Content Integrity Assistant. Respond in strict JSON format:
{"suggested_url": "..." or null, "confidence": 0.0-1.0, "reasoning": "...", "user_facing_explanation": "..."}

User: Broken URL: {broken_url}
      Source page: {source_page}
      Page context: {page_context[:1000]}
      Candidate replacements: {candidate_urls}
      What is the most likely correct replacement?
```

**Offline Fallback:**
If `OPENROUTER_API_KEY` is missing or API call fails:
- Use deterministic Jaccard similarity on URL path segments
- Return `FixSuggestion` with `confidence = similarity_score * 0.5` (capped at 0.5)
- `suggestion_text = "No LLM available. Fallback suggestion based on URL similarity."`

**LLMClient Spec:**

```python
class LLMClient:
    def __init__(self, api_key=None, model="openai/gpt-4o-mini"):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.model = model

    def suggest_fix(self, broken_url, source_page, page_context, candidate_urls) -> dict:
        # POST to https://openrouter.ai/api/v1/chat/completions
        # Parse JSON response, handle markdown fences (```json ... ```)
        # Return parsed dict
```

**SitemapService Spec:**

```python
class SitemapService:
    def __init__(self, http_client):
        self.http = http_client
        self._url_index = {
            "https://canonical.com/data",
            "https://canonical.com/data/docs",
            "https://canonical.com/kubernetes",
            "https://canonical.com/kubernetes/docs",
            "https://canonical.com/microk8s",
            "https://canonical.com/microk8s/docs",
            "https://canonical.com/openstack",
            "https://canonical.com/openstack/pricing",
        }

    def find_similar(self, broken_url: str, top_k=5) -> List[str]:
        # Jaccard similarity on URL path segments
        # broken_url="/old-data-docs" → ["/data/docs"]
        # Return top_k matches with score > 0.1

    def get_page_context(self, html: str, broken_url: str) -> str:
        # Find <a href="broken_url"> in HTML
        # Return 200 chars before + 200 chars after the anchor tag
        # If not found, return first 1000 chars of <body>
```

---

### 3.6 RouterAgent (ConfidenceRouter)

**File:** `agents/confidence_router.py`  
**Owner:** Engineer C  
**Input:** `state.failures`, `state.suggestions`, `state.page_meta`, `state.owners`  
**Output:** Populates `state.notifications`

**Decision Logic per Failure:**

```python
def _decide(failure, state) -> Tuple[RouterAction, str]:
    # 1. Self-validation: re-check broken link
    if failure.severity == TIMEOUT:
        if HTTPClient.is_link_alive(failure.broken_url):
            return (SUPPRESS_FALSE_ALARM, "Link is now alive - transient timeout")
    
    # 2. Owner availability
    owner_email = state.page_meta.get(failure.source_page, {}).page_owner_email
    if not owner_email:
        return (ESCALATE_OPS, "No copydoc or owner found")
    
    # 3. Severity escalation
    if failure.severity == REDIRECT_CHAIN:
        return (NOTIFY_INVESTIGATE, "Redirect chains require human review")
    
    # 4. Confidence-based routing
    suggestions = state.suggestions.get(failure.unique_id(), [])
    if not suggestions:
        return (NOTIFY_INVESTIGATE, "No fix suggestions generated")
    
    top = suggestions[0]
    if top.confidence >= 0.90 and top.suggested_url:
        return (AUTO_FIX, f"High confidence ({top.confidence:.2f}) replacement found")
    elif top.confidence >= 0.60 and top.suggested_url:
        return (NOTIFY_WITH_SUGGESTION, f"Moderate confidence ({top.confidence:.2f})")
    else:
        return (NOTIFY_INVESTIGATE, f"Low confidence ({top.confidence:.2f}) - needs human review")
```

**Batching by Owner:**
- Group failures by `owner_email`
- For each owner, create ONE `Notification` containing all their failures
- Determine `dominant_action`:
  - If all are `AUTO_FIX` → `AUTO_FIX`
  - If any are `AUTO_FIX` or `NOTIFY_WITH_SUGGESTION` → `NOTIFY_WITH_SUGGESTION`
  - If any are `NOTIFY_INVESTIGATE` → `NOTIFY_INVESTIGATE`
  - Default → `ESCALATE_OPS`

**Email Subject Lines:**
- `AUTO_FIX` → `Auto-fix available for {count} broken link(s) on your page(s)`
- `NOTIFY_WITH_SUGGESTION` → `Broken link suggestions ready — {count} issue(s) to review`
- `NOTIFY_INVESTIGATE` → `Content health check: {count} issue(s) need your attention`
- `ESCALATE_OPS` → `Escalated: {count} content issue(s) on canonical.com`

**Email Body Template:**
```
Hi {owner.display_name},

Our Content Integrity Agent scanned canonical.com and found issues on pages you own:

• **{failure.broken_url}** on `{failure.source_page}`
  → Status: {failure.error_message}
  → 💡 Suggestion: Did you mean `{suggested_url}`?

You can update the content via your copydoc(s):
{copydoc_url}

— Content Integrity Agent 🤖
```

---

### 3.7 NotifierAgent

**File:** `agents/notifier.py`  
**Owner:** Engineer C  
**Input:** `state.notifications`  
**Output:** Console output (mock email delivery)

**Behavior:**
1. If `dry_run=True` → print `[DRY RUN - Email #{idx}]` before each notification
2. Print `notification.to_console()` for each notification
3. Log to `state.audit_log`

**Production Note:** In real deployment, this would integrate with Mattermost API or SMTP. For hackathon, console output is sufficient.

---

### 3.8 OrchestratorAgent

**File:** `agents/orchestrator.py`  
**Owner:** Engineer A  
**Input:** List of `BaseAgent` instances  
**Output:** Final `PipelineState`

**Behavior:**
1. Accept `List[BaseAgent]` in constructor
2. `run(state)` executes agents sequentially:
   ```python
   for agent in self.agents:
       print(f"→ Running {agent.name}...")
       state = agent.run(state)
       print(f"✓ {agent.name} complete")
   ```
3. After all agents, call `_print_summary(state)`:
   - Print counts: failures, pages, owners, notifications
   - Group notifications by `RouterAction`
   - Print full `to_console()` output for each notification
   - Print audit trail summary

---

### 3.9 Stubbed Vision Agents

**File:** `agents/stubs.py`  
**Owner:** Engineer C  
**Purpose:** Print convincing messages showing future roadmap

**Implement three agents:**
- `RedirectChainDetector` → Count failures with "redirect" in error message, print `[STUB] Found N redirect chain(s)`
- `ContentDecayScorer` → Calculate `days_old / 365` from `page_meta.last_modified`, print `[STUB] {url} decay score: {score}`
- `CrossPageConsistencyAgent` → Count duplicate `broken_url` across failures, print `[STUB] Site-wide pattern: {url} on {N} pages`

These agents run AFTER the main pipeline and only print messages. They don't modify state.

---

## 4. Service Specifications

### 4.1 HTTPClient

```python
class HTTPClient:
    DEFAULT_TIMEOUT = 15
    USER_AGENT = "ContentIntegrityBot/1.0 (+https://canonical.com; bot@canonical.com)"

    def __init__(self, cache=None):
        self.cache = cache or SimpleCache()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.USER_AGENT})

    def request(self, method: str, url: str, use_cache=True, **kwargs) -> str:
        # Check cache first for GET/HEAD
        # Make request with retry
        # Cache result
        # Return response text

    def head(self, url: str, **kwargs) -> requests.Response:
        # HEAD request, return full response object

    def get(self, url: str, **kwargs) -> str:
        # GET request, return response body text

    def is_link_alive(self, url: str) -> bool:
        # HEAD request with 5s timeout
        # Return True if status < 400, False on any exception
```

**Cache Rules:**
- Only cache GET/HEAD requests
- Only cache requests to `localhost`, `127.0.0.1`, `canonical.com`, or empty netloc
- Use `SimpleCache` with 1-hour TTL

### 4.2 SimpleCache

```python
class SimpleCache:
    def __init__(self, ttl_seconds=3600, cache_dir=".cache"):
        self._memory = {}
        self.ttl = ttl_seconds
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def get(self, url: str) -> Optional[Any]:
        # Check memory first, then file
        # Return None if expired or missing

    def set(self, url: str, value: Any):
        # Store in memory and write to file
        # File format: JSON with "value" and "expires" (ISO timestamp)
```

### 4.3 Retry Decorator

```python
def retry(max_attempts=3, backoff_factor=1.0, jitter=True):
    # Exponential backoff: delay = backoff_factor * 2^(attempt-1)
    # If jitter=True: delay *= (0.5 + random.random())
    # Sleep between retries
```

### 4.4 HTML Parser

```python
def extract_page_meta(html: str) -> Dict[str, Optional[str]]:
    # Use html.parser.HTMLParser from stdlib
    # Extract <meta name="copydoc" content="...">
    # Extract <title> content
    # Only parse <head> section for efficiency
    # Return {"copydoc_url": "...", "title": "..."}
```

---

## 5. Fixture Data

### 5.1 Linkchecker Output

**File:** `fixtures/linkchecker-output.txt`

```
URL        https://canonical.com/old-data-docs
Parent URL https://canonical.com/data, line 42
Error      404 Not Found
Result     Error

URL        https://canonical.com/deprecated-api/v1
Parent URL https://canonical.com/kubernetes, line 120
Error      404 Not Found
Result     Error

URL        https://canonical.com/microk8s/legacy-install
Parent URL https://canonical.com/microk8s, line 88
Error      404 Not Found
Result     Error

URL        https://canonical.com/openstack/old-pricing
Parent URL https://canonical.com/openstack, line 55
Error      404 Not Found
Result     Error

URL        https://canonical.com/broken-timeout-example
Parent URL https://canonical.com/data, line 140
Error      Connection timeout
Result     Error

URL        https://canonical.com/too-many-redirects
Parent URL https://canonical.com/microk8s, line 200
Error      Too many redirects
Result     Error
```

### 5.2 Page Fixtures

**File:** `fixtures/pages/data.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="copydoc" content="https://docs.google.com/document/d/1QKc7tHZZSJttrPOziK_w_9yKLLgoC4Vcufke9dSvQ-g/edit" />
    <title>Canonical open source data platform solutions</title>
</head>
<body>
    <h1>Data Solutions</h1>
    <a href="https://canonical.com/old-data-docs">Old docs (BROKEN)</a>
    <a href="https://canonical.com/data/docs">New docs</a>
</body>
</html>
```

**File:** `fixtures/pages/kubernetes.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="copydoc" content="https://docs.google.com/document/d/aBcDeFgHiJkLmNoPqRsTuV/edit" />
    <title>Kubernetes on Ubuntu | Canonical</title>
</head>
<body>
    <h1>Kubernetes</h1>
    <a href="https://canonical.com/deprecated-api/v1">Old API (BROKEN)</a>
</body>
</html>
```

**File:** `fixtures/pages/microk8s.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="copydoc" content="https://docs.google.com/document/d/xYz123AbCDeFgHiJkLm/edit" />
    <title>MicroK8s | Canonical</title>
</head>
<body>
    <h1>MicroK8s</h1>
    <a href="https://canonical.com/microk8s/legacy-install">Legacy install (BROKEN)</a>
    <a href="https://canonical.com/microk8s/docs">Docs</a>
</body>
</html>
```

**File:** `fixtures/pages/openstack.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="copydoc" content="https://docs.google.com/document/d/mNoPqRsTuVwXyZ123AbC/edit" />
    <title>OpenStack | Canonical</title>
</head>
<body>
    <h1>OpenStack</h1>
    <a href="https://canonical.com/openstack/old-pricing">Old pricing (BROKEN)</a>
    <a href="https://canonical.com/openstack/pricing">Current pricing</a>
</body>
</html>
```

### 5.3 Copydoc Fixtures

**File:** `fixtures/copydocs/doc_1QKc7tH.json`

```json
{
    "doc_id": "1QKc7tHZZSJttrPOziK_w_9yKLLgoC4Vcufke9dSvQ-g",
    "title": "Canonical Data Solutions — Copydoc",
    "owner_email": "alice.chen@canonical.com",
    "last_modified": "2024-12-15T10:30:00Z",
    "contributors": ["alice.chen@canonical.com", "bob.smith@canonical.com"]
}
```

**File:** `fixtures/copydocs/doc_aBcDeFg.json`

```json
{
    "doc_id": "aBcDeFgHiJkLmNoPqRsTuV",
    "title": "Kubernetes on Ubuntu — Copydoc",
    "owner_email": "bob.smith@canonical.com",
    "last_modified": "2024-11-20T14:00:00Z",
    "contributors": ["bob.smith@canonical.com"]
}
```

**File:** `fixtures/copydocs/doc_xYz123.json`

```json
{
    "doc_id": "xYz123AbCDeFgHiJkLm",
    "title": "MicroK8s — Copydoc",
    "owner_email": "diana.prince@canonical.com",
    "last_modified": "2024-10-05T09:15:00Z",
    "contributors": ["diana.prince@canonical.com", "eve.davis@canonical.com"]
}
```

**File:** `fixtures/copydocs/doc_mNoPqR.json`

```json
{
    "doc_id": "mNoPqRsTuVwXyZ123AbC",
    "title": "OpenStack — Copydoc",
    "owner_email": "eve.davis@canonical.com",
    "last_modified": "2024-09-01T16:45:00Z",
    "contributors": ["eve.davis@canonical.com"]
}
```

### 5.4 Directory Fixture

**File:** `fixtures/directory.json`

```json
{
    "users": [
        {
            "email": "alice.chen@canonical.com",
            "display_name": "Alice Chen",
            "team": "Data Platform Engineering",
            "department": "Engineering",
            "mattermost_username": "alice.chen"
        },
        {
            "email": "bob.smith@canonical.com",
            "display_name": "Bob Smith",
            "team": "Cloud Native",
            "department": "Engineering",
            "mattermost_username": "bob.smith"
        },
        {
            "email": "diana.prince@canonical.com",
            "display_name": "Diana Prince",
            "team": "Edge & IoT",
            "department": "Engineering",
            "mattermost_username": "diana.prince"
        },
        {
            "email": "eve.davis@canonical.com",
            "display_name": "Eve Davis",
            "team": "Private Cloud",
            "department": "Engineering",
            "mattermost_username": "eve.davis"
        },
        {
            "email": "ops-team@canonical.com",
            "display_name": "Content Ops Team",
            "team": "Web Operations",
            "department": "Marketing",
            "mattermost_username": "content-ops"
        }
    ]
}
```

---

## 6. CLI Interface

**File:** `cli.py`

**Usage:**
```bash
python cli.py --input fixtures/linkchecker-output.txt --verbose --dry-run
```

**Arguments:**
- `--input, -i`: Path to linkchecker output file (default: `fixtures/linkchecker-output.txt`)
- `--verbose, -v`: Print agent logs (default: True)
- `--quiet, -q`: Suppress logs
- `--dry-run`: Preview only, don't send notifications
- `--agent`: Run single agent (discovery/resolver/owner/suggestion/router/notifier/all)

**Pipeline Wiring:**
```python
def create_pipeline(input_path, verbose=True, dry_run=True):
    http_client = HTTPClient()
    llm_client = LLMClient(api_key=os.environ.get("OPENROUTER_API_KEY"))
    doc_api = MockGoogleDocAPI()
    directory_api = MockDirectoryAPI()
    sitemap = SitemapService(http_client)

    agents = [
        DiscoveryAgent(input_path=input_path, verbose=verbose),
        ResolverAgent(http_client=http_client, verbose=verbose),
        OwnerResolverAgent(doc_api=doc_api, directory_api=directory_api, verbose=verbose),
        SuggestionAgent(http_client=http_client, llm_client=llm_client, sitemap=sitemap, verbose=verbose),
        RouterAgent(verbose=verbose),
        NotifierAgent(dry_run=dry_run, verbose=verbose),
    ]

    return OrchestratorAgent(agents=agents, verbose=verbose)
```

---

## 7. Error Handling

### 7.1 Graceful Degradation Rules

| Failure Point | Fallback Behavior |
|--------------|-------------------|
| Linkchecker file missing | CLI exits with code 1, error message |
| Page fetch timeout | Use local fixture HTML, or minimal synthetic HTML |
| `<meta copydoc>` missing | Log warning, skip owner resolution for this page |
| Google Doc API fails | Return synthetic data with `ops-team@canonical.com` |
| Directory API lookup fails | Return `ops-team@canonical.com` as owner |
| OpenRouter API fails | Use deterministic fallback (Jaccard similarity), confidence capped at 0.5 |
| LLM returns invalid JSON | Return `FixSuggestion` with confidence=0.0, error in reasoning |
| No owner found for any failure | Route all to `ESCALATE_OPS` |

### 7.2 Never Crash the Pipeline

Every agent must handle exceptions internally and continue processing. If an agent encounters an error:
1. Log the error
2. Add audit log entry with `action="..._FAILED"`
3. Return state (possibly with empty/partial results)
4. Next agent continues

---

## 8. Testing Strategy

### 8.1 Contract Tests

**File:** `tests/test_contracts.py`

Verify all agents and models can be imported:
```python
def test_all_agents_importable():
    from agents.discovery import DiscoveryAgent
    from agents.resolver import ResolverAgent
    from agents.owner_resolver import OwnerResolverAgent
    from agents.suggestion import SuggestionAgent
    from agents.confidence_router import RouterAgent
    from agents.notifier import NotifierAgent
    from agents.orchestrator import OrchestratorAgent
    # All imports should succeed
```

### 8.2 End-to-End Test

**File:** `tests/test_e2e.py`

Run full pipeline and assert:
```python
def test_pipeline():
    pipeline = create_pipeline("fixtures/linkchecker-output.txt", verbose=False)
    state = pipeline.run(PipelineState())
    
    assert len(state.failures) == 6
    assert len(state.page_meta) == 4
    assert len(state.owners) >= 3
    assert len(state.notifications) >= 1
    
    for n in state.notifications:
        assert n.recipient.email
        assert n.subject
        assert n.body
```

### 8.3 Agent Unit Tests

Each engineer writes tests for their agents:
- **Engineer B:** `tests/test_discovery.py`, `tests/test_resolver.py`
- **Engineer C:** `tests/test_suggestion.py`, `tests/test_router.py`
- **Engineer A:** `tests/test_http_client.py`, `tests/test_e2e.py`

---

## 9. Environment Setup

### 9.1 Dependencies

**No pip install required.** System uses:
- Python 3.10+ (stdlib)
- `requests` (already installed in environment)
- `jinja2` (already installed, optional for email templates)

### 9.2 Environment Variables

Create `.env` from `.env.example`:
```bash
OPENROUTER_API_KEY=sk-or-v1-...
```

If missing, system falls back to deterministic suggestions.

### 9.3 Running the Demo

```bash
make lint      # Verify imports
make test      # Run contract tests
make demo      # Run full pipeline
make clean     # Remove cache
```

---

## 10. Success Criteria

The system is complete when:

- [x] `models/schemas.py` defines all dataclasses
- [ ] `agents/discovery.py` parses 6 failures from linkchecker output
- [ ] `agents/resolver.py` extracts copydoc from 4 fixture pages
- [ ] `agents/owner_resolver.py` resolves 4+ unique owners
- [ ] `agents/suggestion.py` generates suggestions with confidence scores
- [ ] `agents/confidence_router.py` creates batched notifications by owner
- [ ] `agents/notifier.py` prints 3+ contextual emails to console
- [ ] `cli.py` runs end-to-end with `--input` and `--verbose`
- [ ] `tests/test_e2e.py` passes with all assertions
- [ ] Demo runs successfully with `make demo`

---

## Appendix A: LLM Integration Details

### OpenRouter API

**Endpoint:** `POST https://openrouter.ai/api/v1/chat/completions`

**Headers:**
```
Authorization: Bearer {OPENROUTER_API_KEY}
Content-Type: application/json
HTTP-Referer: https://canonical.com
X-Title: Content Integrity Agent
```

**Payload for suggest_fix:**
```json
{
    "model": "openai/gpt-4o-mini",
    "temperature": 0.2,
    "messages": [
        {"role": "system", "content": "You are a Content Integrity Assistant. Respond in strict JSON: {\"suggested_url\": \"...\" or null, \"confidence\": 0.0-1.0, \"reasoning\": \"...\", \"user_facing_explanation\": \"...\"}"},
        {"role": "user", "content": "Broken URL: ...\nSource page: ...\nPage context: ...\nCandidates: ...\nWhat is the most likely correct replacement?"}
    ]
}
```

**Response Parsing:**
- Content may be wrapped in markdown fences: ` ```json {...} ``` `
- Strip fences, parse JSON
- If parse fails → return error dict with confidence=0.0

---

## Appendix B: Git Workflow for Team

```bash
# Initial setup (Engineer A)
git checkout -b interfaces
git push origin interfaces

# Engineers B & C branch from interfaces
git fetch origin
git checkout -b eng2/discovery origin/interfaces   # Engineer B
git checkout -b eng3/suggestion origin/interfaces  # Engineer C

# Work on your branch, commit frequently
git add .
git commit -m "feat(discovery): implement linkchecker parser"

# Periodically rebase on interfaces
git fetch origin
git rebase origin/interfaces

# Merge to interfaces when done
git checkout interfaces
git merge eng2/discovery

# Final integration
git checkout main
git merge interfaces
```

---

**END OF SPECIFICATION**

> For AI agents implementing this: Every section above contains exact requirements. Do not change signatures, data models, or fixture formats without team consensus. When in doubt, implement exactly as specified.