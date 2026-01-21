# **Architektur und Entwicklungsumgebungen für Home Assistant Custom Integrations: Eine umfassende Analyse**

## **1\. Einleitung und Paradigmenwechsel in der Heimautomatisierung**

Die Landschaft der Heimautomatisierung hat sich in den letzten Jahren fundamental gewandelt. Während proprietäre Systeme lange Zeit dominierte, hat sich Home Assistant als de facto Standard für lokale, datenschutzfreundliche und herstellerübergreifende Automatisierung etabliert. Das Herzstück dieses Ökosystems ist die Erweiterbarkeit durch sogenannte Integrations. Während "Core Integrations" direkt im Hauptrepository von Home Assistant gepflegt werden, ermöglichen "Custom Integrations" Entwicklern, innovative Funktionen, Unterstützung für Nischen-Hardware oder experimentelle Features agil bereitzustellen, ohne den strengen Release-Zyklus des Kernsystems durchlaufen zu müssen. Technisch gesehen sind beide Varianten jedoch nahezu identisch, da sie auf denselben architektonischen Schnittstellen aufsetzen und dieselbe State Machine nutzen.  
Dieser Bericht bietet eine erschöpfende technische Analyse der Entwicklung von Custom Integrations. Er beleuchtet die zugrundeliegende asynchrone Architektur, die mandatorischen Dateistrukturen und die Best Practices für Datenfluss und Konfiguration. Ein besonderer Schwerpunkt liegt auf der Modernisierung der Entwicklungsumgebungen durch Containerisierung. Die Verwendung von Development Containers (Devcontainers) hat sich von einer Nischenlösung zum Industriestandard innerhalb der Home Assistant Community entwickelt. Wir werden die spezifischen Konfigurationen offizieller Repositories der home-assistant Organisation sowie führende Community-Blueprints detailliert untersuchen, um Entwicklern einen robusten Leitfaden für reproduzierbare Entwicklungsumgebungen an die Hand zu geben.

## ---

**2\. Architektur und Designprinzipien**

Das Verständnis der Home Assistant Architektur ist die unverzichtbare Basis für jede Entwicklung. Das System basiert auf Python und nutzt intensiv die asyncio-Bibliothek, um Tausende von Geräten und Zustandsänderungen parallel zu verwalten, ohne den Hauptausführungsthread zu blockieren.

### **2.1 Die Asynchrone Event-Schleife (Event Loop)**

Im Gegensatz zu klassischen synchronen Anwendungen, bei denen ein I/O-Vorgang (wie eine Netzwerkanfrage an eine Glühbirne) das gesamte Programm anhält, bis eine Antwort eintrifft, arbeitet Home Assistant nicht-blockierend. Jede Custom Integration muss sich diesem Muster unterordnen. Blockierender Code in einer Integration führt unweigerlich zu Warnmeldungen im Log ("Detected blocking call inside the event loop") und kann im schlimmsten Fall das gesamte Hausautomationssystem instabil machen.  
Entwickler müssen daher strikt zwischen async def-Funktionen (Coroutinen) und klassischen synchronen Funktionen unterscheiden. Die Integration interagiert primär über den Event Bus mit dem Kernsystem. Wenn ein Gerät seinen Status ändert, feuert die Integration ein Event, das die State Machine aktualisiert. Umgekehrt hören Integrations auf Events (z.B. call\_service), um Aktionen auf der Hardware auszuführen.

### **2.2 Der Lebenszyklus einer Integration**

Der Lebenszyklus einer Integration wird durch spezifische Einsprungpunkte in der \_\_init\_\_.py Datei definiert. Historisch gesehen war async\_setup der primäre Einstiegspunkt, der die Konfiguration aus der configuration.yaml auslas. Mit der strategischen Ausrichtung auf Benutzerfreundlichkeit hat sich dieser Fokus jedoch verschoben.1  
**Tabelle 1: Die Evolution der Initialisierungsmethoden**

