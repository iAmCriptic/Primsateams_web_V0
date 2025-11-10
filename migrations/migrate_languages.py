#!/usr/bin/env python3
"""
Datenbankmigration zur Einführung der Mehrsprachigkeit.

- Fügt `language`-Spalte zur `users`-Tabelle hinzu
- Legt Standard-Systemeinstellungen für Sprachen an
"""

import json
import os
import sys
from contextlib import suppress

from sqlalchemy import inspect, text

# Projektverzeichnis zum Python-Pfad hinzufügen
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Beim Ausführen der Migration sollen Hintergrundjobs nicht gestartet werden
os.environ.setdefault("RUNNING_LANGUAGE_MIGRATION", "1")
os.environ.setdefault("PRISMATEAMS_SKIP_BACKGROUND_JOBS", "1")

from app import create_app, db  # noqa: E402  pylint: disable=wrong-import-position
from app.models.settings import SystemSettings  # noqa: E402  pylint: disable=wrong-import-position

SUPPORTED_LANGUAGES = ["de", "en", "pt", "es", "ru"]


def ensure_user_language_column() -> bool:
    """Stellt sicher, dass die Spalte `language` in `users` existiert."""
    inspector = inspect(db.engine)

    if "users" not in inspector.get_table_names():
        print("⚠ Tabelle 'users' existiert nicht – überspringe Sprachspalte.")
        return True

    columns = {col["name"] for col in inspector.get_columns("users")}
    if "language" in columns:
        print("✓ Spalte 'language' in 'users' existiert bereits.")
        return True

    dialect = db.engine.dialect.name
    default_value = "'de'"

    if dialect == "sqlite":
        column_type = "TEXT"
    else:
        column_type = "VARCHAR(10)"

    add_column_sql = f"ALTER TABLE users ADD COLUMN language {column_type} DEFAULT {default_value} NOT NULL"

    try:
        with db.engine.connect() as conn:
            conn.execute(text(add_column_sql))
            conn.commit()
        print("✓ Spalte 'language' zu 'users' hinzugefügt.")
    except Exception as exc:  # pylint: disable=broad-except
        print(f"❌ Konnte Spalte 'language' nicht hinzufügen: {exc}")
        return False

    try:
        db.session.execute(
            text("UPDATE users SET language = 'de' WHERE language IS NULL OR language = ''")
        )
        db.session.commit()
        print("✓ Standardwert 'de' für bestehende Benutzer gesetzt.")
    except Exception as exc:  # pylint: disable=broad-except
        db.session.rollback()
        print(f"⚠ Konnte Standardwert für Benutzer nicht setzen: {exc}")
        return False

    return True


def ensure_system_language_settings() -> bool:
    """Legt die relevanten SystemSettings an bzw. aktualisiert sie."""
    settings_defaults = {
        "default_language": (
            "de",
            "Standardsprache der Benutzeroberfläche für neue Benutzer.",
        ),
        "email_language": (
            "de",
            "Sprache für automatisch versendete System-E-Mails.",
        ),
        "available_languages": (
            json.dumps(SUPPORTED_LANGUAGES),
            "Aktivierte Sprachen im Portal (JSON-Liste).",
        ),
    }

    try:
        for key, (value, description) in settings_defaults.items():
            setting = SystemSettings.query.filter_by(key=key).first()
            if setting is None:
                db.session.add(SystemSettings(key=key, value=value, description=description))
                print(f"✓ SystemSetting '{key}' angelegt.")
            else:
                if not setting.value:
                    setting.value = value
                    print(f"✓ SystemSetting '{key}' mit Standardwert befüllt.")
                if description and not setting.description:
                    setting.description = description
        db.session.commit()
        return True
    except Exception as exc:  # pylint: disable=broad-except
        db.session.rollback()
        print(f"❌ Konnte SystemSettings nicht aktualisieren: {exc}")
        return False


def run_migration() -> bool:
    """Führt die Gesamtmigration aus."""
    app = create_app(os.getenv("FLASK_ENV", "development"))

    with app.app_context():
        success = ensure_user_language_column()
        if not success:
            return False

        success = ensure_system_language_settings() and success
        return success


if __name__ == "__main__":
    with suppress(KeyboardInterrupt):
        ok = run_migration()
        sys.exit(0 if ok else 1)

