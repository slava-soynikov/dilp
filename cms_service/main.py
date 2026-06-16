"""DILP mini-CMS service.

Separate component as required by Solution Architecture §6.1 / §6.3
(Trennung von Content-Daten und Nutzerdaten). Holds only lesson content
(title, body, locale, attachments) — never PII, never user/progress data.

Wire-compatible with Directus-style paths so Platform Core's CMSClient
keeps working without changes:
    GET    /items/lessons              -> {"data": [...]}
    GET    /items/lessons/{id}         -> {"data": {...}}
    POST   /items/lessons              -> {"data": {...}}
    PATCH  /items/lessons/{id}         -> {"data": {...}}
    DELETE /items/lessons/{id}         -> 204

Attachments (any file type, up to MAX_UPLOAD_BYTES):
    GET    /items/lessons/{id}/attachments              list
    POST   /items/lessons/{id}/attachments              multipart upload
    GET    /items/lessons/{id}/attachments/{att_id}     stream download
    DELETE /items/lessons/{id}/attachments/{att_id}     remove
"""
from __future__ import annotations

import os
import time
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import (
    Depends,
    FastAPI,
    File,
    Header,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker

DATABASE_URL = os.environ["DATABASE_URL"]
CMS_TOKEN = os.environ["CMS_TOKEN"]
STORAGE_PATH = Path(os.environ.get("CMS_STORAGE_PATH", "/data/attachments"))
MAX_UPLOAD_BYTES = int(os.environ.get("CMS_MAX_UPLOAD_BYTES", str(25 * 1024 * 1024)))

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class LessonContent(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False, default="")
    locale = Column(String(8), nullable=False, default="uk")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    attachments = relationship(
        "LessonAttachment",
        back_populates="lesson",
        cascade="all, delete-orphan",
    )


class LessonAttachment(Base):
    __tablename__ = "lesson_attachments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lesson_id = Column(
        Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_name = Column(String(255), nullable=False)
    mime_type = Column(String(127), nullable=False, default="application/octet-stream")
    size_bytes = Column(BigInteger, nullable=False, default=0)
    storage_path = Column(String(500), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    lesson = relationship("LessonContent", back_populates="attachments")


def _wait_for_db_and_create_tables() -> None:
    deadline = time.time() + 60
    last_err: Exception | None = None
    while time.time() < deadline:
        try:
            Base.metadata.create_all(bind=engine)
            return
        except OperationalError as exc:
            last_err = exc
            time.sleep(2)
    raise RuntimeError(f"cms_service: database not reachable: {last_err}")


# ---------------- schemas ----------------


class LessonIn(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    body: str = ""
    locale: str = Field(default="uk", min_length=2, max_length=8)


class LessonPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    body: str | None = None
    locale: str | None = Field(default=None, min_length=2, max_length=8)


class AttachmentOut(BaseModel):
    id: int
    lesson_id: int
    file_name: str
    mime_type: str
    size_bytes: int
    created_at: datetime

    model_config = {"from_attributes": True}


class LessonOut(BaseModel):
    id: int
    title: str
    body: str
    locale: str
    created_at: datetime
    updated_at: datetime
    attachments: list[AttachmentOut] = []

    model_config = {"from_attributes": True}


# ---------------- deps ----------------


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_token(authorization: str | None = Header(default=None)) -> None:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    if token != CMS_TOKEN:
        raise HTTPException(status_code=401, detail="invalid token")


# ---------------- app ----------------


app = FastAPI(title="DILP mini-CMS")


@app.on_event("startup")
def _startup() -> None:
    _wait_for_db_and_create_tables()
    STORAGE_PATH.mkdir(parents=True, exist_ok=True)


@app.get("/health")
def health():
    return {"status": "ok"}


def _lesson_or_404(db: Session, lesson_id: int) -> LessonContent:
    row = db.get(LessonContent, lesson_id)
    if not row:
        raise HTTPException(status_code=404, detail="not found")
    return row


@app.get("/items/lessons")
def list_lessons(
    _: None = Depends(require_token),
    db: Session = Depends(get_db),
):
    rows = db.query(LessonContent).order_by(LessonContent.id.desc()).all()
    return {"data": [LessonOut.model_validate(r).model_dump(mode="json") for r in rows]}


@app.get("/items/lessons/{lesson_id}")
def get_lesson(
    lesson_id: int,
    _: None = Depends(require_token),
    db: Session = Depends(get_db),
):
    row = _lesson_or_404(db, lesson_id)
    return {"data": LessonOut.model_validate(row).model_dump(mode="json")}


@app.post("/items/lessons", status_code=status.HTTP_201_CREATED)
def create_lesson(
    payload: LessonIn,
    _: None = Depends(require_token),
    db: Session = Depends(get_db),
):
    row = LessonContent(title=payload.title, body=payload.body, locale=payload.locale)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"data": LessonOut.model_validate(row).model_dump(mode="json")}


@app.patch("/items/lessons/{lesson_id}")
def update_lesson(
    lesson_id: int,
    payload: LessonPatch,
    _: None = Depends(require_token),
    db: Session = Depends(get_db),
):
    row = _lesson_or_404(db, lesson_id)
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return {"data": LessonOut.model_validate(row).model_dump(mode="json")}


@app.delete("/items/lessons/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lesson(
    lesson_id: int,
    _: None = Depends(require_token),
    db: Session = Depends(get_db),
):
    row = _lesson_or_404(db, lesson_id)
    for att in list(row.attachments):
        _unlink_storage(att.storage_path)
    db.delete(row)
    db.commit()
    return None


# ---------------- attachments ----------------


def _safe_filename(name: str) -> str:
    name = os.path.basename(name or "file").strip()
    if not name:
        name = "file"
    return name[:255]


def _storage_dir(lesson_id: int) -> Path:
    d = STORAGE_PATH / str(lesson_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _unlink_storage(path_str: str) -> None:
    try:
        p = Path(path_str)
        if p.is_file():
            p.unlink()
    except OSError:
        pass


@app.get("/items/lessons/{lesson_id}/attachments")
def list_attachments(
    lesson_id: int,
    _: None = Depends(require_token),
    db: Session = Depends(get_db),
):
    _lesson_or_404(db, lesson_id)
    rows = (
        db.query(LessonAttachment)
        .filter(LessonAttachment.lesson_id == lesson_id)
        .order_by(LessonAttachment.id.desc())
        .all()
    )
    return {
        "data": [AttachmentOut.model_validate(r).model_dump(mode="json") for r in rows]
    }


@app.post(
    "/items/lessons/{lesson_id}/attachments", status_code=status.HTTP_201_CREATED
)
def upload_attachment(
    lesson_id: int,
    file: UploadFile = File(...),
    _: None = Depends(require_token),
    db: Session = Depends(get_db),
):
    _lesson_or_404(db, lesson_id)
    safe_name = _safe_filename(file.filename or "file")
    dest_dir = _storage_dir(lesson_id)
    storage_name = f"{uuid.uuid4().hex}_{safe_name}"
    dest = dest_dir / storage_name

    size = 0
    chunk_size = 1024 * 1024
    try:
        with dest.open("wb") as out:
            while True:
                chunk = file.file.read(chunk_size)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    out.close()
                    dest.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=413,
                        detail=f"file exceeds max size {MAX_UPLOAD_BYTES} bytes",
                    )
                out.write(chunk)
    finally:
        file.file.close()

    att = LessonAttachment(
        lesson_id=lesson_id,
        file_name=safe_name,
        mime_type=file.content_type or "application/octet-stream",
        size_bytes=size,
        storage_path=str(dest),
    )
    db.add(att)
    db.commit()
    db.refresh(att)
    return {"data": AttachmentOut.model_validate(att).model_dump(mode="json")}


@app.get("/items/lessons/{lesson_id}/attachments/{att_id}")
def download_attachment(
    lesson_id: int,
    att_id: int,
    _: None = Depends(require_token),
    db: Session = Depends(get_db),
):
    att = db.get(LessonAttachment, att_id)
    if not att or att.lesson_id != lesson_id:
        raise HTTPException(status_code=404, detail="not found")
    p = Path(att.storage_path)
    if not p.is_file():
        raise HTTPException(status_code=410, detail="file missing")
    return FileResponse(
        path=str(p),
        media_type=att.mime_type or "application/octet-stream",
        filename=att.file_name,
    )


@app.delete(
    "/items/lessons/{lesson_id}/attachments/{att_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_attachment(
    lesson_id: int,
    att_id: int,
    _: None = Depends(require_token),
    db: Session = Depends(get_db),
):
    att = db.get(LessonAttachment, att_id)
    if not att or att.lesson_id != lesson_id:
        raise HTTPException(status_code=404, detail="not found")
    _unlink_storage(att.storage_path)
    db.delete(att)
    db.commit()
    return None