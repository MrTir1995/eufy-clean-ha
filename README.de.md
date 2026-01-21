# Eufy Clean - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Release](https://img.shields.io/github/release/MrTir1995/eufy-clean-ha.svg)](https://github.com/MrTir1995/eufy-clean-ha/releases)

Eine Home Assistant Custom Integration für die **lokale Steuerung** von Eufy Clean (RoboVac) Staubsaugerrobotern. Diese Integration ermöglicht die direkte Steuerung deines Eufy-Roboters aus Home Assistant heraus, ohne auf Cloud-Dienste angewiesen zu sein.

> [🇬🇧 English Version](README.md)

## ✨ Funktionen

- 🏠 **Lokale Steuerung** - Direkte Kommunikation mit deinem Staubsauger über das Tuya-Protokoll (keine Cloud-Abhängigkeit)
- ⚡ **Echtzeit-Updates** - Push-basierte Statusaktualisierungen für sofortiges Feedback
- 🎯 **Vollständige Staubsauger-Steuerung**:
  - Reinigung starten/stoppen/pausieren
  - Zur Ladestation zurückkehren
  - Saugkraftsteuerung (Leise, Standard, Turbo, Max)
  - Batteriestand-Überwachung
  - Reinigungsstatus und Fehlermeldungen
- 🔧 **Einfache Einrichtung** - Unkomplizierter Konfigurationsprozess über die Home Assistant Oberfläche
- 🌐 **Mehrsprachige Unterstützung** - Englische und deutsche Übersetzungen enthalten

## 🤖 Unterstützte Geräte

Diese Integration unterstützt Eufy Clean Staubsaugerroboter, die das Tuya-Protokoll für lokale Kommunikation verwenden. Die folgenden Geräteserien werden unterstützt:

### Vollständig getestete Modelle
- **RoboVac 11C Serie** (11C, 11S MAX)
- **RoboVac 15C Serie** (15C, 15C MAX)
- **RoboVac 25C Serie** (25C, 25C MAX)
- **RoboVac 30C Serie** (30C, 30C MAX)
- **RoboVac 35C**

### Kompatible Modelle (Community-getestet)
- **G-Serie**: G10, G20, G30, G30 Edge, G40, G50 (mit Gyro-Navigation)
- **L-Serie**: L60, L70 (mit LiDAR-Navigation)
- **X-Serie**: X8, X10 (erweiterte Modelle)

> **Hinweis**: Neuere Modelle mit LiDAR-Navigation haben möglicherweise eingeschränkte Kartenunterstützung aufgrund von Verschlüsselung. Die Grundsteuerung (Starten, Stoppen, Dock, Saugkraft) funktioniert zuverlässig.

## 📦 Installation

### Methode 1: HACS (Empfohlen)

1. Öffne HACS in deinem Home Assistant
2. Klicke auf "Integrationen"
3. Klicke auf das Drei-Punkte-Menü in der oberen rechten Ecke
4. Wähle "Benutzerdefinierte Repositories"
5. Füge diese Repository-URL hinzu: `https://github.com/MrTir1995/eufy-clean-ha`
6. Wähle Kategorie "Integration"
7. Klicke "Hinzufügen"
8. Finde "Eufy Clean" in der Integrationsliste und klicke auf "Herunterladen"
9. Starte Home Assistant neu

### Methode 2: Manuelle Installation

