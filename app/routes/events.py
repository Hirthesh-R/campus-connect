from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import IntegrityError

from ..models import (db, Event, EventRegistration, Attendance, Club, ClubMember,
                      create_notification)
from ..utils import current_user, role_required, get_owned_club_or_403

events_bp = Blueprint("events", __name__, url_prefix="/api/events")


@events_bp.route("", methods=["GET"])
@jwt_required()
def list_events():
    return jsonify([e.to_dict() for e in Event.query.order_by(Event.created_at.desc()).all()])


@events_bp.route("", methods=["POST"])
@role_required("ClubLead")
def create_event():
    club, err = get_owned_club_or_403()
    if err:
        return err
    data = request.get_json(silent=True) or {}
    event_id = (data.get("eventId") or "").strip()
    if not event_id or not data.get("name"):
        return jsonify({"error": "Event ID and name are required"}), 400
    if Event.query.get(event_id):
        return jsonify({"error": "Event ID already exists"}), 409
    try:
        cap = int(data.get("maxParticipants") or 100)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid capacity"}), 400
    ev = Event(
        event_id=event_id, club_id=club.id, name=data.get("name"),
        description=data.get("description"), event_date=data.get("eventDate"),
        start_time=data.get("startTime"), end_time=data.get("endTime"),
        venue=data.get("venue"), campus=data.get("campus"), category=data.get("category"),
        max_participants=cap, registration_deadline=data.get("registrationDeadline"),
        poster=data.get("poster"), status=data.get("status") or "Published",
        created_by=current_user().id,
    )
    db.session.add(ev)
    # Notify approved club members
    for m in ClubMember.query.filter_by(club_id=club.id, status="Approved").all():
        create_notification(m.user_id, "New event published",
                            f"{club.name} published a new event: {ev.name}.",
                            "event", club.id, event_id)
    db.session.commit()
    return jsonify(ev.to_dict()), 201


@events_bp.route("/<event_id>", methods=["GET"])
@jwt_required()
def get_event(event_id):
    ev = Event.query.get(event_id)
    if not ev:
        return jsonify({"error": "Event not found"}), 404
    return jsonify(ev.to_dict())


@events_bp.route("/<event_id>", methods=["PUT"])
@role_required("ClubLead")
def update_event(event_id):
    club, err = get_owned_club_or_403()
    if err:
        return err
    ev = Event.query.get(event_id)
    if not ev:
        return jsonify({"error": "Event not found"}), 404
    if ev.club_id != club.id:
        return jsonify({"error": "Forbidden: not your event"}), 403
    data = request.get_json(silent=True) or {}
    for attr, key in [("name", "name"), ("description", "description"),
                      ("event_date", "eventDate"), ("start_time", "startTime"),
                      ("end_time", "endTime"), ("venue", "venue"), ("campus", "campus"),
                      ("category", "category"), ("registration_deadline", "registrationDeadline"),
                      ("poster", "poster"), ("status", "status")]:
        if key in data and data.get(key) is not None:
            setattr(ev, attr, data.get(key))
    if data.get("maxParticipants") is not None:
        try:
            ev.max_participants = int(data.get("maxParticipants"))
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid capacity"}), 400
    db.session.commit()
    return jsonify(ev.to_dict())


@events_bp.route("/<event_id>", methods=["DELETE"])
@role_required("ClubLead")
def delete_event(event_id):
    club, err = get_owned_club_or_403()
    if err:
        return err
    ev = Event.query.get(event_id)
    if not ev:
        return jsonify({"error": "Event not found"}), 404
    if ev.club_id != club.id:
        return jsonify({"error": "Forbidden: not your event"}), 403
    EventRegistration.query.filter_by(event_id=event_id).delete()
    Attendance.query.filter_by(event_id=event_id).delete()
    db.session.delete(ev)
    db.session.commit()
    return jsonify({"message": "Event deleted"})


