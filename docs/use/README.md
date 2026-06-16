# Wie man DILP benutzt

Diese Anleitung zeigt, wie man die Digital Integration Learning Platform (DILP)
lokal startet und welche Aktionen jede Rolle (Administrator / Lehrkraft /
Elternteil / Kind) im UI durchführen kann.

> Stand der Implementierung: Sprint 0–4 + Mini-CMS + Redesign. Progress-,
> Activity-, Audit-Logging und Reporting sind noch nicht implementiert
> (Sprint 5–7).

---

## 1. Lokal starten

Voraussetzung: Docker Desktop läuft.

```bash
cd /Users/evgen/Desktop/dilp
docker compose -f docker-compose.local.yml up -d --build
docker compose -f docker-compose.local.yml ps
```

Erwartet: **fünf Container** im Status `Up` / `healthy`:

| Service | Port (Host) | Zweck |
|---|---|---|
| `db` | 3306 | MySQL — Platform Core |
| `cms_db` | — | PostgreSQL — Mini-CMS |
| `cms` | 8055 | DILP Mini-CMS (FastAPI) — Lerninhalte |
| `backend` | 8000 | Platform Core API (FastAPI) |
| `frontend` | 5173 | React/Vite Dev Server |

Erste URLs zum Prüfen:

- **UI:** http://localhost:5173/new/ (Trailing-Slash ist wichtig)
- **API-Swagger:** http://localhost:8000/docs
- **Mini-CMS health:** http://localhost:8055/health → `{"status":"ok"}`

### Logs ansehen

```bash
docker compose -f docker-compose.local.yml logs -f backend
docker compose -f docker-compose.local.yml logs -f cms
docker compose -f docker-compose.local.yml logs -f frontend
```

### Stoppen

```bash
docker compose -f docker-compose.local.yml down            # Container stoppen, Daten bleiben
docker compose -f docker-compose.local.yml down -v         # + Daten löschen (frischer Start)
```

---

## 2. Ersten Administrator anlegen

Nur einmal nach `down -v` oder beim allerersten Start nötig:

```bash
docker compose -f docker-compose.local.yml exec backend \
  python -m app.cli create-admin \
    --email admin@dilp.local \
    --password Adm1nStr0ngPass
```

Erwartete Ausgabe:

```
created admin id=<uuid> email=admin@dilp.local
```

