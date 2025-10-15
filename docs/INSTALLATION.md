# Team Portal - Installationsanleitung

## Schnellstart (Entwicklung)

### 1. Voraussetzungen prüfen
```bash
python --version  # Python 3.8+ erforderlich
```

### 2. Projekt einrichten
```bash
# Repository klonen
git clone https://github.com/yourusername/teamportal.git
cd teamportal

# Virtual Environment erstellen
python -m venv venv

# Virtual Environment aktivieren
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Dependencies installieren
pip install -r requirements.txt
```

### 3. Umgebungsvariablen konfigurieren
```bash
# Kopiere die Beispiel-Datei
# Windows:
copy env.example .env
# Linux/Mac:
cp env.example .env

# Bearbeite .env und setze mindestens:
# - SECRET_KEY (generiere einen sicheren Schlüssel)
# - DATABASE_URI (für SQLite: sqlite:///teamportal.db)
```

### 4. Datenbank-Setup (Entwicklung)

#### Datenbank erstellen (für MySQL/MariaDB)

**Für MySQL:**
```sql
CREATE DATABASE teamportal CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

**Für MariaDB:**
```sql
CREATE DATABASE teamportal CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

**Datenbankbenutzer erstellen (optional):**
```sql
CREATE USER 'teamportal'@'localhost' IDENTIFIED BY 'IhrSicheresPasswort123!';
GRANT ALL PRIVILEGES ON teamportal.* TO 'teamportal'@'localhost';
FLUSH PRIVILEGES;
```

#### Option A: Automatische Tabellenerstellung (Empfohlen)
Die Anwendung erstellt die Tabellen automatisch beim ersten Start. Starte einfach die App:

```bash
python app.py
```

Die Datenbank-Tabellen werden automatisch erstellt.

#### Option B: Manuelle Tabellenerstellung
Falls du die Tabellen manuell erstellen möchtest, führe folgende SQL-Befehle aus:

**Für SQLite:**
```sql
-- Users Tabelle
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT 0 NOT NULL,
    is_admin BOOLEAN DEFAULT 0 NOT NULL,
    profile_picture VARCHAR(255),
    accent_color VARCHAR(7) DEFAULT '#0d6efd',
    dark_mode BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME
);

CREATE INDEX ix_users_email ON users (email);

-- Chats Tabelle
CREATE TABLE chats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    is_main_chat BOOLEAN DEFAULT 0 NOT NULL,
    is_direct_message BOOLEAN DEFAULT 0 NOT NULL,
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users (id)
);

-- Chat Members Tabelle
CREATE TABLE chat_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_read_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chat_id) REFERENCES chats (id),
    FOREIGN KEY (user_id) REFERENCES users (id),
    UNIQUE (chat_id, user_id)
);

-- Chat Messages Tabelle
CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    sender_id INTEGER NOT NULL,
    content TEXT,
    message_type VARCHAR(20) DEFAULT 'text' NOT NULL,
    media_url VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    edited_at DATETIME,
    is_deleted BOOLEAN DEFAULT 0,
    FOREIGN KEY (chat_id) REFERENCES chats (id),
    FOREIGN KEY (sender_id) REFERENCES users (id)
);

CREATE INDEX ix_chat_messages_created_at ON chat_messages (created_at);

-- Calendar Events Tabelle
CREATE TABLE calendar_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    location VARCHAR(255),
    created_by INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users (id)
);

CREATE INDEX ix_calendar_events_start_time ON calendar_events (start_time);

-- Event Participants Tabelle
CREATE TABLE event_participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    responded_at DATETIME,
    FOREIGN KEY (event_id) REFERENCES calendar_events (id),
    FOREIGN KEY (user_id) REFERENCES users (id),
    UNIQUE (event_id, user_id)
);

-- Folders Tabelle
CREATE TABLE folders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    parent_id INTEGER,
    created_by INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES folders (id),
    FOREIGN KEY (created_by) REFERENCES users (id)
);

-- Files Tabelle
CREATE TABLE files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    folder_id INTEGER,
    uploaded_by INTEGER NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type VARCHAR(100),
    version_number INTEGER DEFAULT 1 NOT NULL,
    is_current BOOLEAN DEFAULT 1 NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (folder_id) REFERENCES folders (id),
    FOREIGN KEY (uploaded_by) REFERENCES users (id)
);

-- File Versions Tabelle
CREATE TABLE file_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    version_number INTEGER NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    uploaded_by INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (file_id) REFERENCES files (id),
    FOREIGN KEY (uploaded_by) REFERENCES users (id)
);

-- Email Messages Tabelle
CREATE TABLE email_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid VARCHAR(100) UNIQUE,
    message_id VARCHAR(255) UNIQUE,
    subject VARCHAR(500) NOT NULL,
    sender VARCHAR(255) NOT NULL,
    recipients TEXT NOT NULL,
    cc TEXT,
    bcc TEXT,
    body_text TEXT,
    body_html TEXT,
    is_read BOOLEAN DEFAULT 0,
    is_sent BOOLEAN DEFAULT 0,
    has_attachments BOOLEAN DEFAULT 0,
    sent_by_user_id INTEGER,
    received_at DATETIME,
    sent_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (sent_by_user_id) REFERENCES users (id)
);

CREATE INDEX ix_email_messages_received_at ON email_messages (received_at);

-- Email Attachments Tabelle
CREATE TABLE email_attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_id INTEGER NOT NULL,
    filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    size INTEGER NOT NULL,
    content BLOB,
    file_path VARCHAR(500),
    is_inline BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (email_id) REFERENCES email_messages (id)
);

-- Email Permissions Tabelle
CREATE TABLE email_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    can_read BOOLEAN DEFAULT 1 NOT NULL,
    can_send BOOLEAN DEFAULT 1 NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- System Settings Tabelle
CREATE TABLE system_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    description VARCHAR(255),
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Für MySQL/MariaDB:**
```sql
-- Users Tabelle
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT FALSE NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE NOT NULL,
    profile_picture VARCHAR(255),
    accent_color VARCHAR(7) DEFAULT '#0d6efd',
    dark_mode BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login DATETIME,
    INDEX ix_users_email (email)
);

