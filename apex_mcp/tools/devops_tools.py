"""Tools: apex_generate_rest_endpoints, apex_export_page, apex_generate_docs,
          apex_begin_batch, apex_commit_batch.

DevOps utilities for ORDS REST endpoint generation, page exports,
documentation generation, and batched execution.
"""
from __future__ import annotations
import json
from ..db import db
from ..session import session
from ..utils import _json,  _esc, _blk
from ..validators import validate_table_name


# ---------------------------------------------------------------------------
# Tool A: apex_generate_rest_endpoints
# ---------------------------------------------------------------------------

def apex_generate_rest_endpoints(
    table_name: str,
    base_path: str | None = None,
    require_auth: bool = True,
    pk_column: str | None = None,
    schema: str | None = None,
) -> str:
    """Generate ORDS REST endpoints (GET collection, GET item, POST, PUT, DELETE) for a table.

    Uses the ORDS PL/SQL API (ORDS.DEFINE_MODULE / DEFINE_TEMPLATE / DEFINE_HANDLER)
    to create a fully-functional REST module for the given table. All five standard
    CRUD endpoints are created automatically.

    The PK column is auto-detected via user_constraints + user_cons_columns if not
    provided. The current schema is resolved by querying SELECT USER FROM DUAL.

    Args:
        table_name: Name of the table to expose via REST (case-insensitive).
        base_path: URL base path segment (e.g. "orders"). Defaults to table_name in
            lowercase. The final module base path will be "/{base_path}/".
        require_auth: Whether to mark the module as requiring authentication.
            Currently used for documentation; ORDS privilege assignment must be
            configured separately in ORDS Admin. Defaults to True.
        pk_column: Primary key column name. Auto-detected from user_constraints
            (type='P') if omitted.
        schema: Database schema. Resolved via SELECT USER FROM DUAL if omitted.

    Returns:
        JSON with keys:
            - status: "ok" or "error"
            - table_name: Uppercased table name
            - module_name: ORDS module name used
            - base_path: The URL base path (e.g. "/orders/")
            - pk_column: The PK column that was used
            - require_auth: The value that was passed
            - endpoints: List of {method, path, description} dicts

    Requires:
        - Active connection (call apex_connect first)
        - User must have EXECUTE on ORDS package (granted to schema users on ADB)
        - The table must exist and be owned by the current schema
    """
    try:
        validate_table_name(table_name)
    except ValueError as e:
        return _json({"status": "error", "error": str(e)})

    if not db.is_connected():
        return _json({"status": "error", "error": "Not connected. Call apex_connect() first."})

    table_upper = table_name.upper()

    try:
        # Resolve current schema
        if schema is None:
            rows = db.execute("SELECT USER FROM DUAL")
            schema = rows[0]["USER"]

        # Auto-detect PK column
        if pk_column is None:
            pk_rows = db.execute("""
                SELECT ucc.column_name
                  FROM user_constraints uc
                  JOIN user_cons_columns ucc
                    ON uc.constraint_name = ucc.constraint_name
                 WHERE uc.table_name      = :tname
                   AND uc.constraint_type = 'P'
                 ORDER BY ucc.position
            """, {"tname": table_upper})

            if not pk_rows:
                return _json({
                    "status": "error",
                    "error": (
                        f"No primary key constraint found on table '{table_upper}'. "
                        "Provide pk_column explicitly."
                    ),
                })

            pk_column = pk_rows[0]["COLUMN_NAME"]

        pk_col = pk_column.upper()
        pk_col_lower = pk_col.lower()

        # Get non-PK columns for PUT handler
        col_rows = db.execute("""
            SELECT column_name
              FROM user_tab_columns
             WHERE table_name = :tname
               AND column_name != :pk
             ORDER BY column_id
        """, {"tname": table_upper, "pk": pk_col})

        non_pk_cols = [r["COLUMN_NAME"] for r in col_rows]
        if non_pk_cols:
            set_clause = ", ".join(
                f"{col} = :{col.lower()}" for col in non_pk_cols
            )
        else:
            set_clause = pk_col + " = :" + pk_col_lower  # fallback

        put_source = f"BEGIN UPDATE {table_upper} SET {set_clause} WHERE {pk_col} = :{pk_col_lower}; END;"

        # Resolve base path and module name
        effective_base = (base_path or table_name).lower().strip("/")
        module_name = effective_base

        # Build the full ORDS PL/SQL block
        plsql_body = f"""
  -- Module
  ORDS.DEFINE_MODULE(
    p_module_name    => '{_esc(module_name)}',
    p_base_path      => '/{_esc(effective_base)}/',
    p_items_per_page => 25,
    p_status         => 'PUBLISHED',
    p_comments       => 'Auto-generated by apex-mcp'
  );
  -- Template for collection
  ORDS.DEFINE_TEMPLATE(
    p_module_name    => '{_esc(module_name)}',
    p_pattern        => '.',
    p_priority       => 0,
    p_etag_type      => 'HASH',
    p_comments       => NULL
  );
  -- GET collection
  ORDS.DEFINE_HANDLER(
    p_module_name    => '{_esc(module_name)}',
    p_pattern        => '.',
    p_method         => 'GET',
    p_source_type    => ORDS.source_type_collection_feed,
    p_items_per_page => 25,
    p_mimes_allowed  => NULL,
    p_comments       => 'List all {_esc(table_upper)}',
    p_source         => 'SELECT * FROM {_esc(table_upper)} ORDER BY {_esc(pk_col)}'
  );
  -- POST
  ORDS.DEFINE_HANDLER(
    p_module_name    => '{_esc(module_name)}',
    p_pattern        => '.',
    p_method         => 'POST',
    p_source_type    => ORDS.source_type_plsql,
    p_mimes_allowed  => 'application/json',
    p_comments       => 'Create {_esc(table_upper)}',
    p_source         => 'BEGIN INSERT INTO {_esc(table_upper)} ({_esc(",".join(non_pk_cols) if non_pk_cols else pk_col)}) VALUES ({_esc(",".join(":" + c.lower() for c in non_pk_cols) if non_pk_cols else ":" + pk_col_lower)}); :status := 201; END;'
  );
  -- Template for single item
  ORDS.DEFINE_TEMPLATE(
    p_module_name    => '{_esc(module_name)}',
    p_pattern        => ':{pk_col_lower}',
    p_priority       => 0,
    p_etag_type      => 'HASH',
    p_comments       => NULL
  );
  -- GET single
  ORDS.DEFINE_HANDLER(
    p_module_name    => '{_esc(module_name)}',
    p_pattern        => ':{pk_col_lower}',
    p_method         => 'GET',
    p_source_type    => ORDS.source_type_collection_item,
    p_items_per_page => 1,
    p_mimes_allowed  => NULL,
    p_comments       => 'Get single {_esc(table_upper)}',
    p_source         => 'SELECT * FROM {_esc(table_upper)} WHERE {_esc(pk_col)} = :{pk_col_lower}'
  );
  -- PUT
  ORDS.DEFINE_HANDLER(
    p_module_name    => '{_esc(module_name)}',
    p_pattern        => ':{pk_col_lower}',
    p_method         => 'PUT',
    p_source_type    => ORDS.source_type_plsql,
    p_mimes_allowed  => 'application/json',
    p_comments       => 'Update {_esc(table_upper)}',
    p_source         => '{_esc(put_source)}'
  );
  -- DELETE
  ORDS.DEFINE_HANDLER(
    p_module_name    => '{_esc(module_name)}',
    p_pattern        => ':{pk_col_lower}',
    p_method         => 'DELETE',
    p_source_type    => ORDS.source_type_plsql,
    p_mimes_allowed  => NULL,
    p_comments       => 'Delete {_esc(table_upper)}',
    p_source         => 'BEGIN DELETE FROM {_esc(table_upper)} WHERE {_esc(pk_col)} = :{pk_col_lower}; END;'
  );
  COMMIT;
"""

        db.plsql(_blk(plsql_body))

        endpoints = [
            {"method": "GET",    "path": f"/{effective_base}/",          "description": "List all"},
            {"method": "POST",   "path": f"/{effective_base}/",          "description": "Create"},
            {"method": "GET",    "path": f"/{effective_base}/:{pk_col_lower}", "description": "Get by PK"},
            {"method": "PUT",    "path": f"/{effective_base}/:{pk_col_lower}", "description": "Update"},
            {"method": "DELETE", "path": f"/{effective_base}/:{pk_col_lower}", "description": "Delete"},
        ]

        return _json({
            "status":      "ok",
            "table_name":  table_upper,
            "module_name": module_name,
            "base_path":   f"/{effective_base}/",
            "pk_column":   pk_col,
            "require_auth": require_auth,
            "endpoints":   endpoints,
        })

    except Exception as e:
        return _json({"status": "error", "error": str(e)})


