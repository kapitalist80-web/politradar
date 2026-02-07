# Parlamentsmonitor – Erweiterung: Parlamentarier-Profile & Abstimmungsprognose

## Übersicht

Erweiterung des bestehenden Parlamentsmonitors um Parlamentarier-Profile. Ziel: Für jedes verfolgte Geschäft soll der Benutzer sehen können, welches Gremium (Kommission, Rat) als nächstes behandelt, wer die Mitglieder sind, und wie sie voraussichtlich abstimmen werden.

## Bestehender Tech-Stack (unverändert)

- **Frontend**: React 18 (Vite) + Tailwind CSS 3, react-router-dom v6
- **Backend**: Python FastAPI, SQLAlchemy ORM, Alembic Migrations
- **Datenbank**: PostgreSQL
- **Auth**: JWT (python-jose, passlib/bcrypt)
- **Scheduler**: APScheduler (AsyncIOScheduler)
- **API-Client**: httpx (async) + swissparlpy (sync, via asyncio.to_thread)
- **Projektstruktur**: Monorepo mit `backend/` und `frontend/`

## Neuer Tech-Stack (Ergänzungen)

### Backend-Erweiterungen (Python)

| Komponente | Zweck | Package |
|---|---|---|
| **scikit-learn** | ML-Modell für Abstimmungsprognose (Random Forest, Gradient Boosting) | `scikit-learn>=1.4` |
| **pandas** | Datenaufbereitung Voting-Records, Feature-Engineering | `pandas>=2.1` |
| **numpy** | Numerische Operationen für ML-Pipeline | `numpy>=1.26` |
| **joblib** | Modell-Serialisierung (Persistenz trainierter Modelle) | (in scikit-learn enthalten) |
| **swissparlpy** | Bereits vorhanden – erweiterte Nutzung für MemberCouncil, Vote, Voting, Committee, etc. | `swissparlpy>=0.3.0` (bereits installiert) |

### Optional / Phase 2

| Komponente | Zweck | Package |
|---|---|---|
| **sentence-transformers** | Text-Embeddings für Geschäfts-Beschreibungen (semantische Ähnlichkeit) | `sentence-transformers` |
| **anthropic** | Claude API für Zusammenfassungen von Parteiprogrammen, Kategorisierung | `anthropic` |

### Frontend-Erweiterungen

Keine neuen npm-Packages nötig. Alles mit bestehenden React + Tailwind realisierbar:
- Neue Seiten/Komponenten für Parlamentarier-Profile
- Gremiums-Übersicht mit Drill-Down
- Prognosebalkenchart (einfache Tailwind-Balken oder inline SVG)
- Optional: recharts (bereits als Artifact-Library verfügbar, aber nicht im Frontend installiert – bei Bedarf `npm install recharts`)

---

## Datenmodell – Neue Tabellen

### Kernprinzip
Parlamentsdaten werden lokal gecacht/gespeichert und monatlich synchronisiert. Abstimmungsdaten werden für das ML-Modell aufbereitet.

### Neue Tabellen

