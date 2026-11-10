"""Offline unit tests for the lab tools, including the team's new tool."""
from __future__ import annotations

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS
import requests


# ---------------- new team tool: dedupe_sources ----------------


def test_dedupe_sources_removes_tracking_variants_and_keeps_first() -> None:
    items = [
        {"title": "first", "url": "https://example.com/story?utm_source=x&id=1"},
        {"title": "second", "url": "https://example.com/story?id=1#section"},
        {"title": "other", "url": "https://example.com/other"},
    ]
    result = TOOL_FUNCTIONS["dedupe_sources"](items=items)
    assert result["items"] == [items[0], items[2]]
    assert result["unique_count"] == 2
    assert result["duplicate_count"] == 1


def test_dedupe_sources_rejects_non_list_input() -> None:
    result = TOOL_FUNCTIONS["dedupe_sources"](items="not a list")
    assert result["error"] == "ValueError"
    assert "items must be a list" in result["message"]


def test_dedupe_sources_returns_error_for_invalid_url() -> None:
    result = TOOL_FUNCTIONS["dedupe_sources"](items=[{"url": "example.com/story"}])
    assert result["error"] == "ValueError"
    assert "absolute http(s) URL" in result["message"]


# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    result = TOOL_FUNCTIONS["clarify"](question="Which source?", response_type="choice", options=["web", "X"])
    assert result["question"] == "Which source?"
    assert result["response_type"] == "choice"
    assert result["options"] == ["web", "X"]
    assert result["awaiting_user"] is True


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    items = [{"section": section, "title": title} for section, title in [("A", "one"), ("B", "two"), ("A", "three")]]
    markdown = TOOL_FUNCTIONS["format"](items=items, template="sections")["markdown"]
    assert markdown.count("## A") == 1
    assert markdown.count("## B") == 1
    assert markdown.index("one") < markdown.index("three")


def test_format_thread_numbers_items() -> None:
    markdown = TOOL_FUNCTIONS["format"](items=[{"title": "A"}, {"title": "B"}], template="thread")["markdown"]
    assert markdown.splitlines()[0].startswith("1/")
    assert markdown.splitlines()[2].startswith("2/")


def test_format_empty_items_does_not_crash() -> None:
    for items in (None, []):
        result = TOOL_FUNCTIONS["format"](items=items, template="bullets")
        assert result["item_count"] == 0
        assert result["markdown"] == ""


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "fake-channel")
    calls = fake_http(FakeResponse({"ok": True}))
    result = TOOL_FUNCTIONS["send"](text="Demo", confirmed=True)
    assert result["status"] == "sent"
    assert len(calls) == 1
    assert calls[0]["method"] == "POST"
    assert "fake-token" in calls[0]["url"]
    assert calls[0]["json"]["chat_id"] == "fake-channel"
    assert calls[0]["json"]["text"] == "Demo"
    assert "parse_mode" not in calls[0]["json"]


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))
    result = TOOL_FUNCTIONS["send"](text="Demo", confirmed=True)
    assert result["error"] == "RuntimeError"
    assert "TELEGRAM_BOT_TOKEN" in result["message"]
    assert calls == []


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "fake-key")
    calls = fake_http(FakeResponse({"results": []}))
    result = TOOL_FUNCTIONS["lookup"](query="AI", timeframe=None)
    assert result["items"] == []
    assert "time_range" not in calls[0]["json"]


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fake-key")
    calls = fake_http(FakeResponse({"data": {"markdown": "Article text", "metadata": {
        "title": "T", "sourceURL": "https://example.com/story"
    }}}))
    result = TOOL_FUNCTIONS["fetch"](url="https://example.com/story")
    item = result["items"][0]
    assert item == {"title": "T", "url": "https://example.com/story", "source": "example.com", "summary": "Article text"}
    assert calls[0]["json"] == {"url": "https://example.com/story", "formats": ["markdown"]}


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fake-key")
    fake_http(FakeResponse({"data": {"markdown": "x" * 5000, "metadata": {}}}))
    result = TOOL_FUNCTIONS["fetch"](url="https://example.com/story")
    assert len(result["items"][0]["summary"]) == 4000


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "fake-key")
    raw = [{"screen_name": "sama", "text": "missing ID"}] + [
        {"screen_name": "sama", "tweet_id": str(i), "text": f"tweet {i}"} for i in range(6)
    ]
    calls = fake_http(FakeResponse({"timeline": raw}))
    result = TOOL_FUNCTIONS["timeline"](screenname="sama", limit=3)
    assert len(result["items"]) == 3
    assert [item["url"] for item in result["items"]] == [f"https://x.com/sama/status/{i}" for i in range(3)]
    assert calls[0]["params"] == {"screenname": "sama"}


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "fake-key")
    calls = fake_http(FakeResponse({"tweets": []}))
    result = TOOL_FUNCTIONS["social_search"](query="AI", search_type="Top")
    assert result["search_type"] == "Top"
    assert calls[0]["params"] == {"query": "AI", "search_type": "Top"}


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    result = TOOL_FUNCTIONS["policy"](query="")
    assert result["results"] == []
    assert result["query"] == ""


