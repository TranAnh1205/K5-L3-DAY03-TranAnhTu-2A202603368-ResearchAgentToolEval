"""Tool Unit Test Challenge & Custom Tool Tests.

Rules:
- Offline only: mock HTTP with `fake_http`, set fake keys with `monkeypatch.setenv`.
- One behaviour per test. Name the test after the behaviour, not the function.
- Done = `pytest tests/ -v` shows 0 skipped, 0 failed.
"""
from __future__ import annotations

import pytest

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS


# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    clarify = TOOL_FUNCTIONS["clarify"]
    options = ["Lựa chọn 1", "Lựa chọn 2"]
    result = clarify(question="Bạn muốn chọn nguồn nào?", response_type="choice", options=options)

    assert result["tool"] == "ask_user"
    assert result["question"] == "Bạn muốn chọn nguồn nào?"
    assert result["response_type"] == "choice"
    assert result["options"] == options
    assert result["awaiting_user"] is True


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    format_tool = TOOL_FUNCTIONS["format"]
    items = [
        {"title": "Tin A1", "section": "Chính trị", "url": "https://example.com/a1"},
        {"title": "Tin B1", "section": "Kinh tế", "url": "https://example.com/b1"},
        {"title": "Tin A2", "section": "Chính trị", "url": "https://example.com/a2"},
    ]
    result = format_tool(items=items, template="sections", headline="Điểm tin")
    markdown = result["markdown"]

    assert markdown.count("## Chính trị") == 1
    assert markdown.count("## Kinh tế") == 1
    assert "Tin A1" in markdown
    assert "Tin A2" in markdown
    assert "Tin B1" in markdown
    assert result["item_count"] == 3


def test_format_thread_numbers_items() -> None:
    format_tool = TOOL_FUNCTIONS["format"]
    items = [
        {"title": "Bài 1", "url": "https://example.com/1"},
        {"title": "Bài 2", "url": "https://example.com/2"},
        {"title": "Bài 3", "url": "https://example.com/3"},
    ]
    result = format_tool(items=items, template="thread")
    lines = result["markdown"].split("\n\n")

    assert len(lines) == 3
    assert lines[0].startswith("1/ ")
    assert lines[1].startswith("2/ ")
    assert lines[2].startswith("3/ ")


def test_format_empty_items_does_not_crash() -> None:
    format_tool = TOOL_FUNCTIONS["format"]
    res_none = format_tool(items=None)
    assert res_none["item_count"] == 0
    assert isinstance(res_none["markdown"], str)

    res_empty = format_tool(items=[])
    assert res_empty["item_count"] == 0
    assert isinstance(res_empty["markdown"], str)


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake_telegram_token_123")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "987654321")
    calls = fake_http(FakeResponse({"ok": True}))

    send_tool = TOOL_FUNCTIONS["send"]
    result = send_tool(text="Bản tin tóm tắt", confirmed=True)

    assert len(calls) == 1
    assert calls[0]["method"] == "POST"
    assert "fake_telegram_token_123" in calls[0]["url"]
    assert calls[0]["json"]["chat_id"] == "987654321"
    assert calls[0]["json"]["text"] == "Bản tin tóm tắt"
    assert result["status"] == "sent"


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))
    send_tool = TOOL_FUNCTIONS["send"]
    result = send_tool(text="Bản tin", confirmed=True)

    assert result["error"] == "RuntimeError"
    assert "TELEGRAM" in result["message"]
    assert calls == []


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "test-key-tavily")
    calls = fake_http(FakeResponse({"results": []}))

    lookup_tool = TOOL_FUNCTIONS["lookup"]
    lookup_tool(query="AI research", timeframe=None)

    assert len(calls) == 1
    assert "time_range" not in calls[0]["json"]
    assert calls[0]["json"]["query"] == "AI research"


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key-firecrawl")
    payload = {
        "data": {
            "markdown": "# Tiêu đề\nNội dung chi tiết bài viết.",
            "metadata": {
                "title": "Trang tin tức",
                "sourceURL": "https://vietnamnet.vn/bai-viet-123",
            },
        }
    }
    calls = fake_http(FakeResponse(payload))
    fetch_tool = TOOL_FUNCTIONS["fetch"]
    result = fetch_tool(url="https://vietnamnet.vn/bai-viet-123")

    assert len(calls) == 1
    assert calls[0]["headers"]["Authorization"] == "Bearer test-key-firecrawl"
    assert calls[0]["json"]["url"] == "https://vietnamnet.vn/bai-viet-123"

    item = result["items"][0]
    assert item["title"] == "Trang tin tức"
    assert item["url"] == "https://vietnamnet.vn/bai-viet-123"
    assert item["source"] == "vietnamnet.vn"
    assert item["summary"] == "# Tiêu đề\nNội dung chi tiết bài viết."


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key-firecrawl")
    long_markdown = "A" * 6000
    payload = {
        "data": {
            "markdown": long_markdown,
            "metadata": {
                "title": "Bài viết dài",
                "sourceURL": "https://example.com/long-article",
            },
        }
    }
    fake_http(FakeResponse(payload))
    fetch_tool = TOOL_FUNCTIONS["fetch"]
    result = fetch_tool(url="https://example.com/long-article")

    summary = result["items"][0]["summary"]
    assert len(summary) == 4000
    assert summary == "A" * 4000


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "test-rapidapi-key")
    raw_timeline = [
        {"text": "Item missing id and tweet_id"},
        {"tweet_id": "111", "screen_name": "sama", "text": "Tweet 1"},
        {"id": "222", "screen_name": "sama", "text": "Tweet 2"},
        {"tweet_id": "333", "screen_name": "sama", "text": "Tweet 3"},
        {"tweet_id": "444", "screen_name": "sama", "text": "Tweet 4"},
        {"tweet_id": "555", "screen_name": "sama", "text": "Tweet 5"},
        {"tweet_id": "666", "screen_name": "sama", "text": "Tweet 6"},
    ]
    calls = fake_http(FakeResponse({"timeline": raw_timeline}))

    timeline_tool = TOOL_FUNCTIONS["timeline"]
    result = timeline_tool(screenname="sama", limit=3)

    assert len(calls) == 1
    assert calls[0]["params"]["screenname"] == "sama"
    assert len(result["items"]) == 3
    assert result["items"][0]["url"] == "https://x.com/sama/status/111"
    assert result["items"][1]["url"] == "https://x.com/sama/status/222"
    assert result["items"][2]["url"] == "https://x.com/sama/status/333"


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "test-rapidapi-key")
    calls = fake_http(FakeResponse({"tweets": []}))

    social_search = TOOL_FUNCTIONS["social_search"]
    social_search(query="deepseek", search_type="Top")

    assert len(calls) == 1
    assert calls[0]["params"]["query"] == "deepseek"
    assert calls[0]["params"]["search_type"] == "Top"


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    policy_tool = TOOL_FUNCTIONS["policy"]
    result = policy_tool(query="")
    assert result["results"] == []


