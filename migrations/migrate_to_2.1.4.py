#!/usr/bin/env python3
"""
Datenbank-Migration: Version 2.1.4
Dashboard-Konfiguration zum User-Modell hinzufügen

Diese Migration fügt das neue Feld für die Dashboard-Personalisierung hinzu:
Users:
- dashboard_config (TEXT, nullable) - JSON-String für Dashboard-Konfiguration

WICHTIG: Das Feld ist bereits im Modell (app/models/user.py) definiert.
Diese Migration ist nur für bestehende Datenbanken erforderlich.
Bei neuen Installationen wird das Feld automatisch durch db.create_all() erstellt.
"""

import os
import sys

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text, inspect

def migrate_table(table_name, fields_config):
    """Führt die Migration für eine Tabelle aus."""
    inspector = inspect(db.engine)
    
    if table_name not in inspector.get_table_names():
        print(f"⚠ Warnung: Tabelle '{table_name}' existiert nicht.")
        print("  Die Tabelle wird beim nächsten Start automatisch erstellt.")
        return True
    
    # Prüfe ob die Felder bereits existieren
    columns = {col['name']: col for col in inspector.get_columns(table_name)}
    
    fields_to_add = []
    for field_name, _ in fields_config.items():
        if field_name not in columns:
            fields_to_add.append(field_name)
    
    if not fields_to_add:
        print(f"✓ Alle Felder in '{table_name}' existieren bereits. Migration nicht erforderlich.")
        return True
    
    print(f"\nFehlende Felder in '{table_name}' gefunden: {', '.join(fields_to_add)}")
    print(f"Starte Migration für '{table_name}'...")
    
    # Bestimme die Datenbank-Engine
    db_url = db.engine.url
    is_sqlite = 'sqlite' in str(db_url)
    is_mysql = 'mysql' in str(db_url) or 'mariadb' in str(db_url)
    is_postgres = 'postgresql' in str(db_url)
    
    with db.engine.connect() as conn:
        if is_sqlite:
            print(f"\nFühre SQLite-Migration für '{table_name}' aus...")
            # SQLite unterstützt nur ein ALTER TABLE ADD COLUMN pro Statement
            for field_name in fields_to_add:
                field_type, field_default, field_nullable = fields_config[field_name]
                
                # Baue SQL-Statement
                sql = f"ALTER TABLE {table_name} ADD COLUMN {field_name} {field_type}"
                
                if field_default is not None:
                    sql += f" DEFAULT {field_default}"
                
                if not field_nullable:
                    sql += " NOT NULL"
                
                try:
                    conn.execute(text(sql))
                    print(f"  ✓ {field_name} hinzugefügt")
                except Exception as e:
                    print(f"  ⚠ Fehler beim Hinzufügen von {field_name}: {e}")
            
            conn.commit()
        
        elif is_mysql or is_postgres:
            print(f"\nFühre {db_url.drivername}-Migration für '{table_name}' aus...")
            # MySQL/MariaDB/PostgreSQL unterstützen mehrere Spalten in einem ALTER TABLE
            alter_statements = []
            
            for field_name in fields_to_add:
                field_type, field_default, field_nullable = fields_config[field_name]
                
                if is_mysql:
                    # MySQL verwendet TEXT als TEXT
                    if field_type == 'TEXT':
                        alter_sql = f"ADD COLUMN {field_name} TEXT"
                    else:
                        alter_sql = f"ADD COLUMN {field_name} {field_type}"
                else:  # PostgreSQL
                    alter_sql = f"ADD COLUMN {field_name} {field_type}"
                
                if field_default is not None:
                    alter_sql += f" DEFAULT {field_default}"
                
                if not field_nullable:
                    alter_sql += " NOT NULL"
                
                alter_statements.append(alter_sql)
            
            if alter_statements:
                alter_sql = f"ALTER TABLE {table_name} {', '.join(alter_statements)}"
                try:
                    conn.execute(text(alter_sql))
                    print(f"  ✓ {len(alter_statements)} Felder hinzugefügt")
                except Exception as e:
                    print(f"  ❌ Fehler beim Hinzufügen der Felder: {e}")
                    return False
            
            conn.commit()
        
        else:
            # Generische Migration für andere Datenbanken
            print(f"\nFühre generische Migration für {db_url.drivername} aus...")
            try:
                for field_name in fields_to_add:
                    field_type, field_default, field_nullable = fields_config[field_name]
                    
                    sql = f"ALTER TABLE {table_name} ADD COLUMN {field_name} {field_type}"
                    
                    if field_default is not None:
                        sql += f" DEFAULT {field_default}"
                    
                    if not field_nullable:
                        sql += " NOT NULL"
                    
                    conn.execute(text(sql))
                    print(f"  ✓ {field_name} hinzugefügt")
                
                conn.commit()
            except Exception as e:
                print(f"  ❌ Fehler bei generischer Migration: {e}")
                print("  Bitte führen Sie die Migration manuell für Ihre Datenbank aus.")
                return False
    
    return True

def migrate():
    """Führt die Migration aus."""
    print("=" * 60)
    print("Migration zu Version 2.1.4")
    print("Dashboard-Konfiguration hinzufügen")
    print("=" * 60)
    
    # Erstelle die Flask-App
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    
    with app.app_context():
        try:
            # Felder-Konfiguration für users-Tabelle
            fields_config = {
                'dashboard_config': ('TEXT', None, True),  # field_type, default, nullable
            }
            
            # Migriere users-Tabelle
            if not migrate_table('users', fields_config):
                print("❌ Migration für 'users' fehlgeschlagen!")
                return False
            
            # Verifiziere die Migration
            print("\nVerifiziere Migration...")
            inspector = inspect(db.engine)
            
            required_fields = ['dashboard_config']
            
            if 'users' not in inspector.get_table_names():
                print("  ⚠ Warnung: Tabelle 'users' existiert nicht.")
                print("  Die Tabelle wird beim nächsten Start automatisch erstellt.")
            else:
                columns_after = {col['name']: col for col in inspector.get_columns('users')}
                missing_fields = [f for f in required_fields if f not in columns_after]
                
                if missing_fields:
                    print(f"  ❌ Warnung: In 'users' fehlen noch: {missing_fields}")
                    print("  Bitte überprüfen Sie die Datenbank-Logs.")
                else:
                    print(f"  ✓ Migration für 'users' erfolgreich abgeschlossen!")
            
            print("\n" + "=" * 60)
            print("Migration abgeschlossen!")
            print("=" * 60)
            print("\nHinzugefügtes Feld (users):")
            print("  - dashboard_config (TEXT, NULLABLE)")
            print("\nHinweis:")
            print("  Das Feld speichert JSON-Daten für die Dashboard-Konfiguration.")
            print("  Standard-Konfiguration wird beim ersten Zugriff automatisch erstellt.")
        
        except Exception as e:
            print(f"\n❌ Fehler bei der Migration: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == '__main__':
    migrate()