# ---------------------------------------------------------------------------
# Tool B: apex_export_page
# ---------------------------------------------------------------------------

def apex_export_page(
    app_id: int,
    page_id: int,
    output_path: str = "",
) -> str:
    """Export a single APEX page as SQL using apex_export.get_page().

    Uses Oracle's built-in apex_export.get_page() function (available in APEX 19+)
    to generate the SQL for a single page in the wwv_flow_imp format. Up to 32 KB
    of the generated SQL is returned inline; the full content is written to disk
    when output_path is provided.

    Args:
        app_id: Numeric application ID (e.g., 100).
        page_id: Numeric page ID to export (e.g., 1).
        output_path: Full file path where the SQL export should be saved
            (e.g., "C:/myproject/apex/f100_p001.sql"). If empty, only the first
            32 KB of SQL is returned in the JSON response.

    Returns:
        JSON with keys:
            - status: "ok" or "error"
            - app_id: Application ID
            - page_id: Page ID
            - file_name: Export file name as returned by APEX
            - total_length: Total character length of the exported SQL
            - sql_preview: First 32 KB of the exported SQL (always included)
            - saved_to: Absolute path written to (only when output_path is provided)
            - message: Human-readable summary

    Requires:
        - Active connection (call apex_connect first)
        - User must have EXECUTE privilege on apex_export package
        - The page must exist in the specified application
        - For ADB: schema user must be workspace owner or have equivalent grants

    Note:
        apex_export.get_page() returns an apex_t_export_files collection (table type).
        This tool pipes that collection through TABLE() to fetch the CLOB content
        directly. Very large pages (> 32 KB) are truncated in the JSON preview;
        use output_path to capture the full export.
    """
    if not db.is_connected():
        return _json({"status": "error", "error": "Not connected. Call apex_connect() first."})

    try:
        # Read the full CLOB via a direct cursor to handle large content correctly.
        # apex_export.get_page returns apex_t_export_files; TABLE() pipes it as rows.
        c = db.conn
        cur = c.cursor()
        try:
            cur.execute("""
                SELECT f.name,
                       f.contents,
                       DBMS_LOB.GETLENGTH(f.contents) AS total_length
                  FROM TABLE(
                         apex_export.get_page(
                           p_application_id => :app_id,
                           p_page_id        => :page_id
                         )
                       ) f
            """, {"app_id": app_id, "page_id": page_id})
            row = cur.fetchone()
        finally:
            cur.close()

        if not row:
            return _json({
                "status":  "error",
                "app_id":  app_id,
                "page_id": page_id,
                "error": (
                    f"No export data returned for page {page_id} of application {app_id}. "
                    "Verify the application and page exist and you have access."
                ),
            })

        file_name    = row[0] or f"f{app_id}_p{page_id:05d}.sql"
        raw_content  = row[1]
        total_length = row[2] or 0

        # oracledb may return a LOB object for large CLOBs or a str for small ones.
        if hasattr(raw_content, "read"):
            content: str = raw_content.read()
        else:
            content = raw_content or ""

        # Limit the inline preview to 32 KB
        sql_preview = content[:32767]

        result: dict = {
            "status":       "ok",
            "app_id":       app_id,
            "page_id":      page_id,
            "file_name":    file_name,
            "total_length": total_length,
            "sql_preview":  sql_preview,
        }

        if output_path:
            with open(output_path, "w", encoding="utf-8") as fh:
                fh.write(content)
            result["saved_to"] = output_path
            result["message"] = (
                f"Page {page_id} of application {app_id} exported to '{output_path}' "
                f"({total_length:,} characters)."
            )
        else:
            result["message"] = (
                f"Page {page_id} of application {app_id} preview "
                f"(first {len(sql_preview):,} of {total_length:,} chars). "
                "Provide output_path to save the complete SQL file."
            )

        return _json(result)

    except Exception as e:
        err_msg = str(e)
        hint = ""
        if "apex_export" in err_msg.lower() or "insufficient privileges" in err_msg.lower():
            hint = (
                " Hint: The current user may not have EXECUTE on the apex_export package. "
                "Grant it with: GRANT EXECUTE ON apex_export TO <schema>;"
            )
        return _json({
            "status":  "error",
            "app_id":  app_id,
            "page_id": page_id,
            "error":   err_msg + hint,
        })


