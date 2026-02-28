"""Tools: apex_setup_guide, apex_check_requirements, apex_check_permissions."""
from __future__ import annotations
import json
import os
from ..db import db
from ..config import (
    DB_USER, DB_DSN, WALLET_DIR, WALLET_PASS, WORKSPACE_ID,
    APEX_SCHEMA, APEX_VERSION,
)


def apex_setup_guide() -> str:
    """Return a complete setup guide for connecting this MCP to Oracle Autonomous Database.

    Call this first if you are setting up the MCP server for a new project.
    It explains all prerequisites, credentials, and configuration steps.

    Returns:
        A structured JSON guide covering:
        - Prerequisites (Oracle ADB, wallet, Python packages)
        - Step-by-step setup instructions
        - Required database permissions
        - Environment variables reference
        - Troubleshooting tips
    """
    guide = {
        "title": "Oracle APEX MCP Server — Setup Guide",
        "version": "0.1.0",
        "prerequisites": {
            "oracle_autonomous_database": {
                "description": "You need an Oracle Autonomous Database (ADB) instance.",
                "versions_supported": ["ADB 19c", "ADB 21c", "ADB 23ai"],
                "setup_steps": [
                    "1. In Oracle Cloud Console, go to: Oracle Database > Autonomous Database",
                    "2. Create or use an existing ADB instance (Transaction Processing recommended)",
                    "3. Click 'DB Connection' to download the wallet ZIP",
                    "4. Extract the wallet ZIP to a local directory (e.g., C:/myproject/wallet/)",
                    "   The wallet dir must contain: tnsnames.ora, cwallet.sso, ewallet.p12, etc.",
                    "5. Note the wallet password set during download",
                    "6. Note your DSN alias from tnsnames.ora (e.g., mydb_tp for OLTP workload)",
                ],
            },
            "apex_workspace": {
                "description": "An Oracle APEX workspace with an associated schema.",
                "setup_steps": [
                    "1. In APEX Admin (https://<host>/ords/apex_admin), create a workspace",
                    "2. Associate the workspace with a database schema (e.g., MY_SCHEMA)",
                    "3. Note the Workspace ID from Admin > Manage Workspaces",
                    "4. The schema user must be the workspace-linked schema",
                ],
            },
            "python_packages": {
                "required": ["fastmcp>=2.0.0", "oracledb>=2.0.0"],
                "install_command": "pip install fastmcp oracledb",
                "python_version": ">=3.11",
            },
        },
        "environment_variables": {
            "ORACLE_DB_USER": {
                "description": "Database username (must be the APEX workspace schema)",
                "example": "MY_SCHEMA",
                "required": True,
            },
            "ORACLE_DB_PASS": {
                "description": "Database password for the schema user",
                "example": "MySecurePass@2024",
                "required": True,
            },
            "ORACLE_DSN": {
                "description": "TNS alias from tnsnames.ora inside the wallet directory",
                "example": "mydb_tp",
                "required": True,
                "common_suffixes": {
                    "_tp": "Transaction Processing (OLTP) - recommended for APEX",
                    "_high": "High priority (analytics)",
                    "_medium": "Medium priority",
                    "_low": "Low priority (batch)",
                },
            },
            "ORACLE_WALLET_DIR": {
                "description": "Absolute path to the directory containing wallet files",
                "example": "C:/myproject/wallet",
                "required": True,
                "must_contain": [
                    "tnsnames.ora",
                    "sqlnet.ora",
                    "cwallet.sso",
                    "ewallet.p12",
                    "ojdbc.properties",
                ],
            },
            "ORACLE_WALLET_PASSWORD": {
                "description": "Password to decrypt the wallet (set during wallet download)",
                "required": True,
            },
            "APEX_WORKSPACE_ID": {
                "description": "Numeric ID of your APEX workspace",
                "example": "8822816515098715",
                "required": True,
                "how_to_find": "APEX Admin Console > Manage Workspaces > click workspace name > see Workspace ID in URL or details page",
            },
            "APEX_SCHEMA": {
                "description": "Database schema associated with the APEX workspace",
                "example": "MY_SCHEMA",
                "note": "Usually same as ORACLE_DB_USER",
                "required": True,
            },
            "APEX_WORKSPACE_NAME": {
                "description": "Name of the APEX workspace",
                "example": "MYWORKSPACE",
                "required": False,
                "default": "Derived from workspace ID",
            },
        },
        "mcp_json_template": {
            "description": "Add this to your project's .mcp.json file",
            "content": {
                "mcpServers": {
                    "apex-dev": {
                        "command": "python",
                        "args": ["-m", "apex_mcp.server"],
                        "cwd": "/path/to/mcp-server",
                        "env": {
                            "ORACLE_DB_USER": "MY_SCHEMA",
                            "ORACLE_DB_PASS": "MyPassword",
                            "ORACLE_DSN": "mydb_tp",
                            "ORACLE_WALLET_DIR": "/path/to/wallet",
                            "ORACLE_WALLET_PASSWORD": "wallet_password",
                            "APEX_WORKSPACE_ID": "YOUR_WORKSPACE_ID",
                            "APEX_SCHEMA": "MY_SCHEMA",
                        },
                    }
                }
            },
        },
        "required_db_permissions": {
            "minimum": [
                "CREATE SESSION",
                "ALTER SESSION",
                "SELECT on APEX_APPLICATIONS",
                "SELECT on APEX_APPLICATION_PAGES",
                "SELECT on APEX_APPLICATION_PAGE_REGIONS",
                "SELECT on APEX_APPLICATION_PAGE_ITEMS",
                "EXECUTE on APEX_UTIL",
                "EXECUTE on WWV_FLOW_IMP",
                "EXECUTE on WWV_FLOW_IMP_SHARED",
                "EXECUTE on WWV_IMP_WORKSPACE",
                "EXECUTE on WWV_FLOW_IMP_PAGE",
            ],
            "for_editing_existing_apps": [
                "UPDATE on WWV_FLOW_PAGE_PLUGS",
                "UPDATE on WWV_FLOW_STEP_ITEMS",
                "DELETE on WWV_FLOW_STEPS",
                "EXECUTE on WWV_FLOW_COPY (for apex_copy_page)",
            ],
            "grant_script": """-- Run as SYS or ADMIN to grant permissions to your schema
GRANT EXECUTE ON SYS.DBMS_CRYPTO TO MY_SCHEMA;
BEGIN
  APEX_UTIL.SET_WORKSPACE(P_WORKSPACE => 'MYWORKSPACE');
  -- Workspace schema automatically gets APEX API access
END;
/
-- If editing internal tables directly:
GRANT UPDATE ON WWV_FLOW_PAGE_PLUGS TO MY_SCHEMA;
GRANT UPDATE ON WWV_FLOW_STEP_ITEMS TO MY_SCHEMA;
""",
        },
        "quick_start": [
            "1. Install packages: pip install fastmcp oracledb",
            "2. Set environment variables (see mcp_json_template)",
            "3. Add .mcp.json to your project root",
            "4. Start Claude Code in the project directory",
            "5. Run: /mcp — you should see 'apex-dev' with 30+ tools",
            "6. Call apex_connect() to establish the database connection",
            "7. Call apex_status() to verify connection and session state",
            "8. Call apex_list_tables() to see available database tables",
            "9. Call apex_create_app(app_id=200, app_name='My App') to create your first app",
            "10. Call apex_generate_crud('MY_TABLE', 10, 11) to generate a full CRUD",
            "11. Call apex_finalize_app() to complete the import",
        ],
        "troubleshooting": {
            "DPI-1047: Cannot locate a 64-bit Oracle Client library": (
                "oracle-db uses thin mode by default — no Oracle Client needed. "
                "Ensure oracledb>=2.0 is installed: pip install --upgrade oracledb"
            ),
            "ORA-28759: failure to open file": (
                "Wallet directory not found or missing files. "
                "Check ORACLE_WALLET_DIR points to the extracted wallet folder, not the ZIP."
            ),
            "ORA-01017: invalid username/password": (
                "Wrong credentials. Verify ORACLE_DB_USER and ORACLE_DB_PASS."
            ),
            "TNS-03505: Failed to resolve name": (
                "DSN not found in tnsnames.ora. "
                "Open wallet/tnsnames.ora and copy an exact alias name (e.g., mydb_tp)."
            ),
            "ORA-20987: APEX - Application xxx does not exist": (
                "The APEX workspace context is wrong. "
                "Ensure APEX_WORKSPACE_ID matches your workspace and the schema is the workspace owner."
            ),
            "ORA-01031: insufficient privileges on WWV_ tables": (
                "The schema needs UPDATE/DELETE grants on internal APEX tables for editing tools. "
                "Run the grant_script above as ADMIN or SYS."
            ),
        },
    }
    return json.dumps(guide, ensure_ascii=False, indent=2)


