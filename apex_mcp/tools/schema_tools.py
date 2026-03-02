"""Tools: apex_list_tables, apex_describe_table."""
from __future__ import annotations
import json
import threading
import time
from ..db import db
from ..utils import _json

# ---------------------------------------------------------------------------
# Module-level TTL cache for apex_describe_table
# ---------------------------------------------------------------------------
_describe_cache: dict[str, tuple[float, dict]] = {}  # key: table_name -> (timestamp, result)
_describe_cache_lock = threading.Lock()
_CACHE_TTL = 300  # 5 minutes


def clear_schema_cache() -> None:
    """Clear the describe_table metadata cache."""
    with _describe_cache_lock:
        _describe_cache.clear()


def apex_list_tables(
    pattern: str = "%",
    include_columns: bool = True,
    object_type: str = "TABLE",
) -> str:
    """List database tables and/or views in the current schema with their columns.

    Args:
        pattern: SQL LIKE pattern to filter object names (default: all objects).
                 Examples: "EMP%", "%DEPT%", "HR_%"
        include_columns: Include column details for each object (default True).
                         Set False for a quick name list only.
        object_type: Which objects to list. One of:
                     "TABLE" (default) — only USER_TABLES,
                     "VIEW"            — only USER_VIEWS,
                     "ALL"             — tables and views combined.
                     Views will have num_rows = NULL.

    Returns:
        JSON object with keys:
            - status: "ok" or "error"
            - data: list of objects. If include_columns=True, each entry has:
                    {object_name, object_type, num_rows, columns: [{column_name, data_type,
                    nullable, data_length, data_precision}]}. If False: [{object_name,
                    object_type, num_rows}]
            - count: total number of objects found

    Use this to discover available tables/views before using apex_generate_crud or apex_describe_table.
    """
    if not db.is_connected():
        return _json({"status": "error", "error": "Not connected. Call apex_connect() first."})

    ot = object_type.upper()
    if ot not in ("TABLE", "VIEW", "ALL"):
        return _json({
            "status": "error",
            "error": "object_type must be 'TABLE', 'VIEW', or 'ALL'.",
        })

    try:
        # Build the objects query based on object_type
        if ot == "TABLE":
            objects_sql = """
                SELECT table_name AS object_name,
                       'TABLE'    AS object_type,
                       num_rows
                  FROM user_tables
                 WHERE table_name LIKE :pattern
                 ORDER BY table_name
            """
        elif ot == "VIEW":
            objects_sql = """
                SELECT view_name AS object_name,
                       'VIEW'    AS object_type,
                       NULL      AS num_rows
                  FROM user_views
                 WHERE view_name LIKE :pattern
                 ORDER BY view_name
            """
        else:  # ALL
            objects_sql = """
                SELECT table_name AS object_name,
                       'TABLE'    AS object_type,
                       num_rows
                  FROM user_tables
                 WHERE table_name LIKE :pattern
                UNION ALL
                SELECT view_name AS object_name,
                       'VIEW'    AS object_type,
                       NULL      AS num_rows
                  FROM user_views
                 WHERE view_name LIKE :pattern
                 ORDER BY 1
            """

        object_rows = db.execute(objects_sql, {"pattern": pattern.upper()})

        if not include_columns:
            result = [
                {
                    "object_name": r["OBJECT_NAME"],
                    "object_type": r["OBJECT_TYPE"],
                    "num_rows":    r["NUM_ROWS"],
                }
                for r in object_rows
            ]
            return _json({"status": "ok", "data": result, "count": len(result)})

        # Fetch all columns for matching objects in a single query.
        # USER_TAB_COLUMNS covers both tables and views.
        col_rows = db.execute("""
            SELECT c.table_name,
                   c.column_name,
                   c.data_type,
                   c.nullable,
                   c.data_length,
                   c.data_precision,
                   c.data_scale,
                   c.column_id
              FROM user_tab_columns c
             WHERE c.table_name LIKE :pattern
             ORDER BY c.table_name,
                      c.column_id
        """, {"pattern": pattern.upper()})

        # Index columns by object name
        columns_by_object: dict[str, list[dict]] = {}
        for col in col_rows:
            oname = col["TABLE_NAME"]
            if oname not in columns_by_object:
                columns_by_object[oname] = []
            columns_by_object[oname].append({
                "column_name":    col["COLUMN_NAME"],
                "data_type":      col["DATA_TYPE"],
                "nullable":       col["NULLABLE"],
                "data_length":    col["DATA_LENGTH"],
                "data_precision": col["DATA_PRECISION"],
            })

        # Build combined result
        result = []
        for orow in object_rows:
            oname = orow["OBJECT_NAME"]
            result.append({
                "object_name": oname,
                "object_type": orow["OBJECT_TYPE"],
                "num_rows":    orow["NUM_ROWS"],
                "columns":     columns_by_object.get(oname, []),
            })

        return _json({"status": "ok", "data": result, "count": len(result)})

    except Exception as e:
        return _json({"status": "error", "error": str(e)})