| Methode | Historische Funktion | Moderne Best Practice |
| :---- | :---- | :---- |
| setup(hass, config) | Synchrone Initialisierung über YAML. | Veraltet, sollte vermieden werden. |
| async\_setup(hass, config) | Asynchroner Einstiegspunkt für YAML. | Wird primär für globale Setups genutzt (z.B. Registrierung generischer Services), gibt oft nur True zurück.2 |
| async\_setup\_entry(hass, entry) | Existierte früher nicht. | **Der Standard.** Wird für jeden Config Entry (UI-Konfiguration) aufgerufen. Hier findet die eigentliche Initialisierung der API-Clients und Koordinatoren statt.1 |
| async\_unload\_entry(hass, entry) | N/A | Zwingend erforderlich für das "Reload"-Feature. Muss Listener entfernen und Plattformen entladen, um Speicherlecks zu verhindern.2 |

Der moderne Ansatz verlangt, dass die Integration in der Lage ist, mehrfach instanziiert zu werden (Multi-Tenancy), da async\_setup\_entry für jede konfigurierte Instanz separat aufgerufen wird. Dies erfordert eine saubere Trennung von Laufzeitdaten, die typischerweise in hass.data\[entry.entry\_id\] gespeichert werden, anstatt globale Variablen zu nutzen.

### **2.3 Die Rolle des Manifests (manifest.json)**

Bevor Home Assistant überhaupt Python-Code lädt, analysiert es die manifest.json. Diese Datei fungiert als Metadaten-Layer und definiert die Identität und die Abhängigkeiten der Integration. Im Kontext von Custom Integrations ist das Vorhandensein eines version-Schlüssels obligatorisch, im Gegensatz zu Core-Integrations, wo dies optional ist.1  
Ein kritischer Aspekt des Manifests ist das requirements-Array. Home Assistant verfolgt den Ansatz, dass die eigentliche Kommunikationslogik mit der Hardware in einer separaten Python-Bibliothek auf PyPI (Python Package Index) liegen sollte. Die Integration selbst dient nur als "Glue Code" (Verbindungscode) zwischen dieser Bibliothek und der Home Assistant State Machine. Das Manifest stellt sicher, dass diese Abhängigkeiten automatisch in der korrekten Version installiert werden.4  
Zusätzlich definiert das Manifest die iot\_class. Diese Klassifizierung (z.B. local\_push, cloud\_polling) informiert den Benutzer transparent darüber, ob die Integration lokal arbeitet oder eine Cloud-Verbindung benötigt, und ob Statusupdates sofort (Push) oder verzögert (Polling) erfolgen. Dies ist entscheidend für die Erwartungshaltung bezüglich Latenzzeiten.4

## ---

**3\. Dateistrukturen und Komponenten-Taxonomie**

Eine Custom Integration muss einer rigiden Verzeichnisstruktur folgen, um vom System erkannt zu werden. Das Root-Verzeichnis der Integration muss exakt dem gewählten domain-Namen entsprechen und im Ordner \<config\_dir\>/custom\_components/ liegen. Abweichungen führen dazu, dass der Loader die Komponente ignoriert.

### **3.1 Obligatorische und Optionale Dateien**

Die Struktur lässt sich in infrastrukturelle Dateien und plattformspezifische Dateien unterteilen.  
**Tabelle 2: Anatomie einer Custom Integration**

| Dateiname | Status | Funktionale Beschreibung |
| :---- | :---- | :---- |
| manifest.json | **Obligatorisch** | Deklaration von Metadaten, Abhängigkeiten, IoT-Klasse und Auto-Discovery-Regeln.1 |
| \_\_init\_\_.py | **Obligatorisch** | Initialisiert die Komponente, verwaltet ConfigEntries und hält die zentrale Setup-Logik.4 |
| config\_flow.py | **Essenziell** | Definiert den UI-Dialog für die Einrichtung (ersetzt YAML). Notwendig, wenn config\_flow: true im Manifest steht.5 |
| strings.json | **Empfohlen** | Enthält alle Texte für Konfigurationsdialoge und Fehler in englischer Sprache. Ermöglicht Übersetzungen.6 |
| coordinator.py | **Best Practice** | Implementiert den DataUpdateCoordinator für zentralisiertes Abrufen von Daten.4 |
| const.py | **Standard** | Definiert Konstanten wie DOMAIN, Timeouts oder Standardwerte, um "Magic Strings" im Code zu vermeiden. |
| \[platform\].py | **Optional** | Implementierung spezifischer Entitäts-Typen wie sensor.py, light.py oder switch.py.1 |
| services.yaml | **Optional** | Dokumentiert benutzerdefinierte Service-Aufrufe für die Automatisierungs-UI.2 |

