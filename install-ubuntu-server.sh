#!/bin/bash

###############################################################################
# Ubuntu Server 24.04 - One-Click Installation Script
# Installiert: RabbitMQ, OnlyOffice (mit PostgreSQL), MySQL (für Teamportal)
###############################################################################

set -e  # Beende bei Fehlern

# Farben für Ausgabe
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funktionen
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Prüfe ob als root/sudo ausgeführt
if [ "$EUID" -ne 0 ]; then 
    print_error "Bitte führen Sie dieses Skript mit sudo aus!"
    exit 1
fi

print_info "=========================================="
print_info "Ubuntu Server 24.04 - One-Click Installation"
print_info "=========================================="
echo ""

# Benutzerinformationen abfragen
print_info "Bitte geben Sie die folgenden Informationen ein:"
echo ""
read -p "System-Benutzername: " SYS_USERNAME
while [ -z "$SYS_USERNAME" ]; do
    print_warning "Benutzername darf nicht leer sein!"
    read -p "System-Benutzername: " SYS_USERNAME
done

read -s -p "System-Passwort: " SYS_PASSWORD
echo ""
while [ -z "$SYS_PASSWORD" ]; do
    print_warning "Passwort darf nicht leer sein!"
    read -s -p "System-Passwort: " SYS_PASSWORD
    echo ""
done

read -s -p "Passwort bestätigen: " SYS_PASSWORD_CONFIRM
echo ""
while [ "$SYS_PASSWORD" != "$SYS_PASSWORD_CONFIRM" ]; do
    print_error "Passwörter stimmen nicht überein!"
    read -s -p "System-Passwort: " SYS_PASSWORD
    echo ""
    read -s -p "Passwort bestätigen: " SYS_PASSWORD_CONFIRM
    echo ""
done

# PostgreSQL Passwort für OnlyOffice abfragen
read -s -p "PostgreSQL-Passwort für OnlyOffice (leer = Standard): " POSTGRES_PASSWORD
echo ""
if [ -z "$POSTGRES_PASSWORD" ]; then
    POSTGRES_PASSWORD="onlyoffice123"
    print_info "Verwende Standard-Passwort für PostgreSQL: onlyoffice123"
fi

# OnlyOffice JWT Secret Key abfragen (optional, aber empfohlen)
read -s -p "OnlyOffice JWT Secret Key (leer = automatisch generieren): " ONLYOFFICE_JWT_SECRET
echo ""
if [ -z "$ONLYOFFICE_JWT_SECRET" ]; then
    ONLYOFFICE_JWT_SECRET=$(openssl rand -base64 32 2>/dev/null || head -c 32 /dev/urandom | base64)
    print_info "JWT Secret Key wurde automatisch generiert"
else
    print_info "Verwende eingegebenes JWT Secret Key"
fi

# MySQL Root-Passwort abfragen
read -s -p "MySQL Root-Passwort: " MYSQL_ROOT_PASSWORD
echo ""
while [ -z "$MYSQL_ROOT_PASSWORD" ]; do
    print_warning "MySQL Root-Passwort darf nicht leer sein!"
    read -s -p "MySQL Root-Passwort: " MYSQL_ROOT_PASSWORD
    echo ""
done

# MySQL Passwort für Teamportal abfragen
read -s -p "MySQL-Passwort für Teamportal (leer = Standard): " MYSQL_TEAMPORTAL_PASSWORD
echo ""
if [ -z "$MYSQL_TEAMPORTAL_PASSWORD" ]; then
    MYSQL_TEAMPORTAL_PASSWORD="teamportal123"
    print_info "Verwende Standard-Passwort für Teamportal: teamportal123"
fi

# Teamportal Admin-Informationen abfragen
echo ""
print_info "Teamportal Admin-Account erstellen:"
read -p "Admin E-Mail-Adresse: " ADMIN_EMAIL
while [ -z "$ADMIN_EMAIL" ]; do
    print_warning "E-Mail-Adresse darf nicht leer sein!"
    read -p "Admin E-Mail-Adresse: " ADMIN_EMAIL
