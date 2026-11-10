def normalize_handle(screenname: str) -> dict:
    handle = screenname.strip().lstrip("@").lower()

    return {
        "screenname": handle
    }