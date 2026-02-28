"""Universal Theme 42 template IDs hardcoded from this APEX workspace.

These IDs are specific to APEX 24.2.13 / Universal Theme 42.
They reference built-in theme templates and do not change across workspaces
for the same APEX version.
"""

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
ITEM_DATE         = "NATIVE_DATE_PICKER_JET"
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
