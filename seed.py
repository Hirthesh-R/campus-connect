"""Seed demo data. Idempotent (upserts by email / natural keys). Run: python seed.py"""
from app import create_app
from app.models import (db, User, Club, ClubMember, Event)

app = create_app()


def upsert_user(email, **kw):
    u = User.query.filter_by(email=email).first()
    if not u:
        u = User(email=email, **{k: v for k, v in kw.items() if k != "password"})
        u.set_password(kw.get("password", "password123"))
        db.session.add(u)
        db.session.flush()
    return u


def run():
    with app.app_context():
        db.create_all()
        student = upsert_user("student@campusconnect.com", name="Rahul Sharma",
                              role="Student", student_id="CS21001", department="CSE",
                              branch="Computer Science", section="A", year="3",
                              password="password123")
        lead = upsert_user("clublead@campusconnect.com", name="Priya Nair",
                           role="ClubLead", student_id="CS20050", department="CSE",
                           branch="Computer Science", section="B", year="4",
                           password="password123")
        faculty = upsert_user("faculty@campusconnect.com", name="Dr. Anand Kumar",
                              role="FacultyCoordinator", department="CSE",
                              password="password123")
        upsert_user("admin@campusconnect.com", name="System Admin", role="Admin",
                    password="password123")

        club = Club.query.filter_by(name="AI & Technology Club").first()
        if not club:
            club = Club(
                name="AI & Technology Club",
                slogan="Building the future with intelligence",
                description="A community of students passionate about artificial intelligence, "
                            "machine learning and emerging technologies. We host hackathons, "
                            "workshops and collaborative projects.",
                category="Technology", campus="Main Campus", status="Active",
                faculty_coordinator_id=faculty.id, club_leader_id=lead.id,
            )
            db.session.add(club)
            db.session.flush()

        # Ensure the lead is an approved member of their own club
        if not ClubMember.query.filter_by(club_id=club.id, user_id=lead.id).first():
            db.session.add(ClubMember(club_id=club.id, user_id=lead.id,
                                      role="Technical", status="Approved"))

        samples = [
            ("AITC-HACK-001", "AI Hackathon 2026", "48-hour hackathon to build AI-powered solutions.",
             "2026-10-15", "Auditorium", "Hackathon", 100),
            ("AITC-WORK-002", "Intro to Machine Learning Workshop",
             "Hands-on workshop covering ML fundamentals with Python.",
             "2026-10-22", "Lab 3", "Workshop", 60),
            ("AITC-SEMINAR-003", "The Future of Generative AI",
             "Seminar with industry experts on generative AI trends.",
             "2026-11-05", "Seminar Hall", "Seminar", 150),
        ]
        for eid, name, desc, date, venue, cat, cap in samples:
            if not Event.query.get(eid):
                db.session.add(Event(
                    event_id=eid, club_id=club.id, name=name, description=desc,
                    event_date=date, start_time="10:00", end_time="17:00", venue=venue,
                    campus="Main Campus", category=cat, max_participants=cap,
                    registration_deadline=date, status="Published", created_by=lead.id,
                ))

        db.session.commit()
        print("Seed complete.")
        print("Demo accounts (password: password123):")
        print("  student@campusconnect.com  (Student)")
        print("  clublead@campusconnect.com (ClubLead)")
        print("  faculty@campusconnect.com  (FacultyCoordinator)")
        print("  admin@campusconnect.com    (Admin)")


if __name__ == "__main__":
    run()
