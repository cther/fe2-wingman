# FE2 Wingman
Das Ziel dieses Projektes ist es, den bestehenden Funktionsumfang der Alarmplattform [FE2](https://alamos.gmbh/loesungen/alarmplattform) der Alamos GmbH zu erweitern. Motiviert durch den Wunsch nach zusätzlichen Möglichkeiten der automatisierten Benachrichtigung, im Zusammenhang mit [Verkehrsbehinderungen](https://alamos-support.atlassian.net/wiki/spaces/documentation/pages/219480778/Verkehrsbehinderungen#Dokumente-anh%C3%A4ngen-FE2-2.38), entstand der FE2 Wingman.

Der FE2 Wingman greift rein lesend auf die zum FE2 System gehörende Datenbank zu und reagiert auf inhaltliche Veränderungen. Alle übrigen Interaktionen mit dem FE2 Server erfolgen über die öffentliche API, in Form von regulären Alarmierungen. Innerhalb von FE2 kann in gewohnter Art und Weise auf die Alarmierung reagiert werden ([Übersicht Alarmparameter](#alarmparameter))

Enthaltenden Funktionen:
* Möglichkeit der Benachrichtigung bei neu erstellten/geänderten, anstehenden oder auslaufenden Verkehrsbehinderungen

## Vorbereitung FE2
Zur Anbindung des Wingman an den FE2 Server sind folgende Voraussetzungen zu schaffen.

### Alarmeingang
1. Alarmeingang [Externe Schnittstelle](https://alamos-support.atlassian.net/wiki/spaces/documentation/pages/219480366/Externe+Schnittstelle) hinzufügen
2. Einstellung -> Version Datenformat: v2
3. Einstellung -> Gültigen Absender festlegen (sollte eine möglichst zufällige Zeichenkette sein!)
4. HTTP -> HTTP POST aktivieren
5. Alarmierung -> Es bestehen zwei Optionen:
  - Standard-Einheit festlegen
  - Alternativ kann der FE2 Wingman direkt eine beliebige Einheit (in Abhängigkeit der Organisation) per [Einheitenkennung](#einheitenkennung) alarmieren. In diesem Fall wird hier keine Standard-Einheit festgelegt.
6. Speichern und schließen

### Einheitenkennung
Wird für die Verarbeitung eine Standardeinheit verwendet, kann dieser Abschnitt übersprungen werden.

Für jede Organisation kann eine zu alarmierende Einheit, per Einheitenkennung, festgelegt werden:

1. Template kopieren
```
cp unit_ids.ini.template data/unit_ids.ini
```
2. Für jede Organisation eine Kennung (uid) eintragen
```
[orga_units]
#orga       uid
Example:    1234567890abcdefghijklmompqrstuvwxyz
```
> [!WARNING]
> Organisationen, für die keine Einheitenkennung hinterlegt ist, werden nicht alarmiert!

## Installation Docker
Grundsätzlich müssen folgende Voraussetzungen für die Installation erfüllt sein:
* Lauffähige [Dockerumgebung](https://docs.docker.com/get-started/get-docker/)
* Docker [Compose](https://getcomposer.org/download/)
* Lauffähige [FE2 Docker](https://github.com/alamos-gmbh/fe2-docker) Instanz

### Wingman an FE2 anbinden
Die folgenden Schritte beschreiben die Integration des FE2 Wingman in ein bestehendes FE2 Docker Setup:

1. Release `fe2-wingman-vXXX.zip` auf den Server kopieren und im Verzeichnis des FE2 Containers, in den Ordner `wingman`, entpacken 
```
tar -xzf fe2-wingman--vXXX.zip wignman
```
2. Container herunterfahren
```
docker compose down
```
3. Den folgenden Block am Ende der Datei `docker-compose.yml` einfügen
```
  fe2_wingman:
    container_name: fe2_wingman
    image: python:3.13-alpine
    restart: unless-stopped
    depends_on:
      - fe2_database
    volumes:
      - ./wingman/data:/usr/src/myapp
    command:
      sh -c "pip install --no-cache-dir -r /usr/src/myapp/requirements.txt && python -u /usr/src/myapp/main.py"
    environment:
      TZ: "Europe/Berlin"
      WM_CONFIG_DB_URL: mongodb://fe2_database:27017
      WM_CONFIG_FE2_URL: http://fe2_app:83
      WM_CONFIG_FE2_SECRET: seCret12357#
      WM_CONFIG_FE2_USE_UNIT_IDS: false
      WM_OPTION_ROADBLOCK_ENABLE: true
      WM_OPTION_ROADBLOCK_NEW: false
      WM_OPTION_ROADBLOCK_UPCOMING: true
      WM_OPTION_ROADBLOCK_EXPIRING: true
	  WM_OPTION_VEHICLE_ENABLE: true
	  WM_OPTION_VEHICLE_SKIP_C: false
	  WM_OPTION_VEHICLE_SKIP_0: false
	  WM_OPTION_VEHICLE_SKIP_5: false
```
4. Wenn erforderlich den Namen des Datenbank Containers und FE2 Containers übernehmen. Die Werte der Parameter `container_name` müssen in die Konfiguration des Wingman übernommen werden
```
fe2_database:
  ...
  container_name: fe2_database
  ...
fe2_app:
  ...
  container_name: fe2_app
  ...
```
Wingman Konfiguration:
```
depends_on:
  - fe2_database
...
    WM_CONFIG_DB_URL: mongodb://fe2_database:27017
	WM_CONFIG_FE2_URL: http://fe2_app:83
```
5. Passwort (Gültiger Absender) aus der Konfiguration der [externen Schnittstelle](#vorbereitung-fe2) eintragen
```
WM_CONFIG_FE2_SECRET: seCret12357#
```
6. Ist die folgende Option aktiviert, wird für jede Organisation die festgelegte Einheit (in der Datei `unit_ids.ini`) alarmiert. Andernfalls wird auf die, im Alarmeingang festgelegte, Standarteinheit zurückgegriffen. Nähere Informationen hierzu finden sich im Abschnitt [Einheitenkennung](#einheitenkennung)  
```
WM_CONFIG_FE2_USE_UNIT_IDS: false
```
7. Ist diese Option deaktiviert, werden __keine__ Benachrichtigungen zu Verkerhrsbehinderungen verschickt
```
WM_OPTION_ROADBLOCK_ENABLE: true
```
8. Über die folgenden Optionen wird festgelegt, bei welchen Ereignissen Benachrichtigungen verschickt werden sollen
 - `NEW` bei Erstellung oder nach Anpassung einer Behinderung
 - `UPCOMING` bei in Kraft treten
 - `EXPIRING` bei Aufhebung
```
WM_OPTION_ROADBLOCK_NEW: false
WM_OPTION_ROADBLOCK_UPCOMING: true
WM_OPTION_ROADBLOCK_EXPIRING: true
```
9. Damit ist die Installation abgeschlossen und das System kann hochgefahren werden
```
docker compose up -d
```

## Alarmparameter
 Der übertragene Alarm zu einer Verkehrsbehinderung enthält folgende Parameter:
| Parameter | Beschreibung |
| --------- | ------------ |
| `sender` | Konstante Zeichenkette mit Versionsnummer `FE2 Wingman vX.X.X`  |
| `city` | Ortsnamen |
| `street` | Straßenname |
| `lat` & `lng` | Bei einem gezeichneten Strecktenabschnitten wird der Mittelpunkt angegeben, andernfalls der ausgewälte Punkt |
| `message` | Vorgefertigter Meldungstext |
| `wm_function` | Konstante Zeichenkette `roadblock`|
| `wm_subject` | Meldungsüberschrift |
| `wm_rb_name` | Name der Verkehrsbehinderung |
| `wm_rb_state` | Bearbeitungsstand (`NEW`, `UPDATE`, `STEADY`) |
| `wm_rb_type` | Art der Behinderung (Baustelle: `ROAD_WORKS`, Sperrung: `ROAD_CLOSED`, Behinderung: `INCIDENT`) |
| `wm_rb_status` | Status der Behinderung (`PENDING`, `ACTIVE`, `EXPIRED`) |
| `wm_rb_orga` | Name der anlegenden Organisation |
| `wm_rb_start` | Startzeitpunkt (Format `dd.mm.yyyy hh:mm`) |
| `wm_rb_end` | Endzeitpunkt (Format `dd.mm.yyyy hh:mm`) |
| `wm_rb_icon` | Konstantes Icon |