-- Chats Tabelle
CREATE TABLE chats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    is_main_chat BOOLEAN DEFAULT FALSE NOT NULL,
    is_direct_message BOOLEAN DEFAULT FALSE NOT NULL,
    created_by INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users (id)
);

-- Chat Members Tabelle
CREATE TABLE chat_members (
    id INT AUTO_INCREMENT PRIMARY KEY,
    chat_id INT NOT NULL,
    user_id INT NOT NULL,
    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_read_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chat_id) REFERENCES chats (id),
    FOREIGN KEY (user_id) REFERENCES users (id),
    UNIQUE KEY unique_chat_member (chat_id, user_id)
);

-- Chat Messages Tabelle
CREATE TABLE chat_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    chat_id INT NOT NULL,
    sender_id INT NOT NULL,
    content TEXT,
    message_type VARCHAR(20) DEFAULT 'text' NOT NULL,
    media_url VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    edited_at DATETIME,
    is_deleted BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (chat_id) REFERENCES chats (id),
    FOREIGN KEY (sender_id) REFERENCES users (id),
    INDEX ix_chat_messages_created_at (created_at)
);

-- Calendar Events Tabelle
CREATE TABLE calendar_events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    location VARCHAR(255),
    created_by INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users (id),
    INDEX ix_calendar_events_start_time (start_time)
);

-- Event Participants Tabelle
CREATE TABLE event_participants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT NOT NULL,
    user_id INT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    responded_at DATETIME,
    FOREIGN KEY (event_id) REFERENCES calendar_events (id),
    FOREIGN KEY (user_id) REFERENCES users (id),
    UNIQUE KEY unique_event_participant (event_id, user_id)
);

-- Folders Tabelle
CREATE TABLE folders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    parent_id INT,
    created_by INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES folders (id),
    FOREIGN KEY (created_by) REFERENCES users (id)
);

-- Files Tabelle
CREATE TABLE files (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    folder_id INT,
    uploaded_by INT NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INT NOT NULL,
    mime_type VARCHAR(100),
    version_number INT DEFAULT 1 NOT NULL,
    is_current BOOLEAN DEFAULT TRUE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (folder_id) REFERENCES folders (id),
    FOREIGN KEY (uploaded_by) REFERENCES users (id)
);

-- File Versions Tabelle
CREATE TABLE file_versions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    file_id INT NOT NULL,
    version_number INT NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INT NOT NULL,
    uploaded_by INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (file_id) REFERENCES files (id),
    FOREIGN KEY (uploaded_by) REFERENCES users (id)
);

-- Email Messages Tabelle
CREATE TABLE email_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    uid VARCHAR(100) UNIQUE,
    message_id VARCHAR(255) UNIQUE,
    subject VARCHAR(500) NOT NULL,
    sender VARCHAR(255) NOT NULL,
    recipients TEXT NOT NULL,
    cc TEXT,
    bcc TEXT,
    body_text TEXT,
    body_html TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    is_sent BOOLEAN DEFAULT FALSE,
    has_attachments BOOLEAN DEFAULT FALSE,
    sent_by_user_id INT,
    received_at DATETIME,
    sent_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (sent_by_user_id) REFERENCES users (id),
    INDEX ix_email_messages_received_at (received_at)
);

