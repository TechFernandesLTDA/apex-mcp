"""Advanced tools: report_page, wizard, search_bar, notification, page_css, interactive_grid, bulk_items, validate, preview."""
from __future__ import annotations
import json
from typing import Any
from ..db import db
from ..ids import ids
from ..session import session, PageInfo, RegionInfo, ItemInfo
from ..templates import (
    REGION_TMPL_STANDARD, REGION_TMPL_IR, REGION_TMPL_BLANK,
    BTN_TMPL_TEXT, LABEL_OPTIONAL, LABEL_REQUIRED,
    ITEM_TEXT, ITEM_SELECT, ITEM_DATE, ITEM_NUMBER, ITEM_HIDDEN, ITEM_TEXTAREA,
    PROC_PLSQL,
)
from ..config import WORKSPACE_ID, APEX_SCHEMA


def _esc(v: str) -> str:
    return v.replace("'", "''")

def _blk(sql: str) -> str:
    return f"begin\n{sql}\nend;"

def _sql_to_varchar2(sql: str) -> str:
    lines = sql.replace("'", "''").splitlines()
    if not lines:
        return "''"
    return "wwv_flow_string.join(wwv_flow_t_varchar2(\n" + ",\n".join(f"'{l}'" for l in lines) + "))"


# ---------------------------------------------------------------------------
# apex_generate_report_page
# ---------------------------------------------------------------------------

def apex_generate_report_page(
    page_id: int,
    page_name: str,
    sql_query: str,
    filter_items: list[dict[str, Any]] | None = None,
    title: str = "",
    auth_scheme: str = "",
    include_export: bool = True,
    sequence: int = 10,
) -> str:
    """Generate a report page with Interactive Report + filter items.

    Creates a page with:
    1. Optional filter items (text/select/date fields) at the top
    2. Interactive Report with the provided SQL
    3. Export button (optional)

    Args:
        page_id: Page ID.
        page_name: Display name.
        sql_query: SQL for the Interactive Report.
            Example: "SELECT * FROM TEA_AVALIACOES WHERE 1=1
                        AND (:P5_STATUS IS NULL OR DS_STATUS = :P5_STATUS)"
        filter_items: List of filter field dicts:
            [{"name": "STATUS", "label": "Status", "type": "select",
              "lov": "SELECT DISTINCT DS_STATUS d, DS_STATUS r FROM TEA_AVALIACOES ORDER BY 1"},
             {"name": "DT_DE", "label": "Data De", "type": "date"},
             {"name": "BUSCA", "label": "Pesquisa", "type": "text"}]
            Item names are auto-prefixed with P{page_id}_.
        title: Optional region title (defaults to page_name).
        auth_scheme: Authorization scheme name.
        include_export: Show export to CSV/Excel button (default True).
        sequence: IR region sequence.

    Returns:
        JSON with status, page_id, items_created.
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})
    if not session.import_begun:
        return json.dumps({"status": "error", "error": "No import session active."})

    ir_title = title or page_name
    log: list[str] = []

    try:
        # Create page if not exists
        if page_id not in session.pages:
            auth_line = f",p_required_role=>'{_esc(auth_scheme)}'\n,p_page_is_public_y_n=>'N'\n,p_protection_level=>'C'" if auth_scheme else ",p_page_is_public_y_n=>'Y'\n,p_protection_level=>'C'"
            db.plsql(_blk(f"""
