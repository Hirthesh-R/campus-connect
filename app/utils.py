from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt, get_jwt_identity

from .models import User, Club


def current_user():
    uid = get_jwt_identity()
    if uid is None:
        return None
    return User.query.get(int(uid))


def role_required(*roles):
    """Require a valid JWT AND one of the given roles. 401 if unauth, 403 if wrong role."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("role") not in roles:
                return jsonify({"error": "Forbidden: insufficient role"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def get_owned_club_or_403(club_id=None):
    """Return (club, None) if the authenticated ClubLead owns the club derived from
    their account. If club_id is supplied it MUST match the owned club, else 403.
    Ownership is derived from the DB, never trusted from the request.
    Returns (None, (response, status)) on failure."""
    user = current_user()
    if not user:
        return None, (jsonify({"error": "Authentication required"}), 401)
    owned = Club.query.filter_by(club_leader_id=user.id).first()
    if not owned:
        return None, (jsonify({"error": "Forbidden: you do not lead any club"}), 403)
    if club_id is not None and str(owned.id) != str(club_id):
        return None, (jsonify({"error": "Forbidden: not your club"}), 403)
    return owned, None
