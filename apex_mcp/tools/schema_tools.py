"""Tools: apex_list_tables, apex_describe_table."""
from __future__ import annotations
import json
from ..db import db


def apex_list_tables(
    pattern: str = "%",
    include_columns: bool = True,
) -> str:
    """List database tables in the current schema with their columns.

    Args:
        pattern: SQL LIKE pattern to filter table names (default: all tables).
                 Examples: "EMP%", "%DEPT%", "HR_%"
        include_columns: Include column details for each table (default True).
                         Set False for a quick table name list only.

    Returns:
        JSON array. If include_columns=True, each entry has:
        {table_name, num_rows, columns: [{column_name, data_type, nullable, data_length, data_precision}]}
        If False: [{table_name, num_rows}]

    Use this to discover available tables before using apex_generate_crud or apex_describe_table.
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})

    try:
        # Fetch tables matching the pattern
        table_rows = db.execute("""
            SELECT table_name,
                   num_rows
              FROM user_tables
             WHERE table_name LIKE :pattern
             ORDER BY table_name
        """, {"pattern": pattern.upper()})

        if not include_columns:
            return json.dumps(table_rows, default=str, ensure_ascii=False, indent=2)

        # Fetch all columns for matching tables in a single query
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

        # Index columns by table name
        columns_by_table: dict[str, list[dict]] = {}
        for col in col_rows:
            tname = col["TABLE_NAME"]
            if tname not in columns_by_table:
                columns_by_table[tname] = []
            columns_by_table[tname].append({
                "column_name":    col["COLUMN_NAME"],
                "data_type":      col["DATA_TYPE"],
                "nullable":       col["NULLABLE"],
                "data_length":    col["DATA_LENGTH"],
                "data_precision": col["DATA_PRECISION"],
            })

        # Build combined result
        result = []
        for trow in table_rows:
            tname = trow["TABLE_NAME"]
            result.append({
                "table_name": tname,
                "num_rows":   trow["NUM_ROWS"],
                "columns":    columns_by_table.get(tname, []),
            })

        return json.dumps(result, default=str, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)


def apex_describe_table(table_name: str) -> str:
    """Get detailed metadata for a specific database table.

    Returns complete schema info including columns, primary keys, foreign keys,
    and indexes — everything needed to generate APEX forms and reports.

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

        # 5. Row count
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
            "row_count":    row_count,
        }

        return json.dumps(result, default=str, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)
