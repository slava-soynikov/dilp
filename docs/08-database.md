# Database & Migrations

## Engines

- **Core**: MySQL 8 (production); SQLite in-memory in tests.
- **CMS**: PostgreSQL 16 backing the in-house DILP Mini-CMS (separate process, separate DB).

The core engine string comes from `DATABASE_URL`, e.g. `mysql+pymysql://root:root@localhost:3306/dev`.

## Session Management

`app/db/session.py` exposes:

- `engine` — SQLAlchemy engine with `pool_pre_ping=True`.
- `SessionLocal` — sessionmaker.
- `get_db()` — FastAPI dependency yielding a session.

Models inherit from `app/db/base.py:Base`.

## Migrations (Alembic)

Migration files live in [`backend/alembic/versions/`](../backend/alembic/versions/).

| Revision | File | Purpose |
|----------|------|---------|
| 0001 | `0001_initial_schema.py` | All core tables. |
| 0002 | `0002_seed_roles.py` | Seed `child`, `parent`, `teacher`, `admin` rows. |
| 0003 | `0003_user_username.py` | Add nullable unique `username` to users (for child PIN login). |
| 0004 | `0004_drop_email_verified_at.py` | Drop the legacy `email_verified_at` column — manual teacher placement replaces email verification. |
| 0005 | `0005_group_programmes.py` | Create the `group_programmes` N:M join table. |
| 0006 | `0006_seed_auditor_role.py` | Seed `auditor` role for read-only `/logs/*` access (§7.3). |
| 0007 | `0007_widen_log_entity_id.py` | Widen `entity_id` columns on `activity_logs` / `audit_logs` to fit longer composite identifiers. |
| 0008 | `0008_user_lockout_until.py` | Add `users.lockout_until` for temporary account lockout after repeated failed PIN/password attempts. |
| 0009 | `0009_teacher_name.py` | Add `first_name` / `last_name` to `teacher_profiles` (backfilled, then made `NOT NULL`) so the admin UI can show a searchable teacher picker. |
| 0010 | `0010_lesson_meeting_url.py` | Add `lessons.meeting_url` for an optional video-conference link (Google Meet, Zoom, …) attached to a lesson. |

### Commands

```bash
alembic upgrade head        # apply all
alembic current             # show revision
alembic revision -m "msg"   # new migration (autogenerate if --autogenerate)
alembic downgrade -1        # rollback one
```

The container entrypoint (`backend/entrypoint.sh`) runs `alembic upgrade head` on start, then launches uvicorn.

## Constraints & Indexes

The schema relies heavily on foreign keys and uniqueness constraints to avoid invalid states:

- `users.email` and `users.username` unique (each nullable).
- `(programme_id, order_index)` unique on `modules`.
- `(module_id, order_index)` unique on `lessons`.
- Composite PKs on join tables (`user_roles`, `group_members`, `group_programmes`, `parent_child_relations`).
- `UNIQUE(child_id, module_id)` / `UNIQUE(child_id, lesson_id)` on progress tables.
- FK indexes on all referencing columns.

## Soft Delete

PII-bearing tables (`users`, `child_profiles`) carry `deleted_at`. Repositories filter `deleted_at IS NULL` by default; explicit “include deleted” paths exist for GDPR export and admin tooling.

## Inspection Tips

```bash
# enter MySQL inside compose
docker exec -it $(docker ps -qf name=db) mysql -uroot -proot dev

# print schema for a table
SHOW CREATE TABLE users\G

# show all roles
SELECT u.id, u.email, r.name FROM users u
  JOIN user_roles ur ON ur.user_id = u.id
  JOIN roles r ON r.id = ur.role_id;
```