#!/usr/bin/env python3
"""
Test-Script für das Whitelist-System
"""

from app import create_app, db
from app.models.whitelist import WhitelistEntry
from app.models.user import User

def test_whitelist():
    app = create_app()
    with app.app_context():
        print("=== Whitelist-System Test ===\n")
        
        # Test 1: E-Mail-Adresse hinzufügen
        print("1. Teste E-Mail-Adresse hinzufügen...")
        email_entry = WhitelistEntry.add_entry("test@merian.schule", "email", "Test-E-Mail")
        if email_entry:
            print(f"   ✓ E-Mail-Eintrag erstellt: {email_entry.entry}")
        else:
            print("   ✗ Fehler beim Erstellen des E-Mail-Eintrags")
        
        # Test 2: Domain hinzufügen
        print("\n2. Teste Domain hinzufügen...")
        domain_entry = WhitelistEntry.add_entry("@merian.schule", "domain", "Merian Schule")
        if domain_entry:
            print(f"   ✓ Domain-Eintrag erstellt: {domain_entry.entry}")
        else:
            print("   ✗ Fehler beim Erstellen des Domain-Eintrags")
        
        # Test 3: Whitelist-Prüfung
        print("\n3. Teste Whitelist-Prüfung...")
        
        test_emails = [
            "test@merian.schule",      # Sollte durch E-Mail-Eintrag matchen
            "lehrer@merian.schule",    # Sollte durch Domain-Eintrag matchen
            "student@merian.schule",   # Sollte durch Domain-Eintrag matchen
            "test@example.com",        # Sollte NICHT matchen
            "other@test.de"            # Sollte NICHT matchen
        ]
        
        for email in test_emails:
            is_whitelisted = WhitelistEntry.is_email_whitelisted(email)
            status = "✓ WHITELISTED" if is_whitelisted else "✗ NOT WHITELISTED"
            print(f"   {email}: {status}")
        
        # Test 4: Alle Einträge anzeigen
        print("\n4. Alle Whitelist-Einträge:")
        entries = WhitelistEntry.query.all()
        for entry in entries:
            status = "Aktiv" if entry.is_active else "Inaktiv"
            print(f"   - {entry.entry} ({entry.entry_type}) - {status}")
        
        print("\n=== Test abgeschlossen ===")

if __name__ == "__main__":
    test_whitelist()
