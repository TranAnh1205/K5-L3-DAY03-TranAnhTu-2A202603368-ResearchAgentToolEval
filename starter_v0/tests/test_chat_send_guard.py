"""The model cannot authorize an external Telegram send on its own."""

from __future__ import annotations

from chat import run_model_tool_loop
from providers.base import ModelResponse, ToolCall
from tools.send.tool import send_telegram


class SendRequestProvider:
    def complete(self, *_args, **_kwargs) -> ModelResponse:
        return ModelResponse(tool_calls=[ToolCall(name="send", args={
            "text": "A draft for review",
            "confirmed": True,
        })])


def test_model_confirmed_flag_does_not_send(monkeypatch) -> None:
    def unexpected_send(**_kwargs):
        raise AssertionError("Telegram POST must wait for human approval")

    monkeypatch.setattr("chat.TOOL_FUNCTIONS", {"send": unexpected_send})
    result = run_model_tool_loop(
        provider=SendRequestProvider(),
        messages=[{"role": "user", "content": "Prepare a Telegram message"}],
        tools=[],
        model=None,
        max_tool_rounds=2,
    )
    assert result["status"] == "waiting_for_send_confirmation"
    assert result["pending_send"]["text"] == "A draft for review"
    assert result["tool_events"][0]["result"]["status"] == "awaiting_confirmation"


def test_send_error_does_not_expose_token(monkeypatch) -> None:
    secret = "123456789:example-secret-token"
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", secret)
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "test-chat")

    def failing_post(*_args, **_kwargs):
        raise RuntimeError(f"Request to https://api.telegram.org/bot{secret}/sendMessage failed")

    monkeypatch.setattr("tools.send.tool.requests.post", failing_post)
    result = send_telegram(text="Review approved", confirmed=True)
    assert result["error"] == "RuntimeError"
    assert secret not in result["message"]
    assert "[REDACTED]" in result["message"]
