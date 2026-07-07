"""Approval guardrails for calendar mutations."""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass


@dataclass
class ApprovalGrant:
    token: str
    action: str
    expires_at: float


class CalendarApprovalStore:
    """In-memory approval tokens for calendar write operations."""

    def __init__(self, ttl_seconds: int = 300) -> None:
        self.ttl_seconds = ttl_seconds
        self._grants: dict[str, ApprovalGrant] = {}

    def request_approval(self, action: str) -> ApprovalGrant:
        self._purge_expired()
        token = secrets.token_urlsafe(16)
        grant = ApprovalGrant(token=token, action=action, expires_at=time.time() + self.ttl_seconds)
        self._grants[token] = grant
        return grant

    def consume(self, token: str, action: str) -> bool:
        self._purge_expired()
        grant = self._grants.get(token)
        if not grant or grant.action != action:
            return False
        if grant.expires_at < time.time():
            self._grants.pop(token, None)
            return False
        self._grants.pop(token, None)
        return True

    def is_valid(self, token: str, action: str) -> bool:
        self._purge_expired()
        grant = self._grants.get(token)
        return bool(grant and grant.action == action and grant.expires_at >= time.time())

    def _purge_expired(self) -> None:
        now = time.time()
        expired = [k for k, g in self._grants.items() if g.expires_at < now]
        for key in expired:
            self._grants.pop(key, None)


approval_store = CalendarApprovalStore()
