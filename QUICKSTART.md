# Quick Start - Ubuntu Server Installation

## Schnellstart-Anleitung

### 1. Skript auf Ubuntu Server 24.04 hochladen

```bash
# Auf Ihrem lokalen Computer (Windows/Mac/Linux)
# Übertragen Sie das Skript auf den Server mit scp:

scp install-ubuntu-server.sh benutzer@ihr-server-ip:/home/benutzer/
```

### 2. Auf dem Server anmelden

```bash
ssh benutzer@ihr-server-ip
```

### 3. Skript ausführbar machen und starten

```bash
# Skript ausführbar machen
chmod +x install-ubuntu-server.sh

# Skript mit sudo ausführen
sudo ./install-ubuntu-server.sh
```

### 4. Eingaben während der Installation

Das Skript fragt Sie nach:

1. **System-Benutzername** (z.B. `admin` oder `teamportal`)
2. **System-Passwort** (für den neuen Benutzer)
3. **PostgreSQL-Passwort für OnlyOffice** (Enter für Standard: `onlyoffice123`)
4. **MySQL Root-Passwort** (wichtig - merken Sie sich dieses!)
5. **MySQL-Passwort für Teamportal** (Enter für Standard: `teamportal123`)

### 5. Installation abwarten

Die Installation dauert ca. 10-15 Minuten, abhängig von Ihrer Internetverbindung.

### 6. Nach der Installation

#### RabbitMQ Passwort ändern (WICHTIG!)

```bash
sudo rabbitmqctl change_password guest IHR_SICHERES_PASSWORT
```

#### Services überprüfen

```bash
# Alle Services prüfen
sudo systemctl status rabbitmq-server
sudo systemctl status postgresql
sudo systemctl status mysql
sudo systemctl status redis-server
sudo systemctl status nginx
sudo systemctl status ds-docservice
```

#### OnlyOffice testen

```bash
# Im Browser öffnen:
http://IHRE-SERVER-IP/onlyoffice/welcome/

# Oder per curl:
curl http://localhost:8000/welcome/
```

## Wichtige Informationen nach der Installation

### Zugangsdaten

Alle Zugangsdaten werden am Ende der Installation angezeigt. Notieren Sie sich:

- ✅ MySQL Root-Passwort
- ✅ PostgreSQL OnlyOffice-Passwort
- ✅ MySQL Teamportal-Passwort
- ✅ System-Benutzer Passwort

### Standard-Ports

- **22** - SSH
- **80** - HTTP (Nginx)
- **443** - HTTPS (Nginx)
- **3306** - MySQL
- **5432** - PostgreSQL
- **6379** - Redis
- **8000** - OnlyOffice (intern)
- **15672** - RabbitMQ Management

### Standard-Zugangsdaten (zu ändern!)

- **RabbitMQ Management**: `guest` / `guest` ⚠️ **SOFORT ÄNDERN!**
- **MySQL Root**: Wie bei Installation angegeben
- **PostgreSQL OnlyOffice**: Wie bei Installation angegeben

## Nächste Schritte

1. ✅ RabbitMQ Passwort ändern
2. ✅ Firewall-Regeln überprüfen (`sudo ufw status`)
3. ✅ Teamportal installieren und konfigurieren
4. ✅ SSL-Zertifikat einrichten (Let's Encrypt)
5. ✅ Regelmäßige Backups einrichten

## Hilfe bei Problemen

Siehe `INSTALLATION_README.md` für detaillierte Fehlerbehebung.

