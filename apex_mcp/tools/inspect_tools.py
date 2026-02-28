"""Tools: discover, inspect, and edit existing APEX applications.

These are read/write tools for existing apps — no active import session required.
All query functions use APEX data dictionary views (APEX_APPLICATION_*).
All update/delete functions operate directly on WWV_FLOW_* internal tables.

WARNING: Direct table updates bypass APEX UI validation. Always verify changes
in APEX App Builder after any update or delete operation.
"""
from __future__ import annotations
import json
from ..db import db
from ..config import WORKSPACE_ID


def _esc(value: str) -> str:
    """Escape single quotes for safe embedding in PL/SQL string literals."""
    return value.replace("'", "''")


def _blk(sql: str) -> str:
    """Wrap SQL in an anonymous PL/SQL begin...end; block."""
    return f"begin\n{sql}\nend;"


# ---------------------------------------------------------------------------
# READ / DISCOVERY TOOLS
# ---------------------------------------------------------------------------


def apex_get_app_details(app_id: int) -> str:
    """Get complete metadata for an existing APEX application.

    Returns all app-level settings: name, alias, authentication, theme,
    authorization schemes, navigation lists, application items, application
    processes, substitution strings, and page count.

    Args:
        app_id: Application ID to inspect.

    Returns:
        JSON with comprehensive app metadata including:
        - Basic info: id, name, alias, status, compatibility_mode, owner
        - Theme: theme_id, theme_name, current_style
        - Authentication: scheme name, type
        - Pages: count and list of page IDs + names
        - Application Items: name, scope, protection level
        - Application Processes: name, point, sequence
        - Authorization Schemes: name, type, caching
        - Navigation Lists: name, item count
        - LOVs: name, source type, query
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})

    try:
        # Basic application info
        apps = db.execute("""
            SELECT application_id,
                   application_name,
                   alias,
                   status,
                   compatibility_mode,
                   owner,
                   pages,
                   TO_CHAR(created_on, 'YYYY-MM-DD HH24:MI') AS created_on,
                   TO_CHAR(last_updated_on, 'YYYY-MM-DD HH24:MI') AS last_updated_on,
                   theme_id,
                   theme_name,
                   authentication_scheme,
                   home_link,
                   login_url
              FROM apex_applications
             WHERE application_id = :app_id
        """, {"app_id": app_id})

        if not apps:
            return json.dumps({"status": "error", "error": f"Application {app_id} not found."})

        app_info = apps[0]

        # Pages list
        pages = db.execute("""
            SELECT page_id,
                   page_name,
                   page_mode,
                   authorization_scheme
              FROM apex_application_pages
             WHERE application_id = :app_id
             ORDER BY page_id
        """, {"app_id": app_id})

        # Application Items
        app_items = db.execute("""
            SELECT item_name,
                   item_scope,
                   item_protection_level,
                   item_data_type,
                   item_default
              FROM apex_application_items
             WHERE application_id = :app_id
             ORDER BY item_name
        """, {"app_id": app_id})

        # Application Processes
        app_procs = db.execute("""
            SELECT process_name,
                   process_type,
                   process_sequence,
                   process_point,
                   condition_type
              FROM apex_application_processes
             WHERE application_id = :app_id
             ORDER BY process_sequence
        """, {"app_id": app_id})

        # Authorization Schemes
        auth_schemes = db.execute("""
            SELECT authorization_scheme_name,
                   authorization_scheme_type,
                   error_message,
                   caching
              FROM apex_application_authorization
             WHERE application_id = :app_id
             ORDER BY authorization_scheme_name
        """, {"app_id": app_id})

        # Navigation Lists
        nav_lists = db.execute("""
            SELECT list_name,
                   list_status,
                   TO_CHAR(created_on, 'YYYY-MM-DD') AS created_on,
                   TO_CHAR(updated_on,  'YYYY-MM-DD') AS updated_on
              FROM apex_application_lists
             WHERE application_id = :app_id
             ORDER BY list_name
        """, {"app_id": app_id})

        # LOVs
        lovs = db.execute("""
            SELECT lov_name,
                   source_type,
                   list_of_values_query AS lov_query,
                   TO_CHAR(created_on, 'YYYY-MM-DD') AS created_on
              FROM apex_application_lov
             WHERE application_id = :app_id
             ORDER BY lov_name
        """, {"app_id": app_id})

        result = {
            "status": "ok",
            "app": app_info,
            "pages": pages,
            "page_count": len(pages),
            "application_items": app_items,
            "application_processes": app_procs,
            "authorization_schemes": auth_schemes,
            "navigation_lists": nav_lists,
            "lovs": lovs,
        }

        return json.dumps(result, default=str, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)


def apex_get_page_details(app_id: int, page_id: int) -> str:
    """Get complete details of a specific APEX page including all components.

    Returns everything on a page: regions, items, buttons, processes,
    dynamic actions, computations, and validations.

    Args:
        app_id: Application ID.
        page_id: Page ID to inspect.

    Returns:
        JSON with page metadata and all component arrays.
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})

    try:
        # Page-level metadata
        pages = db.execute("""
            SELECT page_id,
                   page_name,
                   page_mode,
                   page_template,
                   authorization_scheme,
                   javascript_code,
                   css_inline,
                   help_text,
                   reload_on_submit,
                   warn_on_unsaved_changes
              FROM apex_application_pages
             WHERE application_id = :app_id
               AND page_id = :page_id
        """, {"app_id": app_id, "page_id": page_id})

        if not pages:
            return json.dumps({
                "status": "error",
                "error": f"Page {page_id} not found in application {app_id}."
            })

        # Regions
        regions = db.execute("""
            SELECT region_id,
                   region_name,
                   region_type,
                   display_sequence,
                   display_column,
                   source_type,
                   region_source,
                   authorization_scheme,
                   condition_type,
                   condition_expression1,
                   condition_expression2,
                   region_template
              FROM apex_application_page_regions
             WHERE application_id = :app_id
               AND page_id = :page_id
             ORDER BY display_sequence
        """, {"app_id": app_id, "page_id": page_id})

        # Items
        items = db.execute("""
            SELECT item_name,
                   label           AS item_label,
                   display_as      AS item_type,
                   item_sequence   AS sequence,
                   region,
                   item_default    AS default_value,
                   process_value_column AS source_column,
                   format_mask,
                   lov_definition,
                   item_is_persistent,
                   placeholder
              FROM apex_application_page_items
             WHERE application_id = :app_id
               AND page_id = :page_id
             ORDER BY item_sequence
        """, {"app_id": app_id, "page_id": page_id})

        # Buttons
        buttons = db.execute("""
            SELECT button_name,
                   label           AS button_label,
                   button_action,
                   display_sequence AS sequence,
                   button_plug      AS region,
                   button_position,
                   button_is_hot,
                   redirect_url,
                   condition_type,
                   condition_expression1
              FROM apex_application_page_buttons
             WHERE application_id = :app_id
               AND page_id = :page_id
             ORDER BY display_sequence
        """, {"app_id": app_id, "page_id": page_id})

        # Processes
        processes = db.execute("""
            SELECT process_name,
                   process_type,
                   process_sequence,
                   process_point,
                   process_sql,
                   condition_type,
                   condition_expression1,
                   error_message,
                   success_message
              FROM apex_application_page_proc
             WHERE application_id = :app_id
               AND page_id = :page_id
             ORDER BY process_sequence
        """, {"app_id": app_id, "page_id": page_id})

        # Dynamic Actions
        da_events = db.execute("""
            SELECT dynamic_action_name,
                   event,
                   triggering_element,
                   triggering_element_type,
                   condition_type,
                   condition_expression1,
                   fire_on_page_load
              FROM apex_application_page_da
             WHERE application_id = :app_id
               AND page_id = :page_id
             ORDER BY dynamic_action_name
        """, {"app_id": app_id, "page_id": page_id})

        # Computations
        computations = db.execute("""
            SELECT item_name,
                   computation_type,
                   computation,
                   computation_sequence,
                   computation_point,
                   condition_type
              FROM apex_application_page_comp
             WHERE application_id = :app_id
               AND page_id = :page_id
             ORDER BY computation_sequence
        """, {"app_id": app_id, "page_id": page_id})

        # Validations
        validations = db.execute("""
            SELECT validation_name,
                   validation_type,
                   validation,
                   validation_sequence,
                   error_message,
                   condition_type,
                   associated_item
              FROM apex_application_page_val
             WHERE application_id = :app_id
               AND page_id = :page_id
             ORDER BY validation_sequence
        """, {"app_id": app_id, "page_id": page_id})

        result = {
            "status": "ok",
            "page": pages[0],
            "regions": regions,
            "items": items,
            "buttons": buttons,
            "processes": processes,
            "dynamic_actions": da_events,
            "computations": computations,
            "validations": validations,
        }

        return json.dumps(result, default=str, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)


