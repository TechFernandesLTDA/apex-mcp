"""Tools: apex_add_page, apex_list_pages."""
from __future__ import annotations
import json
from ..db import db
from ..ids import ids
from ..session import session, PageInfo
from ..templates import PAGE_TMPL_STANDARD, PAGE_TMPL_LOGIN, PAGE_TMPL_MODAL
from ..config import WORKSPACE_ID


def _esc(value: str) -> str:
    """Escape single quotes for safe embedding in PL/SQL string literals."""
    return value.replace("'", "''")


def _blk(sql: str) -> str:
    """Wrap SQL in an anonymous PL/SQL begin...end; block."""
    return f"begin\n{sql}\nend;"


def apex_add_page(
    page_id: int,
    page_name: str,
    page_type: str = "blank",
    auth_scheme: str | None = None,
    page_template: str | None = None,
    help_text: str = "",
) -> str:
    """Add a page to the current APEX application.

    Args:
        page_id: Numeric page ID (e.g., 1, 10, 100). Page 0 is the global page.
        page_name: Display name for the page (e.g., "Dashboard", "User List").
        page_type: Type of page. Options:
            - "blank": Empty page (default) — use to add your own regions
            - "report": Interactive Report page template
            - "form": Form page template
            - "login": Login page (no nav, centered layout)
            - "dashboard": Dashboard with card layout
            - "modal": Modal dialog page
            - "global": Global page (page 0, appears on all pages)
        auth_scheme: Name of authorization scheme to restrict access (e.g., "IS_ADMIN").
                     Leave empty for public access.
        page_template: Override page template. Leave empty to use default for page_type.
        help_text: Help text shown to users on this page.

    Returns:
        JSON with status and page details.

    Best practices:
        - Use page IDs in logical groups: 1-9 dashboard, 10-19 entity1, 20-29 entity2, etc.
        - Login page should always be 101 or 100
        - Global page (ID 0) is applied to all pages — use for global JS/CSS
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})
    if not session.import_begun:
        return json.dumps({"status": "error", "error": "No import session active. Call apex_create_app() first."})

    try:
        page_alias = page_name.upper().replace(" ", "-")
        page_title = page_name
        is_public = "Y" if not auth_scheme else "N"
        auth_scheme_escaped = _esc(auth_scheme) if auth_scheme else ""

        # Determine page mode and template based on page_type
        page_type_lower = page_type.lower()
        if page_type_lower == "modal":
            page_mode = "MODAL"
            tmpl_id = PAGE_TMPL_MODAL
        elif page_type_lower == "login":
            page_mode = "NORMAL"
            tmpl_id = PAGE_TMPL_LOGIN
        else:
            # blank, report, form, dashboard, global
            page_mode = "NORMAL"
            tmpl_id = PAGE_TMPL_STANDARD

        # Allow explicit override
        if page_template:
            try:
                tmpl_id = int(page_template)
            except ValueError:
                # If it's not numeric, treat as named template — keep computed default
                pass

        # Build auth_scheme param line
        if auth_scheme:
            auth_line = f",p_page_is_public_y_n=>'N'\n,p_protection_level=>'C'\n,p_required_role=>'{auth_scheme_escaped}'"
        else:
            auth_line = ",p_page_is_public_y_n=>'Y'\n,p_protection_level=>'C'"

        help_line = f",p_help_text=>'{_esc(help_text)}'" if help_text else ""

        page_id_obj = ids.next(f"page_{page_id}")

        plsql = _blk(f"""
wwv_flow_imp_page.create_page(
 p_id=>{page_id}
,p_name=>'{_esc(page_name)}'
,p_alias=>'{_esc(page_alias)}'
,p_step_title=>'{_esc(page_title)}'
,p_autocomplete_on_off=>'OFF'
,p_page_mode=>'{page_mode}'
,p_page_template_id=>{tmpl_id}
,p_last_updated_by=>'APEX_MCP'
,p_last_upd_yyyymmddhh24miss=>TO_CHAR(SYSDATE,'YYYYMMDDHH24MISS')
{auth_line}{help_line}
);""")

        db.plsql(plsql)

        # For the global page (page 0), add a standard container region so components can be placed
        if page_type_lower == "global" or page_id == 0:
            region_id = ids.next(f"page_{page_id}_global_region")
            db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_plug(
 p_id=>wwv_flow_imp.id({region_id})
,p_flow_id=>wwv_flow.g_flow_id
,p_page_id=>{page_id}
,p_plug_name=>'Global Page'
,p_region_template_options=>'#DEFAULT#'
,p_plug_template=>4072358936313175081
,p_plug_display_sequence=>10
,p_plug_display_point=>'BODY'
,p_last_updated_by=>'APEX_MCP'
,p_last_upd_yyyymmddhh24miss=>TO_CHAR(SYSDATE,'YYYYMMDDHH24MISS')
);"""))

        # Update session state
        session.pages[page_id] = PageInfo(
            page_id=page_id,
            page_name=page_name,
            page_type=page_type_lower,
        )

        return json.dumps({
            "status": "ok",
            "page_id": page_id,
            "page_name": page_name,
            "page_type": page_type_lower,
            "page_mode": page_mode,
            "is_public": is_public,
            "auth_scheme": auth_scheme,
            "message": f"Page {page_id} '{page_name}' created successfully.",
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)


def apex_list_pages(app_id: int | None = None) -> str:
    """List all pages in an APEX application.

    Args:
        app_id: Application ID. If omitted, uses current session app_id.

    Returns:
        JSON array of pages with: PAGE_ID, PAGE_NAME, PAGE_MODE, AUTHORIZATION_SCHEME,
        CREATED_ON, UPDATED_ON.
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})

    effective_app_id = app_id if app_id is not None else session.app_id
    if effective_app_id is None:
        return json.dumps({"status": "error", "error": "No app_id provided and no active session. Pass app_id explicitly."})

    try:
        rows = db.execute("""
            SELECT page_id,
                   page_name,
                   page_mode,
                   authorization_scheme,
                   TO_CHAR(created_on, 'YYYY-MM-DD HH24:MI') AS created_on,
                   TO_CHAR(last_updated_on, 'YYYY-MM-DD HH24:MI') AS updated_on
              FROM apex_application_pages
             WHERE application_id = :app_id
             ORDER BY page_id
        """, {"app_id": effective_app_id})

        return json.dumps(rows, default=str, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)
