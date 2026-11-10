from typing import Any

def confirm_action(
    action: str,
    details: str = ""
) -> dict[str, Any]:

    return {
        "tool": "confirm_action",
        "action": action,
        "details": details,
        "awaiting_user": True
    }