import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "campusconnect-dev-secret-change-me")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "campusconnect-jwt-secret-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = 60 * 60 * 12  # 12 hours

    # Default to MySQL (Docker). Override with DATABASE_URL env var.
    # For a quick local smoke test without MySQL, set DATABASE_URL=sqlite:///campusconnect.db
    DB_USER = os.environ.get("DB_USER", "campus")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "campuspass")
    DB_HOST = os.environ.get("DB_HOST", "db")
    DB_PORT = os.environ.get("DB_PORT", "3306")
    DB_NAME = os.environ.get("DB_NAME", "campusconnect")

    _default_uri = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    )
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", _default_uri)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 280}
