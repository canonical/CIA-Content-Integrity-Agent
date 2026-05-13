import json


def test_list_sites_empty(client):
    resp = client.get("/api/sites")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_create_site(client):
    resp = client.post("/api/sites", json={
        "name": "Canonical",
        "base_url": "https://canonical.com",
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["name"] == "Canonical"
    assert data["base_url"] == "https://canonical.com"
    assert data["sitemap_url"] == "https://canonical.com/sitemap.xml"
    assert data["id"] is not None


def test_create_site_custom_sitemap(client):
    resp = client.post("/api/sites", json={
        "name": "Ubuntu",
        "base_url": "https://ubuntu.com",
        "sitemap_url": "https://ubuntu.com/sitemap_index.xml",
    })
    assert resp.status_code == 201
    assert resp.get_json()["sitemap_url"] == "https://ubuntu.com/sitemap_index.xml"


def test_create_site_missing_fields(client):
    resp = client.post("/api/sites", json={"name": "No URL"})
    assert resp.status_code == 400


def test_create_site_duplicate(client):
    client.post("/api/sites", json={"name": "A", "base_url": "https://a.com"})
    resp = client.post("/api/sites", json={"name": "A2", "base_url": "https://a.com"})
    assert resp.status_code == 409


def test_get_site(client):
    create_resp = client.post("/api/sites", json={"name": "X", "base_url": "https://x.com"})
    site_id = create_resp.get_json()["id"]
    resp = client.get(f"/api/sites/{site_id}")
    assert resp.status_code == 200
    assert resp.get_json()["name"] == "X"


def test_get_site_not_found(client):
    resp = client.get("/api/sites/999")
    assert resp.status_code == 404


def test_delete_site(client):
    create_resp = client.post("/api/sites", json={"name": "Y", "base_url": "https://y.com"})
    site_id = create_resp.get_json()["id"]
    resp = client.delete(f"/api/sites/{site_id}")
    assert resp.status_code == 204
    assert client.get(f"/api/sites/{site_id}").status_code == 404
