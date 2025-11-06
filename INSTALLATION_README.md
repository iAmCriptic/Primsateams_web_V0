# Ubuntu Server 24.04 - One-Click Installation

Dieses Skript installiert automatisch alle erforderlichen Komponenten für das Team Portal auf Ubuntu Server 24.04.

## Installierte Komponenten

- ✅ **RabbitMQ** - Message Queue System
- ✅ **OnlyOffice Document Server** - Dokumentenbearbeitung (mit PostgreSQL)
- ✅ **PostgreSQL** - Datenbank für OnlyOffice
- ✅ **MySQL** - Datenbank für Teamportal
- ✅ **Redis** - Caching und Session Storage
- ✅ **Nginx** - Web Server
- ✅ **System-Benutzer** - Neuer Benutzer mit sudo-Rechten

## Voraussetzungen

- Ubuntu Server 24.04 (Noble)
- Root- oder sudo-Zugriff
- Mindestens 4 GB RAM empfohlen
- Mindestens 20 GB freier Speicherplatz
- Internetverbindung

## Installation

### 1. Skript herunterladen

```bash
# Falls noch nicht vorhanden, Repository klonen oder Datei erstellen
```

### 2. Skript ausführbar machen

```bash
chmod +x install-ubuntu-server.sh
```

### 3. Skript ausführen

```bash
sudo ./install-ubuntu-server.sh
```

Das Skript fragt Sie nach folgenden Informationen:

1. **System-Benutzername** - Name für den neuen System-Benutzer
2. **System-Passwort** - Passwort für den neuen Benutzer
3. **PostgreSQL-Passwort für OnlyOffice** - Optional (Standard: onlyoffice123)
4. **OnlyOffice JWT Secret Key** - Optional (wird automatisch generiert wenn leer gelassen)
5. **MySQL Root-Passwort** - Passwort für MySQL Root-Benutzer
6. **MySQL-Passwort für Teamportal** - Optional (Standard: teamportal123)

## Was wird installiert?

### RabbitMQ
- Installiert aus den offiziellen Team RabbitMQ Repositories
- Erlang/OTP wird automatisch mitinstalliert
- Management Plugin wird aktiviert
- Erreichbar unter: `http://SERVER_IP:15672`
- Standard-Login: `guest` / `guest` ⚠️ **Bitte ändern!**

### OnlyOffice Document Server
- Community Edition (kostenlos, bis zu 20 gleichzeitige Verbindungen)
- **Vollständig konfiguriert** mit:
  - PostgreSQL als Datenbank (automatisch eingerichtet)
  - JWT Secret Key (automatisch generiert oder manuell eingegeben)
  - RabbitMQ Integration (automatisch konfiguriert)
  - Redis Integration (automatisch konfiguriert)
  - Nginx Reverse Proxy (automatisch konfiguriert)
- Läuft auf Port 8000 (intern)
- Erreichbar über Nginx unter: `http://SERVER_IP/onlyoffice/`
- JWT Secret Key gespeichert in: `/root/onlyoffice-jwt-secret.txt`

### PostgreSQL
- Datenbank: `onlyoffice`
- Benutzer: `onlyoffice`
- Passwort: Wie bei Installation angegeben

### MySQL
- Root-Passwort: Wie bei Installation angegeben
- Datenbank: `teamportal`
- Benutzer: `teamportal`
- Passwort: Wie bei Installation angegeben

### Redis
- Konfiguriert mit 256MB Memory Limit
- Eviction Policy: allkeys-lru

### Nginx
- Web Server für Reverse Proxy
- Standard-Konfiguration aktiviert

## Nach der Installation

### 1. RabbitMQ Passwort ändern

```bash
sudo rabbitmqctl change_password guest NEUES_SICHERES_PASSWORT
```

### 2. OnlyOffice überprüfen

```bash
# Health Check (lokal)
curl http://localhost:8000/welcome/

# Health Check (über Nginx)
curl http://SERVER_IP/onlyoffice/welcome/

# Oder im Browser
http://SERVER_IP/onlyoffice/welcome/

# JWT Secret Key anzeigen (für Teamportal-Integration)
cat /root/onlyoffice-jwt-secret.txt
```

### 3. OnlyOffice Konfiguration prüfen

```bash
# Konfigurationsdatei anzeigen
sudo cat /etc/onlyoffice/documentserver/local.json

# Service-Status prüfen
sudo systemctl status ds-docservice
sudo systemctl status ds-metrics
sudo systemctl status ds-converter
```

### 4. OnlyOffice ist bereits vollständig konfiguriert!

Das Skript konfiguriert OnlyOffice automatisch vollständig:

✅ **PostgreSQL-Datenbank** - Automatisch erstellt und konfiguriert  
✅ **JWT Secret Key** - Automatisch generiert und konfiguriert  
✅ **RabbitMQ Integration** - Automatisch konfiguriert  
✅ **Redis Integration** - Automatisch konfiguriert  
✅ **Nginx Reverse Proxy** - Automatisch konfiguriert  
✅ **Services** - Alle Services werden automatisch gestartet und aktiviert  

**Hinweis:** Falls Sie die Nginx-Konfiguration manuell anpassen möchten:

```bash
sudo nano /etc/nginx/sites-available/default
```

Fügen Sie folgende Konfiguration hinzu:

```nginx
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
```

Dann Nginx neu laden:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### 4. Firewall überprüfen

```bash
sudo ufw status
```

Standardmäßig sind folgende Ports geöffnet:
- 22 (SSH)
- 80 (HTTP)
- 443 (HTTPS)
- 15672 (RabbitMQ Management)

## Service-Verwaltung

### Services starten/stoppen/status

```bash
# RabbitMQ
sudo systemctl start rabbitmq-server
sudo systemctl stop rabbitmq-server
sudo systemctl status rabbitmq-server

# PostgreSQL
sudo systemctl start postgresql
sudo systemctl stop postgresql
sudo systemctl status postgresql

# MySQL
sudo systemctl start mysql
sudo systemctl stop mysql
sudo systemctl status mysql

# Redis
sudo systemctl start redis-server
sudo systemctl stop redis-server
sudo systemctl status redis-server

# Nginx
sudo systemctl start nginx
sudo systemctl stop nginx
sudo systemctl status nginx

# OnlyOffice
sudo systemctl start ds-docservice
sudo systemctl stop ds-docservice
sudo systemctl status ds-docservice
```

## Logs anzeigen

```bash
# RabbitMQ Logs
sudo journalctl -u rabbitmq-server -f

# OnlyOffice Logs
sudo journalctl -u ds-docservice -f

# Nginx Logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# PostgreSQL Logs
sudo tail -f /var/log/postgresql/postgresql-*.log

# MySQL Logs
sudo tail -f /var/log/mysql/error.log
```

## Fehlerbehebung

### RabbitMQ startet nicht

```bash
# Logs prüfen
sudo journalctl -u rabbitmq-server -n 50

# Erlang-Version prüfen
erl -version

# RabbitMQ Status prüfen
sudo rabbitmqctl status
```

### OnlyOffice läuft nicht

```bash
# Service-Status prüfen
sudo systemctl status ds-docservice

# Port prüfen
sudo netstat -tlnp | grep 8000

# Logs prüfen
sudo journalctl -u ds-docservice -f
```

### PostgreSQL Verbindungsfehler

```bash
# PostgreSQL Status prüfen
sudo systemctl status postgresql

# Verbindung testen
sudo -u postgres psql -c "SELECT version();"

# OnlyOffice Datenbank prüfen
sudo -u postgres psql -c "\l" | grep onlyoffice
```

### MySQL Verbindungsfehler

```bash
# MySQL Status prüfen
sudo systemctl status mysql

# Verbindung testen
mysql -u root -p -e "SHOW DATABASES;"

# Teamportal Datenbank prüfen
mysql -u root -p -e "SHOW DATABASES;" | grep teamportal
```

## Sicherheitshinweise

⚠️ **WICHTIG:**

1. **RabbitMQ Standard-Passwort ändern** - Das Standard-Passwort `guest`/`guest` sollte sofort geändert werden
2. **MySQL Root-Passwort sicher aufbewahren** - Notieren Sie sich das Root-Passwort an einem sicheren Ort
3. **Firewall konfigurieren** - Überprüfen Sie die UFW-Regeln und passen Sie sie an Ihre Bedürfnisse an
4. **SSH absichern** - Konfigurieren Sie SSH-Keys und deaktivieren Sie Passwort-Login wenn möglich
5. **Regelmäßige Updates** - Führen Sie regelmäßig `sudo apt update && sudo apt upgrade` aus

## Unterstützung

Bei Problemen oder Fragen:
- Prüfen Sie die Logs (siehe oben)
- Überprüfen Sie die Service-Status
- Konsultieren Sie die offizielle Dokumentation:
  - [RabbitMQ Dokumentation](https://www.rabbitmq.com/docs)
  - [OnlyOffice Dokumentation](https://helpcenter.onlyoffice.com/)
  - [PostgreSQL Dokumentation](https://www.postgresql.org/docs/)
  - [MySQL Dokumentation](https://dev.mysql.com/doc/)

## Lizenz

Dieses Installationsskript ist Teil des Team Portal Projekts.