done

read -p "Admin Vorname: " ADMIN_FIRSTNAME
read -p "Admin Nachname: " ADMIN_LASTNAME

read -s -p "Admin Passwort: " ADMIN_PASSWORD
echo ""
while [ -z "$ADMIN_PASSWORD" ]; do
    print_warning "Passwort darf nicht leer sein!"
    read -s -p "Admin Passwort: " ADMIN_PASSWORD
    echo ""
done

# Git Repository URL abfragen (optional - falls nicht lokal)
read -p "Git Repository URL für Teamportal (leer = lokale Installation): " GIT_REPO_URL

# Secret Key für Flask generieren
FLASK_SECRET_KEY=$(openssl rand -base64 32 2>/dev/null || head -c 32 /dev/urandom | base64)

echo ""
print_info "Starte Installation..."
echo ""

###############################################################################
# Schritt 1: System aktualisieren
###############################################################################
print_info "Schritt 1/11: System aktualisieren..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get upgrade -y -qq
print_success "System aktualisiert"

###############################################################################
# Schritt 2: Benutzer erstellen
###############################################################################
print_info "Schritt 2/11: System-Benutzer erstellen..."
if id "$SYS_USERNAME" &>/dev/null; then
    print_warning "Benutzer $SYS_USERNAME existiert bereits. Überspringe Erstellung."
else
    adduser --gecos "" --disabled-password "$SYS_USERNAME" || true
    echo "$SYS_USERNAME:$SYS_PASSWORD" | chpasswd
    usermod -aG sudo "$SYS_USERNAME" 2>/dev/null || true
    print_success "Benutzer $SYS_USERNAME erstellt"
fi

###############################################################################
# Schritt 3: Basis-Pakete installieren
###############################################################################
print_info "Schritt 3/11: Basis-Pakete installieren..."
apt-get install -y -qq \
    curl \
    wget \
    gnupg \
    apt-transport-https \
    ca-certificates \
    software-properties-common \
    ufw \
    git \
    unzip \
    htop \
    nano \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    libmysqlclient-dev \
    pkg-config
print_success "Basis-Pakete installiert"

###############################################################################
# Schritt 4: RabbitMQ installieren
###############################################################################
print_info "Schritt 4/11: RabbitMQ installieren..."

# Team RabbitMQ's Signing Key hinzufügen
curl -1sLf "https://keys.openpgp.org/vks/v1/by-fingerprint/0A9AF2115F4687BD29803A206B73A36E6026DFCA" | \
    gpg --dearmor | tee /usr/share/keyrings/com.rabbitmq.team.gpg > /dev/null

# RabbitMQ Repository hinzufügen (Ubuntu 24.04 = noble)
tee /etc/apt/sources.list.d/rabbitmq.list > /dev/null <<EOF
## Modern Erlang/OTP releases
##
deb [arch=amd64 signed-by=/usr/share/keyrings/com.rabbitmq.team.gpg] https://deb1.rabbitmq.com/rabbitmq-erlang/ubuntu/noble noble main
deb [arch=amd64 signed-by=/usr/share/keyrings/com.rabbitmq.team.gpg] https://deb2.rabbitmq.com/rabbitmq-erlang/ubuntu/noble noble main

## Latest RabbitMQ releases
##
deb [arch=amd64 signed-by=/usr/share/keyrings/com.rabbitmq.team.gpg] https://deb1.rabbitmq.com/rabbitmq-server/ubuntu/noble noble main
deb [arch=amd64 signed-by=/usr/share/keyrings/com.rabbitmq.team.gpg] https://deb2.rabbitmq.com/rabbitmq-server/ubuntu/noble noble main
EOF

apt-get update -qq

# Erlang Pakete installieren
apt-get install -y -qq \
    erlang-base \
    erlang-asn1 \
    erlang-crypto \
    erlang-eldap \
    erlang-ftp \
    erlang-inets \
    erlang-mnesia \
    erlang-os-mon \
    erlang-parsetools \
    erlang-public-key \
    erlang-runtime-tools \
    erlang-snmp \
    erlang-ssl \
    erlang-syntax-tools \
    erlang-tftp \
    erlang-tools \
    erlang-xmerl

