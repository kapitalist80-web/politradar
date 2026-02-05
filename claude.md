# Parlamentsmonitor – Swiss Parliament Business Tracker

## Projektübersicht

Webapplikation zur Verfolgung ausgewählter Geschäfte des Schweizer Parlaments. Benutzer erfassen Geschäftsnummern, die automatisch via parlament.ch API aktualisiert werden. Das System bietet Alerting bei Statusänderungen und ein Monitoring-Dashboard für neue Geschäfte.

## Tech Stack

- **Frontend**: React (Vite) + Tailwind CSS, modernes minimalistisches Design
- **Backend**: Node.js (Express) oder Python (FastAPI)
- **Datenbank**: PostgreSQL
- **Auth**: Session-basiert oder JWT, Multi-User mit individuellen Geschäftslisten
- **Scheduler**: Cron-Jobs für periodische API-Abfragen (z.B. alle 6 Stunden)
- **Notifications**: E-Mail-Alerts (optional: Webhook/Push)

## Parlament.ch API

Offene Daten unter `https://ws.parlament.ch/odata.svc/` (OData-Format).

### Wichtige Endpoints

- **Geschäfte**: `Business?$filter=ID eq {id}` – Hauptdaten eines Geschäfts
- **Geschäftsstatus**: `BusinessStatus?$filter=BusinessNumber eq '{nr}'` – Statusverlauf
- **Ratsdebatte**: `BusinessDebate?$filter=BusinessNumber eq '{nr}'` – Debatteninfos
- **Kommissionssitzungen**: `MeetingSession` – Sitzungstermine, filtern nach Kommission
- **Neue Geschäfte**: `Business?$filter=SubmissionDate ge datetime'{date}'&$orderby=SubmissionDate desc` – Neue Geschäfte seit Datum

### API-Hinweise

- Format: OData, Antworten standardmässig als XML. JSON via `$format=json` Parameter
- Paginierung: `$top` und `$skip` verwenden
- Sprachfilter: `Language eq 'DE'` (oder FR, IT)
- Rate Limiting beachten: moderate Abfragefrequenz einhalten
- Dokumentation: https://ws.parlament.ch/odata.svc/$metadata

## Datenmodell

### Kerntabellen

```
users
  id, email, name, password_hash, created_at

tracked_businesses (pro User)
  id, user_id (FK), business_number, title, description, 
  status, business_type, submission_date, 
  last_api_sync, created_at

business_events (Verlaufshistorie)
  id, business_number, event_type, event_date, 
  description, committee_name, raw_data, created_at

alerts
  id, user_id (FK), business_number, alert_type, 
  message, is_read, created_at

monitoring_candidates (neue Geschäfte zum Sichten)
  id, business_number, title, description, business_type,
  submission_date, decision (pending|accepted|rejected), 
  decided_by (FK), decided_at, created_at
```

### Alert-Typen

- `status_change` – Geschäftsstatus ändert sich (z.B. "Im Rat" → "Erledigt")
- `committee_scheduled` – Geschäft auf Kommissionstagesordnung gesetzt
- `debate_scheduled` – Ratsdebatte angesetzt
- `new_document` – Neues Dokument zum Geschäft veröffentlicht
- `vote_result` – Abstimmungsergebnis vorliegend

## Frontend-Struktur

### Seiten / Views

1. **Login / Register** – Authentifizierung
2. **Dashboard** – Übersicht aller verfolgten Geschäfte mit Status-Badges, ungelesene Alerts
3. **Geschäft hinzufügen** – Eingabe einer Geschäftsnummer, Vorschau via API, Bestätigung
4. **Geschäftsdetail** – Vollständige Infos, Eventverlauf (Timeline), Dokumente, Kommissionstermine
5. **Alerts** – Chronologische Alert-Liste mit Filter nach Typ, Gelesen/Ungelesen
6. **Monitoring** – Neue Geschäfte sichten, schnell als "relevant" oder "nicht relevant" markieren (Tinder-Style oder Tabelle mit Entscheidungsbuttons)
7. **Einstellungen** – Benachrichtigungspräferenzen, E-Mail-Einstellungen

### Design-Prinzipien

- Cleanes, modernes Design mit klarer Informationshierarchie
- Status-Badges farbcodiert (grün=aktiv, grau=erledigt, orange=bevorstehend)
- Responsive für Desktop und Mobile
- Dark/Light Mode
- Schweizer Farbgebung dezent integrierbar (Rot-Akzente)

## Backend-Logik

### Sync-Prozess (Scheduler)

```
Alle 6 Stunden:
1. Alle aktiven tracked_businesses abfragen
2. Pro Geschäft: API-Call an parlament.ch
3. Vergleich mit letztem bekannten Status
4. Bei Änderung: business_events anlegen + Alert generieren
5. last_api_sync aktualisieren
```

### Monitoring neuer Geschäfte

```
Täglich (z.B. 07:00):
1. Neue Geschäfte seit letztem Check via API abrufen
2. In monitoring_candidates speichern mit decision=pending
3. Optional: Vorfilterung nach Geschäftstyp oder Themenbereich
```

### Kommissions-Tracking

```
Regelmässig:
1. Kommissionssitzungen abrufen (MeetingSession)
2. Tagesordnungen prüfen auf verfolgte Geschäftsnummern
3. Bei Treffer: Alert "committee_scheduled" generieren
```

## API-Endpunkte (Backend)

```
POST   /api/auth/register
POST   /api/auth/login
POST   /api/auth/logout

GET    /api/businesses              – Alle verfolgten Geschäfte des Users
POST   /api/businesses              – Neues Geschäft tracken (body: {businessNumber})
DELETE /api/businesses/:id          – Tracking beenden
GET    /api/businesses/:id          – Detail mit Events

GET    /api/alerts                  – Alerts des Users (mit Pagination & Filter)
PATCH  /api/alerts/:id/read         – Als gelesen markieren
POST   /api/alerts/read-all         – Alle als gelesen markieren

GET    /api/monitoring              – Pending Monitoring-Kandidaten
PATCH  /api/monitoring/:id          – Entscheidung (accept/reject)

GET    /api/parliament/search?q=    – Geschäft auf parlament.ch suchen (Proxy)
GET    /api/parliament/preview/:nr  – Vorschau eines Geschäfts vor dem Tracking
```

## Wichtige Implementierungsdetails

- **Fehlerbehandlung API**: parlament.ch kann langsam sein oder Timeouts haben. Retries mit Backoff implementieren.
- **Caching**: API-Antworten kurzzeitig cachen um Duplikat-Requests zu vermeiden.
- **Geschäftsnummer-Format**: Format ist z.B. `24.3927` (Jahr.Nummer). Validierung im Frontend.
- **Mehrsprachigkeit**: Geschäftsdaten primär auf Deutsch abrufen (`Language eq 'DE'`), optional FR/IT.
- **Bulk-Sync**: Bei vielen Geschäften sequentiell mit Delays abfragen, nicht parallel.
- **Audit-Log**: Entscheidungen im Monitoring nachvollziehbar speichern (wer, wann, was).

## Sicherheit

- Passwort-Hashing mit bcrypt
- CSRF-Schutz
- Rate Limiting auf Auth-Endpoints
- Input-Validierung auf Geschäftsnummern
- Benutzer sehen nur ihre eigenen Geschäfte und Alerts
