# Sprint Plan

Source of truth for granular sprint items: [`sprints.csv`](../sprints.csv) at the repo root.

## Delivered

### Sprint 0 — Foundation
- SQLAlchemy models, Pydantic schemas, Alembic baseline (migration `0001`).
- Layered architecture (`api / service / repository / model`).
- `pydantic-settings`, `.env.example`, MySQL via Docker.
- GitHub Actions CI/CD scaffolding.

### Sprint 1 — Auth & RBAC
- Full `/auth/*` surface (register, login, refresh, logout, forgot/reset password).
- Argon2 password hashing.
- JWT access + DB-stored hashed refresh tokens.
- `OAuth2PasswordBearer` + `require_role` dependency.
- SlowAPI rate limiting on `/auth/*`.

### Sprint 2 — Users, Profiles, Consents
- CRUD for `/users/me`, `/children`, `/parents`, `/teachers`.
- Parent ↔ child linking.
- GDPR `GET /users/me/export` and `DELETE /users/me` (cascade soft-delete).
- `/consents` grant + revoke; `data_processing` activates a child.
- Locked decisions: username + PIN child auth, only `data_processing` in MVP, admin-bootstrap CLI.

### Sprint 3 — Tenants, Schools, Groups
- CRUD `/tenants`, `/schools`, `/groups`, `/groups/{id}/members`.
- `resolve_scope()` producing an `AccessScope` for row-level filtering.
- Scope-aware listing for parent / teacher / admin.

### Sprint 3b — Cleanup
- Migration `0004` drops `users.email_verified_at`.
- Removed verification flow — children are placed manually by teachers.

### Sprint 4 — Programmes & CMS
- Migration `0005` adds `group_programmes` (N:M).
- CRUD for `/programmes`, `/modules`, `/lessons` with teacher authoring gated by group assignment.
- `POST` / `DELETE` `/groups/{id}/programmes`.
- `httpx`-based CMS client; `GET /lessons/{id}` resolves `content_ref`.
- `GET /children/me/curriculum` returns the assigned programme tree.
- `FakeCMS` test fixture via dependency override.
- DILP Mini-CMS + Postgres added to `docker-compose.local.yml` (originally Strapi 4, later replaced by the in-house service).

### Sprint 5 — Progress Tracking
- `POST /progress/modules/{id}/start | /complete`.
- `POST /progress/lessons/{id}/start | /complete | /heartbeat`.
- Module auto-completes when every lesson is `completed`.
- Child-only writes, scoped to programmes assigned to the child's groups (§7.3).

### Sprint 6 — Activity & Audit Logging
- `ActivityLogMiddleware` writes `ActivityLog` rows for the full auth perimeter
  (`register`, `login`, `logout`, `password_forgot`, `password_reset`),
  `lesson_open`, progress writes (`module_start|complete`,
  `lesson_start|complete`) and consent flow (`consent_grant|revoke`).
- Per-request `current_user_id` ContextVar set by the middleware so SQLAlchemy
  event listeners can attribute mutations to the actor; mutations outside an
  HTTP request (CLI, Alembic) record `user_id = NULL` (system actor).
- `before_flush` listener emits `AuditLog` rows with JSON `before/after/changed`
  diffs on sensitive tables (`users`, `user_roles`, `*_profiles`,
  `parent_child_relations`, `consents`, `group_members`); `password_hash` and
  similarly redacted columns never appear in any diff.
- New `auditor` role (migration `0006`) gates read-only access to
  `GET /logs/activity` and `GET /logs/audit` alongside `admin`, satisfying §7.3
  *Auditor (optional, read-only)*.

### Sprint 7 — Reporting
- `GET /reports/active-users` — distinct active users in a window, bucketed by role (admin/auditor).
- `GET /reports/activity-overview` — total events with `by_action` and `by_day` aggregates (admin/auditor); responses contain no `user_id` to satisfy §7 Data Minimization.
- `GET /reports/groups/{id}/progress` — per-programme module completion totals and average completion percentage across group members; visible to admin/auditor or the owning teacher.
- `GET /reports/programmes/{id}/funnel` — per-module `started`/`completed` counts ordered by `order_index`; visible to admin/auditor or any teacher whose group has the programme assigned.
- `GET /parents/me/children/{id}/dashboard` — per-child programme/module summary with `lessons_total` / `lessons_completed`; only the linked parent can read (404 otherwise, to avoid revealing the existence of unrelated children).
- All reports respect §5.1 (Reporting Basis) and §7.3 (RBAC + auditor read-only).

### Post-Sprint 7 — UX & content polish

Smaller incremental work merged on top of the Sprint 7 cut, captured here so the doc matches the codebase.

- **Replace Strapi with in-house Mini-CMS** (`cms_service/`): smaller surface, no Node admin UI, attachment storage on a named volume; backend talks to it via `CMS_BASE_URL` / `CMS_TOKEN`.
- **Login hardening**: `users.lockout_until` (migration `0008`) — repeated failed PIN / password attempts temporarily lock the account; cleared on successful login.
- **Teacher picker**: `first_name` / `last_name` on `TeacherProfile` (migration `0009`, NOT NULL with backfill from email) so the admin "create group" flow can pick a teacher by name instead of pasting a UUID.
- **Lesson attachments**: teachers can upload any file (PDF, image, doc, …) to a CMS lesson record via `/api/v1/cms/lessons/{id}/attachments`; students see them in a "Materials" block on the lesson page and can download them.
- **Lesson conference link**: `lessons.meeting_url` (migration `0010`) — teachers attach an optional Google Meet / Zoom URL; the student-facing lesson page renders it as a "Join meeting" button.
- **i18n switch**: UI strings moved from `i18n/de.ts` (German) to `i18n/ru.ts` (Russian) — the platform's primary audience is Russian-speaking teachers and parents.
- **Production parity**: production `docker-compose.yml` now mirrors local — Mini-CMS service, Traefik path routing, HTTPS via Let's Encrypt, internal-only CMS network.

## Pending

### Sprint 8 — Hardening & GDPR
- CORS, HSTS, X-Frame-Options, CSP.
- `pip-audit`, `bandit` in CI.
- Formal data flow documentation.
- Backup strategy (`mysqldump` cron).
- EU hosting decision.
- PII audit (logs, third parties).

### Sprint 9 — Testing & Deployment
- End-to-end pytest scenarios.
- Coverage target ≥70 %.
- Sentry runtime monitoring.
- Dev VPS deployment documentation and runbook.