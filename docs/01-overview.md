# Overview

## What is DILP

**DILP (Digital Integration Learning Platform)** is an educational platform that organises structured learning programmes for children, supervised by teachers and authorised by parents. The system is designed around five roles, GDPR-compliant consent flows, and a clean separation between application logic and learning content (delivered through a dedicated in-house Mini-CMS service).

## Users & Roles

| Role | Capabilities |
|------|--------------|
| **Parent** | Self-registers with email and password. Creates child accounts (username + PIN). Grants / revokes consent. Views children's progress. |
| **Child** | Logs in with username and PIN. Sees only programmes assigned to their group. Reads lessons and accumulates progress. |
| **Teacher** | Manually placed by an admin. Manages groups they own, adds children, assigns programmes, can author modules and lessons within assigned programmes. |
| **Admin** | Manages tenants, schools, groups, programmes. Invites teachers. Sees all resources. |
| **Auditor** | Read-only access to activity and audit logs for compliance review. Cannot mutate any data. Provisioned via the `create-auditor` CLI. |

## Core Domain Concepts

- **Tenant** — top-level isolation boundary (e.g. organisation or NGO).
- **School** — belongs to a tenant; holds groups and child profiles.
- **Group** — owned by a single teacher inside a school. Contains children and is assigned programmes (N:M).
- **Programme** — curriculum container, scoped to a tenant (or global).
- **Module** — ordered section inside a programme.
- **Lesson** — atomic unit inside a module. Has a `content_ref` pointing at the DILP Mini-CMS for the rich content, and an optional `meeting_url` for an attached video conference (Google Meet, Zoom, etc.).
- **Consent** — parent's GDPR consent for a child; MVP only supports `data_processing`. A child stays `pending` until `data_processing` is granted.
- **Progress** — module- and lesson-level state per child (`not_started | in_progress | completed`), tracked through the progress endpoints introduced in Sprint 5.

## Design Decisions (Locked)

See memory notes:
- **Sprint 2**: child auth via username + PIN; cascade soft-delete of children with parent; only `data_processing` consent in MVP; admin-bootstrap CLI for the first admin.
- **Sprint 4**: Group ↔ Programme is N:M; teacher authoring is gated by group assignment to the programme; `content_ref` is the path appended to `{CMS_BASE_URL}/`; tests swap in a `FakeCMS` via dependency override.

## Compliance Posture

- Soft-delete (`deleted_at`) on PII-bearing tables; no hard delete from the application.
- `GET /users/me/export` and `DELETE /users/me` implement GDPR Articles 15 and 17.
- Consents are versioned (`consent_version`) and revocable (`revoked_at`).
- Activity and audit logging are live (Sprint 6): HTTP middleware records authenticated requests, a SQLAlchemy listener records mutating ORM changes, and admins/auditors can read both through `/logs/activity` and `/logs/audit`.