```sql
-- Parlamentarier (Ratsmitglieder)
CREATE TABLE parliamentarians (
    id SERIAL PRIMARY KEY,
    person_number INTEGER UNIQUE NOT NULL,     -- parlament.ch PersonNumber
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    gender VARCHAR(10),
    date_of_birth DATE,
    canton_id INTEGER,
    canton_name VARCHAR(100),
    canton_abbreviation VARCHAR(5),
    council_id INTEGER,                        -- 1=Nationalrat, 2=Ständerat
    council_name VARCHAR(100),
    party_id INTEGER,
    party_name VARCHAR(255),
    party_abbreviation VARCHAR(20),
    parl_group_id INTEGER,                     -- Fraktion (kann != Partei sein)
    parl_group_name VARCHAR(255),
    parl_group_abbreviation VARCHAR(20),
    active BOOLEAN DEFAULT TRUE,               -- noch im Amt?
    membership_start DATE,
    membership_end DATE,
    biografie_url VARCHAR(500),
    photo_url VARCHAR(500),
    last_sync TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Partei-Stammdaten
CREATE TABLE parties (
    id SERIAL PRIMARY KEY,
    party_number INTEGER UNIQUE NOT NULL,
    party_name VARCHAR(255),
    party_abbreviation VARCHAR(20),
    -- Später: Parteiprogramm-Zusammenfassung, politische Positionierung
    program_summary TEXT,                       -- von LLM generierte Zusammenfassung
    political_position JSONB,                   -- z.B. {"wirtschaft": "liberal", "soziales": "konservativ", ...}
    last_sync TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Fraktionen (parlamentarische Gruppen)
CREATE TABLE parl_groups (
    id SERIAL PRIMARY KEY,
    parl_group_number INTEGER UNIQUE NOT NULL,
    parl_group_name VARCHAR(255),
    parl_group_abbreviation VARCHAR(20),
    associated_parties TEXT,                    -- Komma-getrennte Partei-Abkürzungen
    last_sync TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Kommissions-Mitgliedschaften
CREATE TABLE committee_memberships (
    id SERIAL PRIMARY KEY,
    person_number INTEGER NOT NULL,
    committee_id INTEGER NOT NULL,
    committee_name VARCHAR(500),
    committee_abbreviation VARCHAR(20),
    council_id INTEGER,                        -- Zugehöriger Rat
    function VARCHAR(100),                     -- Präsident, Vizepräsident, Mitglied
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    last_sync TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(person_number, committee_id, start_date)
);

-- Kommissionen
CREATE TABLE committees (
    id SERIAL PRIMARY KEY,
    committee_number INTEGER UNIQUE NOT NULL,
    committee_name VARCHAR(500),
    committee_abbreviation VARCHAR(20),
    council_id INTEGER,
    committee_type VARCHAR(100),               -- Ständige, Spezial-, etc.
    is_active BOOLEAN DEFAULT TRUE,
    last_sync TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Abstimmungsvorlagen (Vote = eine Abstimmung über ein Thema)
CREATE TABLE votes (
    id SERIAL PRIMARY KEY,
    vote_id INTEGER UNIQUE NOT NULL,           -- parlament.ch Vote ID
    business_number VARCHAR(20),               -- Zugehörige Geschäftsnummer (falls vorhanden)
    business_title VARCHAR(500),
    subject TEXT,                               -- Abstimmungsgegenstand
    meaning_yes TEXT,                           -- Was bedeutet "Ja"?
    meaning_no TEXT,                            -- Was bedeutet "Nein"?
    vote_date TIMESTAMP,
    council_id INTEGER,
    session_id VARCHAR(50),
    total_yes INTEGER,
    total_no INTEGER,
    total_abstain INTEGER,
    total_not_voted INTEGER,
    result VARCHAR(50),                        -- "Angenommen", "Abgelehnt"
    created_at TIMESTAMP DEFAULT NOW()
);

-- Individuelle Stimmabgaben (Voting = einzelne Stimme eines Parlamentariers)
CREATE TABLE votings (
    id SERIAL PRIMARY KEY,
    vote_id INTEGER NOT NULL REFERENCES votes(vote_id),
    person_number INTEGER NOT NULL,
    decision VARCHAR(20) NOT NULL,             -- 'Yes', 'No', 'Abstention', 'Absent', 'President'
    parl_group_number INTEGER,                 -- Fraktion zum Zeitpunkt der Abstimmung
    canton_id INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(vote_id, person_number)
);
CREATE INDEX idx_votings_person ON votings(person_number);
CREATE INDEX idx_votings_vote ON votings(vote_id);
CREATE INDEX idx_votings_decision ON votings(decision);

-- Abstimmungsprognosen (gespeicherte ML-Prognosen pro Geschäft)
CREATE TABLE vote_predictions (
    id SERIAL PRIMARY KEY,
    business_number VARCHAR(20) NOT NULL,
    person_number INTEGER NOT NULL,
    predicted_yes FLOAT,                       -- Wahrscheinlichkeit "Ja"
    predicted_no FLOAT,                        -- Wahrscheinlichkeit "Nein"
    predicted_abstain FLOAT,                   -- Wahrscheinlichkeit "Enthaltung"
    confidence FLOAT,                          -- Konfidenz des Modells
    model_version VARCHAR(50),
    prediction_date TIMESTAMP DEFAULT NOW(),
    UNIQUE(business_number, person_number, model_version)
);

-- Kantone (Lookup)
CREATE TABLE cantons (
    id SERIAL PRIMARY KEY,
    canton_number INTEGER UNIQUE NOT NULL,
    canton_name VARCHAR(100),
    canton_abbreviation VARCHAR(5)
);
```

