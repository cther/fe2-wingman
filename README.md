# FE2 Wingman
Das Ziel dieses Projektes ist es, den bestehenden Funktionsumfang der Alarmplattform [FE2](https://alamos.gmbh/loesungen/alarmplattform) der Alamos GmbH zu erweitern. Motiviert durch den Wunsch nach zusätzlichen Möglichkeiten der automatisierten Benachrichtigung, im Zusammenhang mit [Verkehrsbehinderungen](https://alamos-support.atlassian.net/wiki/spaces/documentation/pages/219480778/Verkehrsbehinderungen#Dokumente-anh%C3%A4ngen-FE2-2.38), entstand der *FE2 Wingman*.

Es besteht darüber hinaus die Möglichkeit, differenziert auf Statusübergänge von Fahrzeugen zu reagieren. Hierzu wird sowohl der aktuelle, als auch der vorherige Status bereitgestellt. Dadurch ist es nun zum Beispiel möglich nur dann ein Ereignis auslösen (eine Nachricht zu verschicken), wenn ein Fahrzeug den Status 6 wieder verlässt.

Der FE2 Wingman greift rein lesend auf die zum FE2 System gehörende Datenbank zu und reagiert auf inhaltliche Veränderungen. Alle übrigen Interaktionen mit dem FE2 Server erfolgen über die öffentliche API, in Form von regulären Alarmierungen. Innerhalb von FE2 kann in gewohnter Art und Weise auf die Alarmierung reagiert werden ([Übersicht Alarmparameter](#alarmparameter))

Enthaltenden Funktionen:
* Möglichkeit der Benachrichtigung bei neu erstellten/geänderten, anstehenden oder auslaufenden Verkehrsbehinderungen
* Fahrzeugstatusmeldung mit zusätzlichen Parametern

## Vorbereitung FE2
Zur Anbindung des Wingman an den FE2 Server wird empfohlen eine separate Schnittstelle anzulegen: 
1. Alarmeingang [Externe Schnittstelle](https://alamos-support.atlassian.net/wiki/spaces/documentation/pages/219480366/Externe+Schnittstelle) hinzufügen
2. Einstellung -> Version Datenformat: v2
3. Einstellung -> Gültigen Absender festlegen (sollte eine möglichst zufällige Zeichenkette sein!)
4. HTTP -> HTTP POST aktivieren
5. Alarmierung -> Es bestehen zwei Optionen:
  - Standard-Einheit festlegen
  - Alternativ kann der FE2 Wingman direkt eine beliebige Einheit (in Abhängigkeit der Organisation) per [Einheitenkennung](#einheitenkennung) alarmieren. In diesem Fall wird hier keine Standard-Einheit festgelegt.
6. Speichern und schließen

## Installation 
Das Prozedere zur Installation variiert etwas zwischen den Plattformen:
- [Linux/Docker](#installation-unter-docker)
- [Windows](#installation-unter-windows)

----
### Installation unter Docker
Es müssen folgende Voraussetzungen für die Installation erfüllt sein:
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
    volumes:
      - ./wingman/src:/usr/src/myapp
    command:
      sh -c "pip install --no-cache-dir -r /usr/src/myapp/requirements.txt && python -u /usr/src/myapp/main.py"
    environment:
      TZ: "Europe/Berlin"
```
4. Konfigurationsdatei aus Template im Unterverzeichnis `src` anlegen
```
cp config.ini.template src/config.ini
```
5. Die Namen des Datenbank Containers und des FE2 Containers anpassen. Die Werte der Parameter `container_name` müssen in die Konfigurationsdatei `src/config.ini` des Wingman übernommen werden
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
[server]
db_url:                  mongodb://fe2_database:27017
fe2_url:                 http://fe2_app:83
```
6. Übrigen Parameter in der Konfigurationsdatei anpassen (siehe Abschnitt [FE2 Wingman Konfigurationsdatei](#fe2-wingman-konfigurationsdatei)).
7. Damit ist die Installation abgeschlossen und das System kann hochgefahren werden
```
docker compose up -d
```


----
### Installation unter Windows
Grundsätzlich müssen folgende Voraussetzungen für die Installation erfüllt sein:
* Lauffähige FE2 Instanz
* Installierte [Python 3](https://www.python.org/downloads/) Umgebung (Version 3.10 oder neuer)

### Wingman mit FE2 verbinden
Die folgenden Schritte beschreiben die Integration des FE2 Wingman in ein bestehendes Windows Setup:

1. Release `fe2-wingman-vXXX.zip` auf den FE2 Server kopieren und an einem beliebigen Ort in das Verzeichnis `FE2 Wingman` entpacken
2. Konfigurationsdatei aus Template im Unterverzeichnis `src` anlegen
```
copy config.ini.template src/config.ini
```
3. In der Konfigurationsdatei `src/config.ini` zunächst die Parameter für die Serveradressen anpassen. Im Link zur Datenbank `db_url` muss lediglich der Datanbankbenutzer `user` und das Passwort `pass` ersetzt werden. Als Datanbankbenutzer ist `Admin` einzusetzen. Das einzusetzende Passwort findet sich unter dem Schlüssel `dbpassword` in der Windows Registry: `HKEY_LOCAL_MACHINE\SOFTWARE\JavaSoft\Prefs\de.alamos.fe2.server.services./Registry/Service`.  
```
[server]
db_url:                  mongodb://user:pass@localhost:27018
fe2_url:                 http://localhost:83
```
4. Die übrigen Parameter in der Konfigurationsdatei anpassen (siehe Abschnitt [FE2 Wingman Konfigurationsdatei](#fe2-wingman-konfigurationsdatei)).
5. Die Einrichtung ist damit abgeschlossen und der FE2 Wingman kann mit Hilfe der folgenden Batchskripte entweder als Desktopanwendung oder als Dienst gestartet/eingerichtet werden:
  - Desktopanwendung: `win_run.bat`
  - Dienst:           `win_service_installer.bat` (erfordert die Ausführung als Administrator)


## FE2 Wingman Konfigurationsdatei
Über die Parameter in der Konfigurationsdatei `src/config.ini` lassen sich verschiedene Optionen einstellen:

1. Die Server Adressen sind entsprechend der verwendeten Plattform ([Docker](#installation-unter-docker) oder [Windows](#installation-unter-windows)) zu setzten 
```
[server]
db_url:                  mongodb://...
fe2_url:                 https://...
```
2. Passwort (Gültiger Absender) aus der Konfiguration der [externen Schnittstelle](#vorbereitung-fe2) eintragen
```
fe2_secret:              seCret12357#
```
3. Über die folgenden Optionen wird festgelegt, bei welchen Ereignissen Benachrichtigungen verschickt werden sollen
 - `new` bei Erstellung oder nach Anpassung einer Behinderung
 - `upcoming` bei in Kraft treten
 - `expiring` bei Aufhebung
```
[opt_roadblock]
roadblock_get_new:       false
roadblock_get_upcoming:  false
roadblock_get_expiring:  false
```
4. Erst wenn diese Option aktiviert ist, erfolgt eine Benachrichtigung bei einem Wechsel eines Fahrzeugstatus
```
[opt_vehiclestate]
vehiclestate_enable:     false
```
5. Der Versand von Meldungen für den Status `C`, `0` und `5` lässt sich bei Bedarf unterdrücken
```
vehiclestate_skip_c:     false
vehiclestate_skip_0:     false
vehiclestate_skip_5:     false
```
6. Ist die folgende Option aktiviert, wird für jede Organisation die festgelegte Einheit (Abschnitt `[orga_units]`) alarmiert. Andernfalls wird auf die, im Alarmeingang festgelegte, Standarteinheit zurückgegriffen. Nähere Informationen hierzu finden sich im Abschnitt [Einheitenkennung](#einheitenkennung)  
```
[opt_orga_units]
orga_units_enable:       false
```

### Einheitenkennung
Wird für die Verarbeitung eine Standardeinheit verwendet, kann dieser Abschnitt übersprungen werden.

Anderenfalls kann für jede Organisation eine zu alarmierende Einheit, per Einheitenkennung, festgelegt werden. Diese gilt sowohl für Verkehrsbehinderungen, als auch die Änderung eines Fahrzeugstatus.

Für jede Organisation muss eine Kennung (uid) im Abschnitt `[orga_units]` in die Konfigurationsdatei eintragen werden
```
[orga_units]
#orga                    uid
Example:                 1234567890abcdefghijklmompqrstu
```
> [!WARNING]
> Organisationen, für die keine Einheitenkennung hinterlegt ist, werden nicht alarmiert!


## Alarmparameter
### Verkehrsbehinderung
 Der übertragene Alarm zu einer Verkehrsbehinderung enthält folgende Parameter:
| Parameter | Beschreibung |
| --------- | ------------ |
| `sender` | Konstante Zeichenkette mit Versionsnummer `FE2 Wingman vX.X.X`  |
| `city` | Ortsnamen |
| `street` | Straßenname |
| `lat` & `lng` | Bei einem gezeichneten Streckenabschnitt wird der Mittelpunkt angegeben, andernfalls der ausgewählte Punkt |
| `keyword` | Meldungsüberschrift |
| `message` | Vorgefertigter Meldungstext |
| `wm_function` | Konstante Zeichenkette `roadblock`|
| `wm_rb_name` | Name der Verkehrsbehinderung |
| `wm_rb_state` | Bearbeitungsstand (`NEW`, `UPDATE`, `STEADY`) |
| `wm_rb_type` | Art der Behinderung (Baustelle: `ROAD_WORKS`, Sperrung: `ROAD_CLOSED`, Behinderung: `INCIDENT`) |
| `wm_rb_status` | Status der Behinderung (`PENDING`, `ACTIVE`, `EXPIRED`) |
| `wm_rb_orga` | Name der anlegenden Organisation |
| `wm_rb_start` | Startzeitpunkt (Format `dd.mm.yyyy hh:mm`) |
| `wm_rb_end` | Endzeitpunkt (Format `dd.mm.yyyy hh:mm`) |
| `wm_rb_icon` | Konstantes Icon |

### Fahrzeugstatus
Der Alarm zu einer Änderung eines Fahrzeugstatus enthält folgende Parameter:
| Parameter | Beschreibung |
| --------- | ------------ |
| `sender` | Konstante Zeichenkette mit Versionsnummer `FE2 Wingman vX.X.X`  |
| `keyword` | Statusbeschreibung mit Icon |
| `message` | Vorgefertigter Meldungstext |
| `wm_function` | Konstante Zeichenkette `vehiclestate`|
| `wm_vs_address` | Einsatzmittelkennung |
| `wm_vs_name` | Fahrzeugname |
| `wm_vs_short_name` | Kurzname |
| `wm_vs_orga` | Liste der zugeordneten Organisationen |
| `wm_vs_source` | Statusquelle |
| `wm_vs_state_from` | Bisheriger Fahrzeugstatus |
| `wm_vs_state_to` | Aktualisierter Fahrzeugstatus |
| `wm_vs_definition` | Statusbeschreibung |
| `wm_vs_icon` | Konstantes Icon |