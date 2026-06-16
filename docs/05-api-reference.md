# API Reference

All endpoints are mounted under `/api/v1`. Authentication uses `Authorization: Bearer <access_token>` unless noted.

Roles: `parent`, `child`, `teacher`, `admin`, `auditor` (read-only, §7.3).

## Auth — `/auth`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register` | public | Parent self-registration (email + password). Creates `User` + `ParentProfile`. |
| POST | `/auth/login` | public | OAuth2 password flow. Returns `access_token` (JWT, 15 min) + `refresh_token` (7 days). |
| POST | `/auth/refresh` | public | Exchange a non-revoked refresh token for a fresh pair. Old token is revoked. |
| POST | `/auth/logout` | public | Revoke the supplied refresh token. |
| POST | `/auth/forgot-password` | public | Issue a purpose-token email (mock mailer). |
| POST | `/auth/reset-password` | public | Consume a purpose-token to set a new password. |

Rate-limited per `AUTH_RATE_LIMIT` (default `10/minute`).

## Users — `/users`

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET | `/users/me` | any | Current user (id, email, status, created_at, roles). |
| PATCH | `/users/me` | any | Update mutable user fields. |
| GET | `/users/me/export` | any | GDPR Art. 15 — JSON export of all personal data. |
| DELETE | `/users/me` | any | GDPR Art. 17 — soft-delete the user and cascade to children. |

## Children — `/children`

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET | `/children/me/curriculum` | child | Tree of assigned programmes → modules → lessons for the current child. |
| GET | `/children` | parent | List parent's children. |
| POST | `/children` | parent | Create a child. System assigns `username` + `{username}@internal.local` email and generates an 8-digit PIN (returned once). |
| PATCH | `/children/{child_id}` | parent | Update first/last name, DOB, native language. |

## Parents — `/parents`

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET | `/parents/me` | parent | Parent profile. |
| GET | `/parents/me/children/{child_id}/dashboard` | parent (linked) | Per-child programme/module summary with `lessons_total` and `lessons_completed`. Returns `404` for unrelated children to avoid leaking existence. |

## Teachers — `/teachers`

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET | `/teachers/me` | teacher | Teacher profile. |

## Consents — `/consents`

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET | `/consents` | parent | List own consents. |
| POST | `/consents` | parent | Grant consent. `data_processing` activates the child user. |
| POST | `/consents/{consent_id}/revoke` | parent | Set `revoked_at`. |

## Tenants — `/tenants`

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET | `/tenants` | admin | List tenants. |
| POST | `/tenants` | admin | Create tenant. |
| PATCH | `/tenants/{tenant_id}` | admin | Rename tenant. |
| DELETE | `/tenants/{tenant_id}` | admin | Delete (cascades). |

## Schools — `/schools`

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET | `/schools` | any | Scoped list. |
| POST | `/schools` | admin | Create school within a tenant. |
| PATCH | `/schools/{school_id}` | admin | Rename. |
| DELETE | `/schools/{school_id}` | admin | Delete (cascades). |

## Groups — `/groups`

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET | `/groups` | any | Scoped list (admin: all; teacher: own; parent: via own children). |
| POST | `/groups` | admin | Create group with `school_id` + `teacher_id`. |
| PATCH | `/groups/{group_id}` | admin, teacher (own) | Rename. |
| DELETE | `/groups/{group_id}` | admin | Delete (cascades). |
| GET | `/groups/{group_id}/members` | scoped | List child members. |
| POST | `/groups/{group_id}/members` | teacher (own) | Add child. |
| DELETE | `/groups/{group_id}/members/{child_id}` | teacher (own) | Remove child. |
| GET | `/groups/{group_id}/programmes` | scoped | List assigned programmes. |
| POST | `/groups/{group_id}/programmes` | admin, teacher (own) | Assign programme. |
| DELETE | `/groups/{group_id}/programmes/{programme_id}` | admin, teacher (own) | Unassign. |

## Programmes — `/programmes`

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET | `/programmes` | any | Scoped list. |
| POST | `/programmes` | admin | Create programme (`name`, `language`, optional `tenant_id`). |
| GET | `/programmes/{programme_id}` | scoped | Programme with modules. |
| PATCH | `/programmes/{programme_id}` | admin | Update name / language. |
| DELETE | `/programmes/{programme_id}` | admin | Delete (cascades). |
| POST | `/programmes/{programme_id}/modules` | admin, teacher (if their group has the programme) | Create module. |