1. Lade die neueste Version von [GitHub Releases](https://github.com/MrTir1995/eufy-clean-ha/releases) herunter
2. Entpacke den `eufy_clean` Ordner aus dem Archiv
3. Kopiere den `eufy_clean` Ordner in dein `<config>/custom_components/` Verzeichnis
4. Starte Home Assistant neu

## ⚙️ Konfiguration

### Schritt 1: Integration hinzufügen

1. Gehe zu **Einstellungen** → **Geräte & Dienste**
2. Klicke auf **"+ Integration hinzufügen"**
3. Suche nach **"Eufy Clean"**
4. Klicke darauf, um die Einrichtung zu starten

### Schritt 2: Zugangsdaten eingeben

Du benötigst deine Eufy-Kontodaten (E-Mail und Passwort). Diese werden **nur einmalig** während der Einrichtung verwendet, um:
- Deine Staubsaugergeräte zu entdecken
- Die lokalen Verschlüsselungsschlüssel (`device_id` und `local_key`) abzurufen
- Die IP-Adresse deines Staubsaugers zu ermitteln

> **Datenschutz-Hinweis**: Deine Zugangsdaten werden nur während der Ersteinrichtung verwendet. Nach der Einrichtung erfolgt die gesamte Kommunikation mit deinem Staubsauger **lokal** und benötigt keinen Cloud-Zugriff.

### Schritt 3: Gerät auswählen

- Die Integration erkennt automatisch alle Eufy Clean Geräte in deinem Konto
- Wähle den Staubsauger aus, den du hinzufügen möchtest
- Die IP-Adresse wird automatisch gesucht (oder als "Nicht gefunden" angezeigt)
- Klicke auf "Absenden"

### Schritt 4: IP-Adresse eingeben (Falls erforderlich)

Wenn die automatische IP-Erkennung fehlschlägt, wirst du aufgefordert, die IP-Adresse manuell einzugeben:

1. Finde die IP-Adresse deines Staubsaugers:
   - In der Eufy Clean App
   - In deinem Router (z.B. FRITZ!Box, Speedport)
   - Mit einem Netzwerk-Scanner
2. Gib die IP-Adresse ein (z.B. `192.168.1.100`)
3. Klicke auf "Absenden"

> **💡 Tipp**: Vergib deinem Staubsauger eine feste IP-Adresse in deinem Router, damit sie sich nicht ändert.

### IP-Adresse später ändern

Wenn sich die IP-Adresse deines Staubsaugers ändert, kannst du sie in den Integrationsoptionen aktualisieren:

1. Gehe zu **Einstellungen** → **Geräte & Dienste**
2. Finde die **Eufy Clean** Integration
3. Klicke auf **"Konfigurieren"**
4. Gib die neue IP-Adresse ein

## 🎮 Verwendung

Nach der Konfiguration erscheint dein Eufy-Staubsauger als Vacuum-Entität in Home Assistant.

### Grundlegende Steuerung

```yaml
# Reinigung starten
service: vacuum.start
target:
  entity_id: vacuum.eufy_robovac

# Zur Ladestation zurückkehren
service: vacuum.return_to_base
target:
  entity_id: vacuum.eufy_robovac

# Reinigung stoppen
service: vacuum.stop
target:
  entity_id: vacuum.eufy_robovac

# Saugkraft einstellen
service: vacuum.set_fan_speed
target:
  entity_id: vacuum.eufy_robovac
data:
  # Optionen: Quiet, Standard, Turbo, Max
  fan_speed: "Turbo"
```

### Automatisierungs-Beispiel

```yaml
automation:
  - alias: "Staubsauger beim Verlassen des Hauses starten"
    trigger:
      - platform: state
        entity_id: person.me
        to: "not_home"
    action:
      - service: vacuum.start
        target:
          entity_id: vacuum.eufy_robovac

  - alias: "Staubsauger zur Ladestation schicken bei Ankunft"
    trigger:
      - platform: state
        entity_id: person.me
        to: "home"
    action:
      - service: vacuum.return_to_base
        target:
          entity_id: vacuum.eufy_robovac
```

### Lovelace Karte Beispiel

```yaml
type: entities
title: Eufy RoboVac
entities:
  - entity: vacuum.eufy_robovac
  - type: attribute
    entity: vacuum.eufy_robovac
    attribute: battery_level
    name: Batterie
  - type: attribute
    entity: vacuum.eufy_robovac
    attribute: status
    name: Status
  - type: button
    name: Reinigung starten
    action_name: Starten
    tap_action:
      action: call-service
      service: vacuum.start
      target:
        entity_id: vacuum.eufy_robovac
  - type: button
    name: Zur Ladestation
    action_name: Dock
    tap_action:
      action: call-service
      service: vacuum.return_to_base
      target:
        entity_id: vacuum.eufy_robovac
```

## 🔧 Fehlerbehebung

Für eine vollständige Anleitung zur Fehlerbehebung, siehe [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

### Häufige Probleme

**Problem**: "Device Unreachable (Error 905)"

**Lösungen**:
1. **Gerät eingeschaltet**: Stelle sicher, dass der Staubsauger eingeschaltet ist
2. **WLAN-Verbindung**: Prüfe, ob das Gerät mit dem WLAN verbunden ist (Eufy Clean App)
3. **IP-Adresse korrekt**: Überprüfe die IP-Adresse in den Integrationseinstellungen
4. **Feste IP vergeben**: Empfohlen - vergib eine feste IP-Adresse im Router (DHCP-Reservierung)
5. **Firewall**: Stelle sicher, dass Port 6668 nicht blockiert wird
6. **Netzwerk-Test**: Pinge das Gerät an: `ping <IP-ADRESSE>`

---

**Problem**: "Verbindung zur Eufy Cloud fehlgeschlagen" während der Einrichtung

**Lösungen**:
- Überprüfe, ob deine Eufy-Kontodaten korrekt sind
- Stelle sicher, dass du während der Einrichtung eine aktive Internetverbindung hast
- Prüfe, ob dein Eufy-Konto Geräte in der Eufy Clean App registriert hat

---

**Problem**: Staubsauger wird nach der Einrichtung als "Nicht verfügbar" angezeigt

**Lösungen**:
1. **Prüfe, ob der Staubsauger eingeschaltet ist** und mit dem WLAN verbunden ist
2. **IP-Adresse überprüfen**: Die IP-Adresse des Staubsaugers könnte sich geändert haben
   - Prüfe die DHCP-Leases deines Routers
   - Aktualisiere die IP-Adresse in den Integrationsoptionen
   - **Empfohlen**: Vergib eine feste IP im Router
3. **Einzel-Verbindungs-Limit**: Eufy-Staubsauger erlauben oft nur eine TCP-Verbindung gleichzeitig
   - Schließe die Eufy Clean App auf allen Geräten (Force Close)
   - Starte die Integration in Home Assistant neu

---

**Problem**: "Keine Geräte gefunden"

**Lösungen**:
- Stelle sicher, dass dein Staubsauger in der **Eufy Clean App** (nicht Eufy Home) registriert ist
- Die Integration unterstützt nur RoboVac-Geräte
- Melde dich bei der Eufy Clean App an und prüfe, ob das Gerät dort sichtbar ist
4. **Netzwerk-Isolation**: Stelle sicher, dass dein Staubsauger und Home Assistant im selben Netzwerk sind oder kommunizieren können

### IP-Adresse statisch machen

Um IP-Adressänderungen zu vermeiden, konfiguriere eine statische IP oder DHCP-Reservierung für deinen Staubsauger:

1. **Router-Methode** (Empfohlen):
   - Melde dich im Admin-Panel deines Routers an
   - Finde die MAC-Adresse deines Staubsaugers in der Liste verbundener Geräte
   - Erstelle eine DHCP-Reservierung mit der MAC-Adresse

2. **Alternative**: Einige Router erlauben die statische IP-Zuweisung direkt in den Netzwerkeinstellungen des Staubsaugers

### Mehrere Geräte

**Problem**: Kann nur mit einem Staubsauger gleichzeitig verbinden

**Lösung**: Dies ist eine Einschränkung des Tuya-Protokolls. Einige Eufy-Modelle erlauben nur eine aktive Verbindung. Wenn du mehrere Staubsauger steuern möchtest:
- Füge jedes Gerät separat über die Integration hinzu
- Stelle sicher, dass die Eufy App geschlossen ist, wenn Home Assistant verbunden ist

### Fehlercodes

Häufige Fehlercodes und ihre Bedeutungen:

| Fehlercode | Bedeutung | Lösung |
|------------|-----------|---------|
| Rad blockiert | Rad ist blockiert | Prüfe und entferne Hindernisse von den Rädern |
| Seitenbürste blockiert | Seitenbürste ist verheddert | Reinige die Seitenbürste |
| Hauptbürste blockiert | Hauptbürste ist verheddert | Reinige die Hauptbürste |
| Festgefahren | Staubsauger ist festgefahren | Bewege den Staubsauger zu einem freien Bereich |
| Absturzsensor-Fehler | Fehlfunktion des Absturzsensors | Reinige die Absturzsensoren |
| Batterie schwach | Batterie ist zu schwach | Schicke den Staubsauger zur Ladestation |

## 🔐 Sicherheit & Datenschutz

- **Lokale Steuerung**: Nach der Ersteinrichtung erfolgt die gesamte Kommunikation lokal (keine Cloud-Abhängigkeit)
- **Zugangsdaten**: Deine Eufy-Zugangsdaten werden nur während der Einrichtung verwendet und nicht gespeichert
- **Schlüssel**: Nur die Geräte-ID und der lokale Verschlüsselungsschlüssel werden gespeichert (erforderlich für lokale Tuya-Kommunikation)
- **Netzwerk-Isolation**: Für maximale Sicherheit solltest du IoT-Geräte in einem separaten VLAN isolieren

## 🐛 Bekannte Einschränkungen

- **Kartenanzeige**: Live-Kartendaten sind aufgrund proprietärer Verschlüsselung nicht verfügbar (Cloud-basiert)
- **Erweiterte Funktionen**: Einige erweiterte Funktionen sind bei neueren Modellen möglicherweise nicht verfügbar (Raumauswahl, virtuelle Grenzen)
- **Einzel-Verbindung**: Nur eine Verbindung pro Gerät (Eufy App schließen, wenn Home Assistant verwendet wird)
- **LiDAR-Modelle**: Neuere Modelle mit LiDAR-Ausstattung haben möglicherweise eingeschränkte Funktionsunterstützung

## 🤝 Mitwirken

Beiträge sind willkommen! Wenn du mitwirken möchtest:

1. Forke das Repository
2. Erstelle einen Feature-Branch
3. Nimm deine Änderungen vor
4. Reiche einen Pull Request ein

Für die Entwicklungsumgebung siehe [DEVELOPMENT.md](DEVELOPMENT.md)

## 🙏 Danksagungen

- [TinyTuya](https://github.com/jasonacox/tinytuya) - Lokale Tuya-Protokoll-Implementierung
- Home Assistant Community für Anleitung und Unterstützung
- Eufy-Nutzer, die Gerätetests und Feedback beigesteuert haben

## 📚 Zusätzliche Dokumentation

- [DEVELOPMENT.md](DEVELOPMENT.md) - Entwicklungsumgebung einrichten
- [Technische Referenz: Eufy-Protokoll](Eufy%20Clean%20Steuerung_%20Lokal%20vs.%20Cloud.md) - Tiefenanalyse des Eufy/Tuya-Protokolls (Deutsch)
- [Integrations-Entwicklungsleitfaden](Home%20Assistant%20Custom%20Integration%20Entwicklung(1).md) - Home Assistant Integrationsarchitektur (Deutsch)

## 📞 Support

- 🐛 [Probleme melden](https://github.com/MrTir1995/eufy-clean-ha/issues)
- 💬 [Diskussionen](https://github.com/MrTir1995/eufy-clean-ha/discussions)
- ⭐ Gib diesem Repo einen Stern, wenn du es nützlich findest!

---

**Mit ❤️ für die Home Assistant Community erstellt**
