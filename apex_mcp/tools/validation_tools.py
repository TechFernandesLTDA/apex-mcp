"""Tools: apex_add_item_validation, apex_add_item_computation."""
from __future__ import annotations
import json
from ..db import db
from ..ids import ids
from ..session import session
from ..utils import _esc, _blk


def apex_add_item_validation(
    page_id: int,
    item_name: str,
    validation_name: str,
    validation_type: str = "not_null",
    validation_expression: str = "",
    error_message: str = "",
    sequence: int = 10,
    condition_item: str = "",
) -> str:
    """Add a validation rule to a page item.

    Creates a page-level validation that runs on submit before processing.

    Args:
        page_id: Page ID containing the item.
        item_name: The item to validate (e.g., "P10_NAME"). Auto-prefixed if needed.
        validation_name: Name for this validation (e.g., "Name Required").
        validation_type: Type of validation:
            - "not_null": Item must not be empty (default)
            - "max_length": Item must not exceed N chars (set N in validation_expression)
            - "min_length": Item must have at least N chars
            - "regex": Item must match regex pattern (set pattern in validation_expression)
            - "plsql_expression": PL/SQL expression that returns TRUE/FALSE
            - "plsql_function": PL/SQL function body that returns NULL (valid) or error message
            - "item_not_null_or_zero": Item must not be null or zero (for number fields)
        validation_expression: Expression for the validation type:
            - For max_length/min_length: the length as string (e.g., "100")
            - For regex: the regex pattern (e.g., "^[0-9]+$")
            - For plsql_expression: PL/SQL boolean expression (e.g., ":P10_AGE > 0 AND :P10_AGE < 120")
            - For plsql_function: PL/SQL function body returning NULL or error message
        error_message: Message shown when validation fails. Auto-generated if omitted.
        sequence: Validation execution order.
        condition_item: Only validate if this item is not null (optional).

    Returns:
        JSON with status, validation_id, validation_name.

    Best practices:
        - Add validations for all required fields
        - Use not_null for mandatory text fields
        - Use plsql_expression for cross-field validations
        - Keep error messages user-friendly and specific
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})
    if not session.import_begun:
        return json.dumps({"status": "error", "error": "No import session active. Call apex_create_app() first."})

    # Auto-prefix item name
    expected_prefix = f"P{page_id}_"
    if not item_name.upper().startswith(expected_prefix.upper()):
        item_name = f"{expected_prefix}{item_name}"

    # Map validation types to APEX native types (verified against APEX 24.2 exports)
    type_map = {
        "not_null":              "ITEM_NOT_NULL",
        "max_length":            "MAX_LENGTH",
        "min_length":            "MIN_LENGTH",
        "regex":                 "REGULAR_EXPRESSION",
        "plsql_expression":      "PLSQL_EXPRESSION",
        "plsql_function":        "PLSQL_FUNCTION_RETURNING_ERROR_TEXT",
        "item_not_null_or_zero": "ITEM_NOT_NULL_OR_ZERO",
    }
    apex_val_type = type_map.get(validation_type.lower(), "ITEM_NOT_NULL")

    # Auto error message
    if not error_message:
        item_label = item_name.split("_", 1)[-1].replace("_", " ").title()
        if validation_type == "not_null":
            error_message = f"{item_label} is required."
        elif validation_type == "max_length":
            error_message = f"{item_label} must not exceed {validation_expression} characters."
        elif validation_type == "min_length":
            error_message = f"{item_label} must have at least {validation_expression} characters."
        elif validation_type == "regex":
            error_message = f"{item_label} has an invalid format."
        else:
            error_message = f"{item_label} is invalid."

    try:
        val_id = ids.next(f"val_{page_id}_{_esc(validation_name)}")

        # Build p_validation line — for ITEM_NOT_NULL the item name is the expression;
        # for length/regex/plsql types the expression is the actual rule.
        if apex_val_type == "ITEM_NOT_NULL":
            expr_lines = f",p_validation=>'{_esc(item_name)}'"
        elif apex_val_type == "ITEM_NOT_NULL_OR_ZERO":
            expr_lines = f",p_validation=>'{_esc(item_name)}'"
        elif validation_expression:
            expr_lines = f",p_validation=>'{_esc(validation_expression)}'"
        else:
            expr_lines = ""

        # Condition line
        condition_line = ""
        if condition_item:
            condition_line = f",p_condition_type=>'ITEM_IS_NOT_NULL'\n,p_condition_expression1=>'{_esc(condition_item)}'"

        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_validation(
 p_id=>wwv_flow_imp.id({val_id})
,p_validation_name=>'{_esc(validation_name)}'
,p_validation_sequence=>{sequence}
,p_validation_type=>'{apex_val_type}'
{expr_lines}
,p_error_message=>'{_esc(error_message)}'
,p_error_display_location=>'INLINE_WITH_FIELD_AND_NOTIFICATION'
{condition_line}
);"""))

        return json.dumps({
            "status": "ok",
            "validation_id": val_id,
            "validation_name": validation_name,
            "validation_type": apex_val_type,
            "item_name": item_name,
            "page_id": page_id,
            "error_message": error_message,
            "message": f"Validation '{validation_name}' added to item '{item_name}' on page {page_id}.",
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)


def apex_add_item_computation(
    page_id: int,
    item_name: str,
    computation_type: str = "static_value",
    computation_expression: str = "",
    computation_point: str = "BEFORE_HEADER",
    sequence: int = 10,
    condition_item: str = "",
) -> str:
    """Add a computation to derive or pre-populate a page item value.

    Computations run at a specified point in the page lifecycle and set
    an item's value automatically (e.g., pre-populate from session, query, or expression).

    Args:
        page_id: Page ID.
        item_name: Item to compute (e.g., "P10_USER"). Auto-prefixed if needed.
        computation_type: How to compute the value:
            - "static_value": A literal string value
            - "plsql_expression": PL/SQL expression (e.g., ":APP_USER || '@company.com'")
            - "plsql_function": PL/SQL function body returning the value
            - "query": SQL query returning a single value (e.g., "SELECT name FROM users WHERE id = :P10_ID")
            - "item_value": Copy value from another item (set item name in computation_expression)
            - "sequence": Get next value from a DB sequence
        computation_expression: The expression/value/SQL for the computation type.
        computation_point: When to compute:
            - "BEFORE_HEADER": Before page renders (default) — good for initialization
            - "AFTER_SUBMIT": After form submit — good for post-processing
            - "BEFORE_BOX_BODY": Before page body renders
        sequence: Computation order (for multiple computations on same item).
        condition_item: Only compute if this item is not null (optional).

    Returns:
        JSON with status, computation_id, item_name.

    Best practices:
        - Use BEFORE_HEADER to pre-populate form fields when opening edit forms
        - Use query type to fetch values from DB based on other items
        - Use item_value to copy from app items (e.g., APP_USER, APP_ID)
        - Avoid heavy computations — keep SQL queries simple and indexed
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})
    if not session.import_begun:
        return json.dumps({"status": "error", "error": "No import session active. Call apex_create_app() first."})

    # Auto-prefix item name
    expected_prefix = f"P{page_id}_"
    if not item_name.upper().startswith(expected_prefix.upper()):
        item_name = f"{expected_prefix}{item_name}"

    # Map computation types to APEX native types
    type_map = {
        "static_value":     "STATIC_ASSIGNMENT",
        "plsql_expression": "PLSQL_EXPRESSION",
        "plsql_function":   "PLSQL_FUNCTION_BODY",
        "query":            "QUERY",
        "item_value":       "ITEM_VALUE",
        "sequence":         "SEQUENCE",
    }
    apex_comp_type = type_map.get(computation_type.lower(), "STATIC_ASSIGNMENT")

    # Map computation point
    point_map = {
        "before_header":   "BEFORE_HEADER",
        "after_submit":    "AFTER_SUBMIT",
        "before_box_body": "BEFORE_BOX_BODY",
    }
    apex_point = point_map.get(computation_point.lower(), "BEFORE_HEADER")

    try:
        comp_id = ids.next(f"comp_{page_id}_{_esc(item_name)}")

        condition_line = ""
        if condition_item:
            condition_line = f",p_condition_type=>'ITEM_IS_NOT_NULL'\n,p_condition_expression1=>'{_esc(condition_item)}'"

        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_computation(
 p_id=>wwv_flow_imp.id({comp_id})
,p_computation_sequence=>{sequence}
,p_computation_item=>'{_esc(item_name)}'
,p_computation_point=>'{apex_point}'
,p_computation_type=>'{apex_comp_type}'
,p_computation=>'{_esc(computation_expression)}'
{condition_line}
);"""))

        return json.dumps({
            "status": "ok",
            "computation_id": comp_id,
            "item_name": item_name,
            "computation_type": apex_comp_type,
            "computation_point": apex_point,
            "page_id": page_id,
            "message": f"Computation added to item '{item_name}' on page {page_id} (point: {apex_point}).",
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)
