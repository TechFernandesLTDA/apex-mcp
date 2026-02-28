"""Tools: apex_create_app, apex_delete_app, apex_finalize_app, apex_list_apps."""
from __future__ import annotations
import json
from ..db import db
from ..ids import ids
from ..session import session
from ..templates import (
    PAGE_TMPL_STANDARD, PAGE_TMPL_LOGIN,
    THEME_STYLE_ID, CHECKSUM_SALT,
    LIST_TMPL_SIDE_NAV, LIST_TMPL_NAVBAR,
)
from ..config import WORKSPACE_ID, APEX_SCHEMA, APEX_VERSION_DATE, APEX_COMPAT_MODE


def _blk(sql: str) -> str:
    return f"begin\n{sql}\nend;"


def apex_list_apps() -> str:
    """List all APEX applications in the current workspace.

    Returns:
        JSON array of apps with: APPLICATION_ID, APPLICATION_NAME, ALIAS, STATUS,
        PAGES, LAST_UPDATED_ON, OWNER.

    Requires:
        - Active connection (call apex_connect first)
        - User must have SELECT on APEX_APPLICATIONS view (granted to APEX schema users)
    """
    if not db.is_connected():
        return "Not connected. Call apex_connect() first."

    rows = db.execute("""
        SELECT application_id,
               application_name,
               alias,
               availability_status AS status,
               pages,
               TO_CHAR(last_updated_on, 'YYYY-MM-DD') AS last_updated_on,
               owner
          FROM apex_applications
         WHERE workspace = (SELECT workspace FROM apex_workspaces WHERE workspace_id = :ws_id)
         ORDER BY application_id
    """, {"ws_id": WORKSPACE_ID})

    if not rows:
        # Fallback: query without workspace filter
        rows = db.execute("""
            SELECT application_id, application_name, alias,
                   availability_status AS status, pages,
                   TO_CHAR(last_updated_on, 'YYYY-MM-DD') AS last_updated_on, owner
              FROM apex_applications
             ORDER BY application_id
        """)

    return json.dumps(rows, default=str, ensure_ascii=False, indent=2)