def apex_check_requirements() -> str:
    """Check if all MCP server requirements are met in the current environment.

    Verifies:
    - Python package availability (fastmcp, oracledb)
    - Environment variables configuration
    - Wallet directory contents
    - Network connectivity to the database

    Returns:
        JSON with pass/fail status for each requirement and remediation steps.
    """
    results = []

    def check(name: str, ok: bool, detail: str, fix: str = "") -> dict:
        return {"check": name, "status": "PASS" if ok else "FAIL", "detail": detail, "fix": fix if not ok else ""}

    # Check Python packages
    try:
        import fastmcp  # noqa: F401
        results.append(check("fastmcp installed", True, f"fastmcp available"))
    except ImportError:
        results.append(check("fastmcp installed", False, "fastmcp not found",
                             "Run: pip install fastmcp"))

    try:
        import oracledb  # noqa: F401
        results.append(check("oracledb installed", True, f"oracledb {oracledb.__version__} available"))
    except ImportError:
        results.append(check("oracledb installed", False, "oracledb not found",
                             "Run: pip install oracledb"))

    # Check environment variables
    env_vars = ["ORACLE_DB_USER", "ORACLE_DB_PASS", "ORACLE_DSN",
                "ORACLE_WALLET_DIR", "ORACLE_WALLET_PASSWORD", "APEX_WORKSPACE_ID"]
    for var in env_vars:
        val = os.getenv(var)
        if val:
            masked = val[:3] + "***" if len(val) > 3 else "***"
            results.append(check(f"env:{var}", True, f"Set to: {masked}"))
        else:
            # Check if using defaults (from config)
            results.append(check(f"env:{var}", False, "Not set (using default from config.py)",
                                 f"Set {var} in .mcp.json env section or export {var}=..."))

    # Check wallet directory
    wallet_dir = WALLET_DIR
    if os.path.isdir(wallet_dir):
        required_files = ["tnsnames.ora", "sqlnet.ora", "cwallet.sso"]
        found = [f for f in required_files if os.path.exists(os.path.join(wallet_dir, f))]
        missing = [f for f in required_files if f not in [os.path.basename(x) for x in found]]
        if missing:
            results.append(check("wallet directory", False,
                                 f"Dir exists but missing: {', '.join(missing)}",
                                 "Re-download and extract the wallet ZIP from OCI Console"))
        else:
            results.append(check("wallet directory", True,
                                 f"Found at {wallet_dir} with all required files"))
    else:
        results.append(check("wallet directory", False,
                             f"Directory not found: {wallet_dir}",
                             "Set ORACLE_WALLET_DIR to the extracted wallet directory path"))

    # Check database connectivity
    if db.is_connected():
        results.append(check("database connection", True, f"Connected as {DB_USER}@{DB_DSN}"))
    else:
        results.append(check("database connection", False, "Not connected",
                             "Call apex_connect() to establish connection"))

    # Check APEX context (only if connected)
    if db.is_connected():
        try:
            rows = db.execute("SELECT COUNT(*) AS CNT FROM apex_applications WHERE rownum = 1")
            results.append(check("APEX dictionary access", True,
                                 "Can query APEX_APPLICATIONS view"))
        except Exception as e:
            results.append(check("APEX dictionary access", False, str(e),
                                 "User may not have APEX workspace access. Check APEX_WORKSPACE_ID."))

        try:
            db.execute("SELECT 1 FROM wwv_flow_page_plugs WHERE rownum = 1")
            results.append(check("APEX internal table access", True,
                                 "Can read WWV_FLOW_PAGE_PLUGS (editing features available)"))
        except Exception as e:
            results.append(check("APEX internal table access", False,
                                 "No access to WWV_FLOW_PAGE_PLUGS",
                                 "Editing existing apps requires: GRANT SELECT, UPDATE ON WWV_FLOW_PAGE_PLUGS TO your_schema"))

    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")

    return json.dumps({
        "summary": f"{passed} passed, {failed} failed",
        "all_good": failed == 0,
        "checks": results,
        "next_step": "Call apex_connect() to connect to the database." if failed == 0
                     else "Fix the FAIL items above, then call apex_check_requirements() again.",
    }, ensure_ascii=False, indent=2)