### Bestehende Tabellen – Änderungen

Keine Schemaänderungen an bestehenden Tabellen nötig. Die Verknüpfung erfolgt über `business_number` (Geschäftsnummer) als logischer Foreign Key.

---

## API-Datenquellen (ws.parlament.ch OData)

### Relevante Entities via swissparlpy

| Entity | Zweck | Key Fields |
|---|---|---|
| **Person** | Stammdaten Parlamentarier | PersonNumber, FirstName, LastName, GenderAsString, DateOfBirth |
| **MemberCouncil** | Aktuelle Ratsmitgliedschaft | PersonNumber, CouncilName, CantonName, ParlGroupName, PartyName |
| **MemberCouncilHistory** | Historische Ratszugehörigkeit | PersonNumber, DateJoining, DateLeaving |
| **MemberCommittee** | Aktive Kommissionsmitgliedschaften | PersonNumber, CommitteeName, CommitteeNumber, Function |
| **MemberCommitteeHistory** | Historische Kommissionszugehörigkeit | PersonNumber, CommitteeName, DateJoining, DateLeaving |
| **Committee** | Kommissions-Stammdaten | CommitteeNumber, CommitteeName, Abbreviation, CouncilId |
| **Party** | Parteien | PartyNumber, PartyName, PartyAbbreviation |
| **ParlGroup** | Fraktionen | ParlGroupNumber, ParlGroupName, ParlGroupAbbreviation |
| **MemberParty** | Parteimitgliedschaft mit Zeitraum | PersonNumber, PartyNumber, StartDate, EndDate |
| **MemberParlGroup** | Fraktionszugehörigkeit mit Zeitraum | PersonNumber, ParlGroupNumber |
| **Vote** | Abstimmungs-Metadaten | ID, BusinessShortNumber, Subject, MeaningYes, MeaningNo, Date |
| **Voting** | Individuelle Stimmabgaben | IdVote, PersonNumber, Decision, ParlGroupNumber, CantonNumber |
| **Canton** | Kantone | CantonNumber, CantonName, CantonAbbreviation |
| **Preconsultation** | Vorberatungen in Kommissionen | BusinessShortNumber, CommitteeName, PreconsultationDate |

### Wichtige Hinweise für API-Zugriff

1. **Voting-Daten sind sehr gross** – immer session-weise oder per IdVote abfragen, nie alles auf einmal
2. **Rate Limiting** beachten – Pausen zwischen Batch-Requests (1-2 Sekunden)
3. **500 Internal Server Error** bei grossen Queries → Batching nötig (z.B. pro Session)
4. **Sprache** immer `Language='DE'` verwenden
5. **swissparlpy** macht synchrone Requests → immer `asyncio.to_thread()` verwenden

---

## Sync-Strategie

### Monatlicher Full-Sync (Parlamentarier & Kommissionen)

```
Scheduler: Cron, 1x pro Monat (z.B. am 1. jeden Monats um 03:00)

1. MemberCouncil abrufen (Language='DE') → Alle aktiven Ratsmitglieder
2. Vergleich mit lokaler DB:
   - Neue Mitglieder → INSERT
   - Ausgetretene → active=False, membership_end setzen
   - Änderungen (Partei, Fraktion, Kommission) → UPDATE
3. Committee + MemberCommittee abrufen → Kommissions-Zusammensetzung aktualisieren
4. Party + ParlGroup abrufen → Stammdaten aktualisieren
5. Bei Änderungen: Alert generieren (neuer Alert-Typ: "council_composition_change")
```

### Wöchentlicher Voting-Sync (Abstimmungsdaten)

```
Scheduler: Cron, 1x pro Woche (z.B. Sonntag 04:00)

1. Neue Sessions seit letztem Sync ermitteln
2. Pro Session: Vote-Records abrufen
3. Pro Vote: Voting-Records (individuelle Stimmen) abrufen
4. In lokale DB speichern
5. ML-Modell-Features aktualisieren
```

### On-Demand: Gremiums-Abfrage bei Geschäftsdetail

```
Wenn User ein Geschäft öffnet:
1. Prüfen welche Kommission / welcher Rat als nächstes behandelt (aus Preconsultation / Session-Schedule)
2. Aktuelle Mitglieder des Gremiums aus lokaler DB laden
3. Falls Prognose-Modell trainiert: Prognose für jedes Mitglied berechnen
4. Ergebnis cachen (vote_predictions Tabelle)
```

