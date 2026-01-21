# Fehlerbehebung

## Gerät nicht erreichbar (Error 905)

### Symptome
```
Invalid status response: {'Error': 'Network Error: Device Unreachable', 'Err': '905', 'Payload': None}
```

### Ursachen
Dieser Fehler tritt auf, wenn Home Assistant nicht mit dem Eufy Clean Gerät kommunizieren kann.

### Lösungsschritte

1. **Gerät eingeschaltet und mit WLAN verbunden**
   - Stellen Sie sicher, dass Ihr Staubsauger eingeschaltet ist
   - Prüfen Sie in der Eufy Clean App, ob das Gerät online ist
   - Das Gerät muss mit demselben WLAN verbunden sein wie Home Assistant

2. **IP-Adresse korrekt**
   - Öffnen Sie die Integration in Home Assistant
   - Gehen Sie zu Einstellungen → Integrationen → Eufy Clean
   - Überprüfen Sie die IP-Adresse
   - Wenn die IP-Adresse falsch ist:
     - Finden Sie die richtige IP in Ihrem Router (z.B. FRITZ!Box, Speedport)
     - Oder verwenden Sie die Eufy Clean App
     - Aktualisieren Sie die IP-Adresse in der Integration

3. **Netzwerk-Konnektivität**
   - Pingen Sie das Gerät von Home Assistant:
     ```bash
     ping <IP-ADRESSE>
     ```
   - Das Gerät sollte antworten

4. **Firewall / Port-Freigabe**
   - Die Integration verwendet Port **6668** (Tuya Protocol)
   - Stellen Sie sicher, dass keine Firewall die Kommunikation blockiert
   - Bei VLANs: Routing zwischen Home Assistant und Gerät muss funktionieren

5. **Feste IP-Adresse vergeben**
   - Empfohlen: Vergeben Sie dem Staubsauger eine feste IP-Adresse im Router
   - So ändert sich die IP nicht nach einem Neustart
   - DHCP-Reservierung in den Router-Einstellungen

### Weitere Diagnose

#### Debug-Logs aktivieren
Fügen Sie zu Ihrer `configuration.yaml` hinzu:
```yaml
logger:
  default: info
  logs:
    custom_components.eufy_clean: debug
```

Starten Sie Home Assistant neu und prüfen Sie die Logs unter:
Einstellungen → System → Protokolle

#### Netzwerk-Scan
Die Integration versucht automatisch, Geräte im lokalen Netzwerk zu finden.
Falls dies fehlschlägt, geben Sie die IP-Adresse manuell ein.

#### Local Key überprüfen
Falls Sie kürzlich:
- Das Gerät zurückgesetzt haben
- Die Eufy Clean App neu installiert haben
- Das WLAN gewechselt haben

Dann müssen Sie möglicherweise den Local Key neu abrufen:
1. Löschen Sie die Integration in Home Assistant
2. Richten Sie sie neu ein
3. Die Integration holt automatisch den neuen Local Key von der Tuya API

## Authentifizierungsfehler

### Symptome
```
invalid_auth: Ungültige Anmeldedaten
```

### Lösung
- Überprüfen Sie E-Mail und Passwort Ihres Eufy Kontos
- Verwenden Sie die gleichen Zugangsdaten wie in der Eufy Clean App
- **Wichtig**: Wenn Sie 2-Faktor-Authentifizierung verwenden, könnte dies Probleme verursachen

## Keine Geräte gefunden

### Symptome
```
no_devices: Keine Geräte gefunden
```

### Lösung
- Stellen Sie sicher, dass Ihr Staubsauger in der Eufy Clean App registriert ist
- Die Integration findet nur Geräte, die in Eufy **Clean** (nicht Eufy Home) registriert sind
- Unterstützte Geräte:
  - RoboVac Serie (G10, G30, L35, L60, etc.)
  - Alle Eufy Clean Staubsaugerroboter

## Integration lädt nicht

### Lösung
1. Überprüfen Sie die Logs auf Fehler
2. Stellen Sie sicher, dass die Integration korrekt installiert wurde
3. Starten Sie Home Assistant neu
4. Falls weiterhin Probleme: Öffnen Sie ein Issue auf GitHub

## Weitere Hilfe

Wenn Sie weiterhin Probleme haben:
1. Aktivieren Sie Debug-Logging
2. Sammeln Sie die Logs
3. Öffnen Sie ein Issue auf GitHub: https://github.com/MrTir1995/eufy-clean-ha/issues
4. Fügen Sie die Logs bei (entfernen Sie sensible Daten wie IP-Adressen, Device IDs)
