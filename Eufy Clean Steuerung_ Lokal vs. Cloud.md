# **Technische Referenz und Forschungsbericht: Eufy Clean Ökosystem-Integration und lokale Steuerungsarchitektur für Home Assistant**

## **Zusammenfassung**

Die Integration von Consumer-Robotik in lokale Hausautomationssysteme stellt eine signifikante Herausforderung in der heutigen Internet-of-Things (IoT)-Landschaft dar, insbesondere bei proprietären Ökosystemen, die Cloud-Konnektivität gegenüber lokaler Steuerung priorisieren. Eufy Clean (ehemals Eufy RoboVac), eine Untermarke von Anker Innovations, stellt in diesem Bereich ein komplexes Fallbeispiel dar. Während die Hardware für Befehl und Kontrolle (Command and Control \- C2) stark auf der Tuya IoT-Middleware basiert, variiert die Implementierung drastisch über die Modellgenerationen hinweg – von den grundlegenden „Bounce“-Navigationsmodellen bis hin zu fortschrittlichen LiDAR- und KI-gesteuerten Einheiten wie dem X10 Pro Omni und dem S1 Pro.  
Dieser Bericht dient als erschöpfende Wissenssammlung für Home Assistant-Integratoren und IoT-Ingenieure, die versuchen, Eufy Clean-Geräte von der Cloud zu entkoppeln. Er dokumentiert die spezifischen Netzwerkprotokolle, API-Endpunkte und Data Point System (DPS)-Zuordnungen, die für den lokalen Betrieb erforderlich sind. Zentral für diese Analyse ist die Unterscheidung zwischen der Legacy-Tuya-basierten Steuerung und den aufkommenden, jedoch noch unreifen Matter-over-Bridge-Implementierungen, die in den Flaggschiffmodellen der Jahre 2024/2025 zu finden sind. Die folgenden Abschnitte detaillieren die Methodik zur Extraktion kryptografischer Schlüssel, die spezifischen Architektur-Forks, die für aktuelle Modelle wie den L60 erforderlich sind, sowie die Grenzen aktueller Standardprotokolle bei der Bereitstellung hochauflösender Daten wie Live-Karten.  
Der Bericht priorisiert strikt Methoden der lokalen Steuerung ("Local Push") gegenüber Cloud-Polling-Mechanismen, um Latenzzeiten zu minimieren, die Privatsphäre zu maximieren und die Ausfallsicherheit bei Internetunterbrechungen zu gewährleisten.

## ---

**1\. Hardware-Taxonomie und Protokollklassifizierung**

Das Verständnis der Integrationsstrategie für einen spezifischen Eufy RoboVac erfordert eine präzise Klassifizierung der Navigationslogik des Geräts und des internen Kommunikationsmoduls. Die Integrationsmethode (Direktes Tuya vs. Cloud Polling vs. Matter) wird durch die zugrunde liegende Hardwaregeneration diktiert. Die Analyse der verfügbaren Modelle zeigt eine klare Trennung in vier technologische Hauptkategorien.

### **1.1 Die "Bounce"-Serie (Einstiegsklasse & Legacy)**

Diese Modelle nutzen primär die Tuya-MCU-Konfiguration mit Standard-Wi-Fi-Modulen (oft ESP8266-Varianten). Sie navigieren basierend auf einem Zufallsalgorithmus, der durch Infrarotsensoren zur Kollisionsvermeidung unterstützt wird. Da sie keine Karte der Umgebung erstellen, ist der Datenverkehr minimal und beschränkt sich auf Statusmeldungen und Steuerbefehle. Sie senden ihren Status über UDP-Port 6668 und können, sobald der lokale Schlüssel (local\_key) extrahiert wurde, mit hoher Zuverlässigkeit lokal gesteuert werden.1

| Modellbezeichnung | Navigationstechnologie | Konnektivität | Protokoll-Status | Integrations-Priorität |
| :---- | :---- | :---- | :---- | :---- |
| **RoboVac 11C** | Bounce (Zufall) | Wi-Fi (2.4GHz) | Tuya 3.1 (Legacy) | Hoch (Vollständig Lokal) |
| **RoboVac 11S MAX** | Bounce (Zufall) | Wi-Fi (2.4GHz) | Tuya 3.3 | Hoch (Vollständig Lokal) |
| **RoboVac 15C / 15C Max** | Bounce (Zufall) | Wi-Fi (2.4GHz) | Tuya 3.3 | Hoch (Vollständig Lokal) |
| **RoboVac 25C / 25C Max** | Bounce (Zufall) | Wi-Fi (2.4GHz) | Tuya 3.3 | Hoch (Vollständig Lokal) |
| **RoboVac 30C / 30C Max** | Bounce (Zufall) | Wi-Fi (2.4GHz) | Tuya 3.3 | Hoch (Vollständig Lokal) |
| **RoboVac 35C** | Bounce (Zufall) | Wi-Fi (2.4GHz) | Tuya 3.3 | Hoch (Vollständig Lokal) |
| **RoboVac R550C** | Bounce (Zufall) | Wi-Fi (2.4GHz) | Tuya 3.1 | Veraltet (Discontinued) |

**Analyse der Bounce-Integration:** Diese Geräte stellen das einfachste Integrationsszenario dar. Die Data Points (DPS) sind weitgehend standardisiert. Ein Befehl "Start" entspricht fast universell dem Setzen eines Booleschen Wertes oder eines Enums auf einem spezifischen Register. Da keine Kartendaten übertragen werden müssen, ist die Kommunikation extrem reaktionsschnell. Die primäre Herausforderung besteht hier lediglich in der Extraktion des Schlüssels, da ältere Methoden (wie das Auslesen von Logcat-Dateien alter Android-Apps) zunehmend durch Sicherheitsupdates der Eufy-App erschwert wurden.2