---

## ML-Modell: Abstimmungsprognose

### Grundansatz

**Ja, es ist möglich, ein erwartetes Abstimmungsverhalten zu berechnen.** Die Forschung zeigt:

- **VPF Framework** (2025): Bis zu 85% Precision bei individuellen Stimmen über 5 Länder
- **Schweizer Besonderheit**: Fraktionsdisziplin ist hoch aber nicht absolut (v.a. bei SVP, SP, Grüne). Ständeräte sind unabhängiger als Nationalräte.
- **LLM-basierter Ansatz** (2025): F1-Score von ~0.79 für EU-Parlament mit Persona-Prompting

### Feature-Engineering

Für jede Kombination (Parlamentarier × Geschäft) werden folgende Features berechnet:

#### Statische Features (Parlamentarier)
- `party_id` (one-hot encoded)
- `parl_group_id` (one-hot encoded)
- `canton_id` (one-hot encoded)
- `council_id` (1=NR, 2=SR)
- `gender`
- `seniority_years` (Jahre im Rat)

#### Verhaltens-Features (aus Abstimmungshistorie)
- `party_loyalty_score`: Wie oft stimmt Parlamentarier mit Partei-Mehrheit? (0.0 - 1.0)
- `parl_group_loyalty_score`: Wie oft mit Fraktions-Mehrheit?
- `yes_rate`: Anteil "Ja"-Stimmen gesamt
- `abstention_rate`: Anteil Enthaltungen
- `absence_rate`: Abwesenheitsrate
- `voting_similarity_to_author_party`: Wie oft stimmt der Parlamentarier gleich wie die Partei des Geschäftsurhebers?

#### Geschäfts-Features
- `business_type` (one-hot: Motion, Postulat, Initiative, etc.)
- `author_party_id` (Partei des Einreichers)
- `author_parl_group_id` (Fraktion des Einreichers)
- `federal_council_proposal` (Annahme/Ablehnung/keine → encoded)

#### Interaktions-Features
- `same_party_as_author`: Boolean
- `same_parl_group_as_author`: Boolean
- `same_canton_as_author`: Boolean
- `historical_agreement_with_author_party`: Rate aus vergangenen Abstimmungen

### Modell-Pipeline

```python
# Vereinfachter Ablauf

from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import classification_report
import pandas as pd
import joblib

# 1. Training-Daten aufbauen
# Für jede vergangene Abstimmung (Vote) und jeden Parlamentarier:
# → Features berechnen, Label = Decision (Yes/No/Abstention)

# 2. Modell trainieren
model = GradientBoostingClassifier(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
)
model.fit(X_train, y_train)

# 3. Evaluation
# TimeSeriesSplit verwenden (chronologisch, nicht random)
tscv = TimeSeriesSplit(n_splits=3)
for train_idx, test_idx in tscv.split(X):
    model.fit(X.iloc[train_idx], y.iloc[train_idx])
    preds = model.predict(X.iloc[test_idx])
    print(classification_report(y.iloc[test_idx], preds))

# 4. Modell speichern
joblib.dump(model, 'vote_prediction_model.joblib')

# 5. Prognose für neues Geschäft
# → Features für alle Gremiums-Mitglieder berechnen
# → model.predict_proba() für Wahrscheinlichkeiten
```

### Einfachere Alternative (Phase 1): Statistischer Ansatz

Bevor ein ML-Modell trainiert wird, kann ein statistischer Ansatz verwendet werden:

1. **Fraktions-Baseline**: Wie stimmt die Fraktion typischerweise bei diesem Geschäftstyp ab?
   - Berechne pro Fraktion × Geschäftstyp die historische Ja/Nein-Rate
   - Gewichte nach Recency (neuere Abstimmungen stärker)
   
2. **Bundesrats-Signal**: Wenn Bundesrat "Annahme" empfiehlt, stimmen Regierungsparteien tendenziell Ja
   
3. **Autor-Signal**: Geschäfte der eigenen Fraktion werden eher unterstützt

Dieser Ansatz braucht kein ML-Training und liefert bereits nützliche Indikationen.

### Darstellung im Frontend

