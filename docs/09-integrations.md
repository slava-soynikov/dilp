# Integrations

## DILP Mini-CMS

### Why

Lesson content (Markdown body, attached files) is authored in a small in-house FastAPI service (`cms_service/`), decoupled from the core app database. Core stores only a `content_ref` pointer (and the optional `meeting_url`) per lesson; rich content is fetched at read time and never persisted in the core DB.

The original prototype used Strapi 4; it was replaced by this Mini-CMS because Strapi's admin UI, plugin model and Node footprint were vastly more than what DILP actually needed (a `lessons` collection + file attachments).

### Client

`app/integrations/cms.py` exposes a thin `CMSClient` backed by `httpx`:

- Base URL: `CMS_BASE_URL` (e.g. `http://cms:8055` locally).
- Auth: `Authorization: Bearer ${CMS_TOKEN}` (static, shared secret in env).
- Timeout: `CMS_TIMEOUT_S` (seconds).
- `get_content(ref)` → fetches `{CMS_BASE_URL}/{ref}` and returns parsed JSON.
- Raises `CMSError` on 404, ≥400, network error, or non-JSON response.

The client is wired through a FastAPI dependency `get_cms_client()` so tests can override it (see `FakeCMS` in `backend/tests/programmes/conftest.py`).

### `content_ref` Convention (locked Sprint 4)

`content_ref` is the path appended to `{CMS_BASE_URL}/`. Example:

```
content_ref = "items/lessons/1"
→ GET http://cms:8055/items/lessons/1
```

### Endpoint Surface

- `GET /api/v1/lessons/{id}` resolves `content_ref` on the fly. On CMS failure the backend returns `502` and includes the CMS error in `detail`. The response also surfaces `meeting_url` so the student-facing viewer can render a "Join meeting" button.
- `/api/v1/cms/*` is a thin authenticated proxy (see [05-api-reference](05-api-reference.md)) that lets the frontend create, edit and delete CMS records and file attachments without seeing `CMS_TOKEN`.

### Test Strategy

Tests inject `FakeCMS` via `app.dependency_overrides[get_cms_client] = lambda: FakeCMS(...)`. The fake holds a dict of `ref → payload`; failures are simulated by raising `CMSError`.

### Local Setup

`docker-compose.local.yml` runs the Mini-CMS (`cms` service, port 8055) backed by a dedicated Postgres 16 (`cms_db`). The CMS service auto-migrates its tables on startup, so no manual admin setup is needed.

## Mailer

`app/integrations/mailer.py` currently writes to an in-memory `outbox` list. Two helpers:

- `send_password_reset(to, token)`
- `send_teacher_invite(to, temp_password)`
- `send_password_change_notice(to)`

Tests assert on `mailer.outbox`. A production implementation should swap the transport (SMTP, SendGrid, SES) behind the same function signatures and add the relevant settings to `config.py` and `.env.example`.

## Future Integrations (out of MVP)

- SSO / OIDC providers (the OAuth2 scaffolding is ready).
- Sentry for runtime error tracking (Sprint 9).
- Analytics pipeline (deferred).