### **1.2 Die G-Serie (Smart Dynamic Navigation)**

Die G-Serie (z.B. G10, G30) repräsentiert eine Übergangsarchitektur. Sie verwenden Gyroskope und optische Flusssensoren für eine "Smart Dynamic Navigation", die logische Reinigungspfade (Bahnen) statt zufälliger Bewegungen ermöglicht. Technisch gesehen basieren sie weiterhin auf der Tuya-Architektur für Basisbefehle (Start, Stopp, Lüftergeschwindigkeit), generieren jedoch eine transiente Karte.1

| Modellbezeichnung | Navigationstechnologie | Besonderheit | Protokoll-Status | Karten-Status |
| :---- | :---- | :---- | :---- | :---- |
| **RoboVac G10 Hybrid** | Gyro \+ Optisch | Wischfunktion | Tuya 3.3 | Keine persistente Karte |
| **RoboVac G20 / G20 Hybrid** | Gyro \+ Optisch | Verbesserte Pfadplanung | Tuya 3.3 | Transiente Karte |
| **RoboVac G30** | Gyro 2.0 | Path Tracking Sensor | Tuya 3.3 | Cloud-Stream Map |
| **RoboVac G30 Edge/Verge** | Gyro 2.0 | Magnetstreifen-Support | Tuya 3.3 | Cloud-Stream Map |
| **RoboVac G32 Pro** | Gyro | Retail-spezifisch | Tuya 3.3 | Cloud-Stream Map |
| **RoboVac G40 / G40+** | Gyro | Selbstentleerung | Tuya 3.3 | Cloud-Stream Map |
| **RoboVac G50 / Hybrid** | Gyro | Neue Generation | Tuya 3.3 | Cloud-Stream Map |

**Analyse der G-Serien-Integration:** Das kritische Unterscheidungsmerkmal der G-Serie ist das Vorhandensein von Kartendaten, die jedoch *nicht* über das lokale Tuya-Protokoll als einfaches Bild oder Datenarray übertragen werden. Stattdessen wird die Karte als Datenstrom (Stream) an die Cloud gesendet, dort verarbeitet und an die App zurückgespielt. Für Home Assistant bedeutet dies, dass die *Steuerung* (Start/Stop/Saugkraft) lokal über localtuya oder Custom Components erfolgen kann, die *Karte* jedoch meist nicht lokal abgreifbar ist, ohne Cloud-APIs zu pollen, was dem Ziel der lokalen Steuerung widerspricht.4 Es gibt Berichte über erfolgreiche Flash-Versuche mit ESPHome auf dem G10 Hybrid, bei denen das Tuya-Modul physisch durch einen ESP8266 ersetzt wurde, um volle lokale Kontrolle zu erlangen.5

### **1.3 Die L-Serie und X-Serie (iPath™ Laser Navigation & AI)**

Diese Modelle integrieren LiDAR (LDS) für Simultaneous Localization and Mapping (SLAM). Dies erhöht die Komplexität der Datenpayload massiv. Während die Steuerbefehle Tuya-basiert bleiben, sind die Kartendaten oft verschlüsselt oder werden über separate Kanäle übertragen. Die Einführung der L60- und X8-Modelle brachte signifikante Änderungen in der Protokollhandhabung ("Magic Suffix Numbers" und veränderte DPS-Strukturen).

| Modellbezeichnung | Navigation | Besonderheit | Integrations-Notiz |
| :---- | :---- | :---- | :---- |
| **RoboVac L70 Hybrid** | Laser SLAM | Erstes LIDAR-Modell | Tuya (Veraltet, oft Cloud-abhängig) |
| **RoboVac L35 Hybrid/+** | Laser SLAM | Absaugstation | Standard L-Serie Logik |
| **RoboVac L50 / L50 SES** | Laser SLAM | Budget LIDAR | Benötigt Code-Anpassung (T226x) |
| **RoboVac L60 / L60 Hybrid** | Laser SLAM | Hair Detangling | **Kritisch:** Benötigt maximoei Fork |
| **RoboVac LR20 / LR30** | Laser SLAM | Hybrid-Modelle | Standard L-Serie Logik |
| **RoboVac X8 / X8 Hybrid** | Twin Turbine | Multi-Map, Zonen | Verschlüsselungsänderungen in Firmware |
| **RoboVac X9 Pro** | MopMaster™ | Hebbarer Mopp | Komplexe DPS für Mopp-Logik |

**Spezifische Herausforderungen bei L60 und X8:** Die Eufy L60 und X8 Hybrid führten Variationen in der Tuya-Protokollbehandlung ein, die Standard-Integrationsmethoden brachen. Insbesondere der L60 erfordert eine spezifische Dateistruktur in der Custom Component, um erkannt zu werden. Die Standard-Repositories (wie CodeFoodPixels) erkennen die Geräte-ID des L60 oft nicht korrekt, weshalb Nutzer auf spezifische Forks (z.B. den maximoei-Fork) ausweichen müssen, die die Python-Klassendefinitionen für T2267 (L60) explizit beinhalten.6 Die X8-Serie führte Multi-Map-Speicherung und Zonenreinigung ein, die auf komplexe DPS-Strings (Base64-kodiertes JSON) statt auf einfache Integer gemappt werden.9

### **1.4 Die Omni / S-Serie (Next-Gen AI & Matter)**

Die neuesten Flaggschiffmodelle markieren eine Abkehr hin zum Matter-Standard, bieten jedoch paradoxerweise oft eine reduzierte Funktionalität in Drittanbieter-Controllern aufgrund der Unreife der Matter-Vacuum-Binding-Spezifikationen (Version 1.2).