### **3.2 Plattform-Implementierung**

Home Assistant abstrahiert physische Geräte in logische Entitäten. Ein physisches Gerät, wie beispielsweise ein intelligenter Thermostat, wird in der Software oft durch mehrere Plattformen repräsentiert: Eine climate-Entität für die Steuerung, eine sensor-Entität für die Temperaturanzeige und eventuell eine binary\_sensor-Entität für den Verbindungsstatus.  
Um dies zu realisieren, ruft async\_setup\_entry in der \_\_init\_\_.py typischerweise die Methode hass.config\_entries.async\_forward\_entry\_setups auf. Diese Methode lädt dynamisch die entsprechenden Plattform-Dateien (z.B. climate.py), welche dann die Entitäten instanziieren und registrieren.7  
Ein häufiger Fehler in frühen Entwicklungsphasen ist die direkte Kommunikation jeder Entität mit der Hardware-API. Dies führt oft zu Inkonsistenzen (z.B. Schalter ist "An", aber Leistungssensor zeigt "0 Watt") und kann API-Limits sprengen. Die architektonische Lösung hierfür ist der DataUpdateCoordinator (typischerweise in coordinator.py). Er fungiert als Singleton pro Geräteinstanz, ruft die Daten einmal zentral ab und verteilt sie an alle abhängigen Entitäten, die von der Klasse CoordinatorEntity erben. Dies garantiert Datenkonsistenz über alle Plattformen hinweg.4

## ---

**4\. Konfigurations-Workflows: Der Weg zur UI**

Der signifikanteste Wandel in der Entwicklung von Integrations ist die Abkehr von YAML-Konfigurationen hin zu interaktiven "Config Flows". Dieser Mechanismus stellt sicher, dass Konfigurationen validiert werden, bevor sie gespeichert werden, und eliminiert Fehler, die erst beim Neustart des Systems auftreten würden.

### **4.1 Der Config Flow Handler (config\_flow.py)**

Der Config Flow ist im Kern ein Zustandsautomat, der den Benutzer durch den Einrichtungsprozess führt. Er wird durch die Klasse ConfigFlow definiert, die von homeassistant.config\_entries.ConfigFlow erbt.

#### **4.1.1 Der Benutzereinstieg (async\_step\_user)**

Dies ist der Standard-Einstiegspunkt, wenn ein Benutzer in der UI auf "Integration hinzufügen" klickt. Die Methode prüft typischerweise, ob bereits eine Instanz für das spezifische Gerät existiert, fordert Zugangsdaten an (z.B. Host, API-Token) und validiert diese durch einen Testaufruf an die API. Wenn die Validierung fehlschlägt, wird das Formular mit einer Fehlermeldung erneut angezeigt. Ist sie erfolgreich, wird der ConfigEntry erstellt und persistent im .storage-Verzeichnis von Home Assistant abgelegt.6

#### **4.1.2 Vermeidung von Duplikaten (Unique IDs)**

Ein kritisches Element der Architektur ist die Behandlung von Unique IDs. Eine Integration muss verhindern, dass dasselbe physische Gerät mehrfach (z.B. unter verschiedenen IP-Adressen) hinzugefügt wird. Hierzu wird await self.async\_set\_unique\_id(device\_unique\_id) aufgerufen, gefolgt von self.\_abort\_if\_unique\_id\_configured(). Als Unique ID eignen sich MAC-Adressen oder Seriennummern, jedoch keine IP-Adressen, da diese sich ändern können.8

### **4.2 Auto-Discovery Mechanismen**