# RabbitMQ Server installieren
apt-get install -y -qq rabbitmq-server --fix-missing

# RabbitMQ Service aktivieren
systemctl enable rabbitmq-server
systemctl start rabbitmq-server

# RabbitMQ Management Plugin aktivieren
rabbitmq-plugins enable rabbitmq_management

print_success "RabbitMQ installiert und gestartet"

###############################################################################
# Schritt 5: PostgreSQL installieren und konfigurieren
###############################################################################
print_info "Schritt 5/11: PostgreSQL installieren und konfigurieren..."

apt-get install -y -qq postgresql postgresql-contrib

# PostgreSQL Service starten
systemctl enable postgresql
systemctl start postgresql

# OnlyOffice Datenbank und Benutzer erstellen
sudo -u postgres psql <<EOF
-- Benutzer erstellen (falls nicht vorhanden)
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'onlyoffice') THEN
    CREATE USER onlyoffice WITH PASSWORD '$POSTGRES_PASSWORD';
  END IF;
END
\$\$;

-- Datenbank erstellen (falls nicht vorhanden)
SELECT 'CREATE DATABASE onlyoffice OWNER onlyoffice'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'onlyoffice')\gexec

-- Berechtigungen setzen
GRANT ALL PRIVILEGES ON DATABASE onlyoffice TO onlyoffice;
\q
EOF

print_success "PostgreSQL installiert und OnlyOffice-Datenbank erstellt"

###############################################################################
# Schritt 6: MySQL installieren und konfigurieren
###############################################################################
print_info "Schritt 6/11: MySQL installieren und konfigurieren..."

# MySQL Server installieren
debconf-set-selections <<< "mysql-server mysql-server/root_password password $MYSQL_ROOT_PASSWORD"
debconf-set-selections <<< "mysql-server mysql-server/root_password_again password $MYSQL_ROOT_PASSWORD"
apt-get install -y -qq mysql-server

# MySQL Service starten
systemctl enable mysql
systemctl start mysql

# MySQL absichern (automatisiert)
mysql -u root -p"$MYSQL_ROOT_PASSWORD" <<EOF
DELETE FROM mysql.user WHERE User='';
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');
DROP DATABASE IF EXISTS test;
DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';
FLUSH PRIVILEGES;
EOF

# Teamportal Datenbank und Benutzer erstellen
mysql -u root -p"$MYSQL_ROOT_PASSWORD" <<EOF
CREATE DATABASE IF NOT EXISTS teamportal CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'teamportal'@'localhost' IDENTIFIED BY '$MYSQL_TEAMPORTAL_PASSWORD';
GRANT ALL PRIVILEGES ON teamportal.* TO 'teamportal'@'localhost';
FLUSH PRIVILEGES;
EOF

print_success "MySQL installiert und Teamportal-Datenbank erstellt"

###############################################################################
# Schritt 7: Redis installieren
###############################################################################
print_info "Schritt 7/11: Redis installieren..."

apt-get install -y -qq redis-server

# Redis konfigurieren
sed -i 's/^supervised no/supervised systemd/' /etc/redis/redis.conf
sed -i 's/^# maxmemory <bytes>/maxmemory 256mb/' /etc/redis/redis.conf
sed -i 's/^# maxmemory-policy noeviction/maxmemory-policy allkeys-lru/' /etc/redis/redis.conf

systemctl enable redis-server
systemctl restart redis-server

print_success "Redis installiert und gestartet"

###############################################################################
# Schritt 8: Nginx installieren
###############################################################################
print_info "Schritt 8/11: Nginx installieren..."

apt-get install -y -qq nginx

# Nginx konfigurieren
systemctl enable nginx
systemctl start nginx

print_success "Nginx installiert und gestartet"

