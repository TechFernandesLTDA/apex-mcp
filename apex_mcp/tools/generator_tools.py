"""Tools: apex_generate_crud, apex_generate_dashboard, apex_generate_login."""
from __future__ import annotations
import json
from ..db import db
from ..ids import ids
from ..session import session, PageInfo, RegionInfo, ItemInfo, LovInfo
from ..templates import (
    REGION_TMPL_STANDARD, REGION_TMPL_IR, REGION_TMPL_BLANK,
    ITEM_TEXT, ITEM_NUMBER, ITEM_DATE, ITEM_SELECT, ITEM_HIDDEN,
    ITEM_TEXTAREA, ITEM_YES_NO, ITEM_PASSWORD, ITEM_DISPLAY,
    BTN_TMPL_TEXT, LABEL_OPTIONAL, LABEL_REQUIRED,
    PROC_DML, PROC_PLSQL,
    PAGE_TMPL_STANDARD, PAGE_TMPL_LOGIN,
)
from ..config import WORKSPACE_ID, APEX_SCHEMA


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _esc(value: str) -> str:
    """Escape single quotes for safe embedding in PL/SQL string literals."""
    return value.replace("'", "''")


def _blk(sql: str) -> str:
    """Wrap SQL in an anonymous PL/SQL begin...end; block."""
    return f"begin\n{sql}\nend;"


# Audit columns to skip when building form items
_AUDIT_COLUMNS = {
    "DT_CRIACAO", "DT_ATUALIZACAO", "DS_CRIADO_POR", "DS_ATUALIZADO_POR",
    "CREATED_ON", "UPDATED_ON", "CREATED_BY", "UPDATED_BY",
}


def _humanize(name: str) -> str:
    """Convert UPPER_SNAKE_CASE table/column name to Title Case label."""
    return name.replace("_", " ").title()


def _infer_item_type(
    col_name: str,
    data_type: str,
    data_length: int,
    pk_columns: set[str],
    fk_columns: set[str],
) -> str:
    """Infer the best APEX item type based on Oracle column name/type conventions.

    Rules (evaluated in order):
      1. PK column  -> NATIVE_HIDDEN
      2. FK column  -> NATIVE_SELECT_LIST
      3. FL_ prefix -> NATIVE_YES_NO
      4. DT_ prefix -> NATIVE_DATE_PICKER_JET
      5. DS_ prefix + length > 500 -> NATIVE_TEXTAREA
      6. DS_ prefix -> NATIVE_TEXT_FIELD
      7. NR_ prefix -> NATIVE_NUMBER_FIELD
      8. data_type NUMBER -> NATIVE_NUMBER_FIELD
      9. data_type DATE/TIMESTAMP -> NATIVE_DATE_PICKER_JET
     10. data_type CLOB or length > 4000 -> NATIVE_TEXTAREA
     11. default -> NATIVE_TEXT_FIELD
    """
    upper = col_name.upper()

    if upper in pk_columns:
        return ITEM_HIDDEN
    if upper in fk_columns:
        return ITEM_SELECT
    if upper.startswith("FL_"):
        return ITEM_YES_NO
    if upper.startswith("DT_"):
        return ITEM_DATE
    if upper.startswith("DS_"):
        if data_length and data_length > 500:
            return ITEM_TEXTAREA
        return ITEM_TEXT
    if upper.startswith("NR_"):
        return ITEM_NUMBER
    if data_type in ("NUMBER", "INTEGER", "FLOAT"):
        return ITEM_NUMBER
    if data_type in ("DATE",) or data_type.startswith("TIMESTAMP"):
        return ITEM_DATE
    if data_type == "CLOB" or (data_length and data_length > 4000):
        return ITEM_TEXTAREA
    return ITEM_TEXT


# ---------------------------------------------------------------------------
# apex_generate_crud
# ---------------------------------------------------------------------------

