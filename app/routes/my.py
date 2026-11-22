from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from ..models import (Club, ClubMember, ClubMembershipRequest, Event, EventRegistration,
                      Project, Broadcast)
from ..utils import current_user

my_bp = Blueprint("my", __name__, url_prefix="/api/my")


@my_bp.route("/clubs", methods=["GET"])
@jwt_required()
def my_clubs():
    """Approved club memberships for the current user, incl. full club detail."""
    user = current_user()
    members = ClubMember.query.filter_by(user_id=user.id, status="Approved").all()
    out = []
    for m in members:
        club = Club.query.get(m.club_id)
        if not club:
            continue
        d = club.to_dict()
        d["myRole"] = m.role
        d["joinedAt"] = m.joined_at.isoformat() if m.joined_at else None
        d["projects"] = [p.to_dict() for p in Project.query.filter_by(club_id=club.id).all()]
        d["events"] = [e.to_dict() for e in Event.query.filter_by(club_id=club.id).all()]
        d["updates"] = [b.to_dict() for b in Broadcast.query.filter_by(club_id=club.id).order_by(Broadcast.created_at.desc()).all()]
        out.append(d)
    return jsonify(out)


@my_bp.route("/registrations", methods=["GET"])
@jwt_required()
def my_registrations():
    user = current_user()
    regs = EventRegistration.query.filter_by(user_id=user.id).order_by(
        EventRegistration.registered_at.desc()).all()
    out = []
    for r in regs:
        ev = Event.query.get(r.event_id)
        d = r.to_dict()
        d["event"] = ev.to_dict() if ev else None
        out.append(d)
    return jsonify(out)


@my_bp.route("/membership-status/<int:club_id>", methods=["GET"])
@jwt_required()
def membership_status(club_id):
    user = current_user()
    member = ClubMember.query.filter_by(club_id=club_id, user_id=user.id, status="Approved").first()
    if member:
        return jsonify({"status": "Approved", "role": member.role})
    req = ClubMembershipRequest.query.filter_by(club_id=club_id, user_id=user.id).order_by(
        ClubMembershipRequest.submitted_at.desc()).first()
    if req:
        return jsonify({"status": req.status, "role": req.requested_role})
    return jsonify({"status": "Not Applied"})


@my_bp.route("/led-club", methods=["GET"])
@jwt_required()
def led_club():
    """The club led by the current user (for ClubLead control panel)."""
    user = current_user()
    club = Club.query.filter_by(club_leader_id=user.id).first()
    if not club:
        return jsonify({"club": None})
    return jsonify({"club": club.to_dict()})
