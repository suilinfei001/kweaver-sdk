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


class PasswordAuth:
    """Browser-based OAuth2 login with auto-refresh.

    Uses Playwright (headless) to automate the Ory OAuth2 login flow:
      1. GET {base_url}/api/dip-hub/v1/login → OAuth2 redirect → signin page
      2. Fill account/password → click login
      3. Extract dip.oauth2_token cookie after callback

    Token is cached and refreshed on demand when expired or on auth error.
    Requires: ``pip install playwright && playwright install chromium``
    """

    # Refresh every 4 minutes (Ory tokens expire in ~5 min)
    _REFRESH_INTERVAL = 240

    def __init__(self, base_url: str, username: str, password: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._username = username
        self._password = password
        self._token: str | None = None
        self._expires_at: float = 0.0
        self._lock = threading.Lock()

    def auth_headers(self) -> dict[str, str]:
        with self._lock:
            if self._token is None or time.time() >= self._expires_at:
                self._refresh()
            return {"Authorization": f"Bearer {self._token}"}

    def refresh(self) -> str:
        """Force a token refresh and return the new token."""
        with self._lock:
            return self._refresh()

    def _refresh(self) -> str:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            page.goto(
                f"{self._base_url}/api/dip-hub/v1/login",
                wait_until="networkidle",
                timeout=30000,
            )

            page.fill('input[name="account"]', self._username)
            page.fill('input[name="password"]', self._password)
            page.click("button.ant-btn-primary")

            token = None
            for _ in range(30):
                time.sleep(1)
                for cookie in context.cookies():
                    if cookie["name"] == "dip.oauth2_token":
                        token = cookie["value"]
                        break
                if token:
                    break

            browser.close()

        if not token:
            raise RuntimeError(
                "Failed to extract ADP token after browser login. "
                "Check username/password."
            )

        self._token = token
        self._expires_at = time.time() + self._REFRESH_INTERVAL
        return token

    def __repr__(self) -> str:
        return f"PasswordAuth(username={self._username!r})"


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