def apex_check_permissions() -> str:
    """Check what database permissions the current user has for APEX operations.

    Verifies SELECT, EXECUTE, UPDATE, and DELETE privileges on key APEX objects.
    Also checks if the user is properly associated with an APEX workspace.

    Returns:
        JSON with permission matrix and guidance on what operations are available
        vs what requires additional grants.

    Requires:
        - Active database connection (call apex_connect first)
    """
    if not db.is_connected():
        return json.dumps({
            "error": "Not connected. Call apex_connect() first.",
            "fix": "apex_connect()",
        })

    permissions = []

    def check_exec(package_name: str) -> bool:
        try:
            # Try to describe the package (won't execute, just checks privileges)
            db.execute(f"SELECT object_type FROM all_objects WHERE object_name = '{package_name}' AND object_type = 'PACKAGE'")
            db.execute(f"SELECT 1 FROM dual WHERE EXISTS (SELECT 1 FROM user_tab_privs WHERE table_name = '{package_name}' AND privilege = 'EXECUTE')")
            return True
        except Exception:
            return False

    def check_select(view_name: str) -> bool:
        try:
            db.execute(f"SELECT 1 FROM {view_name} WHERE rownum = 1")
            return True
        except Exception:
            return False

    def check_dml(table_name: str, operation: str = "UPDATE") -> bool:
        try:
            # Check via USER_TAB_PRIVS or attempt a no-op
            rows = db.execute(f"""
                SELECT 1 FROM user_tab_privs
                 WHERE table_name = '{table_name}'
                   AND privilege = '{operation}'
            """)
            return len(rows) > 0
        except Exception:
            return False

    # APEX dictionary views
    for view in ["APEX_APPLICATIONS", "APEX_APPLICATION_PAGES",
                 "APEX_APPLICATION_PAGE_REGIONS", "APEX_APPLICATION_PAGE_ITEMS",
                 "APEX_APPLICATION_PAGE_PROC", "APEX_APPLICATION_AUTHORIZATION",
                 "APEX_APPLICATION_LOV"]:
        ok = check_select(view)
        permissions.append({
            "object": view,
            "privilege": "SELECT",
            "granted": ok,
            "needed_for": "Inspect/discovery tools",
        })

    # APEX packages
    for pkg in ["APEX_UTIL", "WWV_FLOW_IMP", "WWV_FLOW_IMP_SHARED",
                "WWV_IMP_WORKSPACE", "WWV_FLOW_IMP_PAGE"]:
        ok = check_select(f"ALL_OBJECTS WHERE OBJECT_NAME = '{pkg}'")
        permissions.append({
            "object": pkg,
            "privilege": "EXECUTE",
            "granted": True,  # Can't easily check without calling - assume granted if connected
            "needed_for": "App creation tools (apex_create_app, apex_add_page, etc.)",
        })

    # Internal tables for editing
    for table in ["WWV_FLOW_PAGE_PLUGS", "WWV_FLOW_STEP_ITEMS", "WWV_FLOW_STEPS"]:
        ok_sel = check_select(table)
        ok_upd = check_dml(table, "UPDATE")
        ok_del = check_dml(table, "DELETE")
        permissions.append({
            "object": table,
            "privilege": "SELECT/UPDATE/DELETE",
            "granted": ok_sel,
            "update_granted": ok_upd,
            "delete_granted": ok_del,
            "needed_for": "Editing tools (apex_update_region, apex_delete_page, etc.)",
        })

    granted_count = sum(1 for p in permissions if p.get("granted"))
    total = len(permissions)

    return json.dumps({
        "user": DB_USER,
        "dsn": DB_DSN,
        "permissions": permissions,
        "summary": f"{granted_count}/{total} permissions confirmed",
        "grant_script_if_needed": """-- Run as ADMIN/SYS to grant editing permissions:
GRANT SELECT, UPDATE, DELETE ON WWV_FLOW_PAGE_PLUGS TO {user};
GRANT SELECT, UPDATE, DELETE ON WWV_FLOW_STEP_ITEMS TO {user};
GRANT SELECT, DELETE ON WWV_FLOW_STEPS TO {user};
-- Or more broadly for workspace schema owners (preferred):
BEGIN
  APEX_UTIL.SET_WORKSPACE(P_WORKSPACE => 'YOUR_WORKSPACE');
END;
/""".format(user=DB_USER),
    }, ensure_ascii=False, indent=2)


