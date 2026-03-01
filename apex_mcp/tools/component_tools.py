"""Tools: apex_add_region, apex_add_item, apex_add_button, apex_add_process, apex_add_dynamic_action."""
from __future__ import annotations
import json
from ..db import db
from ..ids import ids
from ..session import session, RegionInfo, ItemInfo
from ..templates import (
    REGION_TMPL_STANDARD,
    REGION_TMPL_IR,
    REGION_TMPL_BLANK,
    BTN_TMPL_TEXT,
    BTN_TMPL_ICON,
    LABEL_OPTIONAL,
    LABEL_REQUIRED,
    ITEM_TEXT,
    ITEM_NUMBER,
    ITEM_DATE,
    ITEM_SELECT,
    ITEM_HIDDEN,
    ITEM_TEXTAREA,
    ITEM_YES_NO,
    ITEM_PASSWORD,
    ITEM_DISPLAY,
    ITEM_CHECKBOX,
    ITEM_RADIO,
    REGION_IR,
    REGION_FORM,
    REGION_STATIC,
    REGION_PLSQL,
    REGION_CHART,
    BTN_ACTION_SUBMIT,
    BTN_ACTION_REDIRECT,
    BTN_ACTION_DEFINED,
    PROC_DML,
    PROC_PLSQL,
)
from ..utils import _esc, _blk, _sql_to_varchar2


def _find_region_id(page_id: int, region_name: str) -> int | None:
    """Look up a region ID by page and name from session state."""
    for reg in session.regions.values():
        if reg.page_id == page_id and reg.region_name == region_name:
            return reg.region_id
    return None


def _ensure_item_prefix(item_name: str, page_id: int) -> str:
    """Ensure item name starts with P{page_id}_ prefix."""
    expected_prefix = f"P{page_id}_"
    if not item_name.upper().startswith(expected_prefix.upper()):
        return f"{expected_prefix}{item_name}"
    return item_name


