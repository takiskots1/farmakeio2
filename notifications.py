import os
from datetime import datetime
from sqlalchemy import select
from models import Prescription, NotificationLog, User
from extensions import db

def send_sms(phone, body):
    """SMS.to integration placeholder. Configure only after verifying current SMS.to API details."""
    api_key = os.environ.get("SMSTO_API_KEY")
    if not api_key:
        raise RuntimeError("SMSTO_API_KEY is not configured")
    # Add provider-specific HTTPS request here after confirming endpoint and payload
    # from your SMS.to account/API documentation. Never log the API key.
    raise NotImplementedError("Connect the current SMS.to API endpoint in services/notifications.py")

def send_email(to_address, subject, body):
    """Send email through configured SMTP. Returns after provider accepts the message."""
    import smtplib
    from email.message import EmailMessage
    host = os.environ.get("SMTP_HOST")
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")
    from_address = os.environ.get("SMTP_FROM")
    port = int(os.environ.get("SMTP_PORT", "587"))
    if not all([host, user, password, from_address]):
        raise RuntimeError("SMTP settings are incomplete")
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_address
    msg["To"] = to_address
    msg.set_content(body)
    with smtplib.SMTP(host, port, timeout=20) as server:
        server.starttls()
        server.login(user, password)
        server.send_message(msg)

def send_due_notifications(app, session, target_date):
    """Idempotent per prescription/channel; failed attempts are logged and can be reviewed."""
    count = 0
    due = session.scalars(select(Prescription).where(
        Prescription.open_date == target_date,
        Prescription.status.in_(["αναμένεται", "άνοιξε"])
    )).all()
    for prescription in due:
        client = prescription.client
        user = client.user
        # A minimal message avoids disclosing sensitive health details on lock screens.
        body = "Η ημερομηνία ανοίγματος της συνταγής σας είναι σήμερα. Επικοινωνήστε με το φαρμακείο για επιβεβαίωση διαθεσιμότητας."
        channels = []
        if client.phone and client.sms_consent:
            channels.append(("sms", client.phone))
        if client.email and client.email_consent:
            channels.append(("email", client.email))
        for channel, recipient in channels:
            exists = session.scalar(select(NotificationLog).where(
                NotificationLog.prescription_id == prescription.id,
                NotificationLog.channel == channel
            ))
            if exists:
                continue
            log = NotificationLog(prescription_id=prescription.id, channel=channel, recipient=recipient, status="pending")
            session.add(log)
            session.flush()
            try:
                if channel == "sms":
                    send_sms(recipient, body)
                else:
                    send_email(recipient, "Ενημέρωση από το CHRYSPHARMACY", body)
                log.status = "sent"
            except Exception as exc:
                log.status = "failed"
                log.error = str(exc)[:2000]
                app.logger.exception("Notification failed: prescription_id=%s channel=%s", prescription.id, channel)
            log.attempted_at = datetime.utcnow()
            count += 1
        session.commit()
    return count