| Modellbezeichnung | Navigation | Konnektivität | Protokoll-Status |
| :---- | :---- | :---- | :---- |
| **X10 Pro Omni** | AI.See™ \+ Laser | Wi-Fi \+ Matter | Hybrid: Tuya lokal \+ Matter Bridge |
| **S1 Pro / S1 Omni** | 3D MatrixEye™ | Wi-Fi \+ Matter | Hybrid: Tuya lokal \+ Matter Bridge |
| **E-Serie (E25, E28)** | Laser | Wi-Fi | Standard High-End Logik |

**Matter vs. Native Kontrolle:** Obwohl der X10 Pro Omni und der S1 Pro über Matter kommunizieren können, zeigen Analysen, dass die exponierten Entitäten in Home Assistant stark limitiert sind – oft beschränkt auf "Start", "Stopp" und "Batterie".11 Fortgeschrittene Funktionen wie Mopp-Wäsche, Trocknung und raumspezifische Reinigung sind im aktuellen Matter-Standard (oder dessen Implementierung durch Eufy) oft noch nicht verfügbar. Dies zwingt Power-User dazu, weiterhin auf die proprietäre Tuya-Schnittstelle zurückzugreifen, um volle lokale Kontrolle zu erlangen.11

## ---

**2\. API-Architektur und lokale Steuerungsmethodik**

Um eine lokale Steuerung ("Local Push") zu erreichen, muss die EufyHome-App umgangen und direkt mit dem Mikrocontroller des Geräts kommuniziert werden. Eufy-Geräte operieren auf Basis des Tuya Smart-Protokolls. Die Architektur besteht aus der **TuyaMCU** (der Mikrocontroller, der die Logik des Roboters steuert) und einem Wi-Fi-Modul, das die Netzwerkkommunikation handhabt.

### **2.1 Das Tuya-Protokoll (Port 6668\)**

Die lokale Kommunikation erfolgt über TCP/UDP Port 6668\. Das Protokoll verwendet eine verschlüsselte Payload, die die Befehlsanweisungen (Data Points \- DPS) umschließt.

* **Version 3.1 vs. 3.3:** Die meisten älteren Eufy-Roboter (11S, 30C, G30) und auch viele neuere verwenden Version 3.3. Diese erfordert einen 16-stelligen local\_key für die Verschlüsselung (AES-128-ECB).  
* **Authentifizierung:** Das Gerät akzeptiert Befehle nur, wenn die Payload mit dem korrekten local\_key signiert ist, der mit der eindeutigen device\_id assoziiert ist.  
* **Sitzungsmanagement (Session):** Die Verbindung ist persistent. Home Assistant baut eine Socket-Verbindung zu Port 6668 auf und sendet "Heartbeat"-Pakete (Keep-Alive).  
* **Das Single-Socket-Problem:** Viele Tuya-Module (insbesondere ältere ESP8266-Varianten) erlauben nur *eine* gleichzeitige TCP-Verbindung. Wenn die offizielle Eufy-App auf einem Smartphone geöffnet ist, monopolisiert sie oft diesen Socket. Dies führt dazu, dass die Home Assistant-Integration "unavailable" wird oder flackert. Die Lösung besteht darin, die App komplett zu schließen (Force Close) oder die Internetverbindung des Roboters per Firewall zu blockieren (wodurch die App-Verbindung fehlschlägt und der Socket für HA frei wird).13

### **2.2 Cloud API vs. Lokale API**

Es ist essenziell, zwischen den beiden API-Ebenen zu unterscheiden:

