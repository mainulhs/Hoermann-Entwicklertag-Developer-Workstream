# Hörmann Entwicklertag - Developer Workstream [L200-300]

**Dauer**: 2-3 Stunden  
**Ziel**: Vom Pflichtenheft zur belastbaren Software mit AI-gestützter Entwicklung

---

## Ihr Szenario

Sie sind Senior Developer im Digitalisierungsteam bei Hörmann. Ihr wichtigster Industriekunde - **MegaSteel Manufacturing** - benötigt bis Ende der Woche eine vollständige Software-Lösung für ihr **Industrielles Anlagenüberwachungssystem**. Die bisherigen manuellen Prozesse und Excel-Listen zur Anlagenverwaltung sind nicht mehr ausreichend für ihre wachsende Produktionslinie.

**Problem**: Ihr Team-Lead hat Ihnen einen funktionierenden Prototyp hinterlassen, aber: "Da sind noch mehrere **Sicherheitslücken** drin, die **Performance ist nicht optimal**, und wir brauchen **bessere Tests**. Nutzen Sie AI-gestützte Entwicklung, um diese Probleme zu identifizieren und zu beheben!"

**Ihre Mission**: 
- Analysieren Sie die bestehende Anwendung auf Sicherheitsprobleme
- Identifizieren und beheben Sie Performance-Engpässe
- Verbessern Sie die Testabdeckung mit Property-Based Testing
- Containerisieren Sie die Anwendung für moderne Deployment-Praktiken

Der Kunde wartet. Zeit zu zeigen, was moderne AI-gestützte Entwicklung kann!

---

## Systemübersicht

Das **Industrielle Anlagenüberwachungssystem** bietet:

- **Anlagenregistrierung**: Verwaltung von Industrieanlagen (Pumpen, Motoren, Förderbänder, Kompressoren)
- **Sensordatenerfassung**: Aufzeichnung von Messwerten (Temperatur, Druck, Vibration)
- **Alarmverwaltung**: Automatische Alarme bei Schwellwertüberschreitungen
- **Wartungsverfolgung**: Planung und Dokumentation von Wartungsarbeiten
- **Web-Dashboard**: Interaktive Oberfläche zur Systemüberwachung
- **REST API**: JSON-basierte API für externe Systemintegration

### Systemarchitektur

```mermaid
graph TB
    subgraph "Benutzer"
        Browser[Web Browser]
        API_Client[API Client/Externe Systeme]
    end
    
    subgraph "Flask Anwendung"
        WebUI[Web UI Routes<br/>Dashboard, Formulare]
        RestAPI[REST API<br/>JSON Endpunkte]
        Auth[Authentifizierung<br/>Login, Token]
        
        subgraph "Business Logic"
            EquipMgr[Equipment Manager]
            SensorProc[Sensor Processor]
            AlertGen[Alert Generator]
            AuthSvc[Auth Service]
        end
        
        subgraph "Data Access Layer"
            EquipRepo[Equipment Repository]
            SensorRepo[Sensor Data Repository]
            AlertRepo[Alert Repository]
            MaintRepo[Maintenance Repository]
            UserRepo[User Repository]
        end
    end
    
    subgraph "Datenspeicherung"
        DB[(SQLite Datenbank<br/>equipment, sensor_readings,<br/>alerts, maintenance, users)]
    end
    
    Browser -->|HTTP| WebUI
    API_Client -->|HTTP/JSON| RestAPI
    
    WebUI --> Auth
    RestAPI --> Auth
    
    WebUI --> EquipMgr
    WebUI --> SensorProc
    WebUI --> AlertGen
    
    RestAPI --> EquipMgr
    RestAPI --> SensorProc
    RestAPI --> AlertGen
    
    Auth --> AuthSvc
    AuthSvc --> UserRepo
    
    EquipMgr --> EquipRepo
    SensorProc --> SensorRepo
    SensorProc --> AlertGen
    AlertGen --> AlertRepo
    EquipMgr --> MaintRepo
    
    EquipRepo --> DB
    SensorRepo --> DB
    AlertRepo --> DB
    MaintRepo --> DB
    UserRepo --> DB
    
    style Browser fill:#e3f2fd
    style API_Client fill:#e3f2fd
    style WebUI fill:#fff3e0
    style RestAPI fill:#fff3e0
    style Auth fill:#ffebee
    style EquipMgr fill:#e8f5e9
    style SensorProc fill:#e8f5e9
    style AlertGen fill:#e8f5e9
    style AuthSvc fill:#e8f5e9
    style DB fill:#f3e5f5
```

### Datenfluss: Messwert erfassen