```
Prognose für: WAK-N (Kommission für Wirtschaft und Abgaben, Nationalrat)
Geschäft: 24.3927 - Motion Müller "..."

┌──────────────────────────────────────────────┐
│  Erwartetes Ergebnis: Annahme wahrscheinlich │
│  ████████████████░░░░  ~65% Ja               │
│                                              │
│  SVP (8 Sitze)    ██████░░  ~75% Nein        │
│  SP (5 Sitze)     ████████  ~90% Ja          │
│  FDP (4 Sitze)    ████░░░░  ~50/50           │
│  Mitte (4 Sitze)  ██████░░  ~70% Ja          │
│  Grüne (3 Sitze)  ████████  ~95% Ja          │
│  GLP (1 Sitz)     ██████░░  ~70% Ja          │
└──────────────────────────────────────────────┘

[Drill-Down per Fraktion → Einzelne Mitglieder]

Mitglied          Partei   Kanton   Prognose   Konfidenz
─────────────────────────────────────────────────────────
Hans Müller       SVP      ZH       Nein       82%
Anna Schmidt      SP       BE       Ja         91%
Peter Weber       FDP      VD       Unsicher   45%
...
```

---

## Backend API-Endpunkte (Neu)

```
GET    /api/parliamentarians                    – Alle aktiven Parlamentarier (mit Filter)
GET    /api/parliamentarians/:person_number     – Profil eines Parlamentariers
GET    /api/parliamentarians/:person_number/votes – Abstimmungshistorie
GET    /api/parliamentarians/:person_number/stats – Statistiken (Loyalität, Aktivität, etc.)

GET    /api/committees                           – Alle aktiven Kommissionen
GET    /api/committees/:id/members               – Mitglieder einer Kommission

GET    /api/councils/:id/members                 – Mitglieder eines Rates (NR/SR)

GET    /api/businesses/:id/treating-body         – Nächstes behandelndes Gremium mit Mitgliedern
GET    /api/businesses/:id/vote-prediction       – Abstimmungsprognose für ein Geschäft

GET    /api/parties                              – Alle Parteien
GET    /api/parl-groups                          – Alle Fraktionen

GET    /api/votes/recent                         – Letzte Abstimmungen
GET    /api/votes/:vote_id                       – Detail einer Abstimmung mit allen Stimmen
```

---

## Frontend – Neue Seiten & Komponenten

### Neue Seiten

1. **Parlamentarier-Übersicht** (`/parliamentarians`)
   - Filterable Liste aller aktiven Mitglieder
   - Filter: Rat, Fraktion, Partei, Kanton
   - Suchfeld (Name)

2. **Parlamentarier-Profil** (`/parliamentarian/:personNumber`)
   - Persönliche Daten, Foto, Partei, Fraktion, Kanton
   - Kommissions-Mitgliedschaften
   - Abstimmungsstatistiken (Loyalitäts-Score, Aktivität)
   - Letzte Abstimmungen mit Stimmverhalten
   - Link zum Profil auf parlament.ch

3. **Gremiums-Ansicht** (in BusinessDetail integriert)
   - Panel das zeigt: "Nächste Behandlung: WAK-N am 15.03.2026"
   - Mitgliederliste mit Fraktions-Farben
   - Prognose-Balken pro Fraktion
   - Drill-Down auf einzelne Mitglieder

4. **Abstimmungsübersicht** (`/votes`)
   - Letzte Abstimmungen mit Ergebnissen
   - Visualisierung der Stimmenverteilung

### Neue Komponenten

- `ParliamentarianCard` – Kompakte Darstellung eines Ratsmitglieds
- `CommitteePanel` – Kommissions-Übersicht mit Mitgliedern
- `VotePredictionBar` – Horizontaler Balken Ja/Nein/Enthaltung
- `FactionBreakdown` – Prognose aufgeschlüsselt nach Fraktionen
- `VotingHistoryTable` – Tabellarische Abstimmungshistorie
- `LoyaltyBadge` – Badge für Fraktionstreue (hoch/mittel/niedrig)

---

## Implementierungsplan (Phasen)

### Phase 1: Datengrundlage (Priorität: HOCH)

1. **Neue DB-Tabellen anlegen** (Alembic-Migration)
2. **Sync-Service für Parlamentarier** implementieren
   - `backend/app/services/parliamentarian_sync.py`
   - Abruf MemberCouncil, Person, Party, ParlGroup, Canton via swissparlpy
   - In lokale DB speichern
3. **Sync-Service für Kommissionen** implementieren
   - Committee, MemberCommittee abrufen und speichern
