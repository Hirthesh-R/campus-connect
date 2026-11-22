from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from ..models import Club, ClubMember, Project, Event, Broadcast

clubs_bp = Blueprint("clubs", __name__, url_prefix="/api/clubs")


@clubs_bp.route("", methods=["GET"])
@jwt_required()
def list_clubs():
    return jsonify([c.to_dict() for c in Club.query.all()])


@clubs_bp.route("/<int:club_id>", methods=["GET"])
@jwt_required()
def get_club(club_id):
    club = Club.query.get(club_id)
    if not club:
        return jsonify({"error": "Club not found"}), 404
    data = club.to_dict()
    data["projects"] = [p.to_dict() for p in Project.query.filter_by(club_id=club_id).all()]
    data["events"] = [e.to_dict() for e in Event.query.filter_by(club_id=club_id).all()]
    data["updates"] = [b.to_dict() for b in Broadcast.query.filter_by(club_id=club_id).order_by(Broadcast.created_at.desc()).all()]
    return jsonify(data)


@clubs_bp.route("/<int:club_id>/members", methods=["GET"])
@jwt_required()
def club_members(club_id):
    members = ClubMember.query.filter_by(club_id=club_id, status="Approved").all()
    return jsonify([m.to_dict() for m in members])


@clubs_bp.route("/<int:club_id>/projects", methods=["GET"])
@jwt_required()
def club_projects(club_id):
    return jsonify([p.to_dict() for p in Project.query.filter_by(club_id=club_id).all()])
