"""Tools: apex_add_lov, apex_add_auth_scheme, apex_add_nav_item, apex_add_app_item, apex_add_app_process."""
from __future__ import annotations
import json
from ..db import db
from ..ids import ids
from ..session import session, LovInfo, AuthSchemeInfo
from ..config import WORKSPACE_ID


def _esc(value: str) -> str:
    """Escape single quotes for safe embedding in PL/SQL string literals."""
    return value.replace("'", "''")


def _blk(sql: str) -> str:
    """Wrap SQL in an anonymous PL/SQL begin...end; block."""
    return f"begin\n{sql}\nend;"


def apex_add_lov(
    lov_name: str,
    lov_type: str = "sql",
    sql_query: str = "",
    static_values: list[dict] | None = None,
    return_column: str = "",
    display_column: str = "",
) -> str:
    """Create a shared List of Values (LOV) for use in select lists, radio groups, etc.

    Args:
        lov_name: Unique name for this LOV (e.g., "DEPARTMENTS", "STATUS_LIST").
                  Referenced by name in apex_add_item(lov_name=...).
        lov_type: Type of LOV:
            - "sql": Dynamic LOV from SQL query (default)
            - "static": Static list of display/return value pairs
        sql_query: SQL query for type="sql". Must return 2 columns: display value, return value.
                   Example: "SELECT department_name d, department_id r FROM departments ORDER BY 1"
                   The column aliases 'd' and 'r' are conventional but any names work.
        static_values: List of dicts for type="static". Each dict: {"display": "...", "return": "..."}
                       Example: [{"display": "Active", "return": "Y"}, {"display": "Inactive", "return": "N"}]
        return_column: Explicit return column name (auto-detected from SQL if omitted).
        display_column: Explicit display column name (auto-detected from SQL if omitted).

    Returns:
        JSON with status and LOV details.

    Best practices:
        - SQL LOVs: always add ORDER BY for consistent user experience
        - Static LOVs: use for small, fixed lists (status flags, yes/no, etc.)
        - Name LOVs by the data they represent, not the page (they're shared)
        - Add WHERE FL_ATIVO = 'S' or similar active flag filters
        - For FK select lists: "SELECT name d, id r FROM parent_table WHERE active='Y' ORDER BY name"

    Examples:
        apex_add_lov("DEPARTMENTS", "sql",
                     "SELECT dept_name d, dept_id r FROM hr_departments ORDER BY 1")
        apex_add_lov("ACTIVE_FLAG", "static",
                     static_values=[{"display": "Yes", "return": "Y"},
                                    {"display": "No", "return": "N"}])
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})
    if not session.import_begun:
        return json.dumps({"status": "error", "error": "No import session active. Call apex_create_app() first."})

    try:
        lov_id = ids.next(f"lov_{lov_name}")
        lov_type_lower = lov_type.lower()

        if lov_type_lower == "static":
            if not static_values:
                return json.dumps({"status": "error", "error": "static_values is required for lov_type='static'."})

            # Build a UNION ALL SQL from static pairs
            union_parts: list[str] = []
            for pair in static_values:
                disp = _esc(str(pair.get("display", "")))
                ret = _esc(str(pair.get("return", "")))
                union_parts.append(f"SELECT '{disp}' d, '{ret}' r FROM dual")

            effective_query = " UNION ALL ".join(union_parts)
        else:
            # sql type
            if not sql_query:
                return json.dumps({"status": "error", "error": "sql_query is required for lov_type='sql'."})
            effective_query = sql_query

        # Split the query into lines for wwv_flow_string.join(wwv_flow_t_varchar2(...))
        lines = effective_query.splitlines()
        if not lines:
            lines = [effective_query]

        # Build each line as a quoted varchar2 element (escape single quotes)
        varchar2_elements = []
        for line in lines:
            escaped_line = line.replace("'", "''")
            varchar2_elements.append(f"'{escaped_line}'")

        lov_query_expr = (
            "wwv_flow_string.join(wwv_flow_t_varchar2(\n"
            + ",\n".join(varchar2_elements)
            + "))"
        )

        plsql = _blk(f"""
