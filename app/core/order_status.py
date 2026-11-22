ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "new": {"in_progress", "canceled"},
    "in_progress": {"ready", "canceled"},
    "ready": {"completed"},
    "canceled": set(),
    "completed": set(),
}
