# Content Integrity Agent (CIA) 🤖

> **Hackathon project:** Multi-agentic system for autonomous broken link detection, owner resolution, and intelligent fix suggestions on canonical.com.

## Architecture

```
[Discovery] → [Resolver] → [OwnerResolver] → [Suggestion] → [Router] → [Notifier]
   parse        fetch          copydoc +         LLM fix       confidence   console
   links        HTML           directory         suggestion    routing      email
```

## Team Assignment

| Engineer | Role | Files |
|----------|------|-------|
| **A** | Scaffolder + Infrastructure | `models/`, `config/`, `agents/base.py`, `agents/orchestrator.py`, `cli.py`, `utils/`, `services/http_client.py` |
| **B** | Discovery Chain | `agents/discovery.py`, `agents/resolver.py`, `agents/owner_resolver.py`, `fixtures/`, `utils/html_parser.py` |
| **C** | Intelligence Layer | `services/llm_client.py`, `services/sitemap_service.py`, `agents/suggestion.py`, `agents/confidence_router.py`, `agents/notifier.py`, `agents/stubs.py` |

## Quick Start

```bash
# Check imports work
make lint

# Run contract tests
make test

# Run demo (once implemented)
make demo
```

## Git Workflow

```bash
# Engineer A creates interfaces branch
git checkout -b interfaces
git push origin interfaces

# Everyone branches from interfaces
git fetch origin
git checkout -b eng2/discovery origin/interfaces  # Engineer B
git checkout -b eng3/suggestion origin/interfaces  # Engineer C

# Merge to main when ready
git checkout main
git merge interfaces
```

## Environment Setup

```bash
cp .env.example .env
# Edit .env with your OPENROUTER_API_KEY
```

## Rules

1. **`models/schemas.py` is FROZEN** after hour 0 - Engineer A owns it exclusively
2. **File ownership is strict** - don't touch another engineer's exclusive files
3. **All agents inherit from `BaseAgent`** and implement `run(state) -> state`
4. **Contract tests must pass** before merging

## Status

- [x] Interface contracts defined
- [ ] DiscoveryAgent implementation
- [ ] ResolverAgent implementation
- [ ] OwnerResolverAgent implementation
- [ ] SuggestionAgent implementation
- [ ] RouterAgent implementation
- [ ] NotifierAgent implementation
- [ ] OrchestratorAgent implementation
- [ ] End-to-end test passing