wwv_flow_imp_shared.create_list_of_values(
 p_id=>wwv_flow_imp.id({lov_id})
,p_lov_name=>'{_esc(lov_name)}'
,p_lov_query=>{lov_query_expr}
,p_source_type=>'LEGACY_SQL'
,p_version_scn=>1
);""")

        db.plsql(plsql)

        # Register in session
        session.lovs[lov_name] = LovInfo(lov_id=lov_id, lov_name=lov_name)

        return json.dumps({
            "status": "ok",
            "lov_name": lov_name,
            "lov_id": lov_id,
            "lov_type": lov_type_lower,
            "message": f"LOV '{lov_name}' created successfully.",
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)


def apex_add_auth_scheme(
    scheme_name: str,
    function_body: str,
    error_message: str = "Access denied.",
    caching: str = "BY_USER_BY_SESSION",
) -> str:
    """Create an Authorization Scheme to control access to pages and components.

    Args:
        scheme_name: Unique name (e.g., "IS_ADMIN", "IS_MANAGER", "CAN_EDIT_RECORDS").
        function_body: PL/SQL function body that returns BOOLEAN.
                       The function MUST return TRUE to grant access.
                       Has access to: apex_application.g_user, apex_util.get_session_state().
                       Example: "return apex_util.get_session_state('APP_USER_ROLE') = 'ADMIN';"
        error_message: Message shown when access is denied.
        caching: When to re-evaluate:
            - "BY_USER_BY_SESSION": Cached per user per session (default, best performance)
            - "BY_USER_BY_PAGE_VIEW": Re-evaluated on every page view
            - "NO_CACHING": Always re-evaluated (use for dynamic permissions)

    Returns:
        JSON with status and scheme details.

    Best practices:
        - Cache by session for role-based schemes (roles don't change mid-session)
        - Name schemes with IS_ prefix for clarity (IS_ADMIN, IS_MANAGER)
        - Use apex_util.get_session_state() to read application items set during login
        - Return FALSE (not raise exception) for unauthorized access

    Examples:
        apex_add_auth_scheme("IS_ADMIN",
            "return apex_util.get_session_state('APP_ROLE') = 'ADMIN';",
            "Restricted to administrators only.")
        apex_add_auth_scheme("IS_MANAGER_OR_ABOVE",
            "return apex_util.get_session_state('APP_ROLE') IN ('ADMIN', 'MANAGER');",
            "Manager access required.")
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})
    if not session.import_begun:
        return json.dumps({"status": "error", "error": "No import session active. Call apex_create_app() first."})

    try:
        scheme_id = ids.next(f"auth_scheme_{scheme_name}")

        # Escape single quotes in the function body and error message
        escaped_body = function_body.replace("'", "''")
        escaped_error = _esc(error_message)

        plsql = _blk(f"""
wwv_flow_imp_shared.create_security_scheme(
 p_id=>wwv_flow_imp.id({scheme_id})
,p_name=>'{_esc(scheme_name)}'
,p_scheme_type=>'NATIVE_FUNCTION_BODY'
,p_attribute_01=>'{escaped_body}'
,p_error_message=>'{escaped_error}'
,p_caching=>'{caching}'
,p_version_scn=>1
);""")

        db.plsql(plsql)

        # Register in session
        session.auth_schemes[scheme_name] = AuthSchemeInfo(
            scheme_id=scheme_id,
            scheme_name=scheme_name,
        )

        return json.dumps({
            "status": "ok",
            "scheme_name": scheme_name,
            "scheme_id": scheme_id,
            "caching": caching,
            "message": f"Authorization scheme '{scheme_name}' created successfully.",
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)


def apex_add_nav_item(
    item_name: str,
    target_page: int,
    sequence: int = 10,
    icon: str = "fa-circle",
    auth_scheme: str = "",
    parent_item: str = "",
) -> str:
    """Add an item to the Navigation Menu (side navigation).

    Args:
        item_name: Display text for the nav item (e.g., "Dashboard", "Users").
        target_page: Page ID to navigate to when clicked.
        sequence: Display order (10, 20, 30...).
        icon: Font APEX icon class. Common icons:
            - "fa-home": Home/Dashboard
            - "fa-users": Users, People
            - "fa-table": Data, Reports
            - "fa-cog": Settings, Configuration
            - "fa-bar-chart": Analytics, Charts
            - "fa-user": Profile, Account
            - "fa-file-text-o": Documents, Reports
            - "fa-shield": Security, Admin
            - "fa-plus": New, Add
            - "fa-search": Search
        auth_scheme: Authorization scheme name to restrict visibility.
                     Empty = visible to all authenticated users.
        parent_item: Parent nav item name for sub-navigation hierarchy.

    Best practices:
        - Keep nav to 7+/-2 items for usability
        - Group related items under parent nav items
        - Use auth_scheme to hide items users cannot access
        - Sequence in multiples of 10 to allow future insertions
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})
    if not session.import_begun:
        return json.dumps({"status": "error", "error": "No import session active. Call apex_create_app() first."})

    try:
        # Retrieve the nav_menu list ID registered during apex_create_app
        if not ids.has("nav_menu"):
            return json.dumps({"status": "error", "error": "Navigation Menu not found. Call apex_create_app() first."})

        nav_menu_id = ids.get("nav_menu")
        nav_item_id = ids.next(f"nav_item_{item_name}")

        target_url = f"f?p=&APP_ID.:{target_page}:&APP_SESSION.::&DEBUG.:::"

        # Optional parent item reference
        parent_line = ""
        if parent_item:
            if not ids.has(f"nav_item_{parent_item}"):
                return json.dumps({
                    "status": "error",
                    "error": f"Parent nav item '{parent_item}' not found. Add it before the child item.",
                })
            parent_id = ids.get(f"nav_item_{parent_item}")
            parent_line = f"\n,p_parent_list_item_id=>wwv_flow_imp.id({parent_id})"

        # Optional auth scheme
        auth_line = ""
        if auth_scheme:
            auth_line = f"\n,p_required_role=>'{_esc(auth_scheme)}'"

        plsql = _blk(f"""
wwv_flow_imp_shared.create_list_item(
 p_id=>wwv_flow_imp.id({nav_item_id})
,p_list_id=>wwv_flow_imp.id({nav_menu_id})
,p_list_item_display_sequence=>{sequence}
,p_list_item_link_text=>'{_esc(item_name)}'
,p_list_item_link_target=>'{target_url}'
,p_list_item_icon=>'{_esc(icon)}'{parent_line}{auth_line}
,p_list_item_current_type=>'TARGET_PAGE'
);""")

        db.plsql(plsql)

        # Register in session
        session.nav_items.append({
            "item_name": item_name,
            "target_page": target_page,
            "sequence": sequence,
            "icon": icon,
            "auth_scheme": auth_scheme,
            "parent_item": parent_item,
        })

        return json.dumps({
            "status": "ok",
            "item_name": item_name,
            "nav_item_id": nav_item_id,
            "target_page": target_page,
            "sequence": sequence,
            "icon": icon,
            "auth_scheme": auth_scheme or None,
            "parent_item": parent_item or None,
            "message": f"Navigation item '{item_name}' -> page {target_page} created successfully.",
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)


def apex_add_app_item(
    item_name: str,
    scope: str = "SESSION",
    protection: str = "I",
    session_state_function: str = "",
) -> str:
    """Create an Application Item (session-level variable accessible on all pages).

    Application items store user context like current user role, ID, preferences.
    They are set during application processes (e.g., on login) and read throughout.

    Args:
        item_name: Item name (uppercase, e.g., "APP_USER_ROLE", "APP_CLINIC_ID").
                   Convention: prefix with APP_ to distinguish from page items.
        scope: Variable scope:
            - "SESSION": Available for the current session (default)
            - "USER": Persisted across sessions for the same user
        protection: Security protection level:
            - "RESTRICTED": Cannot be set via URL parameter (default, recommended)
            - "CHECKSUM_REQUIRED": Can be set via URL with valid checksum
            - "UNRESTRICTED": Can be set freely (use only for non-sensitive data)
        session_state_function: PL/SQL to initialize the item value.

    Best practices:
        - Always use RESTRICTED for items holding user roles or IDs
        - Set values in an On New Instance application process after login
        - Prefix with APP_ to clearly distinguish from page items (P{n}_...)
        - Use apex_util.set_session_state() in PL/SQL to update values

    Examples:
        apex_add_app_item("APP_USER_ROLE")
        apex_add_app_item("APP_CLINIC_ID", protection="RESTRICTED")
        apex_add_app_item("APP_USERNAME")
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})
    if not session.import_begun:
        return json.dumps({"status": "error", "error": "No import session active. Call apex_create_app() first."})

    try:
        item_id = ids.next(f"app_item_{item_name}")

        session_state_line = ""
        if session_state_function:
            escaped_fn = _esc(session_state_function)
            session_state_line = f"\n,p_session_state_code=>'{escaped_fn}'"

        plsql = _blk(f"""
wwv_flow_imp_shared.create_flow_item(
 p_id=>wwv_flow_imp.id({item_id})
,p_name=>'{_esc(item_name.upper())}'
,p_protection_level=>'{protection}'{session_state_line}
,p_version_scn=>1
);""")

        db.plsql(plsql)

        # Register in session
        session.app_items.append(item_name.upper())

        return json.dumps({
            "status": "ok",
            "item_name": item_name.upper(),
            "item_id": item_id,
            "scope": scope,
            "protection": protection,
            "message": f"Application item '{item_name.upper()}' created successfully.",
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)


def apex_add_app_process(
    process_name: str,
    plsql_body: str,
    point: str = "ON_NEW_INSTANCE",
    sequence: int = 10,
    condition_type: str = "",
    condition_expr: str = "",
) -> str:
    """Create an Application Process (runs at application or session level, not page level).

    Use application processes to initialize session state, set context variables,
    check global conditions, or run code that should apply to all pages.

    Args:
        process_name: Process display name.
        plsql_body: PL/SQL anonymous block to execute.
                    Has access to apex_application, apex_util, :APP_* items.
        point: When to execute:
            - "ON_NEW_INSTANCE": On new session start — use to initialize session state (default)
            - "ON_SUBMIT": On every page submit
            - "BEFORE_LOGIN": Before authentication
            - "AFTER_LOGIN": After successful login
        sequence: Execution order when multiple processes exist.
        condition_type: Optional condition:
            - "": Always run (default)
            - "ITEM_IS_NULL": Run only if item is null
            - "ITEM_IS_NOT_NULL": Run only if item is not null
        condition_expr: Item name for the condition.

    Best practices:
        - Use ON_NEW_INSTANCE to load user role, clinic ID, etc. into APP items
        - Keep processes focused — one process per logical concern
        - Use AFTER_LOGIN for post-authentication setup
        - Always handle exceptions to avoid breaking the session

    Example:
        apex_add_app_process(
            "LOAD_USER_CONTEXT",
            '''begin
              select user_role, clinic_id
                into apex_util.set_session_state('APP_ROLE', ...),
                     ...
                from app_users
               where username = :APP_USER;
            exception when no_data_found then null;
            end;''',
            point="ON_NEW_INSTANCE"
        )
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})
    if not session.import_begun:
        return json.dumps({"status": "error", "error": "No import session active. Call apex_create_app() first."})

    try:
        process_id = ids.next(f"app_process_{process_name}")

        escaped_body = _esc(plsql_body)

        # Build optional condition lines
        condition_lines = ""
        if condition_type:
            condition_lines = f"\n,p_condition_type=>'{_esc(condition_type)}'"
            if condition_expr:
                condition_lines += f"\n,p_condition_expression1=>'{_esc(condition_expr)}'"

        plsql = _blk(f"""
wwv_flow_imp_shared.create_flow_process(
 p_id=>wwv_flow_imp.id({process_id})
,p_process_sequence=>{sequence}
,p_process_point=>'{point}'
,p_process_type=>'NATIVE_PLSQL'
,p_process_name=>'{_esc(process_name)}'
,p_process_sql_clob=>'{escaped_body}'{condition_lines}
,p_version_scn=>1
);""")

        db.plsql(plsql)

        # Register in session
        session.app_processes.append(process_name)

        return json.dumps({
            "status": "ok",
            "process_name": process_name,
            "process_id": process_id,
            "point": point,
            "sequence": sequence,
            "condition_type": condition_type or None,
            "condition_expr": condition_expr or None,
            "message": f"Application process '{process_name}' created successfully.",
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)
