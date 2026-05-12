# Architecture Documentation

> Visual guide to the Content Integrity Agent system for AI implementers.

## System Context

```
┌─────────────────────────────────────────────────────────────┐
│                      Content Integrity Agent                   │
│                                                              │
│  Input: linkchecker output                                   │
│  Output: Console emails + audit trail                        │
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │   External   │    │    Mock      │    │   Future     │ │
│  │   APIs       │    │   Services   │    │   Agents     │ │
│  │              │    │              │    │              │ │
│  │ • canonical  │    │ • Google Doc │    │ • Redirect   │ │
│  │   .com       │    │   API        │    │   Chain      │ │
│  │ • OpenRouter │    │ • Directory  │    │   Detector   │ │
│  │   (LLM)      │    │   API        │    │ • Content    │ │
│  │              │    │              │    │   Decay      │ │
│  └──────────────┘    └──────────────┘    │   Scorer     │ │
│                                            │ • Cross-Page │ │
│                                            │   Consistency│ │
│                                            └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

```
linkchecker-output.txt
        │
        ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│  DiscoveryAgent │────▶│  ResolverAgent  │────▶│ OwnerResolver │
│  (parse text)   │     │  (fetch HTML)   │     │  (resolve     │
│                 │     │  (extract meta) │     │   owners)     │
└───────────────┘     └───────────────┘     └───────────────┘
        │                                            │
        │ PipelineState.failures                     │ PipelineState.owners
        │ PipelineState.page_meta                    │ PipelineState.page_meta
        │                                            │
        ▼                                            ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│ SuggestionAgent │────▶│   RouterAgent   │────▶│  NotifierAgent │
│  (LLM reason) │     │  (confidence    │     │  (console     │
│  (sitemap)      │     │   routing)      │     │   output)     │
└───────────────┘     └───────────────┘     └───────────────┘
        │                    │                    │
        │ PipelineState.     │ PipelineState.    │ Console
        │ suggestions      │ notifications     │ emails
        │                    │                    │
        ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────┐
│                  PipelineState.audit_log                  │
│         (Immutable record of all agent decisions)       │
└─────────────────────────────────────────────────────────┘
```

## Agent Responsibilities

| Agent | Reads From State | Writes To State | External Calls |
|-------|-----------------|-----------------|---------------|
| **DiscoveryAgent** | — (reads file) | `failures` | File system |
| **ResolverAgent** | `failures[].source_page` | `page_meta` | HTTP (canonical.com) |
| **OwnerResolverAgent** | `page_meta[].copydoc_url` | `owners`, updates `page_meta` | MockGoogleDocAPI, MockDirectoryAPI |
| **SuggestionAgent** | `failures`, `page_meta` | `suggestions` | OpenRouter API, SitemapService |
| **RouterAgent** | `failures`, `suggestions`, `page_meta`, `owners` | `notifications` | HTTP (re-validation) |
| **NotifierAgent** | `notifications` | `audit_log` | Console (stdout) |

## Shared State Diagram

```
PipelineState
├── failures: List[LinkFailure]
│   ├── source_page: str
│   ├── broken_url: str
│   ├── severity: FailureSeverity
│   └── unique_id(): str
│
├── page_meta: Dict[str, PageMeta]
│   ├── url: str
│   ├── copydoc_url: Optional[str]
│   ├── title: Optional[str]
│   └── page_owner_email: Optional[str]
│
├── owners: Dict[str, Owner]
│   ├── email: str
│   ├── display_name: str
│   ├── team: str
│   └── mattermost_username: Optional[str]
│
├── suggestions: Dict[str, List[FixSuggestion]]
│   ├── original_url: str
│   ├── suggested_url: Optional[str]
│   ├── confidence: float (0.0-1.0)
│   └── reasoning: str
│
├── notifications: List[Notification]
│   ├── recipient: Owner
│   ├── subject: str
│   ├── body: str
│   ├── action_taken: RouterAction
│   └── to_console(): str
│
└── audit_log: List[AgentAuditLog]
    ├── timestamp: ISO8601
    ├── agent_name: str
    ├── action: str
    ├── input_summary: str
    └── output_summary: str
```

## Decision Tree (RouterAgent)

```
For each LinkFailure:
│
├─ Is severity TIMEOUT?
│  └─ Is link now alive (HEAD check)?
│     ├─ YES → SUPPRESS_FALSE_ALARM
│     └─ NO  → Continue...
│
├─ Is owner_email missing?
│  └─ YES → ESCALATE_OPS
│
├─ Is severity REDIRECT_CHAIN?
│  └─ YES → NOTIFY_INVESTIGATE
│
├─ Are there suggestions?
│  └─ NO → NOTIFY_INVESTIGATE
│
└─ Check top suggestion confidence:
   ├─ confidence >= 0.90 → AUTO_FIX
   ├─ confidence >= 0.60 → NOTIFY_WITH_SUGGESTION
   └─ confidence <  0.60 → NOTIFY_INVESTIGATE
