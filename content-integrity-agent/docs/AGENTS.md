# Agent Quick Reference

> One-page cheat sheet for each agent. Implementers: read SPEC.md for full details, use this for quick lookup.

---

## DiscoveryAgent

**File:** `agents/discovery.py`
**Owner:** Engineer B
**Input:** `fixtures/linkchecker-output.txt`
**Output:** `state.failures: List[LinkFailure]`

**What it does:**
Reads linkchecker console output and converts to structured data.

**Key regex patterns:**
- `URL\s+(.*)` → broken_url
- `Parent URL\s+([^,]+)(?:,\s*line\s+(\d+))?` → source_page, line_number
- `Error\s+(.*)` → error_message
- `\d{3}` in error → status_code

**Severity mapping:**
- "404" → CRITICAL_404
- "timeout" / "connection" → TIMEOUT
- "redirect" / "too many redirects" → REDIRECT_CHAIN
- default → UNKNOWN

**Pseudo-code:**
```python
def run(state):
    text = read_file(self.input_path)
    failures = parse(text)  # List[LinkFailure]
    state.failures = failures
    state.log("Discovery", "PARSE", f"file={path}", f"count={len(failures)}")
    return state
```

**Expected output for fixtures:** 6 LinkFailure objects

---

## ResolverAgent

**File:** `agents/resolver.py`
**Owner:** Engineer B
**Input:** `state.failures` (reads source_page URLs)
**Output:** `state.page_meta: Dict[str, PageMeta]`

**What it does:**
Fetches HTML for each unique source page and extracts `<meta name="copydoc">`.

**Strategy:**
1. Collect unique source_page URLs from failures
2. For each URL:
   - If URL matches fixture map → load local HTML file
   - Else → HTTPClient.get(url)
3. Extract meta using html_parser.extract_page_meta()
4. Store PageMeta(url, copydoc_url, title)

**Fixture mapping:**
```python
{
    "https://canonical.com/data": "fixtures/pages/data.html",
    "https://canonical.com/kubernetes": "fixtures/pages/kubernetes.html",
    "https://canonical.com/microk8s": "fixtures/pages/microk8s.html",
    "https://canonical.com/openstack": "fixtures/pages/openstack.html",
}
```

**Error handling:**
- Fetch fails → store PageMeta(url=url) (empty, no copydoc)
- Never crash pipeline

**Expected output:** 4 PageMeta objects, 4 with copydoc URLs

---

## OwnerResolverAgent

**File:** `agents/owner_resolver.py`
**Owner:** Engineer B
**Input:** `state.page_meta` (reads copydoc_url)
**Output:** `state.owners`, updates `page_meta.page_owner_email`

**What it does:**
Resolves copydoc URL → Google Doc owner → Directory contact.

**Resolution chain:**
```
copydoc_url
  → extract doc_id (/d/{id}/)
  → MockGoogleDocAPI.get_document_info(doc_id)
  → get owner_email
  → MockDirectoryAPI.lookup_user(owner_email)
  → create Owner(...)
```

**Fallbacks:**
- No copydoc → skip, log warning
- Doc API fails → synthetic data with ops-team
- Directory lookup fails → ops-team

**Expected output:** 4-5 Owner objects (including ops-team fallback)

---

## SuggestionAgent

**File:** `agents/suggestion.py`
**Owner:** Engineer C
**Input:** `state.failures`, `state.page_meta`
**Output:** `state.suggestions: Dict[str, List[FixSuggestion]]`

**What it does:**
Uses LLM + sitemap similarity to suggest replacement URLs for broken links.

**Algorithm:**
```python
for failure in state.failures:
    candidates = SitemapService.find_similar(failure.broken_url)
    html = HTTPClient.get(failure.source_page)
    context = SitemapService.get_page_context(html, failure.broken_url)
    result = LLMClient.suggest_fix(failure.broken_url, failure.source_page, context, candidates)
    suggestion = FixSuggestion(
        original_url=failure.broken_url,
        suggested_url=result["suggested_url"],
        confidence=clamp(result["confidence"], 0.0, 1.0),
        reasoning=result["reasoning"],
        suggestion_text=result["user_facing_explanation"],
    )
    state.suggestions[failure.unique_id()] = [suggestion]
```

**LLM prompt (must return strict JSON):**
```
System: Respond in strict JSON: {"suggested_url": "...", "confidence": 0.0-1.0, "reasoning": "...", "user_facing_explanation": "..."}
User: Broken URL: {url}
      Source page: {page}
      Context: {html_snippet}
      Candidates: {urls}
```

**Offline fallback:**
If no API key or API fails:
- Use Jaccard similarity on URL path segments
- confidence = similarity * 0.5 (max 0.5)
- suggestion_text = "Fallback suggestion based on URL similarity"