1. **Cloud API:** Die offizielle Eufy/Tuya Cloud API (https://home-api.eufylife.com) wird primär für die Authentifizierung (Abruf der Schlüssel) und für Daten mit hoher Bandbreite genutzt, die lokal schwer zu handhaben sind (z.B. komplexe Kartenstreams bei der G-Serie oder Firmware-Updates).  
2. **Lokale API:** Diese wird für die unmittelbare Befehlsausführung genutzt (Statusänderungen, Lüftergeschwindigkeit, Moduswechsel). Dies ist die Priorität für Home Assistant-Integrationen, um niedrige Latenzen (\<50ms) zu gewährleisten und den Betrieb auch bei Internetausfällen sicherzustellen.

### **2.3 Der "Local Key" als Dreh- und Angelpunkt**

Der local\_key ist ein gemeinsames Geheimnis (Shared Secret), das generiert wird, wenn sich das Gerät mit der Eufy-Cloud koppelt (Pairing-Prozess).

* **Persistenz:** Der Schlüssel ändert sich *nicht* während des normalen Betriebs oder bei Router-Neustarts.  
* **Rotation:** Er ändert sich *jedes Mal*, wenn das Gerät aus der App entfernt und neu hinzugefügt (Re-Pairing) oder auf Werkseinstellungen zurückgesetzt wird.  
* **Strategie:** Um das Gerät dauerhaft lokal zu steuern, sollte man den Schlüssel einmal extrahieren und dann dem Gerät den Internetzugriff entziehen (VLAN/Firewall). Dies verhindert, dass das Gerät sich neu mit der Cloud synchronisiert und einen neuen Schlüssel aushandelt, was den extrahierten Schlüssel ungültig machen würde.

## ---

**3\. Extraktion der Anmeldeinformationen: Die local\_key Methodik**

Das Erlangen der device\_id und des local\_key ist der kritischste Schritt im Integrationsprozess. Historische Methoden wie Packet Capture (Man-in-the-Middle-Angriffe) oder die Nutzung alter Android APK-Versionen (z.B. v2.3) zum Auslesen von Logs sind aufgrund verbesserter App-Sicherheit (Certificate Pinning) und API-Änderungen weitgehend obsolet. Der aktuelle Industriestandard ist die Python-basierte API-Emulation.

### **3.1 Python-basierte Schlüsselextraktion (Empfohlene Methode)**

Das zuverlässigste Werkzeug ist der eufy-clean-local-key-grabber (oft gewartet von Rjevski oder abgeleiteten Forks wie apexad oder mitchellrj-Issues). Dieses Skript emuliert den Anmeldeprozess der Eufy-App, um Gerätedetails direkt von der API abzufragen.  
**Technischer Ablauf der Extraktion:**

1. **Authentifizierung:** Das Skript sendet einen POST-Request an https://home-api.eufylife.com/v1/user/email/login mit der E-Mail und dem Passwort des Nutzers. Dabei werden statische Client-Secrets verwendet, die aus der App extrahiert wurden.14  
2. **Token-Abruf:** Die API antwortet mit einem access\_token.  
3. **Geräteabfrage:** Das Skript nutzt diesen Token, um https://home-api.eufylife.com/v1/device/list/devices-and-groups abzufragen.  
4. **Entschlüsselung/Parsing:** Die Antwort (JSON) enthält die device\_id (meist im Klartext sichtbar) und den local\_key (in der API-Antwort als local\_code oder access\_key bezeichnet).

**Ausführungsumgebung:**  
Nutzer müssen dies in einer Python 3.9+ Umgebung ausführen. Abhängigkeiten umfassen typischerweise requests und aiohttp.

Python

\# Konzeptuelle Rekonstruktion der Extraktionslogik basierend auf \[14\] und \[15\]  
import requests

headers \= {  
    "Content-Type": "application/json"  
}  
\# Diese Credentials sind hardcodiert in der Eufy App  
data \= {  
    "client\_id": "eufyhome-app",  
    "client\_Secret": "GQCpr9dSp3uQpsOMgJ4xQ",   
    "email": "ihre\_email@domain.com",  
    "password": "ihr\_passwort"  
}

\# Schritt 1: Login  
response \= requests.post("https://home-api.eufylife.com/v1/user/email/login", json=data, headers=headers)  
token \= response.json().get('access\_token')

\# Schritt 2: Geräteliste abrufen  
device\_headers \= {"token": token, "category": "Home"}  
devices \= requests.get("https://home-api.eufylife.com/v1/device/list/devices-and-groups", headers=device\_headers)

\# Das Ausgabe-JSON enthält den kritischen 'local\_code' oder 'local\_key'  
print(devices.json())

**Wichtige Hinweise & Fallstricke:**

* **Regionale Locks:** Der API-Endpunkt kann für EU- vs. US-Konten variieren. Das Skript standardisiert oft auf den US-Endpunkt. EU-Nutzer müssen möglicherweise das Skript modifizieren, um auf die korrekten regionalen Server (z.B. Tuya EU Server) zu zeigen, falls der generische Login fehlschlägt.15  
* **Account Locking:** Häufiges Polling oder fehlerhafte Login-Versuche können den Account sperren. Es wird empfohlen, einen sekundären "Gast"-Account zu erstellen (via Family Sharing in der App) und diesen für die Integration zu nutzen. Dies schützt den Hauptaccount und erlaubt dennoch den Zugriff auf die Keys.  
* **2FA:** Wenn Zwei-Faktor-Authentifizierung aktiviert ist, funktionieren einfache Skripte oft nicht. Deaktivieren Sie 2FA temporär für die Extraktion oder nutzen Sie Skripte, die 2FA-Input unterstützen.

## ---

**4\. Home Assistant Integrationsstrategien**

Sobald device\_id und local\_key vorliegen, existieren drei primäre Integrationsstrategien, die je nach Modell und technischer Affinität gewählt werden sollten.

### **4.1 Strategie A: Custom Components ("robovac")**

Dies ist die ausgereifteste Methode für die Mehrheit der Eufy-Staubsauger. Es handelt sich um eine benutzerdefinierte Komponente (installierbar via HACS), die das generische Tuya-Protokoll spezifisch auf die Eigenheiten von Eufy zuschneidet.

* **Repository:** Ursprünglich mitchellrj/eufy\_robovac, weiterentwickelt von CodeFoodPixels/robovac.17 Für neue Modelle (L60) ist der Fork von maximoei oder Ascendor zwingend.19  
* **Mechanismus:** Erstellt eine vacuum-Entität in Home Assistant. Handhabt die spezifischen DPS-Mappings automatisch.  
* **Konfiguration:**  
  * Früher YAML-basiert, unterstützt nun UI Config Flow.  
  * Erforderlich: IP-Adresse, Device ID, Local Key.  
* **Vorteile:** Native Unterstützung für spezifische Eufy-Features (Lüftergeschwindigkeits-Übersetzung, Fehlercode-Parsing).  
* **Nachteile:** Die Entwicklung des Hauptzweigs (CodeFoodPixels) hat sich verlangsamt; neuere Modelle (L60, X10) erfordern spezifische, von der Community gepatchte Forks, um zu funktionieren.

### **4.2 Strategie B: LocalTuya (Generische Integration)**

Für Modelle, die noch nicht explizit von der robovac-Integration unterstützt werden oder bei denen der Nutzer maximale Kontrolle über jeden Datenpunkt wünscht, bietet LocalTuya eine rohe Schnittstelle. Der Nutzer muss manuell jeden DPS-Integer einer Home Assistant-Funktion zuordnen (z.B. Mapping von DPS 1 zu einem "Switch", DPS 102 zu einem "Select" für Lüftergeschwindigkeit).

* **Anwendbarkeit:** Ideal für brandneue Modelle (z.B. X10 Pro Omni direkt nach Release), bevor spezifische Integrationen aktualisiert wurden.  
* **Komplexität:** Hoch. Erfordert das Wissen, welche DPS-ID exakt welcher Funktion entspricht (siehe Abschnitt 5).  
* **Vorteile:** Null Abhängigkeit von Eufy-spezifischem Python-Code; hochgradig anpassbar; keine Wartezeit auf Updates von Maintainern.  
* **Nachteile:** Keine native Kartenunterstützung; die Konfiguration von Enums (Lüfterstufen) ist mühsam und fehleranfällig.20

### **4.3 Strategie C: Matter-Integration (X10 Pro Omni & S1 Pro)**

Die neueste Generation unterstützt Matter-over-Bridge. Dies ist der von den Herstellern präferierte Weg der Zukunft, aktuell jedoch oft enttäuschend in der Tiefe der Kontrolle.

* **Mechanismus:** Die Eufy-Basisstation agiert als Matter-Bridge und exponiert den Roboter als Matter-Gerät im lokalen Netzwerk.  
* **Aktueller Status (2025):**  
  * **Exposure:** Home Assistant erkennt das Gerät über die native Matter-Integration (Python Matter Server).  
  * **Entitäten:** Die Funktionalität ist rudimentär. Nutzer berichten oft, dass nur start, stop und battery als Entitäten sichtbar sind. Erweiterte Funktionen (Raumauswahl, Mopp-Reinigung, Absaugung triggern) fehlen, da der Matter-Standard für Roboterstaubsauger (v1.2) entweder von Eufy noch nicht vollständig implementiert oder vom Client noch nicht voll unterstützt wird.11  
  * **Fazit:** Matter ist derzeit **unterlegen** gegenüber den Methoden der lokalen Tuya-API für Power-User, die komplexe Automationen (z.B. "Reinige Küche nach dem Abendessen") benötigen.

## ---

**5\. Data Point System (DPS) Referenz**

Der Kern der lokalen Steuerung ist das Data Point System (DPS). Tuya-Geräte kommunizieren Zustandsänderungen über JSON-Payloads, wobei Schlüssel Integer (DPS IDs) sind und Werte den Zustand repräsentieren. Die Kenntnis dieser IDs ist essenziell für die Konfiguration von LocalTuya.

### **5.1 Standard/Gemeinsame DPS-Mappings**

Diese Mappings erscheinen konsistent über die C-Serie und G-Serie (Bounce/Gyro Modelle).22

| DPS ID | Funktion | Datentyp | Werte / Beschreibung |
| :---- | :---- | :---- | :---- |
| **1** | Power / Status | Boolean | true (An/Reinigen), false (Standby/Dock) |
| **2** | Arbeitsmodus | Enum | 0: Auto, 1: Spot, 2: Edge, 3: Single Room |
| **3** | Auto-Return | Boolean | true: Zurück zur Ladestation |
| **5** | Saugkraft (Legacy) | Enum | Lüfterstärke (Standard, Max, BoostIQ) – *oft bei älteren Modellen* |
| **15** | Status / Fehler | String/Enum | Detaillierter Status (Charging, Cleaning, Error codes) |
| **101** | Finde Roboter | Boolean | true: Spielt einen Ton ab, um das Gerät zu finden |
| **102** | Lüftergeschwindigkeit | Enum | Spezifische Saugstufen (Quiet, Standard, Turbo, Max) – *ersetzt oft DPS 5 bei neueren Modellen* |
| **104** | Batteriestand | Integer | 0-100 (Batterieprozentsatz) |

### **5.2 Modellspezifische Abweichungen und Details**

#### **RoboVac G30 / G30 Edge**

17  
Die G30-Serie führt Logik für "Dynamic Navigation" ein.

* **DPS 102 (Fan Speed):** Kritisch für das Setzen der Saugkraft. Ältere Integrationen suchen oft nach DPS 5, aber der G30 priorisiert oft 102\.  
* **Kartendaten:** Im Gegensatz zur L-Serie sind G30-Kartendaten nicht einfach über DPS abrufbar. Es handelt sich um einen Stream, der in die Cloud gepusht wird. LocalTuya kann diese Karte nicht rendern.

#### **RoboVac X8 / X8 Hybrid**

10  
Der X8 bietet "Twin Turbine"-Technologie und Multi-Map-Speicherung.

* **Verschlüsselung:** Berichte deuten darauf hin, dass der X8 in späteren Firmware-Versionen eine Variation der Schlüsselhandhabung oder Payload-Signierung verwendet, was oft zu "Failed to decrypt"-Fehlern in Standardbibliotheken führt.10  
* **Zonenreinigung:** Implementiert über komplexe String-Befehle, die an einen spezifischen Befehls-DPS (oft DPS 13 oder eine ähnliche benutzerdefinierte ID) gesendet werden und Koordinaten-Arrays enthalten.

#### **RoboVac L60 / L60 Hybrid**

6  
Der L60 ist ein neueres Modell, das die Kompatibilität mit dem Standard-CodeFoodPixels-Repository aufgrund interner Bezeichneränderungen brach.

* **Dateistruktur-Fix:** Um den L60 zu integrieren, muss zwingend der maximoei-Fork genutzt werden. Die Verzeichnisstruktur in custom\_components muss explizit die Modellidentifikationsdatei des L60 (T2267.py oder ähnlich) enthalten.  
* **Initialisierungsproblem:** Nutzer berichten oft, dass das Gerät trotz korrekter Schlüssel als "Nicht verfügbar" angezeigt wird. Dies wird gelöst, indem ein Status-Update erzwungen wird (manuelles Starten des Saugers am Gerät), was das initiale DPS-Paket an Home Assistant pusht und die Verbindung etabliert.7

#### **X10 Pro Omni / S1 Pro**

12

* **Szenen-Reinigung:** Diese Modelle verlassen sich stark auf "Szenen" oder "Routinen", die in der App definiert sind. Um eine spezifische Raumreinigung über Home Assistant auszulösen, muss man oft die "Scene ID" durch Sniffing (oder Ausprobieren von Integer-Werten auf DPS 5 oder einem Szenen-DPS) reverse-engineeren und einen scene\_clean-Befehl über den send\_command-Dienst senden.  
* **DPS 5 (Scene ID):** Das Setzen von DPS 5 auf einen Integer entspricht oft dem Auslösen einer spezifischen, vorgespeicherten Reinigungsroutine.

## ---

**6\. Detaillierte Installationsanleitung: Das L60 & X10 Szenario**

Aufgrund der Schwierigkeiten, die Nutzer mit den L60- und X10-Modellen haben, beschreibt dieser Abschnitt den spezifischen Workaround, der erforderlich ist, um diese Geräte im Jahr 2025 funktionstüchtig zu machen.

### **6.1 L60 Hybrid Integration (Die maximoei-Methode)**

Die Standard-HACS-Installation von "Eufy RoboVac" wird den L60 wahrscheinlich nicht erkennen, da die internen Modellkennungen (T2267) in der Codebasis fehlen. Folgen Sie dieser manuellen Installationsprozedur:

1. **Vorbereitung:** Stellen Sie sicher, dass Sie device\_id und local\_key über das in Abschnitt 3 beschriebene Python-Skript extrahiert haben.  
2. **Quellcode-Beschaffung:** Laden Sie den **L60-support Branch** (nicht den master Branch) aus dem maximoei/robovac Repository herunter.8  
3. **Verzeichnisstruktur:**  
   Navigieren Sie zu Ihrem Home Assistant config-Verzeichnis.  
   Stellen Sie sicher, dass der Pfad existiert: /config/custom\_components/robovac/.  
4. **Dateiplatzierung:**  
   Kopieren Sie *alle* Dateien aus dem heruntergeladenen Zip-Archiv in diesen Ordner. Es ist kritisch, dass das Unterverzeichnis vacuums die Python-Datei enthält, die dem L60 entspricht (wahrscheinlich T2267.py oder eine modifizierte T226x.py).  
5. **Konfiguration (YAML):**  
   Fügen Sie den Eintrag in die configuration.yaml ein (Legacy-Methode wird oft bevorzugt für bessere Kontrolle bei Forks):  
   YAML  
   eufy\_vacuum:  
     devices:  
       \- name: "Eufy L60"  
         address: "192.168.1.XXX" \# Statische IP ist dringend empfohlen  
         local\_key: "IHR\_LOCAL\_KEY"  
         device\_id: "IHRE\_DEVICE\_ID"  
         type: T2267  \# Essenziell: Muss mit dem Klassennamen in der Python-Datei übereinstimmen

6. **Initialisierung:** Starten Sie Home Assistant neu. **Wichtig:** Starten Sie den Staubsauger manuell am Gerät. Der L60 meldet seinen Status oft nicht sofort beim Verbindungsaufbau; er benötigt eine aktive Zustandsänderung, um das initiale DPS-Paket an Home Assistant zu pushen, damit er von "Nicht verfügbar" auf "Bereit" wechselt.7

### **6.2 X10 Pro Omni Integration**

Für den X10 ist die Matter-Integration die einfachste, aber funktionsärmste Methode. Für lokale Steuerung mittels Tuya-Protokollen:

1. **Discovery:** Der X10 antwortet möglicherweise nicht auf die Standard-UDP-Broadcasts, die von älteren Plugins zur Erkennung genutzt werden. Sie müssen die IP-Adresse statisch spezifizieren.  
2. **Port-Handling:** Stellen Sie sicher, dass Port 6668 durch alle internen Firewalls (VLANs) erlaubt ist.  
3. **Befehls-Injektion:** Um Funktionen wie "Mopp waschen" zu nutzen, müssen Sie wahrscheinlich rohe Tuya-Befehle senden. Nutzen Sie den Dienst localtuya.set\_dp.  
   * *Hypothetischer Befehl:* Wenn "Mopp waschen" DPS 105 (Boolean) ist, würden Sie true an DPS 105 senden, um den Docking-Prozess auszulösen.

## ---

**7\. Limitierungen und Sicherheitsbetrachtungen**

### **7.1 Das "Kartendaten"-Problem**

Eine häufige Nutzeranforderung ist die Anzeige der Live-Reinigungskarte in Home Assistant.

* **Tuya Maps:** Kartendaten sind *kein* Standard-DPS-Wert. Es handelt sich um einen binären Stream oder Blob.  
* **Lokale Extraktion:** Die lokale Extraktion dieses Streams ist extrem schwierig, da er oft proprietär kodiert ist. Projekte wie der "Tuya Cloud Map Extractor" versuchen dies, sind jedoch oft veraltet oder brechen bei Eufy-Geräten.27  
* **Fazit:** Derzeit gibt es keine zuverlässige, rein lokale Methode, um die Live-Karte für Eufy G/L/X-Serien in Home Assistant zu rendern, ohne auf Cloud-Polling oder instabile Drittanbieter-Parser zurückzugreifen.4

### **7.2 Netzwerkisolation (VLANs)**

Um die Privatsphäre zu maximieren, wird empfohlen, Eufy-Staubsauger in einem IoT-VLAN ohne Internetzugriff zu platzieren.

* **Einschränkung:** Die lokale Steuerung funktioniert über Subnetze hinweg *nur*, wenn mDNS/UDP-Broadcast-Reflexion (für Discovery) aktiviert ist, oder wenn die IP im Plugin statisch hinterlegt ist.  
* **Zeitsynchronisation:** Eufy-Staubsauger können zeitlich driften oder geplante Reinigungen verweigern, wenn sie keinen Zugriff auf NTP-Server haben. Erlauben Sie NTP (UDP Port 123\) nach außen, auch wenn Sie Cloud-APIs blockieren.  
* **Key Rotation:** Wenn das Gerät auf Werkseinstellungen zurückgesetzt wird, ändert sich der local\_key. Das Blockieren des Internetzugriffs verhindert, dass sich das Gerät erneut mit der Cloud paart und einen neuen Schlüssel generiert, wodurch der aktuelle Schlüssel effektiv "eingefroren" wird.

## ---

**8\. Fazit**

Das Eufy Clean Ökosystem bleibt ein valider Kandidat für lokale Hausautomation, vorausgesetzt, der Integrator ist bereit, eine fragmentierte Landschaft von Protokollen zu navigieren. Für Einstiegsmodelle (Bounce/Gyro) ist die Standard-Tuya V3.3-Integration robust und reaktionsschnell. Für Flaggschiffmodelle (L60, X10) erfordert die Integration spezifische, von der Community gewartete Forks und manuelle Dateimanipulation.  
Während die Matter-Unterstützung im X10 und S1 Pro eine Zukunft standardisierter, einfacher Integration verspricht, ist die aktuelle Implementierung für fortgeschrittene Nutzer unzureichend. Daher bleibt das **lokale Tuya-Protokoll via Port 6668**, accessed mittels Schlüsseln, die durch Python-Emulation extrahiert wurden, auch im Jahr 2025 der Goldstandard für die Steuerung von Eufy Clean-Geräten. Dieser Ansatz priorisiert Privatsphäre, Latenz und Zuverlässigkeit und folgt der Kernphilosophie der "Local-First"-Hausautomation.

### **Referenzen im Text:**

* **Schlüsselextraktion:** 14  
* **L60 Integration:** 7  
* **X10/Matter Probleme:** 11  
* **Protokoll-Details:** 1  
* **Custom Components:** 17

#### **Referenzen**

1. Which RoboVac models support WiFi/app? \- eufy Support | Troubleshooting & Customer Service, Zugriff am Januar 21, 2026, [https://service.eufy.com/article-description/Which-RoboVac-models-support-WiFi-app?ref=Home\_Page](https://service.eufy.com/article-description/Which-RoboVac-models-support-WiFi-app?ref=Home_Page)  
2. lorenzofattori/robovac30c\_homeassistant: Guide: How to connect the Eufy Robovac 30c To home assistant \- GitHub, Zugriff am Januar 21, 2026, [https://github.com/lorenzofattori/robovac30c\_homeassistant](https://github.com/lorenzofattori/robovac30c_homeassistant)  
3. Support for Eufy RoboVac or Smart Bulbs? \- Page 3 \- Home Assistant Community, Zugriff am Januar 21, 2026, [https://community.home-assistant.io/t/support-for-eufy-robovac-or-smart-bulbs/37970?page=3](https://community.home-assistant.io/t/support-for-eufy-robovac-or-smart-bulbs/37970?page=3)  
4. Tuya Vacuum Maps \- Custom Integrations \- Home Assistant Community, Zugriff am Januar 21, 2026, [https://community.home-assistant.io/t/tuya-vacuum-maps/790597](https://community.home-assistant.io/t/tuya-vacuum-maps/790597)  
5. ESPHome integration for replacing the Tuya module in the Eufy Robovac G10 Hybrid as well as reverse-engineering notes \- GitHub, Zugriff am Januar 21, 2026, [https://github.com/Rjevski/esphome-eufy-robovac-g10-hybrid](https://github.com/Rjevski/esphome-eufy-robovac-g10-hybrid)  
6. STep by Step installation Eufy L60 \- Page 3 \- Hardware \- Home Assistant Community, Zugriff am Januar 21, 2026, [https://community.home-assistant.io/t/step-by-step-installation-eufy-l60/805531?page=3](https://community.home-assistant.io/t/step-by-step-installation-eufy-l60/805531?page=3)  
7. STep by Step installation Eufy L60 \- Page 2 \- Hardware \- Home Assistant Community, Zugriff am Januar 21, 2026, [https://community.home-assistant.io/t/step-by-step-installation-eufy-l60/805531?page=2](https://community.home-assistant.io/t/step-by-step-installation-eufy-l60/805531?page=2)  
8. STep by Step installation Eufy L60 \- Hardware \- Home Assistant Community, Zugriff am Januar 21, 2026, [https://community.home-assistant.io/t/step-by-step-installation-eufy-l60/805531](https://community.home-assistant.io/t/step-by-step-installation-eufy-l60/805531)  
9. \[APP\]\[Pro\] Eufy Clean \- Page 14 \- Homey Community Forum, Zugriff am Januar 21, 2026, [https://community.homey.app/t/app-pro-eufy-clean/46610?page=14](https://community.homey.app/t/app-pro-eufy-clean/46610?page=14)  
10. Eufy X8 integration \- Home Assistant Community, Zugriff am Januar 21, 2026, [https://community.home-assistant.io/t/eufy-x8-integration/464104](https://community.home-assistant.io/t/eufy-x8-integration/464104)  
11. Matter & Works with Home Assistant is a scam\! : r/homeassistant \- Reddit, Zugriff am Januar 21, 2026, [https://www.reddit.com/r/homeassistant/comments/1nob3gn/matter\_works\_with\_home\_assistant\_is\_a\_scam/](https://www.reddit.com/r/homeassistant/comments/1nob3gn/matter_works_with_home_assistant_is_a_scam/)  
12. Integration for Eufy robovac x10 pro \- Feature Requests \- Home Assistant Community, Zugriff am Januar 21, 2026, [https://community.home-assistant.io/t/integration-for-eufy-robovac-x10-pro/811163](https://community.home-assistant.io/t/integration-for-eufy-robovac-x10-pro/811163)  
13. Add support for Eufy X10 Pro Omni · Issue \#68 · CodeFoodPixels/robovac \- GitHub, Zugriff am Januar 21, 2026, [https://github.com/CodeFoodPixels/robovac/issues/68](https://github.com/CodeFoodPixels/robovac/issues/68)  
14. EufyHome \- Home Assistant, Zugriff am Januar 21, 2026, [https://www.home-assistant.io/integrations/eufy/](https://www.home-assistant.io/integrations/eufy/)  
15. Discover local key from Eufy login details · Issue \#1 · mitchellrj/eufy\_robovac \- GitHub, Zugriff am Januar 21, 2026, [https://github.com/mitchellrj/eufy\_robovac/issues/1](https://github.com/mitchellrj/eufy_robovac/issues/1)  
16. Eufy Robovac 35c Working with Home\_Assistant \- Updated 11/2020 \- How To Guide \- Now with Edge Cleaning\! \- Page 14 \- Share your Projects\! \- Home Assistant Community, Zugriff am Januar 21, 2026, [https://community.home-assistant.io/t/eufy-robovac-35c-working-with-home-assistant-updated-11-2020-how-to-guide-now-with-edge-cleaning/152690?page=14](https://community.home-assistant.io/t/eufy-robovac-35c-working-with-home-assistant-updated-11-2020-how-to-guide-now-with-edge-cleaning/152690?page=14)  
17. CodeFoodPixels/robovac: Add a Eufy RoboVac easily to Home Assistant \- GitHub, Zugriff am Januar 21, 2026, [https://github.com/CodeFoodPixels/robovac](https://github.com/CodeFoodPixels/robovac)  
18. mitchellrj/eufy\_robovac \- GitHub, Zugriff am Januar 21, 2026, [https://github.com/mitchellrj/eufy\_robovac](https://github.com/mitchellrj/eufy_robovac)  
19. L60 hybrid support · Issue \#135 · CodeFoodPixels/robovac \- GitHub, Zugriff am Januar 21, 2026, [https://github.com/CodeFoodPixels/robovac/issues/135](https://github.com/CodeFoodPixels/robovac/issues/135)  
20. Use LocalTuya with Robot Vacuum \- Configuration \- Home Assistant Community, Zugriff am Januar 21, 2026, [https://community.home-assistant.io/t/use-localtuya-with-robot-vacuum/442541](https://community.home-assistant.io/t/use-localtuya-with-robot-vacuum/442541)  
21. Absolute beginners guide to setting up Local Tuya for Home Assistant \- Reddit, Zugriff am Januar 21, 2026, [https://www.reddit.com/r/homeassistant/comments/oglpgc/absolute\_beginners\_guide\_to\_setting\_up\_local\_tuya/](https://www.reddit.com/r/homeassistant/comments/oglpgc/absolute_beginners_guide_to_setting_up_local_tuya/)  
22. Device DPs \- Tuya Developer, Zugriff am Januar 21, 2026, [https://developer.tuya.com/en/docs/iot/device-function-point?id=Ka6y8bi672n1s](https://developer.tuya.com/en/docs/iot/device-function-point?id=Ka6y8bi672n1s)  
23. Function Definition \- Tuya Smart, Zugriff am Januar 21, 2026, [https://images.tuyacn.com/goat/pdf/1718309256444/Function%20Definition\_Tuya%20Developer%20Platform\_Tuya%20Developer%20Platform.pdf](https://images.tuyacn.com/goat/pdf/1718309256444/Function%20Definition_Tuya%20Developer%20Platform_Tuya%20Developer%20Platform.pdf)  
24. Eufy Robovac 35c Working with Home\_Assistant \- Updated 11/2020 \- How To Guide \- Now with Edge Cleaning\! \- Home Assistant Community, Zugriff am Januar 21, 2026, [https://community.home-assistant.io/t/eufy-robovac-35c-working-with-home-assistant-updated-11-2020-how-to-guide-now-with-edge-cleaning/152690?page=15](https://community.home-assistant.io/t/eufy-robovac-35c-working-with-home-assistant-updated-11-2020-how-to-guide-now-with-edge-cleaning/152690?page=15)  
25. An Introduction to the Map Function of the X8/X8 Hybrid \- eufy Support | Troubleshooting & Customer Service, Zugriff am Januar 21, 2026, [https://service.eufy.com/article-description/An-Introduction-to-the-Map-Function-of-the-X8-X8-Hybrid?ref=Home\_Page](https://service.eufy.com/article-description/An-Introduction-to-the-Map-Function-of-the-X8-X8-Hybrid?ref=Home_Page)  
26. Eufy clean l60 to home assistant? : r/homeassistant \- Reddit, Zugriff am Januar 21, 2026, [https://www.reddit.com/r/homeassistant/comments/1dmn7fv/eufy\_clean\_l60\_to\_home\_assistant/](https://www.reddit.com/r/homeassistant/comments/1dmn7fv/eufy_clean_l60_to_home_assistant/)  
27. New custom integration to add Vacuum Maps to HA from Tuya Vacuums. This is my first HA project so feedback is greatly appreciated\! : r/homeassistant \- Reddit, Zugriff am Januar 21, 2026, [https://www.reddit.com/r/homeassistant/comments/1gzwnte/new\_custom\_integration\_to\_add\_vacuum\_maps\_to\_ha/](https://www.reddit.com/r/homeassistant/comments/1gzwnte/new_custom_integration_to_add_vacuum_maps_to_ha/)  
28. Eufy Clean Tuya device ID/local key grabber (unmaintained) \- GitHub, Zugriff am Januar 21, 2026, [https://github.com/Rjevski/eufy-clean-local-key-grabber](https://github.com/Rjevski/eufy-clean-local-key-grabber)