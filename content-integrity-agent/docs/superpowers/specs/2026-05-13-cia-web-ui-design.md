# CIA Web UI — Site Selector & Route Scanner Design

> **Version:** 1.0  
> **Date:** 2026-05-13  
> **Status:** Approved

## 1. Summary

Add a web UI to the Content Integrity Agent that allows users to:

1. Register multiple sites (by base URL + sitemap URL)
2. Browse a site's URLs parsed from its remote `sitemap.xml`
3. Pick a route/page and trigger an active content integrity scan
4. View full pipeline results (broken links, suggestions, notifications, audit log) with real-time progress

## 2. Architecture

**Approach:** Flask API + React SPA with WebSocket progress (Approach A)

```
React SPA (Vite + TypeScript + Tailwind)
    │ REST + WebSocket (Flask-SocketIO)
Flask API
    ├── Sites API (/api/sites)
    ├── Sitemap API (/api/sites/:id/urls)
    ├── Scans API (/api/scans)
    ├── PipelineService (wraps existing CIA pipeline)
    └── SitemapFetcher (fetches + parses remote sitemap.xml)
    │
SQLite (sites + scans)
    │
Existing CIA agents + services (unchanged)
```

**New directories:**

```
content-integrity-agent/
├── api/
│   ├── app.py
│   ├── routes/
│   │   ├── sites.py
│   │   ├── sitemaps.py
│   │   └── scans.py
│   ├── models.py          # SQLAlchemy models
│   └── services/
│       ├── pipeline_service.py
│       └── sitemap_fetcher.py
├── web/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── api/
│   └── package.json
├── agents/               # Existing (unchanged)
├── services/             # Existing (extended)
└── cli.py               # Existing (unchanged)
```

## 3. Data Model

### Site (SQLite)

| Field | Type | Notes |
|-------|------|-------|
| id | INTEGER PK | Auto |
| name | TEXT | Display name |
| base_url | TEXT | e.g. `https://canonical.com` |
| sitemap_url | TEXT | e.g. `https://canonical.com/sitemap.xml` |
| created_at | DATETIME | |
| last_scanned_at | DATETIME | Nullable |

### Scan (SQLite)

| Field | Type | Notes |
|-------|------|-------|
| id | INTEGER PK | Auto |
| site_id | INTEGER FK | → sites.id |
| route_url | TEXT | The page URL scanned |
| status | TEXT | `pending` / `crawling` / `analyzing` / `suggesting` / `routing` / `complete` / `failed` / `cancelled` |
| progress | INTEGER | 0–100 |
| current_agent | TEXT | Which agent is running |
| results | TEXT | JSON blob (serialized PipelineState) |
| error_message | TEXT | Nullable |
| created_at | DATETIME | |
| completed_at | DATETIME | Nullable |

**Key decisions:**

- `scan.results` is a JSON blob rather than normalized tables — keeps it simple and maps directly to the existing `PipelineState` dataclasses (serialized via `dataclasses.asdict`)
- `scan.status` maps to pipeline stages so the UI can show "Running DiscoveryAgent..." style progress
- One scan = one route/page. User can kick off multiple scans for different routes concurrently

## 4. API Design

### REST Endpoints

**Sites**

```
GET    /api/sites              → list all sites
POST   /api/sites              → add site {name, base_url, sitemap_url?}
GET    /api/sites/:id          → get site detail
DELETE /api/sites/:id          → remove site
```

- `sitemap_url` is optional on creation — defaults to `{base_url}/sitemap.xml`

**Sitemaps**

```
GET    /api/sites/:id/urls     → fetch cached/remote sitemap URLs
```

- Fetches remote `sitemap.xml`, parses all `<loc>` entries, returns as JSON array of `{url, lastmod?}`
- Handles sitemap indexes: follows child sitemap URLs up to 3 levels deep, max 10,000 URLs per site
- Cached per site (TTL: 1 hour, uses existing SimpleCache)

**Scans**

```
POST   /api/scans              → start scan {site_id, route_url}
GET    /api/scans              → list scans (optional ?site_id= filter)
GET    /api/scans/:id          → get scan detail + results
DELETE /api/scans/:id          → cancel in-progress scan
```

- `POST /api/scans` kicks off the pipeline in a background thread, returns the scan record immediately with `status: "pending"`
- `GET /api/scans/:id` returns current status, progress, current_agent, and results (if complete)
- `DELETE /api/scans/:id` sets status to `"cancelled"` if scan is still running; no-op if already complete

### WebSocket Events

**Server → Client (progress updates)**

```
scan:progress  → {scan_id, status, progress, current_agent}
scan:complete  → {scan_id, results: {...}}
scan:failed    → {scan_id, error_message}
```

**Client → Server (join scan room)**

```
scan:subscribe   → {scan_id}
scan:unsubscribe → {scan_id}
```

- Each scan gets a SocketIO "room" so progress events only go to clients viewing that scan
- The `PipelineService` emits progress events after each agent completes
- Client auto-subscribes when navigating to the scan results page

## 5. Pipeline Integration

### PipelineService

Wraps the existing agent pipeline for web use:

1. Accepts a `route_url` instead of a linkchecker file path
2. **Crawl phase:** fetches the page HTML, extracts links from `<a href>`, `<img src>`, `<link href>`, `<script src>` tags
3. **Link check phase:** HEAD-requests each extracted link, records failures as `LinkFailure` objects with appropriate severity
4. **Pipeline phase:** feeds the `LinkFailure` list into the existing agent chain: ResolverAgent → OwnerResolverAgent → SuggestionAgent → RouterAgent → NotifierAgent
5. Emits WebSocket progress events after each agent completes
6. Serializes final `PipelineState` to JSON and stores in `scan.results`

### SitemapFetcher

- Fetches remote `sitemap.xml` via HTTPClient
- Parses XML, extracts all `<loc>` and `<lastmod>` entries
- Handles sitemap indexes (nested `<sitemap>` elements) by recursively following child sitemap URLs, up to 3 levels deep, capped at 10,000 URLs total per site
- Caches results for 1 hour (reuses existing SimpleCache)
- Returns list of `{url: str, lastmod: Optional[str]}`

## 6. React Frontend

### Pages & Navigation

Sidebar navigation with 3 pages:

1. **Sites** — list of registered sites as cards (name, base_url, last_scanned_at), "Add Site" button opens a modal/form (name, base_url, sitemap_url auto-filled but editable), click a site → navigates to Sitemap Browser, delete site with confirmation

2. **Sitemap Browser** — header shows site name + base_url, URL list fetched from `GET /api/sites/:id/urls` displayed as searchable/filterable table with columns: URL, path (extracted from URL), lastmod, "Scan" button per row that triggers `POST /api/scans` and navigates to Scan Results

3. **Scan Results** — header shows route_url + status badge, progress phase shows real-time progress bar + current agent name (via WebSocket), complete phase shows tabbed results: Broken Links (table of LinkFailures), Suggestions (table with confidence bars), Notifications (drafted notification previews), Audit Log (chronological agent decisions), sidebar lists recent scans for this site (clickable to switch)

### Tech Stack

- **Vite** for build tooling
- **TypeScript**
- **React Router** for navigation
- **TanStack Query** for API fetching + caching
- **socket.io-client** for WebSocket
- **Tailwind CSS** for styling
- No component library — keep it lean

### CORS Configuration

- Dev mode: Flask-CORS enabled with `origins: ["http://localhost:5173"]`
- Dev mode: Vite proxy configuration forwards `/api` and `/socket.io` to `:5000`
- Production: Flask serves static files from `web/dist/` directly — no CORS needed

## 7. Error Handling

**Backend:**

- Sitemap fetch failures (timeout, 404, invalid XML) → return 502 with error detail, UI shows "Could not fetch sitemap" with retry button
- Scan failures (page unreachable, LLM API down) → scan status set to `"failed"`, `error_message` populated, WebSocket emits `scan:failed`
- All API errors return structured JSON: `{error: string, detail?: string}`
- Pipeline agents already handle errors gracefully (existing spec) — `PipelineService` catches any unhandled exception and marks scan as failed

**Frontend:**

- TanStack Query handles fetch errors with retry + error boundaries
- WebSocket disconnection → "Reconnecting..." banner, auto-reconnect via `socket.io-client`
- Stalled scans (no progress update for 60s) → "Scan may be stuck" warning with cancel option
- 429 / rate-limit from target sites → show "Rate limited, retry later" message

## 8. Testing Strategy

**Backend:**

- `api/tests/test_sites_api.py` — CRUD endpoints, validation, duplicate prevention
- `api/tests/test_scans_api.py` — scan trigger, status polling, cancellation, WebSocket event emission mock
- `api/tests/test_pipeline_service.py` — integration: PipelineService wraps existing agents correctly, emits progress events, serializes results
- `api/tests/test_sitemap_fetcher.py` — parse valid/invalid sitemap XML, handle sitemap indexes, respect URL cap, cache behavior

**Frontend:**

- Vitest + React Testing Library for component tests
- Key scenarios: site form submission + validation, URL list rendering + search/filter, scan progress display via mocked WebSocket, results tabs rendering

**Existing tests:**

- `tests/test_e2e.py` continues to work for CLI path — unchanged
- New smoke test: `GET /api/health` returns 200 when Flask is running

## 9. Running the App

```bash
# Backend
cd content-integrity-agent
pip install flask flask-sqlalchemy flask-socketio flask-cors
python -m api.app                        # starts on :5000

# Frontend dev
cd content-integrity-agent/web
npm install
npm run dev                              # Vite dev server on :5173, proxies /api → :5000

# Production build
cd content-integrity-agent/web
npm run build                            # outputs to web/dist/
# Flask serves web/dist/ as static files in production mode

# Shortcut (both at once)
make web
```

- SQLite DB file at `content-integrity-agent/data/cia.db` (gitignored)
- Add `data/` to `.gitignore`

## 10. Success Criteria

- [ ] User can register a site via the UI and see it in the sites list
- [ ] User can browse a site's sitemap URLs (fetched from remote sitemap.xml)
- [ ] User can pick a route and trigger a content integrity scan
- [ ] Scan progress updates appear in real-time via WebSocket
- [ ] Completed scans show broken links, suggestions, notifications, and audit log in tabbed view
- [ ] Existing CLI pipeline (`python cli.py`) still works unchanged
- [ ] All backend API tests pass
- [ ] All frontend component tests pass