```mermaid
sequenceDiagram
    participant U as Benutzer
    participant W as Web UI
    participant SP as Sensor Processor
    participant SR as Sensor Repository
    participant AG as Alert Generator
    participant AR as Alert Repository
    participant DB as Datenbank
    
    U->>W: Messwert eingeben<br/>(Anlage, Typ, Wert)
    W->>SP: record_reading(data)
    SP->>SP: Validierung
    SP->>SR: create(reading)
    SR->>DB: INSERT sensor_reading
    DB-->>SR: OK
    SR-->>SP: reading_id
    
    SP->>SP: check_thresholds(reading)
    alt Schwellwert überschritten
        SP->>AG: generate_alert(equipment_id, type, severity)
        AG->>AR: create(alert)
        AR->>DB: INSERT alert
        DB-->>AR: alert_id
        AR-->>AG: alert_id
        AG-->>SP: alert_generated
    end
    
    SP-->>W: success + alert_info
    W-->>U: Erfolg anzeigen<br/>(+ Alarm falls generiert)
```

---

## Task 0: Entwicklungsumgebung vorbereiten

<details>
<summary><strong>Task 0.1: Projekt klonen und einrichten</strong></summary>

### Aufgabe

1. **Klonen Sie das Repository** (falls noch nicht geschehen)
2. **Öffnen Sie den Projektordner** in Ihrer IDE
3. **Erstellen Sie eine virtuelle Python-Umgebung**:
   ```bash
   # Versuchen Sie zuerst:
   python -m venv venv
   # Falls das nicht funktioniert:
   python3 -m venv venv
   
   # Aktivieren:
   source venv/bin/activate      # Mac/Linux
   venv\Scripts\activate         # Windows
   ```
4. **Installieren Sie die Abhängigkeiten**:
   ```bash
   pip install -r requirements.txt
   # Falls pip nicht funktioniert:
   pip3 install -r requirements.txt
   ```

### Überprüfung

```bash
# Python-Version prüfen (versuchen Sie beide Befehle)
python --version   # Sollte Python 3.8+ anzeigen
python3 --version  # Alternative, falls python nicht funktioniert

# Installierte Pakete prüfen
pip list    # Sollte Flask, Hypothesis, pytest zeigen
pip3 list   # Alternative, falls pip nicht funktioniert
```

> [!TIP]
> Auf Windows-Systemen funktioniert meist `python` und `pip`. Auf manchen Systemen (Mac/Linux) müssen Sie `python3` und `pip3` verwenden.

</details>

<details>
<summary><strong>Task 0.2: Anwendung starten</strong></summary>

### Aufgabe

1. **Starten Sie die Anwendung**:
   ```bash
   python app.py
   # Falls das nicht funktioniert:
   python3 app.py
   ```

2. **Öffnen Sie im Browser**: http://localhost:5000

3. **Melden Sie sich an** mit:
   - Benutzername: `admin`
   - Passwort: `admin123`

### Erwartetes Ergebnis

- Dashboard zeigt deutsche Anlagennamen
- Aktive Alarme werden angezeigt
- Navigation funktioniert

> [!TIP]
> Lassen Sie die Anwendung im Hintergrund laufen während Sie am Code arbeiten.

</details>

<details>
<summary><strong>Task 0.3: Tests ausführen</strong></summary>

### Aufgabe

Führen Sie die bestehenden Tests aus:

```bash
pytest -v
```

### Erwartetes Ergebnis

Alle Tests sollten erfolgreich durchlaufen (grün).

> [!TIP]
> Diese Tests verwenden Property-Based Testing mit Hypothesis - eine moderne Testmethode, die automatisch viele Testfälle generiert.

</details>

---

## Phase 1: Warm-up - System verstehen mit AI (15 Minuten)

> [!NOTE]
> **Lernziel**: Machen Sie sich mit der Anwendung vertraut und lernen Sie, wie AI-Assistenten Ihnen helfen können, Code schnell zu verstehen.

<details>
<summary><strong>Task 1.1: Anwendung erkunden</strong></summary>

### Aufgabe

