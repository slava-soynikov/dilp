# Local Development

## Prerequisites

- Docker + Docker Compose
- Python 3.11
- Node.js 18+
- (Optional) MySQL client for inspection

## Bring Up Services

```bash
docker compose -f docker-compose.local.yml up -d
```

Brings up the full stack: MySQL 8 (core DB), PostgreSQL 16 (CMS DB), DILP Mini-CMS, backend (FastAPI) and frontend (Vite dev server). All five containers should reach `Up` / `healthy`.

For backend or frontend hot reload during development you can stop the compose service for that piece and run it on the host — the others stay in Docker.

## Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env       # then edit values
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

API will be at `http://localhost:8000`. OpenAPI docs at `/docs`.

### Required `.env` Values

The backend refuses to start without auth and CMS settings (see `app/core/config.py`):

```env
DATABASE_URL=mysql+pymysql://root:root@localhost:3306/dev

JWT_SECRET=<32+ byte random string>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_TTL_MIN=15
REFRESH_TOKEN_TTL_DAYS=7
PASSWORD_RESET_TOKEN_TTL_HOURS=1
PASSWORD_MIN_LENGTH=10
AUTH_RATE_LIMIT=10/minute

CMS_BASE_URL=http://localhost:8055
CMS_TOKEN=local-dev-cms-token-change-me
CMS_TIMEOUT_S=5.0
```

### Bootstrap the First Admin

`backend/app/cli.py` provides an admin-bootstrap command (see [memory: Sprint 2 decisions](../README.md)). Run it once after the DB is migrated to create the first admin user.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Vite dev server defaults to `http://localhost:5173`. Configure a proxy or set the backend URL according to project conventions.

## Mini-CMS

The CMS service (`cms_service/`) is a small FastAPI app. It auto-migrates its Postgres schema on first start, so no manual admin setup is needed. Health check: `curl http://localhost:8055/health` → `{"status":"ok"}`.

To author lesson content from the UI, log in as admin or teacher and use **Содержимое уроков** (`/lesson-contents`). The backend proxies all CMS writes through `/api/v1/cms/*` so the bearer token never reaches the browser.

## Running Tests

```bash
cd backend
pytest -v
```

Tests use SQLite in-memory and a `FakeCMS` override — no Docker needed.

## Useful Commands

```bash
alembic current
alembic revision -m "add_x"
alembic downgrade -1

docker compose -f docker-compose.local.yml logs -f cms
docker compose -f docker-compose.local.yml down -v   # wipe volumes
```