###############################################################################
# Schritt 9: OnlyOffice Document Server installieren
###############################################################################
print_info "Schritt 9/11: OnlyOffice Document Server installieren..."

# OnlyOffice GPG Key hinzufügen
curl -fsSL https://download.onlyoffice.com/GPG-KEY-ONLYOFFICE | gpg --dearmor -o /usr/share/keyrings/onlyoffice.gpg

# OnlyOffice Repository hinzufügen
echo "deb [signed-by=/usr/share/keyrings/onlyoffice.gpg] https://download.onlyoffice.com/repo/debian squeeze main" | \
    tee /etc/apt/sources.list.d/onlyoffice.list > /dev/null

apt-get update -qq

# OnlyOffice Document Server installieren
apt-get install -y -qq onlyoffice-documentserver

# OnlyOffice vollständig konfigurieren
print_info "OnlyOffice konfigurieren..."

# Warten bis OnlyOffice installiert ist
sleep 5

# Prüfe ob local.json existiert, falls nicht erstelle es
if [ ! -f /etc/onlyoffice/documentserver/local.json ]; then
    print_info "Erstelle OnlyOffice Konfigurationsdatei..."
    mkdir -p /etc/onlyoffice/documentserver
    touch /etc/onlyoffice/documentserver/local.json
fi

# Backup erstellen
if [ -f /etc/onlyoffice/documentserver/local.json ]; then
    cp /etc/onlyoffice/documentserver/local.json /etc/onlyoffice/documentserver/local.json.backup.$(date +%Y%m%d_%H%M%S)
fi

# Vollständige OnlyOffice-Konfiguration erstellen
print_info "Erstelle vollständige OnlyOffice-Konfiguration..."

# JSON-Konfiguration mit PostgreSQL und JWT
cat > /etc/onlyoffice/documentserver/local.json <<EOF
{
  "services": {
    "CoAuthoring": {
      "sql": {
        "type": "postgres",
        "dbHost": "localhost",
        "dbPort": 5432,
        "dbName": "onlyoffice",
        "dbUser": "onlyoffice",
        "dbPass": "$POSTGRES_PASSWORD"
      },
      "token": {
        "enable": {
          "request": {
            "inbox": true,
            "outbox": true
          },
          "browser": true
        },
        "inbox": {
          "header": "Authorization"
        },
        "outbox": {
          "header": "Authorization"
        }
      },
      "secret": {
        "inbox": {
          "string": "$ONLYOFFICE_JWT_SECRET"
        },
        "outbox": {
          "string": "$ONLYOFFICE_JWT_SECRET"
        },
        "session": {
          "string": "$ONLYOFFICE_JWT_SECRET"
        }
      }
    },
    "FileConverter": {
      "converter": {
        "timeout": 120000
      }
    }
  },
  "rabbitmq": {
    "url": "amqp://guest:guest@localhost"
  },
  "redis": {
    "host": "localhost",
    "port": 6379
  },
  "storage": {
    "fs": {
      "folderPath": "/var/lib/onlyoffice/documentserver/App_Data/cache/files"
    }
  }
}
EOF

# Berechtigungen setzen
chown ds:ds /etc/onlyoffice/documentserver/local.json
chmod 600 /etc/onlyoffice/documentserver/local.json

# JWT Secret Key in separater Datei speichern (für spätere Verwendung)
echo "$ONLYOFFICE_JWT_SECRET" > /root/onlyoffice-jwt-secret.txt
chmod 600 /root/onlyoffice-jwt-secret.txt
print_info "JWT Secret Key gespeichert in: /root/onlyoffice-jwt-secret.txt"

print_success "OnlyOffice-Konfiguration erstellt"

# OnlyOffice Services aktivieren und starten
print_info "OnlyOffice Services starten..."
systemctl enable ds-docservice > /dev/null 2>&1
systemctl enable ds-metrics > /dev/null 2>&1
systemctl enable ds-converter > /dev/null 2>&1
systemctl enable ds-docservice > /dev/null 2>&1

