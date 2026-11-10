from typing import Any


def confirm_action(
    action: str = "",
    details: str = "",
    question: str = "Bạn có chắc chắn muốn thực hiện hành động này không?"
) -> dict[str, Any]:
    if not action or not isinstance(action, str):
        return {
            "error": "ValueError",
            "message": "action must be a non-empty string",
            "tool": "confirm_action",
        }
    return {
        "tool": "confirm_action",
        "action": action,
        "details": details or "",
        "question": question,
        "awaiting_user": True,
    }
