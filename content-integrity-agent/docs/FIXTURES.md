# Fixture Data Reference

> Complete mock data for testing and demo purposes. All fixtures are deterministic and version-controlled.

## Directory Structure

```
fixtures/
├── linkchecker-output.txt          # 6 broken links across 4 pages
├── directory.json                  # 5 user records
├── pages/
│   ├── data.html                   # /data page with copydoc
│   ├── kubernetes.html             # /kubernetes page with copydoc
│   ├── microk8s.html               # /microk8s page with copydoc
│   └── openstack.html              # /openstack page with copydoc
└── copydocs/
    ├── doc_1QKc7tH.json           # /data copydoc metadata
    ├── doc_aBcDeFg.json           # /kubernetes copydoc metadata
    ├── doc_xYz123.json            # /microk8s copydoc metadata
    └── doc_mNoPqR.json            # /openstack copydoc metadata
```

---

## Linkchecker Output

**File:** `fixtures/linkchecker-output.txt`

```text
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

### Parsed Result

| # | broken_url | source_page | line | error | severity |
|---|-----------|-------------|------|-------|----------|
| 1 | /old-data-docs | /data | 42 | 404 Not Found | CRITICAL_404 |
| 2 | /deprecated-api/v1 | /kubernetes | 120 | 404 Not Found | CRITICAL_404 |
| 3 | /microk8s/legacy-install | /microk8s | 88 | 404 Not Found | CRITICAL_404 |
| 4 | /openstack/old-pricing | /openstack | 55 | 404 Not Found | CRITICAL_404 |
| 5 | /broken-timeout-example | /data | 140 | Connection timeout | TIMEOUT |
| 6 | /too-many-redirects | /microk8s | 200 | Too many redirects | REDIRECT_CHAIN |

---

## Directory API

**File:** `fixtures/directory.json`

### User Records

| email | display_name | team | department | mattermost |
|-------|-------------|------|------------|------------|
| alice.chen@canonical.com | Alice Chen | Data Platform Engineering | Engineering | alice.chen |
| bob.smith@canonical.com | Bob Smith | Cloud Native | Engineering | bob.smith |
| diana.prince@canonical.com | Diana Prince | Edge & IoT | Engineering | diana.prince |
| eve.davis@canonical.com | Eve Davis | Private Cloud | Engineering | eve.davis |
| ops-team@canonical.com | Content Ops Team | Web Operations | Marketing | content-ops |

### Resolution Mapping

| Page | Copydoc Owner | Directory Lookup | Result |
|------|--------------|------------------|--------|
| /data | alice.chen | Alice Chen | Success |
| /kubernetes | bob.smith | Bob Smith | Success |
| /microk8s | diana.prince | Diana Prince | Success |
| /openstack | eve.davis | Eve Davis | Success |
| (any missing) | ops-team | Content Ops Team | Fallback |

---

## Google Doc Metadata

### /data Page

**File:** `fixtures/copydocs/doc_1QKc7tH.json`

```json
{
    "doc_id": "1QKc7tHZZSJttrPOziK_w_9yKLLgoC4Vcufke9dSvQ-g",
    "title": "Canonical Data Solutions — Copydoc",
    "owner_email": "alice.chen@canonical.com",
    "last_modified": "2024-12-15T10:30:00Z",
    "contributors": [
        "alice.chen@canonical.com",
        "bob.smith@canonical.com"
    ]
}
```

### /kubernetes Page

**File:** `fixtures/copydocs/doc_aBcDeFg.json`

```json
{
    "doc_id": "aBcDeFgHiJkLmNoPqRsTuV",
    "title": "Kubernetes on Ubuntu — Copydoc",
    "owner_email": "bob.smith@canonical.com",
    "last_modified": "2024-11-20T14:00:00Z",
    "contributors": [
        "bob.smith@canonical.com"
    ]
}
```

### /microk8s Page

**File:** `fixtures/copydocs/doc_xYz123.json`

```json
{
    "doc_id": "xYz123AbCDeFgHiJkLm",
    "title": "MicroK8s — Copydoc",
    "owner_email": "diana.prince@canonical.com",
    "last_modified": "2024-10-05T09:15:00Z",
    "contributors": [
        "diana.prince@canonical.com",
        "eve.davis@canonical.com"
    ]
}
```

### /openstack Page

**File:** `fixtures/copydocs/doc_mNoPqR.json`

```json
{
    "doc_id": "mNoPqRsTuVwXyZ123AbC",
    "title": "OpenStack — Copydoc",
    "owner_email": "eve.davis@canonical.com",
    "last_modified": "2024-09-01T16:45:00Z",
    "contributors": [
        "eve.davis@canonical.com"
    ]
}
```

---

## HTML Page Fixtures

### /data Page

**File:** `fixtures/pages/data.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="description" content="Get support for your open source data platform." />
    <meta name="copydoc" content="https://docs.google.com/document/d/1QKc7tHZZSJttrPOziK_w_9yKLLgoC4Vcufke9dSvQ-g/edit" />
    <meta name="author" content="Canonical Ltd" />
    <title>Canonical open source data platform solutions</title>
    <link rel="canonical" href="https://canonical.com/data" />
</head>
<body>
    <h1>Data Solutions</h1>
    <a href="https://canonical.com/old-data-docs">Old docs (BROKEN)</a>
    <a href="https://canonical.com/data/docs">New docs</a>
</body>
</html>
```

### /kubernetes Page

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

### /microk8s Page

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

### /openstack Page

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

---

## Expected Resolution Results

After all agents run on these fixtures:

| Page | Broken Links | Owner | Suggestions | Router Decision |
|------|-------------|-------|-------------|----------------|
| /data | /old-data-docs (404), /broken-timeout-example (timeout) | Alice | /data/docs (high), None (low) | NOTIFY_WITH_SUGGESTION |
| /kubernetes | /deprecated-api/v1 (404) | Bob | None (low) | NOTIFY_INVESTIGATE |
| /microk8s | /microk8s/legacy-install (404), /too-many-redirects | Diana | /microk8s/docs (high), None | NOTIFY_WITH_SUGGESTION |
| /openstack | /openstack/old-pricing (404) | Eve | /openstack/pricing (high) | AUTO_FIX |

**Expected notifications:** 4 (one per owner)

---

## Adding New Fixtures

To add a new test scenario:

1. **Add linkchecker entry** to `fixtures/linkchecker-output.txt`
2. **Create page fixture** in `fixtures/pages/{name}.html` with `<meta name="copydoc">`
3. **Create copydoc** in `fixtures/copydocs/doc_{id}.json`
4. **Add owner** to `fixtures/directory.json`
5. **Update sitemap** in `services/sitemap_service.py` `_url_index`

---

## Fixture Validation

Run this to verify all fixtures are parseable:
```python
import json

# Test directory
with open("fixtures/directory.json") as f:
    data = json.load(f)
    assert len(data["users"]) == 5

# Test copydocs
import glob
for path in glob.glob("fixtures/copydocs/doc_*.json"):
    with open(path) as f:
        data = json.load(f)
        assert "doc_id" in data
        assert "owner_email" in data

# Test pages
import glob
for path in glob.glob("fixtures/pages/*.html"):
    with open(path) as f:
        html = f.read()
        assert '<meta name="copydoc"' in html

print("✅ All fixtures valid")
```