def apex_list_regions(app_id: int, page_id: int) -> str:
    """List all regions on a specific APEX page.

    Args:
        app_id: Application ID.
        page_id: Page ID.

    Returns:
        JSON array of regions with type, source, sequence, and condition info.
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})

    try:
        rows = db.execute("""
            SELECT region_id,
                   region_name,
                   region_type,
                   display_sequence,
                   display_column,
                   source_type,
                   region_source,
                   authorization_scheme,
                   condition_type,
                   condition_expression1,
                   condition_expression2,
                   region_template,
                   template_options,
                   parent_region
              FROM apex_application_page_regions
             WHERE application_id = :app_id
               AND page_id = :page_id
             ORDER BY display_sequence
        """, {"app_id": app_id, "page_id": page_id})

        return json.dumps(rows, default=str, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)


def apex_list_items(app_id: int, page_id: int, region_name: str = "") -> str:
    """List all items (form fields) on a page, optionally filtered by region.

    Args:
        app_id: Application ID.
        page_id: Page ID.
        region_name: Filter by region name (empty = all regions).

    Returns:
        JSON array of items with type, label, source, LOV, and validation info.
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})

    try:
        params: dict = {"app_id": app_id, "page_id": page_id}
        region_filter = ""
        if region_name:
            region_filter = "AND UPPER(region) = UPPER(:region_name)"
            params["region_name"] = region_name

        rows = db.execute(f"""
            SELECT item_name,
                   label                     AS item_label,
                   display_as                AS item_type,
                   item_sequence             AS sequence,
                   region,
                   item_default              AS default_value,
                   process_value_column      AS source_column,
                   format_mask,
                   lov_definition,
                   item_is_persistent,
                   placeholder,
                   colspan,
                   item_css_classes,
                   condition_type,
                   condition_expression1
              FROM apex_application_page_items
             WHERE application_id = :app_id
               AND page_id = :page_id
               {region_filter}
             ORDER BY item_sequence
        """, params)

        return json.dumps(rows, default=str, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)


