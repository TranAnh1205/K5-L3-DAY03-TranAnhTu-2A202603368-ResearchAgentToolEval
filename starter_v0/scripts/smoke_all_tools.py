"""Safely exercise each registered tool and save a key-free status report.

The send tool is always called with confirmed=False, so this script never
posts to Telegram. Missing external API keys are reported without using them.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from env_loader import load_lab_env  # noqa: E402
from tools import TOOL_FUNCTIONS  # noqa: E402
from versioning import build_artifact_version  # noqa: E402


REQUIRED_ENV = {
    "lookup": ("TAVILY_API_KEY",),
    "fetch": ("FIRECRAWL_API_KEY",),
    "timeline": ("RAPIDAPI_KEY",),
    "social_search": ("RAPIDAPI_KEY",),
}

EXAMPLES = {
    "clarify": {"question": "Which account?", "response_type": "text"},
    "dedupe_sources": {"items": [
        {"url": "https://example.com/story?utm_source=demo"},
        {"url": "https://example.com/story"},
    ]},
    "format": {"items": [{"title": "Example", "url": "https://example.com", "summary": "A source"}], "template": "bullets"},
    "policy": {"query": "source citation", "policy_area": "source_citation"},
    "lookup": {"query": "OpenAI", "topic": "news", "timeframe": "week", "max_results": 2},
    "fetch": {"url": "https://www.python.org/about/"},
    "papers": {"query": "transformer attention", "max_results": 1},
    "paper_text": {"arxiv_url": "https://arxiv.org/abs/1706.03762", "max_pages": 1, "max_chars": 1000},
    "timeline": {"screenname": "sama", "limit": 1},
    "social_search": {"query": "AI", "limit": 1},
    "send": {"text": "Smoke test: never send", "confirmed": False},
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Check all tools without sending Telegram messages.")
    parser.add_argument("--output", type=Path, default=ROOT / "analysis" / "tool_smoke.json")
    parser.add_argument("--only", nargs="+", choices=list(TOOL_FUNCTIONS), help="Run only the named tools.")
    args = parser.parse_args()
    load_lab_env(ROOT)

    artifact = build_artifact_version("tool-smoke", ROOT / "artifacts" / "system_prompt.md", ROOT / "artifacts" / "tools.yaml")
    rows = []
    for name in args.only or TOOL_FUNCTIONS:
        missing = [key for key in REQUIRED_ENV.get(name, ()) if not os.getenv(key)]
        if missing:
            rows.append({"tool": name, "status": "missing_env", "missing_env": missing})
            continue
        started = time.monotonic()
        try:
            result = TOOL_FUNCTIONS[name](**EXAMPLES[name])
            status = "guarded" if name == "send" and result.get("status") == "needs_confirmation" else (
                "error" if result.get("error") else "completed"
            )
            rows.append({
                "tool": name,
                "status": status,
                "error_type": result.get("error"),
                "rapidapi_http_status": int(match.group(1)) if (match := re.match(r"RapidAPI HTTP (\d+):", str(result.get("message") or ""))) else None,
                "item_count": len(result["items"]) if isinstance(result.get("items"), list) else None,
                "result_count": len(result["results"]) if isinstance(result.get("results"), list) else None,
                "elapsed_seconds": round(time.monotonic() - started, 2),
            })
        except Exception as exc:
            rows.append({
                "tool": name,
                "status": "error",
                "error_type": type(exc).__name__,
                "elapsed_seconds": round(time.monotonic() - started, 2),
            })

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "artifact_version": artifact.artifact_version,
        "note": "No Telegram message is sent. API keys and tool response content are not recorded.",
        "tools": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    for row in rows:
        print(f"{row['tool']}: {row['status']}" + (f" ({row['error_type']})" if row.get("error_type") else ""))
    print(f"Saved: {args.output}")


if __name__ == "__main__":
    main()