---

## RouterAgent (ConfidenceRouter)

**File:** `agents/confidence_router.py`
**Owner:** Engineer C
**Input:** `state.failures`, `state.suggestions`, `state.page_meta`, `state.owners`
**Output:** `state.notifications: List[Notification]`

**What it does:**
Decides what action to take for each failure and batches notifications by owner.

**Decision tree per failure:**
```
if TIMEOUT and link now alive:
    → SUPPRESS_FALSE_ALARM
elif no owner_email:
    → ESCALATE_OPS
elif REDIRECT_CHAIN:
    → NOTIFY_INVESTIGATE
elif no suggestions:
    → NOTIFY_INVESTIGATE
elif confidence >= 0.90:
    → AUTO_FIX
elif confidence >= 0.60:
    → NOTIFY_WITH_SUGGESTION
else:
    → NOTIFY_INVESTIGATE
```

**Batching logic:**
- Group failures by owner_email
- Create one Notification per owner
- Dominant action = most severe action in group
- Aggregate all suggestions and failures

**Email subjects:**
- AUTO_FIX: "Auto-fix available for N broken link(s)"
- NOTIFY_WITH_SUGGESTION: "Broken link suggestions ready — N issue(s)"
- NOTIFY_INVESTIGATE: "Content health check: N issue(s) need attention"
- ESCALATE_OPS: "Escalated: N content issue(s)"

---

## NotifierAgent

**File:** `agents/notifier.py`
**Owner:** Engineer C
**Input:** `state.notifications`
**Output:** Console (stdout)

**What it does:**
Prints emails to console as mock delivery.

**Behavior:**
```python
for idx, notification in enumerate(state.notifications, 1):
    if dry_run:
        print(f"[DRY RUN - Email #{idx}]")
    print(notification.to_console())
    state.log("Notifier", "SEND", f"to={notification.recipient.email}", "printed")
```

**Production note:** Would integrate with Mattermost API or SMTP.

---

## OrchestratorAgent

**File:** `agents/orchestrator.py`
**Owner:** Engineer A
**Input:** `List[BaseAgent]`
**Output:** Final `PipelineState`

**What it does:**
Runs all agents sequentially and prints summary.

**Pseudo-code:**
```python
def run(self, state):
    for agent in self.agents:
        print(f"→ Running {agent.name}...")
        state = agent.run(state)
        print(f"✓ {agent.name} complete")
    
    print_summary(state)
    return state
```

**Summary output:**
```
Broken links discovered: 6
Pages resolved: 4
Owners identified: 4
Notifications drafted: 3

notify_with_suggestion: 2 notification(s)
   → Alice: 2 issue(s)
   → Bob: 1 issue(s)

escalate_ops: 1 notification(s)
   → Content Ops Team: 1 issue(s)
```

---

## Stub Agents (Future Vision)

### RedirectChainDetector
- Count failures with "redirect" in error
- Print: `[STUB] Found N redirect chain(s) — future 404 risk`

### ContentDecayScorer
- Calculate days since last_modified / 365
- Print: `[STUB] {url} decay score: {score} ({status})`

### CrossPageConsistencyAgent
- Count duplicate broken_url across failures
- Print: `[STUB] Site-wide: {url} on {N} pages`

---

## Testing Each Agent

| Agent | Test Strategy | Expected Behavior |
|-------|--------------|-------------------|
| Discovery | Parse fixture file | 6 failures, correct URLs |
| Resolver | Load fixture HTML | 4 pages, 4 copydocs |
| OwnerResolver | Chain mock APIs | 4 owners, ops fallback |
| Suggestion | Mock LLM response | Suggestions with confidence |
| Router | Fixed suggestions | Correct routing decisions |
| Notifier | Print capture | Emails formatted correctly |
| Orchestrator | Full pipeline | All stages execute |

---

## Common Pitfalls

1. **Don't modify PipelineState** by reassigning lists (use `.append()`, `.extend()`)
2. **Always call `state.log()`** after significant decisions
3. **Never crash the pipeline** — catch exceptions internally
4. **Clamp confidence to [0.0, 1.0]** — LLMs may return weird values
5. **Batch notifications by owner** — don't send 6 separate emails for 6 links
6. **Use offline fallback** — demo must work without API key

---

## Agent Checklist

When implementing an agent, verify:
- [ ] Inherits from `BaseAgent`
- [ ] Implements `run(self, state) -> PipelineState`
- [ ] Calls `self.log()` for key steps
- [ ] Calls `state.log()` for audit trail
- [ ] Handles errors gracefully (try/except)
- [ ] Returns state (even if empty)
- [ ] Has unit tests