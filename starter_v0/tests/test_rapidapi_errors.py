"""RapidAPI failures should identify the configuration problem without leaking keys."""

from __future__ import annotations

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS


def test_timeline_reports_subscription_error(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "fake-secret-key")
    fake_http(FakeResponse({"message": "You are not subscribed to this API."}, status_code=403))
    result = TOOL_FUNCTIONS["timeline"](screenname="sama", limit=1)
    assert result["error"] == "RuntimeError"
    assert "RapidAPI HTTP 403" in result["message"]
    assert "not subscribed" in result["message"]
    assert "fake-secret-key" not in result["message"]


def test_social_search_reports_rate_limit(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "fake-secret-key")
    fake_http(FakeResponse({"message": "Too many requests"}, status_code=429))
    result = TOOL_FUNCTIONS["social_search"](query="AI")
    assert result["error"] == "RuntimeError"
    assert "RapidAPI HTTP 429" in result["message"]
    assert "Too many requests" in result["message"]
