

## Vollständiges Setup-Beispiel

So erstellst du einen Benutzer und eine zugehörige Datenbank:

```bash
# 1. Benutzer erstellen
sudo -i -u postgres psql -c "CREATE USER Prismateams WITH PASSWORD 'prismateams';"

# 2. Datenbank erstellen und dem Benutzer zuweisen
sudo -i -u postgres psql -c "CREATE DATABASE teamportal OWNER Prismateams;"
```

---

