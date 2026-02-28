"""Tools: apex_list_tables, apex_describe_table."""
from __future__ import annotations
import json
from ..db import db


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
        JSON array. If include_columns=True, each entry has:
        {object_name, object_type, num_rows, columns: [{column_name, data_type, nullable, data_length, data_precision}]}
        If False: [{object_name, object_type, num_rows}]

    Use this to discover available tables/views before using apex_generate_crud or apex_describe_table.
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})

    ot = object_type.upper()
    if ot not in ("TABLE", "VIEW", "ALL"):
        return json.dumps({
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
            return json.dumps(result, default=str, ensure_ascii=False, indent=2)

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

        return json.dumps(result, default=str, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)


def apex_describe_table(table_name: str) -> str:
    """Get detailed metadata for a specific database table.

    Returns complete schema info including columns, primary keys, foreign keys,
    indexes, sequences, and triggers — everything needed to generate APEX forms and reports.

    Args:
        table_name: Table name (case-insensitive).

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
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})

    upper_name = table_name.upper()

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
            return json.dumps({
                "status": "error",
                "error": f"Table '{upper_name}' not found or has no columns.",
            }, ensure_ascii=False, indent=2)

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

        return json.dumps(result, default=str, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)
