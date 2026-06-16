#!/bin/sh
set -e

# Wait until the database is reachable (up to ~60s) before running migrations.
# Works whether MySQL is on the same network (host=db) or on a different host.
echo "[entrypoint] waiting for database..."
python - <<'PY'
import os, time, sys
from sqlalchemy import create_engine, text

url = os.environ.get("DATABASE_URL")
if not url:
    sys.exit("[entrypoint] DATABASE_URL is not set")

deadline = time.time() + 60
last_err = None
while time.time() < deadline:
    try:
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("[entrypoint] database is reachable")
        sys.exit(0)
    except Exception as e:
        last_err = e
        time.sleep(2)

sys.exit(f"[entrypoint] database not reachable after 60s: {last_err}")
PY

echo "[entrypoint] running alembic migrations..."
alembic upgrade head

echo "[entrypoint] starting application: $*"
exec "$@"