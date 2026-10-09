# CHRYSPHARMACY — Flask starter

Αρχική εφαρμογή για διαχείριση πελατών, μηνιαίων συνταγών και μηνυμάτων, με ξεχωριστές σελίδες σύνδεσης πελατών και διαχειριστή.

## Περιλαμβάνει

- Flask + PostgreSQL / SQLAlchemy.
- Ξεχωριστά `/login/client` και `/login/admin`.
- Ρόλους χρήστη και προστατευμένες σελίδες.
- Δημιουργία πελατών με ασφαλές hash κωδικού.
- Καταχώρηση, αναζήτηση και επεξεργασία συνταγών.
- Μηνύματα admin που εμφανίζονται στο client portal.
- Καθημερινό/χειροκίνητο notification runner και log με αποφυγή διπλής αποστολής ανά συνταγή/κανάλι.
- Email μέσω SMTP όταν διαμορφωθεί.
- Σημείο επέκτασης για SMS.to.

## Προαπαιτούμενα

- Python 3.11 ή νεότερη (προτείνεται).
- PostgreSQL 14+.
- Πρόσβαση σε SMTP server για email.

## 1. Δημιουργία βάσης PostgreSQL

Στο `psql` ως διαχειριστής PostgreSQL:

```sql
CREATE USER chryspharmacy WITH PASSWORD 'ΒΑΛΕ_ΕΝΑ_ΙΣΧΥΡΟ_PASSWORD';
CREATE DATABASE chryspharmacy OWNER chryspharmacy;
```

Χρησιμοποίησε το ίδιο password στο `DATABASE_URL`, με URL-encoding αν περιέχει ειδικούς χαρακτήρες.

## 2. Εγκατάσταση

Linux/macOS:

```bash
cd chryspharmacy
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Windows PowerShell:

```powershell
cd chryspharmacy
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Άλλαξε τις τιμές στο `.env`. Δημιούργησε ισχυρό `SECRET_KEY`, π.χ. με:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Φόρτωσε τις μεταβλητές περιβάλλοντος από το `.env` πριν τρέξεις Flask. Η εφαρμογή δεν φορτώνει αυτόματα το `.env` για να μην κρύβεται η διαχείριση των secrets. Για τοπική ανάπτυξη μπορείς να προσθέσεις `from dotenv import load_dotenv; load_dotenv()` στην αρχή του `app.py`, πριν από τη δημιουργία του app, ή να εξάγεις τις μεταβλητές από το shell. Σε production προτίμησε environment variables/secret manager.

Η εφαρμογή φορτώνει αυτόματα το `.env` μέσω `python-dotenv`.

## 3. Δημιουργία πινάκων και admin

Linux/macOS:

```bash
export FLASK_APP=app.py
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD='ΧΡΗΣΙΜΟΠΟΙΗΣΕ_ΙΣΧΥΡΟ_ΜΟΝΑΔΙΚΟ_PASSWORD'
flask init-db
flask create-admin
flask run --host 127.0.0.1 --port 5000
```

Windows PowerShell:

```powershell
$env:FLASK_APP="app.py"
$env:ADMIN_USERNAME="admin"
$env:ADMIN_PASSWORD="ΧΡΗΣΙΜΟΠΟΙΗΣΕ_ΙΣΧΥΡΟ_ΜΟΝΑΔΙΚΟ_PASSWORD"
flask init-db
flask create-admin
flask run --host 127.0.0.1 --port 5000
```

Άνοιξε `http://127.0.0.1:5000`. Η εντολή `flask run` είναι μόνο για ανάπτυξη, όχι για δημόσια παραγωγική λειτουργία.

## 4. Email

Συμπλήρωσε `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` και `SMTP_FROM` στο περιβάλλον. Η εφαρμογή χρησιμοποιεί STARTTLS. Δοκίμασε αρχικά με εσωτερική διεύθυνση email.

## 5. SMS.to — σημαντικό

