# Deployment

## Topology

Production is currently a single VPS running Docker Compose behind Traefik. Backend and frontend images are pulled from GitHub Container Registry (`ghcr.io/edu4ua/dilp/*`).

```
Internet ─▶ Traefik ─┬─▶ frontend container (nginx serving Vite build)
                     └─▶ backend container (uvicorn) ──┬─▶ MySQL 8 (named volume, core DB)
                                                       └─▶ Mini-CMS (internal) ──▶ Postgres 16 (CMS DB)
```

Production compose mirrors local: it ships the DILP Mini-CMS (`cms`) plus its dedicated Postgres (`cms_db`) alongside the core stack. The CMS has no Traefik labels — it is reachable only on the internal compose network as `cms:8055`.

## docker-compose.yml (production)

Highlights from [`/docker-compose.yml`](../docker-compose.yml):

- `backend`: image `ghcr.io/edu4ua/dilp/backend:dev`, Traefik label routes `${HOST_BASE}/api`, `/docs`, `/openapi.json`, `/redoc` to port 8000, loads `.env`.
- `frontend`: image `ghcr.io/edu4ua/dilp/frontend:dev`, Traefik routes `${HOST_BASE}` to port 80 with HTTPS via Let's Encrypt.
- `db`: MySQL 8 with named volume `mysql_data`.
- `cms`: image `ghcr.io/edu4ua/dilp/cms:dev`, internal only (no Traefik), file attachments persisted to the `cms_attachments` named volume.
- `cms_db`: Postgres 16 with named volume `cms_db_data`.

## Container Build

`backend/Dockerfile`:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chmod +x /app/entrypoint.sh
EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

`entrypoint.sh` waits for the DB, runs `alembic upgrade head`, then execs the CMD.

The frontend image builds a Vite production bundle and serves it via nginx.

## CI/CD

GitHub Actions push images to GHCR on the `main` (and `develop`) branches (see `.github/workflows/`). The VPS pulls the new images and runs `docker compose up -d`.

## Environment Variables (production)

The same surface as local development (see [10-development.md](10-development.md)) plus:

- `DATABASE_URL` pointing at the in-compose `db` service.
- Long-lived `JWT_SECRET` (rotate ≠ supported — rotation invalidates all sessions).
- `CMS_BASE_URL=http://cms:8055` (internal compose hostname) and a strong `CMS_TOKEN` shared between `backend` and `cms`.
- `CMS_DB_PASSWORD`, `CMS_DB_USER`, `CMS_DB_NAME` for the Mini-CMS Postgres.

## Open Hardening Items (Sprint 8)

- TLS termination, HSTS, security headers via Traefik middleware.
- CORS allowlist.
- Backups: scheduled `mysqldump` of the named volume.
- Secrets out of plain `.env` into a vault (or Docker secrets / SOPS).
- `pip-audit` and `bandit` in CI.
- Sentry (or alternative) for runtime errors (Sprint 9).
- EU hosting choice formalised (Hetzner / IONOS) for GDPR.