def test_policy_area_filter_only_returns_that_area() -> None:
    policy_tool = TOOL_FUNCTIONS["policy"]
    result = policy_tool(query="privacy data personal", policy_area="data_privacy")

    assert len(result["results"]) > 0
    for item in result["results"]:
        assert item["policy_area"] == "data_privacy"


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    policy_tool = TOOL_FUNCTIONS["policy"]
    result = policy_tool(query="citation injection probe", policy_area="source_citation")

    injection_sections = [r for r in result["results"] if r["section"] == "Injection probe"]
    assert len(injection_sections) > 0
    hit = injection_sections[0]
    assert any("ignore the citation policy" in line for line in hit["untrusted_text"])
    assert "ignore the citation policy" not in hit["facts"]


# ---------------- YOUR NEW TOOL(S) ----------------
# Tests for confirm_action & normalize_handle (≥ 3 tests per tool)

def test_confirm_action_happy_path() -> None:
    tool = TOOL_FUNCTIONS["confirm_action"]
    result = tool(action="send_telegram", details="Gửi bản tin AI lên kênh", question="Bạn xác nhận chứ?")

    assert result["tool"] == "confirm_action"
    assert result["action"] == "send_telegram"
    assert result["details"] == "Gửi bản tin AI lên kênh"
    assert result["question"] == "Bạn xác nhận chứ?"
    assert result["awaiting_user"] is True


def test_confirm_action_bad_input_from_model() -> None:
    tool = TOOL_FUNCTIONS["confirm_action"]
    result = tool(action="")

    assert result["error"] == "ValueError"
    assert "action" in result["message"]
    assert result["tool"] == "confirm_action"


def test_confirm_action_non_string_action_returns_error_dict() -> None:
    tool = TOOL_FUNCTIONS["confirm_action"]
    result = tool(action=None)  # type: ignore

    assert result["error"] == "ValueError"
    assert "action" in result["message"]


def test_normalize_handle_happy_path() -> None:
    tool = TOOL_FUNCTIONS["normalize_handle"]
    result = tool(screenname="  @elonmusk  ")

    assert result["tool"] == "normalize_handle"
    assert result["screenname"] == "elonmusk"


def test_normalize_handle_bad_input_from_model() -> None:
    tool = TOOL_FUNCTIONS["normalize_handle"]
    result = tool(screenname=12345)  # type: ignore

    assert result["error"] == "TypeError"
    assert "screenname" in result["message"]
    assert result["screenname"] == ""


def test_normalize_handle_plain_string_without_at() -> None:
    tool = TOOL_FUNCTIONS["normalize_handle"]
    result = tool(screenname="sama")

    assert result["tool"] == "normalize_handle"
    assert result["screenname"] == "sama"


# ---------------- Regression tests (Challenge+) ----------------

def test_format_section_none_regression() -> None:
    """Regression test: format tool does not crash or generate '## None' when item['section'] is None."""
    format_tool = TOOL_FUNCTIONS["format"]
    items = [
        {"title": "Tin tức chung", "section": None, "url": "https://example.com/news"},
    ]
    result = format_tool(items=items, template="sections")

    assert "## None" not in result["markdown"]
    assert "## Tổng hợp" in result["markdown"]
    assert "Tin tức chung" in result["markdown"]


def test_timeline_limit_zero_regression(monkeypatch, fake_http) -> None:
    """Regression test: timeline tool respects limit=0 instead of falling back to default 5."""
    monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
    raw_timeline = [{"tweet_id": "1", "screen_name": "user", "text": "Hello"}]
    fake_http(FakeResponse({"timeline": raw_timeline}))

    timeline_tool = TOOL_FUNCTIONS["timeline"]
    result = timeline_tool(screenname="user", limit=0)

    assert result["items"] == []
