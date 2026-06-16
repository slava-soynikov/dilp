# DILP Documentation

**DILP** — Digital Integration Learning Platform. A multi-tenant, GDPR-conscious educational platform with role-based access for parents, children, teachers, and admins.

## Index

| # | Document | Contents |
|---|----------|----------|
| 1 | [Overview](01-overview.md) | What DILP is, users, core concepts |
| 2 | [Architecture](02-architecture.md) | Layered backend, frontend, system diagram |
| 3 | [Tech Stack](03-tech-stack.md) | Languages, frameworks, libraries, infra |
| 4 | [Domain Model](04-domain-model.md) | SQLAlchemy entities, relationships |
| 5 | [API Reference](05-api-reference.md) | All `/api/v1/*` endpoints |
| 6 | [Auth & RBAC](06-auth-rbac.md) | JWT, roles, scoping |
| 7 | [Frontend](07-frontend.md) | React/Vite app structure |
| 8 | [Database & Migrations](08-database.md) | MySQL schema, Alembic history |
| 9 | [Integrations](09-integrations.md) | DILP Mini-CMS, mailer |
| 10 | [Local Development](10-development.md) | Setup, env, running services |
| 11 | [Deployment](11-deployment.md) | Docker Compose, Traefik, CI/CD |
| 12 | [Testing](12-testing.md) | Pytest structure, fixtures |
| 13 | [Sprint Plan](13-sprints.md) | Delivered and pending sprints |

## Quick Links

- Backend entrypoint: [`backend/app/main.py`](../backend/app/main.py)
- Frontend entrypoint: [`frontend/src/App.tsx`](../frontend/src/App.tsx)
- Settings: [`backend/app/core/config.py`](../backend/app/core/config.py) · [`backend/.env.example`](../backend/.env.example)
- Local stack: [`docker-compose.local.yml`](../docker-compose.local.yml)
- Production stack: [`docker-compose.yml`](../docker-compose.yml)