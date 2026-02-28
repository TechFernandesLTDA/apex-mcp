"""Oracle ADB connection manager (singleton, mTLS wallet)."""
from __future__ import annotations
import threading
from typing import Optional
import oracledb
from .config import DB_USER, DB_PASS, DB_DSN, WALLET_DIR, WALLET_PASS, WORKSPACE_ID, APEX_SCHEMA


class ConnectionManager:
    """Thread-safe singleton connection manager with auto-reconnect."""

    _instance: Optional["ConnectionManager"] = None
    _lock = threading.Lock()

    def __init__(self):
        self._conn: Optional[oracledb.Connection] = None
        self._conn_lock = threading.Lock()

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
            self._conn = oracledb.connect(
                user=user,
                password=password,
                dsn=dsn,
                config_dir=wallet_dir,
                wallet_location=wallet_dir,
                wallet_password=wallet_pass,
            )
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
                    self.connect()
            return self._conn

    @property
    def conn(self) -> oracledb.Connection:
        return self.ensure_connected()

    def execute(self, sql: str, params: dict | None = None) -> list[dict]:
        """Execute SQL and return list of row dicts."""
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
        """Execute a PL/SQL anonymous block and commit."""
        c = self.conn
        cur = c.cursor()
        try:
            cur.execute(body, params or {})
            c.commit()
        finally:
            cur.close()

    def set_apex_context(self, app_id: int) -> None:
        """Set APEX workspace and application context for import operations."""
        self.plsql(f"""
begin
  apex_util.set_workspace(p_workspace=>'TEA');
  wwv_flow_application_install.set_workspace_id({WORKSPACE_ID});
  wwv_flow_application_install.set_application_id({app_id});
  wwv_flow_application_install.set_schema('{APEX_SCHEMA}');
  wwv_flow_application_install.set_application_name(null);
  wwv_flow_application_install.set_application_alias(null);
  wwv_flow_application_install.set_image_prefix(null);
  wwv_flow_application_install.set_proxy(null);
  wwv_flow_application_install.set_no_proxy_domains(null);
end;
""")

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
