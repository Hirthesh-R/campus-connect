from flask import Blueprint, render_template, send_from_directory, current_app

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/health")
def health():
    return {"status": "ok"}
