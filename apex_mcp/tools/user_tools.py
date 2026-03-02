"""Tools: apex_create_user, apex_list_users."""
from __future__ import annotations
import json
from ..db import db
from ..config import WORKSPACE_ID
from ..utils import _json,  _esc, _blk


def apex_create_user(
    username: str,
    password: str,
    email: str = "",
    first_name: str = "",
    last_name: str = "",
    workspace_id: int | None = None,
) -> str:
    """Create an APEX workspace user account.

    Args:
        username: Login username (alphanumeric, dots, underscores allowed).
                  Best practice: use format "firstname.lastname" or "dept.role".
        password: Initial password. Must meet APEX complexity requirements:
                  - Minimum 6 characters
                  - Mix of upper/lowercase recommended
                  - Special characters allowed
        email: User email address (used for password reset).
        first_name: User first name.
        last_name: User last name.
        workspace_id: Workspace ID (defaults to configured workspace).

    Returns:
        JSON with status and user details.

    Note: This creates an APEX workspace user (for APEX Accounts authentication).
    For custom authentication schemes (custom login PL/SQL), manage users in
    your own application table instead.

    Requires:
        - Connection as APEX workspace admin or schema with APEX admin privileges
        - User must have EXECUTE on apex_util package
    """
    if not db.is_connected():
        return _json({"status": "error", "error": "Not connected. Call apex_connect() first."})

    effective_ws_id = workspace_id if workspace_id is not None else WORKSPACE_ID

    if not username or not username.strip():
        return _json({"status": "error", "error": "username is required."})
    if not password or len(password) < 6:
        return _json({"status": "error", "error": "password must be at least 6 characters."})

    try:
        # Set workspace context before calling apex_util
        db.plsql(_blk(f"""
  apex_util.set_workspace(
    p_workspace => (
      SELECT workspace
        FROM apex_workspaces
       WHERE workspace_id = {effective_ws_id}
         AND rownum = 1
    )
  );"""))

        db.plsql(_blk(f"""
apex_util.create_user(
  p_user_name                => '{_esc(username.strip())}'
 ,p_web_password             => '{_esc(password)}'
 ,p_email_address            => '{_esc(email)}'
 ,p_first_name               => '{_esc(first_name)}'
 ,p_last_name                => '{_esc(last_name)}'
 ,p_developer_privs          => 'NONE'
 ,p_default_schema           => NULL
 ,p_change_password_on_first_use => 'N'
 ,p_account_locked           => 'N'
 ,p_account_expiry           => NULL
);"""))

        return _json({
            "status": "ok",
            "message": f"User '{username}' created successfully.",
            "username": username,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "workspace_id": effective_ws_id,
            "note": (
                "This is an APEX Accounts workspace user. "
                "Use apex_list_users() to verify the account was created."
            ),
        })

    except Exception as e:
        err = str(e)
        # Provide a friendlier message for common errors
        if "ORA-20987" in err or "already exists" in err.lower():
            return _json({
                "status": "error",
                "error": f"User '{username}' already exists in this workspace.",
                "detail": err,
            })
        return _json({"status": "error", "error": err})


def apex_list_users(workspace_id: int | None = None) -> str:
    """List APEX workspace users.

    Args:
        workspace_id: Workspace ID (defaults to configured workspace).

    Returns:
        JSON array of users with: USER_NAME, EMAIL, DATE_CREATED, LAST_LOGIN.

    Queries APEX_WORKSPACE_APEX_USERS view.
    """
    if not db.is_connected():
        return _json({"status": "error", "error": "Not connected. Call apex_connect() first."})

    effective_ws_id = workspace_id if workspace_id is not None else WORKSPACE_ID

    try:
        # First try workspace-filtered query
        rows = db.execute("""
            SELECT user_name,
                   email,
                   TO_CHAR(date_created, 'YYYY-MM-DD HH24:MI') AS date_created,
                   TO_CHAR(last_login,   'YYYY-MM-DD HH24:MI') AS last_login,
                   account_locked
              FROM apex_workspace_apex_users
             WHERE workspace_id = :ws_id
             ORDER BY user_name
        """, {"ws_id": effective_ws_id})

        if not rows:
            # Fallback: list all users visible to the current session
            rows = db.execute("""
                SELECT user_name,
                       email,
                       TO_CHAR(date_created, 'YYYY-MM-DD HH24:MI') AS date_created,
                       TO_CHAR(last_login,   'YYYY-MM-DD HH24:MI') AS last_login,
                       account_locked
                  FROM apex_workspace_apex_users
                 ORDER BY user_name
            """)

        return _json({
            "status": "ok",
            "workspace_id": effective_ws_id,
            "count": len(rows),
            "users": rows,
        })

    except Exception as e:
        return _json({"status": "error", "error": str(e)})
