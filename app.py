import os
from dotenv import load_dotenv
load_dotenv()
from datetime import date, datetime, timedelta
from functools import wraps

from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_, select
from extensions import db
from models import User, Client, Prescription, Message, NotificationLog
from forms import LoginForm, ClientForm, PrescriptionForm, MessageForm
from services.notifications import send_due_notifications
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    CSRFProtect(app)

    login_manager = LoginManager()
    login_manager.login_view = "client_login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    def role_required(role):
        def decorator(view):
            @wraps(view)
            @login_required
            def wrapped(*args, **kwargs):
                if current_user.role != role:
                    abort(403)
                return view(*args, **kwargs)
            return wrapped
        return decorator

    @app.get("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("admin_dashboard" if current_user.role == "admin" else "client_dashboard"))
        return render_template("index.html")

    @app.route("/login/client", methods=["GET", "POST"])
    def client_login():
        if current_user.is_authenticated:
            return redirect(url_for("client_dashboard" if current_user.role == "client" else "admin_dashboard"))
        form = LoginForm()
        if form.validate_on_submit():
            user = db.session.scalar(select(User).where(User.username == form.username.data.strip().lower()))
            if user and user.is_active and user.role == "client" and check_password_hash(user.password_hash, form.password.data):
                login_user(user, remember=bool(form.remember.data))
                return redirect(url_for("client_dashboard"))
            flash("Τα στοιχεία σύνδεσης δεν είναι σωστά ή ο λογαριασμός δεν είναι ενεργός.", "danger")
        return render_template("auth/login.html", form=form, audience="Πελάτες", endpoint="client_login")

    @app.route("/login/admin", methods=["GET", "POST"])
    def admin_login():
        if current_user.is_authenticated:
            return redirect(url_for("admin_dashboard" if current_user.role == "admin" else "client_dashboard"))
        form = LoginForm()
        if form.validate_on_submit():
            user = db.session.scalar(select(User).where(User.username == form.username.data.strip().lower()))
            if user and user.is_active and user.role == "admin" and check_password_hash(user.password_hash, form.password.data):
                login_user(user, remember=bool(form.remember.data))
                return redirect(url_for("admin_dashboard"))
            flash("Τα στοιχεία σύνδεσης δεν είναι σωστά ή ο λογαριασμός δεν είναι ενεργός.", "danger")
        return render_template("auth/login.html", form=form, audience="Διαχειριστής", endpoint="admin_login")

    @app.post("/logout")
    @login_required
    def logout():
        logout_user()
        flash("Αποσυνδεθήκατε.", "info")
        return redirect(url_for("index"))

    @app.get("/admin")
    @role_required("admin")
    def admin_dashboard():
        today = date.today()
        due = db.session.scalars(select(Prescription).where(Prescription.open_date == today).order_by(Prescription.client_id)).all()
        return render_template("admin/dashboard.html",
            client_count=db.session.scalar(select(db.func.count(Client.id))) or 0,
            prescription_count=db.session.scalar(select(db.func.count(Prescription.id))) or 0,
            due=due, today=today)

    @app.route("/admin/clients", methods=["GET", "POST"])
    @role_required("admin")
    def admin_clients():
        form = ClientForm()
        if form.validate_on_submit():
            username = form.username.data.strip().lower()
            if db.session.scalar(select(User).where(User.username == username)):
                flash("Το όνομα χρήστη χρησιμοποιείται ήδη.", "danger")
            else:
                user = User(username=username, password_hash=generate_password_hash(form.password.data), role="client", is_active=True)
                client = Client(full_name=form.full_name.data.strip(), amka=form.amka.data.strip() or None, phone=form.phone.data.strip() or None,
                    email=form.email.data.strip().lower() or None, user=user,
                    sms_consent=bool(form.sms_consent.data), email_consent=bool(form.email_consent.data))
                db.session.add(client)
                db.session.commit()
                flash("Ο πελάτης δημιουργήθηκε.", "success")
                return redirect(url_for("admin_clients"))
        q = request.args.get("q", "").strip()
        stmt = select(Client).join(Client.user)
        if q:
            like = f"%{q}%"
            stmt = stmt.where(or_(Client.full_name.ilike(like), Client.amka.ilike(like), Client.phone.ilike(like),
                Client.email.ilike(like), User.username.ilike(like)))
        clients = db.session.scalars(stmt.order_by(Client.full_name).limit(200)).all()
        return render_template("admin/clients.html", form=form, clients=clients, q=q)

    @app.route("/admin/clients/<int:client_id>/toggle", methods=["POST"])
    @role_required("admin")
    def toggle_client(client_id):
        client = db.get_or_404(Client, client_id)
        client.user.is_active = not client.user.is_active
        db.session.commit()
        flash("Η κατάσταση του λογαριασμού ενημερώθηκε.", "success")
        return redirect(url_for("admin_clients"))

    @app.route("/admin/prescriptions", methods=["GET", "POST"])
    @role_required("admin")
    def admin_prescriptions():
        form = PrescriptionForm()
        form.client_id.choices = [(c.id, f"{c.full_name} ({c.user.username})") for c in db.session.scalars(select(Client).join(Client.user).where(User.is_active.is_(True)).order_by(Client.full_name)).all()]
        if form.validate_on_submit():
            p = Prescription(client_id=form.client_id.data, month=form.month.data, open_date=form.open_date.data,
                status=form.status.data, notes=form.notes.data.strip() or None)
            db.session.add(p)
            db.session.commit()
            flash("Η συνταγή καταχωρήθηκε.", "success")
            return redirect(url_for("admin_prescriptions"))
        q = request.args.get("q", "").strip()
        stmt = select(Prescription).join(Prescription.client).join(Client.user)
        if q:
            like = f"%{q}%"
            stmt = stmt.where(or_(Client.full_name.ilike(like), Client.phone.ilike(like),
                Client.email.ilike(like), Prescription.month.ilike(like), Prescription.status.ilike(like),
                Prescription.notes.ilike(like)))
        prescriptions = db.session.scalars(stmt.order_by(Prescription.open_date.desc()).limit(300)).all()
        return render_template("admin/prescriptions.html", form=form, prescriptions=prescriptions, q=q)

    @app.route("/admin/prescriptions/<int:prescription_id>/edit", methods=["GET", "POST"])
    @role_required("admin")
    def edit_prescription(prescription_id):
        p = db.get_or_404(Prescription, prescription_id)
        form = PrescriptionForm(obj=p)
        form.client_id.choices = [(c.id, f"{c.full_name} ({c.user.username})") for c in db.session.scalars(select(Client).join(Client.user).order_by(Client.full_name)).all()]
        if request.method == "GET":
            form.client_id.data = p.client_id
        if form.validate_on_submit():
            p.client_id = form.client_id.data
            p.month = form.month.data
            p.open_date = form.open_date.data
            p.status = form.status.data
            p.notes = form.notes.data.strip() or None
            db.session.commit()
            flash("Η συνταγή ενημερώθηκε.", "success")
            return redirect(url_for("admin_prescriptions"))
        return render_template("admin/edit_prescription.html", form=form, prescription=p)

    @app.route("/admin/messages", methods=["GET", "POST"])
    @role_required("admin")
    def admin_messages():
        form = MessageForm()
        form.client_id.choices = [(0, "Όλοι οι ενεργοί πελάτες")] + [(c.id, c.full_name) for c in db.session.scalars(select(Client).join(Client.user).where(User.is_active.is_(True)).order_by(Client.full_name)).all()]
        if form.validate_on_submit():
            recipients = db.session.scalars(select(Client).join(Client.user).where(User.is_active.is_(True))).all() if form.client_id.data == 0 else [db.get_or_404(Client, form.client_id.data)]
            for client in recipients:
                db.session.add(Message(client_id=client.id, subject=form.subject.data.strip(), body=form.body.data.strip(), created_by=current_user.id))
            db.session.commit()
            flash(f"Το μήνυμα αποθηκεύτηκε για {len(recipients)} πελάτη/ες στην εφαρμογή.", "success")
            return redirect(url_for("admin_messages"))
        return render_template("admin/messages.html", form=form)

    @app.post("/admin/notifications/run")
    @role_required("admin")
    def run_notifications():
        result = send_due_notifications(app, db.session, date.today())
        flash(f"Ο έλεγχος ολοκληρώθηκε. Νέες προσπάθειες αποστολής: {result}.", "info")
        return redirect(url_for("admin_dashboard"))

    @app.get("/client")
    @role_required("client")
    def client_dashboard():
        client = current_user.client_profile
        if not client:
            abort(403)
        prescriptions = db.session.scalars(select(Prescription).where(Prescription.client_id == client.id).order_by(Prescription.open_date.desc()).limit(100)).all()
        messages = db.session.scalars(select(Message).where(Message.client_id == client.id).order_by(Message.created_at.desc()).limit(100)).all()
        return render_template("client/dashboard.html", client=client, prescriptions=prescriptions, messages=messages)

    @app.cli.command("init-db")
    def init_db():
        """Create tables. Run: flask --app app init-db"""
        db.create_all()
        print("Database tables created.")

    @app.cli.command("send-due-notifications")
    def send_due_notifications_command():
        """Send notifications for prescriptions opening today."""
        result = send_due_notifications(app, db.session, date.today())
        print(f"Notification attempts: {result}")

    @app.cli.command("create-admin")
    def create_admin():
        """Create admin from ADMIN_USERNAME and ADMIN_PASSWORD environment variables."""
        username = os.environ.get("ADMIN_USERNAME", "").strip().lower()
        password = os.environ.get("ADMIN_PASSWORD", "")
        if not username or not password:
            raise SystemExit("Set ADMIN_USERNAME and ADMIN_PASSWORD first.")
        if db.session.scalar(select(User).where(User.username == username)):
            raise SystemExit("That username already exists.")
        db.session.add(User(username=username, password_hash=generate_password_hash(password), role="admin", is_active=True))
        db.session.commit()
        print(f"Admin user {username!r} created.")

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=False)
