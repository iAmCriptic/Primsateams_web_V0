# Push-Benachrichtigungen im Offline-Zustand reparieren

## Problem
Push-Benachrichtigungen funktionieren nicht, wenn die Webseite geschlossen ist (Offline-Zustand).

## Aktueller Status
- ✅ Lokale Benachrichtigungen funktionieren (wenn Webseite offen ist)
- ✅ Service Worker funktioniert
- ✅ API-Endpunkte funktionieren
- ❌ Push-Subscription wird nicht registriert
- ❌ Echte Push-Benachrichtigungen funktionieren nicht

## Mögliche Ursachen
1. **HTTPS-Problem**: Push-Benachrichtigungen funktionieren nur mit HTTPS
   - Aktuell wird mit HTTP getestet (`http://127.0.0.1:5000`)
   - Browser mit `--disable-web-security` wird verwendet
   - Möglicherweise funktioniert es nur mit echten HTTPS-Zertifikaten

2. **Push-Subscription Registrierung**: 
   - Console-Logs zeigen: "Push-Benachrichtigungen werden unterstützt"
   - Console-Logs zeigen: "Sicherer Kontext erkannt, registriere Push-Subscription"
   - ABER: Keine "Starte Push-Notification Registrierung..." Logs
   - Push-Subscription wird nie an Server gesendet

## Debugging-Logs implementiert
- Detaillierte Frontend-Logs mit Markierungen
- Detaillierte Backend-Logs (API + UTILS)
- Service Worker Debugging verbessert

## Nächste Schritte
1. HTTPS-Setup für lokale Entwicklung
2. Push-Subscription Registrierung debuggen
3. Echte Push-Benachrichtigungen testen

## Technische Details
- VAPID-Keys konfiguriert
- Service Worker implementiert
- Push-Subscription Model vorhanden
- WebPush-Bibliothek installiert

## Labels
- bug
- notifications
- push
