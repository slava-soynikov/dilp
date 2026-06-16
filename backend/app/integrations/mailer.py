"""Mock mailer. Replace with real SMTP/SendGrid integration when provider is configured.

Tests inspect `outbox` to assert that messages were sent.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)

outbox: list[dict[str, Any]] = []


def _send(to: str, purpose: str, token: str, subject: str) -> None:
    msg = {"to": to, "purpose": purpose, "token": token, "subject": subject}
    outbox.append(msg)
    logger.info("mailer.mock send to=%s purpose=%s", to, purpose)


def send_password_reset(to: str, token: str) -> None:
    _send(to, "reset_password", token, "Reset your password")


def send_teacher_invite(to: str, temp_password: str) -> None:
    _send(to, "teacher_invite", temp_password, "Welcome to DILP — set your password")