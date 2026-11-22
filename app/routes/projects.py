from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from ..models import db, Project
from ..utils import current_user, role_required, get_owned_club_or_403

projects_bp = Blueprint("projects", __name__, url_prefix="/api/clubs")


@projects_bp.route("/<int:club_id>/projects", methods=["POST"])
@role_required("ClubLead")
def create_project(club_id):
    club, err = get_owned_club_or_403(club_id)
    if err:
        return err
    data = request.get_json(silent=True) or {}
    if not data.get("name"):
        return jsonify({"error": "Project name is required"}), 400
    p = Project(
        club_id=club.id, name=data.get("name"), description=data.get("description"),
        technologies=data.get("technologies"), status=data.get("status") or "Active",
        start_date=data.get("startDate"), expected_completion=data.get("expectedCompletion"),
        team=data.get("team"), created_by=current_user().id,
    )
    db.session.add(p)
    db.session.commit()
    return jsonify(p.to_dict()), 201


@projects_bp.route("/<int:club_id>/projects/<int:project_id>", methods=["PUT"])
@role_required("ClubLead")
def update_project(club_id, project_id):
    club, err = get_owned_club_or_403(club_id)
    if err:
        return err
    p = Project.query.filter_by(id=project_id, club_id=club.id).first()
    if not p:
        return jsonify({"error": "Project not found"}), 404
    data = request.get_json(silent=True) or {}
    for attr, key in [("name", "name"), ("description", "description"),
                      ("technologies", "technologies"), ("status", "status"),
                      ("start_date", "startDate"), ("expected_completion", "expectedCompletion"),
                      ("team", "team")]:
        if key in data and data.get(key) is not None:
            setattr(p, attr, data.get(key))
    db.session.commit()
    return jsonify(p.to_dict())


@projects_bp.route("/<int:club_id>/projects/<int:project_id>", methods=["DELETE"])
@role_required("ClubLead")
def delete_project(club_id, project_id):
    club, err = get_owned_club_or_403(club_id)
    if err:
        return err
    p = Project.query.filter_by(id=project_id, club_id=club.id).first()
    if not p:
        return jsonify({"error": "Project not found"}), 404
    db.session.delete(p)
    db.session.commit()
    return jsonify({"message": "Project deleted"})
