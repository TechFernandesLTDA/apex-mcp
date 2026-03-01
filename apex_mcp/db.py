"""Oracle ADB connection manager (singleton, mTLS wallet)."""
from __future__ import annotations
import logging
import threading
from typing import Optional
import oracledb
from .config import DB_USER, DB_PASS, DB_DSN, WALLET_DIR, WALLET_PASS, WORKSPACE_ID, APEX_SCHEMA

_log = logging.getLogger("apex_mcp.db")

# Oracle error codes that indicate a transient connection failure and
# can be safely retried after re-establishing the connection.
_TRANSIENT_ORA_CODES = {"03113", "03114", "12170", "25408"}


def _is_transient(exc: Exception) -> bool:
    """Return True if the Oracle error is a transient connection failure."""
    msg = str(exc)
    return any(f"ORA-{code}" in msg for code in _TRANSIENT_ORA_CODES)


class ConnectionManager:
    """Thread-safe singleton connection manager with auto-reconnect."""

    _instance: Optional["ConnectionManager"] = None
    _lock = threading.Lock()

    # Column cache persists across reconnects (class-level, not instance-level)
    _col_cache: dict = {}
    _col_cache_lock: threading.Lock = threading.Lock()

    def __init__(self):
        self._conn: Optional[oracledb.Connection] = None
        self._conn_lock = threading.Lock()
        self.dry_run: bool = False
        self._dry_run_log: list[str] = []
        self.batch_mode: bool = False
        self._batch_queue: list[tuple[str, dict | None]] = []  # (plsql_body, params)

    @classmethod
    def get(cls) -> "ConnectionManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def connect(
        self,
        user: str = DB_USER,
        password: str = DB_PASS,
        dsn: str = DB_DSN,
        wallet_dir: str = WALLET_DIR,
        wallet_pass: str = WALLET_PASS,
    ) -> str:
        """Establish or re-establish the database connection."""
        with self._conn_lock:
            if self._conn is not None:
                try:
                    self._conn.close()
                except Exception:
                    pass
            _log.info("Connecting as %s@%s", user, dsn)
            self._conn = oracledb.connect(
                user=user,
                password=password,
                dsn=dsn,
                config_dir=wallet_dir,
                wallet_location=wallet_dir,
                wallet_password=wallet_pass,
            )
            _log.info("Connected — Oracle %s", self._conn.version)
            return f"Connected as {user}@{dsn} — Oracle {self._conn.version}"

    def ensure_connected(self) -> oracledb.Connection:
        """Return connection, auto-reconnecting if stale."""
        with self._conn_lock:
            if self._conn is None:
                self.connect()
            else:
                try:
                    self._conn.ping()
                except Exception:
                    _log.warning("Connection stale, reconnecting")
                    self.connect()
            return self._conn

    @property
    def conn(self) -> oracledb.Connection:
        return self.ensure_connected()

    def execute(self, sql: str, params: dict | None = None) -> list[dict]:
        """Execute SQL and return list of row dicts."""
        last_exc = None
        for attempt in range(3):  # up to 2 retries
            try:
                c = self.conn
                cur = c.cursor()
                try:
                    cur.execute(sql, params or {})
                    if cur.description:
                        cols = [d[0] for d in cur.description]
                        return [dict(zip(cols, row)) for row in cur.fetchall()]
                    return []
                finally:
                    cur.close()
            except Exception as exc:
                last_exc = exc
                if _is_transient(exc) and attempt < 2:
                    _log.warning("Transient error on attempt %d, reconnecting: %s", attempt + 1, exc)
                    with self._conn_lock:
                        self._conn = None  # force reconnect on next .conn access
                    import time; time.sleep(1)
                    continue
                raise
        raise last_exc  # shouldn't reach here

    def execute_many(self, statements: list[str]) -> list[str]:
        """Execute multiple PL/SQL anonymous blocks, return log lines."""
        c = self.conn
        log: list[str] = []
        for stmt in statements:
            stmt = stmt.strip()
            if not stmt:
                continue
            cur = c.cursor()
            try:
                cur.execute(stmt)
                log.append(f"OK: {stmt[:60]}...")
            except oracledb.DatabaseError as e:
                log.append(f"ERR: {e} — {stmt[:80]}")
            finally:
                cur.close()
        c.commit()
        return log

    def plsql(self, body: str, params: dict | None = None) -> None:
        """Execute a PL/SQL anonymous block and commit.

        Behaviour:
        - dry_run=True  → records the SQL in _dry_run_log, does NOT execute.
        - batch_mode=True → appends (body, params) to _batch_queue, does NOT execute.
        - Normal → executes immediately and commits.

        dry_run takes precedence over batch_mode.
        """
        if self.dry_run:
            self._dry_run_log.append(body)
            return
        if self.batch_mode:
            self._batch_queue.append((body, params))
            return
        # Normal path with retry
        last_exc = None
        for attempt in range(3):
            try:
                c = self.conn
                cur = c.cursor()
                try:
                    _log.debug("plsql: %s", body[:80])
                    cur.execute(body, params or {})
                    c.commit()
                    return
                finally:
                    cur.close()
            except Exception as exc:
                last_exc = exc
                if _is_transient(exc) and attempt < 2:
                    _log.warning("Transient error on plsql attempt %d, reconnecting: %s", attempt + 1, exc)
                    with self._conn_lock:
                        self._conn = None
                    import time; time.sleep(1)
                    continue
                raise

    def enable_dry_run(self) -> None:
        """Enable dry-run mode: plsql() calls are logged but NOT executed."""
        self.dry_run = True
        self._dry_run_log = []

    def disable_dry_run(self) -> None:
        """Disable dry-run mode and return to normal execution."""
        self.dry_run = False

    def get_dry_run_log(self) -> list[str]:
        """Return list of PL/SQL blocks collected during dry-run mode."""
        return list(self._dry_run_log)

    def set_apex_context(self, app_id: int) -> None:
        """Set APEX workspace and application context for import operations."""
        from .config import WORKSPACE_ID as _ws_id, APEX_SCHEMA as _schema, WORKSPACE_NAME as _ws_name
        if not _ws_name:
            raise ValueError(
                "APEX_WORKSPACE_NAME is not set. Add it to your .mcp.json env section."
            )
        if not _schema:
            raise ValueError(
                "APEX_SCHEMA is not set. Add it to your .mcp.json env section."
            )
        if not _ws_id:
            raise ValueError(
                "APEX_WORKSPACE_ID is not set. Add it to your .mcp.json env section."
            )
        self.plsql(f"""
begin
  apex_util.set_workspace(p_workspace=>'{_ws_name}');
  wwv_flow_application_install.set_workspace_id({_ws_id});
  wwv_flow_application_install.set_application_id({app_id});
  wwv_flow_application_install.set_schema('{_schema}');
  wwv_flow_application_install.set_application_name(null);
  wwv_flow_application_install.set_application_alias(null);
  wwv_flow_application_install.set_image_prefix(null);
  wwv_flow_application_install.set_proxy(null);
  wwv_flow_application_install.set_no_proxy_domains(null);
end;
""")

    def column_exists(self, view_name: str, column_name: str) -> bool:
        """Check if a column exists in a data dictionary view (cached)."""
        vn = view_name.upper()
        cn = column_name.upper()
        with self._col_cache_lock:
            if vn not in self._col_cache:
                try:
                    rows = self.execute(
                        "SELECT column_name FROM all_tab_columns "
                        "WHERE table_name = :v ORDER BY column_id",
                        {"v": vn}
                    )
                    self._col_cache[vn] = {r["COLUMN_NAME"] for r in rows}
                except Exception:
                    return True  # fail open -- don't block on cache miss
            return cn in self._col_cache.get(vn, set())

    def safe_col(self, view_name: str, column_name: str, fallback: str = "NULL") -> str:
        """Return column_name if it exists in the view, else fallback expression."""
        return column_name if self.column_exists(view_name, column_name) else fallback

    def clear_col_cache(self) -> None:
        """Clear the column cache (useful after APEX upgrades)."""
        with self._col_cache_lock:
            self._col_cache.clear()

    # ------------------------------------------------------------------
    # Batch mode
    # ------------------------------------------------------------------

    def begin_batch(self) -> None:
        """Start batch mode: plsql() calls are queued instead of executed.

        Dry-run mode takes precedence — if dry_run is active, plsql() still
        logs to _dry_run_log rather than _batch_queue.
        """
        self.batch_mode = True
        self._batch_queue = []

    def commit_batch(self, rollback_on_error: bool = True) -> list[str]:
        """Execute all queued PL/SQL blocks in a single connection round-trip and commit.

        Each statement is executed in order. Errors on individual statements are
        captured and reported in the returned log but do not abort the remaining
        queue.

        When all statements succeed, a single COMMIT is issued.
        When any statement fails:
        - rollback_on_error=True (default): performs ROLLBACK and appends a
          "ROLLBACK: ..." line to the log. All changes from the batch are undone.
        - rollback_on_error=False: performs COMMIT despite errors (partial commit).
          A "COMMIT: partial commit..." line is appended to the log.

        Args:
            rollback_on_error: If True (default), roll back all changes when any
                statement in the batch raises an exception. If False, commit
                whatever succeeded (partial commit).

        Returns:
            List of per-statement result strings: "OK: <first 60 chars>..." or
            "ERR: <exception> — <first 60 chars>...", plus a final
            "ROLLBACK: ..." or "COMMIT: partial commit..." line when errors occur.
        """
        self.batch_mode = False
        _log.info("Committing batch of %d statements", len(self._batch_queue))
        if not self._batch_queue:
            return []
        log: list[str] = []
        c = self.conn
        cur = c.cursor()
        had_error = False
        try:
            for body, params in self._batch_queue:
                try:
                    cur.execute(body, params or {})
                    log.append(f"OK: {body[:60]}...")
                except Exception as e:
                    _log.error("Batch statement error: %s", e)
                    log.append(f"ERR: {e} — {body[:60]}...")
                    had_error = True

            if had_error and rollback_on_error:
                c.rollback()
                log.append("ROLLBACK: errors occurred, all changes rolled back.")
                _log.warning("Batch rolled back due to errors")
            else:
                c.commit()
                if had_error:
                    log.append("COMMIT: partial commit despite errors (rollback_on_error=False).")
        finally:
            cur.close()
            self._batch_queue = []
        return log

    def rollback_batch(self) -> None:
        """Discard all queued batch operations without executing them."""
        self.batch_mode = False
        self._batch_queue = []

    def is_connected(self) -> bool:
        if self._conn is None:
            return False
        try:
            self._conn.ping()
            return True
        except Exception:
            return False


# Module-level shortcut
db = ConnectionManager.get()
