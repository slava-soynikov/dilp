# Testing

## Backend

### Runner

`pytest` + `pytest-asyncio`. Run from `backend/`:

```bash
pytest -v
pytest backend/tests/programmes -v
pytest -k "consent"
```

### Layout

```
backend/tests/
  conftest.py              ← root fixtures
  auth/                    ← register, login, refresh, password reset, RBAC
  users/                   ← /users/me, export, delete
  children/                ← child creation, curriculum
  parents/
  tenants/
  schools/
  groups/                  ← CRUD, members, programme assignment
  programmes/              ← programmes, modules, lessons, CMS
    conftest.py            ← FakeCMS override
  consents/
  admin/
  progress/                ← module/lesson progress + auto-completion (Sprint 5)
  activity/                ← ActivityLogMiddleware unit tests (Sprint 6)
  audit/                   ← SQLAlchemy audit listener tests (Sprint 6)
  log_api/                 ← /logs/activity + /logs/audit access control + filters (Sprint 6)
```

### Core Fixtures (`conftest.py`)

| Fixture | What it does |
|---------|--------------|
| `engine` | SQLite in-memory engine with all tables created. |
| `db_session` | Per-test session. Seeds `roles` rows; rolls back state between tests. |
| `client` | `TestClient` with `get_db` overridden to use `db_session`. |
| `outbox` | Reference to `mailer.outbox` for asserting sent emails. |

### Programmes Subsuite (`programmes/conftest.py`)

Overrides `get_cms_client` with a `FakeCMS` so lesson-content tests run offline. The fake holds a `{ref: payload}` dict and can be told to raise `CMSError` to exercise the 502 path.

### Conventions

- One assertion focus per test, but freely build the necessary fixtures inline (`make_parent()`, `make_child()`, `make_group()` helpers per suite).
- Cover both happy path and the relevant role/scope rejections (401, 403, 404, 409).
- Don’t mock the database — tests hit real SQLAlchemy through SQLite.

## Frontend

No automated test runner is configured yet. TypeScript + Vite catches compilation regressions; end-to-end testing is deferred to Sprint 9.

## Manual Smoke Test (recommended)

1. Bring up the local stack (see [Development](10-development.md)).
2. Register a parent through the UI.
3. Bootstrap an admin via CLI, create a tenant + school + teacher.
4. Login as the teacher, create a group, add the parent's child to it.
5. Admin creates a programme, assigns it to the group.
6. Teacher adds a module and lesson with a valid `content_ref`.
7. Login as the child (username + PIN), open `/curriculum`, then the lesson.
8. CMS content should render in the lesson viewer.