# Bekannte Einschränkungen und Problemlösung

## ⚠️ Aktueller Status (v1.2.1)

### Problem: Keine Geräte gefunden

**Symptom**: Die Integration authentifiziert sich erfolgreich, findet aber keine Geräte.

**Ursache**: Eufy RoboVac-Geräte werden über die **Tuya IoT Plattform** verwaltet, nicht direkt über die Eufy API.

### Technischer Hintergrund

Die Eufy Clean App verwendet intern zwei verschiedene APIs:

1. **Eufy Home API** (`home-api.eufylife.com`) - für Authentifizierung und Benutzerverwaltung
2. **Tuya API** (`a1.tuyaeu.com`) - für die eigentlichen Gerätedaten und lokale Schlüssel

Der offizielle `eufy-clean-local-key-grabber` macht folgendes:
```python
# 1. Login bei Eufy
eufy_client = EufyHomeSession(email, password)
user_info = eufy_client.get_user_info()

# 2. Verwende user_id um bei Tuya zu authentifizieren
tuya_username = f'eh-{user_info["id"]}'
tuya_client = TuyaAPISession(username=tuya_username, country_code=user_info["phone_code"])

# 3. Geräte von Tuya abrufen
for home in tuya_client.list_homes():
    for device in tuya_client.list_devices(home["groupId"]):
        print(device['devId'], device['localKey'])
```

### Workarounds

#### Option 1: Manuell Local Keys extrahieren (Empfohlen für jetzt)

1. Verwende das offizielle Tool:
   ```bash
   git clone https://github.com/Rjevski/eufy-clean-local-key-grabber.git
   cd eufy-clean-local-key-grabber
   pip install -r requirements.txt
   python -m eufy_local_id_grabber "your@email.com" "password"
   ```

2. Notiere dir:
   - Device ID
   - Local Key
   - IP-Adresse (aus deinem Router)

3. Füge die Integration mit diesen Daten manuell hinzu

#### Option 2: Alternative Integrations

- **LocalTuya** - Wenn du Device ID und Local Key hast
- **Tuya Integration** - Wenn du einen Tuya Developer Account erstellen möchtest

### Roadmap

Die Integration muss erweitert werden um:

- [ ] Tuya API Client implementieren
- [ ] Komplexe HMAC-Signatur-Generierung für Tuya Requests
- [ ] Tuya-spezifische Verschlüsselung für Passwörter
- [ ] Geräteabfrage über Tuya API statt Eufy API
- [ ] Multi-Home Support (Tuya Homes)

Dies ist eine signifikante Erweiterung, die sorgfältige Implementierung und Tests erfordert.

## Diagnose-Skripte

### check_eufy_account.py
Testet verschiedene API-Endpunkte und zeigt detaillierte Account-Informationen:
```bash
python scripts/check_eufy_account.py
```

Dies zeigt:
- Login-Response mit allen Feldern
- Verschiedene Device-Endpunkt-Versuche
- Deine Tuya User-ID
- Welche API-Endpunkte funktionieren

### debug_eufy_api.py
Testet die aktuelle Integration:
```bash
python scripts/debug_eufy_api.py
```

## Für Entwickler

Die Tuya API Implementierung erfordert:

1. **Authentifizierung**: Komplexes HMAC-basiertes Signatur-System
2. **Verschlüsselung**: RSA für Passwörter, AES für Geräte-Kommunikation
3. **Device ID Generation**: Spezielle Logik basierend auf Android Device Properties
4. **Crypto Utils**: MD5 Shuffling, Base64 Encoding

Referenz-Implementierung:
- https://github.com/Rjevski/eufy-clean-local-key-grabber/blob/master/eufy_local_id_grabber/clients.py
- https://github.com/Rjevski/eufy-clean-local-key-grabber/blob/master/eufy_local_id_grabber/crypto.py

Die Integration sollte idealerweise als separate Python-Bibliothek auf PyPI veröffentlicht werden,
ähnlich wie `tinytuya`, um die Wartbarkeit zu verbessern.
