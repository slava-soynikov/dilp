# Authentication & RBAC

## Password Storage

- Argon2id via `argon2-cffi`.
- Policy (see `config.py`): minimum length, at least one letter and one digit. Enforced in the registration/reset schemas.

## Tokens

### Access token (JWT)

```json
{
  "sub": "<user-uuid>",
  "roles": ["parent"],
  "type": "access",
  "iat": ...,
  "exp": ...
}
```

- Signed HS256 with `JWT_SECRET`.
- TTL: `ACCESS_TOKEN_TTL_MIN` (default 15 minutes).

### Refresh token

- Random URL-safe string returned to the client.
- Stored in `refresh_tokens` as SHA-256 hash.
- TTL: `REFRESH_TOKEN_TTL_DAYS` (default 7).
- One-use: `/auth/refresh` revokes the consumed token and issues a fresh pair.
- `/auth/logout` marks `revoked_at`.

### Purpose token (password reset)

- JWT with `purpose: "reset_password"`.
- TTL: `PASSWORD_RESET_TOKEN_TTL_HOURS` (default 1).

## Login Flow

1. Client posts `username` (email or username) + `password` as `application/x-www-form-urlencoded` (OAuth2 password grant).
2. Backend looks up by email then username.
3. Verifies Argon2 hash; on failure increments `failed_login_count`.
4. Checks `status`:
   - `disabled` → 403
   - `pending` → 403 (child without `data_processing` consent)
   - `active` → continue
5. Resets `failed_login_count`, updates `last_login_at`, issues tokens.

## Roles

Seeded by migrations `0002_seed_roles` and `0006_seed_auditor_role`:

| Role | Notes |
|------|-------|
| `child` | Created only via `POST /children` (parent action). |
| `parent` | Created via public `POST /auth/register`. |
| `teacher` | Created via `POST /admin/teachers` (admin action, emailed temp password). |
| `admin` | Bootstrapped via CLI (`app/cli.py`). |
| `auditor` | Read-only access to `/logs/*` per §7.3. Provisioned out-of-band (DB or CLI). |

A user may hold multiple roles (e.g. a teacher who is also a parent).

## Authorisation Primitives

In `app/core/`:

- `get_current_user(token, db)` — decodes the JWT, loads the `User` (401 on failure).
- `require_role(*roles)` — FastAPI dependency factory; 403 unless the JWT's `roles` intersect.
- `resolve_scope(db, user) → AccessScope` — returns the row-level scope the user can see:

```python
@dataclass
class AccessScope:
    is_admin: bool
    tenant_ids: set[str]
    school_ids: set[str]
    group_ids: set[str]
    child_ids: set[str]
```

Services use the scope to filter queries. Examples:

- Parent: `child_ids` = own children's IDs.
- Teacher: `group_ids` = groups they own; `child_ids` = members of those groups.
- Child: `child_ids` = `{self.id}`.
- Admin: `is_admin=True` short-circuits all scope checks.

## Teacher Authoring Gate (Sprint 4)

Teachers can CRUD modules/lessons only inside a programme that is assigned (via `group_programmes`) to one of their groups. The check lives in `ProgrammeService` and `ModuleService`/`LessonService` — see [memory: Sprint 4 decisions](../README.md) and the `programmes/` tests.

## Rate Limiting

`slowapi` enforces `AUTH_RATE_LIMIT` (default `10/minute`) on every `/auth/*` endpoint. The limiter is wired in `app/main.py` and uses the client IP key.

## Activity & Audit Logging (Sprint 6)

- `ActivityLogMiddleware` (`app/middleware/activity.py`) writes to
  `activity_logs` after a 2xx response on a fixed allow-list of endpoints
  (auth perimeter, lesson read, progress writes, consent grant/revoke).
  See [`05-api-reference.md`](./05-api-reference.md#logs----logs) for the
  full action list.
- The middleware sets `current_user_id` (a `ContextVar` in
  `app/middleware/context.py`) so the SQLAlchemy `before_flush` listener in
  `app/db/audit.py` can attribute each `AuditLog` row to the actor.
- `password_hash` (and any column added to `REDACTED_COLUMNS`) is stripped
  before the diff is serialised — applies to inserts, updates and deletes.
- For mutations outside an HTTP request (CLI, Alembic), `user_id` on the
  audit row is `NULL` — interpreted as "system actor".

## Things Not Yet Implemented

- CORS, HSTS, CSP headers (Sprint 8).
- SSO / OIDC federation (OAuth2 scaffolding is in place; no providers wired).
- Log retention / TTL policy (Sprint 8 hardening).