# ---------------------------------------------------------------------------
# Tool C: apex_generate_docs
# ---------------------------------------------------------------------------

def apex_generate_docs(app_id: int | None = None) -> str:
    """Auto-generate Markdown documentation for an APEX application.

    Queries the APEX data dictionary views to build a comprehensive Markdown
    document covering pages, regions, items, shared LOVs, and auth schemes.
    If app_id is omitted, the app_id from the current import session is used.

    Args:
        app_id: Application ID to document. Falls back to session.app_id if None.

    Returns:
        JSON with keys:
            - status: "ok" or "error"
            - app_id: Application ID that was documented
            - markdown: Full Markdown string ready to write to a .md file
            - stats: Summary counts (pages, regions, items, lovs, auth_schemes)

    Requires:
        - Active connection (call apex_connect first)
        - User must have SELECT on APEX_APPLICATION_* views
        - The application must exist and be accessible to the current schema user

    Note:
        region_source is a CLOB column in apex_application_page_regions.
        Only the first 200 characters are included in the documentation to
        keep output manageable.
    """
    if not db.is_connected():
        return _json({"status": "error", "error": "Not connected. Call apex_connect() first."})

    effective_app_id = app_id if app_id is not None else session.app_id
    if effective_app_id is None:
        return _json({
            "status": "error",
            "error": "No app_id provided and no active import session. Pass app_id explicitly.",
        })

    try:
        # --- App metadata ---
        app_rows = db.execute("""
            SELECT application_id,
                   application_name,
                   alias,
                   pages,
                   owner,
                   availability_status AS status,
                   compatibility_mode,
                   TO_CHAR(last_updated_on, 'YYYY-MM-DD') AS last_updated_on
              FROM apex_applications
             WHERE application_id = :app_id
        """, {"app_id": effective_app_id})

        if not app_rows:
            return _json({
                "status": "error",
                "error": f"Application {effective_app_id} not found.",
            })

        app = app_rows[0]
        app_name    = app.get("APPLICATION_NAME") or f"App {effective_app_id}"
        app_alias   = app.get("ALIAS") or ""
        page_count  = app.get("PAGES") or 0
        app_schema  = app.get("OWNER") or ""
        last_upd    = app.get("LAST_UPDATED_ON") or ""

        # --- Pages ---
        pages = db.execute("""
            SELECT page_id,
                   page_name,
                   page_mode,
                   authorization_scheme
              FROM apex_application_pages
             WHERE application_id = :app_id
             ORDER BY page_id
        """, {"app_id": effective_app_id})

        # --- Regions (all pages at once — join in Python) ---
        regions = db.execute("""
            SELECT page_id,
                   region_name,
                   source_type,
                   DBMS_LOB.SUBSTR(region_source, 200, 1) AS region_source_preview
              FROM apex_application_page_regions
             WHERE application_id = :app_id
             ORDER BY page_id, display_sequence
        """, {"app_id": effective_app_id})

        # Group regions by page_id
        regions_by_page: dict[int, list[dict]] = {}
        for r in regions:
            pid = r.get("PAGE_ID")
            regions_by_page.setdefault(pid, []).append(r)

        # --- Items (all pages at once) ---
        items = db.execute("""
            SELECT page_id,
                   item_name,
                   display_as,
                   item_source
              FROM apex_application_page_items
             WHERE application_id = :app_id
             ORDER BY page_id, display_sequence
        """, {"app_id": effective_app_id})

        # Group items by page_id
        items_by_page: dict[int, list[dict]] = {}
        for i in items:
            pid = i.get("PAGE_ID")
            items_by_page.setdefault(pid, []).append(i)

        # --- Shared LOVs ---
        lovs = db.execute("""
            SELECT list_of_values_name,
                   lov_type,
                   source_type
              FROM apex_application_lovs
             WHERE application_id = :app_id
             ORDER BY list_of_values_name
        """, {"app_id": effective_app_id})

        # --- Auth Schemes ---
        auth_schemes = db.execute("""
            SELECT authorization_scheme_name,
                   scheme_type
              FROM apex_application_authorization
             WHERE application_id = :app_id
             ORDER BY authorization_scheme_name
        """, {"app_id": effective_app_id})

        # -------------------------------------------------------------------
        # Build Markdown
        # -------------------------------------------------------------------
        lines: list[str] = []

        # Header
        lines.append(f"# {app_name} (App {effective_app_id})")
        lines.append("")
        lines.append(
            f"**Alias**: {app_alias} | **Pages**: {page_count} | "
            f"**Schema**: {app_schema} | **Last updated**: {last_upd}"
        )
        lines.append("")

        # Pages section
        lines.append("## Pages")
        lines.append("")

        for page in pages:
            pid       = page.get("PAGE_ID")
            pname     = page.get("PAGE_NAME") or ""
            pmode     = page.get("PAGE_MODE") or ""
            pauth     = page.get("AUTHORIZATION_SCHEME") or "—"

            lines.append(f"### Page {pid}: {pname}")
            lines.append(f"**Auth**: {pauth} | **Mode**: {pmode}")
            lines.append("")

            # Regions table
            page_regions = regions_by_page.get(pid, [])
            if page_regions:
                lines.append("#### Regions")
                lines.append("")
                lines.append("| Region | Type | Source |")
                lines.append("|--------|------|--------|")
                for r in page_regions:
                    rname  = (r.get("REGION_NAME") or "").replace("|", "\\|")
                    rtype  = (r.get("SOURCE_TYPE") or "").replace("|", "\\|")
                    rsrc   = (r.get("REGION_SOURCE_PREVIEW") or "").replace("\n", " ").replace("|", "\\|")
                    lines.append(f"| {rname} | {rtype} | {rsrc} |")
                lines.append("")

            # Items table
            page_items = items_by_page.get(pid, [])
            if page_items:
                lines.append("#### Items")
                lines.append("")
                lines.append("| Item | Type |")
                lines.append("|------|------|")
                for i in page_items:
                    iname = (i.get("ITEM_NAME") or "").replace("|", "\\|")
                    itype = (i.get("DISPLAY_AS") or "").replace("|", "\\|")
                    lines.append(f"| {iname} | {itype} |")
                lines.append("")

            lines.append("---")
            lines.append("")

        # Shared LOVs section
        lines.append(f"## Shared LOVs ({len(lovs)})")
        lines.append("")
        if lovs:
            lines.append("| LOV Name | Type |")
            lines.append("|----------|------|")
            for lov in lovs:
                lname = (lov.get("LIST_OF_VALUES_NAME") or "").replace("|", "\\|")
                ltype = (lov.get("LOV_TYPE") or lov.get("SOURCE_TYPE") or "").replace("|", "\\|")
                lines.append(f"| {lname} | {ltype} |")
        else:
            lines.append("_No shared LOVs defined._")
        lines.append("")

        # Auth Schemes section
        lines.append(f"## Auth Schemes ({len(auth_schemes)})")
        lines.append("")
        if auth_schemes:
            lines.append("| Scheme | Type |")
            lines.append("|--------|------|")
            for scheme in auth_schemes:
                sname = (scheme.get("AUTHORIZATION_SCHEME_NAME") or "").replace("|", "\\|")
                stype = (scheme.get("SCHEME_TYPE") or "").replace("|", "\\|")
                lines.append(f"| {sname} | {stype} |")
        else:
            lines.append("_No authorization schemes defined._")
        lines.append("")

        markdown = "\n".join(lines)

        return _json({
            "status":   "ok",
            "app_id":   effective_app_id,
            "markdown": markdown,
            "stats": {
                "pages":        len(pages),
                "regions":      len(regions),
                "items":        len(items),
                "lovs":         len(lovs),
                "auth_schemes": len(auth_schemes),
            },
        })

    except Exception as e:
        return _json({"status": "error", "error": str(e)})