-- Email Attachments Tabelle
CREATE TABLE email_attachments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email_id INT NOT NULL,
    filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    size INT NOT NULL,
    content LONGBLOB,
    file_path VARCHAR(500),
    is_inline BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (email_id) REFERENCES email_messages (id)
);

-- Email Permissions Tabelle
CREATE TABLE email_permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE NOT NULL,
    can_read BOOLEAN DEFAULT TRUE NOT NULL,
    can_send BOOLEAN DEFAULT TRUE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- System Settings Tabelle
CREATE TABLE system_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    description VARCHAR(255),
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### Hinzufügen der 'group_avatar'-Spalte (Optional)
Falls du das Gruppenbild-Feature für Chats verwenden möchtest, füge diese Spalte hinzu:

```sql
-- Für SQLite:
ALTER TABLE chats ADD COLUMN group_avatar VARCHAR(255);

-- Für MySQL/MariaDB:
ALTER TABLE chats ADD COLUMN group_avatar VARCHAR(255) NULL;
```

### 5. Anwendung starten
```bash
python app.py
```

Die Anwendung läuft nun auf `http://localhost:5000`

### 6. Ersten Admin erstellen

1. Öffne `http://localhost:5000`
2. Registriere einen neuen Benutzer
3. Aktiviere den Benutzer manuell in der Datenbank:

**Für SQLite:**
```bash
sqlite3 teamportal.db
UPDATE users SET is_active=1, is_admin=1 WHERE email='ihre@email.de';
.exit
```

**Für MySQL/MariaDB:**
```bash
mysql -u root -p
USE teamportal;
UPDATE users SET is_active=1, is_admin=1 WHERE email='ihre@email.de';
EXIT;
```

4. Melde dich mit deinem neuen Admin-Account an!

## Produktionsinstallation (Ubuntu Server)

### Schritt 1: System vorbereiten
```bash
# System aktualisieren
sudo apt update && sudo apt upgrade -y

# Notwendige Pakete installieren
sudo apt install -y python3 python3-pip python3-venv \
    nginx mariadb-server git supervisor
```

### Schritt 2: MariaDB einrichten
```bash
# MariaDB absichern
sudo mysql_secure_installation

# Datenbank und Benutzer erstellen
sudo mysql -u root -p
```

In der MySQL-Konsole:
```sql
CREATE DATABASE teamportal CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'teamportal'@'localhost' IDENTIFIED BY 'IhrSicheresPasswort123!';
GRANT ALL PRIVILEGES ON teamportal.* TO 'teamportal'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### Schritt 3: Anwendung installieren
```bash
# Verzeichnis erstellen
sudo mkdir -p /var/www
cd /var/www

# Repository klonen
sudo git clone https://github.com/yourusername/teamportal.git
cd teamportal

# Virtual Environment erstellen
sudo python3 -m venv venv

# Dependencies installieren
sudo ./venv/bin/pip install -r requirements.txt
```

### Schritt 4: Konfiguration
```bash
# .env erstellen
sudo cp env.example .env
sudo nano .env
```

Setze folgende Werte in `.env`:
```env
SECRET_KEY=GeneriereSicherenSchlüsselMit32ZeichenOderMehr
DATABASE_URI=mysql+pymysql://teamportal:IhrSicheresPasswort123!@localhost/teamportal
FLASK_ENV=production

# E-Mail-Einstellungen
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=ihr-email@gmail.com
MAIL_PASSWORD=ihr-app-passwort

# IMAP
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993
IMAP_USE_SSL=True
```

### Schritt 5: Berechtigungen setzen
```bash
# Upload-Verzeichnisse erstellen
sudo mkdir -p uploads/{files,chat,manuals,profile_pics}

# Berechtigungen setzen
sudo chown -R www-data:www-data /var/www/teamportal
sudo chmod -R 755 /var/www/teamportal
sudo chmod -R 775 /var/www/teamportal/uploads
```

### Schritt 6: Supervisor konfigurieren
```bash
sudo nano /etc/supervisor/conf.d/teamportal.conf
```

Inhalt:
```ini
[program:teamportal]
directory=/var/www/teamportal
command=/var/www/teamportal/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
user=www-data
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/teamportal/err.log
stdout_logfile=/var/log/teamportal/out.log
```

```bash
# Log-Verzeichnis erstellen
sudo mkdir -p /var/log/teamportal
sudo chown www-data:www-data /var/log/teamportal

