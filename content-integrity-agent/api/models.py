from datetime import datetime, timezone

from api.extensions import db


class Site(db.Model):
    __tablename__ = "sites"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text, nullable=False)
    base_url = db.Column(db.Text, nullable=False, unique=True)
    sitemap_url = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_scanned_at = db.Column(db.DateTime, nullable=True)

    scans = db.relationship("Scan", backref="site", lazy="select", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Site id={self.id} name={self.name!r}>"

    def __repr__(self):
        return f"<Site id={self.id} name={self.name!r}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "base_url": self.base_url,
            "sitemap_url": self.sitemap_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_scanned_at": self.last_scanned_at.isoformat() if self.last_scanned_at else None,
        }


class Scan(db.Model):
    __tablename__ = "scans"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    site_id = db.Column(db.Integer, db.ForeignKey("sites.id"), nullable=False, index=True)
    route_url = db.Column(db.Text, nullable=False)
    status = db.Column(db.Text, default="pending", nullable=False)
    progress = db.Column(db.Integer, default=0, nullable=False)
    current_agent = db.Column(db.Text, nullable=True)
    results = db.Column(db.Text, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<Scan id={self.id} site_id={self.site_id} status={self.status!r}>"

    def to_dict(self, include_results=False):
        d = {
            "id": self.id,
            "site_id": self.site_id,
            "route_url": self.route_url,
            "status": self.status,
            "progress": self.progress,
            "current_agent": self.current_agent,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
        if include_results and self.results:
            import json

            try:
                d["results"] = json.loads(self.results)
            except (json.JSONDecodeError, TypeError):
                d["results"] = None
        return d

