from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from ..models import db, Broadcast, ClubMember, create_notification
from ..utils import current_user, role_required, get_owned_club_or_403

broadcasts_bp = Blueprint("broadcasts", __name__, url_prefix="/api/clubs")


@broadcasts_bp.route("/<int:club_id>/broadcasts", methods=["GET"])
@jwt_required()
def list_broadcasts(club_id):
    bs = Broadcast.query.filter_by(club_id=club_id).order_by(Broadcast.created_at.desc()).all()
    return jsonify([b.to_dict() for b in bs])


@broadcasts_bp.route("/<int:club_id>/broadcasts", methods=["POST"])
@role_required("ClubLead")
def create_broadcast(club_id):
    club, err = get_owned_club_or_403(club_id)
    if err:
        return err
    data = request.get_json(silent=True) or {}
    if not data.get("title"):
        return jsonify({"error": "Title is required"}), 400
    b = Broadcast(
        club_id=club.id, title=data.get("title"), message=data.get("message"),
        target_audience=data.get("targetAudience") or "All Club Members",
        publish_date=data.get("publishDate"), expiry_date=data.get("expiryDate"),
        created_by=current_user().id,
    )
    db.session.add(b)
    audience = data.get("targetAudience") or "All Club Members"
    members = ClubMember.query.filter_by(club_id=club.id, status="Approved").all()
    for m in members:
        if audience in ("All Club Members", "Event Participants") or m.role == audience:
            create_notification(m.user_id, f"New broadcast: {b.title}",
                                b.message or "", "broadcast", club.id, str(b.id))
    db.session.commit()
    return jsonify(b.to_dict()), 201