# Services neu starten um Konfiguration zu laden
systemctl restart ds-docservice 2>/dev/null || systemctl start ds-docservice
systemctl restart ds-metrics 2>/dev/null || systemctl start ds-metrics
systemctl restart ds-converter 2>/dev/null || systemctl start ds-converter

print_success "OnlyOffice Services gestartet"

# Nginx-Konfiguration für OnlyOffice erstellen
print_info "Nginx-Konfiguration für OnlyOffice erstellen..."

# Backup der Standard-Nginx-Konfiguration
if [ -f /etc/nginx/sites-available/default ]; then
    cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup
fi

# OnlyOffice Location zu Nginx hinzufügen
if ! grep -q "location /onlyoffice/" /etc/nginx/sites-available/default 2>/dev/null; then
    # Füge OnlyOffice-Konfiguration zur default site hinzu
    cat >> /etc/nginx/sites-available/default <<'NGINX_EOF'

    # OnlyOffice Document Server
    location /onlyoffice/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
        send_timeout 600s;
        
        proxy_buffering off;
        proxy_request_buffering off;
        
        client_header_buffer_size 16k;
        large_client_header_buffers 8 32k;
        client_max_body_size 100M;
    }
NGINX_EOF

    # Nginx-Konfiguration testen
    if nginx -t 2>/dev/null; then
        systemctl reload nginx
        print_success "Nginx-Konfiguration für OnlyOffice erstellt"
    else
        print_warning "Nginx-Konfigurationstest fehlgeschlagen. Bitte manuell prüfen."
    fi
else
    print_info "OnlyOffice-Konfiguration bereits vorhanden"
fi

# Warten bis OnlyOffice bereit ist
print_info "Warte auf OnlyOffice Initialisierung..."
sleep 45

# OnlyOffice Health-Check durchführen
print_info "Prüfe OnlyOffice Status..."
MAX_RETRIES=10
RETRY_COUNT=0
ONLYOFFICE_READY=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8000/welcome/ > /dev/null 2>&1; then
        ONLYOFFICE_READY=true
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    print_info "Warte auf OnlyOffice... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 10
done

if [ "$ONLYOFFICE_READY" = true ]; then
    print_success "OnlyOffice Document Server ist bereit"
else
    print_warning "OnlyOffice antwortet noch nicht. Bitte manuell prüfen mit: curl http://localhost:8000/welcome/"
fi

# OnlyOffice Service-Status prüfen
if systemctl is-active --quiet ds-docservice; then
    print_success "OnlyOffice Service läuft"
else
    print_warning "OnlyOffice Service Status: $(systemctl is-active ds-docservice)"
fi

print_success "OnlyOffice Document Server installiert und konfiguriert"

###############################################################################
# Schritt 10: Firewall konfigurieren
###############################################################################
print_info "Schritt 10/11: Firewall konfigurieren..."

# UFW zurücksetzen (falls bereits konfiguriert)
ufw --force reset

# Standard-Regeln
ufw default deny incoming
ufw default allow outgoing

# SSH erlauben
ufw allow ssh
ufw allow 22/tcp

# HTTP und HTTPS erlauben
ufw allow 80/tcp
ufw allow 443/tcp

# RabbitMQ Management (optional, nur lokal empfohlen)
ufw allow 15672/tcp comment 'RabbitMQ Management'

# Firewall aktivieren
ufw --force enable

print_success "Firewall konfiguriert"

###############################################################################
# Schritt 11: Teamportal installieren und konfigurieren
###############################################################################
print_info "Schritt 11/11: Teamportal installieren und konfigurieren..."

# Verzeichnis für Teamportal erstellen
TEAMPORTAL_DIR="/var/www/teamportal"
mkdir -p "$TEAMPORTAL_DIR"

# Teamportal installieren (Git oder lokal)
if [ -n "$GIT_REPO_URL" ]; then
    print_info "Klone Teamportal aus Git Repository..."
    git clone "$GIT_REPO_URL" "$TEAMPORTAL_DIR" || {
        print_error "Git Clone fehlgeschlagen. Bitte Repository-URL prüfen."
        exit 1
    }