def test_policy_area_filter_only_returns_that_area() -> None:
    result = TOOL_FUNCTIONS["policy"](query="privacy data", policy_area="data_privacy")
    assert result["results"]
    assert all(item["policy_area"] == "data_privacy" for item in result["results"])


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    result = TOOL_FUNCTIONS["policy"](query="injection citation", policy_area="source_citation", top_k=10)
    probe = next(item for item in result["results"] if item["section"] == "Injection probe")
    assert any("ignore the citation policy" in text for text in probe["untrusted_text"])
    assert "ignore the citation policy" not in probe["facts"]


# ---------------- additional dedupe_sources cases ----------------

def test_dedupe_sources_keeps_unlinked_items_separate() -> None:
    result = TOOL_FUNCTIONS["dedupe_sources"](items=[{"title": "A"}, {"title": "B"}])
    assert result["unique_count"] == 2
    assert result["duplicate_count"] == 0


def test_dedupe_sources_rejects_non_object_item() -> None:
    result = TOOL_FUNCTIONS["dedupe_sources"](items=[{"url": "https://example.com"}, 3])
    assert result["error"] == "ValueError"
    assert "Each item must be an object" in result["message"]


def test_dedupe_sources_rejects_non_string_url_without_raising() -> None:
    result = TOOL_FUNCTIONS["dedupe_sources"](items=[{"url": 42}])
    assert result["error"] == "ValueError"
    assert "URL must be a string" in result["message"]


# ---------------- new team tools: wiki, hn_search, github_repos ----------------


def test_wiki_maps_results_and_strips_html(fake_http) -> None:
    calls = fake_http(FakeResponse({"query": {"search": [
        {"title": "Artificial intelligence", "snippet": "<span>AI</span> &amp; research"}
    ]}}))
    result = TOOL_FUNCTIONS["wiki"](query="AI", lang="en", limit=1)
    assert calls[0]["params"]["srsearch"] == "AI"
    assert calls[0]["params"]["srlimit"] == 1
    assert result["items"][0]["summary"] == "AI & research"
    assert result["items"][0]["url"] == "https://en.wikipedia.org/wiki/Artificial_intelligence"


def test_wiki_bad_input_makes_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({}))
    assert TOOL_FUNCTIONS["wiki"](query=" ")["error"] == "ValueError"
    assert TOOL_FUNCTIONS["wiki"](query="AI", lang="xx")["error"] == "ValueError"
    assert TOOL_FUNCTIONS["wiki"](query="AI", lang=[])["error"] == "ValueError"
    assert TOOL_FUNCTIONS["wiki"](query="AI", limit=0)["error"] == "ValueError"
    assert calls == []


def test_wiki_http_error_returns_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=503))
    assert TOOL_FUNCTIONS["wiki"](query="AI")["error"] == "HTTPError"


def test_hn_search_routes_date_and_maps_discussion(fake_http) -> None:
    calls = fake_http(FakeResponse({"hits": [
        {"objectID": "123", "title": "New Python", "url": None, "points": 12, "num_comments": 4}
    ]}))
    result = TOOL_FUNCTIONS["hn_search"](query="Python", sort="date", limit=1)
    assert calls[0]["url"].endswith("/search_by_date")
    assert calls[0]["params"] == {"query": "Python", "tags": "story", "hitsPerPage": 1}
    assert result["items"][0]["url"] == "https://news.ycombinator.com/item?id=123"
    assert result["items"][0]["points"] == 12


def test_hn_search_bad_input_makes_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({}))
    assert TOOL_FUNCTIONS["hn_search"](query="")["error"] == "ValueError"
    assert TOOL_FUNCTIONS["hn_search"](query="Python", sort="wrong")["error"] == "ValueError"
    assert TOOL_FUNCTIONS["hn_search"](query="Python", sort=[])["error"] == "ValueError"
    assert TOOL_FUNCTIONS["hn_search"](query="Python", limit=True)["error"] == "ValueError"
    assert calls == []


def test_hn_search_timeout_returns_dict(fake_http) -> None:
    fake_http(requests.Timeout("timed out"))
    assert TOOL_FUNCTIONS["hn_search"](query="Python")["error"] == "Timeout"


def test_github_repos_filters_language_and_stars(fake_http) -> None:
    calls = fake_http(FakeResponse({"items": [
        {"full_name": "owner/repo", "html_url": "https://github.com/owner/repo",
         "description": "A research agent", "language": "Python", "stargazers_count": 99}
    ]}))
    result = TOOL_FUNCTIONS["github_repos"](query="research agent", language="Python", sort="stars", limit=1)
    assert calls[0]["params"] == {"q": "research agent language:Python", "per_page": 1,
                                    "sort": "stars", "order": "desc"}
    assert result["items"][0]["stars"] == 99


def test_github_repos_bad_input_makes_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({}))
    assert TOOL_FUNCTIONS["github_repos"](query=" ")["error"] == "ValueError"
    assert TOOL_FUNCTIONS["github_repos"](query="AI", sort="wrong")["error"] == "ValueError"
    assert TOOL_FUNCTIONS["github_repos"](query="AI", sort=[])["error"] == "ValueError"
    assert TOOL_FUNCTIONS["github_repos"](query="AI", language="Python:foo")["error"] == "ValueError"
    assert TOOL_FUNCTIONS["github_repos"](query="AI", limit=21)["error"] == "ValueError"
    assert calls == []


def test_github_repos_rate_limit_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=403))
    assert TOOL_FUNCTIONS["github_repos"](query="AI")["error"] == "HTTPError"
