"""Tools: apex_add_page_js, apex_add_global_js, apex_generate_ajax_handler."""
from __future__ import annotations
import json
from ..db import db
from ..ids import ids
from ..session import session
from ..config import WORKSPACE_ID
from ..templates import REGION_TMPL_BLANK, PROC_PLSQL
from ..utils import _json,  _esc, _blk


def _camel(name: str) -> str:
    """Convert ``UPPER_SNAKE_CASE`` to ``camelCase``.

    Example: ``SAVE_RECORD`` → ``saveRecord``.
    """
    parts = name.lower().split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def apex_add_page_js(
    page_id: int,
    javascript_code: str,
    js_file_urls: str = "",
) -> str:
    """Add inline JavaScript to a page (runs when the page loads).

    The JavaScript runs after the page DOM is ready, within the APEX context.
    Has access to apex, $, apex.item(), apex.region(), etc.

    Args:
        page_id: Target page ID.
        javascript_code: JavaScript code to add to the page. This code is placed
                         in a script block injected via a hidden static region.
                         Example:
                             function showConfirm(msg) {
                                 apex.confirm(msg, {title: 'Confirm'});
                             }

                             // Auto-initialize
                             apex.jQuery(document).ready(function() {
                                 initMyPage();
                             });
        js_file_urls: URLs of external JS files to load (newline separated).
                      Example: "#APP_FILES#mylib.js"

    Returns:
        JSON with status.

    Best practices:
        - Use apex.item('P1_ITEM').getValue() instead of $('#P1_ITEM').val()
        - Use apex.server.process() for AJAX calls to APEX processes
        - Use apex.message.showPageSuccess() for user feedback
        - Avoid global variables — use apex.namespace instead
        - For DA-triggered code, prefer Dynamic Actions over inline JS
        - Wrap initialization in apex.jQuery(document).ready() or use DAs

    APEX JavaScript API quick reference:
        apex.item('ITEM_NAME').getValue()            -- Get item value
        apex.item('ITEM_NAME').setValue('val')       -- Set item value
        apex.item('ITEM_NAME').show() / .hide()      -- Show/hide item
        apex.item('ITEM_NAME').enable() / .disable() -- Enable/disable
        apex.region('REGION_ID').refresh()           -- Refresh a region
        apex.server.process('CALLBACK_NAME', {       -- AJAX call to PL/SQL
            pageItems: '#P1_ITEM1,#P1_ITEM2',
            success: function(data) { ... }
        })
        apex.message.showPageSuccess('Saved!')       -- Success toast
        apex.message.showErrors([{message:'Error'}]) -- Show errors
    """
    if not db.is_connected():
        return _json({"status": "error", "error": "Not connected. Call apex_connect() first."})
    if not session.import_begun:
        return _json({"status": "error", "error": "No import session active. Call apex_create_app() first."})

    if page_id not in session.pages:
        return _json({
            "status": "error",
            "error": (
                f"Page {page_id} not found in current session. "
                "Call apex_add_page() first or check the page_id."
            ),
        })

    try:
        # Use NATIVE_PLSQL + sys.htp.p() to inject the <script> tag.
        # NATIVE_STATIC can render the tag as escaped text depending on the
        # region template's "Escape Special Characters" setting.
        #
        # Escaping strategy — two levels:
        #   Level 1: _esc(javascript_code)  → escapes ' → '' for the inner
        #            PL/SQL string literal (the sys.htp.p argument).
        #   Level 2: _esc(stored_plsql)     → escapes the whole PL/SQL block
        #            for embedding in the outer create_page_plug string literal.
        js_esc = _esc(javascript_code)  # level 1

        # Build the PL/SQL block that will be stored in p_plug_source.
        if js_file_urls.strip():
            file_lines = ""
            for url in js_file_urls.strip().splitlines():
                url = url.strip()
                if url:
                    file_lines += (
                        f"  sys.htp.p('<script src=\"{url}\""
                        f" type=\"text/javascript\"></script>');\n"
                    )
            stored_plsql = (
                f"begin\n"
                f"{file_lines}"
                f"  sys.htp.p('<script type=\"text/javascript\">\n{js_esc}\n</script>');\n"
                f"end;"
            )
        else:
            stored_plsql = (
                f"begin"
                f" sys.htp.p('<script type=\"text/javascript\">\n{js_esc}\n</script>');"
                f" end;"
            )

        region_id = ids.next(f"js_region_{page_id}_{ids.next()}")
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_plug(
 p_id=>wwv_flow_imp.id({region_id})
,p_plug_name=>'Page JavaScript'
,p_plug_template=>{REGION_TMPL_BLANK}
,p_plug_display_sequence=>9999
,p_plug_display_point=>'BODY'
,p_plug_source=>'{_esc(stored_plsql)}'
,p_plug_source_type=>'NATIVE_PLSQL'
,p_plug_query_options=>'DERIVED_REPORT_COLUMNS'
);"""))

        return _json({
            "status": "ok",
            "page_id": page_id,
            "region_id": region_id,
            "message": (
                f"JavaScript injected on page {page_id} via a hidden static region "
                f"(sequence 9999, display_point BODY). "
                f"The script tag will render at the bottom of the page body."
            ),
            "has_file_urls": bool(js_file_urls.strip()),
        })

    except Exception as e:
        return _json({"status": "error", "error": str(e)})


def apex_add_global_js(
    function_name: str,
    javascript_code: str,
    description: str = "",
) -> str:
    """Add a reusable JavaScript function to Shared Components (available on all pages).

    Args:
        function_name: Function name / identifier (e.g., "TEA_UTILS").
                       Used only as a label; the JS itself can define multiple functions.
        javascript_code: The full JavaScript code. Can be multiple functions.
                         Will be wrapped in an IIFE to avoid polluting global scope
                         unless the code already starts with '(' or 'var '/'let '/'const '.
        description: Description of what this JS does.

    Returns:
        JSON with:
        - status: "ok"
        - js_content: The prepared JavaScript content to upload
        - filename: Suggested filename (e.g., "tea-utils.js")
        - upload_instructions: Step-by-step guide for uploading to APEX Static Files
        - reference_url: URL substitution to reference the file in app properties

    Note:
        Due to APEX architecture, truly global JS (available on ALL pages) must be
        uploaded as an APEX Static File (Shared Components > Static Application Files)
        and referenced in App Properties > User Interface > JavaScript > File URLs as
        '#APP_FILES#filename.js'.

        This tool generates the JavaScript content and provides upload instructions.
        For page-specific JS, use apex_add_page_js() instead.
    """
    if not function_name or not function_name.strip():
        return _json({"status": "error", "error": "function_name is required."})
    if not javascript_code or not javascript_code.strip():
        return _json({"status": "error", "error": "javascript_code is required."})

    # Decide whether to wrap in an IIFE
    stripped = javascript_code.strip()
    already_iife = stripped.startswith("(function") or stripped.startswith("(()") or stripped.startswith(";(")
    already_module = stripped.startswith("var ") or stripped.startswith("let ") or stripped.startswith("const ")

    if not already_iife and not already_module:
        prepared_js = (
            f"/* {function_name}"
            + (f" — {description}" if description else "")
            + " */\n"
            + "(function() {\n"
            + "  'use strict';\n\n"
            + javascript_code
            + "\n})();"
        )
    else:
        header = f"/* {function_name}" + (f" — {description}" if description else "") + " */\n"
        prepared_js = header + javascript_code

    filename = function_name.lower().replace("_", "-") + ".js"

    upload_instructions = [
        "1. In APEX Builder, go to Shared Components > Files and Reports > Static Application Files.",
        f"2. Click 'Upload File' and upload a file named '{filename}' with the JavaScript content provided.",
        "3. Copy the 'Reference' path shown after upload (e.g., '#APP_FILES#" + filename + "').",
        "4. Go to App Properties > User Interface > Attributes > JavaScript > File URLs.",
        f"5. Add '#APP_FILES#{filename}' on a new line in File URLs.",
        "6. Save and run the application — the JS will be available on all pages.",
        "",
        "Alternative (quick method — global page only):",
        "  Use apex_add_page_js(page_id=0, javascript_code=...) to add JS to the Global Page (page 0).",
        "  This is slightly less efficient but avoids file upload.",
    ]

    return _json({
        "status": "ok",
        "function_name": function_name,
        "filename": filename,
        "description": description,
        "js_content": prepared_js,
        "upload_instructions": upload_instructions,
        "reference_url": f"#APP_FILES#{filename}",
        "note": (
            "This tool returns the JS content and upload instructions. "
            "Use apex_add_page_js(page_id=0, ...) for a quick alternative that injects "
            "JS on the Global Page (page 0) without requiring file upload."
        ),
    })


def apex_generate_ajax_handler(
    page_id: int,
    callback_name: str,
    plsql_code: str,
    input_items: list[str] | None = None,
    return_json: bool = True,
    auto_add_js: bool = True,
) -> str:
    """Generate an AJAX callback (PL/SQL process + JavaScript caller).

    Creates a server-side AJAX endpoint (PL/SQL process) and returns the
    JavaScript code to call it from the client side. By default, the generated
    JavaScript function is automatically added to the page via apex_add_page_js().

    Args:
        page_id: Page that owns this callback.
        callback_name: UPPERCASE name for the callback (e.g., "SAVE_RECORD", "SEARCH_DATA").
                       Called from JS as: apex.server.process('CALLBACK_NAME', {...})
        plsql_code: PL/SQL block that runs server-side.
                    Access page items via bind variables: :P10_ITEM_NAME
                    Return JSON via: apex_json.open_object; apex_json.write('key', val);
                                     apex_json.close_object;
                    Example:
                        DECLARE v_count NUMBER;
                        BEGIN
                          SELECT COUNT(*) INTO v_count
                            FROM my_table WHERE status = :P10_STATUS;
                          apex_json.open_object;
                          apex_json.write('count', v_count);
                          apex_json.write('status', 'success');
                          apex_json.close_object;
                        END;
        input_items: List of page item names to send to server
                     (e.g., ["P10_SEARCH", "P10_STATUS"]).
        return_json: Whether the callback returns JSON (default True).
        auto_add_js: Automatically add the generated JavaScript caller function to the page
                     via apex_add_page_js() (default True). When True, the function will be
                     available at runtime without any additional steps. Set to False if you
                     want to manually review and modify the JS before adding it to the page.

    Returns:
        JSON with:
        - status: ok/error
        - process_created: bool
        - callback_name: the callback name registered
        - javascript_caller: JavaScript code snippet to call this callback
        - usage_example: Complete example showing how to use it
        - js_auto_added: bool — whether the JS was automatically added to the page
        - js_add_error: error message if auto-add failed, None otherwise

    The generated JavaScript:
        function call{CamelCaseName}() {
            apex.server.process('{CALLBACK_NAME}', {
                pageItems: '#P10_ITEM1,#P10_ITEM2',
                success: function(data) {
                    console.log(data);
                    apex.message.showPageSuccess('Done!');
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    apex.message.showErrors([{message: errorThrown}]);
                }
            });
        }

    Best practices for AJAX in APEX:
        - Always use apex_json package for JSON responses (not manual concatenation)
        - Access page items via bind variables (:P10_ITEM), not direct SQL
        - Use PRAGMA AUTONOMOUS_TRANSACTION if you need to COMMIT in a callback
        - Add EXCEPTION handling: WHEN OTHERS THEN apex_json.open_object;
          apex_json.write('error', SQLERRM); apex_json.close_object;
        - Call apex_application.g_unrecoverable_error := TRUE; for fatal errors
    """
    if not db.is_connected():
        return _json({"status": "error", "error": "Not connected. Call apex_connect() first."})
    if not session.import_begun:
        return _json({"status": "error", "error": "No import session active. Call apex_create_app() first."})

    if page_id not in session.pages:
        return _json({
            "status": "error",
            "error": (
                f"Page {page_id} not found in current session. "
                "Call apex_add_page() first or check the page_id."
            ),
        })

    if not callback_name or not callback_name.strip():
        return _json({"status": "error", "error": "callback_name is required."})
    if not plsql_code or not plsql_code.strip():
        return _json({"status": "error", "error": "plsql_code is required."})

    upper_callback = callback_name.strip().upper()
    items = input_items or []

    # Wrap in begin...end if the PL/SQL does not already have a block wrapper
    stripped_plsql = plsql_code.strip()
    if not stripped_plsql.upper().startswith("BEGIN") and not stripped_plsql.upper().startswith("DECLARE"):
        full_plsql = f"BEGIN\n{stripped_plsql}\nEND;"
    else:
        full_plsql = stripped_plsql
        if not full_plsql.rstrip().endswith(";"):
            full_plsql += ";"

    # Add error wrapper if return_json and no exception block visible
    if return_json and "EXCEPTION" not in full_plsql.upper():
        # Inject a generic exception handler before the final END;
        full_plsql = full_plsql.rstrip().rstrip(";")
        full_plsql += (
            "\nEXCEPTION\n"
            "  WHEN OTHERS THEN\n"
            "    apex_json.open_object;\n"
            "    apex_json.write('status', 'error');\n"
            "    apex_json.write('error', SQLERRM);\n"
            "    apex_json.close_object;\n"
            "END;"
        )

    try:
        proc_id = ids.next(f"ajax_{page_id}_{upper_callback.lower()}")

        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_process(
 p_id=>wwv_flow_imp.id({proc_id})
,p_process_sequence=>10
,p_process_point=>'ON_DEMAND'
,p_process_type=>'NATIVE_PLSQL'
,p_process_name=>'{_esc(upper_callback)}'
,p_process_sql_clob=>'{_esc(full_plsql)}'
,p_error_display_location=>'INLINE_IN_NOTIFICATION'
);"""))

        # ── Generate the JavaScript caller ────────────────────────────────
        camel_name = _camel(upper_callback)
        js_func_name = f"call{camel_name[0].upper() + camel_name[1:]}"

        # Build pageItems string
        if items:
            page_items_selector = "#" + ",#".join(items)
            page_items_line = f"            pageItems: '{page_items_selector}',"
        else:
            page_items_selector = ""
            page_items_line = "            // No page items to send"

        if return_json:
            success_body = (
                "                // data is parsed JSON from apex_json response\n"
                "                console.log(data);\n"
                "                if (data.status === 'error') {\n"
                "                    apex.message.showErrors([{type: 'error', message: data.error}]);\n"
                "                } else {\n"
                "                    apex.message.showPageSuccess('Done!');\n"
                "                }"
            )
        else:
            success_body = (
                "                // Callback returned non-JSON (plain text)\n"
                "                console.log(data);\n"
                "                apex.message.showPageSuccess('Done!');"
            )

        javascript_caller = (
            f"function {js_func_name}() {{\n"
            f"    apex.server.process(\n"
            f"        '{upper_callback}',\n"
            f"        {{\n"
            f"{page_items_line}\n"
            f"        }},\n"
            f"        {{\n"
            f"            dataType: '{'json' if return_json else 'text'}',\n"
            f"            success: function(data) {{\n"
            f"{success_body}\n"
            f"            }},\n"
            f"            error: function(jqXHR, textStatus, errorThrown) {{\n"
            f"                apex.message.showErrors([{{type: 'error', message: errorThrown}}]);\n"
            f"            }}\n"
            f"        }}\n"
            f"    );\n"
            f"}}"
        )

        usage_example = (
            f"// Call from a Dynamic Action (Execute JavaScript Code):\n"
            f"{js_func_name}();\n\n"
            f"// Or call from a button click handler:\n"
            f"apex.jQuery('#MY_BUTTON').on('click', function() {{\n"
            f"    {js_func_name}();\n"
            f"}});"
        )

        # Auto-add the generated JS caller to the page if requested
        js_added = False
        js_add_error = None
        if auto_add_js:
            js_result_str = apex_add_page_js(page_id=page_id, javascript_code=javascript_caller)
            js_result = json.loads(js_result_str)
            js_added = js_result.get("status") == "ok"
            if not js_added:
                js_add_error = js_result.get("error")

        result = {
            "status": "ok",
            "page_id": page_id,
            "callback_name": upper_callback,
            "process_id": proc_id,
            "process_created": True,
            "javascript_caller": javascript_caller,
            "usage_example": usage_example,
            "js_auto_added": js_added,
            "js_add_error": js_add_error,
        }

        # Include manual tip only when JS was not auto-added
        if not js_added:
            result["tip"] = (
                f"Use apex_add_page_js(page_id={page_id}, javascript_code=...) "
                f"to add the generated function to the page so it is available at runtime."
            )

        return _json(result)

    except Exception as e:
        return _json({"status": "error", "error": str(e)})
