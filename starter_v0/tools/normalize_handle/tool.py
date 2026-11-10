from typing import Any


def normalize_handle(screenname: str = "") -> dict[str, Any]:
    if not isinstance(screenname, str):
        return {
            "error": "TypeError",
            "message": "screenname must be a string",
            "tool": "normalize_handle",
            "screenname": "",
        }
    handle = screenname.strip().lstrip("@").strip()
    return {
        "tool": "normalize_handle",
        "screenname": handle,
    }
