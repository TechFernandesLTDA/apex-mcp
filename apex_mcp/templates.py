"""Universal Theme 42 template IDs for Oracle APEX 24.2.

The hardcoded IDs below are the defaults for APEX 24.2.13 / Universal Theme 42.
Call `discover_template_ids()` after connecting to refresh them from the live database.
This is recommended when running against a different APEX version or workspace.
"""
from __future__ import annotations
import logging

_log = logging.getLogger("apex_mcp.templates")


def discover_template_ids(db=None) -> dict:
    """Discover actual template IDs from the connected APEX workspace.

    Queries APEX data dictionary views to find the real template IDs for this
    workspace and APEX version. Updates module-level constants as a side-effect.

    Args:
        db: ConnectionManager instance. If None, imports from ..db.

    Returns:
        dict with discovered IDs (keys match module constant names).
        Falls back to hardcoded defaults for any template not found.

    Usage:
        from apex_mcp.db import db
        apex_connect()
        from apex_mcp import templates
        templates.discover_template_ids(db)
    """
    global PAGE_TMPL_STANDARD, PAGE_TMPL_LOGIN, PAGE_TMPL_DIALOG
    global REGION_TMPL_STANDARD, REGION_TMPL_IR, REGION_TMPL_BLANK, REGION_TMPL_BUTTONS, REGION_TMPL_CARDS, REGION_TMPL_LOGIN
    global BTN_TMPL_TEXT, BTN_TMPL_ICON
    global LABEL_OPTIONAL, LABEL_REQUIRED
    global LIST_TMPL_SIDE_NAV, LIST_TMPL_TOP_NAV, LIST_TMPL_NAVBAR
    global THEME_STYLE_ID

    if db is None:
        try:
            from .db import db as _db
            db = _db
        except Exception:
            return {}

    if not db.is_connected():
        return {}

    discovered: dict = {}

    try:
        # Page templates
        rows = db.execute("""
            SELECT template_name, template_id
              FROM apex_application_templates
             WHERE theme_number = 42
               AND template_type = 'PAGE'
               AND template_name IN ('Standard', 'Login', 'Modal Dialog')
        """)
        for r in rows:
            name = r.get("TEMPLATE_NAME", "")
            tid = r.get("TEMPLATE_ID")
            if tid and "Standard" in name:
                PAGE_TMPL_STANDARD = tid
                discovered["PAGE_TMPL_STANDARD"] = tid
            elif tid and "Login" in name:
                PAGE_TMPL_LOGIN = tid
                discovered["PAGE_TMPL_LOGIN"] = tid
            elif tid and "Dialog" in name:
                PAGE_TMPL_DIALOG = tid
                discovered["PAGE_TMPL_DIALOG"] = tid

        # Region templates
        rows = db.execute("""
            SELECT template_name, template_id
              FROM apex_application_templates
             WHERE theme_number = 42
               AND template_type = 'REGION'
               AND template_name IN ('Standard', 'Interactive Report', 'Blank with Attributes',
                                     'Buttons Container', 'Cards', 'Login')
        """)
        for r in rows:
            name = r.get("TEMPLATE_NAME", "")
            tid = r.get("TEMPLATE_ID")
            if tid and name == "Standard":
                REGION_TMPL_STANDARD = tid
                discovered["REGION_TMPL_STANDARD"] = tid
            elif tid and "Interactive Report" in name:
                REGION_TMPL_IR = tid
                discovered["REGION_TMPL_IR"] = tid
            elif tid and "Blank" in name:
                REGION_TMPL_BLANK = tid
                discovered["REGION_TMPL_BLANK"] = tid
            elif tid and "Buttons" in name:
                REGION_TMPL_BUTTONS = tid
                discovered["REGION_TMPL_BUTTONS"] = tid
            elif tid and "Cards" in name:
                REGION_TMPL_CARDS = tid
                discovered["REGION_TMPL_CARDS"] = tid
            elif tid and name == "Login":
                REGION_TMPL_LOGIN = tid
                discovered["REGION_TMPL_LOGIN"] = tid

        # Button templates
        rows = db.execute("""
            SELECT template_name, template_id
              FROM apex_application_templates
             WHERE theme_number = 42
               AND template_type = 'BUTTON'
               AND template_name IN ('Text', 'Icon')
        """)
        for r in rows:
            name = r.get("TEMPLATE_NAME", "")
            tid = r.get("TEMPLATE_ID")
            if tid and name == "Text":
                BTN_TMPL_TEXT = tid
                discovered["BTN_TMPL_TEXT"] = tid
            elif tid and name == "Icon":
                BTN_TMPL_ICON = tid
                discovered["BTN_TMPL_ICON"] = tid

        # Label templates
        rows = db.execute("""
            SELECT template_name, template_id
              FROM apex_application_templates
             WHERE theme_number = 42
               AND template_type = 'FIELD'
               AND template_name IN ('Optional', 'Required')
        """)
        for r in rows:
            name = r.get("TEMPLATE_NAME", "")
            tid = r.get("TEMPLATE_ID")
            if tid and name == "Optional":
                LABEL_OPTIONAL = tid
                discovered["LABEL_OPTIONAL"] = tid
            elif tid and name == "Required":
                LABEL_REQUIRED = tid
                discovered["LABEL_REQUIRED"] = tid

        # Theme style (Redwood Light)
        rows = db.execute("""
            SELECT theme_style_id
              FROM apex_application_theme_styles
             WHERE theme_number = 42
               AND theme_style_name LIKE '%Redwood%'
               AND rownum = 1
        """)
        if rows:
            THEME_STYLE_ID = rows[0].get("THEME_STYLE_ID", THEME_STYLE_ID)
            discovered["THEME_STYLE_ID"] = THEME_STYLE_ID

        # List templates
        rows = db.execute("""
            SELECT template_name, template_id
              FROM apex_application_templates
             WHERE theme_number = 42
               AND template_type = 'LIST'
               AND template_name IN ('Side Navigation Menu', 'Top Navigation Menu', 'Navigation Bar')
        """)
        for r in rows:
            name = r.get("TEMPLATE_NAME", "")
            tid = r.get("TEMPLATE_ID")
            if tid and "Side" in name:
                LIST_TMPL_SIDE_NAV = tid
                discovered["LIST_TMPL_SIDE_NAV"] = tid
            elif tid and "Top" in name:
                LIST_TMPL_TOP_NAV = tid
                discovered["LIST_TMPL_TOP_NAV"] = tid
            elif tid and "Navigation Bar" in name:
                LIST_TMPL_NAVBAR = tid
                discovered["LIST_TMPL_NAVBAR"] = tid

    except Exception as e:
        _log.warning("Template discovery failed: %s", e)

    return discovered