def apex_detect_relationships(tables: list[str]) -> str:
    """Detect FK relationships between a given set of tables and suggest APEX components.

    Queries ``user_constraints`` and ``user_cons_columns`` to find all foreign-key
    relationships that involve the specified tables — both internal (from-table and
    to-table both in the list) and external (one side is outside the list).

    Args:
        tables: List of table names to analyse (case-insensitive).
                Example: ["ORDERS", "CUSTOMERS", "ORDER_ITEMS", "PRODUCTS"]

    Returns:
        JSON with:
        {
          "status": "ok",
          "tables": ["TABLE_A", "TABLE_B", ...],
          "relationships": [
            {
              "from_table": "ORDERS",
              "from_column": "CUSTOMER_ID",
              "to_table": "CUSTOMERS",
              "to_column": "ID",
              "constraint_name": "FK_ORD_CUST",
              "internal": true,
              "suggested_component": "master_detail | select_lov | cascade_filter"
            }
          ],
          "suggestions": [
            "ORDERS -> CUSTOMERS: consider master-detail page",
            ...
          ]
        }

    ``suggested_component`` logic:
    - If ``from_table`` has many FK rows pointing to ``to_table``
      (i.e. ``to_table`` is a parent / lookup) -> "master_detail"
      when the FK is internal (both tables in the list), otherwise -> "select_lov"
    - External FK references (to_table not in the input list) -> "select_lov"

    ``internal`` is True when both the from_table and the to_table are in the
    provided ``tables`` list.
    """
    if not db.is_connected():
        return _json({"status": "error", "error": "Not connected. Call apex_connect() first."})

    if not tables:
        return _json({"status": "error", "error": "At least one table name is required."})

    upper_tables: list[str] = [t.upper() for t in tables]
    upper_set: set[str] = set(upper_tables)

    try:
        # ── 1. Find all FK constraints where the from-table is in our list ──
        # We use a single query joining user_constraints (FK side) with
        # user_constraints (PK/UK referenced side) and user_cons_columns for
        # both sides to get column names.
        #
        # Oracle does not support binding a list directly, so we query all FKs
        # for each table individually and aggregate in Python.
        all_fks: list[dict] = []

        for tbl in upper_tables:
            fk_rows = db.execute("""
                SELECT c.constraint_name,
                       cc.column_name     AS from_column,
                       rc.table_name      AS to_table,
                       rcc.column_name    AS to_column
                  FROM user_constraints   c
                  JOIN user_cons_columns  cc
                    ON cc.constraint_name = c.constraint_name
                   AND cc.position        = 1
                  JOIN user_constraints   rc
                    ON rc.constraint_name = c.r_constraint_name
                  JOIN user_cons_columns  rcc
                    ON rcc.constraint_name = rc.constraint_name
                   AND rcc.position        = 1
                 WHERE c.table_name      = :tname
                   AND c.constraint_type = 'R'
                 ORDER BY c.constraint_name
            """, {"tname": tbl})

            for row in fk_rows:
                all_fks.append({
                    "from_table":       tbl,
                    "from_column":      row["FROM_COLUMN"],
                    "to_table":         row["TO_TABLE"],
                    "to_column":        row["TO_COLUMN"],
                    "constraint_name":  row["CONSTRAINT_NAME"],
                })

        # ── 2. Deduplicate (same constraint may appear from multiple tables) ──
        seen_constraints: set[str] = set()
        unique_fks: list[dict] = []
        for fk in all_fks:
            if fk["constraint_name"] not in seen_constraints:
                seen_constraints.add(fk["constraint_name"])
                unique_fks.append(fk)

        # ── 3. Estimate row-counts for all involved tables (from stats) ───────
        # Used to decide master_detail vs select_lov: if from_table num_rows >>
        # to_table num_rows, to_table is a lookup and from_table is the detail.
        involved_tables: set[str] = upper_set.copy()
        for fk in unique_fks:
            involved_tables.add(fk["to_table"])

        row_count_map: dict[str, int] = {}
        for itbl in involved_tables:
            rc_rows = db.execute(
                "SELECT num_rows FROM user_tables WHERE table_name = :tname",
                {"tname": itbl},
            )
            if rc_rows and rc_rows[0]["NUM_ROWS"] is not None:
                row_count_map[itbl] = int(rc_rows[0]["NUM_ROWS"])
            else:
                row_count_map[itbl] = 0

        # ── 4. Build relationship list with suggested_component ───────────────
        relationships: list[dict] = []
        suggestions: list[str] = []

        for fk in unique_fks:
            from_tbl = fk["from_table"]
            to_tbl   = fk["to_table"]
            internal = to_tbl in upper_set

            from_rows = row_count_map.get(from_tbl, 0)
            to_rows   = row_count_map.get(to_tbl,   0)

            # Heuristic: if the referenced (parent) table has significantly
            # fewer rows it is a lookup/parent -> master_detail when internal,
            # select_lov otherwise.  When we cannot distinguish, default to
            # select_lov for external references.
            if internal and to_rows > 0 and from_rows >= to_rows:
                suggested = "master_detail"
                suggestion_text = (
                    f"{from_tbl} -> {to_tbl}: consider master-detail page "
                    f"(both tables in scope; {from_tbl} is the detail side)"
                )
            elif internal:
                suggested = "select_lov"
                suggestion_text = (
                    f"{from_tbl} -> {to_tbl}: consider select LOV on "
                    f"{fk['from_column']} (both tables in scope)"
                )
            else:
                suggested = "select_lov"
                suggestion_text = (
                    f"{from_tbl} -> {to_tbl}: external reference; "
                    f"add a select LOV for {fk['from_column']} pointing to {to_tbl}"
                )

            relationships.append({
                "from_table":          from_tbl,
                "from_column":         fk["from_column"],
                "to_table":            to_tbl,
                "to_column":           fk["to_column"],
                "constraint_name":     fk["constraint_name"],
                "internal":            internal,
                "suggested_component": suggested,
            })
            suggestions.append(suggestion_text)

        return _json({
            "status":        "ok",
            "tables":        upper_tables,
            "relationships": relationships,
            "suggestions":   suggestions,
        })

    except Exception as e:
        return _json({"status": "error", "error": str(e)})


