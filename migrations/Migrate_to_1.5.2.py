#!/usr/bin/env python3
"""
Datenbank-Migration: Version 1.5.2
Briefkasten-Felder zum folders-Modell hinzufügen

Diese Migration fügt die neuen Felder für das Briefkasten-Feature hinzu:
- is_dropbox (Boolean)
- dropbox_token (String, unique)
- dropbox_password_hash (String, nullable)

WICHTIG: Die Felder sind bereits im Modell (app/models/file.py) definiert.
Diese Migration ist nur für bestehende Datenbanken erforderlich.
Bei neuen Installationen werden die Felder automatisch durch db.create_all() erstellt.
"""

import os
import sys

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text, inspect

def migrate():
    """Führt die Migration aus."""
    print("=" * 60)
    print("Migration zu Version 1.5.2")
    print("Briefkasten-Felder hinzufügen")
    print("=" * 60)
    
    # Erstelle die Flask-App
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    
    with app.app_context():
        try:
            # Prüfe ob die Tabelle existiert
            inspector = inspect(db.engine)
            if 'folders' not in inspector.get_table_names():
                print("⚠ Warnung: Tabelle 'folders' existiert nicht.")
                print("  Die Tabelle wird beim nächsten Start automatisch erstellt.")
                return
            
            # Prüfe ob die Felder bereits existieren
            columns = {col['name']: col for col in inspector.get_columns('folders')}
            
            fields_to_add = []
            if 'is_dropbox' not in columns:
                fields_to_add.append('is_dropbox')
            if 'dropbox_token' not in columns:
                fields_to_add.append('dropbox_token')
            if 'dropbox_password_hash' not in columns:
                fields_to_add.append('dropbox_password_hash')
            
            if not fields_to_add:
                print("✓ Alle Felder existieren bereits. Migration nicht erforderlich.")
                return
            
            print(f"\nFehlende Felder gefunden: {', '.join(fields_to_add)}")
            print("Starte Migration...")
            
            # Bestimme die Datenbank-Engine
            db_url = db.engine.url
            is_sqlite = 'sqlite' in str(db_url)
            is_mysql = 'mysql' in str(db_url) or 'mariadb' in str(db_url)
            is_postgres = 'postgresql' in str(db_url)
            
            print(f"Datenbank-Typ: {db_url.drivername}")
            
            with db.engine.connect() as conn:
                if is_sqlite:
                    print("\nFühre SQLite-Migration aus...")
                    # SQLite unterstützt nur ein ALTER TABLE ADD COLUMN pro Statement
                    if 'is_dropbox' in fields_to_add:
                        conn.execute(text("ALTER TABLE folders ADD COLUMN is_dropbox BOOLEAN DEFAULT 0 NOT NULL"))
                        print("  ✓ is_dropbox hinzugefügt")
                    if 'dropbox_token' in fields_to_add:
                        conn.execute(text("ALTER TABLE folders ADD COLUMN dropbox_token VARCHAR(255)"))
                        print("  ✓ dropbox_token hinzugefügt")
                    if 'dropbox_password_hash' in fields_to_add:
                        conn.execute(text("ALTER TABLE folders ADD COLUMN dropbox_password_hash VARCHAR(255)"))
                        print("  ✓ dropbox_password_hash hinzugefügt")
                    
                    # Unique Index für SQLite
                    try:
                        conn.execute(text("""
                            CREATE UNIQUE INDEX IF NOT EXISTS idx_folders_dropbox_token 
                            ON folders(dropbox_token) 
                            WHERE dropbox_token IS NOT NULL
                        """))
                        print("  ✓ Unique Index erstellt")
                    except Exception as e:
                        print(f"  ⚠ Index-Erstellung übersprungen: {e}")
                    
                    conn.commit()
                
                elif is_mysql or is_postgres:
                    print(f"\nFühre {db_url.drivername}-Migration aus...")
                    # MySQL/MariaDB/PostgreSQL unterstützen mehrere Spalten in einem ALTER TABLE
                    alter_statements = []
                    
                    if 'is_dropbox' in fields_to_add:
                        if is_mysql:
                            alter_statements.append("ADD COLUMN is_dropbox BOOLEAN DEFAULT FALSE NOT NULL")
                        else:  # PostgreSQL
                            alter_statements.append("ADD COLUMN is_dropbox BOOLEAN DEFAULT FALSE NOT NULL")
                    
                    if 'dropbox_token' in fields_to_add:
                        alter_statements.append("ADD COLUMN dropbox_token VARCHAR(255) NULL")
                    
                    if 'dropbox_password_hash' in fields_to_add:
                        alter_statements.append("ADD COLUMN dropbox_password_hash VARCHAR(255) NULL")
                    
                    if alter_statements:
                        alter_sql = f"ALTER TABLE folders {', '.join(alter_statements)}"
                        conn.execute(text(alter_sql))
                        print(f"  ✓ {len(alter_statements)} Felder hinzugefügt")
                    
                    # Unique Index
                    try:
                        conn.execute(text("CREATE UNIQUE INDEX idx_folders_dropbox_token ON folders(dropbox_token)"))
                        print("  ✓ Unique Index erstellt")
                    except Exception as e:
                        print(f"  ⚠ Index-Erstellung übersprungen: {e}")
                    
                    conn.commit()
                
                else:
                    # Generische Migration für andere Datenbanken
                    print(f"\nFühre generische Migration für {db_url.drivername} aus...")
                    try:
                        if 'is_dropbox' in fields_to_add:
                            conn.execute(text("ALTER TABLE folders ADD COLUMN is_dropbox BOOLEAN DEFAULT FALSE NOT NULL"))
                            print("  ✓ is_dropbox hinzugefügt")
                        if 'dropbox_token' in fields_to_add:
                            conn.execute(text("ALTER TABLE folders ADD COLUMN dropbox_token VARCHAR(255)"))
                            print("  ✓ dropbox_token hinzugefügt")
                        if 'dropbox_password_hash' in fields_to_add:
                            conn.execute(text("ALTER TABLE folders ADD COLUMN dropbox_password_hash VARCHAR(255)"))
                            print("  ✓ dropbox_password_hash hinzugefügt")
                        conn.commit()
                    except Exception as e:
                        print(f"  ❌ Fehler bei generischer Migration: {e}")
                        print("  Bitte führen Sie die Migration manuell für Ihre Datenbank aus.")
                        return
            
            # Verifiziere die Migration
            print("\nVerifiziere Migration...")
            inspector = inspect(db.engine)
            columns_after = {col['name']: col for col in inspector.get_columns('folders')}
            
            required_fields = ['is_dropbox', 'dropbox_token', 'dropbox_password_hash']
            missing_fields = [f for f in required_fields if f not in columns_after]
            
            if missing_fields:
                print(f"  ❌ Warnung: Folgende Felder fehlen noch: {missing_fields}")
                print("  Bitte überprüfen Sie die Datenbank-Logs.")
            else:
                print("  ✓ Migration erfolgreich abgeschlossen!")
                print("\nHinzugefügte Felder:")
                print("  - is_dropbox (BOOLEAN, DEFAULT FALSE)")
                print("  - dropbox_token (VARCHAR(255), UNIQUE, NULLABLE)")
                print("  - dropbox_password_hash (VARCHAR(255), NULLABLE)")
        
        except Exception as e:
            print(f"\n❌ Fehler bei der Migration: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == '__main__':
    migrate()