Ein wesentlicher Vorteil von Home Assistant ist die automatische Erkennung von Geräten. Dies wird durch "Discovery Steps" im Config Flow realisiert. Das Manifest definiert, auf welche Netzwerksignale (SSDP, Zeroconf, Bluetooth, DHCP) die Integration reagieren soll.  
Empfängt Home Assistant ein passendes Signal (z.B. ein mDNS-Paket eines Druckers), wird der Config Flow automatisch im Schritt async\_step\_zeroconf (oder entsprechend) instanziiert. Die Integration kann dann die bereits gefundenen Daten (wie IP und Hostname) nutzen, um den Benutzer nur noch zur Bestätigung aufzufordern, anstatt alle Daten manuell eingeben zu lassen. Wichtig ist hierbei, dass auch im Discovery-Schritt sofort die Unique ID geprüft wird, um bestehende Konfigurationen lediglich zu aktualisieren (z.B. bei IP-Änderung), anstatt neue Einträge zu erzeugen.9

### **4.3 Options Flow und Rekonfiguration**

Die Anforderungen an eine Integration enden nicht mit der initialen Einrichtung. Benutzer müssen in der Lage sein, Parameter wie Polling-Intervalle oder API-Keys zu ändern.

* **Options Flow:** Dient der Anpassung von Verhaltensparametern, die nicht essenziell für die Verbindung sind. Er speichert Daten in entry.options. Um dies zu implementieren, muss der Config Flow Handler die Methode async\_get\_options\_flow definieren. Ein UpdateListener in der \_\_init\_\_.py sorgt dann dafür, dass die Integration bei Änderungen neu geladen wird.11  
* **Reconfigure Flow:** Dient der Korrektur essenzieller Verbindungsdaten (z.B. neues WLAN-Passwort für das Gerät). Der reconfigure-Schritt authentifiziert den Benutzer neu und aktualisiert den bestehenden ConfigEntry in-place, ohne dass Entitäten (und damit historische Daten) verloren gehen.8

## ---

**5\. Entwicklungsumgebungen: Devcontainers im Fokus**

Die Entwicklung für Home Assistant erfordert eine spezifische Umgebung mit exakten Python-Versionen (aktuell oft 3.12 oder 3.13) und Systembibliotheken (ffmpeg, libpcap etc.). Um "Works on my machine"-Probleme zu eliminieren, setzt die Community und das Core-Team fast ausschließlich auf **Visual Studio Code Devcontainers**. Diese Technologie nutzt Docker, um eine vollständige Entwicklungsumgebung zu kapseln. Der Quellcode auf dem Host-System wird in den Container "gemountet", sodass Entwickler ihren gewohnten Editor nutzen können, während der Code in einer isolierten, Linux-basierten Umgebung ausgeführt wird.12

### **5.1 Analyse relevanter Devcontainer-Repositories**

Für Entwickler von Custom Integrations ist es entscheidend, den richtigen Devcontainer für den jeweiligen Anwendungszweck zu wählen. Nicht alle Repositories der home-assistant Organisation dienen demselben Zweck.

#### **5.1.1 home-assistant/developers.home-assistant (Dokumentation)**

Dieses Repository beinhaltet den Quellcode für die Entwicklerdokumentation (developers.home-assistant.io).

* **Technologie:** Der Devcontainer basiert hier nicht auf Python, sondern auf **Node.js**, da die Dokumentation mit Docusaurus generiert wird.14  
* **Konfiguration:** Die devcontainer.json konfiguriert das Port-Forwarding für Port 3000\. Dies ermöglicht es dem Entwickler, die Dokumentation lokal im Browser unter localhost:3000 als Vorschau zu sehen, während sie im Container gerendert wird.15  
* **Einsatzzweck:** Dieser Container ist ausschließlich relevant, wenn man zur Dokumentation beitragen möchte. Er ist **nicht** für die Entwicklung von Integrations geeignet.

#### **5.1.2 home-assistant/core (Der Kern)**

Das Repository des Home Assistant Cores enthält eine sehr komplexe Devcontainer-Definition.