def apex_describe_table(table_name: str, force_refresh: bool = False) -> str:
    """Get detailed metadata for a specific database table.

    Returns complete schema info including columns, primary keys, foreign keys,
    indexes, sequences, and triggers — everything needed to generate APEX forms and reports.

    Results are cached for 5 minutes per table name to avoid redundant DB round-trips.

    Args:
        table_name: Table name (case-insensitive).
        force_refresh: Bypass cache and fetch fresh from DB (default False).

    Returns:
        JSON with:
        {
          "table_name": "...",
          "columns": [{
            "column_name", "data_type", "data_length", "data_precision",
            "nullable", "column_id", "data_default"
          }],
          "primary_key": {
            "constraint_name": "...",
            "columns": ["COL1", "COL2"]
          },
          "foreign_keys": [{
            "constraint_name": "...",
            "columns": ["FK_COL"],
            "references_table": "PARENT_TABLE",
            "references_columns": ["PK_COL"]
          }],
          "indexes": [{
            "index_name": "...",
            "uniqueness": "UNIQUE|NONUNIQUE",
            "columns": ["COL1"]
          }],
          "sequences": [{
            "sequence_name": "...",
            "min_value", "max_value", "increment_by",
            "cycle_flag", "order_flag", "cache_size", "last_number"
          }],
          "triggers": [{
            "trigger_name": "...",
            "trigger_type": "...",
            "triggering_event": "...",
            "status": "ENABLED|DISABLED",
            "trigger_body": "... (first 200 chars)"
          }],
          "row_count": 1234
        }

    Use this before apex_generate_crud to understand the table structure.
    """
    if not db.is_connected():
        return _json({"status": "error", "error": "Not connected. Call apex_connect() first."})

    upper_name = table_name.upper().strip()
    cache_key = upper_name

    # Check cache first (unless force_refresh is requested)
    if not force_refresh:
        with _describe_cache_lock:
            cached = _describe_cache.get(cache_key)
            if cached:
                ts, result = cached
                if time.time() - ts < _CACHE_TTL:
                    return _json(result)

    try:
        # 1. Columns
        col_rows = db.execute("""
            SELECT column_name,
                   data_type,
                   data_length,
                   data_precision,
                   data_scale,
                   nullable,
                   column_id,
                   data_default
              FROM user_tab_columns
             WHERE table_name = :tname
             ORDER BY column_id
        """, {"tname": upper_name})

        if not col_rows:
            return _json({
                "status": "error",
                "error": f"Table '{upper_name}' not found or has no columns.",
            })

        columns = []
        for c in col_rows:
            columns.append({
                "column_name":    c["COLUMN_NAME"],
                "data_type":      c["DATA_TYPE"],
                "data_length":    c["DATA_LENGTH"],
                "data_precision": c["DATA_PRECISION"],
                "nullable":       c["NULLABLE"],
                "column_id":      c["COLUMN_ID"],
                "data_default":   c["DATA_DEFAULT"],
            })

        # 2. Primary key
        pk_cons_rows = db.execute("""
            SELECT constraint_name
              FROM user_constraints
             WHERE table_name      = :tname
               AND constraint_type = 'P'
        """, {"tname": upper_name})

        primary_key: dict | None = None
        if pk_cons_rows:
            pk_cons_name = pk_cons_rows[0]["CONSTRAINT_NAME"]
            pk_col_rows = db.execute("""
                SELECT column_name
                  FROM user_cons_columns
                 WHERE constraint_name = :cname
                 ORDER BY position
            """, {"cname": pk_cons_name})
            primary_key = {
                "constraint_name": pk_cons_name,
                "columns": [r["COLUMN_NAME"] for r in pk_col_rows],
            }

        # 3. Foreign keys
        fk_cons_rows = db.execute("""
            SELECT c.constraint_name,
                   r.table_name AS references_table
              FROM user_constraints c
              JOIN user_constraints r
                ON r.constraint_name = c.r_constraint_name
             WHERE c.table_name      = :tname
               AND c.constraint_type = 'R'
             ORDER BY c.constraint_name
        """, {"tname": upper_name})

        foreign_keys = []
        for fk in fk_cons_rows:
            fk_name = fk["CONSTRAINT_NAME"]
            ref_table = fk["REFERENCES_TABLE"]

            # Columns on the FK side
            fk_col_rows = db.execute("""
                SELECT column_name
                  FROM user_cons_columns
                 WHERE constraint_name = :cname
                 ORDER BY position
            """, {"cname": fk_name})

            # Columns on the referenced (PK) side
            pk_for_fk_rows = db.execute("""
                SELECT cc.column_name
                  FROM user_constraints c
                  JOIN user_cons_columns cc
                    ON cc.constraint_name = c.r_constraint_name
                 WHERE c.constraint_name = :cname
                 ORDER BY cc.position
            """, {"cname": fk_name})

            foreign_keys.append({
                "constraint_name":    fk_name,
                "columns":            [r["COLUMN_NAME"] for r in fk_col_rows],
                "references_table":   ref_table,
                "references_columns": [r["COLUMN_NAME"] for r in pk_for_fk_rows],
            })

        # 4. Indexes
        idx_rows = db.execute("""
            SELECT index_name,
                   uniqueness
              FROM user_indexes
             WHERE table_name = :tname
             ORDER BY index_name
        """, {"tname": upper_name})

        indexes = []
        for idx in idx_rows:
            idx_name = idx["INDEX_NAME"]
            idx_col_rows = db.execute("""
                SELECT column_name
                  FROM user_ind_columns
                 WHERE index_name = :iname
                 ORDER BY column_position
            """, {"iname": idx_name})
            indexes.append({
                "index_name": idx_name,
                "uniqueness": idx["UNIQUENESS"],
                "columns":    [r["COLUMN_NAME"] for r in idx_col_rows],
            })

        # 5. Sequences — find sequences related to this table by name convention
        seq_rows = db.execute("""
            SELECT sequence_name,
                   min_value,
                   max_value,
                   increment_by,
                   cycle_flag,
                   order_flag,
                   cache_size,
                   last_number
              FROM user_sequences
             WHERE sequence_name LIKE :prefix
                OR sequence_name LIKE :suffix
             ORDER BY sequence_name
        """, {
            "prefix": upper_name + "%",
            "suffix": "%" + upper_name,
        })

        sequences = []
        for seq in seq_rows:
            sequences.append({
                "sequence_name": seq["SEQUENCE_NAME"],
                "min_value":     seq["MIN_VALUE"],
                "max_value":     seq["MAX_VALUE"],
                "increment_by":  seq["INCREMENT_BY"],
                "cycle_flag":    seq["CYCLE_FLAG"],
                "order_flag":    seq["ORDER_FLAG"],
                "cache_size":    seq["CACHE_SIZE"],
                "last_number":   seq["LAST_NUMBER"],
            })

        # 6. Triggers — find triggers defined on this table
        trg_rows = db.execute("""
            SELECT trigger_name,
                   trigger_type,
                   triggering_event,
                   status,
                   SUBSTR(trigger_body, 1, 200) AS trigger_body
              FROM user_triggers
             WHERE table_name = :tname
             ORDER BY trigger_name
        """, {"tname": upper_name})

        triggers = []
        for trg in trg_rows:
            triggers.append({
                "trigger_name":      trg["TRIGGER_NAME"],
                "trigger_type":      trg["TRIGGER_TYPE"],
                "triggering_event":  trg["TRIGGERING_EVENT"],
                "status":            trg["STATUS"],
                "trigger_body":      trg["TRIGGER_BODY"],
            })

        # 7. Row count (from stats; may be stale if table not analyzed recently)
        row_count_rows = db.execute(
            "SELECT num_rows FROM user_tables WHERE table_name = :tname",
            {"tname": upper_name},
        )
        row_count = row_count_rows[0]["NUM_ROWS"] if row_count_rows else None

        result = {
            "table_name":   upper_name,
            "columns":      columns,
            "primary_key":  primary_key,
            "foreign_keys": foreign_keys,
            "indexes":      indexes,
            "sequences":    sequences,
            "triggers":     triggers,
            "row_count":    row_count,
        }

        # Store in cache before returning
        with _describe_cache_lock:
            _describe_cache[cache_key] = (time.time(), result)

        return _json(result)

    except Exception as e:
        return _json({"status": "error", "error": str(e)})
