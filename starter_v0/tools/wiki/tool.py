"""Search Wikipedia articles using the public MediaWiki Action API."""
from __future__ import annotations

import html
import re
from typing import Any
from urllib.parse import quote

import requests


def wiki(query: str = "", lang: str = "vi", limit: int = 5) -> dict[str, Any]:
    if not isinstance(query, str) or not query.strip():
        return {"tool": "wiki", "error": "ValueError", "message": "query must be a non-empty string"}
    if not isinstance(lang, str) or lang not in {"vi", "en"}:
        return {"tool": "wiki", "error": "ValueError", "message": "lang must be vi or en"}
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 10:
        return {"tool": "wiki", "error": "ValueError", "message": "limit must be an integer from 1 to 10"}
    try:
        response = requests.get(
            f"https://{lang}.wikipedia.org/w/api.php",
            params={"action": "query", "list": "search", "srsearch": query.strip(), "srlimit": limit,
                    "srprop": "snippet", "format": "json", "formatversion": 2},
            headers={"User-Agent": "ResearchAgentToolEval/1.0 (educational research)"},
            timeout=15,
        )
        response.raise_for_status()
        rows = response.json().get("query", {}).get("search", [])
        if not isinstance(rows, list):
            raise ValueError("Unexpected Wikipedia response")
        items = []
        for row in rows[:limit]:
            if not isinstance(row, dict) or not isinstance(row.get("title"), str):
                continue
            title = row["title"]
            snippet = re.sub(r"<[^>]*>", "", str(row.get("snippet") or ""))
            items.append({"title": title, "url": f"https://{lang}.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}",
                          "source": f"{lang}.wikipedia.org", "summary": html.unescape(snippet)})
        return {"tool": "wiki", "query": query.strip(), "lang": lang, "items": items}
    except (requests.RequestException, ValueError, TypeError, AttributeError) as exc:
        return {"tool": "wiki", "error": type(exc).__name__, "message": str(exc)[:300]}
