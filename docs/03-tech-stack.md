# Tech Stack

## Backend

| Concern | Choice |
|---------|--------|
| Language | Python 3.11 |
| Framework | FastAPI |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Validation | Pydantic + `pydantic-settings` |
| DB driver | `pymysql` (MySQL 8) |
| Auth | OAuth2PasswordBearer, JWT (PyJWT), Argon2 (`argon2-cffi`) |
| Rate limiting | `slowapi` |
| HTTP client (CMS) | `httpx` |
| Tests | `pytest`, `pytest-asyncio` |

See [`backend/requirements.txt`](../backend/requirements.txt) for pinned versions.

## Frontend

| Concern | Choice |
|---------|--------|
| Language | TypeScript |
| Framework | React 18 |
| Build | Vite 7 |
| Routing | `react-router-dom` 6 |
| UI kit | FluentUI (`@fluentui/react-components`) |
| Markdown | `react-markdown` |
| PDF generation | `pdf-lib` |
| Date/time | `moment`, `moment-timezone` |

See [`frontend/package.json`](../frontend/package.json).

## Data Stores

- **MySQL 8** — core application database (users, profiles, content metadata, progress).
- **PostgreSQL 16** — backing store for the DILP Mini-CMS (separate from the core DB).

## CMS Service

- **DILP Mini-CMS** (`cms_service/`) — a small in-house FastAPI service that stores lesson rich content (Markdown body, title, language) plus arbitrary file attachments per lesson. Backend calls it over HTTP with a static bearer token (`CMS_TOKEN`). Replaces the original Strapi prototype.

## External Services

- **Mailer** — currently a mock writing to an in-memory `outbox`; intended to be replaced by SMTP/SendGrid.

## Infrastructure

- **Docker** + **Docker Compose** for local and production deployment.
- **Traefik** in production for HTTP routing and TLS (per `docker-compose.yml` labels).
- **GitHub Container Registry** (`ghcr.io/edu4ua/dilp/*`) for backend and frontend images.

## Environment Configuration

All backend settings live in `app/core/config.py` and are sourced from environment variables; no defaults are baked into the code for security-sensitive values. See [`backend/.env.example`](../backend/.env.example) for the full list.