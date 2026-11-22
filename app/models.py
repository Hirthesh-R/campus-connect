from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

ROLES = ["Student", "ClubLead", "FacultyCoordinator", "Admin"]


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False, default="Student")
    student_id = db.Column(db.String(60))
    department = db.Column(db.String(120))
    branch = db.Column(db.String(120))
    section = db.Column(db.String(30))
    year = db.Column(db.String(30))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw or "")

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "email": self.email, "role": self.role,
            "studentId": self.student_id, "department": self.department,
            "branch": self.branch, "section": self.section, "year": self.year,
        }


class Club(db.Model):
    __tablename__ = "clubs"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    slogan = db.Column(db.String(255))
    description = db.Column(db.Text)
    category = db.Column(db.String(80))
    logo = db.Column(db.String(500))
    campus = db.Column(db.String(120))
    faculty_coordinator_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    club_leader_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    status = db.Column(db.String(30), default="Active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    faculty = db.relationship("User", foreign_keys=[faculty_coordinator_id])
    leader = db.relationship("User", foreign_keys=[club_leader_id])

    def to_dict(self):
        members = ClubMember.query.filter_by(club_id=self.id, status="Approved").count()
        projects = Project.query.filter_by(club_id=self.id).count()
        events = Event.query.filter_by(club_id=self.id).count()
        return {
            "id": self.id, "name": self.name, "slogan": self.slogan,
            "description": self.description, "category": self.category,
            "logo": self.logo, "campus": self.campus, "status": self.status,
            "facultyCoordinator": self.faculty.name if self.faculty else None,
            "clubLeader": self.leader.name if self.leader else None,
            "memberCount": members, "projectCount": projects, "eventCount": events,
        }


class ClubMember(db.Model):
    __tablename__ = "club_members"
    id = db.Column(db.Integer, primary_key=True)
    club_id = db.Column(db.Integer, db.ForeignKey("clubs.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    role = db.Column(db.String(80))
    status = db.Column(db.String(30), default="Approved")
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint("club_id", "user_id", name="uq_member"),)

    user = db.relationship("User")

    def to_dict(self):
        u = self.user
        return {
            "id": self.id, "clubId": self.club_id, "role": self.role,
            "status": self.status,
            "joinedAt": self.joined_at.isoformat() if self.joined_at else None,
            "name": u.name if u else None, "studentId": u.student_id if u else None,
            "email": u.email if u else None, "department": u.department if u else None,
            "branch": u.branch if u else None, "section": u.section if u else None,
        }


class ClubMembershipRequest(db.Model):
    __tablename__ = "membership_requests"
    id = db.Column(db.Integer, primary_key=True)
    club_id = db.Column(db.Integer, db.ForeignKey("clubs.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    requested_role = db.Column(db.String(80))
    skills = db.Column(db.Text)
    activities = db.Column(db.Text)
    projects = db.Column(db.Text)
    club_related_experience = db.Column(db.Text)
    contribution = db.Column(db.Text)
    motivation = db.Column(db.Text)
    status = db.Column(db.String(30), default="Pending")
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    reviewed_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    review_message = db.Column(db.Text)

    user = db.relationship("User", foreign_keys=[user_id])

    def to_dict(self):
        u = self.user
        return {
            "id": self.id, "clubId": self.club_id, "requestedRole": self.requested_role,
            "skills": self.skills, "activities": self.activities, "projects": self.projects,
            "clubRelatedExperience": self.club_related_experience,
            "contribution": self.contribution, "motivation": self.motivation,
            "status": self.status,
            "submittedAt": self.submitted_at.isoformat() if self.submitted_at else None,
            "reviewedAt": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "reviewMessage": self.review_message,
            "name": u.name if u else None, "studentId": u.student_id if u else None,
            "email": u.email if u else None, "department": u.department if u else None,
            "branch": u.branch if u else None, "section": u.section if u else None,
            "year": u.year if u else None,
        }


class Event(db.Model):
    __tablename__ = "events"
    event_id = db.Column(db.String(80), primary_key=True)
    club_id = db.Column(db.Integer, db.ForeignKey("clubs.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    event_date = db.Column(db.String(40))
    start_time = db.Column(db.String(40))
    end_time = db.Column(db.String(40))
    venue = db.Column(db.String(200))
    campus = db.Column(db.String(120))
    category = db.Column(db.String(80))
    max_participants = db.Column(db.Integer, default=100)
    registration_deadline = db.Column(db.String(40))
    poster = db.Column(db.String(500))
    status = db.Column(db.String(30), default="Published")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))

    club = db.relationship("Club")

    def to_dict(self):
        regs = EventRegistration.query.filter_by(event_id=self.event_id).count()
        return {
            "eventId": self.event_id, "clubId": self.club_id,
            "clubName": self.club.name if self.club else None,
            "name": self.name, "description": self.description,
            "eventDate": self.event_date, "startTime": self.start_time,
            "endTime": self.end_time, "venue": self.venue, "campus": self.campus,
            "category": self.category, "maxParticipants": self.max_participants,
            "registrationDeadline": self.registration_deadline, "poster": self.poster,
            "status": self.status, "registeredCount": regs,
            "availableCapacity": max(0, (self.max_participants or 0) - regs),
        }


class EventRegistration(db.Model):
    __tablename__ = "event_registrations"
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.String(80), db.ForeignKey("events.event_id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(120))
    student_id_number = db.Column(db.String(60))
    email = db.Column(db.String(160))
    department = db.Column(db.String(120))
    branch = db.Column(db.String(120))
    section = db.Column(db.String(30))
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(30), default="Registered")
    __table_args__ = (db.UniqueConstraint("event_id", "user_id", name="uq_registration"),)

    def to_dict(self):
        return {
            "id": self.id, "eventId": self.event_id, "userId": self.user_id,
            "name": self.name, "studentId": self.student_id_number, "email": self.email,
            "department": self.department, "branch": self.branch, "section": self.section,
            "registeredAt": self.registered_at.isoformat() if self.registered_at else None,
            "status": self.status,
        }


class Attendance(db.Model):
    __tablename__ = "attendance"
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.String(80), db.ForeignKey("events.event_id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(30), default="Not Marked")
    marked_at = db.Column(db.DateTime, default=datetime.utcnow)
    marked_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    __table_args__ = (db.UniqueConstraint("event_id", "user_id", name="uq_attendance"),)

    def to_dict(self):
        return {"id": self.id, "eventId": self.event_id, "userId": self.user_id,
                "status": self.status}


class Broadcast(db.Model):
    __tablename__ = "broadcasts"
    id = db.Column(db.Integer, primary_key=True)
    club_id = db.Column(db.Integer, db.ForeignKey("clubs.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text)
    target_audience = db.Column(db.String(80), default="All Club Members")
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    publish_date = db.Column(db.String(40))
    expiry_date = db.Column(db.String(40))
    status = db.Column(db.String(30), default="Active")

    def to_dict(self):
        return {
            "id": self.id, "clubId": self.club_id, "title": self.title,
            "message": self.message, "targetAudience": self.target_audience,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "publishDate": self.publish_date, "expiryDate": self.expiry_date,
            "status": self.status,
        }


class Project(db.Model):
    __tablename__ = "projects"
    id = db.Column(db.Integer, primary_key=True)
    club_id = db.Column(db.Integer, db.ForeignKey("clubs.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    technologies = db.Column(db.String(400))
    status = db.Column(db.String(30), default="Active")
    start_date = db.Column(db.String(40))
    expected_completion = db.Column(db.String(40))
    team = db.Column(db.String(400))
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "clubId": self.club_id, "name": self.name,
            "description": self.description, "technologies": self.technologies,
            "status": self.status, "startDate": self.start_date,
            "expectedCompletion": self.expected_completion, "team": self.team,
        }


class Notification(db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    club_id = db.Column(db.Integer, db.ForeignKey("clubs.id"))
    type = db.Column(db.String(60))
    title = db.Column(db.String(200))
    message = db.Column(db.Text)
    related_entity_id = db.Column(db.String(80))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "type": self.type, "title": self.title,
            "message": self.message, "relatedEntityId": self.related_entity_id,
            "isRead": self.is_read,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }


def create_notification(user_id, title, message, ntype="info", club_id=None, related=None):
    n = Notification(user_id=user_id, title=title, message=message, type=ntype,
                     club_id=club_id, related_entity_id=related)
    db.session.add(n)
    return n