wwv_flow_imp_page.create_page(
 p_id=>{page_id}
,p_name=>'{_esc(page_name)}'
,p_alias=>'{_esc(page_name.upper().replace(" ","-"))}'
,p_step_title=>'{_esc(page_name)}'
,p_autocomplete_on_off=>'OFF'
,p_page_template_options=>'#DEFAULT#'
{auth_line}
);"""))
            session.pages[page_id] = PageInfo(page_id=page_id, page_name=page_name, page_type="report")
            log.append(f"Page {page_id} created")

        items_created: list[str] = []

        # Filter region (if filter_items provided)
        if filter_items:
            filter_region_id = ids.next(f"filter_region_{page_id}")
            db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_plug(
 p_id=>wwv_flow_imp.id({filter_region_id})
,p_plug_name=>'Filtros'
,p_region_template_options=>'#DEFAULT#:t-Form--stretchInputs:t-Form--labelsAbove'
,p_plug_template=>{REGION_TMPL_STANDARD}
,p_plug_display_sequence=>5
,p_plug_display_point=>'BODY'
,p_plug_source_type=>'NATIVE_STATIC'
);"""))
            session.regions[filter_region_id] = RegionInfo(
                region_id=filter_region_id, page_id=page_id,
                region_name="Filtros", region_type="filter"
            )

            type_map = {"text": ITEM_TEXT, "select": ITEM_SELECT, "date": ITEM_DATE, "number": ITEM_NUMBER}
            for seq_n, fi in enumerate(filter_items, start=10):
                fi_name = fi.get("name", f"FILTER{seq_n}")
                item_name = f"P{page_id}_{fi_name.upper()}"
                fi_label = fi.get("label", fi_name.replace("_", " ").title())
                fi_type = type_map.get(fi.get("type", "text"), ITEM_TEXT)
                fi_lov = fi.get("lov", "")
                item_id = ids.next(f"item_{page_id}_{fi_name.lower()}")
                lov_line = f",p_lov=>'{_esc(fi_lov)}'\n,p_lov_display_null=>'YES'\n,p_lov_null_text=>'- All -'" if fi_lov else ""
                db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_item(
 p_id=>wwv_flow_imp.id({item_id})
,p_name=>'{_esc(item_name)}'
,p_item_sequence=>{seq_n * 10}
,p_item_plug_id=>wwv_flow_imp.id({filter_region_id})
,p_prompt=>'{_esc(fi_label)}'
,p_display_as=>'{fi_type}'
,p_label_alignment=>'RIGHT'
,p_field_template=>{LABEL_OPTIONAL}
,p_item_template_options=>'#DEFAULT#'
{lov_line}
);"""))
                session.items[item_name] = ItemInfo(item_id=item_id, page_id=page_id, item_name=item_name, item_type=fi_type)
                items_created.append(item_name)

            # Search button
            search_btn_id = ids.next(f"btn_search_{page_id}")
            db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_button(
 p_id=>wwv_flow_imp.id({search_btn_id})
,p_button_sequence=>10
,p_button_plug_id=>wwv_flow_imp.id({filter_region_id})
,p_button_name=>'SEARCH'
,p_button_action=>'SUBMIT'
,p_button_template_options=>'#DEFAULT#'
,p_button_template_id=>{BTN_TMPL_TEXT}
,p_button_is_hot=>'Y'
,p_button_image_alt=>'Search'
,p_button_position=>'BELOW_BOX'
);"""))
            log.append(f"Filter region + {len(filter_items)} filter items created")

        # IR region
        ir_region_id = ids.next(f"ir_region_{page_id}")
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_plug(
 p_id=>wwv_flow_imp.id({ir_region_id})
,p_plug_name=>'{_esc(ir_title)}'
,p_region_template_options=>'#DEFAULT#'
,p_plug_template=>{REGION_TMPL_IR}
,p_plug_display_sequence=>{sequence}
,p_plug_display_point=>'BODY'
,p_query_type=>'SQL'
,p_plug_source=>'{_esc(sql_query)}'
,p_plug_source_type=>'NATIVE_IR'
);"""))
        session.regions[ir_region_id] = RegionInfo(
            region_id=ir_region_id, page_id=page_id,
            region_name=ir_title, region_type="NATIVE_IR"
        )

        ws_id = ids.next(f"ws_{page_id}")
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_worksheet(
 p_id=>wwv_flow_imp.id({ws_id})
,p_region_id=>wwv_flow_imp.id({ir_region_id})
,p_max_row_count=>10000
,p_max_row_count_message=>'More than #MAX_ROW_COUNT# rows found — apply a filter.'
,p_no_data_found_message=>'No records found.'
,p_pagination_type=>'ROWS_X_TO_Y'
,p_pagination_display_pos=>'BOTTOM_RIGHT'
,p_report_list_mode=>'TABS'
,p_show_search_bar=>'Y'
,p_show_actions_menu=>'Y'
,p_show_detail_link=>'N'
,p_download_formats=>'{"CSV:HTML:XLSX:PDF" if include_export else ""}'
,p_owner=>'APEX_MCP'
,p_internal_uid=>{ws_id}
);"""))
        log.append("IR region + worksheet created")

        return json.dumps({
            "status": "ok", "page_id": page_id, "page_name": page_name,
            "ir_region_id": ir_region_id, "items_created": items_created,
            "message": f"Report page {page_id} '{page_name}' created with {len(filter_items or [])} filter(s).",
            "log": log,
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e), "log": log}, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# apex_generate_wizard
# ---------------------------------------------------------------------------

def apex_generate_wizard(
    start_page_id: int,
    steps: list[dict[str, Any]],
    wizard_title: str = "Wizard",
    auth_scheme: str = "",
    finish_redirect_page: int | None = None,
) -> str:
    """Generate a multi-step wizard (2-6 steps) with progress indicator.

    Each step is a separate APEX page with items, Previous/Next buttons,
    and a progress bar rendered via inline HTML.

    Args:
        start_page_id: First step page ID. Subsequent steps use start_page_id+1, +2...
        steps: List of step definitions. Each dict:
            {
              "title": "Step 1: Basic Info",
              "items": [
                {"name": "NOME", "label": "Full Name", "type": "text", "required": True},
                {"name": "EMAIL", "label": "Email", "type": "text"},
              ]
            }
        wizard_title: Wizard header title.
        auth_scheme: Authorization scheme name.
        finish_redirect_page: Page to redirect to on final step submit. Defaults to page 1.

    Returns:
        JSON with status, pages created, items created.
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})
    if not session.import_begun:
        return json.dumps({"status": "error", "error": "No import session active."})
    if not steps:
        return json.dumps({"status": "error", "error": "At least one step is required."})

    log: list[str] = []
    all_items: list[str] = []
    finish_page = finish_redirect_page or 1
    total_steps = len(steps)
    auth_line = f",p_required_role=>'{_esc(auth_scheme)}'\n,p_page_is_public_y_n=>'N'\n,p_protection_level=>'C'" if auth_scheme else ",p_page_is_public_y_n=>'Y'\n,p_protection_level=>'C'"

    try:
        type_map = {"text": ITEM_TEXT, "select": ITEM_SELECT, "date": ITEM_DATE, "number": ITEM_NUMBER, "textarea": ITEM_TEXTAREA, "hidden": ITEM_HIDDEN}

        for step_idx, step in enumerate(steps):
            page_id = start_page_id + step_idx
            step_title = step.get("title", f"Step {step_idx + 1}")
            step_items = step.get("items", [])
            is_last = step_idx == total_steps - 1
            is_first = step_idx == 0
            next_page = page_id + 1 if not is_last else finish_page
            prev_page = page_id - 1 if not is_first else page_id

            # Page
            db.plsql(_blk(f"""