# ---------------------------------------------------------------------------
# Tool D: apex_begin_batch / apex_commit_batch
# ---------------------------------------------------------------------------

def apex_begin_batch() -> str:
    """Start batch mode: all APEX build operations are queued and not executed until apex_commit_batch().

    Use this to group multiple operations into a single database round-trip,
    dramatically reducing latency for complex app builds.

    When batch mode is active, every call to db.plsql() appends the PL/SQL body
    to an internal queue instead of executing it immediately. The queue is flushed
    (and committed) when apex_commit_batch() is called.

    Dry-run mode takes precedence: if dry_run is active, plsql() calls are still
    captured in the dry-run log, not the batch queue.

    Returns:
        JSON confirmation that batch mode is active.
    """
    db.begin_batch()
    return _json({
        "status":  "ok",
        "message": (
            "Batch mode started. Operations will be queued until apex_commit_batch(). "
            "Call apex_commit_batch() to execute all queued operations in one round-trip."
        ),
    })


def apex_commit_batch() -> str:
    """Execute all queued batch operations in a single round-trip and commit.

    Call this after apex_begin_batch() and all your build operations.
    Each queued PL/SQL block is executed in order; errors on individual statements
    are captured and reported but do not abort the remaining queue. A COMMIT is
    issued after all statements are attempted.

    Returns:
        JSON with keys:
            - status: "ok" if no errors, "partial" if some statements failed
            - executed: Total number of statements attempted
            - ok: Count of successful statements
            - errors: Count of failed statements
            - log: List of per-statement result strings ("OK: ..." or "ERR: ...")
    """
    log = db.commit_batch()
    ok_count  = sum(1 for entry in log if entry.startswith("OK"))
    err_count = sum(1 for entry in log if entry.startswith("ERR"))
    return _json({
        "status":   "ok" if err_count == 0 else "partial",
        "executed": len(log),
        "ok":       ok_count,
        "errors":   err_count,
        "log":      log,
    })
