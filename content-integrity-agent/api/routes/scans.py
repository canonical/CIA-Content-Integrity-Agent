import json
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from api.extensions import db, socketio
from api.models import Scan, Site
from api.services.pipeline_service import PipelineService

scans_bp = Blueprint("scans", __name__)


def _emit_progress(scan_id, status, progress, current_agent, error_message=None):
    socketio.emit("scan:progress", {
        "scan_id": scan_id,
        "status": status,
        "progress": progress,
        "current_agent": current_agent,
    }, room=f"scan_{scan_id}")

    if status == "complete":
        socketio.emit("scan:complete", {"scan_id": scan_id}, room=f"scan_{scan_id}")
    elif status == "failed":
        socketio.emit("scan:failed", {
            "scan_id": scan_id,
            "error_message": error_message or "Unknown error",
        }, room=f"scan_{scan_id}")


def _run_scan_background(scan_id: int, route_url: str):
    service = PipelineService()

    def on_progress(sid, status, progress, current_agent, error_message=None):
        scan = Scan.query.get(sid)
        if scan is None:
            return
        scan.status = status
        scan.progress = progress
        scan.current_agent = current_agent
        if status == "complete":
            scan.completed_at = datetime.now(timezone.utc)
        if error_message:
            scan.error_message = error_message
        db.session.commit()
        _emit_progress(sid, status, progress, current_agent, error_message)

    try:
        results = service.run_scan(route_url, scan_id, on_progress=on_progress)
        scan = Scan.query.get(scan_id)
        if scan and scan.status != "failed":
            scan.status = "complete"
            scan.progress = 100
            scan.results = json.dumps(results)
            scan.completed_at = datetime.now(timezone.utc)
            site = Site.query.get(scan.site_id)
            if site:
                site.last_scanned_at = datetime.now(timezone.utc)
            db.session.commit()
            _emit_progress(scan_id, "complete", 100, None)
    except Exception as exc:
        scan = Scan.query.get(scan_id)
        if scan:
            scan.status = "failed"
            scan.error_message = str(exc)
            scan.completed_at = datetime.now(timezone.utc)
            db.session.commit()
            _emit_progress(scan_id, "failed", 0, None, str(exc))


@scans_bp.route("", methods=["POST"])
def create_scan():
    data = request.get_json()
    if not data or not data.get("site_id") or not data.get("route_url"):
        return jsonify({"error": "site_id and route_url are required"}), 400

    site = Site.query.get(data["site_id"])
    if not site:
        return jsonify({"error": "site not found"}), 404

    scan = Scan(
        site_id=site.id,
        route_url=data["route_url"],
        status="pending",
        progress=0,
    )
    db.session.add(scan)
    db.session.commit()

    socketio.start_background_task(_run_scan_background, scan.id, data["route_url"])

    return jsonify(scan.to_dict()), 201


@scans_bp.route("", methods=["GET"])
def list_scans():
    site_id = request.args.get("site_id", type=int)
    query = Scan.query
    if site_id:
        query = query.filter_by(site_id=site_id)
    scans = query.order_by(Scan.created_at.desc()).all()
    return jsonify([s.to_dict() for s in scans])


@scans_bp.route("/<int:scan_id>", methods=["GET"])
def get_scan(scan_id):
    scan = Scan.query.get_or_404(scan_id)
    include = request.args.get("include") == "results"
    return jsonify(scan.to_dict(include_results=include))


@scans_bp.route("/<int:scan_id>", methods=["DELETE"])
def cancel_scan(scan_id):
    scan = Scan.query.get_or_404(scan_id)
    if scan.status in ("complete", "failed", "cancelled"):
        return jsonify(scan.to_dict())

    scan.status = "cancelled"
    scan.completed_at = datetime.now(timezone.utc)
    scan.error_message = "Cancelled by user"
    db.session.commit()
    _emit_progress(scan_id, "failed", scan.progress, None, "Cancelled by user")
    return jsonify(scan.to_dict())


@socketio.on("scan:subscribe")
def on_scan_subscribe(data):
    from flask_socketio import join_room
    join_room(f"scan_{data['scan_id']}")


@socketio.on("scan:unsubscribe")
def on_scan_unsubscribe(data):
    from flask_socketio import leave_room
    leave_room(f"scan_{data['scan_id']}")