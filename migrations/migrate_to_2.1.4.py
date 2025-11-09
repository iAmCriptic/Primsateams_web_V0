#!/usr/bin/env python3
"""
Datenbank-Migration: Version 2.1.4
Konsolidierte Migration für alle Versionen bis 2.1.4

Diese Migration führt alle bisherigen Migrationen in der richtigen Reihenfolge aus:

1. Version 1.5.2: Briefkasten-Felder zu folders hinzufügen
   - is_dropbox (Boolean)
   - dropbox_token (String, unique)
   - dropbox_password_hash (String, nullable)

2. Version 1.5.6: Freigabe-Felder zu folders und files hinzufügen
   - share_enabled (Boolean, default=False)
   - share_token (String, unique, nullable)
   - share_password_hash (String, nullable)
   - share_expires_at (DateTime, nullable)
   - share_name (String, nullable)

3. Borrow Group ID: Mehrfachausleihen für Inventory
   - borrow_group_id (String(50), nullable, indexiert) in borrow_transactions

4. Kalender-Features: Wiederkehrende Termine und öffentliche iCal-Feeds
   - recurrence_type, recurrence_end_date, recurrence_interval, recurrence_days
   - parent_event_id, is_recurring_instance, recurrence_sequence
   - public_ical_token, is_public
   - Tabelle: public_calendar_feeds

5. Version 2.1.4: Dashboard-Konfiguration
   - dashboard_config (TEXT, nullable) in users

WICHTIG: Die Felder sind bereits in den Modellen definiert.
Diese Migration ist nur für bestehende Datenbanken erforderlich.
Bei neuen Installationen werden die Felder automatisch durch db.create_all() erstellt.
"""

import os
import sys

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text, inspect


def migrate_table(table_name, fields_config, create_indexes=None):
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
        print(f"✓ Alle Felder in '{table_name}' existieren bereits.")
        return True
    
    print(f"\nFehlende Felder in '{table_name}' gefunden: {', '.join(fields_to_add)}")
    
    # Bestimme die Datenbank-Engine
    db_url = db.engine.url
    is_sqlite = 'sqlite' in str(db_url)
    is_mysql = 'mysql' in str(db_url) or 'mariadb' in str(db_url)
    is_postgres = 'postgresql' in str(db_url)
    
    with db.engine.connect() as conn:
        if is_sqlite:
            # SQLite unterstützt nur ein ALTER TABLE ADD COLUMN pro Statement
            for field_name in fields_to_add:
                field_type, field_default, field_nullable = fields_config[field_name]
                
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
            
            # Erstelle Indizes
            if create_indexes:
                for index_name, index_field, unique in create_indexes:
                    if index_field in fields_to_add:
                        try:
                            if unique:
                                conn.execute(text(f"""
                                    CREATE UNIQUE INDEX IF NOT EXISTS {index_name} 
                                    ON {table_name}({index_field}) 
                                    WHERE {index_field} IS NOT NULL
                                """))
                            else:
                                conn.execute(text(f"""
                                    CREATE INDEX IF NOT EXISTS {index_name} 
                                    ON {table_name}({index_field})
                                """))
                            print(f"  ✓ Index {index_name} erstellt")
                        except Exception as e:
                            print(f"  ⚠ Index {index_name} konnte nicht erstellt werden: {e}")
            
            conn.commit()
        
        elif is_mysql or is_postgres:
            # MySQL/MariaDB/PostgreSQL unterstützen mehrere Spalten in einem ALTER TABLE
            alter_statements = []
            
            for field_name in fields_to_add:
                field_type, field_default, field_nullable = fields_config[field_name]
                
                if is_mysql:
                    if field_type == 'BOOLEAN':
                        alter_sql = f"ADD COLUMN {field_name} TINYINT(1)"
                    elif field_type == 'TEXT':
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
            
            # Erstelle Indizes
            if create_indexes:
                for index_name, index_field, unique in create_indexes:
                    if index_field in fields_to_add:
                        try:
                            if unique:
                                conn.execute(text(f"CREATE UNIQUE INDEX {index_name} ON {table_name}({index_field})"))
                            else:
                                conn.execute(text(f"CREATE INDEX {index_name} ON {table_name}({index_field})"))
                            print(f"  ✓ Index {index_name} erstellt")
                        except Exception as e:
                            print(f"  ⚠ Index {index_name} konnte nicht erstellt werden: {e}")
            
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
                return False
    
    return True


