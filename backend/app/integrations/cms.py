"""Vendor-agnostic CMS client (currently targets Directus).

`content_ref` is the path appended to `{CMS_BASE_URL}/`, e.g.
`"items/lessons/1"` or `"items/lessons?filter[slug][_eq]=abc"`. The Platform
Core stays agnostic of CMS-specific collection naming — the lesson author
decides what path to store.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class CMSError(Exception):
    """Raised when the CMS cannot fulfil a content fetch."""


class CMSClient:
    def __init__(
        self,
        base_url: str | None = None,
        token: str | None = None,
        timeout_s: float | None = None,
    ):
        self.base_url = (base_url or settings.CMS_BASE_URL).rstrip("/")
        self.token = token or settings.CMS_TOKEN
        self.timeout_s = timeout_s if timeout_s is not None else settings.CMS_TIMEOUT_S

    def get_content(self, content_ref: str) -> dict[str, Any]:
        if not content_ref:
            raise CMSError("empty content_ref")
        url = f"{self.base_url}/{content_ref.lstrip('/')}"
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            resp = httpx.get(url, headers=headers, timeout=self.timeout_s)
        except httpx.HTTPError as exc:
            logger.warning("cms.fetch failed url=%s err=%s", url, exc)
            raise CMSError(f"cms unreachable: {exc}") from exc
        if resp.status_code == 404:
            raise CMSError(f"content not found: {content_ref}")
        if resp.status_code >= 400:
            raise CMSError(f"cms error {resp.status_code}: {resp.text[:200]}")
        try:
            return resp.json()
        except ValueError as exc:
            raise CMSError("cms returned non-json") from exc


_singleton: CMSClient | None = None


def get_cms_client() -> CMSClient:
    """FastAPI dependency. Returns a process-wide singleton.

    Tests override via `app.dependency_overrides[get_cms_client]`.
    """
    global _singleton
    if _singleton is None:
        _singleton = CMSClient()
    return _singleton