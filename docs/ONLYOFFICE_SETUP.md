# ONLYOFFICE Document Server Installation und Konfiguration

Diese Anleitung beschreibt die Installation und Konfiguration von **ONLYOFFICE Docs Community Edition** auf Ubuntu für die Integration in das Team Portal.

## ONLYOFFICE Docs Community Edition

Wir verwenden die **ONLYOFFICE Docs Community Edition** (kostenlos):

- ✅ **Kostenlos** und Open Source
- ✅ Bis zu **20 gleichzeitige Verbindungen**
- ✅ Alle Editor-Features (Word, Excel, PowerPoint, PDF, Markdown)
- ✅ Kollaborative Bearbeitung
- ✅ Minimaler Ressourcenbedarf

**Hinweis:** Die Community Edition ist für die meisten Anwendungsfälle völlig ausreichend. Die Integration funktioniert identisch mit der Enterprise-Version.

## Voraussetzungen

- Ubuntu Server (20.04 oder höher empfohlen)
- Nginx bereits installiert und konfiguriert
- Root- oder sudo-Zugriff
- Mindestens 2 GB RAM (4 GB empfohlen)
- Mindestens 10 GB freier Speicherplatz

## Installation

### 1. ONLYOFFICE Repository hinzufügen

```bash
# GPG-Schlüssel hinzufügen
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys CB2DE8E5

# Repository hinzufügen
sudo echo "deb http://download.onlyoffice.com/repo/debian squeeze main" | sudo tee /etc/apt/sources.list.d/onlyoffice.list
```

### 2. ONLYOFFICE Docs Community Edition installieren

```bash
# Paketlisten aktualisieren
sudo apt-get update

# ONLYOFFICE Docs Community Edition installieren
sudo apt-get install onlyoffice-documentserver
```

**Hinweis:** Das Paket `onlyoffice-documentserver` installiert standardmäßig die Community Edition, die kostenlos ist und bis zu 20 gleichzeitige Verbindungen unterstützt. Für mehr Verbindungen benötigen Sie eine Enterprise-Lizenz.

### 3. Service starten und aktivieren

```bash
# Service starten
sudo systemctl start ds-docservice

# Service aktivieren (startet automatisch beim Booten)
sudo systemctl enable ds-docservice

# Status prüfen
sudo systemctl status ds-docservice
```

### 4. Health-Check durchführen

```bash
# Prüfen ob ONLYOFFICE auf Port 8000 läuft
curl http://localhost:8000/welcome/

# Oder im Browser öffnen:
# http://localhost:8000/welcome/
```

Wenn Sie eine Erfolgsseite sehen, ist ONLYOFFICE Docs Community Edition korrekt installiert.

## Nginx Reverse Proxy Konfiguration

### 1. Nginx-Konfiguration erstellen

Erstellen Sie eine neue Datei `/etc/nginx/sites-available/onlyoffice` oder fügen Sie die folgende Konfiguration zu Ihrer bestehenden Nginx-Konfiguration hinzu:

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
    
    # Timeouts für große Dateien
    proxy_connect_timeout 600s;
    proxy_send_timeout 600s;
    proxy_read_timeout 600s;
    send_timeout 600s;
    
    # Buffer-Einstellungen
    proxy_buffering off;
    proxy_request_buffering off;
    
    # Größere Header-Buffer (behebt "Request Header Or Cookie Too Large")
    client_header_buffer_size 16k;
    large_client_header_buffers 8 32k;
    
    # Größere Dateien erlauben
    client_max_body_size 100M;
}
```

### 2. Konfiguration aktivieren

```bash
# Wenn Sie eine separate Datei erstellt haben:
sudo ln -s /etc/nginx/sites-available/onlyoffice /etc/nginx/sites-enabled/

# Nginx-Konfiguration testen
sudo nginx -t

# Nginx neu laden
sudo systemctl reload nginx
```

### 3. Testen

```bash
# Testen ob ONLYOFFICE über Nginx erreichbar ist
curl http://localhost/onlyoffice/web-apps/apps/api/documents/api.js

