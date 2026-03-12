"""Authentication providers."""

from __future__ import annotations

import threading
import time
from typing import Protocol

import httpx


class AuthProvider(Protocol):
    """Protocol for authentication header injection."""

    def auth_headers(self) -> dict[str, str]: ...


class TokenAuth:
    """Static bearer-token authentication."""

    def __init__(self, token: str) -> None:
        self._token = token

    def auth_headers(self) -> dict[str, str]:
        return {"Authorization": self._token}

    def __repr__(self) -> str:
        return "TokenAuth(token='***')"


class OAuth2Auth:
    """OAuth2 client-credentials authentication with auto-refresh."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token_endpoint: str,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._token_endpoint = token_endpoint
        self._token: str | None = None
        self._expires_at: float = 0.0
        self._lock = threading.Lock()

    def auth_headers(self) -> dict[str, str]:
        token = self._get_token()
        return {"Authorization": f"Bearer {token}"}

    def _get_token(self) -> str:
        with self._lock:
            if self._token and time.time() < self._expires_at - 30:
                return self._token
            return self._refresh()

    def _refresh(self) -> str:
        resp = httpx.post(
            self._token_endpoint,
            data={
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        self._expires_at = time.time() + data.get("expires_in", 3600)
        return self._token  # type: ignore[return-value]

    def __repr__(self) -> str:
        return f"OAuth2Auth(client_id={self._client_id!r}, token_endpoint={self._token_endpoint!r})"