4. **Scheduler-Jobs** einrichten (monatlich für Parlamentarier, Kommissionen)
5. **Initiales Laden**: Management-Command oder Startup-Task für ersten Full-Load

### Phase 2: Abstimmungsdaten (Priorität: HOCH)

1. **Voting-Sync** implementieren
   - Session-weise Vote + Voting Records abrufen
   - Batching mit Pausen (Rate Limiting)
   - Mindestens aktuelle Legislaturperiode (51., seit 2023)
2. **API-Endpunkte** für Parlamentarier-Profile und Abstimmungshistorie
3. **Frontend**: Parlamentarier-Übersicht und Profil-Seite

### Phase 3: Gremiums-Übersicht (Priorität: HOCH)

1. **Treating-Body Endpoint**: Für ein Geschäft ermitteln welches Gremium als nächstes behandelt
   - Preconsultation-Daten nutzen (bereits vorhanden)
   - Kommissions-Mitglieder aus lokaler DB laden
2. **Frontend**: Gremiums-Panel in BusinessDetail einbauen
3. **Fraktions-Aufschlüsselung** anzeigen

### Phase 4: Prognose-Modell (Priorität: MITTEL)

1. **Feature-Engineering** Pipeline bauen
   - Historische Abstimmungsdaten aufbereiten
   - Features pro Parlamentarier × Geschäft berechnen
2. **Statistischer Basis-Ansatz** implementieren (Fraktions-Tendenz)
3. **ML-Modell** trainieren (Gradient Boosting)
4. **Prediction-Endpoint** und Frontend-Visualisierung
5. **Modell-Update**: Scheduler für periodisches Re-Training (z.B. nach jeder Session)

### Phase 5: Anreicherung (Priorität: NIEDRIG)

1. **Parteiprogramm-Analyse** via Claude API (Zusammenfassungen, politische Positionierung)
2. **Semantische Ähnlichkeit** zwischen Geschäft und Partei-Position
3. **Kantonale Dimension**: Regionale Muster im Abstimmungsverhalten
4. **Export-Funktionen**: Prognosen als PDF/Excel

---

## Dateistruktur (Neue/Geänderte Files)

```
backend/
├── app/
│   ├── models.py                      # ERWEITERN: Neue SQLAlchemy Models
│   ├── schemas.py                     # ERWEITERN: Neue Pydantic Schemas
│   ├── main.py                        # ERWEITERN: Neue Router + Scheduler-Jobs
│   ├── routers/
│   │   ├── parliamentarians.py        # NEU: Parlamentarier-Endpunkte
│   │   ├── committees_router.py       # NEU: Kommissions-Endpunkte
│   │   ├── votes_router.py            # NEU: Abstimmungs-Endpunkte
│   │   ├── predictions.py             # NEU: Prognose-Endpunkte
│   │   └── businesses.py              # ERWEITERN: treating-body Endpoint
│   └── services/
│       ├── parliamentarian_sync.py    # NEU: Sync Parlamentarier, Parteien, Fraktionen
│       ├── committee_sync.py          # NEU: Sync Kommissionen + Mitgliedschaften
│       ├── voting_sync.py             # NEU: Sync Abstimmungsdaten (Vote + Voting)
│       ├── prediction_service.py      # NEU: ML-Modell Training + Prediction
│       ├── feature_engineering.py     # NEU: Feature-Berechnung für ML
│       └── scheduler.py               # ERWEITERN: Neue Sync-Jobs
├── alembic/versions/
│   └── 004_add_parliamentarian_tables.py  # NEU: Migration
├── ml_models/                         # NEU: Gespeicherte ML-Modelle (.joblib)
└── requirements.txt                   # ERWEITERN: neue Dependencies

frontend/src/
├── pages/
│   ├── Parliamentarians.jsx           # NEU: Übersicht
│   ├── ParliamentarianProfile.jsx     # NEU: Profil-Detail
│   ├── Votes.jsx                      # NEU: Abstimmungsübersicht
│   └── BusinessDetail.jsx             # ERWEITERN: Gremiums-Panel
├── components/
│   ├── ParliamentarianCard.jsx        # NEU
│   ├── CommitteePanel.jsx             # NEU
│   ├── VotePredictionBar.jsx          # NEU
│   ├── FactionBreakdown.jsx           # NEU
│   ├── VotingHistoryTable.jsx         # NEU
│   ├── LoyaltyBadge.jsx              # NEU
│   └── Layout.jsx                     # ERWEITERN: Neue Nav-Items
└── App.jsx                            # ERWEITERN: Neue Routen
```

