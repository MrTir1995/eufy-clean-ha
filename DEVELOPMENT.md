# Eufy Clean - Entwicklungsdokumentation

> **📖 Hinweis für Anwender**: Wenn du nur die Integration nutzen möchtest, sieh dir stattdessen die [Benutzer-Dokumentation](README.md) ([Deutsche Version](README.de.md)) an.

Diese Dokumentation richtet sich an Entwickler, die an der Eufy Clean Home Assistant Integration arbeiten möchten.

## Übersicht

Entwicklungsumgebung für eine Home Assistant Custom Integration zur lokalen Steuerung von Eufy Clean (RoboVac) Geräten.

## 🚀 Quick Start

### Voraussetzungen

- Docker Desktop oder Docker Engine
- Visual Studio Code mit der "Dev Containers" Extension

### Entwicklungsumgebung starten

1. **Repository in VS Code öffnen**
   ```bash
   code /home/timo/Dokumente/Github/eufy_HA
   ```

2. **Devcontainer öffnen**
   - Drücke `F1` oder `Ctrl+Shift+P`
   - Wähle: "Dev Containers: Reopen in Container"
   - Warte, bis der Container erstellt und konfiguriert ist

3. **Eufy Credentials extrahieren**
   ```bash
   python3 scripts/get_eufy_keys.py
   ```
   Dies extrahiert `device_id` und `local_key` für deine Geräte.

4. **Home Assistant starten**
   ```bash
   hass -c config
   ```
   Oder nutze den VS Code Task: `Ctrl+Shift+P` → "Tasks: Run Task" → "Run Home Assistant"

5. **Home Assistant öffnen**
   - Öffne im Browser: http://localhost:8123
   - Erstelle einen Account beim ersten Start

## 📁 Projektstruktur

```
eufy_HA/
├── .devcontainer/          # Devcontainer Konfiguration
│   └── devcontainer.json
├── .vscode/                # VS Code Einstellungen
│   ├── launch.json        # Debug-Konfiguration
│   └── tasks.json         # VS Code Tasks
├── config/                 # Home Assistant Config (wird erstellt)
│   ├── configuration.yaml
│   └── custom_components/
│       └── eufy_clean/    # Deine Integration hier
├── scripts/
│   ├── setup              # Setup-Script (wird automatisch ausgeführt)
│   └── get_eufy_keys.py   # Credential-Extraktor
├── tests/                  # Unit Tests
├── requirements_test.txt   # Test Dependencies
└── pyproject.toml         # Ruff & Tool Config
```

## 🔧 Entwicklung

### Integration entwickeln

1. Erstelle deine Integration in `config/custom_components/eufy_clean/`
2. Starte Home Assistant mit dem Debugger (F5 in VS Code)
3. Setze Breakpoints und debugge deinen Code

### Tests ausführen

```bash
# Alle Tests
pytest tests/ -v

# Mit Coverage
pytest tests/ -v --cov=custom_components/eufy_clean

# Oder nutze VS Code Task
Ctrl+Shift+P → "Tasks: Run Task" → "Run Tests"
```

### Code Quality

```bash
# Linting
ruff check custom_components/eufy_clean

# Formatierung
ruff format custom_components/eufy_clean

# Oder nutze VS Code Tasks
```

## 🐛 Debugging

Die Devcontainer-Konfiguration enthält vorkonfigurierte Debug-Launches:

- **Home Assistant**: Startet HA mit Debugger (F5)
- **Python: Current File**: Debuggt die aktuelle Datei
- **Pytest: Current File**: Debuggt den aktuellen Test

## 📚 Dokumentation

Siehe die ausführlichen Dokumentationen im Repository:
- `Home Assistant Custom Integration Entwicklung(1).md` - Architektur & Best Practices
- `Eufy Clean Steuerung_ Lokal vs. Cloud.md` - Eufy-spezifische Protokoll-Details

## 🔑 Sicherheit

- **Niemals** Credentials in Git committen
- Die Datei `eufy_credentials.json` ist in `.gitignore`
- Nutze einen separaten "Gast"-Account für die Entwicklung
- Isoliere Eufy-Geräte in einem IoT-VLAN ohne Internetzugang (optional)

## 🛠️ Bekannte Probleme

### Eufy L60 / X10 Support

Für neuere Modelle wie L60 oder X10 benötigst du spezielle Forks:
- Siehe `Eufy Clean Steuerung_ Lokal vs. Cloud.md` Abschnitt 6

### Single Socket Problem

Eufy-Geräte erlauben oft nur eine TCP-Verbindung:
- Schließe die Eufy App komplett (Force Close)
- Oder blockiere Internet-Zugang des Roboters per Firewall

## 📦 Port-Übersicht

- **8123**: Home Assistant Web-Interface
- **6668**: Tuya-Protokoll (lokal zu den Robotern)

## 🤝 Contributing

1. Entwickle in einem Feature-Branch
2. Stelle sicher, dass alle Tests bestehen
3. Code muss Ruff-Checks bestehen
4. Erstelle Pull Request

## 📄 Lizenz

Siehe LICENSE-Datei (falls vorhanden)