# Supervisor neu laden
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start teamportal
sudo supervisorctl status teamportal
```

### Schritt 7: Nginx konfigurieren
```bash
sudo nano /etc/nginx/sites-available/teamportal
```

Inhalt:
```nginx
server {
    listen 80;
    server_name ihre-domain.de www.ihre-domain.de;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # File upload limit
    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (für zukünftige Features)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /static {
        alias /var/www/teamportal/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /uploads {
        alias /var/www/teamportal/uploads;
        expires 7d;
    }
}
```

```bash
# Site aktivieren
sudo ln -s /etc/nginx/sites-available/teamportal /etc/nginx/sites-enabled/

# Nginx testen und neu starten
sudo nginx -t
sudo systemctl restart nginx
```

### Schritt 8: SSL mit Let's Encrypt
```bash
# Certbot installieren
sudo apt install -y certbot python3-certbot-nginx

# SSL-Zertifikat erstellen
sudo certbot --nginx -d ihre-domain.de -d www.ihre-domain.de

# Automatische Erneuerung testen
sudo certbot renew --dry-run
```

### Schritt 9: Firewall konfigurieren
```bash
# UFW installieren (falls nicht vorhanden)
sudo apt install -y ufw

# Firewall-Regeln setzen
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

### Schritt 11: Ersten Admin erstellen
```bash
# Zur Anwendung gehen
cd /var/www/teamportal

# Flask Shell öffnen
sudo -u www-data ./venv/bin/python
```

In der Python-Shell:
```python
from app import create_app, db
from app.models.user import User

app = create_app('production')
with app.app_context():
    # Admin-Benutzer erstellen
    admin = User(
        email='admin@example.com',
        first_name='Admin',
        last_name='User',
        is_active=True,
        is_admin=True
    )
    admin.set_password('SicheresPasswort123!')
    db.session.add(admin)
    db.session.commit()
    print("Admin erstellt!")
exit()
```

## Wartung

### Logs überprüfen
```bash
# Supervisor Logs
sudo tail -f /var/log/teamportal/out.log
sudo tail -f /var/log/teamportal/err.log

# Nginx Logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Anwendung neu starten
```bash
sudo supervisorctl restart teamportal
```

### Updates einspielen
```bash
cd /var/www/teamportal
sudo git pull
sudo ./venv/bin/pip install -r requirements.txt
sudo supervisorctl restart teamportal
```

### Backup erstellen
```bash
# Datenbank-Backup
sudo mysqldump -u teamportal -p teamportal > backup_$(date +%Y%m%d).sql

# Upload-Verzeichnis sichern
sudo tar -czf uploads_backup_$(date +%Y%m%d).tar.gz uploads/
```

## Troubleshooting

### Anwendung startet nicht
```bash
# Logs prüfen
sudo supervisorctl tail teamportal stderr

# Manuell starten zum Testen
cd /var/www/teamportal
sudo -u www-data ./venv/bin/python app.py
```

### Datenbankverbindung schlägt fehl
```bash
# MariaDB-Status prüfen
sudo systemctl status mariadb

# Verbindung testen
mysql -u teamportal -p teamportal
```

### Upload schlägt fehl
```bash
# Berechtigungen prüfen
ls -la /var/www/teamportal/uploads

# Berechtigungen korrigieren
sudo chown -R www-data:www-data /var/www/teamportal/uploads
sudo chmod -R 775 /var/www/teamportal/uploads
```

### Nginx zeigt 502 Bad Gateway
```bash
# Prüfen ob Gunicorn läuft
sudo supervisorctl status teamportal

# Neu starten
sudo supervisorctl restart teamportal
```

## Performance-Optimierung

### Gunicorn-Worker anpassen
```bash
# In /etc/supervisor/conf.d/teamportal.conf
# Faustregel: (2 x CPU-Kerne) + 1
# Für 4 CPU-Kerne: -w 9
command=/var/www/teamportal/venv/bin/gunicorn -w 9 -b 127.0.0.1:5000 app:app
```

### Nginx Caching
```bash
sudo nano /etc/nginx/sites-available/teamportal
```

Füge hinzu:
```nginx
# Cache für statische Dateien
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

## Sicherheits-Checkliste

- [ ] Starken SECRET_KEY gesetzt
- [ ] Datenbank-Passwort ist sicher
- [ ] SSL/HTTPS ist aktiviert
- [ ] Firewall ist konfiguriert
- [ ] Regelmäßige Backups sind eingerichtet
- [ ] Standard-Ports sind geschützt
- [ ] Nur notwendige Services laufen
- [ ] System-Updates sind aktuell

## Support

Bei Problemen:
1. Logs überprüfen
2. GitHub Issues durchsuchen
3. Neues Issue erstellen mit detaillierter Fehlerbeschreibung



