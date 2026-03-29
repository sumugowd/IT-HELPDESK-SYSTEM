from app import db
from datetime import datetime

class Ticket(db.Model):
    __tablename__ = "tickets"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    issue_type = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(100), nullable=False)

    status = db.Column(db.String(50), default="Open")

    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKEy('users.id'),nullable=True)

    phone = db.Column(db.String(15), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)