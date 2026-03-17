"""Reusable pre-condition checks for tool functions.

These helpers reduce boilerplate by centralizing the common pattern of
checking connection state, session state, and page existence.  Each
function returns ``None`` when the check passes, or a JSON error string
when it fails -- ready to be returned directly by the calling tool.
"""
from __future__ import annotations

from typing import Optional

from .db import db
from .session import session
from .utils import _json


def require_connection() -> Optional[str]:
    """Return an error JSON string if the database is not connected, else ``None``."""
    if not db.is_connected():
        return _json({"status": "error", "error": "Not connected. Call apex_connect() first."})
    return None


def require_session() -> Optional[str]:
    """Return an error JSON string if no import session is active, else ``None``.

    Also checks the database connection first.
    """
    err = require_connection()
    if err:
        return err
    if not session.import_begun:
        return _json({"status": "error", "error": "No import session active. Call apex_create_app() first."})
    return None


def require_page(page_id: int) -> Optional[str]:
    """Return an error JSON string if the page does not exist in the session.

    Also checks connection and session state.
    """
    err = require_session()
    if err:
        return err
    if page_id not in session.pages:
        return _json({"status": "error", "error": f"Page {page_id} not found in current session. Call apex_add_page() first."})
    return None