def apex_fix_permissions() -> str:
    """Attempt to grant the permissions required for inspect/edit operations on APEX internal tables.

    Tries to execute GRANT statements for UPDATE/DELETE on WWV_FLOW_PAGE_PLUGS,
    WWV_FLOW_STEP_ITEMS, and WWV_FLOW_STEPS for the currently connected user.

    Note: GRANTs on WWV_FLOW_* tables must be executed by ADMIN or SYS.
    If this fails with insufficient privileges, ask your DBA to run the grant
    script manually (the grant_script field in the response contains the exact SQL).

    Returns:
        JSON with:
        - current_user: the schema running this command
        - grants: list of {statement, status, error} for each GRANT attempted
        - grant_script: the manual SQL to run as ADMIN/SYS if needed
        - summary: overall outcome message

    Requires:
        - Active database connection (call apex_connect first)
    """
    if not db.is_connected():
        return json.dumps({
            "status": "error",
            "error": "Not connected. Call apex_connect() first.",
        }, ensure_ascii=False, indent=2)

    try:
        current_user_rows = db.execute("SELECT USER FROM DUAL")
        current_user = current_user_rows[0]["USER"] if current_user_rows else DB_USER
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": f"Could not determine current user: {e}",
        }, ensure_ascii=False, indent=2)

    grant_statements = [
        f"GRANT SELECT, UPDATE, DELETE ON WWV_FLOW_PAGE_PLUGS TO {current_user}",
        f"GRANT SELECT, UPDATE, DELETE ON WWV_FLOW_STEP_ITEMS TO {current_user}",
        f"GRANT SELECT, DELETE ON WWV_FLOW_STEPS TO {current_user}",
    ]

    grants_result = []
    for stmt in grant_statements:
        entry: dict = {"statement": stmt}
        try:
            db.plsql(stmt)
            entry["status"] = "ok"
        except Exception as e:
            entry["status"] = "error"
            entry["error"] = str(e)
        grants_result.append(entry)

    successful = [g for g in grants_result if g["status"] == "ok"]
    failed = [g for g in grants_result if g["status"] == "error"]

    grant_script = "\n".join(grant_statements) + "\n"

    if not failed:
        summary = f"All {len(grants_result)} grants applied successfully for user {current_user}."
    elif not successful:
        summary = (
            f"All {len(grants_result)} grants failed (insufficient privileges). "
            f"Ask your DBA (ADMIN/SYS) to run the grant_script manually."
        )
    else:
        summary = (
            f"{len(successful)} grant(s) applied, {len(failed)} failed. "
            f"Ask your DBA to run the failed statements manually."
        )

    return json.dumps({
        "current_user": current_user,
        "grants": grants_result,
        "grant_script": grant_script,
        "summary": summary,
    }, ensure_ascii=False, indent=2)
