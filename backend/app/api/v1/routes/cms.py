"""Authenticated passthrough to the mini-CMS service.

Frontend talks to this router using the normal JWT cookie/header. Backend
forwards the request to the CMS service (which lives in a separate
container, holds its own DB, and authenticates via a static bearer token).

This keeps the CMS_TOKEN out of the browser while preserving the
separation-of-concerns model from Solution Architecture §6.1 / §6.3.
"""
from __future__ import annotations

from typing import Any

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from fastapi.responses import StreamingResponse

from app.api.deps import get_current_user, require_role
from app.core.config import settings
from app.model.user import User
from pydantic import BaseModel, Field

router = APIRouter(prefix="/cms", tags=["cms"])


def _cms_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {settings.CMS_TOKEN}"}


def _cms_url(path: str) -> str:
    return f"{settings.CMS_BASE_URL.rstrip('/')}/{path.lstrip('/')}"


class LessonContentIn(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    body: str = ""
    locale: str = Field(default="uk", min_length=2, max_length=8)


class LessonContentPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    body: str | None = None
    locale: str | None = Field(default=None, min_length=2, max_length=8)


def _proxy_get(path: str) -> Any:
    try:
        resp = httpx.get(_cms_url(path), headers=_cms_headers(), timeout=settings.CMS_TIMEOUT_S)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"cms unreachable: {exc}") from exc
    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="not found")
    if resp.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"cms error {resp.status_code}")
    return resp.json()


@router.get("/lessons")
def list_lessons(_: User = Depends(require_role("admin", "teacher"))):
    return _proxy_get("items/lessons")


@router.get("/lessons/{lesson_id}")
def get_lesson(
    lesson_id: int,
    _: User = Depends(require_role("admin", "teacher")),
):
    return _proxy_get(f"items/lessons/{lesson_id}")


@router.post("/lessons", status_code=201)
def create_lesson(
    payload: LessonContentIn,
    _: User = Depends(require_role("admin", "teacher")),
):
    try:
        resp = httpx.post(
            _cms_url("items/lessons"),
            headers={**_cms_headers(), "Content-Type": "application/json"},
            json=payload.model_dump(),
            timeout=settings.CMS_TIMEOUT_S,
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"cms unreachable: {exc}") from exc
    if resp.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"cms error {resp.status_code}: {resp.text[:200]}")
    return resp.json()


@router.patch("/lessons/{lesson_id}")
def update_lesson(
    lesson_id: int,
    payload: LessonContentPatch,
    _: User = Depends(require_role("admin", "teacher")),
):
    try:
        resp = httpx.patch(
            _cms_url(f"items/lessons/{lesson_id}"),
            headers={**_cms_headers(), "Content-Type": "application/json"},
            json=payload.model_dump(exclude_unset=True),
            timeout=settings.CMS_TIMEOUT_S,
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"cms unreachable: {exc}") from exc
    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="not found")
    if resp.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"cms error {resp.status_code}: {resp.text[:200]}")
    return resp.json()


@router.delete("/lessons/{lesson_id}", status_code=204)
def delete_lesson(
    lesson_id: int,
    _: User = Depends(require_role("admin", "teacher")),
):
    try:
        resp = httpx.delete(
            _cms_url(f"items/lessons/{lesson_id}"),
            headers=_cms_headers(),
            timeout=settings.CMS_TIMEOUT_S,
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"cms unreachable: {exc}") from exc
    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="not found")
    if resp.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"cms error {resp.status_code}")
    return Response(status_code=204)


# ---------------- attachments ----------------


@router.get("/lessons/{lesson_id}/attachments")
def list_attachments(
    lesson_id: int,
    _: User = Depends(get_current_user),
):
    return _proxy_get(f"items/lessons/{lesson_id}/attachments")


@router.post("/lessons/{lesson_id}/attachments", status_code=201)
async def upload_attachment(
    lesson_id: int,
    file: UploadFile = File(...),
    _: User = Depends(require_role("admin", "teacher")),
):
    data = await file.read()
    try:
        resp = httpx.post(
            _cms_url(f"items/lessons/{lesson_id}/attachments"),
            headers=_cms_headers(),
            files={
                "file": (
                    file.filename or "file",
                    data,
                    file.content_type or "application/octet-stream",
                )
            },
            timeout=settings.CMS_TIMEOUT_S,
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"cms unreachable: {exc}") from exc
    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="lesson not found")
    if resp.status_code == 413:
        raise HTTPException(status_code=413, detail=resp.json().get("detail", "file too large"))
    if resp.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=f"cms error {resp.status_code}: {resp.text[:200]}",
        )
    return resp.json()


@router.get("/lessons/{lesson_id}/attachments/{att_id}")
def download_attachment(
    lesson_id: int,
    att_id: int,
    _: User = Depends(get_current_user),
):
    url = _cms_url(f"items/lessons/{lesson_id}/attachments/{att_id}")
    try:
        client = httpx.Client(timeout=settings.CMS_TIMEOUT_S)
        req = client.build_request("GET", url, headers=_cms_headers())
        resp = client.send(req, stream=True)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"cms unreachable: {exc}") from exc
    if resp.status_code == 404:
        resp.close()
        client.close()
        raise HTTPException(status_code=404, detail="not found")
    if resp.status_code >= 400:
        code = resp.status_code
        resp.close()
        client.close()
        raise HTTPException(status_code=502, detail=f"cms error {code}")

    media_type = resp.headers.get("content-type", "application/octet-stream")
    content_disposition = resp.headers.get("content-disposition")

    def iterator():
        try:
            for chunk in resp.iter_bytes(chunk_size=64 * 1024):
                yield chunk
        finally:
            resp.close()
            client.close()

    headers = {}
    if content_disposition:
        headers["Content-Disposition"] = content_disposition
    return StreamingResponse(iterator(), media_type=media_type, headers=headers)


@router.delete("/lessons/{lesson_id}/attachments/{att_id}", status_code=204)
def delete_attachment(
    lesson_id: int,
    att_id: int,
    _: User = Depends(require_role("admin", "teacher")),
):
    try:
        resp = httpx.delete(
            _cms_url(f"items/lessons/{lesson_id}/attachments/{att_id}"),
            headers=_cms_headers(),
            timeout=settings.CMS_TIMEOUT_S,
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"cms unreachable: {exc}") from exc
    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="not found")
    if resp.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"cms error {resp.status_code}")
    return Response(status_code=204)