def apex_generate_crud(
    table_name: str,
    list_page_id: int,
    form_page_id: int,
    list_page_name: str = "",
    form_page_name: str = "",
    include_search: bool = True,
    auth_scheme: str = "",
) -> str:
    """Generate a complete CRUD (Create/Read/Update/Delete) module for a database table.

    This is the most powerful generator tool. It:
    1. Introspects the table structure (columns, PKs, FKs)
    2. Creates a list page with Interactive Report showing all records
    3. Adds a "New" button on the list page
    4. Creates a form page with:
       - All columns as appropriate item types (inferred from naming/data type)
       - LOVs auto-created for FK columns
       - Save/Cancel/Delete buttons
       - DML process for INSERT/UPDATE/DELETE
       - Detail link from the IR to the form
    5. Links the two pages together

    Args:
        table_name: Database table name (case-insensitive, e.g., "EMPLOYEES").
        list_page_id: Page ID for the Interactive Report list (e.g., 10).
        form_page_id: Page ID for the form (e.g., 11).
        list_page_name: Display name for list page. Defaults to table_name humanized.
        form_page_name: Display name for form page. Defaults to "Edit {list_page_name}".
        include_search: Add search bar to the IR (default True).
        auth_scheme: Authorization scheme name for both pages.

    Returns:
        JSON with status, pages created, items created, LOVs created, and summary.

    Best practices applied automatically:
        - PK columns are hidden (NATIVE_HIDDEN) in the form
        - FK columns get automatic select list + LOV creation
        - Audit columns (created_on, updated_on, etc.) are excluded from forms
        - Delete button only shown when editing existing record (PK not null)
        - DML process handles INSERT/UPDATE/DELETE automatically
        - IR has proper edit link to form
        - Cancel returns to list page
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})
    if not session.import_begun:
        return json.dumps({"status": "error", "error": "No import session active. Call apex_create_app() first."})

    upper_table = table_name.upper()
    list_page_name = list_page_name or _humanize(upper_table)
    form_page_name = form_page_name or f"Edit {list_page_name}"

    log: list[str] = []
    items_created: list[str] = []
    lovs_created: list[str] = []

    try:
        # ── 1. Introspect columns ──────────────────────────────────────────
        cols = db.execute("""
            SELECT column_name,
                   data_type,
                   NVL(data_length, 0) AS data_length,
                   nullable,
                   column_id
              FROM user_tab_columns
             WHERE table_name = :tname
             ORDER BY column_id
        """, {"tname": upper_table})

        if not cols:
            return json.dumps({
                "status": "error",
                "error": f"Table '{upper_table}' not found or no columns returned.",
            })

        col_names = [c["COLUMN_NAME"] for c in cols]

        # ── 2. PKs ────────────────────────────────────────────────────────
        pk_rows = db.execute("""
            SELECT cc.column_name
              FROM user_constraints c
              JOIN user_cons_columns cc
                ON cc.constraint_name = c.constraint_name
             WHERE c.table_name = :tname
               AND c.constraint_type = 'P'
             ORDER BY cc.position
        """, {"tname": upper_table})
        pk_columns: set[str] = {r["COLUMN_NAME"] for r in pk_rows}
        pk_list: list[str] = [r["COLUMN_NAME"] for r in pk_rows]
        primary_key = pk_list[0] if pk_list else (col_names[0] if col_names else "ID")
        pk_type = "composite" if len(pk_list) > 1 else "simple"

        # ── 3. FKs ────────────────────────────────────────────────────────
        fk_rows = db.execute("""
            SELECT cc.column_name,
                   rc.table_name AS ref_table,
                   rcc.column_name AS ref_column
              FROM user_constraints c
              JOIN user_cons_columns cc
                ON cc.constraint_name = c.constraint_name
              JOIN user_constraints rc
                ON rc.constraint_name = c.r_constraint_name
              JOIN user_cons_columns rcc
                ON rcc.constraint_name = rc.constraint_name
             WHERE c.table_name = :tname
               AND c.constraint_type = 'R'
             ORDER BY cc.position
        """, {"tname": upper_table})
        fk_map: dict[str, dict] = {r["COLUMN_NAME"]: r for r in fk_rows}
        fk_columns: set[str] = set(fk_map.keys())

        # ── 4. Auto-create LOVs for FK columns ───────────────────────────
        lov_ids: dict[str, int] = {}
        for fk_col, fk_info in fk_map.items():
            ref_table = fk_info["REF_TABLE"]
            ref_col = fk_info["REF_COLUMN"]

            # Try to find a good display column (DS_ or NAME column)
            display_candidates = db.execute("""
                SELECT column_name FROM user_tab_columns
                 WHERE table_name = :tname
                   AND (column_name LIKE 'DS_%'
                        OR column_name LIKE '%NAME%'
                        OR column_name LIKE '%NOME%'
                        OR column_name LIKE '%DESCR%')
                   AND column_name != :refcol
                 ORDER BY column_id
            """, {"tname": ref_table, "refcol": ref_col})

            display_col = (
                display_candidates[0]["COLUMN_NAME"] if display_candidates else ref_col
            )

            lov_name = f"LOV_{fk_col}"
            lov_sql = (
                f"SELECT {display_col} AS d, {ref_col} AS r "
                f"FROM {ref_table} ORDER BY 1"
            )
            lov_id = ids.next(f"lov_{fk_col.lower()}")

            db.plsql(_blk(f"""