---

## Wichtige Implementierungsdetails

### swissparlpy Nutzung – Beispiele

```python
import swissparlpy as spp
import asyncio

# Alle aktiven Ratsmitglieder
def fetch_active_members():
    data = spp.get_data("MemberCouncil", Language="DE")
    return [dict(row) for row in data]

# Kommissions-Mitglieder
def fetch_committee_members(committee_number):
    data = spp.get_data("MemberCommittee", Language="DE", CommitteeNumber=committee_number)
    return [dict(row) for row in data]

# Abstimmungen einer Session (WICHTIG: batch-weise!)
def fetch_votes_of_session(session_id):
    votes = spp.get_data("Vote", Language="DE", IdSession=session_id)
    return [dict(v) for v in votes]

def fetch_votings_of_vote(vote_id):
    votings = spp.get_data("Voting", Language="DE", IdVote=vote_id)
    return [dict(v) for v in votings]

# Async wrapper
async def async_fetch_active_members():
    return await asyncio.to_thread(fetch_active_members)
```

### Voting-Daten Batching

```python
import time

async def sync_all_votings(session_ids: list[str]):
    """Abstimmungen session-weise abrufen mit Rate-Limiting."""
    for session_id in session_ids:
        votes = await asyncio.to_thread(
            lambda: list(spp.get_data("Vote", Language="DE", IdSession=session_id))
        )
        for vote in votes:
            # Individuelle Stimmen pro Abstimmung
            votings = await asyncio.to_thread(
                lambda vid=vote["ID"]: list(spp.get_data("Voting", Language="DE", IdVote=vid))
            )
            # In DB speichern...
            time.sleep(0.5)  # Rate Limiting
        time.sleep(1.0)  # Pause zwischen Sessions
```

### Feature-Berechnung

```python
def compute_party_loyalty(person_number: int, db: Session) -> float:
    """Berechne wie oft ein Parlamentarier mit seiner Partei-Mehrheit stimmt."""
    # 1. Alle Abstimmungen dieses Parlamentariers laden
    # 2. Pro Abstimmung: Mehrheitsentscheid der Fraktion bestimmen
    # 3. Anteil der Übereinstimmungen berechnen
    ...

def compute_agreement_with_party(person_number: int, target_party_id: int, db: Session) -> float:
    """Historische Übereinstimmung eines Parlamentariers mit einer bestimmten Partei."""
    # Für Prognose relevant: Wie oft stimmt Person X gleich wie Partei Y?
    ...
```

### Prognose-Darstellung: Konfidenz-Hinweise

Die Prognose sollte immer mit Disclaimer angezeigt werden:
- "Basierend auf historischem Abstimmungsverhalten und Fraktionszugehörigkeit"
- "Prognose-Qualität abhängig von verfügbaren Abstimmungsdaten"
- Bei niedrigem Konfidenz-Score: "Keine zuverlässige Prognose möglich"
- Farbcodierung: Grün (>70% Konfidenz), Orange (50-70%), Grau (<50%)

---

## Sicherheit & Performance

- **Parlamentarier-Daten sind öffentlich** – keine Datenschutzbedenken
- **Caching**: Gremiums-Zusammensetzung und Prognosen cachen (Stunden, nicht Sekunden)
- **Lazy Loading**: Abstimmungshistorie nur bei Bedarf laden (Pagination)
- **Bulk-Inserts**: Bei initialem Voting-Import SQLAlchemy bulk_save_objects verwenden
- **ML-Modell**: Offline trainieren, nur Inference online (schnell)

---

## Abhängigkeiten – requirements.txt Ergänzung

```
# Bestehend (unverändert)
fastapi==0.115.6
uvicorn[standard]==0.34.0
sqlalchemy==2.0.36
alembic==1.14.0
psycopg2-binary==2.9.10
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
bcrypt==4.0.1
python-multipart==0.0.19
httpx==0.28.1
apscheduler==3.10.4
pydantic[email-validator]==2.10.3
python-dotenv==1.0.1
swissparlpy==0.3.0

# NEU
pandas>=2.1.0
scikit-learn>=1.4.0
numpy>=1.26.0
```
