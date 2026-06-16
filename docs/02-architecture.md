
# Architecture

## High-Level Topology

```
┌──────────────┐      HTTPS      ┌──────────────────┐
│  Browser     │ ───────────────▶│  Traefik (prod)  │
│  (React SPA) │                  └────────┬─────────┘
└──────────────┘                           │
                                ┌──────────┴──────────┐
                                ▼                      ▼
                         ┌────────────┐         ┌────────────┐
                         │  Frontend  │         │  Backend   │
                         │  (Vite)    │         │  (FastAPI) │
                         └────────────┘         └─────┬──────┘
                                                       │
                          ┌────────────────────────────┼─────────────────┐
                          ▼                            ▼                 ▼
                   ┌────────────┐              ┌────────────┐    ┌────────────┐
                   │  MySQL 8   │              │  Mini-CMS  │    │  Mailer    │
                   │  (Core DB) │              │ (FastAPI)  │    │  (mock)    │
                   └────────────┘              └─────┬──────┘    └────────────┘
                                                     ▼
                                              ┌────────────┐
                                              │ Postgres   │
                                              │  (CMS DB)  │
                                              └────────────┘
```

## Backend Layered Architecture

```
api/v1/routes/   ← FastAPI routers; only validation + dependency wiring
   │
   ▼
service/         ← business logic, RBAC checks, orchestrates repositories
   │
   ▼
repository/      ← SQLAlchemy queries; no business logic
   │
   ▼
model/           ← SQLAlchemy ORM declarations
```

Cross-cutting:
- `schema/` — Pydantic request/response models.
- `core/` — settings, security primitives, RBAC dependencies, scope resolution, rate limiting.
- `db/` — SQLAlchemy `Base`, session factory, `get_db` dependency.
- `integrations/` — external clients (CMS, mailer).
- `middleware/` — `ActivityLogMiddleware` (records authenticated HTTP calls into `activity_logs`) and supporting helpers. A SQLAlchemy event listener also writes mutating ORM changes into `audit_logs` (see [04-domain-model](04-domain-model.md) and [06-auth-rbac](06-auth-rbac.md)).

### Rule of thumb

- Routers never touch the DB directly; they call a service.
- Services contain authorisation logic; they take the current `User` and call `resolve_scope()` for row-level filtering.
- Repositories know SQLAlchemy; services do not.
- Schemas isolate the wire format from the ORM.

## Request Lifecycle (example)

`POST /api/v1/groups/{group_id}/programmes`

1. FastAPI routes to `groups.add_programme()` in `app/api/v1/routes/groups.py`.
2. Dependencies: `get_db` opens a session; `require_role("teacher", "admin")` decodes the JWT and enforces role.
3. The router calls `GroupService(db).assign_programme(user, group_id, programme_id)`.
4. Service runs `resolve_scope(db, user)` and checks the teacher owns the group / admin sees all.
5. Service calls `GroupRepository` (or operates on ORM directly via `db.add(...)`).
6. Response is built via a Pydantic schema in `schema/programme.py`.

## Frontend Layered Structure

```
pages/         ← route-level views, one per URL
components/    ← reusable UI (AppShell, dialogs, form fields)
api/           ← typed fetch wrappers, one module per domain
auth/          ← AuthContext, RequireAuth, RequireRole, token store
i18n/          ← translation strings (Russian)
```

`api/client.ts` handles tokens, automatic refresh on 401, and error parsing. Each domain module (`children.ts`, `programmes.ts`, …) exports typed helpers that wrap the generic client.

## Key Cross-Cutting Concerns

- **Multi-tenancy**: enforced by `resolve_scope()` returning an `AccessScope` (tenant IDs, school IDs, group IDs, child IDs, `is_admin`). Services filter queries by scope.
- **Soft delete**: PII-bearing rows use a nullable `deleted_at`. Repositories filter `deleted_at IS NULL` by default.
- **Rate limiting**: SlowAPI on `/auth/*` (configurable via `AUTH_RATE_LIMIT`).
- **CMS decoupling**: lessons hold only a `content_ref`; content is fetched at read time and never persisted in the core DB.