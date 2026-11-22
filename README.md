# CampusConnect — Student, Club & Event Management Platform

Full-stack app: **Python Flask + SQLAlchemy + MySQL 8.0**, JWT auth with strict RBAC,\
vanilla HTML/CSS/JS glassmorphism SPA frontend, containerised with Docker Compose.

## Run with Docker (recommended)

```bash
docker compose up --build
```

Then open [http://localhost:5000](http://localhost:5000)

The `web` container waits for MySQL, seeds demo data, then serves via Gunicorn on port 5000.

## Run locally without Docker

```bash
pip install -r requirements.txt
# Quick start with SQLite (no MySQL needed):
export DATABASE_URL=sqlite:///campusconnect.db
python seed.py
python run.py            # http://localhost:5000
# Or point at a real MySQL via DB_HOST/DB_USER/DB_PASSWORD/DB_NAME env vars.
```

## Demo accounts (password: `password123`)

| Role | Email |
| --- | --- |
| Student | [student@campusconnect.com](mailto:student@campusconnect.com) |
| Club Lead | [clublead@campusconnect.com](mailto:clublead@campusconnect.com) |
| Faculty Coordinator | [faculty@campusconnect.com](mailto:faculty@campusconnect.com) |
| Admin | [admin@campusconnect.com](mailto:admin@campusconnect.com) |

## Architecture

Frontend (SPA) → REST API → Flask → SQLAlchemy → MySQL → JSON → Frontend

* **Auth**: `Flask-JWT-Extended`, tokens carry the user role.

* **RBAC**: `@role_required(...)` and `get_owned_club_or_403()` — a Club Lead's club is\
  always derived from their JWT identity in the DB, never trusted from the request.

* **10 models**: User, Club, ClubMember, ClubMembershipRequest, Event (string PK like\
  `AITC-HACK-001`), EventRegistration (UNIQUE event+user), Attendance (UNIQUE event+user),\
  Broadcast, Project, Notification.

See `app/routes/` for all endpoints.