def migrate_calendar_events():
    """Migriert calendar_events Tabelle mit wiederkehrenden Terminen."""
    inspector = inspect(db.engine)
    
    if 'calendar_events' not in inspector.get_table_names():
        print("\n⚠ Warnung: Tabelle 'calendar_events' existiert nicht.")
        print("  Die Tabelle wird beim nächsten Start automatisch erstellt.")
        return True
    
    print("\n1.4. Migriere 'calendar_events' Tabelle...")
    
    columns = {col['name']: col for col in inspector.get_columns('calendar_events')}
    
    fields_config = {
        'recurrence_type': ('VARCHAR(20)', "'none'", False),
        'recurrence_end_date': ('DATETIME', None, True),
        'recurrence_interval': ('INTEGER', '1', False),
        'recurrence_days': ('VARCHAR(50)', None, True),
        'parent_event_id': ('INTEGER', None, True),
        'is_recurring_instance': ('BOOLEAN', '0', False),
        'recurrence_sequence': ('INTEGER', None, True),
        'public_ical_token': ('VARCHAR(64)', None, True),
        'is_public': ('BOOLEAN', '0', False)
    }
    
    create_indexes = [
        ('idx_calendar_events_public_ical_token', 'public_ical_token', True)
    ]
    
    success = migrate_table('calendar_events', fields_config, create_indexes)
    
    # Foreign Key für parent_event_id
    db_url = db.engine.url
    is_sqlite = 'sqlite' in str(db_url)
    is_mysql = 'mysql' in str(db_url) or 'mariadb' in str(db_url)
    is_postgres = 'postgresql' in str(db_url)
    
    if 'parent_event_id' not in columns and not is_sqlite:
        try:
            with db.engine.connect() as conn:
                conn.execute(text("""
                    ALTER TABLE calendar_events 
                    ADD CONSTRAINT fk_calendar_events_parent_event_id 
                    FOREIGN KEY (parent_event_id) REFERENCES calendar_events(id)
                """))
                conn.commit()
                print("  ✓ Foreign Key für parent_event_id erstellt")
        except Exception as e:
            print(f"  ⚠ Foreign Key konnte nicht erstellt werden: {e}")
    
    return success


def migrate_public_calendar_feeds():
    """Erstellt public_calendar_feeds Tabelle."""
    inspector = inspect(db.engine)
    
    print("\n1.5. Erstelle 'public_calendar_feeds' Tabelle...")
    
    if 'public_calendar_feeds' in inspector.get_table_names():
        print("  ✓ Tabelle 'public_calendar_feeds' existiert bereits")
        return True
    
    db_url = db.engine.url
    is_sqlite = 'sqlite' in str(db_url)
    is_mysql = 'mysql' in str(db_url) or 'mariadb' in str(db_url)
    is_postgres = 'postgresql' in str(db_url)
    
    with db.engine.connect() as conn:
        if is_sqlite:
            sql = """
            CREATE TABLE IF NOT EXISTS public_calendar_feeds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token VARCHAR(64) NOT NULL UNIQUE,
                created_by INTEGER NOT NULL,
                name VARCHAR(200),
                include_all_events BOOLEAN NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL,
                last_synced DATETIME,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
            """
        elif is_mysql or is_mariadb:
            sql = """
            CREATE TABLE IF NOT EXISTS public_calendar_feeds (
                id INT AUTO_INCREMENT PRIMARY KEY,
                token VARCHAR(64) NOT NULL UNIQUE,
                created_by INT NOT NULL,
                name VARCHAR(200),
                include_all_events BOOLEAN NOT NULL DEFAULT FALSE,
                created_at DATETIME NOT NULL,
                last_synced DATETIME,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
            """
        elif is_postgres:
            sql = """
            CREATE TABLE IF NOT EXISTS public_calendar_feeds (
                id SERIAL PRIMARY KEY,
                token VARCHAR(64) NOT NULL UNIQUE,
                created_by INTEGER NOT NULL,
                name VARCHAR(200),
                include_all_events BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP NOT NULL,
                last_synced TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
            """
        
        try:
            conn.execute(text(sql))
            conn.commit()
            print("  ✓ Tabelle 'public_calendar_feeds' erstellt")
            return True
        except Exception as e:
            print(f"  ⚠ Fehler beim Erstellen der Tabelle: {e}")
            return False


