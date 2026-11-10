"""Remove duplicate research sources without making a network request."""

from __future__ import annotations

from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


TRACKING_PARAMS = {"fbclid", "gclid", "mc_cid", "mc_eid"}


def _source_key(url: str) -> str:
    parts = urlsplit(url.strip())
    if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
        raise ValueError("Each source URL must be an absolute http(s) URL")
    query = sorted(
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in TRACKING_PARAMS
    )
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, urlencode(query), ""))


def dedupe_sources(items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    if not isinstance(items, list):
        return {"tool": "dedupe_sources", "error": "ValueError", "message": "items must be a list"}

    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    try:
        for item in items:
            if not isinstance(item, dict):
                raise ValueError("Each item must be an object")
            url = item.get("url")
            if not url:
                unique.append(item)
                continue
            if not isinstance(url, str):
                raise ValueError("Each source URL must be a string")
            key = _source_key(url)
            if key not in seen:
                seen.add(key)
                unique.append(item)
    except ValueError as exc:
        return {"tool": "dedupe_sources", "error": "ValueError", "message": str(exc)}

    return {
        "tool": "dedupe_sources",
        "items": unique,
        "unique_count": len(unique),
        "duplicate_count": len(items) - len(unique),
    }
