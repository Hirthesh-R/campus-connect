from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from ..models import db, Notification
from ..utils import current_user

notifications_bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")


@notifications_bp.route("", methods=["GET"])
@jwt_required()
def list_notifications():
    user = current_user()
    ns = Notification.query.filter_by(user_id=user.id).order_by(
        Notification.created_at.desc()).all()
    unread = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    return jsonify({"notifications": [n.to_dict() for n in ns], "unreadCount": unread})


@notifications_bp.route("/<int:notification_id>/read", methods=["PUT"])
@jwt_required()
def mark_read(notification_id):
    user = current_user()
    n = Notification.query.filter_by(id=notification_id, user_id=user.id).first()
    if not n:
        return jsonify({"error": "Notification not found"}), 404
    n.is_read = True
    db.session.commit()
    return jsonify(n.to_dict())


@notifications_bp.route("/read-all", methods=["PUT"])
@jwt_required()
def mark_all_read():
    user = current_user()
    Notification.query.filter_by(user_id=user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    return jsonify({"message": "All marked read"})