def migrate():
    """Führt alle Migrationen aus."""
    print("=" * 60)
    print("Migration zu Version 2.1.4")
    print("Konsolidierte Migration für alle Versionen bis 2.1.4")
    print("=" * 60)
    
    # Erstelle die Flask-App
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    
    with app.app_context():
        try:
            # 1. Version 1.5.2: Briefkasten-Felder zu folders
            print("\n1.1. Version 1.5.2: Briefkasten-Felder zu 'folders'...")
            fields_config = {
                'is_dropbox': ('BOOLEAN', '0', False),
                'dropbox_token': ('VARCHAR(255)', None, True),
                'dropbox_password_hash': ('VARCHAR(255)', None, True)
            }
            create_indexes = [
                ('idx_folders_dropbox_token', 'dropbox_token', True)
            ]
            if not migrate_table('folders', fields_config, create_indexes):
                print("❌ Migration für 'folders' (1.5.2) fehlgeschlagen!")
                return False
            
            # 2. Version 1.5.6: Freigabe-Felder zu folders und files
            print("\n1.2. Version 1.5.6: Freigabe-Felder zu 'folders' und 'files'...")
            fields_config = {
                'share_enabled': ('BOOLEAN', '0', False),
                'share_token': ('VARCHAR(255)', None, True),
                'share_password_hash': ('VARCHAR(255)', None, True),
                'share_expires_at': ('DATETIME', None, True),
                'share_name': ('VARCHAR(255)', None, True)
            }
            create_indexes = [
                ('idx_folders_share_token', 'share_token', True),
                ('idx_files_share_token', 'share_token', True)
            ]
            if not migrate_table('folders', fields_config, [('idx_folders_share_token', 'share_token', True)]):
                print("❌ Migration für 'folders' (1.5.6) fehlgeschlagen!")
                return False
            if not migrate_table('files', fields_config, [('idx_files_share_token', 'share_token', True)]):
                print("❌ Migration für 'files' (1.5.6) fehlgeschlagen!")
                return False
            
            # 3. Borrow Group ID für Inventory
            print("\n1.3. Borrow Group ID für 'borrow_transactions'...")
            fields_config = {
                'borrow_group_id': ('VARCHAR(50)', None, True)
            }
            create_indexes = [
                ('idx_borrow_transactions_borrow_group_id', 'borrow_group_id', False)
            ]
            if not migrate_table('borrow_transactions', fields_config, create_indexes):
                print("❌ Migration für 'borrow_transactions' fehlgeschlagen!")
                return False
            
            # 4. Kalender-Features
            if not migrate_calendar_events():
                print("❌ Migration für 'calendar_events' fehlgeschlagen!")
                return False
            
            if not migrate_public_calendar_feeds():
                print("❌ Migration für 'public_calendar_feeds' fehlgeschlagen!")
                return False
            
            # 5. Version 2.1.4: Dashboard-Konfiguration
            print("\n1.6. Version 2.1.4: Dashboard-Konfiguration zu 'users'...")
            fields_config = {
                'dashboard_config': ('TEXT', None, True)
            }
            if not migrate_table('users', fields_config):
                print("❌ Migration für 'users' (2.1.4) fehlgeschlagen!")
                return False
            
            # Verifiziere die Migration
            print("\n" + "=" * 60)
            print("Verifiziere Migration...")
            print("=" * 60)
            
            inspector = inspect(db.engine)
            
            # Prüfe alle Tabellen
            checks = [
                ('folders', ['is_dropbox', 'dropbox_token', 'dropbox_password_hash', 
                            'share_enabled', 'share_token', 'share_password_hash', 
                            'share_expires_at', 'share_name']),
                ('files', ['share_enabled', 'share_token', 'share_password_hash', 
                          'share_expires_at', 'share_name']),
                ('borrow_transactions', ['borrow_group_id']),
                ('calendar_events', ['recurrence_type', 'recurrence_end_date', 
                                    'recurrence_interval', 'recurrence_days', 
                                    'parent_event_id', 'is_recurring_instance', 
                                    'recurrence_sequence', 'public_ical_token', 'is_public']),
                ('users', ['dashboard_config'])
            ]
            
            all_success = True
            for table_name, required_fields in checks:
                if table_name not in inspector.get_table_names():
                    print(f"  ⚠ Tabelle '{table_name}' existiert nicht (wird beim nächsten Start erstellt)")
                    continue
                
                columns_after = {col['name']: col for col in inspector.get_columns(table_name)}
                missing_fields = [f for f in required_fields if f not in columns_after]
                
                if missing_fields:
                    print(f"  ❌ Warnung: In '{table_name}' fehlen noch: {missing_fields}")
                    all_success = False
                else:
                    print(f"  ✓ '{table_name}': Alle Felder vorhanden")
            
            # Prüfe public_calendar_feeds Tabelle
            if 'public_calendar_feeds' in inspector.get_table_names():
                print(f"  ✓ 'public_calendar_feeds': Tabelle vorhanden")
            else:
                print(f"  ⚠ 'public_calendar_feeds': Tabelle existiert nicht (wird beim nächsten Start erstellt)")
            
            print("\n" + "=" * 60)
            if all_success:
                print("Migration erfolgreich abgeschlossen!")
            else:
                print("Migration abgeschlossen mit Warnungen!")
            print("=" * 60)
            
            print("\nZusammenfassung der hinzugefügten Features:")
            print("  - Version 1.5.2: Briefkasten-Felder (folders)")
            print("  - Version 1.5.6: Freigabe-Felder (folders & files)")
            print("  - Borrow Group ID: Mehrfachausleihen (borrow_transactions)")
            print("  - Kalender-Features: Wiederkehrende Termine & iCal-Feeds")
            print("  - Version 2.1.4: Dashboard-Konfiguration (users)")
            
            return all_success
        
        except Exception as e:
            print(f"\n❌ Fehler bei der Migration: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == '__main__':
    success = migrate()
    sys.exit(0 if success else 1)
