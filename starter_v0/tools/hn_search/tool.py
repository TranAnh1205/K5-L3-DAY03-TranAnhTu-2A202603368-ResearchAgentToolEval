"""Find Hacker News stories through HN Search by Algolia."""
from __future__ import annotations

from typing import Any

import requests


def hn_search(query: str = "", sort: str = "relevance", limit: int = 5) -> dict[str, Any]:
    if not isinstance(query, str) or not query.strip():
        return {"tool": "hn_search", "error": "ValueError", "message": "query must be a non-empty string"}
    if not isinstance(sort, str) or sort not in {"relevance", "date"}:
        return {"tool": "hn_search", "error": "ValueError", "message": "sort must be relevance or date"}
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 20:
        return {"tool": "hn_search", "error": "ValueError", "message": "limit must be an integer from 1 to 20"}
    endpoint = "search_by_date" if sort == "date" else "search"
    try:
        response = requests.get(f"https://hn.algolia.com/api/v1/{endpoint}",
                                params={"query": query.strip(), "tags": "story", "hitsPerPage": limit}, timeout=15)
        response.raise_for_status()
        rows = response.json().get("hits", [])
        if not isinstance(rows, list):
            raise ValueError("Unexpected Hacker News response")
        items = []
        for row in rows[:limit]:
            if not isinstance(row, dict) or not row.get("objectID"):
                continue
            discussion = f"https://news.ycombinator.com/item?id={row['objectID']}"
            items.append({"title": str(row.get("title") or "Untitled"), "url": row.get("url") or discussion,
                          "discussion_url": discussion, "source": "Hacker News",
                          "summary": f"{row.get('points') or 0} points, {row.get('num_comments') or 0} comments",
                          "points": row.get("points") or 0, "num_comments": row.get("num_comments") or 0})
        return {"tool": "hn_search", "query": query.strip(), "sort": sort, "items": items}
    except (requests.RequestException, ValueError, TypeError, AttributeError) as exc:
        return {"tool": "hn_search", "error": type(exc).__name__, "message": str(exc)[:300]}