* **Komplexität:** Da der Core alle integrierten Komponenten unterstützen muss, enthält dieser Container eine massive Anzahl an vorinstallierten Systembibliotheken (z.B. für Z-Wave, Zigbee, diverse Medienformate).16  
* **Einrichtung:** Die Initialisierung erfolgt über Skripte wie script/setup, die eine vollständige Entwicklungsumgebung bootstrap-en.  
* **Relevanz:** Für Custom-Integration-Entwickler ist dieser Container meist zu schwergewichtig ("Overkill"). Er dient jedoch als Referenzimplementierung, um zu sehen, welche Systembibliotheken in der Produktionsumgebung (Home Assistant OS) verfügbar sind.17

#### **5.1.3 home-assistant/devcontainer (Basis-Images)**

Dieses Repository enthält nicht den Code für Home Assistant selbst, sondern die Dockerfiles für die Basis-Images, die von anderen Containern genutzt werden.

* **Struktur:** Es gibt spezifische Images für verschiedene Kontexte, z.B. ghcr.io/home-assistant/devcontainer:addons für Add-on-Entwicklung oder Varianten für den Supervisor.18  
* **Versionierung:** Die Images sind versioniert (z.B. 1-supervisor), um Stabilität zu gewährleisten, wenn sich Python-Versionen im Upstream ändern.19

#### **5.1.4 ludeeus/integration\_blueprint (Der Community-Standard)**

Dies ist das wichtigste Repository für Einsteiger und Profis im Bereich Custom Integrations. Es wird von ludeeus (dem Entwickler von HACS) gepflegt und gilt als Best-Practice-Referenz.

* **Konzept:** Der Devcontainer ist hier speziell darauf optimiert, *eine* spezifische Integration isoliert zu entwickeln, ohne den Ballast des gesamten Cores.  
* **Technische Details (devcontainer.json):**  
  * **Image:** Verwendet ein aktuelles Python-Image (z.B. mcr.microsoft.com/vscode/devcontainers/python:3.12), das die Anforderungen des HA Cores widerspiegelt.20  
  * **Post-Create Command:** Führt ein Skript aus (scripts/setup), das homeassistant und Test-Bibliotheken (pytest) via pip installiert. Dies geht deutlich schneller als das Klonen des Cores.20  
  * **Port Forwarding:** Leitet Port 8123 weiter, sodass die im Container laufende HA-Instanz auf dem Host erreichbar ist.  
  * **Extensions:** Installiert automatisch VS Code Extensions wie ms-python.python und ruff für Linting.20  
* **Workflow:** Entwickler nutzen oft Tools wie cookiecutter, um basierend auf diesem Blueprint ein neues Projekt zu generieren. Das Tool cookiecutter-homeassistant-custom-component automatisiert diesen Prozess und erstellt direkt die .devcontainer-Ordnerstruktur, inklusive Debugging-Konfigurationen (debugpy), die es erlauben, Breakpoints im Integrationscode zu setzen.21

### **5.2 Technische Analyse der devcontainer.json**

Eine korrekte devcontainer.json ist der Schlüssel zu einer funktionierenden Umgebung. Folgende Tabelle schlüsselt die essenziellen Eigenschaften auf, die in einer Custom Integration Konfiguration zu finden sind.  
**Tabelle 3: Analyse der devcontainer.json Konfiguration**