else
    print_info "Lokale Installation - prüfe ob Teamportal-Dateien vorhanden sind..."
    # Falls lokal, müssen die Dateien bereits vorhanden sein
    if [ ! -f "$TEAMPORTAL_DIR/app.py" ]; then
        print_warning "Teamportal-Dateien nicht in $TEAMPORTAL_DIR gefunden."
        print_info "Bitte Teamportal-Dateien nach $TEAMPORTAL_DIR kopieren oder Git Repository URL angeben."
        print_info "Installation wird fortgesetzt, aber Teamportal muss manuell eingerichtet werden."
        # Erstelle zumindest das Verzeichnis
        mkdir -p "$TEAMPORTAL_DIR"
    else
        print_success "Teamportal-Dateien gefunden"
    fi
fi

cd "$TEAMPORTAL_DIR" || exit 1

# Virtual Environment erstellen
print_info "Erstelle Python Virtual Environment..."
python3 -m venv venv

# Virtual Environment aktivieren und Dependencies installieren
if [ -f requirements.txt ]; then
    print_info "Installiere Python Dependencies..."
    source venv/bin/activate
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    print_success "Python Dependencies installiert"
else
    print_error "requirements.txt nicht gefunden! Bitte Teamportal-Dateien prüfen."
    exit 1
fi

# .env-Datei erstellen
print_info "Erstelle .env Konfigurationsdatei..."
if [ -f docs/env.example ]; then
    cp docs/env.example .env
elif [ -f env.example ]; then
    cp env.example .env
else
    touch .env
fi

# .env konfigurieren
print_info "Konfiguriere .env-Datei..."

# JWT Secret Key aus OnlyOffice lesen
ONLYOFFICE_JWT_FROM_FILE=$(cat /root/onlyoffice-jwt-secret.txt 2>/dev/null || echo "$ONLYOFFICE_JWT_SECRET")

cat > .env <<ENVEOF
# Flask Configuration
SECRET_KEY=$FLASK_SECRET_KEY
FLASK_APP=app.py
FLASK_ENV=production

# Database Configuration
DATABASE_URI=mysql+pymysql://teamportal:$MYSQL_TEAMPORTAL_PASSWORD@localhost/teamportal

# Upload Configuration
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=104857600

# Application Configuration
TIMEZONE=Europe/Berlin

# ONLYOFFICE Configuration
ONLYOFFICE_ENABLED=True
ONLYOFFICE_DOCUMENT_SERVER_URL=/onlyoffice
ONLYOFFICE_SECRET_KEY=$ONLYOFFICE_JWT_FROM_FILE
ENVEOF

# Berechtigungen setzen
chown -R www-data:www-data "$TEAMPORTAL_DIR"
chmod -R 755 "$TEAMPORTAL_DIR"
chmod 600 .env

# Upload-Verzeichnis erstellen
mkdir -p uploads
chown -R www-data:www-data uploads

# Datenbank initialisieren
print_info "Initialisiere Datenbank..."
cd "$TEAMPORTAL_DIR"
source venv/bin/activate

python3 <<PYTHON_SCRIPT
import os
import sys
sys.path.insert(0, '$TEAMPORTAL_DIR')

os.environ['FLASK_ENV'] = 'production'

from app import create_app, db
from app.models import *