Login danach im UI (http://localhost:5173/new/) mit denselben Daten.

> Hinweis: weitere Administratoren über das UI anlegen ist aktuell nicht
> vorgesehen (Sprint-2-Entscheidung). Wenn nötig — diesen CLI-Befehl
> erneut mit einer anderen E-Mail ausführen.

---

## 3. Rollen-Überblick

Die Plattform hat vier Rollen (PDF §5.1, §7.3):

| Rolle | Anmeldung | Ansicht |
|---|---|---|
| **Administrator** | E-Mail + Passwort | komplettes Menü, alles verwalten |
| **Lehrkraft** | E-Mail + Passwort (vom Admin erstellt) | eigene Gruppen, Programme der eigenen Gruppen, Lektionsinhalte |
| **Elternteil** | E-Mail + Passwort (Selbstregistrierung) | eigene Kinder + Konsense |
| **Kind** | **Benutzername + PIN** (vom Elternteil) | nur eigener Lehrplan + Profil |

Sichtbarkeit im UI:
- Sidebar zeigt nur die Bereiche, die für die jeweilige Rolle sinnvoll sind.
- Nicht erlaubte Seiten werden im Backend mit 403/404 geblockt.

---

## 4. Typischer End-to-End Ablauf

Reihenfolge in einer Demonstration:

1. **Admin** legt Tenant + Schule an (Sidebar → „Organisation").
2. **Admin** erstellt Lehrkraft (Sidebar → „Administration" → „Lehrkraft einladen").
   Das **temporäre Passwort wird einmal angezeigt** — bitte sicher an die
   Lehrkraft weitergeben.
3. **Elternteil** registriert sich selbst über `/register`.
4. **Elternteil** legt Kind an (Sidebar → „Meine Kinder" → „Kind hinzufügen") —
   Benutzername wird vom Elternteil vergeben, die **8-stellige PIN** wird
   **einmal angezeigt** und muss sicher notiert werden.
5. **Elternteil** erteilt die Datenverarbeitungs-Einwilligung
   (Spalte „Einwilligung" in der Tabelle → „Einwilligung erteilen").
   Erst danach wird der Kinderaccount aktiv.
6. **Admin** legt eine Lerngruppe in der Schule an und weist die Lehrkraft zu
   (Sidebar → „Lerngruppen" → „Lerngruppe anlegen"). Die Lehrkraft-Profil-ID
   findet man unter http://localhost:8000/docs `GET /teachers`.
7. **Lehrkraft** (oder Admin) fügt das Kind als Mitglied der Lerngruppe hinzu.
8. **Admin** legt ein Programm an (Sidebar → „Programme"). Sprache passend zur
   Muttersprache des Kindes (z. B. `uk`).
9. **Admin** weist das Programm der Lerngruppe zu (auf der Lerngruppe →
   „Programme zuweisen"). Erst danach darf die Lehrkraft Module/Lektionen in
   diesem Programm bearbeiten.
10. **Lehrkraft** öffnet das Programm, legt **Module** und **Lektionen** an. Im
    Feld `content_ref` einer Lektion wird der Pfad zum CMS-Inhalt eingetragen,
    z. B. `items/lessons/1`.
11. **Lehrkraft** (oder Admin) legt unter „Lektionsinhalte" einen CMS-Eintrag an
    (Titel, Sprache, Text). Die generierte ID wird unter der Karte angezeigt
    als `content_ref: items/lessons/<id>` und kann in Schritt 10 eingesetzt
    werden.
12. **Kind** meldet sich an (Benutzername + PIN), öffnet „Mein Lehrplan", wählt
    die Lektion. Der Inhalt wird aus dem Mini-CMS geladen und gerendert.

---

## 5. Häufige Aktionen pro Rolle

### 5.1 Administrator

| Bereich | Aktion |
|---|---|
| Administration → Lehrkraft einladen | Lehrkraftkonto erstellen, temp. Passwort einmalig anzeigen |
| Administration → Passwort zurücksetzen | Neues Passwort für Lehrkraft/Eltern generieren (für Kinder: PIN über Elternkonto zurücksetzen) |
| Organisation | Mandanten + Schulen anlegen / löschen |
| Lerngruppen | Gruppe erstellen, Lehrkraft + Schule zuordnen, Programme zuweisen, Mitglieder verwalten |
| Programme | Programme + Module + Lektionen anlegen (auch ohne Gruppen-Zuweisung) |
| Lektionsinhalte | CMS-Inhalte erstellen / bearbeiten / löschen |
| Mein Konto | Daten exportieren (Art. 15 DSGVO), Konto löschen (Art. 17 DSGVO) |

### 5.2 Lehrkraft

| Bereich | Aktion |
|---|---|
| Lerngruppen | Eigene Gruppen ansehen, Mitglieder hinzufügen/entfernen |
| Programme | Programme der eigenen Gruppen ansehen und bearbeiten (Module/Lektionen) |
| Lektionsinhalte | CMS-Inhalte erstellen / bearbeiten / löschen |

### 5.3 Elternteil

| Bereich | Aktion |
|---|---|
| Meine Kinder | Kinder anlegen (Benutzername, PIN wird einmalig angezeigt) |
| Meine Kinder | Datenverarbeitungs-Einwilligung erteilen / widerrufen |
| Meine Kinder | Kind bearbeiten, PIN zurücksetzen |
| Mein Konto | Daten exportieren (inkl. der Kinder), Konto löschen (Kinder werden mit gelöscht) |

### 5.4 Kind

| Bereich | Aktion |
|---|---|
| Mein Lehrplan | Programme/Module/Lektionen sehen, Lektion öffnen, Inhalt lesen |
| Mein Konto | Daten exportieren, Konto löschen |

---

## 6. Passwörter und PINs vergessen

Es gibt **kein Self-Service-Passwort-Reset im UI**.

- **Kinder** wenden sich an ihre Lehrkraft. Die Lehrkraft informiert das
  Elternteil — das Elternteil setzt die PIN zurück
  (Meine Kinder → „PIN zurücksetzen").
- **Lehrkräfte und Elternteile** wenden sich an die Administration. Der
  Administrator setzt das Passwort über
  „Administration → Passwort zurücksetzen" zurück und übergibt das neue
  Passwort sicher.
- **Administrator** kann sich nicht selbst zurücksetzen. Bei Verlust: in der
  Datenbank kann ein neues Admin-Konto per CLI angelegt werden (s. Abschnitt 2).

---

## 7. Themen-Wechsel (Light / Dark)

In der oberen Leiste rechts neben dem Profilsymbol befindet sich ein
🌙/☀️-Button. Klick wechselt zwischen hellem und dunklem Design.
Die Einstellung wird im Browser gespeichert und respektiert standardmäßig die
System-Einstellung (`prefers-color-scheme`).

---

## 8. Tests laufen lassen

```bash
docker compose -f docker-compose.local.yml exec backend pytest -v
```

Erwartet: alle Tests grün (Stand zuletzt: 118 passed). Die Tests verwenden
SQLite In-Memory + Fake-CMS und brauchen weder MySQL noch den `cms`-Container.

---

## 9. Troubleshooting

| Symptom | Ursache / Lösung |
|---|---|
| `port is already allocated 8055` beim `up` | Alte Container (z. B. ein früherer `directus`) blockieren den Port. `docker compose -f docker-compose.local.yml down --remove-orphans` und erneut starten. |
| Backend in Loop-Restart, Logs zeigen `IntegrityError` bei `roles` | Sollte mit der idempotenten Migration `0002_seed_roles` nicht mehr passieren. Wenn doch — `down -v` und neu hochfahren. |
| Frontend zeigt `The server is configured with a public base URL of /new/ - did you mean to visit /new/` | URL falsch — bitte immer **mit** Trailing-Slash: `http://localhost:5173/new/`. |
| Kinderaccount kann sich nicht anmelden | Wahrscheinlich ist die Datenverarbeitungs-Einwilligung des Elternteils nicht erteilt → Status des Kindes ist `pending`. UI → „Meine Kinder" → „Einwilligung erteilen". |
| Lektion zeigt „Inhalt konnte nicht aus dem CMS geladen werden" | `content_ref` der Lektion zeigt auf einen nicht existierenden CMS-Eintrag, oder der `cms`-Container ist down. Prüfen: `docker compose ... logs cms`. |
| E-Mail-Adresse `…@dilp.local` wird bei Registrierung abgelehnt | `.local` ist als reservierter TLD nicht zulässig. Für Tests bitte `@example.com` o. ä. verwenden. Der CLI-Befehl `create-admin` umgeht diese Prüfung. |

---

## 10. Aufräumen / Reset

Kompletter Reset (alle Daten weg, Container neu gebaut):

```bash
docker compose -f docker-compose.local.yml down -v --remove-orphans
docker compose -f docker-compose.local.yml up -d --build
docker compose -f docker-compose.local.yml exec backend \
  python -m app.cli create-admin \
    --email admin@dilp.local \
    --password Adm1nStr0ngPass
```

Danach ist der Stack im jungfräulichen Zustand und der erste Admin ist
wieder vorhanden.

---

## 11. Weitere Dokumentation

- Architektur und Hintergrund: [`docs/02-architecture.md`](../02-architecture.md)
- API-Referenz: [`docs/05-api-reference.md`](../05-api-reference.md)
- Auth / RBAC: [`docs/06-auth-rbac.md`](../06-auth-rbac.md)
- Test-Konzept: [`docs/12-testing.md`](../12-testing.md)
- Sprintplan und Fortschritt: [`docs/13-sprints.md`](../13-sprints.md)