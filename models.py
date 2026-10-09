from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import CheckConstraint, UniqueConstraint
from extensions import db

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    client_profile = db.relationship("Client", back_populates="user", uselist=False)
    __table_args__ = (CheckConstraint("role IN ('admin', 'client')", name="ck_user_role"),)

class Client(db.Model):
    __tablename__ = "clients"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    full_name = db.Column(db.String(160), nullable=False, index=True)
    amka = db.Column(db.String(11), nullable=True, index=True)
    phone = db.Column(db.String(40), index=True)
    email = db.Column(db.String(254), index=True)
    sms_consent = db.Column(db.Boolean, nullable=False, default=False)
    email_consent = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user = db.relationship("User", back_populates="client_profile")
    prescriptions = db.relationship("Prescription", back_populates="client", cascade="all, delete-orphan")
    messages = db.relationship("Message", back_populates="client", cascade="all, delete-orphan")

class Prescription(db.Model):
    __tablename__ = "prescriptions"
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    month = db.Column(db.String(7), nullable=False, index=True)  # YYYY-MM
    open_date = db.Column(db.Date, nullable=False, index=True)
    status = db.Column(db.String(30), nullable=False, default="αναμένεται")
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    client = db.relationship("Client", back_populates="prescriptions")
    __table_args__ = (
        CheckConstraint("status IN ('αναμένεται', 'άνοιξε', 'ενημερώθηκε', 'ολοκληρώθηκε')", name="ck_prescription_status"),
    )

class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    subject = db.Column(db.String(160), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    client = db.relationship("Client", back_populates="messages")

class NotificationLog(db.Model):
    __tablename__ = "notification_logs"
    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey("prescriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    channel = db.Column(db.String(20), nullable=False)
    recipient = db.Column(db.String(254), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")
    provider_message_id = db.Column(db.String(160))
    error = db.Column(db.Text)
    attempted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("prescription_id", "channel", name="uq_prescription_notification_channel"),)
