from flask import Blueprint, jsonify
from api.models import Site
from api.services.sitemap_fetcher import SitemapFetcher
from services.http_client import HTTPClient

sitemaps_bp = Blueprint("sitemaps", __name__)

_http_client = HTTPClient()
_fetcher = SitemapFetcher(_http_client)


@sitemaps_bp.route("/<int:site_id>/urls", methods=["GET"])
def get_site_urls(site_id):
    site = Site.query.get_or_404(site_id)

    cached = _http_client.cache.get(site.sitemap_url)
    if cached is not None:
        import json
        try:
            return jsonify(json.loads(cached))
        except (json.JSONDecodeError, TypeError):
            pass

    urls = _fetcher.fetch_urls(site.sitemap_url)
    if not urls:
        return jsonify({"error": "could not fetch sitemap", "detail": site.sitemap_url}), 502

    import json
    _http_client.cache.set(site.sitemap_url, json.dumps(urls))

    return jsonify(urls)