# Prismateams - Team Portal

Ein umfassendes, webbasiertes Team-Portal mit modernem Design und vollständiger Funktionalität für Teams. Entwickelt mit Flask (Python) und Bootstrap 5.

## 📋 Inhaltsverzeichnis

- [Features](#-features)
- [Installation](#-installation)
- [Deployment](#-deployment)
- [OnlyOffice Integration](#-onlyoffice-integration)
- [Projektstruktur](#️-projektstruktur)
- [API-Dokumentation](#-api-dokumentation)
- [Konfiguration](#-konfiguration)
- [Sicherheit](#-sicherheit)
- [Troubleshooting](#-troubleshooting)

## ✨ Features

### Kernfunktionen

#### 📊 Dashboard
- Übersicht mit Widgets für Termine, Chats und E-Mails
- Schnellzugriff auf wichtige Informationen
- Personalisierbare Ansicht

#### 💬 Chat-System
- Haupt-Chat für alle Teammitglieder
- Gruppen-Chats für spezifische Teams
- Direktnachrichten zwischen Benutzern
- Medien-Upload (Bilder, Videos, Dokumente)
- Echtzeit-Nachrichten mit WebSocket-Unterstützung
- Push-Benachrichtigungen für neue Nachrichten
- Chat-spezifische Benachrichtigungseinstellungen

#### 📁 Dateiverwaltung
- Cloud-Speicher mit Ordnerstruktur
- Dateiversionierung (letzte 3 Versionen werden gespeichert)
- **OnlyOffice Integration** - Online-Bearbeitung von Dokumenten direkt im Browser
  - Unterstützt: Word (.docx, .doc, .odt, .rtf, .txt, .md), Excel (.xlsx, .xls, .ods, .csv), PowerPoint (.pptx, .ppt, .odp), PDF (Ansicht)
- Datei-Sharing mit anderen Benutzern
- Markdown-Vorschau
- Upload von verschiedenen Dateitypen (Dokumente, Bilder, Videos, Audio)

#### 📅 Kalender
- Gemeinsame Termine mit Teilnahmestatus
- Termine erstellen, bearbeiten und löschen
- Teilnahme zusagen/absagen
- Übersichtliche Kalenderansicht
- Benachrichtigungen für anstehende Termine

#### 📧 E-Mail-Client
- Zentrales E-Mail-Konto mit IMAP/SMTP-Integration
- E-Mails lesen, senden und verwalten
- Anhänge unterstützt
- E-Mail-Berechtigungen pro Benutzer (Admin-Verwaltung)
- HTML-E-Mail-Unterstützung

#### 🔐 Zugangsdaten-Verwaltung
- Sichere Passwortverwaltung mit Verschlüsselung (Fernet)
- Verschlüsselte Speicherung sensibler Daten
- Kategorisierung und Organisation von Zugangsdaten

#### 📚 Bedienungsanleitungen
- PDF-Verwaltung (Admin-Upload)
- Zentrale Sammlung von Anleitungen und Dokumentationen
- Einfacher Zugriff für alle Teammitglieder

#### 🎨 Canvas
- Kreativbereich mit dynamischen Textfeldern
- Freies Layout für Notizen und Ideen
- Speicherung von Canvas-Inhalten

#### 📦 Inventar-Verwaltung
- Produktverwaltung mit Kategorien und Ordnern
- QR-Code-Generierung für Produkte
- Ausleihsystem mit Transaktionsverfolgung
- Inventurlisten und PDF-Export
- Produktbilder und Metadaten
- Statusverwaltung (verfügbar, ausgeliehen, fehlend)
- Scanner-Funktion für QR-Codes

#### ⚙️ Einstellungen
- Benutzerprofile verwalten
- Dark Mode Support
- Personalisierbare Akzentfarben
- Benachrichtigungseinstellungen
- System-Einstellungen (nur für Admins)
- Modulverwaltung (Admin)

### Technische Features

- ✅ **Mobile-First Design** mit Bootstrap 5
- ✅ **RESTful API** für zukünftige mobile Apps
- ✅ **Push-Benachrichtigungen** mit Web Push API (VAPID)
- ✅ **Service Worker** für Offline-Funktionalität
- ✅ **OnlyOffice Document Server Integration** für Online-Dokumentenbearbeitung
- ✅ **Benutzerverwaltung** mit Admin-Freischaltung
- ✅ **Rollenbasierte Berechtigungen** (User/Admin)
- ✅ **Dark Mode Support**
- ✅ **Personalisierbare Akzentfarben**
- ✅ **Sichere Passwort-Verschlüsselung** (Argon2)
- ✅ **Dateiversionierung** (letzte 3 Versionen)
- ✅ **Responsive Navigation** (Desktop Sidebar / Mobile Bottom Nav)
- ✅ **Setup-Assistent** für einfache Erstkonfiguration
- ✅ **Modulare Architektur** - Module können aktiviert/deaktiviert werden

## 🚀 Installation

### Voraussetzungen

- Python 3.8 oder höher
- MariaDB/MySQL (oder SQLite für Entwicklung)
- pip und virtualenv
- (Optional) OnlyOffice Document Server für Online-Dokumentenbearbeitung

### Schritt 1: Repository klonen

```bash
git clone https://github.com/yourusername/Primsateams_web_V0.git
cd Primsateams_web_V0
```

### Schritt 2: Virtual Environment erstellen

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### Schritt 3: Dependencies installieren

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Schritt 4: Umgebungsvariablen konfigurieren

Kopieren Sie `docs/env.example` nach `.env` und passen Sie die Werte an:

```bash
# Windows
copy docs\env.example .env

# Linux/Mac
cp docs/env.example .env
```

Bearbeiten Sie `.env` mit Ihren Einstellungen:

```env
# Flask Configuration
SECRET_KEY=ihr-geheimer-schluessel-hier
FLASK_ENV=development

# Database Configuration
DATABASE_URI=mysql+pymysql://username:password@localhost/teamportal

# Email Configuration
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=team@example.com
MAIL_PASSWORD=ihr-email-passwort

# IMAP Configuration
IMAP_SERVER=imap.example.com
IMAP_PORT=993
IMAP_USE_SSL=True

# OnlyOffice Configuration (optional)
ONLYOFFICE_ENABLED=False
ONLYOFFICE_DOCUMENT_SERVER_URL=/onlyoffice
ONLYOFFICE_SECRET_KEY=ihr-onlyoffice-secret-key

# Push Notifications (optional)
VAPID_PUBLIC_KEY=
VAPID_PRIVATE_KEY=
```

### Schritt 5: Datenbank initialisieren

Die Datenbank wird automatisch beim ersten Start erstellt. Sie können auch manuell initialisieren:

```bash
python scripts/init_database.py
```

### Schritt 6: Ersten Admin-User erstellen

1. Starten Sie die Anwendung
2. Registrieren Sie sich über `/register`
3. Öffnen Sie die Datenbank und setzen Sie `is_active=1` und `is_admin=1` für Ihren User

**MySQL Beispiel:**
```sql
UPDATE users SET is_active=1, is_admin=1 WHERE email='ihre@email.de';
```

Alternativ können Sie den Setup-Assistenten verwenden, der beim ersten Start automatisch erscheint.

### Schritt 7: Anwendung starten

```bash
# Entwicklungsmodus
python app.py

# Produktion mit Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
```

Die Anwendung ist jetzt unter `http://localhost:5000` verfügbar.

## 📦 Deployment

### Ubuntu Server mit OnlyOffice

Für eine vollständige Installation auf Ubuntu Server **mit OnlyOffice Document Server Integration** finden Sie eine detaillierte Schritt-für-Schritt-Anleitung in:

**[📖 UBUNTU_ONLYOFFICE_INSTALLATION.md](UBUNTU_ONLYOFFICE_INSTALLATION.md)**

Diese Anleitung umfasst:
- Ubuntu Server Setup
- OnlyOffice Document Server Installation (Docker oder DEB)
- MariaDB Konfiguration
- Nginx Reverse Proxy Setup
- SSL-Zertifikat mit Let's Encrypt
- Supervisor/Gunicorn Konfiguration
- Firewall-Einrichtung
- Troubleshooting-Tipps

### Schnelle Ubuntu Installation (ohne OnlyOffice)

```bash
# 1. Server vorbereiten
sudo apt update
sudo apt install python3 python3-pip python3-venv nginx mariadb-server supervisor -y

# 2. MariaDB konfigurieren
sudo mysql_secure_installation
sudo mysql -u root -p
```

In MySQL:
```sql
CREATE DATABASE teamportal CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'teamportal'@'localhost' IDENTIFIED BY 'sicheres-passwort';
GRANT ALL PRIVILEGES ON teamportal.* TO 'teamportal'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

```bash
# 3. Anwendung einrichten
cd /var/www
sudo git clone https://github.com/yourusername/Primsateams_web_V0.git teamportal
cd teamportal
sudo python3 -m venv venv
sudo ./venv/bin/pip install -r requirements.txt

# 4. .env konfigurieren
sudo cp docs/env.example .env
sudo nano .env

# 5. Upload-Verzeichnisse erstellen
sudo mkdir -p uploads/{files,chat,manuals,profile_pics,inventory/product_images,system}
sudo chown -R www-data:www-data /var/www/teamportal
sudo chmod -R 755 /var/www/teamportal
sudo chmod -R 775 /var/www/teamportal/uploads

# 6. Supervisor konfigurieren
sudo nano /etc/supervisor/conf.d/teamportal.conf
```

Supervisor-Konfiguration:
```ini
[program:teamportal]
directory=/var/www/teamportal
command=/var/www/teamportal/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 --timeout 600 wsgi:app
user=www-data
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/teamportal/err.log
stdout_logfile=/var/log/teamportal/out.log
environment=PATH="/var/www/teamportal/venv/bin",FLASK_ENV="production"
```

```bash
# 7. Supervisor starten
sudo mkdir -p /var/log/teamportal
sudo chown www-data:www-data /var/log/teamportal
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start teamportal

# 8. Nginx konfigurieren
sudo nano /etc/nginx/sites-available/teamportal
```

Nginx-Konfiguration:
```nginx
server {
    listen 80;
    server_name ihre-domain.de;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /static {
        alias /var/www/teamportal/app/static;
        expires 30d;
    }

    location /uploads {
        alias /var/www/teamportal/uploads;
        expires 7d;
    }
}
```

```bash
# 9. Nginx aktivieren
sudo ln -s /etc/nginx/sites-available/teamportal /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 🔧 OnlyOffice Integration

Prismateams unterstützt die Integration mit OnlyOffice Document Server für die Online-Bearbeitung von Dokumenten direkt im Browser.

### Unterstützte Dateitypen

- **Word-Dokumente**: .docx, .doc, .odt, .rtf, .txt, .md, .markdown
- **Excel-Tabellen**: .xlsx, .xls, .ods, .csv
- **PowerPoint-Präsentationen**: .pptx, .ppt, .odp
- **PDF**: .pdf (nur Ansicht)

### Konfiguration

1. **OnlyOffice Document Server installieren**

   Siehe [UBUNTU_ONLYOFFICE_INSTALLATION.md](UBUNTU_ONLYOFFICE_INSTALLATION.md) für detaillierte Installationsanweisungen.

2. **OnlyOffice in der .env aktivieren**

   ```env
   ONLYOFFICE_ENABLED=True
   ONLYOFFICE_DOCUMENT_SERVER_URL=/onlyoffice
   ONLYOFFICE_SECRET_KEY=ihr-jwt-secret-key
   ```

3. **Nginx konfigurieren**

   Die Nginx-Konfiguration muss einen Proxy für OnlyOffice enthalten:

   ```nginx
   location /onlyoffice {
       proxy_pass http://127.0.0.1:8080;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto $scheme;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection "upgrade";
       proxy_connect_timeout 600;
       proxy_send_timeout 600;
       proxy_read_timeout 600;
       send_timeout 600;
   }
   ```

### JWT-Authentifizierung

Für Produktionsumgebungen wird die Verwendung von JWT-Authentifizierung empfohlen:

- Der `ONLYOFFICE_SECRET_KEY` in der `.env` muss mit dem JWT-Secret von OnlyOffice übereinstimmen
- Bei Docker-Installation: Verwenden Sie `-e JWT_SECRET=ihr-secret-key` beim Start
- Bei DEB-Installation: Der JWT-Secret wird während der Installation angezeigt

### Verwendung

Nach der Aktivierung können Benutzer:
- Dokumente direkt im Browser öffnen und bearbeiten
- Änderungen werden automatisch gespeichert
- Mehrere Benutzer können gleichzeitig an einem Dokument arbeiten (Kollaboration)

## 🗂️ Projektstruktur

```
Primsateams_web_V0/
├── app/
│   ├── __init__.py              # Flask App Factory
│   ├── models/                   # Datenbank-Modelle
│   │   ├── user.py
│   │   ├── chat.py
│   │   ├── file.py
│   │   ├── calendar.py
│   │   ├── email.py
│   │   ├── credential.py
│   │   ├── manual.py
│   │   ├── canvas.py
│   │   ├── inventory.py
│   │   ├── notification.py
│   │   ├── settings.py
│   │   └── whitelist.py
│   ├── blueprints/               # Flask Blueprints (Module)
│   │   ├── auth.py
│   │   ├── dashboard.py
│   │   ├── chat.py
│   │   ├── files.py
│   │   ├── calendar.py
│   │   ├── email.py
│   │   ├── credentials.py
│   │   ├── manuals.py
│   │   ├── canvas.py
│   │   ├── inventory.py
│   │   ├── settings.py
│   │   ├── setup.py
│   │   └── api.py
│   ├── templates/                # Jinja2 Templates
│   │   ├── base.html
│   │   ├── auth/
│   │   ├── dashboard/
│   │   ├── chat/
│   │   ├── files/
│   │   ├── calendar/
│   │   ├── email/
│   │   ├── credentials/
│   │   ├── manuals/
│   │   ├── canvas/
│   │   ├── inventory/
│   │   ├── settings/
│   │   ├── setup/
│   │   └── errors/
│   ├── static/                   # Statische Dateien
│   │   ├── css/
│   │   ├── js/
│   │   ├── img/
│   │   ├── sw.js                  # Service Worker
│   │   └── manifest.json
│   ├── tasks/                     # Hintergrund-Tasks
│   │   └── notification_scheduler.py
│   └── utils/                     # Hilfsfunktionen
│       ├── common.py
│       ├── email_sender.py
│       ├── notifications.py
│       ├── onlyoffice.py
│       ├── pdf_generator.py
│       └── qr_code.py
├── docs/                          # Dokumentation
│   ├── README.md
│   ├── UBUNTU_ONLYOFFICE_INSTALLATION.md
│   ├── API_Übersicht.md
│   ├── INSTALLATION.md
│   └── env.example
├── migrations/                    # Datenbank-Migrationen
├── scripts/                       # Hilfsskripte
│   ├── init_database.py
│   ├── generate_vapid_keys.py
│   ├── check_vapid_keys.py
│   └── deploy.py
├── uploads/                       # Upload-Verzeichnis
│   ├── files/
│   ├── chat/
│   ├── manuals/
│   ├── profile_pics/
│   └── inventory/
├── app.py                         # Einstiegspunkt (Entwicklung)
├── wsgi.py                        # WSGI-Einstiegspunkt (Produktion)
├── config.py                      # Konfiguration
├── requirements.txt               # Python Dependencies
└── .gitignore
```

## 🔑 API-Dokumentation

Alle API-Endpunkte sind unter `/api/` verfügbar. Eine detaillierte API-Dokumentation finden Sie in:

**[📖 API_Übersicht.md](API_Übersicht.md)**

### Wichtige API-Endpunkte

#### Benutzer
- `GET /api/users` - Alle aktiven Benutzer
- `GET /api/users/<id>` - Einzelner Benutzer

#### Chats
- `GET /api/chats` - Alle Chats des Benutzers
- `GET /api/chats/<id>/messages` - Nachrichten eines Chats
- `POST /api/chats/<id>/messages` - Neue Nachricht senden

#### Kalender
- `GET /api/events` - Alle Termine
- `GET /api/events/<id>` - Einzelner Termin
- `POST /api/events` - Neuen Termin erstellen

#### Dateien
- `GET /api/files?folder_id=<id>` - Dateien in einem Ordner
- `GET /api/folders?parent_id=<id>` - Unterordner
- `POST /api/files` - Datei hochladen

#### Dashboard
- `GET /api/dashboard/stats` - Dashboard-Statistiken

#### Push Notifications
- `POST /api/push/subscribe` - Push-Benachrichtigung abonnieren
- `GET /api/push/vapid-public-key` - VAPID Public Key abrufen
- `POST /api/push/test` - Test-Benachrichtigung senden (Admin)

## ⚙️ Konfiguration

### Umgebungsvariablen

Die wichtigsten Konfigurationsoptionen werden über die `.env`-Datei gesteuert:

#### Flask-Konfiguration
- `SECRET_KEY` - Geheimer Schlüssel für Sessions (erforderlich)
- `FLASK_ENV` - Umgebung (development/production)

#### Datenbank
- `DATABASE_URI` - Datenbankverbindungs-URI (SQLite/MySQL/MariaDB)

#### E-Mail
- `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS` - SMTP-Einstellungen
- `IMAP_SERVER`, `IMAP_PORT`, `IMAP_USE_SSL` - IMAP-Einstellungen

#### OnlyOffice
- `ONLYOFFICE_ENABLED` - OnlyOffice aktivieren/deaktivieren
- `ONLYOFFICE_DOCUMENT_SERVER_URL` - URL zum OnlyOffice Server
- `ONLYOFFICE_SECRET_KEY` - JWT-Secret für OnlyOffice
- `ONLYOFFICE_PUBLIC_URL` - Öffentliche URL der Flask-App (für Callbacks)

#### Push Notifications
- `VAPID_PUBLIC_KEY` - VAPID Public Key
- `VAPID_PRIVATE_KEY` - VAPID Private Key

Eine vollständige Liste aller verfügbaren Konfigurationsoptionen finden Sie in `docs/env.example`.

### VAPID Keys generieren

Für Push-Benachrichtigungen müssen VAPID Keys generiert werden:

```bash
python scripts/generate_vapid_keys.py
```

Die generierten Keys werden in der `.env`-Datei gespeichert.

## 🔒 Sicherheit

### Implementierte Sicherheitsmaßnahmen

- **Passwort-Hashing**: Argon2 für sichere Passwort-Speicherung
- **Verschlüsselung**: Fernet (symmetrische Verschlüsselung) für Zugangsdaten
- **CSRF-Schutz**: Flask-WTF für Cross-Site-Request-Forgery-Schutz
- **XSS-Schutz**: Jinja2 Auto-Escaping verhindert Cross-Site-Scripting
- **SQL-Injection-Schutz**: SQLAlchemy ORM verhindert SQL-Injection
- **Rollenbasierte Zugriffskontrolle**: User/Admin-Rollen mit granularer Berechtigung
- **Session-Sicherheit**: Sichere Cookie-Einstellungen für Produktion
- **Rate Limiting**: Flask-Limiter für API-Endpunkte

### Best Practices für Produktion

1. **Starken SECRET_KEY verwenden**: Generieren Sie einen sicheren Schlüssel mit `openssl rand -hex 32`
2. **HTTPS aktivieren**: Verwenden Sie SSL/TLS-Zertifikate (z.B. Let's Encrypt)
3. **Datenbank-Passwort sicher wählen**: Verwenden Sie ein starkes, eindeutiges Passwort
4. **OnlyOffice JWT aktivieren**: Für Produktion sollte JWT-Authentifizierung aktiviert sein
5. **Firewall konfigurieren**: Beschränken Sie den Zugriff auf notwendige Ports
6. **Regelmäßige Backups**: Erstellen Sie regelmäßig Backups der Datenbank und Uploads
7. **System-Updates**: Halten Sie das System und Dependencies aktuell

## 📝 Berechtigungen

### Standard-Benutzer
- Dashboard anzeigen
- Chats lesen und schreiben
- Dateien hochladen, bearbeiten, löschen
- Termine erstellen, bearbeiten, Teilnahme zusagen/absagen
- E-Mails lesen und senden (wenn berechtigt)
- Zugangsdaten erstellen, bearbeiten, löschen
- Anleitungen anzeigen
- Canvas erstellen und bearbeiten
- Inventar anzeigen und ausleihen

### Administratoren
Alle Benutzer-Rechte plus:
- Benutzer aktivieren/deaktivieren/löschen
- Admin-Rechte vergeben
- Termine löschen
- Teilnehmer von Terminen entfernen
- E-Mail-Berechtigungen verwalten
- Anleitungen hochladen und löschen
- System-Einstellungen bearbeiten
- Modulverwaltung (Module aktivieren/deaktivieren)
- Inventar vollständig verwalten

## 🐛 Troubleshooting

### Datenbank-Verbindungsfehler

**Problem**: Die Anwendung kann nicht auf die Datenbank zugreifen.

**Lösung**:
- Überprüfen Sie die `DATABASE_URI` in `.env`
- Stellen Sie sicher, dass MariaDB/MySQL läuft: `sudo systemctl status mariadb`
- Testen Sie die Verbindung: `mysql -u teamportal -p teamportal`

### E-Mails werden nicht gesendet

**Problem**: E-Mails werden nicht versendet.

**Lösung**:
- Überprüfen Sie SMTP-Einstellungen in `.env`
- Testen Sie die Verbindung mit einem E-Mail-Test-Tool
- Prüfen Sie Firewall-Einstellungen für Port 587/465
- Für Gmail: Verwenden Sie ein App-Passwort statt des normalen Passworts

### Uploads schlagen fehl

**Problem**: Datei-Uploads funktionieren nicht.

**Lösung**:
```bash
sudo chmod -R 775 uploads/
sudo chown -R www-data:www-data uploads/
```

### OnlyOffice funktioniert nicht

**Problem**: OnlyOffice öffnet Dokumente nicht oder zeigt Fehler.

**Lösung**:
- Überprüfen Sie, ob OnlyOffice läuft: `sudo docker ps` (Docker) oder `sudo systemctl status ds-docservice` (DEB)
- Prüfen Sie die Nginx-Konfiguration für `/onlyoffice`
- Stellen Sie sicher, dass `ONLYOFFICE_SECRET_KEY` mit dem OnlyOffice JWT-Secret übereinstimmt
- Prüfen Sie die OnlyOffice-Logs: `sudo docker logs <container-id>`

### Push-Benachrichtigungen funktionieren nicht

**Problem**: Push-Benachrichtigungen werden nicht empfangen.

**Lösung**:
- Überprüfen Sie, ob VAPID Keys in `.env` gesetzt sind
- Generieren Sie neue Keys mit `python scripts/generate_vapid_keys.py`
- Stellen Sie sicher, dass HTTPS verwendet wird (Push funktioniert nicht über HTTP)
- Prüfen Sie die Browser-Konsole auf Fehler
- Überprüfen Sie die Service Worker-Registrierung

### Static Files werden nicht geladen

**Problem**: CSS/JS-Dateien werden nicht geladen.

**Lösung**:
- Überprüfen Sie die Nginx-Konfiguration für `/static`
- Stellen Sie sicher, dass der Pfad korrekt ist: `/var/www/teamportal/app/static`
- Prüfen Sie die Berechtigungen: `sudo chmod -R 755 app/static`

### 502 Bad Gateway

**Problem**: Nginx zeigt 502 Bad Gateway Fehler.

**Lösung**:
- Prüfen Sie, ob Gunicorn läuft: `sudo supervisorctl status teamportal`
- Überprüfen Sie die Logs: `sudo tail -50 /var/log/teamportal/err.log`
- Starten Sie Gunicorn neu: `sudo supervisorctl restart teamportal`

## 📚 Weitere Dokumentation

- **[INSTALLATION.md](INSTALLATION.md)** - Detaillierte Installationsanleitung
- **[UBUNTU_ONLYOFFICE_INSTALLATION.md](UBUNTU_ONLYOFFICE_INSTALLATION.md)** - Ubuntu Server Installation mit OnlyOffice
- **[API_Übersicht.md](API_Übersicht.md)** - Vollständige API-Dokumentation

## 📜 Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert. Siehe [LICENSE](LICENSE) für Details.

## 👥 Beitrag

Beiträge sind willkommen! Bitte erstellen Sie einen Pull Request oder öffnen Sie ein Issue.

## 📧 Support

Bei Fragen oder Problemen:
1. Prüfen Sie die Dokumentation
2. Überprüfen Sie die Logs
3. Öffnen Sie ein Issue auf GitHub

---

**Entwickelt mit ❤️ für effiziente Team-Zusammenarbeit**
