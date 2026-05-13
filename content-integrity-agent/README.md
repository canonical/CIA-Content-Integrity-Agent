# Content Integrity Agent (CIA) 🤖

> **Hackathon project:** Multi-agentic system for autonomous broken link detection, owner resolution, and intelligent fix suggestions on canonical.com.

## 📚 Documentation

| Document | Purpose | For |
|----------|---------|-----|
| **[SPEC.md](docs/SPEC.md)** | Complete technical specification | **AI implementers** — exact requirements, data models, agent behaviors, API contracts |
| **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** | Visual diagrams and data flow | **System designers** — architecture overview, decision trees, error handling |
| **[AGENTS.md](docs/AGENTS.md)** | Quick reference per agent | **Implementers** — pseudocode, expected inputs/outputs, testing strategy |
| **[FIXTURES.md](docs/FIXTURES.md)** | All mock data | **Testers** — fixture formats, expected resolution results, validation |

## 🏗️ Architecture

```
[Discovery] → [Resolver] → [OwnerResolver] → [Suggestion] → [Router] → [Notifier]
   parse        fetch          copydoc +         LLM fix       confidence   console
   links        HTML           directory         suggestion    routing      email
```

## 👥 Team Assignment

| Engineer | Role | Files | Documentation |
|----------|------|-------|---------------|
| **A** | Scaffolder + Infrastructure | `models/`, `config/`, `agents/base.py`, `agents/orchestrator.py`, `cli.py`, `utils/`, `services/http_client.py` | Read [AGENTS.md](docs/AGENTS.md) Orchestrator section |
| **B** | Discovery Chain | `agents/discovery.py`, `agents/resolver.py`, `agents/owner_resolver.py`, `fixtures/`, `utils/html_parser.py`, `services/mock_*.py` | Read [AGENTS.md](docs/AGENTS.md) Discovery/Resolver/OwnerResolver sections |
| **C** | Intelligence Layer | `services/llm_client.py`, `services/sitemap_service.py`, `agents/suggestion.py`, `agents/confidence_router.py`, `agents/notifier.py`, `agents/stubs.py` | Read [AGENTS.md](docs/AGENTS.md) Suggestion/Router/Notifier sections |

## 🚀 Quick Start

```bash
# Using run.sh (works everywhere):
./run.sh lint     # Check imports
./run.sh test     # Run all tests
./run.sh demo     # Run full pipeline

# Or using make (if available):
make lint
make test
make demo
```

## 🔧 Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your OpenRouter API key
OPENROUTER_API_KEY=sk-or-v1-...
```

If no API key is provided, the system falls back to **deterministic URL similarity matching** (Jaccard on path segments).

## 📁 Project Structure

```
content-integrity-agent/
├── cli.py                    # Entry point
├── run.sh                     # Shell runner (use if make unavailable)
├── Makefile                   # Quick commands
├── .env.example              # Environment template
├── models/                   # Data models (FROZEN)
│   └── schemas.py
├── config/                   # Settings
│   └── settings.py
├── agents/                   # Agent implementations
│   ├── base.py              # Abstract base
│   ├── orchestrator.py      # Pipeline runner
│   ├── discovery.py         # Parse linkchecker
│   ├── resolver.py          # Fetch page meta
│   ├── owner_resolver.py    # Resolve owners
│   ├── suggestion.py        # LLM suggestions
│   ├── confidence_router.py # Route decisions
│   ├── notifier.py          # Console output
│   └── stubs.py             # Future agents
├── services/                 # External API wrappers
│   ├── http_client.py       # HTTP + cache
│   ├── llm_client.py        # OpenRouter API
│   ├── sitemap_service.py   # URL similarity
│   ├── mock_google_doc_api.py
│   └── mock_directory_api.py
├── utils/                    # Utilities
│   ├── decorators.py         # Retry logic
│   ├── cache.py             # File-backed cache
│   ├── logger.py            # Structured logging
│   └── html_parser.py       # Stdlib HTML parsing
├── fixtures/                 # Mock data
│   ├── linkchecker-output.txt
│   ├── directory.json
│   ├── pages/
│   └── copydocs/
├── tests/                    # Tests
│   ├── test_contracts.py
│   └── test_e2e.py
└── docs/                     # Documentation
    ├── SPEC.md
    ├── ARCHITECTURE.md
    ├── AGENTS.md
    └── FIXTURES.md
```

## 🔄 Git Workflow

```bash
# Engineer A creates interfaces branch
git checkout -b interfaces
git push origin interfaces

# Everyone branches from interfaces
git fetch origin
git checkout -b eng2/discovery origin/interfaces   # Engineer B
git checkout -b eng3/suggestion origin/interfaces  # Engineer C

# Merge to interfaces when ready
git checkout interfaces
git merge eng2/discovery

# Final integration
git checkout main
git merge interfaces
```

## 🧪 Testing Strategy

- **Contract tests:** Verify all agents importable (`tests/test_contracts.py`)
- **Unit tests:** Per-agent tests in `tests/test_{agent}.py`
- **End-to-end test:** Full pipeline with fixtures (`tests/test_e2e.py`)

## ⚠️ Rules

1. **`models/schemas.py` is FROZEN** after hour 0 — Engineer A owns exclusively
2. **File ownership is strict** — don't touch another engineer's files
3. **All agents inherit from `BaseAgent`** and implement `run(state) -> state`
4. **Contract tests must pass** before merging
5. **Never crash the pipeline** — handle errors gracefully

## 🎯 Success Criteria

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

## 📊 Performance

| Operation | Expected Time |
|-----------|--------------|
| Parse linkchecker output | < 10ms |
| Fetch page HTML | 1-5s |
| Resolve copydoc metadata | < 1ms |
| LLM suggestion call | 2-10s |
| Router decision | < 1ms |
| Console output | < 10ms |
| **Total pipeline** | **5-20s** |

## 🔮 Future Extensions

- Mattermost integration (send DMs instead of console)
- Real Google Doc API + Directory API
- Content decay scoring (flag pages not updated in 90+ days)
- A/B test content suggestions
- Scheduled runs via GitHub Actions
- Web dashboard (Streamlit)

---

> **For AI implementers:** Start with [SPEC.md](docs/SPEC.md) for complete technical details. Use [AGENTS.md](docs/AGENTS.md) for quick reference while implementing.