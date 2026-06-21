"""Shared PicoCalc app key bindings."""

from __future__ import annotations

from .keys import Key, KeyPress


def is_app_exit_key(key: KeyPress | None) -> bool:
    """Return True for the standard app-level exit chord."""
    return key is not None and key.name == Key.F5 and key.ctrl