def apex_add_region(
    page_id: int,
    region_name: str,
    region_type: str = "static",
    sequence: int = 10,
    source_sql: str = "",
    static_content: str = "",
    template: str | None = None,
    grid_column: str = "BODY",
    attributes: dict | None = None,
) -> str:
    """Add a region to a page.

    Args:
        page_id: Page to add the region to.
        region_name: Display name of the region.
        region_type: Type of region:
            - "static": Static HTML content (use static_content param)
            - "ir": Interactive Report (use source_sql param) — best for data grids
            - "form": Form container (add items with apex_add_item after)
            - "chart": JET Chart
            - "plsql": PL/SQL Dynamic Content
        sequence: Display sequence (10, 20, 30...).
        source_sql: SQL query for ir/chart regions (e.g., "SELECT * FROM my_table").
        static_content: HTML for static regions.
        template: Override region template name. Uses type default if omitted.
        grid_column: Page layout position: "BODY", "BREADCRUMB_BAR", "AFTER_HEADER",
                     "BEFORE_FOOTER", "AFTER_FOOTER".
        attributes: Extra template options dict.

    Best practices:
        - IR regions: always provide source_sql with proper WHERE clauses
        - Form regions: create the region first, then add items with apex_add_item
        - Use sequence increments of 10 to allow future insertions
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})
    if not session.import_begun:
        return json.dumps({"status": "error", "error": "No import session active. Call apex_create_app() first."})

    try:
        region_type_lower = region_type.lower()

        # Map region type to APEX native type and default template
        type_map = {
            "static":  (REGION_STATIC, REGION_TMPL_STANDARD),
            "ir":      (REGION_IR,     REGION_TMPL_IR),
            "form":    (REGION_FORM,   REGION_TMPL_STANDARD),
            "chart":   (REGION_CHART,  REGION_TMPL_STANDARD),
            "plsql":   (REGION_PLSQL,  REGION_TMPL_STANDARD),
        }
        apex_region_type, default_tmpl = type_map.get(region_type_lower, (REGION_STATIC, REGION_TMPL_STANDARD))

        # Allow explicit template override (numeric ID)
        tmpl_id = default_tmpl
        if template:
            try:
                tmpl_id = int(template)
            except ValueError:
                pass  # keep computed default

        region_id = ids.next(f"region_{page_id}_{_esc(region_name)}")

        # Build source attribute lines
        source_line = ""
        if region_type_lower == "static" and static_content:
            source_line = f",p_plug_source=>'{_esc(static_content)}'"
        elif region_type_lower in ("ir", "plsql", "chart") and source_sql:
            source_line = f",p_plug_source=>'{_esc(source_sql)}'"

        # Template options
        tmpl_options = "#DEFAULT#"
        if attributes:
            extra = " ".join(f":{k}:{v}" for k, v in attributes.items())
            tmpl_options = f"#DEFAULT#{extra}"

        plug_tmpl_line = f",p_plug_template=>{tmpl_id}" if tmpl_id else ""

        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_plug(
 p_id=>wwv_flow_imp.id({region_id})
,p_plug_name=>'{_esc(region_name)}'
,p_region_template_options=>'{tmpl_options}'
{plug_tmpl_line}
,p_plug_display_sequence=>{sequence}
,p_plug_display_point=>'{grid_column}'
,p_plug_source_type=>'{apex_region_type}'
{source_line}
);"""))

        # For Interactive Report regions, create the worksheet definition
        if region_type_lower == "ir" and source_sql:
            ws_id = ids.next(f"worksheet_{page_id}_{region_id}")
            db.plsql(_blk(f"""
wwv_flow_imp_page.create_worksheet(
 p_id=>wwv_flow_imp.id({ws_id})
,p_max_row_count_message=>'The maximum row count for this report is #MAX_ROW_COUNT# rows.  Please apply a filter to reduce the number of records in your query.'
,p_no_data_found_message=>'No data found.'
,p_pagination_type=>'ROWS_X_TO_Y'
,p_pagination_display_pos=>'BOTTOM_RIGHT'
,p_report_list_mode=>'TABS'
,p_lazy_loading=>false
,p_show_detail_link=>'N'
,p_show_notify=>'Y'
,p_download_formats=>'CSV:HTML:XLSX'
,p_enable_mail_download=>'Y'
,p_internal_uid=>{ws_id}
);"""))

        # Update session state
        session.regions[region_id] = RegionInfo(
            region_id=region_id,
            page_id=page_id,
            region_name=region_name,
            region_type=region_type_lower,
        )

        return json.dumps({
            "status": "ok",
            "region_id": region_id,
            "page_id": page_id,
            "region_name": region_name,
            "region_type": region_type_lower,
            "sequence": sequence,
            "message": f"Region '{region_name}' added to page {page_id}.",
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)


def apex_add_item(
    page_id: int,
    region_name: str,
    item_name: str,
    item_type: str = "text",
    label: str = "",
    sequence: int = 10,
    source_column: str = "",
    lov_name: str = "",
    is_required: bool = False,
    placeholder: str = "",
    default_value: str = "",
    read_only: bool = False,
    colspan: int = 1,
) -> str:
    """Add a form item (input field) to a region.

    Args:
        page_id: Page ID.
        region_name: Name of the parent region (must exist, created with apex_add_region).
        item_name: Item name following APEX convention P{PAGE}_{NAME} (e.g., P10_FIRST_NAME).
                   Will be auto-prefixed with P{page_id}_ if not already prefixed.
        item_type: Input type:
            - "text": Text input (default)
            - "number": Numeric input with validation
            - "date": Date picker (JET)
            - "select": Select list (requires lov_name)
            - "hidden": Hidden field (no label shown)
            - "textarea": Multi-line text
            - "yes_no": Yes/No switch
            - "password": Password field (masked)
            - "display": Display-only (non-editable)
            - "checkbox": Checkbox group
            - "radio": Radio button group
        label: Display label. Auto-generated from item_name if omitted.
        sequence: Display order within the region.
        source_column: Database column to bind (for form DML, e.g., "FIRST_NAME").
        lov_name: Name of LOV for select/radio/checkbox items.
        is_required: Show required indicator and add NOT NULL validation.
        placeholder: Placeholder text for text inputs.
        default_value: Default item value (can be &SUBSTITUTION.).
        read_only: Make item read-only (display value, not editable).
        colspan: Number of grid columns to span (1-12).

    Best practices:
        - Always prefix item names with P{page_id}_ (auto-applied if missing)
        - Hidden PKs should be type "hidden" with source_column = primary key column
        - Required fields should have is_required=True for proper UX
        - Use source_column to auto-populate from DB when page loads
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})
    if not session.import_begun:
        return json.dumps({"status": "error", "error": "No import session active. Call apex_create_app() first."})

    # Ensure correct item name prefix
    item_name = _ensure_item_prefix(item_name, page_id)

    # Find the parent region
    region_id = _find_region_id(page_id, region_name)
    if region_id is None:
        return json.dumps({
            "status": "error",
            "error": f"Region '{region_name}' not found on page {page_id}. Create it first with apex_add_region().",
        })

    try:
        item_type_lower = item_type.lower()

        # Map friendly type to APEX native type
        item_type_map = {
            "text":     ITEM_TEXT,
            "number":   ITEM_NUMBER,
            "date":     ITEM_DATE,
            "select":   ITEM_SELECT,
            "hidden":   ITEM_HIDDEN,
            "textarea": ITEM_TEXTAREA,
            "yes_no":   ITEM_YES_NO,
            "password": ITEM_PASSWORD,
            "display":  ITEM_DISPLAY,
            "checkbox": ITEM_CHECKBOX,
            "radio":    ITEM_RADIO,
        }
        apex_item_type = item_type_map.get(item_type_lower, ITEM_TEXT)

        # Auto-generate label from item name if not provided
        if not label:
            # Strip P{n}_ prefix and replace underscores with spaces, title-case
            raw = item_name.split("_", 1)[-1] if "_" in item_name else item_name
            label = raw.replace("_", " ").title()

        label_tmpl = LABEL_REQUIRED if is_required else LABEL_OPTIONAL

        item_id = ids.next(f"item_{page_id}_{item_name}")

        # Build optional parameter lines
        lov_line = f",p_lov=>'{_esc(lov_name)}'" if lov_name else ""
        source_line = (
            f",p_source=>'{_esc(source_column)}'\n,p_source_type=>'DB_COLUMN'"
            if source_column else ""
        )
        placeholder_line = f",p_placeholder=>'{_esc(placeholder)}'" if placeholder else ""
        default_line = f",p_item_default=>'{_esc(default_value)}'" if default_value else ""
        readonly_line = ",p_read_only_when_type=>'ALWAYS'" if read_only else ""
        colspan_line = f",p_grid_column_span=>{colspan}" if colspan and colspan != 1 else ""

        # Date picker requires plugin attributes (APEX 24.2)
        attrs_line = ""
        if item_type_lower == "date":
            attrs_line = (
                ",p_attributes=>wwv_flow_t_plugin_attributes(wwv_flow_t_varchar2("
                "'display_as','POPUP','max_date','NONE','min_date','NONE',"
                "'multiple_months','N','show_time','N','use_defaults','Y')).to_clob"
            )

        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_item(
 p_id=>wwv_flow_imp.id({item_id})
,p_name=>'{item_name}'
,p_item_sequence=>{sequence}
,p_item_plug_id=>wwv_flow_imp.id({region_id})
,p_prompt=>'{_esc(label)}'
,p_display_as=>'{apex_item_type}'
,p_label_alignment=>'RIGHT'
,p_field_template=>{label_tmpl}
,p_item_template_options=>'#DEFAULT#'
{lov_line}
{source_line}
{placeholder_line}
{default_line}
{readonly_line}
{colspan_line}
{attrs_line}
);"""))

        # Update session state
        session.items[item_name] = ItemInfo(
            item_id=item_id,
            page_id=page_id,
            item_name=item_name,
            item_type=item_type_lower,
        )

        return json.dumps({
            "status": "ok",
            "item_id": item_id,
            "item_name": item_name,
            "item_type": item_type_lower,
            "page_id": page_id,
            "region_name": region_name,
            "label": label,
            "sequence": sequence,
            "message": f"Item '{item_name}' added to region '{region_name}' on page {page_id}.",
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)


def apex_add_button(
    page_id: int,
    region_name: str,
    button_name: str,
    label: str,
    action: str = "submit",
    sequence: int = 10,
    position: str = "BELOW_BOX",
    hot: bool = False,
    icon: str = "",
    url: str = "",
    condition_type: str = "",
    condition_expr: str = "",
) -> str:
    """Add a button to a region.

    Args:
        page_id: Page ID.
        region_name: Parent region name.
        button_name: Internal button name (e.g., SAVE, CANCEL, DELETE).
        label: Button label text shown to user.
        action: Button action:
            - "submit": Submit the page (default) — triggers page processing
            - "redirect": Navigate to a URL (use url param)
            - "da": Defined by Dynamic Action (no built-in action)
        sequence: Display order.
        position: Button position relative to region:
            - "BELOW_BOX": Below the region content (default)
            - "ABOVE_BOX": Above the region content
            - "RIGHT_OF_TITLE": In the region title bar
        hot: Mark as primary action button (filled style). Use for Save/Submit.
        icon: Font APEX icon class (e.g., "fa-save", "fa-trash-o").
        url: Redirect URL for action="redirect" (e.g., "f?p=&APP_ID.:10:&SESSION.").
        condition_type: Condition to show/hide button:
            - "": Always shown (default)
            - "ITEM_IS_NOT_NULL": Show when item is not null
            - "ITEM_IS_NULL": Show when item is null
        condition_expr: Item name or expression for condition.

    Best practices:
        - Save button: hot=True, action="submit", position="BELOW_BOX"
        - Cancel button: action="redirect", url points back to IR page
        - Delete button: condition to show only when editing existing record (PK not null)
        - Use consistent button ordering: Save (seq 10), Cancel (seq 20), Delete (seq 30)
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})
    if not session.import_begun:
        return json.dumps({"status": "error", "error": "No import session active. Call apex_create_app() first."})

    region_id = _find_region_id(page_id, region_name)
    if region_id is None:
        return json.dumps({
            "status": "error",
            "error": f"Region '{region_name}' not found on page {page_id}. Create it first with apex_add_region().",
        })

    try:
        action_lower = action.lower()
        action_map = {
            "submit":   BTN_ACTION_SUBMIT,
            "redirect": BTN_ACTION_REDIRECT,
            "da":       BTN_ACTION_DEFINED,
        }
        apex_action = action_map.get(action_lower, BTN_ACTION_SUBMIT)

        # Choose template
        btn_tmpl = BTN_TMPL_ICON if icon else BTN_TMPL_TEXT

        # Hot (primary) button gets filled style
        btn_options = "#DEFAULT#:t-Button--hot" if hot else "#DEFAULT#"

        button_id = ids.next(f"btn_{page_id}_{button_name}")

        # Redirect target line
        redirect_line = ""
        if action_lower == "redirect" and url:
            redirect_line = f",p_button_redirect_url=>'{_esc(url)}'"

        # Icon line
        icon_line = f",p_icon_css_classes=>'{_esc(icon)}'" if icon else ""

        # Condition lines
        condition_lines = ""
        if condition_type:
            condition_lines = f",p_condition_type=>'{_esc(condition_type)}'"
            if condition_expr:
                condition_lines += f"\n,p_condition_expression1=>'{_esc(condition_expr)}'"

        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_button(
 p_id=>wwv_flow_imp.id({button_id})
,p_button_sequence=>{sequence}
,p_button_plug_id=>wwv_flow_imp.id({region_id})
,p_button_name=>'{_esc(button_name.upper())}'
,p_button_action=>'{apex_action}'
,p_button_template_options=>'{btn_options}'
,p_button_template_id=>{btn_tmpl}
,p_button_is_hot=>'{("Y" if hot else "N")}'
,p_button_image_alt=>'{_esc(label)}'
,p_button_position=>'{position}'
{redirect_line}
{icon_line}
{condition_lines}
);"""))

        # Track button ID for condition lookup in processes
        session.buttons[f"{page_id}:{button_name.upper()}"] = button_id

        return json.dumps({
            "status": "ok",
            "button_id": button_id,
            "button_name": button_name.upper(),
            "label": label,
            "action": apex_action,
            "page_id": page_id,
            "region_name": region_name,
            "hot": hot,
            "message": f"Button '{button_name}' added to region '{region_name}' on page {page_id}.",
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)


def apex_add_process(
    page_id: int,
    process_name: str,
    process_type: str = "dml",
    sequence: int = 10,
    source: str = "",
    table_name: str = "",
    return_pk_item: str = "",
    condition_button: str = "",
    success_message: str = "",
    error_message: str = "",
    point: str = "AFTER_SUBMIT",
) -> str:
    """Add a page process (server-side action triggered on submit or AJAX).

    Args:
        page_id: Page ID.
        process_name: Process display name.
        process_type: Type of process:
            - "dml": Automatic DML (INSERT/UPDATE/DELETE based on form items and table).
                     Requires table_name. Auto-handles PK detection.
            - "plsql": Custom PL/SQL block (use source param).
            - "ajax": AJAX Callback (accessible via apex.server.process()).
                      Use for auto-save, search, etc.
            - "close_dialog": Close modal dialog.
            - "clear_cache": Clear page cache.
        sequence: Execution order.
        source: PL/SQL source for plsql/ajax types.
        table_name: Table name for dml type (e.g., "MY_TABLE").
        return_pk_item: Page item to store the returned primary key (for INSERT).
        condition_button: Button name that triggers this process (e.g., "SAVE").
                          Empty = runs on any submit.
        success_message: Message shown on success.
        error_message: Custom error message on failure.
        point: When to execute:
            - "AFTER_SUBMIT": After page submission (default)
            - "BEFORE_HEADER": Before page header renders
            - "ON_SUBMIT_BEFORE_COMPUTATION": Very early in submit

    Best practices:
        - DML processes: always specify table_name and condition_button
        - PL/SQL processes: wrap in proper error handling
        - AJAX callbacks: name in UPPERCASE (convention for apex.server.process())
        - Use success_message to confirm actions to users
        - Set condition_button to avoid running process on wrong button clicks
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})
    if not session.import_begun:
        return json.dumps({"status": "error", "error": "No import session active. Call apex_create_app() first."})

    try:
        process_type_lower = process_type.lower()

        # Map friendly type to APEX native process type
        type_map = {
            "dml":          PROC_DML,
            "plsql":        PROC_PLSQL,
            "ajax":         PROC_PLSQL,          # AJAX callbacks are PL/SQL with a specific point
            "close_dialog": "NATIVE_CLOSE_WINDOW",
            "clear_cache":  "NATIVE_CLEAR_CACHE",
        }
        apex_proc_type = type_map.get(process_type_lower, PROC_PLSQL)

        # AJAX callbacks run at a specific process point
        exec_point = point
        if process_type_lower == "ajax":
            exec_point = "ON_DEMAND"

        process_id = ids.next(f"proc_{page_id}_{_esc(process_name)}")

        # Build type-specific attribute lines
        attr_lines = ""
        if process_type_lower == "dml" and table_name:
            attr_lines = (
                f",p_attribute_01=>'NOT_IDENTIFIED_BY_PRIMARY_KEY'"
                f"\n,p_attribute_04=>'{_esc(table_name.upper())}'"
            )
            if return_pk_item:
                pk_item = _ensure_item_prefix(return_pk_item, page_id)
                attr_lines += f"\n,p_attribute_05=>'{_esc(pk_item)}'"
        elif process_type_lower in ("plsql", "ajax") and source:
            attr_lines = (
                f",p_process_sql_clob=>{_sql_to_varchar2(source)}"
                f"\n,p_process_clob_language=>'PLSQL'"
            )

        # Condition (button trigger) — needs numeric button ID via wwv_flow_imp.id()
        condition_lines = ""
        if condition_button:
            btn_key = f"{page_id}:{condition_button.upper()}"
            btn_id = session.buttons.get(btn_key)
            if btn_id:
                condition_lines = f",p_process_when_button_id=>wwv_flow_imp.id({btn_id})"
            # If button ID not found, skip condition (process runs on any submit)

        # Success / error messages
        success_line = f",p_process_success_message=>'{_esc(success_message)}'" if success_message else ""
        error_line = f",p_error_display_location=>'INLINE_IN_NOTIFICATION'" if error_message else ""

        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_process(
 p_id=>wwv_flow_imp.id({process_id})
,p_process_sequence=>{sequence}
,p_process_point=>'{exec_point}'
,p_process_type=>'{apex_proc_type}'
,p_process_name=>'{_esc(process_name)}'
{attr_lines}
{condition_lines}
{success_line}
{error_line}
);"""))

        # Track in session
        session.app_processes.append(process_name)

        return json.dumps({
            "status": "ok",
            "process_id": process_id,
            "process_name": process_name,
            "process_type": apex_proc_type,
            "exec_point": exec_point,
            "page_id": page_id,
            "condition_button": condition_button or None,
            "message": f"Process '{process_name}' added to page {page_id}.",
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)


def apex_add_dynamic_action(
    page_id: int,
    da_name: str,
    event: str = "click",
    trigger_element: str = "",
    action_type: str = "execute_javascript",
    javascript_code: str = "",
    plsql_code: str = "",
    affected_element: str = "",
    sequence: int = 10,
    fire_on_init: bool = False,
    false_action_type: str = "",
    false_javascript_code: str = "",
    false_affected_element: str = "",
) -> str:
    """Add a Dynamic Action (client-side event handler) to a page.

    Args:
        page_id: Page ID.
        da_name: Dynamic Action name.
        event: Triggering event:
            - "click": Button/element click (default)
            - "change": Item value change
            - "page-load": On page load (DOMReady)
            - "keydown": Key pressed
            - "custom": Custom jQuery event
        trigger_element: Item name, button name, or jQuery selector that triggers the DA.
                         Leave empty for page-level events (page-load).
        action_type: What the DA does (TRUE branch):
            - "execute_javascript": Run JavaScript code (use javascript_code param)
            - "submit_page": Submit the page
            - "set_value": Set an item value
            - "show": Show element
            - "hide": Hide element
            - "enable": Enable item
            - "disable": Disable item
            - "refresh": Refresh a region
            - "plsql": Execute PL/SQL (use plsql_code param) — runs via AJAX
        javascript_code: JavaScript to execute (TRUE branch). Has access to apex.item(), apex.server.process().
        plsql_code: PL/SQL for action_type="plsql" (TRUE branch).
        affected_element: Item or region name affected by the action (TRUE branch).
        sequence: Order of execution.
        fire_on_init: Also fire when page first loads.
        false_action_type: Action type for the FALSE branch (same values as action_type).
                           When provided, a FALSE branch action is created alongside the TRUE branch.
                           Example: use action_type="show" and false_action_type="hide" for
                           conditional show/hide based on a condition expression.
        false_javascript_code: JavaScript code for the FALSE branch
                               (used when false_action_type="execute_javascript").
        false_affected_element: Item or region name affected by the FALSE branch action.

    Best practices:
        - Use page-load DAs to initialize page state (show/hide based on conditions)
        - Use change DAs on select lists to cascade filters
        - Keep JavaScript minimal — prefer apex.item() and apex.server.process()
        - AJAX DAs with plsql should reference named APEX items via :ITEM_NAME bind vars
        - For conditional show/hide: set action_type="show", false_action_type="hide",
          and use the same affected_element / false_affected_element for symmetric behavior.
          Example: show P10_DETAIL when P10_TYPE = 'DETAIL', hide it otherwise.
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})
    if not session.import_begun:
        return json.dumps({"status": "error", "error": "No import session active. Call apex_create_app() first."})

    try:
        event_lower = event.lower()
        action_lower = action_type.lower()

        # Map friendly event name to APEX event
        event_map = {
            "click":     "click",
            "change":    "change",
            "page-load": "ready",
            "keydown":   "keydown",
            "custom":    "custom",
        }
        apex_event = event_map.get(event_lower, event_lower)

        # Map friendly action to APEX native action type
        action_map = {
            "execute_javascript": "NATIVE_JAVASCRIPT_CODE",
            "submit_page":        "NATIVE_SUBMIT_PAGE",
            "set_value":          "NATIVE_SET_VALUE",
            "show":               "NATIVE_SHOW",
            "hide":               "NATIVE_HIDE",
            "enable":             "NATIVE_ENABLE",
            "disable":            "NATIVE_DISABLE",
            "refresh":            "NATIVE_REFRESH",
            "plsql":              "NATIVE_PLSQL",
        }
        apex_action_type = action_map.get(action_lower, "NATIVE_JAVASCRIPT_CODE")

        da_id    = ids.next(f"da_{page_id}_{_esc(da_name)}")
        da_ev_id = ids.next(f"da_ev_{page_id}_{_esc(da_name)}")
        da_act_id = ids.next(f"da_act_{page_id}_{_esc(da_name)}")

        # Trigger element lines (verified against APEX 24.2 exports)
        trigger_lines = ""
        if trigger_element:
            # Item names look like P\d+_... ; everything else treated as jQuery selector
            if trigger_element.upper().startswith("P") and "_" in trigger_element:
                trigger_lines = (
                    f",p_triggering_element_type=>'ITEM'"
                    f"\n,p_triggering_element=>'{_esc(trigger_element)}'"
                )
            else:
                trigger_lines = (
                    f",p_triggering_element_type=>'JQUERY_SELECTOR'"
                    f"\n,p_triggering_element=>'{_esc(trigger_element)}'"
                )
        else:
            # Page-level event — no triggering element needed
            trigger_lines = ""

        # Create the DA event (no p_fire_on_initialization or p_display_when_type — invalid in 24.2)
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_da_event(
 p_id=>wwv_flow_imp.id({da_id})
,p_name=>'{_esc(da_name)}'
,p_event_sequence=>{sequence}
{trigger_lines}
,p_bind_type=>'bind'
,p_execution_type=>'IMMEDIATE'
,p_bind_event_type=>'{apex_event}'
);"""))

        # JS sanitization — warn about unsafe patterns in development context
        js_warnings = []
        if javascript_code:
            if "eval(" in javascript_code:
                js_warnings.append(
                    "Warning: eval() detected in JavaScript code. Consider using safer alternatives."
                )
            if "document.write(" in javascript_code:
                js_warnings.append(
                    "Warning: document.write() detected. Use DOM manipulation APIs instead."
                )

        # Build action attribute lines based on action type
        action_attr_lines = ""
        if action_lower == "execute_javascript" and javascript_code:
            action_attr_lines = f",p_attribute_01=>'{_esc(javascript_code)}'"
        elif action_lower == "plsql" and plsql_code:
            action_attr_lines = f",p_attribute_01=>'{_esc(plsql_code)}'"

        # Affected element line
        affected_lines = ""
        if affected_element:
            if affected_element.upper().startswith("P") and "_" in affected_element:
                affected_lines = (
                    f",p_affected_elements_type=>'ITEM'"
                    f"\n,p_affected_elements=>'{_esc(affected_element)}'"
                )
            else:
                affected_lines = (
                    f",p_affected_elements_type=>'REGION'"
                    f"\n,p_affected_region_id=>'{_esc(affected_element)}'"
                )

        # Create the DA action (TRUE branch)
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_da_action(
 p_id=>wwv_flow_imp.id({da_act_id})
,p_event_id=>wwv_flow_imp.id({da_id})
,p_event_result=>'TRUE'
,p_action_sequence=>{sequence}
,p_execute_on_page_init=>'{("Y" if fire_on_init else "N")}'
,p_action=>'{apex_action_type}'
{action_attr_lines}
{affected_lines}
);"""))

        # Create the DA action (FALSE branch) — only when false_action_type is provided
        if false_action_type:
            false_action_lower = false_action_type.lower()
            false_apex_action = action_map.get(false_action_lower, "NATIVE_JAVASCRIPT_CODE")
            da_false_act_id = ids.next(f"da_false_act_{page_id}_{_esc(da_name)}")

            false_action_attr_lines = ""
            if false_action_lower == "execute_javascript" and false_javascript_code:
                false_action_attr_lines = f",p_attribute_01=>'{_esc(false_javascript_code)}'"

            false_affected_lines = ""
            if false_affected_element:
                if false_affected_element.upper().startswith("P") and "_" in false_affected_element:
                    false_affected_lines = (
                        f",p_affected_elements_type=>'ITEM'"
                        f"\n,p_affected_elements=>'{_esc(false_affected_element)}'"
                    )
                else:
                    false_affected_lines = (
                        f",p_affected_elements_type=>'REGION'"
                        f"\n,p_affected_region_id=>'{_esc(false_affected_element)}'"
                    )

            db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_da_action(
 p_id=>wwv_flow_imp.id({da_false_act_id})
,p_event_id=>wwv_flow_imp.id({da_id})
,p_event_result=>'FALSE'
,p_action_sequence=>{sequence}
,p_execute_on_page_init=>'{("Y" if fire_on_init else "N")}'
,p_action=>'{false_apex_action}'
{false_action_attr_lines}
{false_affected_lines}
);"""))

        return json.dumps({
            "status": "ok",
            "da_id": da_id,
            "da_name": da_name,
            "event": apex_event,
            "action_type": apex_action_type,
            "page_id": page_id,
            "trigger_element": trigger_element or None,
            "affected_element": affected_element or None,
            "fire_on_init": fire_on_init,
            "has_false_branch": bool(false_action_type),
            "warnings": js_warnings,
            "message": f"Dynamic Action '{da_name}' added to page {page_id}.",
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)