def apex_list_processes(app_id: int, page_id: int) -> str:
    """List all server-side processes on a page.

    Args:
        app_id: Application ID.
        page_id: Page ID.

    Returns:
        JSON array with process name, type, point, SQL/PL/SQL source,
        condition, error and success messages.
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})

    try:
        rows = db.execute("""
            SELECT process_name,
                   process_type,
                   process_sequence,
                   process_point,
                   process_sql,
                   condition_type,
                   condition_expression1,
                   condition_expression2,
                   error_message,
                   success_message,
                   when_button_pressed
              FROM apex_application_page_proc
             WHERE application_id = :app_id
               AND page_id = :page_id
             ORDER BY process_sequence
        """, {"app_id": app_id, "page_id": page_id})

        return json.dumps(rows, default=str, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)


def apex_list_dynamic_actions(app_id: int, page_id: int) -> str:
    """List all Dynamic Actions on a page.

    Args:
        app_id: Application ID.
        page_id: Page ID.

    Returns:
        JSON array of dynamic actions, each with their associated action steps.
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})

    try:
        # DA event headers
        da_events = db.execute("""
            SELECT dynamic_action_id,
                   dynamic_action_name,
                   event,
                   triggering_element,
                   triggering_element_type,
                   condition_type,
                   condition_expression1,
                   fire_on_page_load
              FROM apex_application_page_da
             WHERE application_id = :app_id
               AND page_id = :page_id
             ORDER BY dynamic_action_name
        """, {"app_id": app_id, "page_id": page_id})

        # DA action steps — joined via event id
        da_acts = db.execute("""
            SELECT a.dynamic_action_id,
                   a.action_name,
                   a.action,
                   a.action_sequence,
                   a.affected_elements,
                   a.affected_elements_type,
                   a.javascript_code,
                   a.attribute_01
              FROM apex_application_page_da_acts a
             WHERE a.application_id = :app_id
               AND a.page_id = :page_id
             ORDER BY a.dynamic_action_id, a.action_sequence
        """, {"app_id": app_id, "page_id": page_id})

        # Group actions under their parent DA event
        acts_by_da: dict[str, list] = {}
        for act in da_acts:
            da_id_str = str(act.get("DYNAMIC_ACTION_ID") or act.get("dynamic_action_id", ""))
            acts_by_da.setdefault(da_id_str, []).append(act)

        result = []
        for ev in da_events:
            da_id_str = str(ev.get("DYNAMIC_ACTION_ID") or ev.get("dynamic_action_id", ""))
            ev_copy = dict(ev)
            ev_copy["actions"] = acts_by_da.get(da_id_str, [])
            result.append(ev_copy)

        return json.dumps(result, default=str, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)


