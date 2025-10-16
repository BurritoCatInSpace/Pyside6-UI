from __future__ import annotations


def needs_admin_for_plugin(is_windows: bool, requires_admin: bool, is_admin: bool) -> bool:
    """Predicate to decide whether admin is required for a plugin tab creation on Windows."""
    return bool(is_windows and requires_admin and not is_admin)