```

## Notification Batching

```
Before RouterAgent:
  Failure 1 → Alice
  Failure 2 → Alice
  Failure 3 → Bob
  Failure 4 → Bob
  Failure 5 → ops (no owner)
  Failure 6 → Alice

After RouterAgent (batched by owner):
  Notification 1 (Alice): Contains Failures 1, 2, 6
  Notification 2 (Bob):   Contains Failures 3, 4
  Notification 3 (ops):   Contains Failure 5
```

## Error Handling Flow

```
Any agent encounters error:
        │
        ▼
┌───────────────┐
│ Catch exception│
│ Log error      │
│ Add audit entry│
│ with "_FAILED" │
└───────────────┘
        │
        ▼
┌───────────────┐
│ Return state   │
│ (possibly      │
│ with empty/    │
│ partial data)  │
└───────────────┘
        │
        ▼
Next agent continues
```

## File Dependencies

```
models/schemas.py (frozen)
        │
        ├───▶ agents/base.py
        │       └───▶ All agents inherit
        │
        ├───▶ services/*.py
        │       └───▶ Return/use dataclasses
        │
        ├───▶ cli.py
        │       └───▶ Creates PipelineState
        │
        └───▶ tests/*.py
                └───▶ Assert dataclass behavior
```

## Call Chain (End-to-End)

```python
# cli.py
pipeline = OrchestratorAgent([
    DiscoveryAgent("fixtures/linkchecker-output.txt"),
    ResolverAgent(HTTPClient()),
    OwnerResolverAgent(MockGoogleDocAPI(), MockDirectoryAPI()),
    SuggestionAgent(HTTPClient(), LLMClient(), SitemapService()),
    RouterAgent(),
    NotifierAgent(dry_run=True),
])

state = pipeline.run(PipelineState())
# state now contains: failures, page_meta, owners, suggestions, notifications, audit_log
```

## Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Language | Python 3.10 | Available in environment |
| HTTP | `requests` (pre-installed) | No pip needed |
| HTML Parsing | `html.parser.HTMLParser` (stdlib) | No BeautifulSoup needed |
| Data Models | `dataclasses` (stdlib) | Simple, type-safe |
| LLM | OpenRouter API | Supports multiple models |
| Cache | File-backed dict | Survives restarts |
| Config | `.env` + `os.environ` | Simple, standard |

## Performance Characteristics

| Operation | Expected Time | Notes |
|-----------|--------------|-------|
| Parse linkchecker output | < 10ms | File I/O only |
| Fetch page HTML | 1-5s | HTTP to canonical.com |
| Resolve copydoc metadata | < 1ms | File read from fixture |
| LLM suggestion call | 2-10s | OpenRouter API latency |
| Router decision | < 1ms | Local computation |
| Console output | < 10ms | Print only |
| **Total pipeline** | **5-20s** | **Dominated by LLM + HTTP** |

## Caching Strategy

```
HTTP Request
    │
    ├─ Is it GET/HEAD?
    │  └─ NO → Skip cache, make request
    │
    ├─ Is target canonical.com or localhost?
    │  └─ NO → Skip cache, make request
    │
    ├─ Check SimpleCache
    │  ├─ HIT + not expired → Return cached
    │  └─ MISS or expired → Make request
    │
    └─ Store result in cache (TTL: 1 hour)
```

## Security Considerations

- `OPENROUTER_API_KEY` is read from environment only, never hardcoded
- Cache directory `.cache/` should be in `.gitignore`
- HTTP client sends `User-Agent` identifying as bot
- No credentials stored in fixtures or logs

## Future Extensions

| Feature | Description | Priority |
|---------|-------------|----------|
| Mattermost integration | Send DMs instead of console output | High |
| Real Google Doc API | Replace mock with actual API | High |
| Real Directory API | Replace mock with actual API | High |
| Content decay scoring | Flag pages not updated in 90+ days | Medium |
| A/B test suggestion | LLM suggests headline variants | Medium |
| Scheduled runs | GitHub Actions cron job | Medium |
| Web dashboard | Streamlit UI showing agent status | Low |
| Multi-site support | Scan ubuntu.com, snapcraft.io, etc. | Low |

---

> **For AI implementers:** This architecture is designed for clarity and modularity. Each agent is independently testable. The shared state pattern allows agents to be added, removed, or reordered without changing other agents' code.