"""Search public GitHub repositories."""
from __future__ import annotations

from typing import Any

import requests


def github_repos(query: str = "", language: str = "", sort: str = "best_match", limit: int = 5) -> dict[str, Any]:
    if not isinstance(query, str) or not query.strip():
        return {"tool": "github_repos", "error": "ValueError", "message": "query must be a non-empty string"}
    if not isinstance(language, str) or any(char in language for char in "\r\n:"):
        return {"tool": "github_repos", "error": "ValueError", "message": "language must be a plain string"}
    if not isinstance(sort, str) or sort not in {"best_match", "stars", "updated"}:
        return {"tool": "github_repos", "error": "ValueError", "message": "sort must be best_match, stars or updated"}
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 20:
        return {"tool": "github_repos", "error": "ValueError", "message": "limit must be an integer from 1 to 20"}
    search_query = query.strip() + (f" language:{language.strip()}" if language.strip() else "")
    params: dict[str, Any] = {"q": search_query, "per_page": limit}
    if sort != "best_match":
        params.update({"sort": "stars" if sort == "stars" else "updated", "order": "desc"})
    try:
        response = requests.get("https://api.github.com/search/repositories", params=params,
                                headers={"Accept": "application/vnd.github+json",
                                         "User-Agent": "ResearchAgentToolEval/1.0"}, timeout=15)
        response.raise_for_status()
        rows = response.json().get("items", [])
        if not isinstance(rows, list):
            raise ValueError("Unexpected GitHub response")
        items = []
        for row in rows[:limit]:
            if not isinstance(row, dict) or not isinstance(row.get("html_url"), str):
                continue
            items.append({"title": row.get("full_name") or row.get("name") or "Repository",
                          "url": row["html_url"], "source": "GitHub",
                          "summary": row.get("description") or "", "language": row.get("language"),
                          "stars": row.get("stargazers_count") or 0, "updated_at": row.get("updated_at")})
        return {"tool": "github_repos", "query": query.strip(), "language": language.strip(),
                "sort": sort, "items": items}
    except (requests.RequestException, ValueError, TypeError, AttributeError) as exc:
        return {"tool": "github_repos", "error": type(exc).__name__, "message": str(exc)[:300]}
