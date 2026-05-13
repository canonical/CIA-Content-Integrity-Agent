from flask import Blueprint, request, jsonify
from api.extensions import db
from api.models import Site

sites_bp = Blueprint("sites", __name__)


@sites_bp.route("", methods=["GET"])
def list_sites():
    sites = Site.query.order_by(Site.created_at.desc()).all()
    return jsonify([s.to_dict() for s in sites])


@sites_bp.route("", methods=["POST"])
def create_site():
    data = request.get_json()
    if not data or not data.get("name") or not data.get("base_url"):
        return jsonify({"error": "name and base_url are required"}), 400

    base_url = data["base_url"].rstrip("/")
    sitemap_url = data.get("sitemap_url", f"{base_url}/sitemap.xml")

    existing = Site.query.filter_by(base_url=base_url).first()
    if existing:
        return jsonify({"error": "site with this base_url already exists", "detail": f"site id={existing.id}"}), 409

    site = Site(name=data["name"], base_url=base_url, sitemap_url=sitemap_url)
    db.session.add(site)
    db.session.commit()
    return jsonify(site.to_dict()), 201


@sites_bp.route("/<int:site_id>", methods=["GET"])
def get_site(site_id):
    site = Site.query.get_or_404(site_id)
    return jsonify(site.to_dict())


@sites_bp.route("/<int:site_id>", methods=["DELETE"])
def delete_site(site_id):
    site = Site.query.get_or_404(site_id)
    db.session.delete(site)
    db.session.commit()
    return "", 204
