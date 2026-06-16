# Domain Model

All entities use string (UUID) primary keys unless noted. PII-bearing tables carry a nullable `deleted_at` for soft delete.

## Entity Map

```
Tenant ──< School ──< ChildProfile
   │           │
   │           └──< Group ──< GroupMember >── ChildProfile
   │                  │
   │                  ├── teacher: TeacherProfile
   │                  └──< GroupProgramme >── Programme
   │
   └──< Programme ──< Module ──< Lesson

User ──┬── ParentProfile ──< ParentChildRelation >── ChildProfile
       ├── ChildProfile
       ├── TeacherProfile
       ├──< UserRole >── Role
       └──< RefreshToken

ParentProfile ──< Consent >── ChildProfile

ChildProfile ──< ModuleProgress >── Module
ChildProfile ──< LessonProgress >── Lesson

User ──< ActivityLog
User ──< AuditLog
```

## Auth & Identity

### User (`users`)
- `id`, `email?` (unique), `username?` (unique), `password_hash`
- `status`: `active | disabled | pending` (children stay `pending` until `data_processing` consent is granted)
- `last_login_at`, `failed_login_count`, `lockout_until?` (auto-set after repeated failed PIN/password attempts; cleared on successful login)
- `created_at`, `deleted_at?`

### Role (`roles`) + UserRole (`user_roles`)
Seeded with: `child`, `parent`, `teacher`, `admin`.

### RefreshToken (`refresh_tokens`)
SHA-256 hash of the issued token, `expires_at`, `revoked_at?`. Index on `(user_id, created_at)`.

## Profiles

### ParentProfile
One-to-one with User; carries `created_at`.

### TeacherProfile (`teacher_profiles`)
One-to-one with User. Holds `first_name`, `last_name` (both `NOT NULL` since migration `0009`) so the admin UI can show a searchable teacher picker instead of a raw UUID input. `created_at`.

### ChildProfile (`child_profiles`)
- `user_id` (unique), `school_id?`
- `first_name`, `last_name`, `date_of_birth?`, `native_language?` (ISO 639-1)
- `created_at`, `deleted_at?`

### ParentChildRelation (`parent_child_relations`)
Composite PK `(parent_id, child_id)`. Supports multiple parents per child.

## Tenancy

### Tenant (`tenants`)
`id`, `name`, `created_at`.

### School (`schools`)
`tenant_id`, `name`. Index on `tenant_id`.

## Grouping & Assignment

### Group (`groups`)
`school_id`, `teacher_id`, `name`. Indexed by both FKs.

### GroupMember (`group_members`)
Composite PK `(group_id, child_id)`, `joined_at`.

### GroupProgramme (`group_programmes`) — Sprint 4
Composite PK `(group_id, programme_id)`, `assigned_at`. N:M join between groups and programmes; gates teacher authoring.

## Content

### Programme (`programmes`)
`tenant_id?` (null = global), `name`, `language`.

### Module (`modules`)
`programme_id`, `title`, `order_index`. Unique `(programme_id, order_index)`.

### Lesson (`lessons`)
`module_id`, `title`, `content_ref?`, `meeting_url?`, `order_index`. Unique `(module_id, order_index)`.

- `content_ref` is the path appended to `{CMS_BASE_URL}/` to fetch Mini-CMS content at read time. The CMS payload includes the Markdown body and any file attachments uploaded for the lesson.
- `meeting_url` (added in migration `0010`) is an optional link to a video conference (Google Meet, Zoom, …). The student-facing lesson page renders it as a "Join meeting" button; nullable, up to 2048 chars.

## Consent

### Consent (`consents`)
- `parent_id`, `child_id`, `consent_type`, `consent_version` (default `"1.0"`)
- `consent_text_ref?`, `granted_at`, `revoked_at?`
- Index `(child_id, consent_type)`

## Progress

### ModuleProgress (`module_progress`) / LessonProgress (`lesson_progress`)
- `child_id`, `module_id|lesson_id`, `status` (`not_started | in_progress | completed`)
- `started_at?`, `completed_at?`, `updated_at`/`last_accessed_at`
- Unique `(child_id, module_id)` / `(child_id, lesson_id)`

## Audit & Activity

### ActivityLog (`activity_logs`)
`user_id?`, `action`, `entity_type?`, `entity_id?`, `created_at`. Indexed on `(user_id, created_at)` and `(entity_type, entity_id)`.

### AuditLog (`audit_logs`)
`user_id?`, `action` (`create|update|delete`), `entity_type`, `entity_id`, `diff?` (JSON blob, `password_hash` filtered), `timestamp`.

Both tables are populated automatically (Sprint 6): `ActivityLogMiddleware` writes one row per authenticated HTTP request, and a SQLAlchemy event listener writes one row per mutating ORM change. `password_hash` is redacted from `diff` before persistence. Read access is limited to `admin` and `auditor` via `/logs/activity` and `/logs/audit`.

## Cascade Rules

- Deleting a `User` cascades to roles, refresh tokens, and the linked profile (parent/teacher/child).
- Deleting a `Tenant` cascades to schools and (through schools) groups, children, programmes.
- `ChildProfile.school_id` uses `ON DELETE SET NULL` — orphaned children survive a school delete.
- Programme deletion cascades to modules and lessons.