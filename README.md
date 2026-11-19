# Intelligent IoT Solutions – Monitoring & Alarm API

**Delopgave 6.2 · Teknisk MVP · REST API / Microservice**  
**Case:** Intelligent IoT Solutions A/S · **Gruppe 6**

## Projektet kort fortalt

Dette repository indeholder en teknisk MVP til **overvågning af temperaturmålinger fra IoT-enheder**. Løsningen er udviklet med udgangspunkt i domænet *Anlægsovervågning* og scenariet *Predictive Maintenance / notifikation* fra delopgave 1.

En Python-simulator efterligner en temperatursensor, som sender målinger til et Flask REST API. API'et validerer input, vurderer målingen ud fra en temperaturgrænse og gemmer målinger, domænehændelser og eventuelle alarmer i MySQL.

> **Afgrænsning:** MVP'en bruger en simpel regel (`temperatur > 80 °C`) til at opdage afvigelser. Den laver ikke machine-learning-baserede forudsigelser eller sender eksterne notifikationer.

## Funktionalitet

- Modtag sensormålinger via HTTP `POST`.
- Valider påkrævede felter og temperaturværdier.
- Registrer `Sensor Value Received` for normale målinger.
- Registrer `Anomaly Detected` og opret en alarm ved temperaturer **over 80 °C**.
- Gem data i de tre MySQL-tabeller `sensor_measurements`, `domain_events` og `alarms`.
- Hent historiske målinger og alarmer via HTTP `GET`.
- Kør API og database i separate Docker-containere med vedvarende datalagring.
- Kør seks automatiserede API-tests med `pytest`, også på GitHub Actions.
- Tilgå API'et fra en anden computer på samme lokale netværk, når netværk og firewall tillader det.

## Arkitektur


## Kom hurtigt i gang med Docker

### Forudsætninger

- Docker Desktop med Docker Compose installeret og startet.
- Git installeret.
- Adgang til dette private GitHub-repository.
- Python 3.12 til lokal sensorsimulering og pytest (Docker-delen kræver ikke lokal Python-installation).

### 1. Hent projektet

```bash
git clone https://github.com/Steinomite14/Delopgave-2.git
cd Delopgave-2
```

### 2. Opret lokale miljøvariabler

Opret en fil med navnet **`.env`** i projektets rodmappe. Til Docker Compose skal den som minimum indeholde:

```dotenv
DOCKER_ROOT_PASSWORD=vaelg_en_staerk_rod_adgangskode
DOCKER_DB_PASSWORD=vaelg_en_staerk_app_adgangskode
```

Vælg dine **egne stærke adgangskoder**. Variablerne bruges af `docker-compose.yml` til at konfigurere MySQL. Kontrollér i `docker-compose.yml`, om der er yderligere variabler, som din version af projektet kræver.

**Vigtigt:** `.env` må ikke uploades til GitHub. Den er udelukket via `.gitignore` og `.dockerignore`. Brug aldrig produktionsadgangskoder i demoen.

### 3. Start API og database

```bash
docker compose up -d --build
```

Kontrollér status:

```bash
docker compose ps
```

API'et kan derefter tilgås på:

- [Målinger – GET](http://127.0.0.1:5006/api/measurements)
- [Alarmer – GET](http://127.0.0.1:5006/api/alarms)

**Bemærk:** Disse adresser bruger den Docker-port (`5006`), der er anvendt i gruppens testopsætning. Tjek `ports:` under API-servicen i `docker-compose.yml`, hvis porten ændres.

En helt ny database vil typisk vise en tom liste (`[]`), indtil den første måling er modtaget. `database.sql` initialiserer tabellerne, når MySQL-datavolumen oprettes første gang.

## API-dokumentation

**Base URL, lokal Docker:** `http://127.0.0.1:5006`

| Metode | Endpoint | Funktion | Successtatus |
| --- | --- | --- | --- |
| `POST` | `/api/measurements` | Opret måling, evaluér threshold og registrér event/alarm | `201 Created` |
| `GET` | `/api/measurements` | Hent gemte målinger | `200 OK` |
| `GET` | `/api/alarms` | Hent gemte alarmer | `200 OK` |

### POST /api/measurements

I Postman: Vælg **POST → Body → raw → JSON**, og send følgende eksempel:

```json
{
  "sensor_id": "PUMP-01-TEMP",
  "asset_id": "PUMP-01",
  "value": 95,
  "unit": "C",
  "timestamp": "2026-11-19T10:35:00Z"
}
```

Eksempel på svar ved en temperatur over 80 °C:

```json
{
  "event": "Anomaly Detected",
  "measurement_id": 1,
  "sensor_id": "PUMP-01-TEMP",
  "status": "ALARM",
  "value": 95
}
```

Ved eksempelvis `65 °C` returnerer API'et i stedet `status: "NORMAL"` og `event: "Sensor Value Received"`.

**Beslutningsregel:** Temperaturen **80 °C** er normal; kun værdier **over 80 °C** udløser alarm.

### GET /api/measurements

Sender en liste over gemte målinger, herunder bl.a. sensor-ID, anlægs-ID, tidspunkt, temperatur, enhed og status.

### GET /api/alarms

Sender en liste over registrerede alarmer med bl.a. målings-ID, status, besked og oprettelsestidspunkt. Alarmer starter med status `OPEN`.

### Fejlsvar

| Situation | HTTP-status | Eksempel på svar |
| --- | --- | --- |
| Manglende obligatoriske felter | `400` | `{"error": "Missing fields"}` |
| Ugyldig temperaturværdi | `400` | `{"error": "Invalid value"}` |
| Databaseforbindelse fejler | `500` | `{"error": "Database error"}` |

API'et logger databasefejl med Flask-loggeren. Der er **ikke** implementeret en automatisk kø eller genforsøg af målinger, hvis databasen er utilgængelig.

## Automatisk sensorsimulering

`sensor_simulator.py` sender ti temperaturmålinger til API'et med korte intervaller. Måleserien er:

```text
62, 65, 68, 73, 79, 84, 90, 94, 76, 67 °C
```

De tre værdier **84, 90 og 94 °C** skal udløse alarmer.

Start først Docker-servicene. Kontrollér dernæst, at `API_URL` i `sensor_simulator.py` peger på:

```python
API_URL = "http://127.0.0.1:5006/api/measurements"
```

Installer om nødvendigt Requests, og start simulatoren fra projektmappen:

```powershell
py -m pip install requests
py sensor_simulator.py
```

Kontrollér derefter de gemte målinger og alarmer via GET-endpoints eller i MySQL.

## Data og persistens

MySQL bruger et navngivet Docker-volume til vedvarende lagring. Derfor kan databasen beholde sine målinger, selv om containerne genstartes.

```bash
docker compose restart
```

Efter genstart kan `GET /api/measurements` bruges til at kontrollere, at data stadig findes.

**Advarsel:** `docker compose down -v` sletter også Docker-volumes og kan derfor fjerne alle gemte demo-data.

Databaseoplysninger kan kontrolleres med en MySQL-klient, fx MySQL Workbench, eller fra databasecontaineren:

```bash
docker compose exec db mysql -u iot_app -p iot_monitoring
```

Indtast databasebrugerens adgangskode, når du bliver bedt om den. Derefter kan du eksempelvis køre:

```sql
SELECT * FROM sensor_measurements;
SELECT * FROM domain_events;
SELECT * FROM alarms;
```

## Automatiserede tests

Seks tests er implementeret i `Tests/test_api.py`:

1. Normal måling (`65 °C`) registreres som `NORMAL`.
2. For høj temperatur (`95 °C`) registreres som `ALARM`.
3. Grænseværdien (`80 °C`) klassificeres som `NORMAL`.
4. Manglende `sensor_id` afvises med HTTP `400`.
5. Ugyldig temperatur afvises med HTTP `400`.
6. Simuleret utilgængelig database returnerer HTTP `500`.

Testene bruger mocks af databaseforbindelsen og ændrer derfor **ikke** den rigtige MySQL-database. Den fulde integration med MySQL er desuden afprøvet manuelt gennem Docker og Postman.

Kør testene lokalt:

```powershell
py -m pip install -r requirements-dev.txt
py -m pytest -v
```

**Verificeret resultat:** `6 passed` ved lokal kørsel og i GitHub Actions.

## GitHub Actions – Continuous Integration

Workflowet findes i `.github/workflows/ci.yml` og starter ved push og pull request. Det:

1. Henter repository-koden.
2. Opsætter Python 3.12.
3. Installerer afhængigheder fra `requirements-dev.txt`.
4. Kører alle seks `pytest`-tests.
5. Bygger API'ets Docker-image.

[Se CI-kørsler på GitHub](https://github.com/Steinomite14/Delopgave-2/actions) *(kræver adgang til det private repository)*.

**Status:** CI er implementeret og har bestået. Automatisk **deployment (CD)** er ikke implementeret; lokal deployment sker med `docker compose up -d --build`.

## Remote adgang på lokalt netværk

API'et kan bruges fra en anden computer på samme netværk, hvis Docker publicerer port 5006, og computerens firewall tillader forbindelsen.

1. Find værtscomputerens lokale IPv4-adresse med `ipconfig` (Windows).
2. Åbn Postman på den anden computer.
3. Brug `http://<VAERTS_IP>:5006/api/measurements` til GET eller POST.

Brug **ikke** `127.0.0.1` på klientcomputeren; adressen henviser altid til klienten selv. Remote adgang på det lokale netværk er afprøvet i projektet.

**Sikkerhed:** Demo-API'et har ikke implementeret egentlig klientautentifikation eller HTTPS. Udstil det derfor **ikke direkte på det offentlige internet**. Begræns adgang til et betroet lokalt netværk.

## Logging og fejlfinding

Vis API-logs:

```bash
docker compose logs --tail=100 api
```

Vis database-logs:

```bash
docker compose logs --tail=100 db
```

Typiske situationer:

| Problem | Mulig løsning |
| --- | --- |
| `GET /api/measurements` viser `[]` | Send en måling med Postman eller kør simulatoren. |
| `Connection refused` | Kontrollér `docker compose ps`, korrekt port og firewall. |
| API'et returnerer `500` | Kontrollér databasecontaineren og `docker compose logs api`. |
| Database-tabeller mangler | Kontrollér `database.sql`; init-scriptet køres ved første oprettelse af datavolumen. |
| Python kan ikke importere `requests` | Kør `py -m pip install requests`. |

## Projektstruktur

```text
Delopgave-2/
├── .github/workflows/ci.yml  # GitHub Actions: tests og Docker-build
├── Tests/test_api.py         # Automatiserede pytest-tests
├── .dockerignore             # Undtagelser fra Docker-build
├── .gitignore                # Undtagelser fra Git, bl.a. .env
├── app.py                    # Flask REST API og domænelogik
├── database.sql              # MySQL-tabeller
├── docker-compose.yml        # API-, database- og volume-opsætning
├── Dockerfile                # Container-image til Flask API
├── requirements.txt          # Afhængigheder til applikationen
├── requirements-dev.txt      # Afhængigheder til test
├── sensor_simulator.py       # Simulerede temperaturmålinger
├── test_mysql.py             # Lokal forbindelsestest til MySQL
└── README.md                 # Denne dokumentation
```

Den lokale `.env`-fil indgår ikke i Git-repositoriet.

## Begrænsninger og videreudvikling

MVP'en demonstrerer event–beslutning–handling, men er bevidst afgrænset. Mulige forbedringer er API-autentifikation, HTTPS, retry/kø ved databaseudfald, integrationstests med rigtig MySQL, mere avanceret overvågning, automatisk deployment og egentlige service-notifikationer.

---

**Uddannelsesprojekt:** Afleveringsopgave 6.2 – Teknisk MVP – REST API Microservice, baseret på casen *Intelligent IoT Solutions A/S*.