wwv_flow_imp_shared.create_list_of_values(
 p_id=>wwv_flow_imp.id({lov_id})
,p_lov_name=>'{_esc(lov_name)}'
,p_lov_query=>'{_esc(lov_sql)}'
,p_source_type=>'SQL'
,p_version_scn=>1
);"""))
            lov_ids[fk_col] = lov_id
            lovs_created.append(lov_name)
            session.lovs[lov_name] = LovInfo(lov_id=lov_id, lov_name=lov_name)

        log.append(f"LOVs created: {len(lov_ids)}")

        # ── 5. Build auth lines ───────────────────────────────────────────
        def _auth_lines(scheme: str) -> str:
            if scheme:
                return (
                    f",p_page_is_public_y_n=>'N'\n"
                    f",p_protection_level=>'C'\n"
                    f",p_required_role=>'{_esc(scheme)}'"
                )
            return ",p_page_is_public_y_n=>'Y'\n,p_protection_level=>'C'"

        # ── 6. Create list page ───────────────────────────────────────────
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page(
 p_id=>{list_page_id}
,p_name=>'{_esc(list_page_name)}'
,p_alias=>'{_esc(list_page_name.upper().replace(" ", "-"))}'
,p_step_title=>'{_esc(list_page_name)}'
,p_autocomplete_on_off=>'OFF'
,p_page_mode=>'NORMAL'
,p_page_template_id=>{PAGE_TMPL_STANDARD}
,p_last_updated_by=>'APEX_MCP'
,p_last_upd_yyyymmddhh24miss=>TO_CHAR(SYSDATE,'YYYYMMDDHH24MISS')
{_auth_lines(auth_scheme)}
);"""))
        session.pages[list_page_id] = PageInfo(
            page_id=list_page_id,
            page_name=list_page_name,
            page_type="report",
        )
        log.append(f"List page {list_page_id} created")

        # ── 7. Create IR region on list page ─────────────────────────────
        # Build edit link: clicking a row opens the form page.
        # For composite PKs, pass all PK items in the URL (names:values CSV).
        if pk_type == "composite":
            pk_item_names = ",".join(f"P{form_page_id}_{pk}" for pk in pk_list)
            pk_item_vals = ",".join(f"#{pk}#" for pk in pk_list)
            edit_link = (
                f"f?p=&APP_ID.:{form_page_id}:&SESSION.::&DEBUG.::"
                f"{pk_item_names}:{pk_item_vals}"
            )
        else:
            edit_link = (
                f"f?p=&APP_ID.:{form_page_id}:&SESSION.::&DEBUG.::"
                f"P{form_page_id}_{primary_key}:#ROWID#"
            )

        ir_region_id = ids.next(f"ir_region_{list_page_id}")

        # Column list (all columns)
        col_csv = ", ".join(col_names)
        ir_sql = f"SELECT {col_csv} FROM {upper_table}"

        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_plug(
 p_id=>wwv_flow_imp.id({ir_region_id})
,p_flow_id=>wwv_flow.g_flow_id
,p_page_id=>{list_page_id}
,p_plug_name=>'{_esc(list_page_name)}'
,p_region_template_options=>'#DEFAULT#'
,p_plug_template=>{REGION_TMPL_IR}
,p_plug_display_sequence=>10
,p_plug_display_point=>'BODY'
,p_query_type=>'SQL'
,p_plug_source=>'{_esc(ir_sql)}'
,p_plug_source_type=>'NATIVE_IR'
,p_last_updated_by=>'APEX_MCP'
,p_last_upd_yyyymmddhh24miss=>TO_CHAR(SYSDATE,'YYYYMMDDHH24MISS')
);"""))
        session.regions[ir_region_id] = RegionInfo(
            region_id=ir_region_id,
            page_id=list_page_id,
            region_name=list_page_name,
            region_type="NATIVE_IR",
        )
        log.append(f"IR region {ir_region_id} created on page {list_page_id}")

        # ── 8. IR Worksheet definition ────────────────────────────────────
        ws_id = ids.next(f"worksheet_{list_page_id}")
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_worksheet(
 p_id=>wwv_flow_imp.id({ws_id})
,p_region_id=>wwv_flow_imp.id({ir_region_id})
,p_max_row_count=>1000
,p_max_row_count_message=>'The maximum row count for this report is #MAX_ROW_COUNT# rows. Please apply a filter to reduce the number of records in your query.'
,p_no_data_found_message=>'No data found.'
,p_pagination_type=>'ROWS_X_TO_Y'
,p_pagination_display_pos=>'BOTTOM_RIGHT'
,p_report_list_mode=>'TABS'
,p_show_search_bar=>'{("YES" if include_search else "NO")}'
,p_show_actions_menu=>'YES'
,p_show_detail_link=>'C'
,p_detail_link=>'{_esc(edit_link)}'
,p_detail_link_text=>'<span aria-label="Edit"><span class="fa fa-edit" aria-hidden="true" title="Edit"></span></span>'
,p_owner=>'APEX_MCP'
,p_internal_uid=>{ws_id}
);"""))
        log.append("IR worksheet created")

        # IR worksheet columns
        for seq, col in enumerate(cols, start=10):
            wc_id = ids.next(f"wscol_{list_page_id}_{col['COLUMN_NAME']}")
            db.plsql(_blk(f"""
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id({wc_id})
,p_db_column_name=>'{_esc(col["COLUMN_NAME"])}'
,p_display_order=>{seq * 10}
,p_column_identifier=>'{chr(64 + min(seq, 26))}'
,p_column_label=>'{_esc(_humanize(col["COLUMN_NAME"]))}'
,p_column_type=>'{"NUMBER" if col["DATA_TYPE"] in ("NUMBER","INTEGER","FLOAT") else "DATE" if col["DATA_TYPE"] in ("DATE",) or col["DATA_TYPE"].startswith("TIMESTAMP") else "STRING"}'
,p_tz_dependent=>'N'
);"""))
        log.append(f"IR worksheet columns created: {len(cols)}")

        # Worksheet report (default report)
        wr_id = ids.next(f"wsrpt_{list_page_id}")
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_worksheet_rpt(
 p_id=>wwv_flow_imp.id({wr_id})
,p_application_user=>'APXWS_DEFAULT'
,p_report_seq=>10
,p_report_alias=>'DEFAULT'
,p_status=>'PUBLIC'
,p_is_default=>'Y'
,p_report_columns=>'{":".join(col_names)}'
,p_sort_column_1=>'{primary_key}'
,p_sort_direction_1=>'ASC'
);"""))
        log.append("IR worksheet default report created")

        # ── 9. "New" button on list page ──────────────────────────────────
        new_btn_id = ids.next(f"btn_new_{list_page_id}")
        new_link = (
            f"f?p=&APP_ID.:{form_page_id}:&SESSION.::&DEBUG.:::"
        )
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_button(
 p_id=>wwv_flow_imp.id({new_btn_id})
,p_flow_id=>wwv_flow.g_flow_id
,p_flow_step_id=>{list_page_id}
,p_button_sequence=>10
,p_button_plug_id=>wwv_flow_imp.id({ir_region_id})
,p_button_name=>'CREATE'
,p_button_action=>'REDIRECT_URL'
,p_button_template_options=>'#DEFAULT#'
,p_button_template_id=>{BTN_TMPL_TEXT}
,p_button_is_hot=>'Y'
,p_button_image_alt=>'New'
,p_button_position=>'RIGHT_OF_IR_SEARCH_BAR'
,p_button_redirect_url=>'{_esc(new_link)}'
);"""))
        log.append("New button created on list page")

        # ── 10. Create form page ──────────────────────────────────────────
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page(
 p_id=>{form_page_id}
,p_name=>'{_esc(form_page_name)}'
,p_alias=>'{_esc(form_page_name.upper().replace(" ", "-"))}'
,p_step_title=>'{_esc(form_page_name)}'
,p_autocomplete_on_off=>'OFF'
,p_page_mode=>'NORMAL'
,p_page_template_id=>{PAGE_TMPL_STANDARD}
,p_last_updated_by=>'APEX_MCP'
,p_last_upd_yyyymmddhh24miss=>TO_CHAR(SYSDATE,'YYYYMMDDHH24MISS')
{_auth_lines(auth_scheme)}
);"""))
        session.pages[form_page_id] = PageInfo(
            page_id=form_page_id,
            page_name=form_page_name,
            page_type="form",
        )
        log.append(f"Form page {form_page_id} created")

        # ── 11. Form region ───────────────────────────────────────────────
        form_region_id = ids.next(f"form_region_{form_page_id}")
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_plug(
 p_id=>wwv_flow_imp.id({form_region_id})
,p_flow_id=>wwv_flow.g_flow_id
,p_page_id=>{form_page_id}
,p_plug_name=>'{_esc(form_page_name)}'
,p_region_template_options=>'#DEFAULT#'
,p_plug_template=>{REGION_TMPL_STANDARD}
,p_plug_display_sequence=>10
,p_plug_display_point=>'BODY'
,p_plug_source_type=>'NATIVE_FORM'
,p_last_updated_by=>'APEX_MCP'
,p_last_upd_yyyymmddhh24miss=>TO_CHAR(SYSDATE,'YYYYMMDDHH24MISS')
);"""))
        session.regions[form_region_id] = RegionInfo(
            region_id=form_region_id,
            page_id=form_page_id,
            region_name=form_page_name,
            region_type="NATIVE_FORM",
        )
        log.append(f"Form region {form_region_id} created on page {form_page_id}")

        # ── 12. Page items for each column ────────────────────────────────
        item_seq = 10
        for col in cols:
            col_name = col["COLUMN_NAME"]
            # Skip audit columns
            if col_name.upper() in _AUDIT_COLUMNS:
                continue

            item_name = f"P{form_page_id}_{col_name.upper()}"
            item_type = _infer_item_type(
                col_name=col_name,
                data_type=col["DATA_TYPE"],
                data_length=col["DATA_LENGTH"],
                pk_columns=pk_columns,
                fk_columns=fk_columns,
            )
            label = _humanize(col_name)
            is_required = col["NULLABLE"] == "N" and col_name.upper() not in pk_columns
            label_tmpl = LABEL_REQUIRED if is_required else LABEL_OPTIONAL
            item_id = ids.next(f"item_{form_page_id}_{col_name.lower()}")

            # LOV clause for FK select lists
            lov_clause = ""
            if item_type == ITEM_SELECT and col_name.upper() in lov_ids:
                lov_clause = f",p_lov=>wwv_flow_imp.id({lov_ids[col_name.upper()]})\n,p_lov_display_null=>'YES'\n,p_lov_null_text=>'-Select-'"

            db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_item(
 p_id=>wwv_flow_imp.id({item_id})
,p_flow_id=>wwv_flow.g_flow_id
,p_flow_step_id=>{form_page_id}
,p_name=>'{_esc(item_name)}'
,p_item_sequence=>{item_seq}
,p_item_plug_id=>wwv_flow_imp.id({form_region_id})
,p_prompt=>'{_esc(label)}'
,p_source=>'{_esc(col_name)}'
,p_source_type=>'DB_COLUMN'
,p_display_as=>'{item_type}'
,p_label_alignment=>'RIGHT'
,p_field_template=>{label_tmpl}
,p_item_template_options=>'#DEFAULT#'
{lov_clause}
);"""))
            session.items[item_name] = ItemInfo(
                item_id=item_id,
                page_id=form_page_id,
                item_name=item_name,
                item_type=item_type,
            )
            items_created.append(item_name)
            item_seq += 10

        log.append(f"Form items created: {len(items_created)}")

        # ── 13. Buttons region on form page ───────────────────────────────
        btn_region_id = ids.next(f"btn_region_{form_page_id}")
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_plug(
 p_id=>wwv_flow_imp.id({btn_region_id})
,p_flow_id=>wwv_flow.g_flow_id
,p_page_id=>{form_page_id}
,p_plug_name=>'Buttons'
,p_region_template_options=>'#DEFAULT#'
,p_plug_template=>2126429139436695430
,p_plug_display_sequence=>20
,p_plug_display_point=>'REGION_POSITION_03'
,p_last_updated_by=>'APEX_MCP'
,p_last_upd_yyyymmddhh24miss=>TO_CHAR(SYSDATE,'YYYYMMDDHH24MISS')
);"""))

        cancel_url = f"f?p=&APP_ID.:{list_page_id}:&SESSION.::&DEBUG.:::"

        # Cancel button
        cancel_btn_id = ids.next(f"btn_cancel_{form_page_id}")
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_button(
 p_id=>wwv_flow_imp.id({cancel_btn_id})
,p_flow_id=>wwv_flow.g_flow_id
,p_flow_step_id=>{form_page_id}
,p_button_sequence=>10
,p_button_plug_id=>wwv_flow_imp.id({btn_region_id})
,p_button_name=>'CANCEL'
,p_button_action=>'REDIRECT_URL'
,p_button_template_options=>'#DEFAULT#'
,p_button_template_id=>{BTN_TMPL_TEXT}
,p_button_is_hot=>'N'
,p_button_image_alt=>'Cancel'
,p_button_position=>'EDIT'
,p_button_redirect_url=>'{_esc(cancel_url)}'
);"""))

        # Delete button (conditional: only shown when PK is not null)
        delete_btn_id = ids.next(f"btn_delete_{form_page_id}")
        pk_item = f"P{form_page_id}_{primary_key}"
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_button(
 p_id=>wwv_flow_imp.id({delete_btn_id})
,p_flow_id=>wwv_flow.g_flow_id
,p_flow_step_id=>{form_page_id}
,p_button_sequence=>20
,p_button_plug_id=>wwv_flow_imp.id({btn_region_id})
,p_button_name=>'DELETE'
,p_button_action=>'SUBMIT'
,p_button_template_options=>'#DEFAULT#'
,p_button_template_id=>{BTN_TMPL_TEXT}
,p_button_is_hot=>'N'
,p_button_image_alt=>'Delete'
,p_button_position=>'EDIT'
,p_button_condition_type=>'ITEM_IS_NOT_NULL'
,p_button_condition=>'{_esc(pk_item)}'
,p_confirm_message=>'Would you like to delete this record?'
);"""))

        # Save button (hot)
        save_btn_id = ids.next(f"btn_save_{form_page_id}")
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_button(
 p_id=>wwv_flow_imp.id({save_btn_id})
,p_flow_id=>wwv_flow.g_flow_id
,p_flow_step_id=>{form_page_id}
,p_button_sequence=>30
,p_button_plug_id=>wwv_flow_imp.id({btn_region_id})
,p_button_name=>'SAVE'
,p_button_action=>'SUBMIT'
,p_button_template_options=>'#DEFAULT#'
,p_button_template_id=>{BTN_TMPL_TEXT}
,p_button_is_hot=>'Y'
,p_button_image_alt=>'Save'
,p_button_position=>'EDIT'
);"""))
        log.append("Form buttons created (Cancel, Delete, Save)")

        # ── 14. DML process on form page ──────────────────────────────────
        proc_id = ids.next(f"proc_dml_{form_page_id}")
        # Build column list for DML process (skip audit cols)
        dml_cols = [
            c["COLUMN_NAME"] for c in cols
            if c["COLUMN_NAME"].upper() not in _AUDIT_COLUMNS
        ]
        col_items_csv = ",".join(
            f"p_col{i:02d}=>'{c}',p_val{i:02d}=>:{item_prefix}"
            for i, (c, item_prefix) in enumerate(
                [(c, f"P{form_page_id}_{c}") for c in dml_cols], start=1
            )
        )

        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_process(
 p_id=>wwv_flow_imp.id({proc_id})
,p_flow_id=>wwv_flow.g_flow_id
,p_flow_step_id=>{form_page_id}
,p_process_sequence=>10
,p_process_point=>'AFTER_SUBMIT'
,p_process_type=>'NATIVE_FORM_DML'
,p_process_name=>'Process Form {_esc(upper_table)}'
,p_attribute_01=>'REGION_SOURCE'
,p_attribute_05=>'Y'
,p_attribute_06=>'Y'
,p_attribute_08=>'Y'
,p_error_display_location=>'INLINE_IN_NOTIFICATION'
,p_process_when_button_id=>wwv_flow_imp.id({save_btn_id})
,p_process_success_message=>'Record saved.'
,p_version_scn=>1
);"""))
        log.append("DML process created")

        # Delete process
        del_proc_id = ids.next(f"proc_del_{form_page_id}")
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_process(
 p_id=>wwv_flow_imp.id({del_proc_id})
,p_flow_id=>wwv_flow.g_flow_id
,p_flow_step_id=>{form_page_id}
,p_process_sequence=>20
,p_process_point=>'AFTER_SUBMIT'
,p_process_type=>'NATIVE_FORM_DML'
,p_process_name=>'Delete Record'
,p_attribute_01=>'REGION_SOURCE'
,p_attribute_05=>'Y'
,p_attribute_06=>'Y'
,p_attribute_08=>'Y'
,p_error_display_location=>'INLINE_IN_NOTIFICATION'
,p_process_when_button_id=>wwv_flow_imp.id({delete_btn_id})
,p_process_success_message=>'Record deleted.'
,p_version_scn=>1
);"""))

        # After delete/save: redirect to list page
        redirect_proc_id = ids.next(f"proc_redirect_{form_page_id}")
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_process(
 p_id=>wwv_flow_imp.id({redirect_proc_id})
,p_flow_id=>wwv_flow.g_flow_id
,p_flow_step_id=>{form_page_id}
,p_process_sequence=>30
,p_process_point=>'AFTER_SUBMIT'
,p_process_type=>'NATIVE_SESSION_STATE'
,p_process_name=>'Return to List'
,p_attribute_01=>'CLEAR_CACHE_FOR_PAGES'
,p_attribute_02=>'{list_page_id}'
,p_error_display_location=>'INLINE_IN_NOTIFICATION'
,p_process_when=>'SAVE,DELETE'
,p_process_when_type=>'REQUEST_IN_CONDITION'
);"""))
        log.append("Post-submit processes created (delete + redirect)")

        # ── 15. Breadcrumb / nav menu entry ───────────────────────────────
        nav_id = ids.next(f"nav_{list_page_id}")
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_da_event(
 p_id=>wwv_flow_imp.id({nav_id})
,p_flow_id=>wwv_flow.g_flow_id
,p_page_id=>{form_page_id}
,p_name=>'Cancel Dialog'
,p_event_sequence=>10
,p_triggering_element_type=>'BUTTON'
,p_triggering_button_id=>wwv_flow_imp.id({cancel_btn_id})
,p_bind_type=>'bind'
,p_execution_type=>'IMMEDIATE'
,p_bind_event_type=>'click'
);"""))
        log.append("Cancel DA event created")

        return json.dumps({
            "status": "ok",
            "table": upper_table,
            "list_page_id": list_page_id,
            "form_page_id": form_page_id,
            "pages_created": [list_page_id, form_page_id],
            "items_created": items_created,
            "lovs_created": lovs_created,
            "summary": {
                "columns_found": len(cols),
                "pk_columns": list(pk_columns),
                "fk_columns": list(fk_columns),
                "items_on_form": len(items_created),
                "lovs": len(lovs_created),
            },
            "log": log,
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e), "log": log}, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# apex_generate_dashboard
# ---------------------------------------------------------------------------

def apex_generate_dashboard(
    page_id: int,
    page_name: str = "Dashboard",
    kpi_queries: list[dict] | None = None,
    ir_sql: str = "",
    ir_title: str = "Recent Records",
) -> str:
    """Generate a dashboard page with KPI cards and an Interactive Report.

    Args:
        page_id: Page ID for the dashboard (typically 1).
        page_name: Display name (default: "Dashboard").
        kpi_queries: List of KPI card definitions. Each dict:
            {
                "title": "Total Users",
                "sql": "SELECT COUNT(*) FROM users",
                "icon": "fa-users",
                "color": "u-color-1"
            }
            If omitted, creates 4 sample KPI cards.
        ir_sql: SQL for the bottom Interactive Report. If omitted, uses a sample query.
        ir_title: Title for the IR region (default: "Recent Records").

    Returns:
        JSON with status and components created.

    The dashboard layout:
        - Top: KPI cards in a responsive grid (1-4 cards)
        - Bottom: Interactive Report for detailed data

    Uses APEX Universal Theme PL/SQL dynamic content regions for KPIs.
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})
    if not session.import_begun:
        return json.dumps({"status": "error", "error": "No import session active. Call apex_create_app() first."})

    log: list[str] = []

    # Default KPI cards if none provided
    if not kpi_queries:
        kpi_queries = [
            {"title": "Total Records", "sql": "SELECT COUNT(*) FROM dual", "icon": "fa-database", "color": "u-color-1"},
            {"title": "Active Users", "sql": "SELECT COUNT(*) FROM apex_workspace_apex_users", "icon": "fa-users", "color": "u-color-2"},
            {"title": "Today", "sql": "SELECT TO_NUMBER(TO_CHAR(SYSDATE,'DD')) FROM dual", "icon": "fa-calendar", "color": "u-color-3"},
            {"title": "System", "sql": "SELECT 1 FROM dual", "icon": "fa-cog", "color": "u-color-4"},
        ]

    default_ir_sql = ir_sql or "SELECT table_name, num_rows FROM user_tables ORDER BY table_name"

    try:
        # ── Create the page ───────────────────────────────────────────────
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page(
 p_id=>{page_id}
,p_name=>'{_esc(page_name)}'
,p_alias=>'{_esc(page_name.upper().replace(" ", "-"))}'
,p_step_title=>'{_esc(page_name)}'
,p_autocomplete_on_off=>'OFF'
,p_page_mode=>'NORMAL'
,p_page_template_id=>{PAGE_TMPL_STANDARD}
,p_last_updated_by=>'APEX_MCP'
,p_last_upd_yyyymmddhh24miss=>TO_CHAR(SYSDATE,'YYYYMMDDHH24MISS')
,p_page_is_public_y_n=>'Y'
,p_protection_level=>'C'
);"""))
        session.pages[page_id] = PageInfo(
            page_id=page_id,
            page_name=page_name,
            page_type="dashboard",
        )
        log.append(f"Dashboard page {page_id} created")

        # ── KPI cards container region ────────────────────────────────────
        kpi_container_id = ids.next(f"kpi_container_{page_id}")
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_plug(
 p_id=>wwv_flow_imp.id({kpi_container_id})
,p_flow_id=>wwv_flow.g_flow_id
,p_page_id=>{page_id}
,p_plug_name=>'KPI Cards'
,p_region_template_options=>'#DEFAULT#:t-Region--noPadding:t-Region--hideHeader:t-Region--scrollBody'
,p_plug_template=>{REGION_TMPL_BLANK}
,p_plug_display_sequence=>10
,p_plug_display_point=>'BODY'
,p_last_updated_by=>'APEX_MCP'
,p_last_upd_yyyymmddhh24miss=>TO_CHAR(SYSDATE,'YYYYMMDDHH24MISS')
);"""))
        log.append("KPI container region created")

        # ── Individual KPI PL/SQL dynamic content regions ─────────────────
        for idx, kpi in enumerate(kpi_queries, start=1):
            kpi_title = kpi.get("title", f"KPI {idx}")
            kpi_sql = kpi.get("sql", "SELECT 0 FROM dual")
            kpi_icon = kpi.get("icon", "fa-info")
            kpi_color = kpi.get("color", f"u-color-{idx}")

            # PL/SQL block that queries the value and emits HTML
            plsql_source = (
                f"DECLARE\n"
                f"  v_val VARCHAR2(100);\n"
                f"BEGIN\n"
                f"  BEGIN\n"
                f"    EXECUTE IMMEDIATE '{_esc(kpi_sql)}' INTO v_val;\n"
                f"  EXCEPTION WHEN OTHERS THEN v_val := 'N/A'; END;\n"
                f"  sys.htp.p('<div class=\"t-Card\">');\n"
                f"  sys.htp.p('<a href=\"#\" class=\"t-Card-wrap\">');\n"
                f"  sys.htp.p('<div class=\"t-Card-icon {kpi_color}\">'||"
                f"'<span class=\"t-Icon {kpi_icon}\"></span></div>');\n"
                f"  sys.htp.p('<div class=\"t-Card-titleWrap\">'||"
                f"'<h3 class=\"t-Card-title\">'||APEX_ESCAPE.HTML('{_esc(kpi_title)}')||'</h3>'||"
                f"'<h4 class=\"t-Card-subtitle\">'||APEX_ESCAPE.HTML(v_val)||'</h4></div>');\n"
                f"  sys.htp.p('</a></div>');\n"
                f"END;"
            )

            kpi_region_id = ids.next(f"kpi_region_{page_id}_{idx}")
            db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_plug(
 p_id=>wwv_flow_imp.id({kpi_region_id})
,p_flow_id=>wwv_flow.g_flow_id
,p_page_id=>{page_id}
,p_plug_name=>'{_esc(kpi_title)}'
,p_parent_plug_id=>wwv_flow_imp.id({kpi_container_id})
,p_region_template_options=>'#DEFAULT#:t-Card--noPadding:t-Region--hideHeader'
,p_plug_template=>{REGION_TMPL_BLANK}
,p_plug_display_sequence=>{idx * 10}
,p_plug_display_point=>'BODY'
,p_plug_source=>'{_esc(plsql_source)}'
,p_plug_source_type=>'NATIVE_PLSQL'
,p_last_updated_by=>'APEX_MCP'
,p_last_upd_yyyymmddhh24miss=>TO_CHAR(SYSDATE,'YYYYMMDDHH24MISS')
);"""))
            session.regions[kpi_region_id] = RegionInfo(
                region_id=kpi_region_id,
                page_id=page_id,
                region_name=kpi_title,
                region_type="NATIVE_PLSQL",
            )
        log.append(f"KPI card regions created: {len(kpi_queries)}")

        # ── IR region at the bottom ───────────────────────────────────────
        ir_region_id = ids.next(f"ir_region_{page_id}")
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_plug(
 p_id=>wwv_flow_imp.id({ir_region_id})
,p_flow_id=>wwv_flow.g_flow_id
,p_page_id=>{page_id}
,p_plug_name=>'{_esc(ir_title)}'
,p_region_template_options=>'#DEFAULT#'
,p_plug_template=>{REGION_TMPL_IR}
,p_plug_display_sequence=>20
,p_plug_display_point=>'BODY'
,p_query_type=>'SQL'
,p_plug_source=>'{_esc(default_ir_sql)}'
,p_plug_source_type=>'NATIVE_IR'
,p_last_updated_by=>'APEX_MCP'
,p_last_upd_yyyymmddhh24miss=>TO_CHAR(SYSDATE,'YYYYMMDDHH24MISS')
);"""))
        session.regions[ir_region_id] = RegionInfo(
            region_id=ir_region_id,
            page_id=page_id,
            region_name=ir_title,
            region_type="NATIVE_IR",
        )
        log.append("IR region created")

        # IR worksheet
        ws_id = ids.next(f"ws_{page_id}")
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_worksheet(
 p_id=>wwv_flow_imp.id({ws_id})
,p_region_id=>wwv_flow_imp.id({ir_region_id})
,p_max_row_count=>1000
,p_max_row_count_message=>'The maximum row count for this report is #MAX_ROW_COUNT# rows.'
,p_no_data_found_message=>'No data found.'
,p_pagination_type=>'ROWS_X_TO_Y'
,p_pagination_display_pos=>'BOTTOM_RIGHT'
,p_report_list_mode=>'TABS'
,p_show_search_bar=>'YES'
,p_show_actions_menu=>'YES'
,p_show_detail_link=>'N'
,p_owner=>'APEX_MCP'
,p_internal_uid=>{ws_id}
);"""))
        log.append("IR worksheet created")

        return json.dumps({
            "status": "ok",
            "page_id": page_id,
            "page_name": page_name,
            "kpi_count": len(kpi_queries),
            "ir_sql": default_ir_sql,
            "components": {
                "kpi_container_region": kpi_container_id,
                "kpi_regions": len(kpi_queries),
                "ir_region": ir_region_id,
            },
            "log": log,
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e), "log": log}, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# apex_generate_login
# ---------------------------------------------------------------------------

def apex_generate_login(
    page_id: int = 101,
    page_name: str = "Login",
    app_name: str = "",
    username_label: str = "Username",
    password_label: str = "Password",
    login_button_label: str = "Sign In",
    auth_process_plsql: str = "",
) -> str:
    """Generate a professional login page with username, password, and authentication process.

    Args:
        page_id: Page ID (default 101). Must match the login URL in create_app.
        page_name: Page display name.
        app_name: Application name shown above the login form.
        username_label: Label for username field (default "Username").
        password_label: Label for password field (default "Password").
        login_button_label: Login button text (default "Sign In").
        auth_process_plsql: Custom PL/SQL authentication block.
            If omitted, uses APEX native authentication:
            "apex_authentication.login(p_username=>:P101_USERNAME, p_password=>:P101_PASSWORD);"

            For custom auth example:
            '''DECLARE
                 v_user_id NUMBER;
               BEGIN
                 SELECT user_id INTO v_user_id FROM app_users
                  WHERE username = LOWER(:P101_USERNAME)
                    AND password_hash = DBMS_CRYPTO.HASH(
                          UTL_RAW.CAST_TO_RAW(:P101_PASSWORD || salt), 3);
                 apex_util.set_session_state('APP_USER_ID', v_user_id);
               END;'''

    Returns:
        JSON with status and page components created.

    The login page includes:
        - Login page template (centered, no navigation)
        - Username text item (P{page_id}_USERNAME)
        - Password item (P{page_id}_PASSWORD)
        - Sign In button (hot, submit)
        - Authentication process
        - Proper error handling for bad credentials
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})
    if not session.import_begun:
        return json.dumps({"status": "error", "error": "No import session active. Call apex_create_app() first."})

    log: list[str] = []
    username_item = f"P{page_id}_USERNAME"
    password_item = f"P{page_id}_PASSWORD"

    # Default auth PL/SQL
    if not auth_process_plsql:
        auth_process_plsql = (
            f"apex_authentication.login(\n"
            f"  p_username => :{username_item},\n"
            f"  p_password => :{password_item}\n"
            f");"
        )

    # Derive the app name to show on the login page
    effective_app_name = app_name or session.app_name or "Application"

    try:
        # ── Create login page ─────────────────────────────────────────────
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page(
 p_id=>{page_id}
,p_name=>'{_esc(page_name)}'
,p_alias=>'LOGIN'
,p_step_title=>'{_esc(page_name)}'
,p_autocomplete_on_off=>'OFF'
,p_page_mode=>'NORMAL'
,p_page_template_id=>{PAGE_TMPL_LOGIN}
,p_page_is_public_y_n=>'Y'
,p_protection_level=>'C'
,p_last_updated_by=>'APEX_MCP'
,p_last_upd_yyyymmddhh24miss=>TO_CHAR(SYSDATE,'YYYYMMDDHH24MISS')
);"""))
        session.pages[page_id] = PageInfo(
            page_id=page_id,
            page_name=page_name,
            page_type="login",
        )
        log.append(f"Login page {page_id} created")

        # ── Login form region ─────────────────────────────────────────────
        login_region_id = ids.next(f"login_region_{page_id}")
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_plug(
 p_id=>wwv_flow_imp.id({login_region_id})
,p_flow_id=>wwv_flow.g_flow_id
,p_page_id=>{page_id}
,p_plug_name=>'{_esc(effective_app_name)}'
,p_icon_css_classes=>'app-login-icon'
,p_region_template_options=>'#DEFAULT#'
,p_plug_template=>2101018444965420270
,p_plug_display_sequence=>10
,p_plug_display_point=>'BODY'
,p_last_updated_by=>'APEX_MCP'
,p_last_upd_yyyymmddhh24miss=>TO_CHAR(SYSDATE,'YYYYMMDDHH24MISS')
);"""))
        session.regions[login_region_id] = RegionInfo(
            region_id=login_region_id,
            page_id=page_id,
            region_name=effective_app_name,
            region_type="LOGIN",
        )
        log.append(f"Login region {login_region_id} created")

        # ── Username item ─────────────────────────────────────────────────
        username_id = ids.next(f"item_{page_id}_username")
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_item(
 p_id=>wwv_flow_imp.id({username_id})
,p_flow_id=>wwv_flow.g_flow_id
,p_flow_step_id=>{page_id}
,p_name=>'{_esc(username_item)}'
,p_item_sequence=>10
,p_item_plug_id=>wwv_flow_imp.id({login_region_id})
,p_prompt=>'{_esc(username_label)}'
,p_placeholder=>'{_esc(username_label)}'
,p_display_as=>'{ITEM_TEXT}'
,p_cSize=>40
,p_cMaxlength=>100
,p_label_alignment=>'RIGHT'
,p_field_template=>{LABEL_OPTIONAL}
,p_item_template_options=>'#DEFAULT#'
,p_is_required=>false
,p_warn_on_unsaved_changes=>'I'
,p_attributes=>wwv_flow_t_plugin_attributes(wwv_flow_t_plugin_attribute_value('autocomplete', 'username'))
);"""))
        session.items[username_item] = ItemInfo(
            item_id=username_id,
            page_id=page_id,
            item_name=username_item,
            item_type=ITEM_TEXT,
        )
        log.append(f"Username item {username_item} created")

        # ── Password item ─────────────────────────────────────────────────
        password_id = ids.next(f"item_{page_id}_password")
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_item(
 p_id=>wwv_flow_imp.id({password_id})
,p_flow_id=>wwv_flow.g_flow_id
,p_flow_step_id=>{page_id}
,p_name=>'{_esc(password_item)}'
,p_item_sequence=>20
,p_item_plug_id=>wwv_flow_imp.id({login_region_id})
,p_prompt=>'{_esc(password_label)}'
,p_placeholder=>'{_esc(password_label)}'
,p_display_as=>'{ITEM_PASSWORD}'
,p_cSize=>40
,p_cMaxlength=>100
,p_label_alignment=>'RIGHT'
,p_field_template=>{LABEL_OPTIONAL}
,p_item_template_options=>'#DEFAULT#'
,p_is_required=>false
,p_warn_on_unsaved_changes=>'I'
,p_attributes=>wwv_flow_t_plugin_attributes(wwv_flow_t_plugin_attribute_value('autocomplete', 'current-password'))
);"""))
        session.items[password_item] = ItemInfo(
            item_id=password_id,
            page_id=page_id,
            item_name=password_item,
            item_type=ITEM_PASSWORD,
        )
        log.append(f"Password item {password_item} created")

        # ── Sign In button ────────────────────────────────────────────────
        signin_btn_id = ids.next(f"btn_signin_{page_id}")
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_button(
 p_id=>wwv_flow_imp.id({signin_btn_id})
,p_flow_id=>wwv_flow.g_flow_id
,p_flow_step_id=>{page_id}
,p_button_sequence=>30
,p_button_plug_id=>wwv_flow_imp.id({login_region_id})
,p_button_name=>'LOGIN'
,p_button_action=>'SUBMIT'
,p_button_template_options=>'#DEFAULT#:t-Button--large:t-Button--stretch'
,p_button_template_id=>{BTN_TMPL_TEXT}
,p_button_is_hot=>'Y'
,p_button_image_alt=>'{_esc(login_button_label)}'
,p_button_position=>'NEXT'
);"""))
        log.append(f"Sign In button created")

        # ── Authentication process ────────────────────────────────────────
        auth_proc_id = ids.next(f"proc_auth_{page_id}")
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_process(
 p_id=>wwv_flow_imp.id({auth_proc_id})
,p_flow_id=>wwv_flow.g_flow_id
,p_flow_step_id=>{page_id}
,p_process_sequence=>10
,p_process_point=>'AFTER_SUBMIT'
,p_process_type=>'NATIVE_PLSQL'
,p_process_name=>'Login'
,p_process_sql_clob=>'{_esc(auth_process_plsql)}'
,p_error_display_location=>'INLINE_IN_NOTIFICATION'
,p_process_when_button_id=>wwv_flow_imp.id({signin_btn_id})
);"""))
        log.append("Authentication process created")

        return json.dumps({
            "status": "ok",
            "page_id": page_id,
            "page_name": page_name,
            "items_created": [username_item, password_item],
            "login_region_id": login_region_id,
            "auth_process_id": auth_proc_id,
            "note": (
                "Login page created. Ensure the login URL in apex_create_app(login_page=...) "
                f"matches page_id={page_id}."
            ),
            "log": log,
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e), "log": log}, ensure_ascii=False, indent=2)