Öffnen Sie die Anwendung im Browser (http://localhost:5000) und erkunden Sie alle Seiten:

1. **Dashboard** - Übersicht aller Anlagen mit Gauge-Charts
2. **Anlage hinzufügen** - Formular zur Registrierung neuer Anlagen
3. **Messwert erfassen** - Sensordaten aufzeichnen
4. **Wartung** - Wartungsaufzeichnungen und überfällige Wartungen
5. **Alarme** - Aktive und bestätigte Alarme
6. **Anmelden** - Authentifizierung

### Erwartetes Ergebnis

Sie haben einen Überblick über alle Funktionen der Anwendung.

</details>

<details>
<summary><strong>Task 1.2: AI-Assistent nutzen - Code-Erklärungen</strong></summary>

### Aufgabe

Nutzen Sie Ihren AI-Assistenten (Q Developer, Copilot, etc.), um die Anwendungsstruktur zu verstehen.

**Fragen Sie Ihren AI-Assistenten:**

1. **Über die Hauptseiten:**
   - "Erkläre in 1-2 Sätzen, was die Dashboard-Seite macht"
   - "Was ist der Zweck der Wartungsseite?"
   - "Wie funktioniert die Alarmgenerierung?"

2. **Über die Architektur:**
   - "Öffne `app.py` - Was macht diese Datei?"
   - "Erkläre die Struktur des `repositories/` Ordners"
   - "Was ist der Unterschied zwischen Services und Repositories?"

3. **Über spezifische Komponenten:**
   - "Öffne `routes/web.py` - Welche Routen gibt es?"
   - "Was macht die Klasse `SensorProcessor` in `services/sensor_processor.py`?"
   - "Erkläre die Datenbank-Tabellen in `schema.sql`"

### Beispiel-Prompts

```
"Analysiere die Datei routes/web.py und erkläre mir in 2-3 Sätzen, 
welche Hauptfunktionen diese Routen bereitstellen."
```

```
"Schaue dir services/alert_generator.py an und erkläre, 
wann und wie Alarme generiert werden."
```

```
"Öffne templates/dashboard.html und beschreibe, 
welche Informationen auf dem Dashboard angezeigt werden."
```

### Erwartetes Ergebnis

Sie verstehen:
- Die Hauptkomponenten der Anwendung
- Wie die verschiedenen Layer (Routes → Services → Repositories → Database) zusammenarbeiten
- Welche Funktionalität jede Seite bietet

> [!TIP]
> Nutzen Sie AI nicht nur zum Code schreiben, sondern auch zum Code verstehen! Das spart Zeit und hilft beim Onboarding.

</details>

<details>
<summary><strong>Task 1.3: Projektstruktur verstehen</strong></summary>

### Aufgabe

Lassen Sie sich von Ihrem AI-Assistenten die Projektstruktur erklären.

**Fragen Sie:**
- "Erkläre mir die Ordnerstruktur dieses Projekts"
- "Welche Dateien sind für die Web-UI verantwortlich?"
- "Wo finde ich die Datenbank-Logik?"
- "Welche Test-Dateien gibt es und was testen sie?"

### Erwartetes Ergebnis

Sie wissen, wo Sie welchen Code finden:
- **`app.py`** - Haupteinstiegspunkt
- **`routes/`** - Web UI und API Endpunkte
- **`services/`** - Business-Logik
- **`repositories/`** - Datenbankzugriff
- **`templates/`** - HTML-Templates
- **`test_*.py`** - Property-Based Tests

</details>

---

## Phase 2: Feature-Entwicklung - Equipment Management erweitern (45 Minuten)

> [!NOTE]
> **Lernziel**: Nutzen Sie AI-Assistenten, um eine neue Funktion zu entwickeln und in die bestehende Anwendung zu integrieren.

<details>
<summary><strong>Task 2.1: Fehlende Funktionalität identifizieren</strong></summary>

### Aufgabe

Analysieren Sie die bestehende Anwendung und identifizieren Sie fehlende Equipment-Management-Funktionen.

**Fragen Sie Ihren AI-Assistenten**:
- "Öffne `services/equipment_manager.py` - Welche Methoden sind implementiert?"
- "Öffne `routes/web.py` - Welche Equipment-Routen existieren bereits?"
- "Vergleiche die beiden Dateien - welche Funktionen fehlen in der Web-UI?"

<details>
<summary>💡 <strong>Hinweis: Erwartetes Ergebnis</strong> (klicken zum Anzeigen)</summary>

<br>

Sie sollten feststellen:
- ✅ `equipment_manager.py` hat `update_equipment()` und `delete_equipment()` Methoden
- ✅ Es gibt bereits eine Equipment-Detail-Seite (`/equipment/<id>`)
- ❌ Es gibt **keine** Route zum Bearbeiten von Equipment
- ❌ Es gibt **keine** Route zum Löschen von Equipment
- ❌ Es gibt **keine** Template-Seite für Equipment-Bearbeitung

🎯 **Ihre Aufgabe**: Implementieren Sie die fehlenden Edit- und Delete-Funktionen!

</details>

</details>

<details>
<summary><strong>Task 2.2: Equipment-Edit-Route implementieren</strong></summary>

### Aufgabe

Erstellen Sie eine neue Route in `routes/web.py` zum Bearbeiten von Equipment.

**Fragen Sie Ihren AI-Assistenten**:
- "Erstelle eine Route `/equipment/<equipment_id>/edit` mit GET und POST Methoden"
- "Die GET-Methode soll ein Formular mit den aktuellen Equipment-Daten anzeigen"
- "Die POST-Methode soll die `update_equipment()` Methode vom EquipmentManager aufrufen"
- "Nach erfolgreichem Update soll zur Equipment-Detail-Seite weitergeleitet werden"

### Implementierung

1. Öffnen Sie `routes/web.py`
2. Fügen Sie die neue Route nach der `equipment_detail()` Funktion hinzu
3. Verwenden Sie `equipment_manager.update_equipment()` für die Aktualisierung
4. Behandeln Sie Fehler und zeigen Sie Erfolgsmeldungen an

### Beispiel-Struktur

```python
@web_bp.route('/equipment/<equipment_id>/edit', methods=['GET', 'POST'])
def equipment_edit(equipment_id: str):
    """
    Equipment bearbeiten
    
    GET /equipment/<id>/edit - Zeigt Bearbeitungsformular
    POST /equipment/<id>/edit - Verarbeitet Aktualisierung
    """
    if request.method == 'POST':
        # TODO: Form-Daten holen
        # TODO: equipment_manager.update_equipment() aufrufen
        # TODO: Bei Erfolg zu equipment_detail weiterleiten
        # TODO: Bei Fehler Fehlermeldung anzeigen
        pass
    
    # GET: Aktuelles Equipment laden und Formular anzeigen
    # TODO: equipment_manager.get_equipment_status() aufrufen
    # TODO: Template mit Equipment-Daten rendern
    pass
```

### Überprüfung

Testen Sie die Route manuell:
1. Starten Sie die Anwendung
2. Navigieren Sie zu einem Equipment (z.B. http://localhost:5000/equipment/PUMPE-001)
3. Fügen Sie `/edit` zur URL hinzu
4. Ändern Sie Daten und speichern Sie

</details>

<details>
<summary><strong>Task 2.3: Equipment-Edit-Template erstellen</strong></summary>

### Aufgabe

Erstellen Sie ein HTML-Template für die Equipment-Bearbeitung.

**Fragen Sie Ihren AI-Assistenten**:
- "Erstelle ein Template `templates/equipment_edit.html` basierend auf `equipment_form.html`"
- "Das Formular soll die aktuellen Equipment-Werte vorausfüllen"
- "Füge einen 'Abbrechen'-Button hinzu, der zurück zur Detail-Seite führt"

### Implementierung

1. Erstellen Sie `templates/equipment_edit.html`
2. Kopieren Sie die Struktur von `equipment_form.html`
3. Ändern Sie das Formular:
   - Equipment-ID sollte **nicht editierbar** sein (readonly oder hidden)
   - Alle anderen Felder sollten mit aktuellen Werten vorausgefüllt sein
   - Formular-Action sollte zur Edit-Route zeigen
4. Fügen Sie Buttons hinzu:
   - "Speichern" (submit)
   - "Abbrechen" (Link zurück zur Detail-Seite)

### Beispiel-Formular

```html
<form method="POST" action="{{ url_for('web.equipment_edit', equipment_id=equipment.equipment_id) }}">
    <input type="hidden" name="equipment_id" value="{{ equipment.equipment_id }}">
    
    <label>Name:</label>
    <input type="text" name="name" value="{{ equipment.name }}" required>
    
    <label>Typ:</label>
    <select name="type" required>
        <option value="pump" {% if equipment.type == 'pump' %}selected{% endif %}>Pumpe</option>
        <!-- weitere Optionen -->
    </select>
    
    <!-- weitere Felder -->
    
    <button type="submit">Speichern</button>
    <a href="{{ url_for('web.equipment_detail', equipment_id=equipment.equipment_id) }}">Abbrechen</a>
</form>
```

</details>

<details>
<summary><strong>Task 2.4: Equipment-Delete-Route implementieren</strong></summary>

### Aufgabe

Erstellen Sie eine Route zum Löschen von Equipment.

**Fragen Sie Ihren AI-Assistenten**:
- "Erstelle eine Route `/equipment/<equipment_id>/delete` mit POST Methode"
- "Die Route soll `delete_equipment()` vom EquipmentManager aufrufen"
- "Nach erfolgreichem Löschen soll zum Dashboard weitergeleitet werden"
- "Füge eine Sicherheitsabfrage hinzu, um versehentliches Löschen zu verhindern"

### Implementierung

1. Öffnen Sie `routes/web.py`
2. Fügen Sie die Delete-Route hinzu
3. Verwenden Sie `equipment_manager.delete_equipment()`
4. Leiten Sie nach erfolgreichem Löschen zum Dashboard weiter

### Beispiel-Struktur

```python
@web_bp.route('/equipment/<equipment_id>/delete', methods=['POST'])
def equipment_delete(equipment_id: str):
    """
    Equipment löschen
    
    POST /equipment/<id>/delete
    """
    try:
        # TODO: equipment_manager.delete_equipment() aufrufen
        # TODO: Bei Erfolg zum Dashboard weiterleiten
        # TODO: Bei Fehler Fehlermeldung anzeigen
        pass
    except Exception as e:
        # TODO: Fehlerbehandlung
        pass
```

⚠️ **ACHTUNG**: Löschen ist eine destruktive Operation! Stellen Sie sicher, dass Benutzer bestätigen müssen, bevor Equipment gelöscht wird.

</details>

<details>
<summary><strong>Task 2.5: UI-Buttons zur Equipment-Detail-Seite hinzufügen</strong></summary>

### Aufgabe

Fügen Sie "Bearbeiten" und "Löschen" Buttons zur Equipment-Detail-Seite hinzu.

**Fragen Sie Ihren AI-Assistenten**:
- "Öffne `templates/equipment_detail.html`"
- "Füge einen 'Bearbeiten'-Button hinzu, der zur Edit-Route führt"
- "Füge einen 'Löschen'-Button mit JavaScript-Bestätigung hinzu"

### Implementierung

1. Öffnen Sie `templates/equipment_detail.html`
2. Finden Sie einen geeigneten Platz für die Buttons (z.B. neben dem Equipment-Namen)
3. Fügen Sie die Buttons hinzu:

```html
<div class="equipment-actions">
    <a href="{{ url_for('web.equipment_edit', equipment_id=equipment.equipment_id) }}" 
       class="btn btn-primary">
        Bearbeiten
    </a>
    
    <form method="POST" 
          action="{{ url_for('web.equipment_delete', equipment_id=equipment.equipment_id) }}"
          style="display: inline;"
          onsubmit="return confirm('Möchten Sie dieses Equipment wirklich löschen?');">
        <button type="submit" class="btn btn-danger">Löschen</button>
    </form>
</div>
```

### Überprüfung

1. Öffnen Sie eine Equipment-Detail-Seite
2. Überprüfen Sie, dass beide Buttons sichtbar sind
3. Testen Sie den "Bearbeiten"-Button
4. Testen Sie den "Löschen"-Button (mit Bestätigung)

</details>

<details>
<summary><strong>Task 2.6: End-to-End Test durchführen</strong></summary>

### Aufgabe

Testen Sie den kompletten Equipment-Management-Workflow.

**Test-Szenario**:
1. Öffnen Sie das Dashboard
2. Wählen Sie ein Equipment aus
3. Klicken Sie auf "Bearbeiten"
4. Ändern Sie den Namen und Standort
5. Speichern Sie die Änderungen
6. Überprüfen Sie, dass die Änderungen auf der Detail-Seite sichtbar sind
7. Klicken Sie auf "Löschen"
8. Bestätigen Sie die Löschung
9. Überprüfen Sie, dass das Equipment nicht mehr im Dashboard erscheint

### Erwartetes Ergebnis

✅ Equipment kann erfolgreich bearbeitet werden  
✅ Änderungen werden in der Datenbank gespeichert  
✅ Equipment kann gelöscht werden  
✅ Gelöschtes Equipment erscheint nicht mehr in der Liste  
✅ Fehlermeldungen werden korrekt angezeigt  

💡 **Tipp**: Nutzen Sie die Browser-Entwicklertools (F12), um Netzwerk-Requests und eventuelle JavaScript-Fehler zu überprüfen.

</details>

---

## Phase 3: Code-Review und Sicherheitsanalyse (30 Minuten)

> [!NOTE]
> **Lernziel**: Nutzen Sie AI-Tools (Q Developer, Kiro, Copilot), um Sicherheitslücken in bestehendem Code zu identifizieren.

<details>
<summary><strong>Task 3.1: Codebase-Analyse</strong></summary>

### Aufgabe

Nutzen Sie Ihren AI-Assistenten für eine erste Sicherheitsanalyse der Codebasis.

**Fragen Sie Ihren AI-Assistenten**:
- "Analysiere die Datei `repositories/equipment.py` auf Sicherheitsprobleme"
- "Überprüfe `config.py` auf Sicherheitsrisiken"
- "Untersuche `routes/api.py` auf fehlende Sicherheitsmaßnahmen"

**Ihre Aufgabe**: Lassen Sie den AI-Assistenten die Dateien analysieren und dokumentieren Sie die gefundenen Probleme.

<details>
<summary>💡 <strong>Hinweis: Erwartete Sicherheitsprobleme</strong> (klicken zum Anzeigen)</summary>

<br>

Der AI-Assistent sollte mindestens diese Probleme identifizieren:
1. **SQL-Injection** in der `search()` Methode
2. **Hardcodierte Secrets** in der Konfiguration
3. **Fehlende Authentifizierung** bei sensiblen API-Endpunkten

📄 **Detaillierte Hinweise**: Öffnen Sie `SECURITY_ISSUES.md` für ausführliche Erklärungen zu den Schwachstellen.

</details>

</details>

<details>
<summary><strong>Task 3.2: Sicherheitsproblem in Equipment-Repository beheben</strong></summary>

### Aufgabe

⚠️ **Problem**: Die `search()` Methode in `repositories/equipment.py` hat eine Sicherheitslücke.

**Fragen Sie Ihren AI-Assistenten**:
- "Wie behebe ich die Sicherheitslücke in der search() Methode?"
- "Zeige mir, wie ich parametrisierte Queries verwende"
- "Was ist das Problem mit String-Konkatenation in SQL-Queries?"

### Implementierung

1. Öffnen Sie `repositories/equipment.py`
2. Finden Sie die `search()` Methode
3. Ersetzen Sie String-Konkatenation durch parametrisierte Queries
4. Testen Sie die Änderung

### Überprüfung

```bash
# Dieser Test sollte weiterhin funktionieren
pytest test_equipment_properties.py -v
```

> [!CAUTION]
> **Vorher** (unsicher):
> ```python
> sql = f"SELECT * FROM equipment WHERE name LIKE '%{query}%'"
> ```

> [!TIP]
> **Nachher** (sicher):
> ```python
> sql = "SELECT * FROM equipment WHERE name LIKE ?"
> params = (f'%{query}%',)
> ```

</details>

<details>
<summary><strong>Task 3.3: Konfigurationssicherheit verbessern</strong></summary>

### Aufgabe

⚠️ **Problem**: `config.py` enthält sensible Daten, die nicht im Code stehen sollten.

**Fragen Sie Ihren AI-Assistenten**:
- "Analysiere config.py - welche Daten sollten nicht im Code stehen?"
- "Wie verschiebe ich sensible Konfigurationsdaten in Umgebungsvariablen?"
- "Zeige mir, wie ich python-dotenv verwende"

### Implementierung

> [!IMPORTANT]
> Erstellen Sie eine `.env` Datei und fügen Sie sie zu `.gitignore` hinzu!

1. Erstellen Sie eine `.env` Datei
2. Verschieben Sie Secrets aus `config.py` in die `.env` Datei
3. Laden Sie Secrets aus Umgebungsvariablen

### Überprüfung

```bash
grep -r "hardcoded-secret" .  # Sollte nichts finden
```

</details>

---

## Phase 4: Performance-Optimierung (45 Minuten)

> [!NOTE]
> **Lernziel**: Identifizieren und beheben Sie Performance-Engpässe mit AI-Unterstützung (Q Developer, Kiro, Copilot).


<details>
<summary><strong>Task 2.1: N+1 Query Problem identifizieren</strong></summary>

### Aufgabe

**Problem**: Das Dashboard lädt Sensordaten ineffizient.

**Fragen Sie Ihren AI-Assistenten**:
- "Analysiere `repositories/sensor_data.py` auf N+1 Query Probleme"
- "Wie kann ich die `get_latest_readings()` Methode optimieren?"

### Analyse

1. Öffnen Sie `repositories/sensor_data.py`
2. Untersuchen Sie die `get_latest_readings()` Methode
3. Zählen Sie, wie viele Datenbankabfragen für 10 Anlagen ausgeführt werden

### Erwartetes Ergebnis

Sie sollten feststellen: Bei 10 Anlagen werden 11 Queries ausgeführt (1 + 10).

> [!IMPORTANT]
> Siehe `PERFORMANCE_ISSUES.md` für detaillierte Erklärungen.

</details>

<details>
<summary><strong>Task 2.2: N+1 Query Problem beheben</strong></summary>

### Aufgabe

**Fragen Sie Ihren AI-Assistenten**:
- "Schreibe die Methode um, um alle Daten mit einem JOIN zu laden"
- "Zeige mir, wie ich Window Functions in SQLite verwende"

### Implementierung

1. Ersetzen Sie die Schleife durch eine einzelne SQL-Abfrage mit JOIN
2. Verwenden Sie `ROW_NUMBER()` Window Function für die neuesten Messwerte
3. Testen Sie die Performance-Verbesserung

### Überprüfung

```python
# Messen Sie die Ausführungszeit
import time
start = time.time()
readings = sensor_repo.get_latest_readings()
print(f"Zeit: {time.time() - start:.3f}s")
```

**Erwartete Verbesserung**: 5-10x schneller!

</details>

<details>
<summary><strong>Task 2.3: Datenbank-Indizes hinzufügen</strong></summary>

### Aufgabe

**Problem**: Die `sensor_readings` Tabelle hat keine Indizes auf häufig abgefragten Spalten.

**Fragen Sie Ihren AI-Assistenten**:
- "Welche Indizes sollte ich für die sensor_readings Tabelle erstellen?"
- "Wie analysiere ich Query-Performance in SQLite?"

### Implementierung

1. Öffnen Sie `schema.sql`
2. Fügen Sie Indizes für `equipment_id` und `timestamp` hinzu
3. Erstellen Sie einen zusammengesetzten Index für beide Spalten

### SQL-Befehle

```sql
CREATE INDEX idx_sensor_readings_equipment ON sensor_readings(equipment_id);
CREATE INDEX idx_sensor_readings_timestamp ON sensor_readings(timestamp DESC);
CREATE INDEX idx_sensor_readings_equipment_timestamp ON sensor_readings(equipment_id, timestamp DESC);
```

### Überprüfung

```sql
EXPLAIN QUERY PLAN
SELECT * FROM sensor_readings 
WHERE equipment_id = 'PUMPE-001' 
ORDER BY timestamp DESC 
LIMIT 10;
```

Sollte jetzt "SEARCH ... USING INDEX" anzeigen statt "SCAN".

</details>

<details>
<summary><strong>Task 2.4: Ineffiziente Statistik-Berechnung optimieren</strong></summary>

### Aufgabe

**Problem**: `services/sensor_processor.py` berechnet Statistiken in mehreren Durchläufen.

**Fragen Sie Ihren AI-Assistenten**:
- "Optimiere diese Statistik-Berechnung auf einen einzigen Durchlauf"
- "Wie berechne ich Min, Max, Durchschnitt und Standardabweichung effizient?"

### Implementierung

1. Öffnen Sie `services/sensor_processor.py`
2. Finden Sie die `calculate_statistics()` Methode
3. Kombinieren Sie alle Berechnungen in einer Schleife

### Erwartetes Ergebnis

**Vorher**: 5 Durchläufe über die Daten  
**Nachher**: 1 Durchlauf über die Daten  
**Speedup**: 5-6x schneller

</details>

---

## Phase 5: Property-Based Testing (45 Minuten)

> [!NOTE]
> **Lernziel**: Verstehen und erweitern Sie Property-Based Tests mit Hypothesis und AI-Unterstützung (Q Developer, Kiro, Copilot).

<details>
<summary><strong>Task 3.1: Property-Based Testing verstehen</strong></summary>

### Aufgabe

**Fragen Sie Ihren AI-Assistenten**:
- "Was ist Property-Based Testing und wie unterscheidet es sich von Unit-Tests?"
- "Erkläre mir, wie Hypothesis funktioniert"
- "Zeige mir Beispiele für gute Properties in diesem Projekt"

### Analyse

1. Öffnen Sie `test_equipment_properties.py`
2. Untersuchen Sie die bestehenden Property-Tests
3. Verstehen Sie, wie `@given` Dekoratoren funktionieren

### Erwartetes Ergebnis

Sie verstehen:
- Properties sind universelle Regeln, die für alle Eingaben gelten
- Hypothesis generiert automatisch Testfälle
- Tests validieren Korrektheit über viele Szenarien

</details>

<details>
<summary><strong>Task 3.2: Neue Property-Tests schreiben</strong></summary>

### Aufgabe

Schreiben Sie einen neuen Property-Test für die Alarmgenerierung.

**Fragen Sie Ihren AI-Assistenten**:
- "Schreibe einen Property-Test, der prüft, dass Alarme bei Schwellwertüberschreitung generiert werden"
- "Wie erstelle ich einen Hypothesis-Generator für Sensordaten?"

### Implementierung

Erstellen Sie einen Test in `test_alert_properties.py`:

```python
from hypothesis import given, strategies as st

@given(
    sensor_value=st.floats(min_value=0, max_value=200),
    threshold=st.floats(min_value=50, max_value=100)
)
def test_threshold_alert_generation(sensor_value, threshold):
    # Property: Wenn Wert > Schwellwert, dann Alarm
    if sensor_value > threshold:
        alert = generate_alert(sensor_value, threshold)
        assert alert is not None
    else:
        alert = generate_alert(sensor_value, threshold)
        assert alert is None
```

### Überprüfung

```bash
pytest test_alert_properties.py -v
```

</details>

<details>
<summary><strong>Task 3.3: Round-Trip Property testen</strong></summary>

### Aufgabe

Round-Trip Properties sind besonders wertvoll für Serialisierung/Deserialisierung.

**Fragen Sie Ihren AI-Assistenten**:
- "Schreibe einen Round-Trip Test für Equipment-Daten"
- "Was ist ein Round-Trip Property und warum ist es wichtig?"

### Konzept

```python
# Property: Speichern → Laden → Sollte identisch sein
@given(equipment=equipment_strategy())
def test_equipment_roundtrip(equipment):
    # Speichern
    repo.create(equipment)
    
    # Laden
    loaded = repo.get_by_id(equipment['equipment_id'])
    
    # Vergleichen
    assert loaded['name'] == equipment['name']
    assert loaded['type'] == equipment['type']
```

</details>

---

## Phase 6: Containerisierung (30 Minuten)

> [!NOTE]
> **Lernziel**: Containerisieren Sie die Anwendung für moderne Deployment-Praktiken mit AI-Unterstützung (Q Developer, Kiro, Copilot).

<details>
<summary><strong>Task 4.1: Dockerfile erstellen</strong></summary>

### Aufgabe

**Fragen Sie Ihren AI-Assistenten**:
- "Erstelle ein Dockerfile für diese Flask-Anwendung"
- "Was sind Best Practices für Python-Container?"

### Implementierung

Erstellen Sie `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
```

### Überprüfung

```bash
docker build -t industrial-monitoring .
docker run -p 5000:5000 industrial-monitoring
```

</details>

<details>
<summary><strong>Task 4.2: Docker Compose konfigurieren</strong></summary>

### Aufgabe

**Fragen Sie Ihren AI-Assistenten**:
- "Erstelle eine docker-compose.yml für diese Anwendung"
- "Wie konfiguriere ich Volume-Mounts für die Datenbank?"

### Implementierung

Erstellen Sie `docker-compose.yml`:

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./industrial_monitoring.db:/app/industrial_monitoring.db
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_PATH=/app/industrial_monitoring.db
```

### Überprüfung

```bash
docker-compose up
```

</details>

<details>
<summary><strong>Task 4.3: .dockerignore erstellen</strong></summary>

### Aufgabe

**Fragen Sie Ihren AI-Assistenten**:
- "Was sollte in .dockerignore für ein Python-Projekt stehen?"

### Implementierung

Erstellen Sie `.dockerignore`:

```
__pycache__
*.pyc
*.pyo
*.pyd
.Python
venv/
.venv/
.pytest_cache/
.hypothesis/
*.db
.git/
.gitignore
README.md
```

</details>

---

## Bonus-Aufgaben (Optional)

<details>
<summary><strong>Bonus 1: API-Paginierung implementieren</strong></summary>

### Aufgabe

Fügen Sie Paginierung zu den Sensor-Endpunkten hinzu.

**Fragen Sie Ihren AI-Assistenten**:
- "Implementiere Paginierung für den /api/sensors/readings Endpunkt"
- "Was sind Best Practices für REST API Paginierung?"

### Erwartetes Ergebnis

```bash
curl "http://localhost:5000/api/sensors/readings?page=1&per_page=50"
```

Sollte paginierte Ergebnisse mit Metadaten zurückgeben.

</details>

<details>
<summary><strong>Bonus 2: Passwort-Hashing implementieren</strong></summary>

### Aufgabe

Ersetzen Sie Klartext-Passwörter durch gehashte Passwörter.

**Fragen Sie Ihren AI-Assistenten**:
- "Implementiere sicheres Passwort-Hashing mit werkzeug.security"
- "Wie migriere ich bestehende Klartext-Passwörter?"

### Implementierung

Verwenden Sie `werkzeug.security`:
- `generate_password_hash()` beim Erstellen
- `check_password_hash()` beim Authentifizieren

</details>

<details>
<summary><strong>Bonus 3: Token-Expiration hinzufügen</strong></summary>

### Aufgabe

Implementieren Sie Token-Ablauf für Authentifizierung.

**Fragen Sie Ihren AI-Assistenten**:
- "Implementiere JWT-Tokens mit Ablaufzeit"
- "Wie validiere ich abgelaufene Tokens?"

</details>

---

## Zusammenfassung und Reflexion

### Was Sie gelernt haben

✅ **Sicherheit**:
- SQL-Injection-Schwachstellen identifizieren und beheben
- Secrets aus Code in Umgebungsvariablen verschieben
- Authentifizierung für sensible Endpunkte implementieren

✅ **Performance**:
- N+1 Query Probleme erkennen und lösen
- Datenbank-Indizes strategisch einsetzen
- Algorithmen für Single-Pass-Verarbeitung optimieren

✅ **Testing**:
- Property-Based Testing mit Hypothesis verstehen
- Universelle Properties definieren und testen
- Round-Trip Properties für Datenintegrität nutzen

✅ **DevOps**:
- Anwendungen containerisieren mit Docker
- Multi-Container-Setups mit Docker Compose
- Best Practices für Container-Images

### Diskussionsfragen

1. **Wie hat AI-Unterstützung Ihren Entwicklungsprozess verändert?**
2. **Welche Sicherheitsprobleme waren am schwierigsten zu finden?**
3. **Wie würden Sie Property-Based Testing in Ihren Projekten einsetzen?**
4. **Was sind die nächsten Schritte für Production-Deployment?**

---

## Ressourcen

### Dokumentation
- `README.md` - Projektübersicht und API-Dokumentation
- `SECURITY_ISSUES.md` - Detaillierte Sicherheitsprobleme und Lösungen
- `PERFORMANCE_ISSUES.md` - Performance-Optimierungen mit Beispielen

### Weiterführende Links
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/3.0.x/security/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

## Nächste Schritte

Nach dem Workshop können Sie:

1. **Weitere Sicherheitsprobleme beheben** (siehe SECURITY_ISSUES.md)
2. **Zusätzliche Performance-Optimierungen** implementieren
3. **Test-Coverage erweitern** mit mehr Property-Tests
4. **CI/CD Pipeline** einrichten für automatisierte Tests
5. **Monitoring und Logging** hinzufügen für Production

**Viel Erfolg beim Workshop! 🚀**
