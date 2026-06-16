import logging

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import app.model  # noqa: F401  — register tables on Base.metadata
from app.db import audit as _audit

_audit.register()
from app.api.v1.routes.admin import router as admin_router  # noqa: E402
from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.children import router as children_router
from app.api.v1.routes.cms import router as cms_router
from app.api.v1.routes.consents import router as consents_router
from app.api.v1.routes.groups import router as groups_router
from app.api.v1.routes.parents import router as parents_router
from app.api.v1.routes.schools import router as schools_router
from app.api.v1.routes.teachers import router as teachers_router
from app.api.v1.routes.tenants import router as tenants_router
from app.api.v1.routes.lessons import router as lessons_router
from app.api.v1.routes.logs import router as logs_router
from app.api.v1.routes.modules import router as modules_router
from app.api.v1.routes.programmes import router as programmes_router
from app.api.v1.routes.progress import router as progress_router
from app.api.v1.routes.reports import router as reports_router
from app.api.v1.routes.users import router as users_router
from app.core.rate_limit import limiter
from app.middleware.activity import ActivityLogMiddleware



logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(title="DILP Platform Core")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(ActivityLogMiddleware)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(children_router, prefix="/api/v1")
app.include_router(consents_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(parents_router, prefix="/api/v1")
app.include_router(teachers_router, prefix="/api/v1")
app.include_router(tenants_router, prefix="/api/v1")
app.include_router(schools_router, prefix="/api/v1")
app.include_router(groups_router, prefix="/api/v1")
app.include_router(programmes_router, prefix="/api/v1")
app.include_router(modules_router, prefix="/api/v1")
app.include_router(lessons_router, prefix="/api/v1")
app.include_router(progress_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")
app.include_router(logs_router, prefix="/api/v1")
app.include_router(cms_router, prefix="/api/v1")


@app.get("/")
def hello():
    return {"message": "Hello from backend"}


@app.get("/health")
def health():
    return {"status": "ok"}