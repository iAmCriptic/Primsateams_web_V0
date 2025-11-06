#!/usr/bin/env python3
"""
Script zum Prüfen der ONLYOFFICE-Konfiguration
"""

import os
import sys
from dotenv import load_dotenv

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

def check_onlyoffice_config():
    """Prüfe ONLYOFFICE-Konfiguration."""
    print("=" * 60)
    print("ONLYOFFICE-Konfiguration prüfen")
    print("=" * 60)
    
    onlyoffice_enabled = os.environ.get('ONLYOFFICE_ENABLED', 'False').lower() == 'true'
    onlyoffice_url = os.environ.get('ONLYOFFICE_DOCUMENT_SERVER_URL', '/onlyoffice')
    onlyoffice_secret = os.environ.get('ONLYOFFICE_SECRET_KEY', '')
    
    print(f"\nONLYOFFICE_ENABLED: {onlyoffice_enabled}")
    print(f"ONLYOFFICE_DOCUMENT_SERVER_URL: {onlyoffice_url}")
    print(f"ONLYOFFICE_SECRET_KEY: {'Gesetzt' if onlyoffice_secret else 'Nicht gesetzt (optional)'}")
    
    if not onlyoffice_enabled:
        print("\n⚠ WARNUNG: ONLYOFFICE ist nicht aktiviert!")
        print("Lösung: Setzen Sie ONLYOFFICE_ENABLED=True in Ihrer .env-Datei")
        return False
    
    # Generiere erwartete API-URL
    if onlyoffice_url.startswith('http'):
        api_url = f"{onlyoffice_url.rstrip('/')}/web-apps/apps/api/documents/api.js"
    else:
        api_url = f"http://localhost{onlyoffice_url.rstrip('/')}/web-apps/apps/api/documents/api.js"
    
    print(f"\nErwartete API-URL: {api_url}")
    
    # Teste ob URL erreichbar ist
    try:
        import requests
        print(f"\nTeste Erreichbarkeit von {api_url}...")
        response = requests.get(api_url, timeout=5)
        if response.status_code == 200:
            print("✓ ONLYOFFICE Document Server ist erreichbar!")
            print(f"  Status Code: {response.status_code}")
            print(f"  Content-Type: {response.headers.get('Content-Type', 'N/A')}")
            if 'javascript' in response.headers.get('Content-Type', '').lower():
                print("✓ Korrekte JavaScript-Datei empfangen")
            else:
                print("⚠ WARNUNG: Erwartete JavaScript-Datei, aber Content-Type ist anders")
        else:
            print(f"✗ ONLYOFFICE Document Server antwortet mit Status {response.status_code}")
            print("  Bitte prüfen Sie:")
            print("  1. Läuft ONLYOFFICE Document Server?")
            print("  2. Ist die URL korrekt?")
            print("  3. Gibt es Firewall-Probleme?")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Verbindungsfehler: ONLYOFFICE Document Server ist nicht erreichbar")
        print("  Bitte prüfen Sie:")
        print("  1. Läuft ONLYOFFICE Document Server?")
        print("  2. Ist die IP-Adresse/URL korrekt?")
        print("  3. Gibt es Netzwerk-Probleme?")
        return False
    except requests.exceptions.Timeout:
        print("✗ Timeout: ONLYOFFICE Document Server antwortet nicht")
        return False
    except ImportError:
        print("⚠ WARNUNG: requests-Bibliothek nicht installiert, kann Erreichbarkeit nicht testen")
        print("  Installieren Sie mit: pip install requests")
    
    print("\n" + "=" * 60)
    print("Konfiguration prüfen abgeschlossen")
    print("=" * 60)
    
    return True

if __name__ == '__main__':
    success = check_onlyoffice_config()
    sys.exit(0 if success else 1)

