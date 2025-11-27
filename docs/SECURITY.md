# Sicherheitsrichtlinien

## Unterstützte Versionen

**Wichtig**: Nur der aktuelle `main` Branch wird aktiv unterstützt und erhält Sicherheitsupdates.

- ✅ **Unterstützt**: `main` Branch (aktuelle Version)
- ❌ **Nicht unterstützt**: Ältere Branches, Tags oder Versionen

Für Produktionsumgebungen wird dringend empfohlen, immer die neueste Version vom `main` Branch zu verwenden, um sicherzustellen, dass alle bekannten Sicherheitslücken behoben sind.

## Meldung von Sicherheitslücken

Wir nehmen die Sicherheit von Prismateams sehr ernst. Wenn Sie eine Sicherheitslücke entdecken, bitten wir Sie, diese verantwortungsvoll zu melden.

### Wie melden Sie eine Sicherheitslücke?

Sie können Sicherheitslücken auf folgende Weise melden:

1. **GitHub Issues**: Erstellen Sie ein neues Issue mit dem Label `security` oder `vulnerability`
2. **GitHub Discussions**: Erwähnen Sie die Sicherheitslücke in den Diskussionen
Andere wege sind zurzeit aufgrund dessen das dies ein freizeit schulprojket ist nicht möglich

### Was sollten Sie in Ihrer Meldung enthalten?

Um eine schnelle Bearbeitung zu gewährleisten, bitten wir Sie, folgende Informationen bereitzustellen:

- **Beschreibung**: Eine klare Beschreibung der Sicherheitslücke
- **Schweregrad**: Ihre Einschätzung des Schweregrads (niedrig, mittel, hoch, kritisch)
- **Schritte zur Reproduktion**: Detaillierte Schritte, um die Sicherheitslücke zu reproduzieren
- **Betroffene Version**: Welche Version/Branch ist betroffen?
- **Mögliche Auswirkungen**: Welche Auswirkungen könnte diese Sicherheitslücke haben?

## Sicherheitsmaßnahmen

Prismateams implementiert verschiedene Sicherheitsmaßnahmen:

### Authentifizierung & Autorisierung
- **Passwort-Hashing**: Argon2 für sichere Passwort-Speicherung
- **Rollenbasierte Zugriffskontrolle**: User/Admin-Rollen mit granularer Berechtigung
- **Session-Sicherheit**: Sichere Cookie-Einstellungen für Produktion

### Datenverschlüsselung
- **Verschlüsselung**: Fernet (symmetrische Verschlüsselung) für Zugangsdaten
- **HTTPS**: Verwendung von SSL/TLS-Zertifikaten wird dringend empfohlen

### Schutz vor gängigen Angriffen
- **CSRF-Schutz**: Flask-WTF für Cross-Site-Request-Forgery-Schutz
- **XSS-Schutz**: Jinja2 Auto-Escaping verhindert Cross-Site-Scripting
- **SQL-Injection-Schutz**: SQLAlchemy ORM verhindert SQL-Injection
- **Rate Limiting**: Flask-Limiter für API-Endpunkte

## Best Practices für Administratoren

Wenn Sie Prismateams in einer Produktionsumgebung betreiben:

1. **Aktualisierungen**: Halten Sie die Anwendung immer auf dem neuesten Stand vom `main` Branch
2. **Starker SECRET_KEY**: Generieren Sie einen sicheren Schlüssel mit `openssl rand -hex 32`
3. **HTTPS aktivieren**: Verwenden Sie SSL/TLS-Zertifikate (z.B. Let's Encrypt)
4. **Sichere Passwörter**: Verwenden Sie starke, eindeutige Passwörter für Datenbank und E-Mail-Konten
5. **Firewall**: Beschränken Sie den Zugriff auf notwendige Ports
6. **Regelmäßige Backups**: Erstellen Sie regelmäßig Backups der Datenbank und Uploads
7. **System-Updates**: Halten Sie das Betriebssystem und Dependencies aktuell
8. **OnlyOffice JWT**: Für Produktion sollte JWT-Authentifizierung aktiviert sein
9. **Dateiberechtigungen**: Stellen Sie sicher, dass Upload-Verzeichnisse korrekte Berechtigungen haben

## Bekannte Sicherheitslücken

- nicht bekannt bisher

## Sicherheits-Updates

Sicherheitsupdates werden im `main` Branch veröffentlicht. Wir empfehlen:

- Regelmäßig den `main` Branch zu aktualisieren
- Die [Release Notes](../../releases) zu überprüfen
- Sicherheitsrelevante Updates so schnell wie möglich einzuspielen

## Weitere Informationen

Für weitere Informationen zur Sicherheit von Prismateams siehe auch:
- [README.md](README.md) - Allgemeine Projektinformationen
- [INSTALLATION.md](INSTALLATION.md) - Installationsanleitung mit Sicherheitshinweisen

---

**Vielen Dank, dass Sie zur Sicherheit von Prismateams beitragen!**