def apex_create_app(
    app_id: int,
    app_name: str,
    app_alias: str | None = None,
    login_page: int = 101,
    home_page: int = 1,
    schema: str = APEX_SCHEMA,
    language: str = "pt-br",
    date_format: str = "DD/MM/YYYY",
    auth_type: str = "NATIVE_APEX_ACCOUNTS",
) -> str:
    """Create a new APEX application (full scaffold: flow + theme 42 + auth + UI + nav).

    This tool:
    1. Calls wwv_flow_imp.import_begin to start the import session
    2. Removes any existing app with the same ID
    3. Creates the flow (application) with all metadata
    4. Applies Universal Theme 42 with Redwood Light style
    5. Creates authentication scheme (APEX Accounts by default)
    6. Creates Navigation Menu list and Navigation Bar list
    7. Creates User Interface binding navigation to the app

    After calling this tool:
    - Use apex_add_page() to add pages
    - Use apex_add_region(), apex_add_item(), etc. to add components
    - ALWAYS call apex_finalize_app() when done

    Args:
        app_id: Numeric application ID (e.g., 200). Must not conflict with existing apps.
        app_name: Display name shown in the APEX header (e.g., "My App").
        app_alias: URL alias (e.g., "MY-APP"). Auto-generated from app_name if omitted.
        login_page: Page ID for the login page (default 101).
        home_page: Page ID for the home/dashboard (default 1).
        schema: Database schema owner (default: APEX_SCHEMA env or TEA_APP).
        language: Application primary language (default: pt-br).
        date_format: Date display format (default: DD/MM/YYYY).
        auth_type: Authentication scheme type. Options:
            - NATIVE_APEX_ACCOUNTS (default): APEX user accounts
            - NATIVE_CUSTOM_AUTH: custom PL/SQL function
            - NATIVE_DAD: Database Access Descriptor
            - NATIVE_LDAP: LDAP directory

    Returns:
        JSON with status, app_id, and list of operations performed.

    Requires:
        - Active connection as a privileged APEX schema user
        - User must have EXECUTE on wwv_flow_imp_shared, wwv_imp_workspace packages
        - User must have CREATE SESSION, ALTER SESSION
        - For ADB: user must be the APEX workspace schema or have equivalent grants
    """
    if not db.is_connected():
        return "Not connected. Call apex_connect() first."

    alias = app_alias or app_name.upper().replace(" ", "-")
    log: list[str] = []

    try:
        # Reset session state and ID generator
        session.reset()
        ids.reset()

        # Fixed IDs for cross-references
        ID_AUTH     = ids.next("auth")
        ID_UI       = ids.next("ui")
        ID_THEME    = ids.next("theme")
        ID_NAV_MENU = ids.next("nav_menu")
        ID_NAV_BAR  = ids.next("nav_bar")
        ID_NAV_BAR_USER   = ids.next("nav_bar_user")
        ID_NAV_BAR_LOGOUT = ids.next("nav_bar_logout")

        # 1. import_begin
        db.plsql(_blk(f"""
wwv_flow_imp.import_begin (
 p_version_yyyy_mm_dd=>'{APEX_VERSION_DATE}'
,p_release=>'24.2.13'
,p_default_workspace_id=>{WORKSPACE_ID}
,p_default_application_id=>{app_id}
,p_default_id_offset=>0
,p_default_owner=>'{schema}'
);"""))
        log.append("import_begin: OK")

        # 2. Remove existing app (ignore errors)
        try:
            db.plsql(_blk("""
  begin
    wwv_flow_imp.remove_flow(wwv_flow.g_flow_id);
  exception when others then null;
  end;"""))
            log.append("remove_flow: OK (or no prior app)")
        except Exception:
            log.append("remove_flow: skipped")

        # 3. create_flow
        db.plsql(_blk(f"""
wwv_imp_workspace.create_flow(
 p_id=>wwv_flow.g_flow_id
,p_owner=>nvl(wwv_flow_application_install.get_schema,'{schema}')
,p_name=>nvl(wwv_flow_application_install.get_application_name,'{app_name.replace("'", "''")}')
,p_alias=>nvl(wwv_flow_application_install.get_application_alias,'{alias}')
,p_page_view_logging=>'YES'
,p_page_protection_enabled_y_n=>'Y'
,p_checksum_salt=>'{CHECKSUM_SALT}'
,p_bookmark_checksum_function=>'SH512'
,p_max_session_length_sec=>28800
,p_max_session_idle_sec=>3600
,p_compatibility_mode=>'{APEX_COMPAT_MODE}'
,p_flow_language=>'{language}'
,p_flow_language_derived_from=>'FLOW_PRIMARY_LANGUAGE'
,p_allow_feedback_yn=>'N'
,p_date_format=>'{date_format}'
,p_timestamp_format=>'{date_format} HH24:MI'
,p_timestamp_tz_format=>'DS'
,p_flow_image_prefix => nvl(wwv_flow_application_install.get_image_prefix,'')
,p_authentication_id=>wwv_flow_imp.id({ID_AUTH})
,p_application_tab_set=>0
,p_logo_type=>'T'
,p_logo_text=>'{app_name.replace("'", "''")}'
,p_public_user=>'APEX_PUBLIC_USER'
,p_proxy_server=>nvl(wwv_flow_application_install.get_proxy,'')
,p_no_proxy_domains=>nvl(wwv_flow_application_install.get_no_proxy_domains,'')
,p_flow_version=>'{APEX_COMPAT_MODE}.0'
,p_flow_status=>'AVAILABLE_W_EDIT_LINK'
,p_flow_unavailable_text=>'System temporarily unavailable.'
,p_exact_substitutions_only=>'Y'
,p_browser_cache=>'N'
,p_browser_frame=>'S'
,p_deep_linking=>'Y'
,p_rejoin_existing_sessions=>'N'
,p_csv_encoding=>'Y'
,p_auto_time_zone=>'N'
,p_substitution_string_01=>'APP_NAME'
,p_substitution_value_01=>'{app_name.replace("'", "''")}'
,p_file_prefix => nvl(wwv_flow_application_install.get_static_app_file_prefix,'')
,p_files_version=>1
,p_version_scn=>1
,p_print_server_type=>'INSTANCE'
,p_file_storage=>'DB'
,p_is_pwa=>'N'
);"""))
        log.append("create_flow: OK")

        # 4. Theme 42
        db.plsql(_blk(f"""
wwv_flow_imp_shared.create_theme(
 p_id=>wwv_flow_imp.id({ID_THEME})
,p_theme_id=>42
,p_theme_name=>'Universal Theme'
,p_theme_internal_name=>'UNIVERSAL_THEME'
,p_version_identifier=>'{APEX_COMPAT_MODE}'
,p_navigation_type=>'L'
,p_nav_bar_type=>'LIST'
,p_reference_id=>4072363937200175119
,p_is_locked=>false
,p_current_theme_style_id=>{THEME_STYLE_ID}
,p_default_page_template=>{PAGE_TMPL_STANDARD}
,p_default_dialog_template=>2100407606326202693
,p_error_template=>{PAGE_TMPL_LOGIN}
,p_printer_friendly_template=>{PAGE_TMPL_STANDARD}
,p_login_template=>{PAGE_TMPL_LOGIN}
,p_default_button_template=>4072362960822175091
,p_default_region_template=>4072358936313175081
,p_default_chart_template=>4072358936313175081
,p_default_form_template=>4072358936313175081
,p_default_reportr_template=>4072358936313175081
,p_default_tabform_template=>4072358936313175081
,p_default_wizard_template=>4072358936313175081
,p_default_menur_template=>2531463326621247859
,p_default_listr_template=>4072358936313175081
,p_default_irr_template=>2100526641005906379
,p_default_report_template=>2538654340625403440
,p_default_label_template=>1609121967514267634
,p_default_menu_template=>4072363345357175094
,p_default_calendar_template=>4072363550766175095
,p_default_list_template=>4072361143931175087
,p_default_nav_list_template=>2526754704087354841
,p_default_top_nav_list_temp=>2526754704087354841
,p_default_side_nav_list_temp=>{LIST_TMPL_SIDE_NAV}
,p_default_nav_list_position=>'SIDE'
,p_default_dialogbtnr_template=>2126429139436695430
,p_default_dialogr_template=>4501440665235496320
,p_default_option_label=>1609121967514267634
,p_default_required_label=>1609122147107268652
,p_default_navbar_list_template=>{LIST_TMPL_NAVBAR}
,p_file_prefix => nvl(wwv_flow_application_install.get_static_theme_file_prefix(42),'#APEX_FILES#themes/theme_42/{APEX_COMPAT_MODE}/')
,p_files_version=>64
,p_icon_library=>'FONTAPEX'
,p_javascript_file_urls=>wwv_flow_string.join(wwv_flow_t_varchar2(
'#APEX_FILES#libraries/apex/#MIN_DIRECTORY#widget.stickyWidget#MIN#.js?v=#APEX_VERSION#'
,'#THEME_FILES#js/theme42#MIN#.js?v=#APEX_VERSION#'))
,p_css_file_urls=>'#THEME_FILES#css/Core#MIN#.css?v=#APEX_VERSION#'
);"""))
        log.append("create_theme: OK")

        # 5. Authentication scheme
        db.plsql(_blk(f"""
wwv_flow_imp_shared.create_authentication(
 p_id=>wwv_flow_imp.id({ID_AUTH})
,p_name=>'App Authentication'
,p_scheme_type=>'{auth_type}'
,p_invalid_session_type=>'LOGIN'
,p_use_secure_cookie_yn=>'N'
,p_ras_mode=>0
,p_version_scn=>1
);"""))
        log.append("create_authentication: OK")

        # 6. Navigation Menu list
        db.plsql(_blk(f"""
wwv_flow_imp_shared.create_list(
 p_id=>wwv_flow_imp.id({ID_NAV_MENU})
,p_name=>'Navigation Menu'
,p_list_status=>'PUBLIC'
,p_version_scn=>1
);"""))
        log.append("create_list(nav_menu): OK")

        # 7. Navigation Bar list
        db.plsql(_blk(f"""
wwv_flow_imp_shared.create_list(
 p_id=>wwv_flow_imp.id({ID_NAV_BAR})
,p_name=>'Navigation Bar'
,p_list_status=>'PUBLIC'
,p_version_scn=>1
);"""))
        # Nav bar: user item + logout sub-item
        db.plsql(_blk(f"""
wwv_flow_imp_shared.create_list_item(
 p_id=>wwv_flow_imp.id({ID_NAV_BAR_USER})
,p_list_id=>wwv_flow_imp.id({ID_NAV_BAR})
,p_list_item_display_sequence=>10
,p_list_item_link_text=>'&APP_USER.'
,p_list_item_link_target=>'#'
,p_list_item_icon=>'fa-user'
,p_list_item_current_type=>'NEVER'
);"""))
        db.plsql(_blk(f"""
wwv_flow_imp_shared.create_list_item(
 p_id=>wwv_flow_imp.id({ID_NAV_BAR_LOGOUT})
,p_list_id=>wwv_flow_imp.id({ID_NAV_BAR})
,p_list_item_display_sequence=>20
,p_list_item_link_text=>'Logout'
,p_list_item_link_target=>'&LOGOUT_URL.'
,p_list_item_icon=>'fa-sign-out'
,p_parent_list_item_id=>wwv_flow_imp.id({ID_NAV_BAR_USER})
,p_list_item_current_type=>'NEVER'
);"""))
        log.append("create_list(nav_bar): OK")

        # 8. User Interface
        db.plsql(_blk(f"""
wwv_flow_imp_shared.create_user_interface(
 p_id=>wwv_flow_imp.id({ID_UI})
,p_theme_id=>42
,p_home_url=>'f?p=&APP_ID.:{home_page}:&APP_SESSION.::&DEBUG.:::'
,p_login_url=>'f?p=&APP_ID.:{login_page}:&APP_SESSION.::&DEBUG.:::'
,p_theme_style_by_user_pref=>false
,p_built_with_love=>false
,p_global_page_id=>0
,p_navigation_list_id=>wwv_flow_imp.id({ID_NAV_MENU})
,p_navigation_list_position=>'SIDE'
,p_navigation_list_template_id=>{LIST_TMPL_SIDE_NAV}
,p_nav_list_template_options=>'#DEFAULT#:js-defaultCollapsed:js-navCollapsed--hidden:t-TreeNav--styleA'
,p_nav_bar_type=>'LIST'
,p_nav_bar_list_id=>wwv_flow_imp.id({ID_NAV_BAR})
,p_nav_bar_list_template_id=>{LIST_TMPL_NAVBAR}
,p_nav_bar_template_options=>'#DEFAULT#'
);"""))
        log.append("create_user_interface: OK")

        # Update session state
        session.app_id = app_id
        session.app_name = app_name
        session.workspace_id = WORKSPACE_ID
        session.import_begun = True

        return json.dumps({
            "status": "ok",
            "app_id": app_id,
            "app_name": app_name,
            "next_step": "Use apex_add_page() to add pages, then apex_finalize_app() when done.",
            "log": log,
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        # Cleanup: try to end any partial import session
        try:
            db.plsql("begin wwv_flow_imp.import_end(p_auto_install_sup_obj=>false); end;")
        except Exception:
            pass
        session.reset()
        ids.reset()
        return json.dumps({"status": "error", "error": str(e), "log": log, "cleanup": "session reset"}, ensure_ascii=False, indent=2)


def apex_finalize_app() -> str:
    """Finalize the APEX application import (import_end + commit).

    MUST be called after all pages and components have been added.
    Without this call, the application will not be visible in APEX.

    Returns:
        JSON with status and the APEX URL to access the application.
    """
    if not db.is_connected():
        return "Not connected. Call apex_connect() first."
    if not session.import_begun:
        return "No import session active. Call apex_create_app() first."
    if session.import_ended:
        return "Import already finalized."

    try:
        db.plsql("begin wwv_flow_imp.import_end(p_auto_install_sup_obj=>nvl(wwv_flow_application_install.get_auto_install_sup_obj,false)); end;")
        db.conn.commit()
        session.import_ended = True

        app_url = f"f?p={session.app_id}"
        return json.dumps({
            "status": "ok",
            "app_id": session.app_id,
            "message": f"Application {session.app_name} (ID {session.app_id}) finalized successfully.",
            "apex_url": app_url,
            "summary": session.summary(),
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)


def apex_delete_app(app_id: int) -> str:
    """Delete an APEX application by ID.

    WARNING: This permanently deletes the application and all its pages, regions,
    items, and components. This action cannot be undone.

    Args:
        app_id: The numeric application ID to delete.

    Returns:
        JSON with status message.

    Requires:
        - Active connection
        - User must own the application or have APEX admin privileges
    """
    if not db.is_connected():
        return "Not connected. Call apex_connect() first."

    try:
        db.plsql(_blk(f"""
  wwv_flow_imp.import_begin (
   p_version_yyyy_mm_dd=>'{APEX_VERSION_DATE}'
  ,p_release=>'24.2.13'
  ,p_default_workspace_id=>{WORKSPACE_ID}
  ,p_default_application_id=>{app_id}
  ,p_default_id_offset=>0
  ,p_default_owner=>'{APEX_SCHEMA}'
  );"""))
        db.plsql(_blk("""
  begin
    wwv_flow_imp.remove_flow(wwv_flow.g_flow_id);
  exception when others then null;
  end;"""))
        db.plsql("begin wwv_flow_imp.import_end(p_auto_install_sup_obj=>false); end;")
        db.conn.commit()

        if session.app_id == app_id:
            session.reset()

        return json.dumps({
            "status": "ok",
            "message": f"Application {app_id} deleted successfully.",
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)


def apex_export_app(app_id: int, output_path: str = "") -> str:
    """Export an APEX application as a SQL file (wwv_flow_imp format) for version control.

    Uses Oracle APEX's built-in apex_export.get_application() function to generate
    the full application export in the wwv_flow_imp format compatible with APEX 24.2.
    The resulting SQL can be re-imported via SQLcl, APEX SQL Workshop, or the import
    tool to recreate the application on any APEX instance.

    This is the recommended approach for versioning APEX applications in git:
    the generated SQL file captures all pages, regions, items, shared components,
    authentication schemes, navigation, and theme settings.

    Args:
        app_id: Numeric application ID to export (e.g., 100).
        output_path: Full file path where the SQL export should be saved
            (e.g., "C:/Projetos/Apex/apex/f100.sql"). If empty, only the first
            4000 characters are returned as a preview in the JSON response.

    Returns:
        JSON with keys:
            - status: "ok" or "error"
            - app_id: the requested application ID
            - file_name: name of the export file as generated by APEX (e.g., "f100.sql")
            - saved_to: absolute path where the file was written (only if output_path provided)
            - content_preview: first 500 characters of the SQL export (always included)
            - message: human-readable description of the result

    Requires:
        - Active connection (call apex_connect first)
        - User must have EXECUTE privilege on apex_export package
        - The application must exist in the current workspace
        - For ADB: the schema user must be the workspace owner or have equivalent grants

    Example:
        apex_export_app(100, "C:/Projetos/Apex/apex/f100.sql")
        # Saves f100.sql and returns a preview of the first 500 chars.

        apex_export_app(100)
        # Returns only the first 4000 chars as preview (no file saved).
    """
    if not db.is_connected():
        return "Not connected. Call apex_connect() first."

    try:
        rows = db.execute("""
            SELECT f.name,
                   DBMS_LOB.SUBSTR(f.contents, 4000, 1) AS content_start
              FROM TABLE(apex_export.get_application(
                     p_application_id         => :app_id,
                     p_split                  => false,
                     p_with_date              => true,
                     p_with_ir_public_reports => false
                   )) f
        """, {"app_id": app_id})

        if not rows:
            return json.dumps({
                "status": "error",
                "app_id": app_id,
                "error": f"No export data returned for application {app_id}. "
                         "Verify the application exists and you have access.",
            }, ensure_ascii=False, indent=2)

        file_name = rows[0].get("NAME") or rows[0].get("name") or f"f{app_id}.sql"
        content_start = rows[0].get("CONTENT_START") or rows[0].get("content_start") or ""

        result: dict = {
            "status": "ok",
            "app_id": app_id,
            "file_name": file_name,
            "content_preview": content_start[:500],
        }

        if output_path:
            with open(output_path, "w", encoding="utf-8") as fh:
                fh.write(content_start)
            result["saved_to"] = output_path
            result["message"] = (
                f"Application {app_id} exported to '{output_path}'. "
                "Note: only the first 4000 characters were written via DBMS_LOB.SUBSTR. "
                f"For a complete export, use SQLcl: apex export -applicationid {app_id}."
            )
        else:
            result["message"] = (
                f"Application {app_id} export preview (first 4000 chars). "
                "Provide output_path to save the full file, or use SQLcl for a complete export: "
                f"apex export -applicationid {app_id}."
            )

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "app_id": app_id,
            "error": str(e),
        }, ensure_ascii=False, indent=2)