def apex_list_lovs(app_id: int) -> str:
    """List all shared LOVs (Lists of Values) for an application.

    Args:
        app_id: Application ID.

    Returns:
        JSON array with LOV name, type, query, and timestamps.
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})

    try:
        rows = db.execute("""
            SELECT lov_name,
                   source_type          AS lov_type,
                   list_of_values_query AS lov_query,
                   TO_CHAR(created_on, 'YYYY-MM-DD HH24:MI') AS created_on,
                   TO_CHAR(updated_on,  'YYYY-MM-DD HH24:MI') AS updated_on
              FROM apex_application_lov
             WHERE application_id = :app_id
             ORDER BY lov_name
        """, {"app_id": app_id})

        return json.dumps(rows, default=str, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)


def apex_list_auth_schemes(app_id: int) -> str:
    """List all Authorization Schemes for an application.

    Args:
        app_id: Application ID.

    Returns:
        JSON array with scheme name, type, function body (for custom types),
        error message, and caching setting.
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})

    try:
        rows = db.execute("""
            SELECT authorization_scheme_name,
                   authorization_scheme_type,
                   attribute_01,
                   error_message,
                   caching
              FROM apex_application_authorization
             WHERE application_id = :app_id
             ORDER BY authorization_scheme_name
        """, {"app_id": app_id})

        return json.dumps(rows, default=str, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# WRITE / UPDATE TOOLS
# ---------------------------------------------------------------------------


def apex_update_region(
    app_id: int,
    page_id: int,
    region_name: str,
    new_name: str | None = None,
    new_source_sql: str | None = None,
    new_static_content: str | None = None,
    new_sequence: int | None = None,
    new_auth_scheme: str | None = None,
    new_condition_type: str | None = None,
    new_condition_expr: str | None = None,
) -> str:
    """Update properties of an existing region on a page.

    Implementation uses direct UPDATE on WWV_FLOW_PAGE_PLUGS, which is the
    internal APEX metadata table backing all page regions.

    WARNING: Direct table updates bypass APEX UI validation. Always verify
    changes in APEX App Builder after updating.

    Args:
        app_id: Application ID.
        page_id: Page ID.
        region_name: Current name of the region to update.
        new_name: New display name for the region (optional).
        new_source_sql: New SQL source for IR/chart regions (optional).
        new_static_content: New HTML content for static regions (optional).
        new_sequence: New display sequence (optional).
        new_auth_scheme: New authorization scheme name (optional).
        new_condition_type: New condition type (optional).
        new_condition_expr: New condition expression (optional).

    Returns:
        JSON with status and what was changed.
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})

    # At least one change must be requested
    if all(v is None for v in [
        new_name, new_source_sql, new_static_content,
        new_sequence, new_auth_scheme, new_condition_type, new_condition_expr,
    ]):
        return json.dumps({
            "status": "error",
            "error": "No changes specified. Provide at least one new_* parameter."
        })

    try:
        # Verify the region exists
        existing = db.execute("""
            SELECT id, name, plug_source
              FROM wwv_flow_page_plugs
             WHERE flow_id = :app_id
               AND page_id = :page_id
               AND UPPER(name) = UPPER(:region_name)
        """, {"app_id": app_id, "page_id": page_id, "region_name": region_name})

        if not existing:
            return json.dumps({
                "status": "error",
                "error": (
                    f"Region '{region_name}' not found on page {page_id} of app {app_id}. "
                    "Tip: if TEA_APP does not have UPDATE on WWV_FLOW_PAGE_PLUGS, grant it as ADMIN: "
                    "GRANT UPDATE ON APEX_240200.WWV_FLOW_PAGE_PLUGS TO TEA_APP;"
                )
            })

        # Build SET clauses dynamically
        set_clauses: list[str] = []
        params: dict = {"app_id": app_id, "page_id": page_id, "region_name": region_name}
        changed: dict = {}

        if new_name is not None:
            set_clauses.append("name = :new_name")
            params["new_name"] = new_name
            changed["name"] = new_name

        if new_source_sql is not None:
            set_clauses.append("plug_source = :new_source_sql")
            params["new_source_sql"] = new_source_sql
            changed["plug_source"] = "(updated)"

        if new_static_content is not None:
            set_clauses.append("plug_source = :new_static_content")
            params["new_static_content"] = new_static_content
            changed["plug_source"] = "(static content updated)"

        if new_sequence is not None:
            set_clauses.append("display_sequence = :new_sequence")
            params["new_sequence"] = new_sequence
            changed["display_sequence"] = new_sequence

        if new_auth_scheme is not None:
            set_clauses.append("plug_required_role = :new_auth_scheme")
            params["new_auth_scheme"] = new_auth_scheme
            changed["plug_required_role"] = new_auth_scheme

        if new_condition_type is not None:
            set_clauses.append("plug_display_condition_type = :new_condition_type")
            params["new_condition_type"] = new_condition_type
            changed["plug_display_condition_type"] = new_condition_type

        if new_condition_expr is not None:
            set_clauses.append("plug_display_when_condition = :new_condition_expr")
            params["new_condition_expr"] = new_condition_expr
            changed["plug_display_when_condition"] = new_condition_expr

        set_clause_str = ", ".join(set_clauses)
        update_sql = f"""
            UPDATE wwv_flow_page_plugs
               SET {set_clause_str},
                   last_updated_by = 'APEX_MCP',
                   last_updated_on = SYSDATE
             WHERE flow_id = :app_id
               AND page_id = :page_id
               AND UPPER(name) = UPPER(:region_name)
        """
        db.execute(update_sql, params)
        db.conn.commit()

        return json.dumps({
            "status": "ok",
            "app_id": app_id,
            "page_id": page_id,
            "region_name": region_name,
            "changed": changed,
            "message": f"Region '{region_name}' on page {page_id} updated successfully.",
            "warning": "Direct table update performed. Verify changes in APEX App Builder.",
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        err_msg = str(e)
        hint = ""
        if "ORA-01031" in err_msg or "insufficient privileges" in err_msg.lower():
            hint = (
                " Hint: Grant UPDATE privilege as ADMIN: "
                "GRANT UPDATE ON APEX_240200.WWV_FLOW_PAGE_PLUGS TO TEA_APP;"
            )
        return json.dumps({
            "status": "error",
            "error": err_msg + hint
        }, ensure_ascii=False, indent=2)


def apex_update_item(
    app_id: int,
    page_id: int,
    item_name: str,
    new_label: str | None = None,
    new_item_type: str | None = None,
    new_default_value: str | None = None,
    new_source_column: str | None = None,
    new_lov_definition: str | None = None,
    new_is_required: bool | None = None,
    new_placeholder: str | None = None,
    new_read_only: bool | None = None,
) -> str:
    """Update properties of an existing page item.

    Uses direct UPDATE on WWV_FLOW_STEP_ITEMS (internal APEX table backing
    all page items).

    WARNING: Direct table updates bypass APEX UI validation. Always verify
    changes in APEX App Builder after updating.

    Args:
        app_id: Application ID.
        page_id: Page ID.
        item_name: Item name (e.g., P10_USERNAME).
        new_label: New display label.
        new_item_type: New item type (NATIVE_TEXT_FIELD, NATIVE_SELECT_LIST, etc.)
        new_default_value: New default value expression.
        new_source_column: New database source column for DML.
        new_lov_definition: New LOV query for select lists.
        new_is_required: Make required (True) or optional (False).
        new_placeholder: New placeholder text.
        new_read_only: Make read-only (True) or editable (False).

    Returns:
        JSON with status and changed fields.
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})

    if all(v is None for v in [
        new_label, new_item_type, new_default_value, new_source_column,
        new_lov_definition, new_is_required, new_placeholder, new_read_only,
    ]):
        return json.dumps({
            "status": "error",
            "error": "No changes specified. Provide at least one new_* parameter."
        })

    try:
        # Verify the item exists
        existing = db.execute("""
            SELECT id, name, prompt
              FROM wwv_flow_step_items
             WHERE flow_id = :app_id
               AND flow_step_id = :page_id
               AND UPPER(name) = UPPER(:item_name)
        """, {"app_id": app_id, "page_id": page_id, "item_name": item_name})

        if not existing:
            return json.dumps({
                "status": "error",
                "error": (
                    f"Item '{item_name}' not found on page {page_id} of app {app_id}. "
                    "Tip: if TEA_APP does not have UPDATE on WWV_FLOW_STEP_ITEMS, grant it as ADMIN: "
                    "GRANT UPDATE ON APEX_240200.WWV_FLOW_STEP_ITEMS TO TEA_APP;"
                )
            })

        set_clauses: list[str] = []
        params: dict = {"app_id": app_id, "page_id": page_id, "item_name": item_name}
        changed: dict = {}

        if new_label is not None:
            set_clauses.append("prompt = :new_label")
            params["new_label"] = new_label
            changed["prompt"] = new_label

        if new_item_type is not None:
            set_clauses.append("display_as = :new_item_type")
            params["new_item_type"] = new_item_type
            changed["display_as"] = new_item_type

        if new_default_value is not None:
            set_clauses.append("item_default = :new_default_value")
            params["new_default_value"] = new_default_value
            changed["item_default"] = new_default_value

        if new_source_column is not None:
            set_clauses.append("source = :new_source_column")
            params["new_source_column"] = new_source_column
            changed["source"] = new_source_column

        if new_lov_definition is not None:
            set_clauses.append("lov => :new_lov_definition")
            # lov column name in the table is just "lov"
            set_clauses[-1] = "lov = :new_lov_definition"
            params["new_lov_definition"] = new_lov_definition
            changed["lov"] = "(updated)"

        if new_is_required is not None:
            # In APEX internals, field_required is stored as 'Y'/'N'
            req_val = "Y" if new_is_required else "N"
            set_clauses.append("field_required = :new_is_required")
            params["new_is_required"] = req_val
            changed["field_required"] = req_val

        if new_placeholder is not None:
            set_clauses.append("placeholder = :new_placeholder")
            params["new_placeholder"] = new_placeholder
            changed["placeholder"] = new_placeholder

        if new_read_only is not None:
            # read_only_when_type: 'ALWAYS' = read-only, '' = editable
            ro_val = "ALWAYS" if new_read_only else ""
            set_clauses.append("read_only_when_type = :new_read_only")
            params["new_read_only"] = ro_val
            changed["read_only_when_type"] = ro_val

        if not set_clauses:
            return json.dumps({"status": "error", "error": "No valid changes to apply."})

        set_clause_str = ", ".join(set_clauses)
        update_sql = f"""
            UPDATE wwv_flow_step_items
               SET {set_clause_str},
                   last_updated_by = 'APEX_MCP',
                   last_updated_on = SYSDATE
             WHERE flow_id = :app_id
               AND flow_step_id = :page_id
               AND UPPER(name) = UPPER(:item_name)
        """
        db.execute(update_sql, params)
        db.conn.commit()

        return json.dumps({
            "status": "ok",
            "app_id": app_id,
            "page_id": page_id,
            "item_name": item_name.upper(),
            "changed": changed,
            "message": f"Item '{item_name}' on page {page_id} updated successfully.",
            "warning": "Direct table update performed. Verify changes in APEX App Builder.",
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        err_msg = str(e)
        hint = ""
        if "ORA-01031" in err_msg or "insufficient privileges" in err_msg.lower():
            hint = (
                " Hint: Grant UPDATE privilege as ADMIN: "
                "GRANT UPDATE ON APEX_240200.WWV_FLOW_STEP_ITEMS TO TEA_APP;"
            )
        return json.dumps({
            "status": "error",
            "error": err_msg + hint
        }, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# DELETE TOOLS
# ---------------------------------------------------------------------------


def apex_delete_page(app_id: int, page_id: int) -> str:
    """Delete a page from an APEX application.

    WARNING: This permanently deletes the page and ALL its components
    (regions, items, buttons, processes, dynamic actions, etc.).
    This action cannot be undone without a backup.

    Args:
        app_id: Application ID.
        page_id: Page ID to delete. Cannot delete page 0 (global page).

    Returns:
        JSON with status.
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})

    if page_id == 0:
        return json.dumps({
            "status": "error",
            "error": "Cannot delete page 0 (global page). The global page is required by APEX."
        })

    try:
        # Verify the page exists first
        existing = db.execute("""
            SELECT page_id, page_name
              FROM apex_application_pages
             WHERE application_id = :app_id
               AND page_id = :page_id
        """, {"app_id": app_id, "page_id": page_id})

        if not existing:
            return json.dumps({
                "status": "error",
                "error": f"Page {page_id} not found in application {app_id}."
            })

        page_name = existing[0].get("PAGE_NAME") or existing[0].get("page_name", str(page_id))

        # Use wwv_flow_page_dev.delete_page if available (APEX 24.x internal API),
        # otherwise cascade-delete via the internal tables.
        try:
            db.plsql(_blk(f"""
  wwv_flow_page_dev.delete_page(
    p_flow_id => {app_id},
    p_page_id => {page_id}
  );"""))
        except Exception:
            # Fallback: direct cascade delete on WWV_FLOW_STEPS and children.
            # Child rows in wwv_flow_page_plugs, wwv_flow_step_items, etc. reference
            # flow_id + flow_step_id; delete them before the parent step row.
            db.plsql(_blk(f"""
  -- Child items
  DELETE FROM wwv_flow_step_items
   WHERE flow_id = {app_id} AND flow_step_id = {page_id};
  -- Child page processes
  DELETE FROM wwv_flow_step_processing
   WHERE flow_id = {app_id} AND flow_step_id = {page_id};
  -- Child buttons
  DELETE FROM wwv_flow_step_buttons
   WHERE flow_id = {app_id} AND flow_step_id = {page_id};
  -- Child dynamic actions and their acts
  DELETE FROM wwv_flow_step_da_actions
   WHERE flow_id = {app_id} AND page_id = {page_id};
  DELETE FROM wwv_flow_step_da_events
   WHERE flow_id = {app_id} AND page_id = {page_id};
  -- Child regions (plugs)
  DELETE FROM wwv_flow_page_plugs
   WHERE flow_id = {app_id} AND page_id = {page_id};
  -- Child computations
  DELETE FROM wwv_flow_page_computations
   WHERE flow_id = {app_id} AND page_id = {page_id};
  -- Child validations
  DELETE FROM wwv_flow_step_validations
   WHERE flow_id = {app_id} AND flow_step_id = {page_id};
  -- Parent page step
  DELETE FROM wwv_flow_steps
   WHERE flow_id = {app_id} AND id = {page_id};
"""))

        db.conn.commit()

        return json.dumps({
            "status": "ok",
            "app_id": app_id,
            "page_id": page_id,
            "page_name": page_name,
            "message": f"Page {page_id} '{page_name}' deleted from application {app_id}.",
            "warning": "This deletion is permanent. Restore from backup if needed.",
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        err_msg = str(e)
        hint = ""
        if "ORA-01031" in err_msg or "insufficient privileges" in err_msg.lower():
            hint = (
                " Hint: Grant DELETE privilege as ADMIN on the relevant APEX internal tables "
                "or use the APEX App Builder UI to delete the page."
            )
        return json.dumps({
            "status": "error",
            "error": err_msg + hint
        }, ensure_ascii=False, indent=2)


def apex_delete_region(app_id: int, page_id: int, region_name: str) -> str:
    """Delete a specific region from a page.

    WARNING: Deletes the region and all its child items, buttons, and sub-regions.

    Args:
        app_id: Application ID.
        page_id: Page ID.
        region_name: Exact name of the region to delete.

    Returns:
        JSON with status and number of child items deleted.
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})

    try:
        # Look up the internal region id (plug id) from WWV_FLOW_PAGE_PLUGS
        existing = db.execute("""
            SELECT id, name
              FROM wwv_flow_page_plugs
             WHERE flow_id = :app_id
               AND page_id = :page_id
               AND UPPER(name) = UPPER(:region_name)
        """, {"app_id": app_id, "page_id": page_id, "region_name": region_name})

        if not existing:
            return json.dumps({
                "status": "error",
                "error": (
                    f"Region '{region_name}' not found on page {page_id} of app {app_id}. "
                    "Tip: check the exact region name with apex_list_regions()."
                )
            })

        plug_id = existing[0].get("ID") or existing[0].get("id")

        # Count child items before deleting
        child_items = db.execute("""
            SELECT COUNT(*) AS cnt
              FROM wwv_flow_step_items
             WHERE flow_id = :app_id
               AND flow_step_id = :page_id
               AND item_plug_id = :plug_id
        """, {"app_id": app_id, "page_id": page_id, "plug_id": plug_id})

        items_deleted = (
            child_items[0].get("CNT") or child_items[0].get("cnt", 0)
        ) if child_items else 0

        # Delete child items bound to this region
        db.plsql(_blk(f"""
  DELETE FROM wwv_flow_step_items
   WHERE flow_id = {app_id}
     AND flow_step_id = {page_id}
     AND item_plug_id = {plug_id};
"""))

        # Delete child buttons bound to this region
        db.plsql(_blk(f"""
  DELETE FROM wwv_flow_step_buttons
   WHERE flow_id = {app_id}
     AND flow_step_id = {page_id}
     AND button_plug_id = {plug_id};
"""))

        # Delete sub-regions (child plugs whose parent_plug_id = this plug)
        db.plsql(_blk(f"""
  DELETE FROM wwv_flow_page_plugs
   WHERE flow_id = {app_id}
     AND page_id = {page_id}
     AND parent_plug_id = {plug_id};
"""))

        # Delete the region itself
        db.plsql(_blk(f"""
  DELETE FROM wwv_flow_page_plugs
   WHERE flow_id = {app_id}
     AND page_id = {page_id}
     AND id = {plug_id};
"""))

        db.conn.commit()

        return json.dumps({
            "status": "ok",
            "app_id": app_id,
            "page_id": page_id,
            "region_name": region_name,
            "plug_id": plug_id,
            "child_items_deleted": int(items_deleted),
            "message": (
                f"Region '{region_name}' deleted from page {page_id}. "
                f"{int(items_deleted)} child item(s) also removed."
            ),
            "warning": "This deletion is permanent. Restore from backup if needed.",
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        err_msg = str(e)
        hint = ""
        if "ORA-01031" in err_msg or "insufficient privileges" in err_msg.lower():
            hint = (
                " Hint: Grant DELETE privilege as ADMIN: "
                "GRANT DELETE ON APEX_240200.WWV_FLOW_PAGE_PLUGS TO TEA_APP; "
                "GRANT DELETE ON APEX_240200.WWV_FLOW_STEP_ITEMS TO TEA_APP;"
            )
        return json.dumps({
            "status": "error",
            "error": err_msg + hint
        }, ensure_ascii=False, indent=2)


def apex_copy_page(
    source_app_id: int,
    source_page_id: int,
    target_app_id: int,
    target_page_id: int,
    new_page_name: str = "",
) -> str:
    """Copy a page from one app to another (or within the same app with a new ID).

    Args:
        source_app_id: Source application ID.
        source_page_id: Source page ID to copy.
        target_app_id: Target application ID (can be same as source).
        target_page_id: New page ID in the target app.
        new_page_name: Name for the copied page. Defaults to "Copy of {original_name}".

    Returns:
        JSON with status and new page details.
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})

    try:
        # Verify the source page exists and get its name
        src_pages = db.execute("""
            SELECT page_id, page_name
              FROM apex_application_pages
             WHERE application_id = :app_id
               AND page_id = :page_id
        """, {"app_id": source_app_id, "page_id": source_page_id})

        if not src_pages:
            return json.dumps({
                "status": "error",
                "error": f"Source page {source_page_id} not found in application {source_app_id}."
            })

        orig_name = (
            src_pages[0].get("PAGE_NAME") or src_pages[0].get("page_name", str(source_page_id))
        )
        resolved_name = new_page_name if new_page_name else f"Copy of {orig_name}"

        # Check target page does not already exist
        target_existing = db.execute("""
            SELECT page_id FROM apex_application_pages
             WHERE application_id = :app_id AND page_id = :page_id
        """, {"app_id": target_app_id, "page_id": target_page_id})

        if target_existing:
            return json.dumps({
                "status": "error",
                "error": (
                    f"Target page {target_page_id} already exists in application {target_app_id}. "
                    "Choose a different target_page_id or delete the existing page first."
                )
            })

        # Attempt wwv_flow_copy.copy_page (available in APEX internals)
        try:
            db.plsql(_blk(f"""
  wwv_flow_copy.copy_page(
    p_from_application_id => {source_app_id},
    p_from_page_id        => {source_page_id},
    p_to_application_id   => {target_app_id},
    p_to_page_id          => {target_page_id},
    p_to_page_name        => '{_esc(resolved_name)}'
  );"""))
        except Exception as copy_err:
            # Fallback: try wwv_flow_utilities.copy_page if the above failed
            try:
                db.plsql(_blk(f"""
  wwv_flow_utilities.copy_page(
    p_from_flow_id  => {source_app_id},
    p_from_step_id  => {source_page_id},
    p_to_flow_id    => {target_app_id},
    p_to_step_id    => {target_page_id},
    p_to_step_name  => '{_esc(resolved_name)}'
  );"""))
            except Exception as fallback_err:
                return json.dumps({
                    "status": "error",
                    "error": (
                        f"Both copy APIs failed. "
                        f"Primary: {copy_err}. "
                        f"Fallback: {fallback_err}. "
                        "Consider using the APEX App Builder UI to copy the page."
                    )
                }, ensure_ascii=False, indent=2)

        db.conn.commit()

        return json.dumps({
            "status": "ok",
            "source_app_id": source_app_id,
            "source_page_id": source_page_id,
            "target_app_id": target_app_id,
            "target_page_id": target_page_id,
            "new_page_name": resolved_name,
            "message": (
                f"Page {source_page_id} '{orig_name}' from app {source_app_id} "
                f"copied to page {target_page_id} '{resolved_name}' in app {target_app_id}."
            ),
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)