## Modules — `/modules`

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| PATCH | `/modules/{module_id}` | admin, teacher (gated) | Update title / order. |
| DELETE | `/modules/{module_id}` | admin, teacher (gated) | Delete (cascades). |
| POST | `/modules/{module_id}/lessons` | admin, teacher (gated) | Create lesson. |

## Lessons — `/lessons`

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET | `/lessons/{lesson_id}` | scoped | Lesson metadata (`title`, `content_ref`, `meeting_url`, `order_index`) + resolved CMS content (502 on CMS error). |
| PATCH | `/lessons/{lesson_id}` | admin, teacher (gated) | Update fields. Accepts `title`, `content_ref`, `meeting_url`, `order_index`. Pass `meeting_url: null` to clear an existing link. |
| DELETE | `/lessons/{lesson_id}` | admin, teacher (gated) | Delete. |

`POST /modules/{module_id}/lessons` accepts the same fields as PATCH; `meeting_url` is optional and defaults to `null`.

## CMS proxy — `/cms`

Thin authenticated proxy to the in-house Mini-CMS service. The proxy injects the `CMS_TOKEN` so the frontend never sees it and applies platform-level role checks on top.

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET | `/cms/lessons` | scoped | List CMS lesson records (title, language, body preview). |
| GET | `/cms/lessons/{id}` | scoped | Single CMS lesson record. |
| POST | `/cms/lessons` | admin, teacher | Create a CMS record (title, language, Markdown body). |
| PATCH | `/cms/lessons/{id}` | admin, teacher | Update a CMS record. |
| DELETE | `/cms/lessons/{id}` | admin, teacher | Delete a CMS record. |
| GET | `/cms/lessons/{id}/attachments` | scoped | List file attachments on the CMS lesson. |
| POST | `/cms/lessons/{id}/attachments` | admin, teacher | Upload a file (multipart, up to ~25 MB). |
| GET | `/cms/lessons/{id}/attachments/{att_id}` | scoped | Download the file (streams the binary). |
| DELETE | `/cms/lessons/{id}/attachments/{att_id}` | admin, teacher | Remove the attachment. |

## Reports — `/reports`

Sprint 7 aggregated reporting (§5.1 Reporting Basis). All responses are
aggregated and contain no `user_id` (§7 Data Minimization).

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET | `/reports/active-users` | admin, auditor | Distinct users with at least one `ActivityLog` row in the window, bucketed by role. Query: `window_days` (1–365, default 30). |
| GET | `/reports/activity-overview` | admin, auditor | Total events with `by_action` (sorted) and `by_day` aggregates over the window. Query: `window_days` (1–365, default 30). |
| GET | `/reports/groups/{group_id}/progress` | admin, auditor, owning teacher | Per-programme module completion totals plus `completion_avg_pct` across group members. 404 if the group does not exist; 403 if a teacher does not own it. |
| GET | `/reports/programmes/{programme_id}/funnel` | admin, auditor, teacher whose group has the programme assigned | Per-module `started`/`completed` counts ordered by `order_index`. |

## Logs — `/logs`

Read-only access to the append-only activity and audit trails. Restricted to
`admin` and `auditor` roles (§7.3).

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET | `/logs/activity` | admin, auditor | Behavioural log. Query: `user_id`, `action`, `entity_type`, `limit` (≤500), `offset`. Ordered by `created_at desc`. |
| GET | `/logs/audit` | admin, auditor | Compliance log with JSON diff. Query: `user_id`, `action`, `entity_type`, `entity_id`, `limit`, `offset`. `password_hash` is never present in any diff. |

Actions written to `activity_logs` by the middleware: `register`, `login`,
`logout`, `password_forgot`, `password_reset`, `lesson_open`, `module_start`,
`module_complete`, `lesson_start`, `lesson_complete`, `consent_grant`,
`consent_revoke`.

Tables audited by the SQLAlchemy `before_flush` listener: `users`,
`user_roles`, `child_profiles`, `parent_profiles`, `teacher_profiles`,
`parent_child_relations`, `consents`, `group_members`.

## Admin — `/admin`

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| POST | `/admin/teachers` | admin | Create teacher user + profile; mailer dispatches temp password. |

## Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Liveness ping. |
| GET | `/health` | Readiness ping. |

## Error Conventions

- `400` invalid payload (Pydantic) or business rule violation.
- `401` missing/expired access token.
- `403` role guard or scope check failed.
- `404` entity missing or out of scope (preferred over 403 to avoid leaking existence).
- `409` unique constraint violation (email, username, `(programme_id, order_index)` …).
- `422` validation (e.g. password policy).
- `429` rate limit.
- `502` upstream CMS failure on `GET /lessons/{id}`.