import os

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-do-not-use-in-prod-32bytes!")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_TTL_MIN", "15")
os.environ.setdefault("REFRESH_TOKEN_TTL_DAYS", "7")
os.environ.setdefault("PASSWORD_RESET_TOKEN_TTL_HOURS", "1")
os.environ.setdefault("PASSWORD_MIN_LENGTH", "10")
os.environ.setdefault("AUTH_RATE_LIMIT", "10/minute")
os.environ.setdefault("CMS_BASE_URL", "http://cms.test")
os.environ.setdefault("CMS_TOKEN", "test-token")
os.environ.setdefault("CMS_TIMEOUT_S", "1.0")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
import app.model  # noqa: F401 — register tables on Base.metadata
from app.db.session import get_db
from app.main import app
from app.integrations import mailer
from app.core.rate_limit import limiter
from app.model.user import Role

limiter.enabled = False


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def db_session(engine):
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSessionLocal()
    # Seed roles each test (cheap; tables persist across tests but we wipe rows).
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    for name in ("child", "parent", "teacher", "admin", "auditor"):
        session.add(Role(name=name))
    session.commit()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def outbox():
    mailer.outbox.clear()
    yield mailer.outbox
    mailer.outbox.clear()


# ---------------- Sprint 3 shared fixtures ----------------

from app.core.security import hash_password  # noqa: E402
from app.model.profile import TeacherProfile  # noqa: E402
from app.model.user import User, UserRole  # noqa: E402


def _seed_role_user(db_session, *, email, password, role_name, with_teacher_profile=False):
    user = User(
        email=email,
        password_hash=hash_password(password),
        status="active",
    )
    db_session.add(user)
    db_session.flush()
    role = db_session.query(Role).filter_by(name=role_name).one()
    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    profile_id = None
    if with_teacher_profile:
        tp = TeacherProfile(user_id=user.id, first_name="Test", last_name="Teacher")
        db_session.add(tp)
        db_session.flush()
        profile_id = tp.id
    db_session.commit()
    return user, profile_id


def login_as(client, identifier: str, password: str) -> dict[str, str]:
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": identifier, "password": password},
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
def admin_headers(client, db_session):
    _seed_role_user(
        db_session, email="admin@example.com", password="AdminPass1234", role_name="admin"
    )
    return login_as(client, "admin@example.com", "AdminPass1234")