| Eigenschaft | Typischer Wert | Erklärung & Bedeutung |
| :---- | :---- | :---- |
| image | python:3.13 (oder ähnlich) | Definiert das Betriebssystem und die Laufzeitumgebung. Muss zur Python-Version der Ziel-HA-Version passen.23 |
| forwardPorts | \`\` | Öffnet den HTTP-Port von Home Assistant zum Host-System. Ohne dies ist kein Zugriff auf die UI möglich.24 |
| postCreateCommand | script/setup | Führt Shell-Befehle nach dem Erstellen des Containers aus. Hier werden Abhängigkeiten aus requirements\_test.txt installiert.20 |
| customizations.vscode.extensions | charliermarsh.ruff, ms-python | Erzwingt die Installation von Linting-Tools im Container, um Code-Qualität sicherzustellen.20 |
| runArgs | \--network=host | **Kritisch für Linux:** Erlaubt dem Container den Zugriff auf das Host-Netzwerk für Discovery (mDNS/SSDP). Unter Windows/Mac funktioniert dies aufgrund der Docker-Virtualisierung oft nicht wie erwartet.17 |

## ---

**6\. Qualitätssicherung und Best Practices**

Die Entwicklung einer Integration endet nicht mit funktionierendem Code. Um langfristig wartbar zu sein und in HACS aufgenommen zu werden, müssen strenge Qualitätsstandards eingehalten werden.

### **6.1 Statische Code-Analyse (Linting)**

In der Vergangenheit setzte Home Assistant auf eine Kombination aus black (Formatierung), flake8 (Linting) und isort (Import-Sortierung). Aktuell vollzieht sich ein massiver Shift hin zu **Ruff**. Ruff ist ein in Rust geschriebener Linter, der extrem performant ist und die Funktionen der oben genannten Tools vereint. Die Konfiguration erfolgt zentral über die pyproject.toml. Core-Entwickler und Blueprints haben hierfür strenge Regeln definiert (z.B. absolute Imports, Behandlung ungenutzter Variablen). Es ist Best Practice, pre-commit Hooks einzurichten, die Ruff vor jedem Git-Commit ausführen, um zu verhindern, dass unsauberer Code überhaupt ins Repository gelangt.25

### **6.2 Teststrategien**

Unit-Tests sind unerlässlich, insbesondere für den Config Flow, der viele Verzweigungen haben kann.

* **pytest-homeassistant-custom-component:** Da viele Test-Werkzeuge (Fixtures) tief im HA Core vergraben sind und nicht im normalen pip-Paket enthalten sind, nutzt die Community dieses spezielle Paket. Es extrahiert Test-Helfer wie MockConfigEntry oder aioclient\_mock und macht sie für Custom Integrations verfügbar.27  
* **Snapshot Testing:** Für komplexe Datenstrukturen (wie API-Antworten) empfiehlt sich die Nutzung von syrupy. Anstatt manuell jede Eigenschaft zu asserten (assert data\['temp'\] \== 20), vergleicht ein Snapshot-Test das gesamte Ergebnisobjekt mit einer gespeicherten "Gold Master"-Datei. Ändert sich die API-Struktur, schlägt der Test fehl, was Regressionen effektiv verhindert.27

## ---

**7\. Distribution und das HACS Ökosystem**

Nach der Entwicklung erfolgt die Verteilung meist über den Home Assistant Community Store (HACS). Damit eine Integration dort gelistet werden kann, muss eine hacs.json im Root-Verzeichnis liegen.  
Diese Datei steuert, wie HACS die Integration darstellt und validiert.

* **Wichtige Schlüssel:**  
  * name: Der Anzeigename im Store.  
  * content\_in\_root: Wenn false (Standard), erwartet HACS die Integration in einem Unterordner (meist custom\_components/domain).  
  * zip\_release: Wenn true, lädt HACS ein gezipptes Release von GitHub herunter, anstatt den Quellcode direkt zu klonen. Dies ist nützlich, wenn Build-Schritte (z.B. Kompilierung von Frontend-Assets) notwendig sind.28

Zusätzlich prüft HACS, ob die Integration die Qualitätsstandards erfüllt, z.B. ob alle Bilder und Dokumentationen vorhanden sind und ob die manifest.json valide ist. GitHub Actions Workflows, die diese Validierung bei jedem Push durchführen ("HACS Validation"), gehören zum Standardumfang moderner Blueprints.30

## ---

**8\. Fazit**

Die Entwicklung von Custom Integrations für Home Assistant hat sich professionalisiert. War es früher ausreichend, einige Zeilen Python-Code in eine Datei zu schreiben, erfordert der heutige Standard ein tiefes Verständnis der asynchronen Architektur, die Implementierung komplexer Config Flows und die Nutzung moderner Toolchains wie Devcontainers und Ruff.  
Die strikte Trennung von Konfiguration (Config Flow), Logik (Coordinator) und Darstellung (Entities) führt zu robusteren und wartbaren Systemen. Durch die Nutzung von Blueprints wie dem integration\_blueprint von ludeeus können Entwickler diese Komplexität jedoch beherrschen, da die Boilerplate-Konfiguration für Docker, VS Code und CI/CD bereits vorgerüstet ist. Dies ermöglicht es, sich auf die eigentliche Logik – die Integration des Geräts – zu konzentrieren, während die Einhaltung der architektonischen Richtlinien von Home Assistant sichergestellt bleibt.

#### **Referenzen**

1. Creating your first integration \- Home Assistant Developer Docs, Zugriff am Januar 19, 2026, [https://developers.home-assistant.io/docs/creating\_component\_index/](https://developers.home-assistant.io/docs/creating_component_index/)  
2. Service actions are registered in async\_setup \- Home Assistant Developer Docs, Zugriff am Januar 19, 2026, [https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/action-setup/](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/action-setup/)  
3. Custom Integration. Best way to handle Home Assistant shutdown : r/homeassistant \- Reddit, Zugriff am Januar 19, 2026, [https://www.reddit.com/r/homeassistant/comments/12y9w5c/custom\_integration\_best\_way\_to\_handle\_home/](https://www.reddit.com/r/homeassistant/comments/12y9w5c/custom_integration_best_way_to_handle_home/)  
4. Integration file structure | Home Assistant Developer Docs, Zugriff am Januar 19, 2026, [https://developers.home-assistant.io/docs/creating\_integration\_file\_structure](https://developers.home-assistant.io/docs/creating_integration_file_structure)  
5. Config flow | Home Assistant Developer Docs, Zugriff am Januar 19, 2026, [https://developers.home-assistant.io/docs/config\_entries\_config\_flow\_handler/](https://developers.home-assistant.io/docs/config_entries_config_flow_handler/)  
6. Integration needs to be able to be set up via the UI | Home Assistant Developer Docs, Zugriff am Januar 19, 2026, [https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-flow/](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-flow/)  
7. Working example of HA integration \- Page 3 \- Development \- Home Assistant Community, Zugriff am Januar 19, 2026, [https://community.home-assistant.io/t/working-example-of-ha-integration/730465?page=3](https://community.home-assistant.io/t/working-example-of-ha-integration/730465?page=3)  
8. Integrations should have a reconfigure flow \- Home Assistant Developer Docs, Zugriff am Januar 19, 2026, [https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/reconfiguration-flow/](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/reconfiguration-flow/)  
9. Config flow | Home Assistant Developer Docs, Zugriff am Januar 19, 2026, [https://developers.home-assistant.io/docs/config\_entries\_config\_flow\_handler](https://developers.home-assistant.io/docs/config_entries_config_flow_handler)  
10. Integration manifest | Home Assistant Developer Docs, Zugriff am Januar 19, 2026, [https://developers.home-assistant.io/docs/creating\_integration\_manifest/](https://developers.home-assistant.io/docs/creating_integration_manifest/)  
11. Options flow | Home Assistant Developer Docs, Zugriff am Januar 19, 2026, [https://developers.home-assistant.io/docs/config\_entries\_options\_flow\_handler/](https://developers.home-assistant.io/docs/config_entries_options_flow_handler/)  
12. Developing Custom Integrations for Home Assistant – Getting Started \- Helge Klein, Zugriff am Januar 19, 2026, [https://helgeklein.com/blog/developing-custom-integrations-for-home-assistant-getting-started/](https://helgeklein.com/blog/developing-custom-integrations-for-home-assistant-getting-started/)  
13. Set up development environment | Home Assistant Developer Docs, Zugriff am Januar 19, 2026, [https://developers.home-assistant.io/docs/development\_environment](https://developers.home-assistant.io/docs/development_environment)  
14. developers.home-assistant/package.json at master · home-assistant/developers.home-assistant · GitHub, Zugriff am Januar 19, 2026, [https://github.com/home-assistant/developers.home-assistant/blob/master/package.json](https://github.com/home-assistant/developers.home-assistant/blob/master/package.json)  
15. Developers website for Home Assistant. \- GitHub, Zugriff am Januar 19, 2026, [https://github.com/home-assistant/developers.home-assistant](https://github.com/home-assistant/developers.home-assistant)  
16. core/.devcontainer/devcontainer.json at dev · home-assistant/core · GitHub, Zugriff am Januar 19, 2026, [https://github.com/home-assistant/home-assistant/blob/dev/.devcontainer/devcontainer.json](https://github.com/home-assistant/home-assistant/blob/dev/.devcontainer/devcontainer.json)  
17. Set up development environment | Home Assistant Developer Docs, Zugriff am Januar 19, 2026, [https://developers.home-assistant.io/docs/development\_environment/](https://developers.home-assistant.io/docs/development_environment/)  
18. README.md \- home-assistant/devcontainer \- GitHub, Zugriff am Januar 19, 2026, [https://github.com/home-assistant/devcontainer/blob/main/README.md](https://github.com/home-assistant/devcontainer/blob/main/README.md)  
19. Custom devcontainers for the home-assistant org \- GitHub, Zugriff am Januar 19, 2026, [https://github.com/home-assistant/devcontainer](https://github.com/home-assistant/devcontainer)  
20. securityspy/.devcontainer.json at master \- GitHub, Zugriff am Januar 19, 2026, [https://github.com/briis/securityspy/blob/master/.devcontainer.json](https://github.com/briis/securityspy/blob/master/.devcontainer.json)  
21. GitHub \- oncleben31/cookiecutter-homeassistant-custom-component, Zugriff am Januar 19, 2026, [https://github.com/oncleben31/cookiecutter-homeassistant-custom-component](https://github.com/oncleben31/cookiecutter-homeassistant-custom-component)  
22. Quickstart Guide \- Home Assistant custom component Cookiecutter, Zugriff am Januar 19, 2026, [https://cookiecutter-homeassistant-custom-component.readthedocs.io/en/latest/quickstart.html](https://cookiecutter-homeassistant-custom-component.readthedocs.io/en/latest/quickstart.html)  
23. jpawlowski/hacs.integration\_blueprint: AI-enabled Modern Home Assistant Custom Integration Blueprint with \- GitHub, Zugriff am Januar 19, 2026, [https://github.com/jpawlowski/hacs.integration\_blueprint](https://github.com/jpawlowski/hacs.integration_blueprint)  
24. devcontainer/addons/devcontainer.json at main · home-assistant/devcontainer \- GitHub, Zugriff am Januar 19, 2026, [https://github.com/home-assistant/devcontainer/blob/main/addons/devcontainer.json](https://github.com/home-assistant/devcontainer/blob/main/addons/devcontainer.json)  
25. astral-sh/ruff: An extremely fast Python linter and code formatter, written in Rust. \- GitHub, Zugriff am Januar 19, 2026, [https://github.com/astral-sh/ruff](https://github.com/astral-sh/ruff)  
26. Configure Ruff Easily with pyproject.toml | by Gema Correa \- Medium, Zugriff am Januar 19, 2026, [https://medium.com/@gema.correa/configure-ruff-easily-with-pyproject-toml-f75914fab055](https://medium.com/@gema.correa/configure-ruff-easily-with-pyproject-toml-f75914fab055)  
27. MatthewFlamm/pytest-homeassistant-custom-component \- GitHub, Zugriff am Januar 19, 2026, [https://github.com/MatthewFlamm/pytest-homeassistant-custom-component](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component)  
28. General requirements \- HACS, Zugriff am Januar 19, 2026, [https://www.hacs.xyz/docs/publish/start/](https://www.hacs.xyz/docs/publish/start/)  
29. Include default repositories \- HACS, Zugriff am Januar 19, 2026, [https://hacs.xyz/docs/publish/include\#hacsjson](https://hacs.xyz/docs/publish/include#hacsjson)  
30. ha-ipixel-color/Home-Assistant-HACS-Integration-Development-Guide.md at main \- GitHub, Zugriff am Januar 19, 2026, [https://github.com/cagcoach/ha-ipixel-color/blob/main/Home-Assistant-HACS-Integration-Development-Guide.md](https://github.com/cagcoach/ha-ipixel-color/blob/main/Home-Assistant-HACS-Integration-Development-Guide.md)