"""Thin async client for the existing Tcherly Node API.

Every call forwards the teacher's own `Authorization: Bearer <jwt>` header, so
the Node app's authentication and lesson-ownership checks still apply: the
assistant can only ever see lessons the logged-in teacher owns.
"""
from typing import Any

import httpx

from .config import settings


class TcherlyAPIError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(f"Tcherly API {status}: {message}")
        self.status = status


class TcherlyClient:
    def __init__(self, authorization: str, base_url: str | None = None):
        self._http = httpx.AsyncClient(
            base_url=base_url or settings.tcherly_api_url,
            headers={"Authorization": authorization},
            timeout=30,
        )
        self._reason_labels: dict[str, dict[str, str]] | None = None

    async def aclose(self) -> None:
        await self._http.aclose()

    async def _get(self, path: str, **params: Any) -> dict:
        response = await self._http.get(path, params=params or None)
        if response.status_code in (401, 403):
            raise TcherlyAPIError(response.status_code, "not authorised for this resource")
        if response.status_code == 404:
            raise TcherlyAPIError(404, "not found")
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and data.get("success") is False:
            raise TcherlyAPIError(404, data.get("message") or "request failed")
        return data

    async def lesson(self, lesson_id: str) -> dict:
        return (await self._get(f"/lessons/{lesson_id}"))["lesson"]

    async def feedback(self, lesson_id: str, start_min: int, end_min: int) -> dict:
        """Analytics for minutes (start_min, end_min] - same semantics as the dashboard sliders."""
        data = await self._get(f"/lessons/{lesson_id}/feedback", min=start_min, max=end_min)
        return {"lesson": data["lesson"], "feedback": data["feedback"]}

    async def course(self, course_id: str) -> dict:
        return (await self._get(f"/courses/{course_id}"))["course"]

    async def add_bookmark(self, lesson_object_id: str, bookmark: dict) -> dict:
        """Create a Tcherly bookmark (Save your analysis) with a question and optional action."""
        response = await self._http.put(f"/lessons/{lesson_object_id}/bookmark/add", json=bookmark)
        if response.status_code in (401, 403):
            raise TcherlyAPIError(response.status_code, "not authorised for this lesson")
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            raise TcherlyAPIError(400, data.get("message") or "couldn't save the bookmark")
        return data["current_bookmark"]

    async def reason_labels(self) -> dict[str, dict[str, str]]:
        if self._reason_labels is None:
            options = (await self._get("/misc/columns"))["options"]
            self._reason_labels = {state: {o["id"]: o["name"] for o in opts} for state, opts in options.items()}
        return self._reason_labels


async def sign_in(email: str, password: str, base_url: str | None = None) -> str:
    """Log in as a teacher and return the `Bearer <jwt>` header value (used by the CLI)."""
    async with httpx.AsyncClient(base_url=base_url or settings.tcherly_api_url, timeout=30) as http:
        response = await http.post("/auth/signin", json={"email": email, "password": password})
        if response.status_code != 200:
            raise TcherlyAPIError(response.status_code, "sign-in failed (check email/password)")
        return response.json()["jwt_token"]