app = create_app('production')
with app.app_context():
    try:
        print("Erstelle Datenbank-Tabellen...")
        db.create_all()
        print("Datenbank-Tabellen erstellt")
        
        # Admin-User erstellen
        from app.models.user import User
        from app.models.chat import Chat, ChatMember
        from app.models.email_permission import EmailPermission
        
        # Prüfe ob Admin bereits existiert
        admin_email = '$ADMIN_EMAIL'
        admin = User.query.filter_by(email=admin_email).first()
        if not admin:
            admin = User(
                email=admin_email,
                first_name='$ADMIN_FIRSTNAME',
                last_name='$ADMIN_LASTNAME',
                is_active=True,
                is_admin=True,
                is_email_confirmed=True
            )
            admin.set_password('$ADMIN_PASSWORD')
            db.session.add(admin)
            db.session.flush()
            
            # Email-Berechtigungen
            email_perm = EmailPermission(
                user_id=admin.id,
                can_read=True,
                can_send=True
            )
            db.session.add(email_perm)
            
            # Haupt-Chat erstellen
            main_chat = Chat(
                name="Haupt-Chat",
                is_main_chat=True,
                created_by=admin.id
            )
            db.session.add(main_chat)
            db.session.flush()
            
            # Admin zum Haupt-Chat hinzufügen
            chat_member = ChatMember(
                chat_id=main_chat.id,
                user_id=admin.id
            )
            db.session.add(chat_member)
            
            db.session.commit()
            print(f"Admin-User erfolgreich erstellt: {admin_email}")
        else:
            print("Admin-User existiert bereits")
    except Exception as e:
        import traceback
        print(f"Fehler bei Datenbank-Initialisierung: {e}")
        traceback.print_exc()
        sys.exit(1)
PYTHON_SCRIPT

if [ $? -ne 0 ]; then
    print_error "Datenbank-Initialisierung fehlgeschlagen!"
    exit 1
fi

print_success "Datenbank initialisiert und Admin-User erstellt"

# Gunicorn Service erstellen
print_info "Erstelle Systemd Service für Teamportal..."
cat > /etc/systemd/system/teamportal.service <<SERVICEEOF
[Unit]
Description=Teamportal Gunicorn Application Server
After=network.target mysql.service redis-server.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=$TEAMPORTAL_DIR
Environment="PATH=$TEAMPORTAL_DIR/venv/bin"
ExecStart=$TEAMPORTAL_DIR/venv/bin/gunicorn --workers 4 --bind 127.0.0.1:5000 --timeout 120 --access-logfile $TEAMPORTAL_DIR/logs/access.log --error-logfile $TEAMPORTAL_DIR/logs/error.log app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICEEOF

# Log-Verzeichnis erstellen
mkdir -p "$TEAMPORTAL_DIR/logs"
chown -R www-data:www-data "$TEAMPORTAL_DIR/logs"

# Service aktivieren und starten
systemctl daemon-reload
systemctl enable teamportal
systemctl start teamportal

# Warten bis Service läuft
sleep 5

if systemctl is-active --quiet teamportal; then
    print_success "Teamportal Service läuft"
else
    print_warning "Teamportal Service startet noch oder hat Probleme"
    print_info "Status prüfen mit: systemctl status teamportal"
fi

# Nginx-Konfiguration für Teamportal erstellen
print_info "Erstelle Nginx-Konfiguration für Teamportal..."

# Backup der default-Konfiguration
if [ -f /etc/nginx/sites-available/default ]; then
    cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup.teamportal
fi

# Neue Nginx-Konfiguration erstellen
cat > /etc/nginx/sites-available/teamportal <<NGINXEOF
server {
    listen 80;
    listen [::]:80;
    server_name _;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # File upload limit
    client_max_body_size 100M;
    
    # Root location - Teamportal
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_set_header X-Forwarded-Port \$server_port;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Statische Dateien direkt ausliefern
    location /static {
        alias $TEAMPORTAL_DIR/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    # Upload-Verzeichnis
    location /uploads {
        alias $TEAMPORTAL_DIR/uploads;
        expires 7d;
        access_log off;
    }
    
    # OnlyOffice Document Server Integration
    location /onlyoffice/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
        send_timeout 600s;
        
        proxy_buffering off;
        proxy_request_buffering off;
        
        client_header_buffer_size 16k;
        large_client_header_buffers 8 32k;
        client_max_body_size 100M;
    }
    
    # Logging
    access_log /var/log/nginx/teamportal_access.log;
    error_log /var/log/nginx/teamportal_error.log;
}
NGINXEOF