# ── Page Templates ────────────────────────────────────────────────────────────
PAGE_TMPL_STANDARD    = 4072355960268175073
PAGE_TMPL_LOGIN       = 2101157952850466385
PAGE_TMPL_DIALOG      = 2100407606326202693
PAGE_TMPL_MODAL       = 2100407606326202693

# ── Region Templates ──────────────────────────────────────────────────────────
REGION_TMPL_STANDARD  = 4072358936313175081  # Standard (shadow card)
REGION_TMPL_IR        = 2100526641005906379  # Interactive Report (no title bar)
REGION_TMPL_HERO      = None                 # Hero (not used for regions directly)
REGION_TMPL_BLANK     = 2600971555240739962  # Blank with Attributes
REGION_TMPL_BUTTONS   = 2126429139436695430  # Buttons Container (dialog footer)
REGION_TMPL_CARDS     = 2538654340625403440  # Cards
REGION_TMPL_LOGIN     = 2101018444965420270  # Login region

# ── Button Templates ──────────────────────────────────────────────────────────
BTN_TMPL_TEXT         = 4072362960822175091  # Text (default)
BTN_TMPL_ICON         = 4072363219559175092  # Icon

# ── Label Templates ───────────────────────────────────────────────────────────
LABEL_OPTIONAL        = 1609121967514267634
LABEL_REQUIRED        = 1609122147107268652

# ── List Templates ────────────────────────────────────────────────────────────
LIST_TMPL_SIDE_NAV    = 2467739217141810545  # Side Navigation (tree)
LIST_TMPL_TOP_NAV     = 2526754704087354841  # Top Navigation Bar
LIST_TMPL_NAVBAR      = 2847543055748234966  # Navigation Bar

# ── Theme style ───────────────────────────────────────────────────────────────
THEME_STYLE_ID        = 2721322117358710262  # Redwood Light

# ── Report Templates ──────────────────────────────────────────────────────────
REPORT_TMPL_VALUE_ATTR = 2538654340625403440

# ── Checksum salt ─────────────────────────────────────────────────────────────
CHECKSUM_SALT = "A1B2C3D4E5F6789012345678901234567890ABCDEF1234567890ABCDEF123456"

# ── Item types (APEX native) ──────────────────────────────────────────────────
ITEM_TEXT         = "NATIVE_TEXT_FIELD"
ITEM_NUMBER       = "NATIVE_NUMBER_FIELD"
ITEM_DATE         = "NATIVE_DATE_PICKER_APEX"
ITEM_SELECT       = "NATIVE_SELECT_LIST"
ITEM_HIDDEN       = "NATIVE_HIDDEN"
ITEM_TEXTAREA     = "NATIVE_TEXTAREA"
ITEM_YES_NO       = "NATIVE_YES_NO"
ITEM_PASSWORD     = "NATIVE_PASSWORD"
ITEM_DISPLAY      = "NATIVE_DISPLAY_ONLY"
ITEM_CHECKBOX     = "NATIVE_CHECKBOX"
ITEM_RADIO        = "NATIVE_RADIOGROUP"

# ── Region types ──────────────────────────────────────────────────────────────
REGION_IR         = "NATIVE_IR"
REGION_FORM       = "NATIVE_FORM"
REGION_STATIC     = "NATIVE_STATIC"
REGION_PLSQL      = "NATIVE_PLSQL"
REGION_CHART      = "NATIVE_JET_CHART"

# ── Button actions ────────────────────────────────────────────────────────────
BTN_ACTION_SUBMIT   = "SUBMIT"
BTN_ACTION_REDIRECT = "REDIRECT_URL"
BTN_ACTION_DEFINED  = "DEFINED_BY_DA"

# ── Process types ─────────────────────────────────────────────────────────────
PROC_DML  = "NATIVE_FORM_DML"
PROC_PLSQL = "NATIVE_PLSQL"

# ── Dynamic Action events ─────────────────────────────────────────────────────
DA_CLICK  = "click"
DA_CHANGE = "change"
DA_LOAD   = "page-load"
