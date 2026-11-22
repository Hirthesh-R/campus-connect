from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from ..models import (db, Club, ClubMember, ClubMembershipRequest, create_notification)
from ..utils import current_user, role_required, get_owned_club_or_403

memberships_bp = Blueprint("memberships", __name__, url_prefix="/api/clubs")


@memberships_bp.route("/<int:club_id>/membership-requests", methods=["POST"])
@role_required("Student", "ClubLead", "FacultyCoordinator", "Admin")
def submit_request(club_id):
    user = current_user()
    club = Club.query.get(club_id)
    if not club:
        return jsonify({"error": "Club not found"}), 404
    # Already an approved member?
    if ClubMember.query.filter_by(club_id=club_id, user_id=user.id, status="Approved").first():
        return jsonify({"error": "You are already a member of this club"}), 409
    # Existing pending request?
    if ClubMembershipRequest.query.filter_by(club_id=club_id, user_id=user.id, status="Pending").first():
        return jsonify({"error": "You already have a pending request for this club"}), 409
    data = request.get_json(silent=True) or {}
    req = ClubMembershipRequest(
        club_id=club_id, user_id=user.id,
        requested_role=data.get("requestedRole"), skills=data.get("skills"),
        activities=data.get("activities"), projects=data.get("projects"),
        club_related_experience=data.get("clubRelatedExperience"),
        contribution=data.get("contribution"), motivation=data.get("motivation"),
        status="Pending",
    )
    db.session.add(req)
    if club.club_leader_id:
        create_notification(club.club_leader_id, "New membership request",
                            f"{user.name} requested to join {club.name}.",
                            "membership", club_id, str(club_id))
    create_notification(user.id, "Membership request submitted",
                        f"Your request to join {club.name} was submitted and is pending review.",
                        "membership", club_id, str(club_id))
    db.session.commit()
    return jsonify(req.to_dict()), 201


@memberships_bp.route("/<int:club_id>/membership-requests", methods=["GET"])
@role_required("ClubLead")
def list_requests(club_id):
    club, err = get_owned_club_or_403(club_id)
    if err:
        return err
    reqs = ClubMembershipRequest.query.filter_by(club_id=club.id).order_by(
        ClubMembershipRequest.submitted_at.desc()).all()
    return jsonify([r.to_dict() for r in reqs])


@memberships_bp.route("/<int:club_id>/membership-requests/<int:request_id>", methods=["GET"])
@role_required("ClubLead")
def get_request(club_id, request_id):
    club, err = get_owned_club_or_403(club_id)
    if err:
        return err
    req = ClubMembershipRequest.query.filter_by(id=request_id, club_id=club.id).first()
    if not req:
        return jsonify({"error": "Request not found"}), 404
    return jsonify(req.to_dict())


@memberships_bp.route("/<int:club_id>/membership-requests/<int:request_id>/approve", methods=["PUT"])
@role_required("ClubLead")
def approve_request(club_id, request_id):
    club, err = get_owned_club_or_403(club_id)
    if err:
        return err
    req = ClubMembershipRequest.query.filter_by(id=request_id, club_id=club.id).first()
    if not req:
        return jsonify({"error": "Request not found"}), 404
    if req.status != "Pending":
        return jsonify({"error": "Request is not pending"}), 409
    try:
        req.status = "Approved"
        req.reviewed_at = datetime.utcnow()
        req.reviewed_by = current_user().id
        if not ClubMember.query.filter_by(club_id=club.id, user_id=req.user_id).first():
            db.session.add(ClubMember(club_id=club.id, user_id=req.user_id,
                                      role=req.requested_role, status="Approved"))
        create_notification(req.user_id,
                            f"Congratulations! Approved for {club.name}",
                            f"Your request to join {club.name} has been approved. Role: {req.requested_role}. Welcome to the club!",
                            "membership", club.id, str(club.id))
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Failed to approve request"}), 500
    return jsonify(req.to_dict())


@memberships_bp.route("/<int:club_id>/membership-requests/<int:request_id>/reject", methods=["PUT"])
@role_required("ClubLead")
def reject_request(club_id, request_id):
    club, err = get_owned_club_or_403(club_id)
    if err:
        return err
    req = ClubMembershipRequest.query.filter_by(id=request_id, club_id=club.id).first()
    if not req:
        return jsonify({"error": "Request not found"}), 404
    if req.status != "Pending":
        return jsonify({"error": "Request is not pending"}), 409
    data = request.get_json(silent=True) or {}
    try:
        req.status = "Rejected"
        req.reviewed_at = datetime.utcnow()
        req.reviewed_by = current_user().id
        req.review_message = data.get("reviewMessage")
        create_notification(req.user_id, "Membership application update",
                            f"Your request to join {club.name} was not approved this time. Keep building your skills and apply again in future!",
                            "membership", club.id, str(club.id))
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Failed to reject request"}), 500
    return jsonify(req.to_dict())