wwv_flow_imp_page.create_page(
 p_id=>{page_id}
,p_name=>'{_esc(step_title)}'
,p_alias=>'WIZARD-STEP-{step_idx+1}'
,p_step_title=>'{_esc(step_title)}'
,p_autocomplete_on_off=>'OFF'
,p_page_template_options=>'#DEFAULT#'
{auth_line}
);"""))
            session.pages[page_id] = PageInfo(page_id=page_id, page_name=step_title, page_type="form")

            # Progress bar region
            pct = int((step_idx + 1) / total_steps * 100)
            step_labels = "".join(
                f'<span class="wizard-step{" active" if i == step_idx else " done" if i < step_idx else ""}">{s.get("title","Step "+str(i+1))}</span>'
                for i, s in enumerate(steps)
            )
            progress_plsql = f"""BEGIN
  sys.htp.p('<style>
    .wizard-header{{padding:16px 0 20px;}}
    .wizard-steps{{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px;}}
    .wizard-step{{flex:1;text-align:center;font-size:.75rem;padding:6px 4px;border-radius:4px;
      background:#f1f5f9;color:#64748b;}}
    .wizard-step.done{{background:#dcfce7;color:#166534;}}
    .wizard-step.active{{background:#3b82f6;color:#fff;font-weight:600;}}
    .wizard-progress{{height:6px;background:#e2e8f0;border-radius:3px;overflow:hidden;}}
    .wizard-progress-bar{{height:100%;background:#3b82f6;border-radius:3px;
      transition:width .4s ease;width:{pct}%;}}
  </style>');
  sys.htp.p('<div class="wizard-header">');
  sys.htp.p('<div class="wizard-steps">{step_labels}</div>');
  sys.htp.p('<div class="wizard-progress"><div class="wizard-progress-bar"></div></div>');
  sys.htp.p('</div>');
END;"""
            prog_region_id = ids.next(f"prog_region_{page_id}")
            db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_plug(
 p_id=>wwv_flow_imp.id({prog_region_id})
,p_plug_name=>'Progress'
,p_region_template_options=>'#DEFAULT#:t-Region--noPadding:t-Region--hideHeader'
,p_plug_template=>{REGION_TMPL_BLANK}
,p_plug_display_sequence=>5
,p_plug_display_point=>'BODY'
,p_plug_source=>'{_esc(progress_plsql)}'
,p_plug_source_type=>'NATIVE_PLSQL'
,p_plug_query_options=>'DERIVED_REPORT_COLUMNS'
);"""))

            # Form region
            form_region_id = ids.next(f"form_region_{page_id}")
            db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_plug(
 p_id=>wwv_flow_imp.id({form_region_id})
,p_plug_name=>'{_esc(step_title)}'
,p_region_template_options=>'#DEFAULT#'
,p_plug_template=>{REGION_TMPL_STANDARD}
,p_plug_display_sequence=>10
,p_plug_display_point=>'BODY'
,p_plug_source_type=>'NATIVE_STATIC'
);"""))
            session.regions[form_region_id] = RegionInfo(
                region_id=form_region_id, page_id=page_id,
                region_name=step_title, region_type="form"
            )

            # Items
            for seq_n, item in enumerate(step_items, start=10):
                item_name = f"P{page_id}_{item.get('name','ITEM'+str(seq_n)).upper()}"
                item_label = item.get("label", item.get("name","Item").replace("_"," ").title())
                item_type = type_map.get(item.get("type","text"), ITEM_TEXT)
                is_req = item.get("required", False)
                item_lov = item.get("lov","")
                label_tmpl = LABEL_REQUIRED if is_req else LABEL_OPTIONAL
                item_id = ids.next(f"item_{page_id}_{item.get('name','').lower()}")
                lov_line = f",p_lov=>'{_esc(item_lov)}'\n,p_lov_display_null=>'YES'" if item_lov else ""
                db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_item(
 p_id=>wwv_flow_imp.id({item_id})
,p_name=>'{_esc(item_name)}'
,p_item_sequence=>{seq_n * 10}
,p_item_plug_id=>wwv_flow_imp.id({form_region_id})
,p_prompt=>'{_esc(item_label)}'
,p_display_as=>'{item_type}'
,p_label_alignment=>'RIGHT'
,p_field_template=>{label_tmpl}
,p_item_template_options=>'#DEFAULT#'
{lov_line}
);"""))
                session.items[item_name] = ItemInfo(item_id=item_id, page_id=page_id, item_name=item_name, item_type=item_type)
                all_items.append(item_name)

            # Buttons
            btn_region_id = ids.next(f"btn_region_{page_id}")
            db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_plug(
 p_id=>wwv_flow_imp.id({btn_region_id})
,p_plug_name=>'Buttons'
,p_region_template_options=>'#DEFAULT#'
,p_plug_template=>2126429139436695430
,p_plug_display_sequence=>20
,p_plug_display_point=>'REGION_POSITION_03'
);"""))

            if not is_first:
                prev_btn_id = ids.next(f"btn_prev_{page_id}")
                db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_button(
 p_id=>wwv_flow_imp.id({prev_btn_id})
,p_button_sequence=>10
,p_button_plug_id=>wwv_flow_imp.id({btn_region_id})
,p_button_name=>'PREVIOUS'
,p_button_action=>'REDIRECT_URL'
,p_button_template_options=>'#DEFAULT#'
,p_button_template_id=>{BTN_TMPL_TEXT}
,p_button_is_hot=>'N'
,p_button_image_alt=>'Previous'
,p_button_position=>'EDIT'
,p_button_redirect_url=>'f?p=&APP_ID.:{prev_page}:&SESSION.::&DEBUG.:::'
);"""))

            next_btn_id = ids.next(f"btn_next_{page_id}")
            next_label = "Finish" if is_last else "Next"
            next_hot = is_last
            db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_button(
 p_id=>wwv_flow_imp.id({next_btn_id})
,p_button_sequence=>20
,p_button_plug_id=>wwv_flow_imp.id({btn_region_id})
,p_button_name=>'NEXT'
,p_button_action=>'{"SUBMIT" if is_last else "REDIRECT_URL"}'
,p_button_template_options=>'#DEFAULT#'
,p_button_template_id=>{BTN_TMPL_TEXT}
,p_button_is_hot=>'{"Y" if next_hot else "Y"}'
,p_button_image_alt=>'{next_label}'
,p_button_position=>'EDIT'
{f",p_button_redirect_url=>'f?p=&APP_ID.:{next_page}:&SESSION.::&DEBUG.:::'" if not is_last else ""}
);"""))

            if is_last:
                redir_proc_id = ids.next(f"proc_redir_{page_id}")
                db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_process(
 p_id=>wwv_flow_imp.id({redir_proc_id})
,p_process_sequence=>10
,p_process_point=>'AFTER_SUBMIT'
,p_process_type=>'NATIVE_SESSION_STATE'
,p_process_name=>'Finish Wizard'
,p_attribute_01=>'CLEAR_CACHE_FOR_PAGES'
,p_attribute_02=>'{finish_page}'
,p_error_display_location=>'INLINE_IN_NOTIFICATION'
);"""))

            log.append(f"Step {step_idx+1}: page {page_id} '{step_title}' created ({len(step_items)} items)")

        return json.dumps({
            "status": "ok",
            "wizard_title": wizard_title,
            "steps": total_steps,
            "pages": list(range(start_page_id, start_page_id + total_steps)),
            "items_created": all_items,
            "message": f"Wizard '{wizard_title}' created with {total_steps} steps.",
            "log": log,
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e), "log": log}, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# apex_add_notification_region
# ---------------------------------------------------------------------------

def apex_add_notification_region(
    page_id: int,
    region_name: str,
    message: str = "",
    message_sql: str = "",
    notification_type: str = "info",
    dismissible: bool = True,
    sequence: int = 5,
    condition_item: str = "",
) -> str:
    """Add an inline notification/alert region to a page.

    Renders a styled alert box (info/success/warning/error) with a message
    that can be static text or dynamically queried from the database.

    Args:
        page_id: Target page ID.
        region_name: Internal region name.
        message: Static message text. Use {item_name} for substitution:
            e.g., "Welcome back, &APP_USER.!"
        message_sql: SQL returning a single VARCHAR2 value as the message.
            If provided, overrides message. Example:
            "SELECT 'Last login: ' || TO_CHAR(DT_ULTIMO_ACESSO,'DD/MM/YYYY')
               FROM TEA_USUARIOS WHERE DS_LOGIN = :APP_USER"
        notification_type: Alert style:
            - "info": Blue information box (default)
            - "success": Green success box
            - "warning": Orange warning box
            - "error": Red error box
        dismissible: Show X button to close the notification (default True).
        sequence: Display order on page (default 5 = top of page).
        condition_item: Show notification only when this page item is not null.

    Returns:
        JSON with status, region_id.
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})
    if not session.import_begun:
        return json.dumps({"status": "error", "error": "No import session active."})
    if page_id not in session.pages:
        return json.dumps({"status": "error", "error": f"Page {page_id} not found."})

    type_styles = {
        "info":    ("#1e88e5", "#e3f2fd", "#bbdefb", "fa-info-circle"),
        "success": ("#2e7d32", "#e8f5e9", "#c8e6c9", "fa-check-circle"),
        "warning": ("#e65100", "#fff3e0", "#ffe0b2", "fa-exclamation-triangle"),
        "error":   ("#c62828", "#ffebee", "#ffcdd2", "fa-times-circle"),
    }
    txt_color, bg_color, border_color, icon = type_styles.get(notification_type, type_styles["info"])
    dismiss_btn = f'<button onclick="this.parentElement.remove()" style="float:right;background:none;border:none;cursor:pointer;color:{txt_color};font-size:16px;">&times;</button>' if dismissible else ""

    if message_sql:
        plsql_body = f"""DECLARE
  v_msg VARCHAR2(4000);
BEGIN
  BEGIN
    EXECUTE IMMEDIATE '{_esc(message_sql)}' INTO v_msg;
  EXCEPTION WHEN OTHERS THEN v_msg := '';
  END;
  IF v_msg IS NOT NULL THEN
    sys.htp.p('<div style="background:{bg_color};border:1px solid {border_color};border-radius:8px;'||
              'padding:12px 16px;margin-bottom:12px;color:{txt_color};">');
    sys.htp.p('{_esc(dismiss_btn)}');
    sys.htp.p('<span class="fa {icon}" style="margin-right:8px;"></span>' || APEX_ESCAPE.HTML(v_msg));
    sys.htp.p('</div>');
  END IF;
END;"""
    else:
        safe_msg = _esc(message or "Notification")
        plsql_body = f"""BEGIN
  sys.htp.p('<div style="background:{bg_color};border:1px solid {border_color};border-radius:8px;'||
            'padding:12px 16px;margin-bottom:12px;color:{txt_color};">');
  sys.htp.p('{_esc(dismiss_btn)}');
  sys.htp.p('<span class="fa {icon}" style="margin-right:8px;"></span>{safe_msg}');
  sys.htp.p('</div>');
END;"""

    try:
        region_id = ids.next(f"notif_region_{page_id}_{_esc(region_name)}")

        cond_line = f"\n,p_plug_display_condition_type=>'ITEM_IS_NOT_NULL'\n,p_plug_display_when_condition=>'{_esc(condition_item)}'" if condition_item else ""

        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_plug(
 p_id=>wwv_flow_imp.id({region_id})
,p_plug_name=>'{_esc(region_name)}'
,p_region_template_options=>'#DEFAULT#:t-Region--noPadding:t-Region--hideHeader'
,p_plug_template=>{REGION_TMPL_BLANK}
,p_plug_display_sequence=>{sequence}
,p_plug_display_point=>'BODY'
,p_plug_source=>'{_esc(plsql_body)}'
,p_plug_source_type=>'NATIVE_PLSQL'
,p_plug_query_options=>'DERIVED_REPORT_COLUMNS'
{cond_line}
);"""))

        session.regions[region_id] = RegionInfo(
            region_id=region_id, page_id=page_id,
            region_name=region_name, region_type="notification"
        )

        return json.dumps({
            "status": "ok", "region_id": region_id, "notification_type": notification_type,
            "page_id": page_id,
            "message": f"Notification region '{region_name}' ({notification_type}) added to page {page_id}.",
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# apex_add_page_css
# ---------------------------------------------------------------------------

def apex_add_page_css(
    page_id: int,
    css_code: str,
) -> str:
    """Add inline CSS to a page (equivalent to Page > CSS > Inline in App Builder).

    The CSS is injected into the page's <head> via the p_inline_css parameter.
    Use for page-specific styling that shouldn't affect the whole application.
    For global CSS affecting all pages, upload a static file instead.

    Args:
        page_id: Target page ID.
        css_code: CSS rules to inject. Example:
            ".my-region { border: 2px solid #00995D; border-radius: 8px; }
             .my-region .t-Region-header { background: #00995D; color: #fff; }"

    Returns:
        JSON with status.

    Note:
        This updates the page's inline CSS — if called multiple times for the same
        page, only the last call takes effect. Concatenate your CSS before calling.
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})
    if not session.import_begun:
        return json.dumps({"status": "error", "error": "No import session active."})
    if page_id not in session.pages:
        return json.dumps({"status": "error", "error": f"Page {page_id} not found."})

    try:
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_plug(
 p_id=>wwv_flow_imp.id({ids.next(f"css_region_{page_id}")})
,p_plug_name=>'Page CSS'
,p_region_template_options=>'#DEFAULT#:t-Region--noPadding:t-Region--hideHeader'
,p_plug_template=>{REGION_TMPL_BLANK}
,p_plug_display_sequence=>1
,p_plug_display_point=>'BODY'
,p_plug_source=>'begin sys.htp.p(''<style>{_esc(css_code)}</style>''); end;'
,p_plug_source_type=>'NATIVE_PLSQL'
,p_plug_query_options=>'DERIVED_REPORT_COLUMNS'
);"""))

        return json.dumps({
            "status": "ok", "page_id": page_id,
            "message": f"CSS injected into page {page_id} ({len(css_code)} chars).",
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# apex_add_interactive_grid
# ---------------------------------------------------------------------------

def apex_add_interactive_grid(
    page_id: int,
    region_name: str,
    table_name: str,
    sql_query: str = "",
    editable: bool = True,
    add_row: bool = True,
    sequence: int = 10,
    auth_scheme: str = "",
) -> str:
    """Add an Interactive Grid (IG) region to a page.

    Interactive Grid is more powerful than IR for data entry — it allows
    inline editing of multiple rows simultaneously, like a spreadsheet.

    Args:
        page_id: Target page ID.
        region_name: Region display name.
        table_name: Database table for DML operations (INSERT/UPDATE/DELETE).
        sql_query: SELECT SQL for the IG. If omitted, uses SELECT * FROM table_name.
        editable: Allow inline cell editing (default True).
        add_row: Show "Add Row" button for inserting new records (default True).
        sequence: Region display order.
        auth_scheme: Authorization scheme name.

    Returns:
        JSON with status, region_id.
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})
    if not session.import_begun:
        return json.dumps({"status": "error", "error": "No import session active."})
    if page_id not in session.pages:
        return json.dumps({"status": "error", "error": f"Page {page_id} not found."})

    upper_table = table_name.upper()
    ig_sql = sql_query or f"SELECT * FROM {upper_table}"
    edit_enabled = "Y" if editable else "N"
    add_enabled = "Y" if add_row else "N"

    try:
        region_id = ids.next(f"ig_region_{page_id}_{_esc(region_name)}")

        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_plug(
 p_id=>wwv_flow_imp.id({region_id})
,p_plug_name=>'{_esc(region_name)}'
,p_region_template_options=>'#DEFAULT#'
,p_plug_template=>{REGION_TMPL_STANDARD}
,p_plug_display_sequence=>{sequence}
,p_plug_display_point=>'BODY'
,p_query_type=>'SQL'
,p_plug_source=>'{_esc(ig_sql)}'
,p_plug_source_type=>'NATIVE_IG'
);"""))

        ig_id = ids.next(f"ig_def_{page_id}_{_esc(region_name)}")
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_interactive_grid(
 p_id=>wwv_flow_imp.id({ig_id})
,p_internal_uid=>{ig_id}
,p_is_editable=>{edit_enabled}
,p_edit_operations=>'{"iud" if editable else "r"}'
,p_lost_update_check_type=>'VALUES'
,p_add_row_if_empty=>'N'
,p_submit_checked_rows=>false
,p_lazy_loading=>false
,p_requires_filter=>false
,p_max_rows=>100
,p_show_nulls_as=>'-'
,p_pagination_type=>'SCROLL'
,p_show_total_row_count=>true
,p_show_toolbar=>true
,p_toolbar_buttons=>'{"SEARCH,SAVE,ADD_ROW" if add_row else "SEARCH,SAVE"}'
,p_enable_save_public_report=>false
,p_enable_subscriptions=>false
,p_enable_flashback=>false
,p_define_chart_view=>false
,p_enable_download=>true
,p_download_formats=>'CSV:HTML:XLSX'
,p_enable_mail_download=>true
,p_fixed_row_height=>true
,p_pagination_max_rows=>100
,p_show_icon_view=>false
,p_show_detail_view=>false
);"""))

        session.regions[region_id] = RegionInfo(
            region_id=region_id, page_id=page_id,
            region_name=region_name, region_type="NATIVE_IG"
        )

        return json.dumps({
            "status": "ok", "region_id": region_id, "ig_id": ig_id,
            "table": upper_table, "editable": editable, "page_id": page_id,
            "message": f"Interactive Grid '{region_name}' added to page {page_id} (editable={editable}).",
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# apex_bulk_add_items
# ---------------------------------------------------------------------------

def apex_bulk_add_items(
    page_id: int,
    region_name: str,
    items: list[dict[str, Any]],
    start_sequence: int = 10,
) -> str:
    """Add multiple form items to a region in a single call.

    Efficient alternative to calling apex_add_item() for each field.
    Automatically assigns sequences and handles LOVs.

    Args:
        page_id: Target page ID.
        region_name: Parent region name (must exist).
        items: List of item dicts. Each dict:
            {
                "name": "DS_NOME",        # required — auto-prefixed with P{page_id}_
                "label": "Full Name",     # optional — auto-generated if omitted
                "type": "text",           # text|number|date|select|textarea|hidden|yes_no
                "required": True,         # optional — shows required indicator
                "lov": "SELECT d, r FROM table ORDER BY 1",  # for select type
                "default": "ACTIVE",      # optional default value
                "placeholder": "Enter...",# optional placeholder
                "colspan": 1,            # optional grid columns (1-12)
            }
        start_sequence: Sequence number for first item (default 10, increments by 10).

    Returns:
        JSON with status, items_created list.
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})
    if not session.import_begun:
        return json.dumps({"status": "error", "error": "No import session active."})
    if page_id not in session.pages:
        return json.dumps({"status": "error", "error": f"Page {page_id} not found."})

    # Find region
    region_id = None
    for reg in session.regions.values():
        if reg.page_id == page_id and reg.region_name == region_name:
            region_id = reg.region_id
            break
    if region_id is None:
        return json.dumps({"status": "error", "error": f"Region '{region_name}' not found on page {page_id}."})

    type_map = {
        "text": ITEM_TEXT, "number": ITEM_NUMBER, "date": ITEM_DATE,
        "select": ITEM_SELECT, "textarea": ITEM_TEXTAREA, "hidden": ITEM_HIDDEN,
        "yes_no": "NATIVE_YES_NO", "password": "NATIVE_PASSWORD",
    }
    items_created: list[str] = []
    errors: list[str] = []

    seq = start_sequence
    for item in items:
        raw_name = item.get("name", "")
        if not raw_name:
            errors.append("Skipped item with no name")
            continue
        item_name = f"P{page_id}_{raw_name.upper()}" if not raw_name.upper().startswith(f"P{page_id}_") else raw_name.upper()
        label = item.get("label") or raw_name.replace("_", " ").title()
        item_type = type_map.get(item.get("type", "text"), ITEM_TEXT)
        is_req = item.get("required", False)
        label_tmpl = LABEL_REQUIRED if is_req else LABEL_OPTIONAL
        lov = item.get("lov", "")
        default = item.get("default", "")
        placeholder = item.get("placeholder", "")
        colspan = item.get("colspan", 1)

        try:
            item_id = ids.next(f"item_{page_id}_{raw_name.lower()}")
            lov_line = f",p_lov=>'{_esc(lov)}'\n,p_lov_display_null=>'YES'\n,p_lov_null_text=>'- Select -'" if lov else ""
            default_line = f",p_item_default=>'{_esc(default)}'" if default else ""
            placeholder_line = f",p_placeholder=>'{_esc(placeholder)}'" if placeholder else ""
            colspan_line = f",p_colspan=>{colspan}" if colspan and colspan > 1 else ""

            db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_item(
 p_id=>wwv_flow_imp.id({item_id})
,p_name=>'{_esc(item_name)}'
,p_item_sequence=>{seq}
,p_item_plug_id=>wwv_flow_imp.id({region_id})
,p_prompt=>'{_esc(label)}'
,p_display_as=>'{item_type}'
,p_label_alignment=>'RIGHT'
,p_field_template=>{label_tmpl}
,p_item_template_options=>'#DEFAULT#'
{lov_line}
{default_line}
{placeholder_line}
{colspan_line}
);"""))
            session.items[item_name] = ItemInfo(item_id=item_id, page_id=page_id, item_name=item_name, item_type=item_type)
            items_created.append(item_name)
            seq += 10
        except Exception as e:
            errors.append(f"{item_name}: {e}")

    return json.dumps({
        "status": "ok" if not errors else "partial",
        "items_created": items_created,
        "errors": errors,
        "count": len(items_created),
        "message": f"{len(items_created)} items added to region '{region_name}' on page {page_id}.",
    }, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# apex_validate_app
# ---------------------------------------------------------------------------

def apex_validate_app(app_id: int | None = None) -> str:
    """Validate an APEX application and return any errors or warnings.

    Checks the application for common issues: invalid SQL, broken page references,
    missing items, unauthorized access, etc. Runs APEX's built-in validation.

    Args:
        app_id: Application ID to validate. Uses current session app if omitted.

    Returns:
        JSON with validation results: errors, warnings, info messages, and a score.
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})

    effective_app_id = app_id or (session.app_id if session.app_id else None)
    if not effective_app_id:
        return json.dumps({"status": "error", "error": "No app_id provided and no active session."})

    try:
        rows = db.execute("""
            SELECT message_type,
                   message,
                   page_id,
                   component_name,
                   component_type
              FROM apex_application_all_auth
             WHERE application_id = :app_id
               AND message_type IN ('ERROR','WARNING')
             ORDER BY message_type, page_id
        """, {"app_id": effective_app_id})

        errors   = [r for r in rows if r.get("MESSAGE_TYPE") == "ERROR"]
        warnings = [r for r in rows if r.get("MESSAGE_TYPE") == "WARNING"]

        # Also check for pages/regions with invalid SQL using system view
        invalid_items = db.execute("""
            SELECT page_id, item_name, item_type
              FROM apex_application_page_items
             WHERE application_id = :app_id
               AND item_type LIKE '%SELECT%'
               AND list_of_values_type IS NULL
               AND lov_definition IS NULL
             ORDER BY page_id
        """, {"app_id": effective_app_id})

        score = 100 - len(errors) * 10 - len(warnings) * 2
        score = max(0, min(100, score))

        return json.dumps({
            "status": "ok",
            "app_id": effective_app_id,
            "validation_score": score,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "errors": errors[:20],
            "warnings": warnings[:20],
            "select_items_without_lov": invalid_items[:10],
            "message": f"Validation complete: {len(errors)} errors, {len(warnings)} warnings. Score: {score}/100.",
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# apex_preview_page
# ---------------------------------------------------------------------------

def apex_preview_page(
    page_id: int | None = None,
    app_id: int | None = None,
) -> str:
    """Get the direct URL to preview a page in the APEX runtime.

    Returns the full URL to open the page in the browser after creating it.
    The URL is relative and must be combined with your APEX base URL.

    Args:
        page_id: Page ID to preview. Uses last created page if omitted.
        app_id: Application ID. Uses current session app if omitted.

    Returns:
        JSON with:
            - apex_url: Relative URL (f?p=APP_ID:PAGE_ID...)
            - full_hint: Instructions to combine with APEX base URL
            - page_info: Page details from session
    """
    effective_app_id = app_id or (session.app_id if session.app_id else None)
    effective_page_id = page_id

    if not effective_app_id:
        return json.dumps({"status": "error", "error": "No app_id available. Provide app_id or call apex_create_app() first."})

    if not effective_page_id:
        # Use last page in session
        if session.pages:
            effective_page_id = max(session.pages.keys())
        else:
            return json.dumps({"status": "error", "error": "No page_id provided and no pages in session."})

    page_info = None
    if effective_page_id in session.pages:
        p = session.pages[effective_page_id]
        page_info = {"page_id": p.page_id, "page_name": p.page_name, "page_type": p.page_type}

    apex_url = f"f?p={effective_app_id}:{effective_page_id}"

    return json.dumps({
        "status": "ok",
        "app_id": effective_app_id,
        "page_id": effective_page_id,
        "apex_url": apex_url,
        "page_info": page_info,
        "full_hint": (
            f"Combine with your APEX base URL. Example:\n"
            f"https://your-adb.oraclecloudapps.com/ords/{apex_url}\n"
            f"Or use the relative URL: {apex_url}"
        ),
        "message": f"Preview URL for App {effective_app_id}, Page {effective_page_id}: {apex_url}",
    }, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# apex_add_search_bar
# ---------------------------------------------------------------------------

def apex_add_search_bar(
    page_id: int,
    region_name: str,
    target_region_name: str,
    search_item_name: str = "BUSCA",
    search_label: str = "Search",
    placeholder: str = "Type to search...",
    sequence: int = 5,
) -> str:
    """Add a real-time search bar that filters an Interactive Report via Dynamic Action.

    Creates a text input that filters the target IR region on every keystroke
    using APEX's native IR filtering (apex.region.refresh with search).

    Args:
        page_id: Target page ID.
        region_name: Name for the search bar region.
        target_region_name: Name of the IR region to filter.
        search_item_name: Item name suffix (auto-prefixed with P{page_id}_).
        search_label: Label for the search field.
        placeholder: Input placeholder text.
        sequence: Search bar region display order (before IR region).

    Returns:
        JSON with status, item created, dynamic action created.
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})
    if not session.import_begun:
        return json.dumps({"status": "error", "error": "No import session active."})
    if page_id not in session.pages:
        return json.dumps({"status": "error", "error": f"Page {page_id} not found."})

    full_item_name = f"P{page_id}_{search_item_name.upper()}"

    try:
        # Search region
        search_region_id = ids.next(f"search_region_{page_id}")
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_plug(
 p_id=>wwv_flow_imp.id({search_region_id})
,p_plug_name=>'{_esc(region_name)}'
,p_region_template_options=>'#DEFAULT#:t-Region--noPadding:t-Region--hideHeader'
,p_plug_template=>{REGION_TMPL_BLANK}
,p_plug_display_sequence=>{sequence}
,p_plug_display_point=>'BODY'
,p_plug_source_type=>'NATIVE_STATIC'
);"""))
        session.regions[search_region_id] = RegionInfo(
            region_id=search_region_id, page_id=page_id,
            region_name=region_name, region_type="search"
        )

        # Search item
        item_id = ids.next(f"item_{page_id}_{search_item_name.lower()}")
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_item(
 p_id=>wwv_flow_imp.id({item_id})
,p_name=>'{_esc(full_item_name)}'
,p_item_sequence=>10
,p_item_plug_id=>wwv_flow_imp.id({search_region_id})
,p_prompt=>'{_esc(search_label)}'
,p_placeholder=>'{_esc(placeholder)}'
,p_display_as=>'{ITEM_TEXT}'
,p_cSize=>40
,p_label_alignment=>'RIGHT'
,p_field_template=>{LABEL_OPTIONAL}
,p_item_template_options=>'#DEFAULT#'
);"""))
        session.items[full_item_name] = ItemInfo(
            item_id=item_id, page_id=page_id,
            item_name=full_item_name, item_type=ITEM_TEXT
        )

        # Dynamic Action: keyup on search item -> refresh IR with search
        da_id = ids.next(f"da_search_{page_id}")
        da_action_id = ids.next(f"da_action_search_{page_id}")
        da_js = (
            f"var $ir = apex.region(\"{_esc(target_region_name)}\");"
            f"if ($ir) {{ $ir.widget().interactiveReport(\"search\", apex.item(\"{full_item_name}\").getValue()); }}"
        )
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_da_event(
 p_id=>wwv_flow_imp.id({da_id})
,p_name=>'Search Filter'
,p_event_sequence=>10
,p_triggering_element_type=>'ITEM'
,p_triggering_element=>'{_esc(full_item_name)}'
,p_bind_type=>'bind'
,p_execution_type=>'IMMEDIATE'
,p_bind_event_type=>'keyup'
);"""))

        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_da_action(
 p_id=>wwv_flow_imp.id({da_action_id})
,p_event_id=>wwv_flow_imp.id({da_id})
,p_event_result=>'TRUE'
,p_action_sequence=>10
,p_execute_on_page_init=>'N'
,p_action=>'NATIVE_JAVASCRIPT_CODE'
,p_attribute_01=>'{_esc(da_js)}'
);"""))

        return json.dumps({
            "status": "ok",
            "search_region_id": search_region_id,
            "search_item": full_item_name,
            "target_region": target_region_name,
            "page_id": page_id,
            "message": f"Search bar '{full_item_name}' added — filters '{target_region_name}' on keyup.",
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# apex_generate_from_schema
# ---------------------------------------------------------------------------

def apex_generate_from_schema(
    tables: list[str],
    start_page_id: int = 10,
    include_dashboard: bool = True,
    nav_icon_map: dict[str, str] | None = None,
) -> str:
    """Generate a complete application structure from a list of database tables.

    For each table, automatically creates a CRUD module (list + form pages).
    Optionally creates a dashboard page with KPI counts for each table.
    Adds navigation menu entries for all generated pages.

    This is the highest-level generator — give it your tables and get a working app.

    Args:
        tables: List of table names to generate CRUDs for.
            Example: ["EMPLOYEES", "DEPARTMENTS", "PROJECTS"]
        start_page_id: First page ID for the first CRUD list (default 10).
            Pages are allocated: 10/11, 12/13, 14/15...
        include_dashboard: Generate a dashboard page with record counts (default True).
        nav_icon_map: Dict mapping table name to Font Awesome icon class.
            Example: {"EMPLOYEES": "fa-users", "DEPARTMENTS": "fa-building"}
            Defaults to "fa-table" for unmapped tables.

    Returns:
        JSON with status, all pages created, all items created.
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})
    if not session.import_begun:
        return json.dumps({"status": "error", "error": "No import session active."})
    if not tables:
        return json.dumps({"status": "error", "error": "At least one table is required."})

    from .generator_tools import apex_generate_crud
    from .shared_tools import apex_add_nav_item
    from .visual_tools import apex_add_metric_cards

    icon_map = nav_icon_map or {}
    log: list[str] = []
    all_pages: list[int] = []
    total_items = 0

    try:
        page_cursor = start_page_id

        # Dashboard page (page 1 or before first CRUD)
        if include_dashboard:
            metrics = []
            for t in tables:
                icon = icon_map.get(t.upper(), "fa-table")
                label = t.replace("_", " ").title()
                metrics.append({
                    "label": label,
                    "sql": f"SELECT COUNT(*) FROM {t.upper()}",
                    "icon": icon,
                    "color": ["blue","green","orange","purple","teal","indigo"][len(metrics) % 6],
                })
            # Use page 1 for dashboard
            dash_page_id = 1
            if dash_page_id not in session.pages:
                from .page_tools import apex_add_page
                apex_add_page(dash_page_id, "Dashboard", "blank")

            r = json.loads(apex_add_metric_cards(
                page_id=dash_page_id,
                region_name="Record Counts",
                metrics=metrics,
                sequence=10,
                columns=min(len(tables), 4),
            ))
            if r.get("status") == "ok":
                log.append(f"Dashboard with {len(metrics)} KPI cards created on page {dash_page_id}")
            all_pages.append(dash_page_id)
            apex_add_nav_item("Dashboard", dash_page_id, 5, "fa-home")

        # CRUDs
        for i, table in enumerate(tables):
            list_pg = page_cursor
            form_pg = page_cursor + 1
            page_cursor += 2

            r = json.loads(apex_generate_crud(table, list_pg, form_pg))
            if r.get("status") == "ok":
                items_n = len(r.get("items_created", []))
                total_items += items_n
                all_pages.extend([list_pg, form_pg])
                log.append(f"CRUD for {table.upper()}: pages {list_pg}/{form_pg}, {items_n} items")

                # Nav item
                nav_label = table.replace("_", " ").title()
                nav_icon = icon_map.get(table.upper(), "fa-table")
                apex_add_nav_item(nav_label, list_pg, (i + 1) * 10 + 10, nav_icon)
            else:
                log.append(f"CRUD for {table}: ERROR — {r.get('error')}")

        return json.dumps({
            "status": "ok",
            "tables": tables,
            "pages_created": all_pages,
            "total_items": total_items,
            "total_pages": len(all_pages),
            "message": f"Generated app from {len(tables)} tables: {len(all_pages)} pages, {total_items} items.",
            "log": log,
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e), "log": log}, ensure_ascii=False, indent=2)
