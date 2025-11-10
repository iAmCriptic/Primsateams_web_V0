#!/usr/bin/env python3
"""
Datenbank-Migration für Mehrsprachigkeit.

- Fügt die Spalte `language` zur Tabelle `users` hinzu.
- Ergänzt SystemSettings um `default_language`, `email_language`, `available_languages`.
- Setzt für bestehende Benutzer eine Standardsprache.
"""

import os
import sys

from sqlalchemy import inspect, text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db  # pylint: disable=wrong-import-position


def add_language_column():
    inspector = inspect(db.engine)

    if 'users' not in inspector.get_table_names():
        print("⚠ Tabelle 'users' existiert nicht – wird bei Neuinstallationen automatisch erstellt.")
        return True

    columns = {col['name'] for col in inspector.get_columns('users')}
    if 'language' in columns:
        print("✓ Spalte 'language' existiert bereits in 'users'.")
        return True

    db_url = db.engine.url
    is_sqlite = 'sqlite' in str(db_url)
    is_mysql = 'mysql' in str(db_url) or 'mariadb' in str(db_url)
    is_postgres = 'postgresql' in str(db_url)

    print("➕ Füge Spalte 'language' zu 'users' hinzu...")

    try:
        alter_sql = ""
        if is_sqlite:
            alter_sql = "ALTER TABLE users ADD COLUMN language VARCHAR(10) NOT NULL DEFAULT 'de'"
        elif is_mysql:
            alter_sql = "ALTER TABLE users ADD COLUMN language VARCHAR(10) NOT NULL DEFAULT 'de'"
        elif is_postgres:
            alter_sql = "ALTER TABLE users ADD COLUMN language VARCHAR(10) NOT NULL DEFAULT 'de'"
        else:
            alter_sql = "ALTER TABLE users ADD COLUMN language VARCHAR(10) NOT NULL DEFAULT 'de'"

        with db.engine.begin() as connection:
            connection.execute(text(alter_sql))

        print("  ✓ Spalte 'language' hinzugefügt.")
        return True
    except Exception as exc:  # pylint: disable=broad-except
        print(f"  ❌ Fehler beim Hinzufügen der Spalte: {exc}")
        return False


def ensure_user_language_defaults():
    inspector = inspect(db.engine)
    if 'users' not in inspector.get_table_names():
        return True

    columns = {col['name'] for col in inspector.get_columns('users')}
    if 'language' not in columns:
        print("⚠ Spalte 'language' fehlt weiterhin – bitte Migration erneut prüfen.")
        return False

    print("⚙ Setze Standardsprache für bestehende Benutzer...")
    try:
        with db.engine.begin() as connection:
            connection.execute(
                text("""
                    UPDATE users
                    SET language = :default_lang
                    WHERE language IS NULL OR TRIM(language) = ''
                """),
                {'default_lang': 'de'}
            )
        print("  ✓ Standardsprache gesetzt.")
        return True
    except Exception as exc:  # pylint: disable=broad-except
        print(f"  ❌ Konnte Standardsprache nicht setzen: {exc}")
        return False


def ensure_system_settings():
    from app.models.settings import SystemSettings  # pylint: disable=import-outside-toplevel

    created_any = False

    defaults = [
        ('default_language', 'de', 'Standardsprache für die Benutzeroberfläche'),
        ('email_language', 'de', 'Standardsprache für System-E-Mails'),
        ('available_languages', '["de","en","pt","es","ru"]', 'Liste der aktivierten Sprachen'),
    ]

    for key, value, description in defaults:
        setting = SystemSettings.query.filter_by(key=key).first()
        if not setting:
            db.session.add(SystemSettings(key=key, value=value, description=description))
            created_any = True
            print(f"  ✓ SystemSetting '{key}' hinzugefügt.")
        else:
            print(f"  ✓ SystemSetting '{key}' existiert bereits.")

    if created_any:
        db.session.commit()
        print("  ✓ SystemSettings gespeichert.")
    else:
        print("  ✓ Keine neuen SystemSettings erforderlich.")

    return True


def migrate():
    print("=" * 60)
    print("Migration: Mehrsprachigkeit")
    print("=" * 60)

    app = create_app(os.getenv('FLASK_ENV', 'development'))

    with app.app_context():
        if not add_language_column():
            return False

        if not ensure_user_language_defaults():
            return False

        if not ensure_system_settings():
            return False

        print("\nMigration abgeschlossen.")
        return True


if __name__ == '__main__':
    success = migrate()
    sys.exit(0 if success else 1)

