from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required

from ..models import db, User
from ..utils import current_user

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401
    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    return jsonify({"token": token, "user": user.to_dict()})


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    if not email or not data.get("password") or not data.get("name"):
        return jsonify({"error": "Name, email and password are required"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409
    user = User(
        name=data.get("name"), email=email, role="Student",
        student_id=data.get("studentId"), department=data.get("department"),
        branch=data.get("branch"), section=data.get("section"), year=data.get("year"),
    )
    user.set_password(data.get("password"))
    db.session.add(user)
    db.session.commit()
    from flask_jwt_extended import create_access_token
    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    return jsonify({"token": token, "user": user.to_dict()}), 201


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user = current_user()
    if not user:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"user": user.to_dict()})