# Oder im Browser:
# http://ihre-domain.de/onlyoffice/web-apps/apps/api/documents/api.js
```


## Markdown-Plugin aktivieren

Das Markdown-Plugin ist standardmäßig in ONLYOFFICE Docs Community Edition enthalten und aktiviert. Falls Sie es manuell aktivieren müssen:

1. Öffnen Sie die ONLYOFFICE-Konfiguration:
   ```bash
   sudo nano /etc/onlyoffice/documentserver/default.json
   ```

2. Stellen Sie sicher, dass das Markdown-Plugin aktiviert ist (standardmäßig aktiviert).

3. Service neu starten:
   ```bash
   sudo systemctl restart ds-docservice
   ```

## Anwendungskonfiguration

### 1. .env-Datei aktualisieren

Fügen Sie die folgenden Zeilen zu Ihrer `.env`-Datei hinzu:

```env
# ONLYOFFICE Configuration
ONLYOFFICE_ENABLED=True
ONLYOFFICE_DOCUMENT_SERVER_URL=/onlyoffice
ONLYOFFICE_SECRET_KEY=ihr-geheimer-schluessel-hier
```

**Wichtig:**
- `ONLYOFFICE_ENABLED=True` aktiviert ONLYOFFICE
- `ONLYOFFICE_DOCUMENT_SERVER_URL` sollte `/onlyoffice` sein (wenn über Nginx)
- `ONLYOFFICE_SECRET_KEY` ist optional, aber für Produktion empfohlen

### 2. Secret Key generieren (optional)

Für zusätzliche Sicherheit können Sie einen Secret Key generieren:

```bash
# Zufälligen Schlüssel generieren
openssl rand -base64 32
```

Kopieren Sie den generierten Schlüssel in die `.env`-Datei.

### 3. Anwendung neu starten

```bash
# Flask-Anwendung neu starten (abhängig von Ihrer Setup-Methode)
sudo systemctl restart teamportal
# oder
sudo supervisorctl restart teamportal
```

## Unterstützte Dateitypen

ONLYOFFICE unterstützt die folgenden Dateitypen:

- **Word**: `.docx`, `.doc`, `.odt`, `.rtf`, `.txt`
- **Excel**: `.xlsx`, `.xls`, `.ods`, `.csv`
- **PowerPoint**: `.pptx`, `.ppt`, `.odp`
- **PDF**: `.pdf` (nur Ansicht, keine Bearbeitung)
- **Markdown**: `.md`, `.markdown` (mit aktiviertem Plugin)

## Fehlerbehebung

### Problem: ONLYOFFICE lädt nicht

1. **Service prüfen:**
   ```bash
   sudo systemctl status ds-docservice
   ```

2. **Port prüfen:**
   ```bash
   sudo netstat -tlnp | grep 8000
   ```

3. **Logs prüfen:**
   ```bash
   sudo journalctl -u ds-docservice -f
   ```

### Problem: Nginx gibt 502 Bad Gateway

1. **ONLYOFFICE läuft auf Port 8000:**
   ```bash
   curl http://localhost:8000/welcome/
   ```

2. **Nginx-Konfiguration prüfen:**
   ```bash
   sudo nginx -t
   ```

3. **Firewall prüfen:**
   ```bash
   sudo ufw status
   ```

### Problem: Editor lädt nicht im Browser

1. **Browser-Konsole prüfen** (F12) auf JavaScript-Fehler
2. **ONLYOFFICE API-URL prüfen:**
   ```bash
   curl http://ihre-domain.de/onlyoffice/web-apps/apps/api/documents/api.js
   ```
3. **CORS-Einstellungen prüfen** (falls Probleme auftreten)

## Deaktivieren von ONLYOFFICE

Falls Sie ONLYOFFICE vorübergehend deaktivieren möchten, ohne es zu deinstallieren:

1. In `.env` setzen:
   ```env
   ONLYOFFICE_ENABLED=False
   ```

2. Anwendung neu starten

Die Anwendung läuft dann normal weiter, ohne ONLYOFFICE-Features anzuzeigen.

## Weitere Informationen

- [ONLYOFFICE Docs Community Edition Download](https://www.onlyoffice.com/download-community#docs-community)
- [ONLYOFFICE Dokumentation](https://api.onlyoffice.com/)
- [ONLYOFFICE Help Center](https://helpcenter.onlyoffice.com/)
- [ONLYOFFICE Docs Community Installation Guide](https://helpcenter.onlyoffice.com/installation/docs-community-install-ubuntu.aspx)