@events_bp.route("/<event_id>/register", methods=["POST"])
@role_required("Student", "ClubLead", "FacultyCoordinator", "Admin")
def register_event(event_id):
    user = current_user()
    ev = Event.query.get(event_id)
    if not ev:
        return jsonify({"error": "Event not found"}), 404
    if (ev.status or "").lower() in ("cancelled", "closed"):
        return jsonify({"error": "Event is not accepting registrations"}), 400
    if EventRegistration.query.filter_by(event_id=event_id, user_id=user.id).first():
        return jsonify({"error": "You are already registered for this event"}), 409
    regs = EventRegistration.query.filter_by(event_id=event_id).count()
    if ev.max_participants and regs >= ev.max_participants:
        return jsonify({"error": "Event is full"}), 400
    data = request.get_json(silent=True) or {}
    reg = EventRegistration(
        event_id=event_id, user_id=user.id,
        name=data.get("name") or user.name,
        student_id_number=data.get("studentId") or user.student_id,
        email=data.get("email") or user.email,
        department=data.get("department") or user.department,
        branch=data.get("branch") or user.branch,
        section=data.get("section") or user.section,
    )
    db.session.add(reg)
    create_notification(user.id, "Registration successful",
                        f"You are registered for {ev.name} ({event_id}).", "event",
                        ev.club_id, event_id)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "You are already registered for this event"}), 409
    return jsonify(reg.to_dict()), 201


@events_bp.route("/<event_id>/registration-status", methods=["GET"])
@jwt_required()
def registration_status(event_id):
    user = current_user()
    reg = EventRegistration.query.filter_by(event_id=event_id, user_id=user.id).first()
    return jsonify({"registered": reg is not None})


@events_bp.route("/<event_id>/registrations", methods=["GET"])
@role_required("ClubLead")
def event_registrations(event_id):
    club, err = get_owned_club_or_403()
    if err:
        return err
    ev = Event.query.get(event_id)
    if not ev:
        return jsonify({"error": "Event not found"}), 404
    if ev.club_id != club.id:
        return jsonify({"error": "Forbidden: not your event"}), 403
    regs = EventRegistration.query.filter_by(event_id=event_id).order_by(
        EventRegistration.registered_at.asc()).all()
    return jsonify([r.to_dict() for r in regs])


@events_bp.route("/<event_id>/attendance", methods=["GET"])
@role_required("ClubLead")
def get_attendance(event_id):
    club, err = get_owned_club_or_403()
    if err:
        return err
    ev = Event.query.get(event_id)
    if not ev or ev.club_id != club.id:
        return jsonify({"error": "Forbidden: not your event"}), 403
    regs = EventRegistration.query.filter_by(event_id=event_id).all()
    att = {a.user_id: a.status for a in Attendance.query.filter_by(event_id=event_id).all()}
    out = []
    for r in regs:
        d = r.to_dict()
        d["attendance"] = att.get(r.user_id, "Not Marked")
        out.append(d)
    return jsonify(out)


@events_bp.route("/<event_id>/attendance", methods=["PUT"])
@role_required("ClubLead")
def mark_attendance(event_id):
    club, err = get_owned_club_or_403()
    if err:
        return err
    ev = Event.query.get(event_id)
    if not ev or ev.club_id != club.id:
        return jsonify({"error": "Forbidden: not your event"}), 403
    data = request.get_json(silent=True) or {}
    records = data.get("records") or []
    for rec in records:
        uid = rec.get("userId")
        status = rec.get("status", "Not Marked")
        if uid is None:
            continue
        a = Attendance.query.filter_by(event_id=event_id, user_id=uid).first()
        if a:
            a.status = status
            a.marked_at = datetime.utcnow()
            a.marked_by = current_user().id
        else:
            db.session.add(Attendance(event_id=event_id, user_id=uid, status=status,
                                      marked_by=current_user().id))
    db.session.commit()
    return jsonify({"message": "Attendance saved"})
