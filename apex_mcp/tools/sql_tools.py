"""Tools: apex_connect, apex_run_sql, apex_status."""
from __future__ import annotations
import json
from ..db import db
from ..session import session
from ..config import DB_USER, DB_PASS, DB_DSN, WALLET_DIR, WALLET_PASS, WORKSPACE_ID


def apex_connect(
    user: str = DB_USER,
    password: str = DB_PASS,
    dsn: str = DB_DSN,
    wallet_dir: str = WALLET_DIR,
    wallet_password: str = WALLET_PASS,
) -> str:
    """Connect to Oracle Autonomous Database via mTLS wallet.

    Args:
        user: Database username (default: from ORACLE_DB_USER env or TEA_APP)
        password: Database password (default: from ORACLE_DB_PASS env)
        dsn: TNS alias from tnsnames.ora inside the wallet (default: from ORACLE_DSN env)
        wallet_dir: Path to the directory containing the Oracle wallet files (default: from ORACLE_WALLET_DIR env)
        wallet_password: Wallet decryption password (default: from ORACLE_WALLET_PASSWORD env)

    Returns:
        Connection confirmation string with Oracle version.

    Setup guide for Oracle Autonomous Database:
        1. Download the wallet ZIP from OCI Console > Autonomous Database > DB Connection
        2. Extract to a local directory (e.g., C:/myproject/wallet)
        3. Note the DSN alias from tnsnames.ora (e.g., mydb_tp for OLTP workload)
        4. Set env vars: ORACLE_DB_USER, ORACLE_DB_PASS, ORACLE_DSN,
           ORACLE_WALLET_DIR, ORACLE_WALLET_PASSWORD
        5. Call apex_connect() — it will use the env vars automatically

    mTLS is required for Oracle Autonomous Database (TLS direct mode may not work).
    """
    result = db.connect(
        user=user,
        password=password,
        dsn=dsn,
        wallet_dir=wallet_dir,
        wallet_pass=wallet_password,
    )
    return result


def apex_run_sql(sql: str, max_rows: int = 100) -> str:
    """Execute an arbitrary SELECT query or PL/SQL anonymous block against the database.

    Args:
        sql: SQL SELECT statement or PL/SQL anonymous block (BEGIN...END).
             For SELECT: returns rows as JSON array.
             For PL/SQL: executes and returns 'OK' or error message.
        max_rows: Maximum rows to return for SELECT (default 100, max 1000).

    Returns:
        JSON array of row objects for SELECT, or status string for DML/PL/SQL.

    Examples:
        apex_run_sql("SELECT table_name FROM user_tables ORDER BY 1")
        apex_run_sql("SELECT * FROM tea_beneficiarios WHERE rownum <= 5")
        apex_run_sql("BEGIN dbms_output.put_line('hello'); END;")
    """
    if not db.is_connected():
        return "Not connected. Call apex_connect() first."

    sql_stripped = sql.strip().upper()
    is_select = sql_stripped.startswith("SELECT") or sql_stripped.startswith("WITH")

    if is_select:
        max_rows = min(max_rows, 1000)
        rows = db.execute(sql)
        if len(rows) > max_rows:
            rows = rows[:max_rows]
        return json.dumps(rows, default=str, ensure_ascii=False, indent=2)
    else:
        try:
            db.plsql(sql)
            return "OK"
        except Exception as e:
            return f"ERROR: {e}"


def apex_status() -> str:
    """Return the current MCP session state: connection status, active app, and components created.

    Returns:
        JSON object with:
        - connected: bool
        - db_version: Oracle version string (if connected)
        - session: current import session summary (app_id, pages, regions, items, lovs, etc.)

    Use this to check what has been built so far before adding more components.
    """
    result: dict = {"connected": db.is_connected()}

    if db.is_connected():
        try:
            rows = db.execute("SELECT banner FROM v$version WHERE rownum = 1")
            result["db_version"] = rows[0]["BANNER"] if rows else "unknown"
        except Exception:
            result["db_version"] = "unknown"

    result["session"] = session.summary()
    return json.dumps(result, default=str, ensure_ascii=False, indent=2)
