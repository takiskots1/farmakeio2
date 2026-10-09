from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, DateField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, Email, Regexp, EqualTo

class LoginForm(FlaskForm):
    username = StringField("Όνομα χρήστη", validators=[DataRequired(), Length(max=80)])
    password = PasswordField("Κωδικός πρόσβασης", validators=[DataRequired(), Length(max=256)])
    remember = BooleanField("Να παραμείνω συνδεδεμένος")
    submit = SubmitField("Σύνδεση")

class ClientForm(FlaskForm):
    full_name = StringField("Ονοματεπώνυμο", validators=[DataRequired(), Length(max=160)])
    amka = StringField("ΑΜΚΑ", validators=[Optional(), Length(min=11, max=11), Regexp(r"^\d{11}$", message="Ο ΑΜΚΑ πρέπει να αποτελείται από 11 ψηφία.")])
    phone = StringField("Τηλέφωνο", validators=[Optional(), Length(max=40)])
    email = StringField("Email", validators=[Optional(), Email(), Length(max=254)])
    username = StringField("Όνομα χρήστη", validators=[DataRequired(), Length(min=3, max=80), Regexp(r"^[a-zA-Z0-9_.-]+$", message="Χρησιμοποίησε λατινικούς χαρακτήρες, αριθμούς, τελεία, παύλα ή κάτω παύλα.")])
    password = PasswordField("Προσωρινός κωδικός", validators=[DataRequired(), Length(min=12, max=128)])
    sms_consent = BooleanField("Έχει καταγραφεί συγκατάθεση για SMS")
    email_consent = BooleanField("Έχει καταγραφεί συγκατάθεση για email")
    submit = SubmitField("Δημιουργία πελάτη")

class PrescriptionForm(FlaskForm):
    client_id = SelectField("Πελάτης", coerce=int, validators=[DataRequired()])
    month = StringField("Μήνας (YYYY-MM)", validators=[DataRequired(), Regexp(r"^\d{4}-(0[1-9]|1[0-2])$", message="Χρησιμοποίησε μορφή YYYY-MM.")])
    open_date = DateField("Ημερομηνία ανοίγματος", validators=[DataRequired()], format="%Y-%m-%d")
    status = SelectField("Κατάσταση", choices=[
        ("αναμένεται", "Αναμένεται"), ("άνοιξε", "Άνοιξε"),
        ("ενημερώθηκε", "Ενημερώθηκε"), ("ολοκληρώθηκε", "Ολοκληρώθηκε")
    ], validators=[DataRequired()])
    notes = TextAreaField("Σχόλια (μην καταχωρείς περιττά δεδομένα υγείας)", validators=[Optional(), Length(max=2000)])
    submit = SubmitField("Αποθήκευση")

class MessageForm(FlaskForm):
    client_id = SelectField("Παραλήπτης", coerce=int, validators=[DataRequired()])
    subject = StringField("Θέμα", validators=[DataRequired(), Length(max=160)])
    body = TextAreaField("Μήνυμα", validators=[DataRequired(), Length(max=4000)])
    submit = SubmitField("Αποστολή στην εφαρμογή")