Το `send_sms()` είναι σκόπιμα placeholder και **δεν στέλνει πραγματικά SMS**. Πρέπει να συμπληρωθεί με το endpoint, το payload και τον μηχανισμό authentication που αναγράφονται στην τρέχουσα τεκμηρίωση του λογαριασμού SMS.to. Δεν υποθέτουμε API endpoint για να αποφύγουμε λανθασμένες ή μη ασφαλείς κλήσεις.

## 6. Αυτόματη καθημερινή εκτέλεση

Η αρχική έκδοση παρέχει κουμπί «Έλεγχος ειδοποιήσεων τώρα» στον admin και CLI command:

```bash
flask send-due-notifications
```

Για καθημερινή αυτόματη λειτουργία, προγραμμάτισε την εντολή με cron ή systemd timer. Παράδειγμα cron στις 08:00 (ρύθμισε τα σωστά paths και environment variables για τον server):

```cron
0 8 * * * cd /path/to/chryspharmacy && /path/to/chryspharmacy/.venv/bin/flask --app app send-due-notifications
```

Μην ξεκινάς scheduler σε κάθε worker web, γιατί μπορεί να γίνουν διπλές αποστολές. Το τρέχον log έχει μοναδικό περιορισμό ανά συνταγή και κανάλι.

Πριν ενεργοποιήσεις το job σε production, ολοκλήρωσε και δοκίμασε το SMS.to integration και ρύθμισε τα SMTP credentials.

## 7. Παραγωγική λειτουργία και ασφάλεια

- Πίσω από reverse proxy με HTTPS.
- `COOKIE_SECURE=true` μόνο όταν λειτουργεί μέσω HTTPS.
- Κράτησε `.env` έξω από git και backups με κατάλληλα δικαιώματα.
- Μη χρησιμοποιείς πραγματικά δεδομένα ασθενών σε δοκιμές.
- Ρύθμισε backups, ενημερώσεις ασφαλείας, rate limiting και monitoring.
- Πρόσθεσε migrations με Flask-Migrate πριν αλλάξει το schema σε παραγωγή.
- Έλεγξε GDPR, νόμιμη βάση επεξεργασίας και πολιτική διατήρησης πριν τη χρήση.
- Οι ειδοποιήσεις είναι ουδέτερες και δεν αναφέρουν φάρμακα ή διάγνωση.

## Περιορισμοί της αρχικής έκδοσης

- Δεν υπάρχει ακόμη αλλαγή/επαναφορά κωδικού από πελάτη.
- Δεν υπάρχει ακόμη ιστορικό ανάγνωσης μηνυμάτων.
- Δεν υπάρχει αυτόματο scheduler εγκατεστημένο.
- Η ενσωμάτωση SMS.to χρειάζεται συμπλήρωση και δοκιμή.
- Το `init-db` προορίζεται μόνο για αρχική εγκατάσταση· σε παραγωγή χρησιμοποίησε migrations.


## Προσθήκη πεδίου ΑΜΚΑ σε υπάρχουσα βάση

Η αλλαγή προσθέτει πεδίο ΑΜΚΑ στην καρτέλα πελάτη και στην αναζήτηση πελατών. Αν η βάση δημιουργήθηκε ήδη πριν από αυτή την αλλαγή, το `flask init-db` δεν τροποποιεί υπάρχοντες πίνακες. Εκτέλεσε μία φορά στην PostgreSQL:

```sql
ALTER TABLE clients ADD COLUMN amka VARCHAR(11);
CREATE INDEX ix_clients_amka ON clients (amka);
```

Το πεδίο είναι προαιρετικό και, όταν συμπληρώνεται, δέχεται 11 ψηφία. Ο ΑΜΚΑ είναι ευαίσθητο προσωπικό δεδομένο· περιόρισε την πρόσβαση, χρησιμοποίησε HTTPS και μην τον συμπεριλαμβάνεις σε SMS/email. Το πεδίο «Μήνας (YYYY-MM)» παραμένει στην καταχώρηση συνταγής, επειδή περιγράφει τον μήνα της συνταγής και είναι διαφορετικό από τον ΑΜΚΑ του πελάτη.