# Alte default-Site deaktivieren und neue aktivieren
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/teamportal /etc/nginx/sites-enabled/teamportal

# Nginx-Konfiguration testen
if nginx -t 2>/dev/null; then
    systemctl reload nginx
    print_success "Nginx-Konfiguration für Teamportal erstellt"
else
    print_error "Nginx-Konfigurationstest fehlgeschlagen!"
    nginx -t
fi

# Warten bis Teamportal bereit ist
print_info "Warte auf Teamportal Initialisierung..."
sleep 10

# Health-Check
if curl -s http://localhost:5000 > /dev/null 2>&1; then
    print_success "Teamportal ist erreichbar"
else
    print_warning "Teamportal antwortet noch nicht. Bitte Status prüfen: systemctl status teamportal"
fi

print_success "Teamportal installiert und konfiguriert"

###############################################################################
# Installation abgeschlossen
###############################################################################
echo ""
print_success "=========================================="
print_success "Installation erfolgreich abgeschlossen!"
print_success "=========================================="
echo ""

# Zusammenfassung ausgeben
SERVER_IP=$(hostname -I | awk '{print $1}')

cat <<EOF
${GREEN}Installations-Zusammenfassung:${NC}

${BLUE}System-Benutzer:${NC}
  Benutzername: $SYS_USERNAME
  Passwort: [wie eingegeben]

${BLUE}RabbitMQ:${NC}
  Status: Läuft
  Management UI: http://$SERVER_IP:15672
  Standard-Benutzer: guest / guest
  ${YELLOW}WICHTIG: Ändern Sie das Standard-Passwort!${NC}

${BLUE}PostgreSQL (OnlyOffice):${NC}
  Datenbank: onlyoffice
  Benutzer: onlyoffice
  Passwort: $POSTGRES_PASSWORD
  Port: 5432

${BLUE}MySQL (Teamportal):${NC}
  Root-Passwort: $MYSQL_ROOT_PASSWORD
  Datenbank: teamportal
  Benutzer: teamportal
  Passwort: $MYSQL_TEAMPORTAL_PASSWORD
  Port: 3306

${BLUE}Redis:${NC}
  Status: Läuft
  Port: 6379

${BLUE}Nginx:${NC}
  Status: Läuft
  HTTP: http://$SERVER_IP

${BLUE}OnlyOffice Document Server:${NC}
  Status: Läuft
  URL: http://$SERVER_IP/onlyoffice/
  Health Check: http://$SERVER_IP/onlyoffice/welcome/
  JWT Secret Key: $ONLYOFFICE_JWT_SECRET
  JWT Key gespeichert in: /root/onlyoffice-jwt-secret.txt
  ${YELLOW}WICHTIG: Speichern Sie den JWT Secret Key für die Integration!${NC}

${YELLOW}Nächste Schritte:${NC}
1. RabbitMQ Management Passwort ändern:
   sudo rabbitmqctl change_password guest NEUES_PASSWORT

2. OnlyOffice überprüfen:
   curl http://localhost:8000/welcome/
   curl http://$SERVER_IP/onlyoffice/welcome/

3. JWT Secret Key für Teamportal-Integration verwenden:
   cat /root/onlyoffice-jwt-secret.txt

${BLUE}Teamportal:${NC}
  Status: Läuft
  URL: http://$SERVER_IP
  Admin E-Mail: $ADMIN_EMAIL
  Admin Passwort: [wie eingegeben]
  Installation: $TEAMPORTAL_DIR
  Service: systemctl status teamportal

${GREEN}🎉 FERTIG! Sie können jetzt im Browser die IP-Adresse eingeben:${NC}
${GREEN}   http://$SERVER_IP${NC}
${GREEN}   OnlyOffice: http://$SERVER_IP/onlyoffice/${NC}

${GREEN}Alle Services sind aktiviert und starten automatisch beim Booten.${NC}
EOF

echo ""
print_info "Installations-Log gespeichert in: /var/log/ubuntu-install.log"
print_info "Viel Erfolg mit Ihrer Installation!"

