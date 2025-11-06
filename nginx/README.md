# Nginx Konfiguration für Team Portal

Diese Dateien enthalten die Nginx-Konfiguration für die Team Portal Flask-Anwendung.

## Dateien

- `teamportal.conf` - Hauptkonfiguration für die Flask-App (HTTP/HTTPS)
- `onlyoffice.conf` - Konfiguration für ONLYOFFICE Document Server Integration

## Installation

### 1. Nginx-Konfiguration installieren

```bash
# Kopieren Sie die Konfiguration nach Nginx
sudo cp nginx/teamportal.conf /etc/nginx/sites-available/teamportal

# Aktivieren Sie die Site
sudo ln -s /etc/nginx/sites-available/teamportal /etc/nginx/sites-enabled/

# Testen Sie die Konfiguration
sudo nginx -t

# Starten Sie Nginx neu
sudo systemctl restart nginx
```

### 2. Domain anpassen

Bearbeiten Sie `/etc/nginx/sites-available/teamportal` und ersetzen Sie:
- `server_name _;` mit Ihrer tatsächlichen Domain, z.B. `server_name ihre-domain.de www.ihre-domain.de;`

### 3. Pfade anpassen (falls nötig)

Standardmäßig verwendet die Konfiguration:
- `/var/www/teamportal` - Projektverzeichnis
- `127.0.0.1:5000` - Flask-App (läuft mit Gunicorn)

Wenn Ihre Installation anders ist, passen Sie die Pfade entsprechend an.

### 4. SSL/HTTPS einrichten (empfohlen)

```bash
# Certbot installieren
sudo apt install certbot python3-certbot-nginx -y

# SSL-Zertifikat erstellen (ersetzt automatisch Ihre Domain)
sudo certbot --nginx -d ihre-domain.de -d www.ihre-domain.de

# Automatische Erneuerung testen
sudo certbot renew --dry-run
```

Certbot wird automatisch die HTTPS-Konfiguration in Ihrer Nginx-Datei hinzufügen und HTTP auf HTTPS umleiten.

## Funktionsweise

1. **Nginx läuft auf Port 80 (HTTP) und Port 443 (HTTPS)**
   - Diese sind die Standard-Ports für Web-Traffic
   - Benutzer können direkt auf `http://ihre-domain.de` oder `https://ihre-domain.de` zugreifen

2. **Flask-App läuft weiterhin auf Port 5000 (localhost)**
   - Die Flask-App ist nur lokal erreichbar (127.0.0.1)
   - Nginx leitet alle Anfragen an die Flask-App weiter

3. **Reverse Proxy Pattern**
   - Nginx empfängt Anfragen von Clients
   - Nginx leitet sie an die Flask-App weiter
   - Flask-App verarbeitet die Anfrage und sendet die Antwort zurück
   - Nginx sendet die Antwort an den Client

## Vorteile

- ✅ **Standard-Ports**: Keine Port-Angabe in der URL nötig
- ✅ **SSL/HTTPS**: Einfache Integration von SSL-Zertifikaten
- ✅ **Performance**: Statische Dateien werden direkt von Nginx ausgeliefert
- ✅ **Sicherheit**: Flask-App ist nicht direkt aus dem Internet erreichbar
- ✅ **Load Balancing**: Kann später leicht erweitert werden

## Troubleshooting

### Nginx startet nicht
```bash
# Prüfen Sie die Konfiguration
sudo nginx -t

# Prüfen Sie die Logs
sudo tail -f /var/log/nginx/error.log
```

### Flask-App nicht erreichbar
```bash
# Prüfen Sie ob Gunicorn läuft
sudo systemctl status teamportal

# Prüfen Sie ob Port 5000 erreichbar ist
curl http://127.0.0.1:5000
```

### Statische Dateien werden nicht angezeigt
```bash
# Prüfen Sie die Berechtigungen
sudo chown -R www-data:www-data /var/www/teamportal/app/static
sudo chmod -R 755 /var/www/teamportal/app/static
```


