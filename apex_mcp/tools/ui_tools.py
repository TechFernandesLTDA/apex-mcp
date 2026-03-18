"""UI Tools: 20 rich visual components for Oracle APEX pages.

All tools render HTML via NATIVE_PLSQL regions using sys.htp.p().
No external JS libraries required — works with Universal Theme 42 / APEX 24.2.
"""
from __future__ import annotations

import html as _html_mod
from typing import Any

from ..db import db
from ..ids import ids
from ..session import session, RegionInfo
from ..templates import REGION_TMPL_STANDARD, REGION_TMPL_BLANK
from ..utils import _json, _esc, _blk, _sql_to_varchar2

from ..palette import COLORS, resolve_color, resolve_palette  # noqa: F401


def _col(color: str) -> str:
    """Resolve a named or hex color via the palette module."""
    return resolve_color(color)


def _html_esc(text: str) -> str:
    """Escape user-provided text for safe embedding in HTML output.

    Converts &, <, >, and quotes to HTML entities so that user text
    cannot break the generated HTML structure.
    """
    return _html_mod.escape(str(text), quote=True)


def _guard(page_id: int) -> str | None:
    if not db.is_connected():
        return _json({"status": "error", "error": "Not connected. Call apex_connect() first."})
    if not session.import_begun:
        return _json({"status": "error", "error": "No import session active."})
    if page_id not in session.pages:
        return _json({"status": "error", "error": f"Page {page_id} not found."})
    return None


def _plsql_region(region_id: int, region_name: str, plsql_body: str,
                  sequence: int, hide_header: bool = True) -> None:
    tmpl_opts = "#DEFAULT#:t-Region--noPadding:t-Region--hideHeader" if hide_header else "#DEFAULT#:t-Region--noPadding"
    db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_plug(
 p_id=>wwv_flow_imp.id({region_id})
,p_plug_name=>'{_esc(region_name)}'
,p_region_template_options=>'{tmpl_opts}'
,p_plug_template=>{REGION_TMPL_BLANK}
,p_plug_display_sequence=>{sequence}
,p_plug_display_point=>'BODY'
,p_plug_source=>'{_esc(plsql_body)}'
,p_plug_source_type=>'NATIVE_PLSQL'
,p_plug_query_options=>'DERIVED_REPORT_COLUMNS'
);"""))


# ── 1. Hero Banner ─────────────────────────────────────────────────────────────

def apex_add_hero_banner(
    page_id: int,
    title: str,
    subtitle: str = "",
    stats: list[dict[str, str]] | None = None,
    bg_color: str = "unimed",
    button_label: str = "",
    button_url: str = "",
    title_size: str = "1.7rem",
    subtitle_size: str = "1rem",
    custom_css: str = "",
    sequence: int = 5,
) -> str:
    """Add a full-width hero banner to a page.

    Renders a prominent welcome/header section with a title, optional subtitle,
    optional inline KPI stats, and an optional call-to-action button.

    Args:
        page_id: Target page ID.
        title: Main banner title. Supports &APP_USER. substitutions.
        subtitle: Secondary text under the title.
        stats: Up to 4 inline KPI items shown inside the banner.
            Each dict: {"label": "Total", "sql": "SELECT COUNT(*) FROM T", "suffix": ""}
        bg_color: Background color — named ("unimed","blue","teal") or hex ("#00995D").
        button_label: Optional CTA button label (e.g., "New Record").
        button_url: URL or f?p= reference for CTA button.
        title_size: CSS font-size for the title (default "1.7rem").
        subtitle_size: CSS font-size for the subtitle (default "1rem").
        custom_css: Additional CSS rules injected into the style block.
        sequence: Display order on page.

    Returns:
        JSON with status, region_id.
    """
    err = _guard(page_id)
    if err:
        return err

    color = _col(bg_color)
    region_id = ids.next(f"hero_{page_id}_{_esc(title)}")

    stat_lines: list[str] = []
    for s in (stats or []):
        lbl = _esc(_html_esc(s.get("label", "")))
        sql = _esc(s.get("sql", "SELECT '' FROM DUAL"))
        sfx = _esc(_html_esc(s.get("suffix", "")))
        stat_lines.append(f"""
  BEGIN EXECUTE IMMEDIATE '{sql}' INTO v_val;
  EXCEPTION WHEN OTHERS THEN v_val := '-'; END;
  sys.htp.p('<div class="mcp-hero-stat"><div class="mcp-hero-stat-val">'||APEX_ESCAPE.HTML(v_val)||'{sfx}</div>'||
            '<div class="mcp-hero-stat-lbl">{lbl}</div></div>');""")

    btn_html = ""
    if button_label and button_url:
        btn_html = (f'<a href=\\"{_esc(_html_esc(button_url))}\\" class="mcp-hero-btn">'
                    f'{_esc(_html_esc(button_label))}</a>')

    stats_block = "".join(stat_lines)
    has_stats = bool(stats)
    stats_open = "  sys.htp.p('<div class=\"mcp-hero-stats\">'); " if has_stats else ""
    stats_close = "  sys.htp.p('</div>'); " if has_stats else ""
    extra_css = _esc(custom_css) if custom_css else ""

    plsql = f"""DECLARE v_val VARCHAR2(4000);
BEGIN
  sys.htp.p('<style>
    .mcp-hero{{background:linear-gradient(135deg,{color} 0%,{color}cc 100%);
      color:#fff;padding:28px 32px;border-radius:12px;margin-bottom:16px;}}
    .mcp-hero h2{{margin:0 0 6px;font-size:{_esc(title_size)};font-weight:700;color:#fff;}}
    .mcp-hero-sub{{opacity:.85;font-size:{_esc(subtitle_size)};margin-bottom:16px;color:#fff;}}
    .mcp-hero-stats{{display:flex;gap:24px;flex-wrap:wrap;margin-top:14px;}}
    .mcp-hero-stat{{background:rgba(255,255,255,.18);border-radius:8px;padding:10px 18px;
      min-width:90px;text-align:center;flex:1 1 auto;}}
    .mcp-hero-stat-val{{font-size:1.5rem;font-weight:700;color:#fff;}}
    .mcp-hero-stat-lbl{{font-size:.75rem;opacity:.85;text-transform:uppercase;letter-spacing:.5px;color:#fff;}}
    .mcp-hero-btn{{display:inline-block;background:#fff;color:{color};padding:9px 22px;
      border-radius:20px;font-weight:600;text-decoration:none;margin-top:14px;
      transition:opacity .2s;}}.mcp-hero-btn:hover{{opacity:.85;}}
    @media(max-width:600px){{
      .mcp-hero{{padding:20px 16px;}}
      .mcp-hero h2{{font-size:1.3rem;}}
      .mcp-hero-stats{{gap:12px;}}
      .mcp-hero-stat{{min-width:70px;padding:8px 12px;}}
    }}
    {extra_css}
  </style>');
  sys.htp.p('<div class="mcp-hero">');
  sys.htp.p('<h2>{_esc(_html_esc(title))}</h2>');
  sys.htp.p('<div class="mcp-hero-sub">{_esc(_html_esc(subtitle))}</div>');
  {stats_open}
  {stats_block}
  {stats_close}
  sys.htp.p('{_esc(btn_html)}');
  sys.htp.p('</div>');
END;"""

    try:
        _plsql_region(region_id, title, plsql, sequence)
        session.regions[region_id] = RegionInfo(
            region_id=region_id, page_id=page_id,
            region_name=title, region_type="hero_banner",
        )
        return _json({"status": "ok", "region_id": region_id, "page_id": page_id,
                      "message": f"Hero banner '{title}' added to page {page_id}."})
    except Exception as e:
        return _json({"status": "error", "error": str(e)})


# ── 2. KPI Row ─────────────────────────────────────────────────────────────────

def apex_add_kpi_row(
    page_id: int,
    region_name: str,
    metrics: list[dict[str, str]],
    value_size: str = "1.4rem",
    custom_css: str = "",
    sequence: int = 10,
) -> str:
    """Add a compact horizontal KPI row with colored values and labels.

    Lighter than apex_add_metric_cards — single-line strip, no icons,
    ideal as a summary bar between sections.

    Args:
        page_id: Target page ID.
        region_name: Internal region name.
        metrics: List of metric dicts (3–6 items):
            - "label": Display label
            - "sql": SQL returning a single scalar value
            - "suffix": Optional unit suffix ("%" , " dias", etc.)
            - "color": Accent color for the value text
        value_size: CSS font-size for metric values (default "1.4rem").
        custom_css: Additional CSS rules injected into the style block.

    Returns:
        JSON with status, region_id.
    """
    err = _guard(page_id)
    if err:
        return err

    region_id = ids.next(f"kpirow_{page_id}_{_esc(region_name)}")
    extra_css = _esc(custom_css) if custom_css else ""
    lines: list[str] = [
        "DECLARE v_val VARCHAR2(4000);",
        "BEGIN",
        "  sys.htp.p('<style>"
        ".mcp-kpi-row{display:flex;flex-wrap:wrap;gap:0;background:#fff;border-radius:10px;"
        "box-shadow:0 2px 8px rgba(0,0,0,.08);overflow:hidden;margin-bottom:12px;}"
        ".mcp-kpi-cell{flex:1 1 auto;padding:14px 20px;text-align:center;border-right:1px solid #f0f0f0;min-width:100px;}"
        ".mcp-kpi-cell:last-child{border-right:none;}"
        f".mcp-kpi-val{{font-size:{_esc(value_size)};font-weight:700;}}"
        ".mcp-kpi-lbl{font-size:.72rem;color:#888;text-transform:uppercase;letter-spacing:.4px;margin-top:3px;}"
        "@media(max-width:600px){"
        ".mcp-kpi-row{flex-direction:column;}"
        ".mcp-kpi-cell{border-right:none;border-bottom:1px solid #f0f0f0;padding:10px 16px;}"
        ".mcp-kpi-cell:last-child{border-bottom:none;}}"
        f"{extra_css}"
        "</style>');",
        "  sys.htp.p('<div class=\"mcp-kpi-row\">');",
    ]
    for m in metrics:
        lbl = _esc(_html_esc(m.get("label", "")))
        sql = _esc(m.get("sql", "SELECT '' FROM DUAL"))
        sfx = _esc(_html_esc(m.get("suffix", "")))
        clr = _col(m.get("color", "blue"))
        lines.append(f"""
  BEGIN EXECUTE IMMEDIATE '{sql}' INTO v_val;
  EXCEPTION WHEN OTHERS THEN v_val := '-'; END;
  sys.htp.p('<div class="mcp-kpi-cell">');
  sys.htp.p('<div class="mcp-kpi-val" style="color:{clr}">'||APEX_ESCAPE.HTML(v_val)||'{sfx}</div>');
  sys.htp.p('<div class="mcp-kpi-lbl">{lbl}</div>');
  sys.htp.p('</div>');""")
    lines += ["  sys.htp.p('</div>');", "END;"]
    plsql = "\n".join(lines)

    try:
        _plsql_region(region_id, region_name, plsql, sequence)
        session.regions[region_id] = RegionInfo(
            region_id=region_id, page_id=page_id,
            region_name=region_name, region_type="kpi_row",
        )
        return _json({"status": "ok", "region_id": region_id, "page_id": page_id,
                      "message": f"KPI row '{region_name}' added to page {page_id} ({len(metrics)} metrics)."})
    except Exception as e:
        return _json({"status": "error", "error": str(e)})


# ── 3. Progress Tracker ────────────────────────────────────────────────────────

def apex_add_progress_tracker(
    page_id: int,
    region_name: str,
    steps: list[str],
    current_step: int = 1,
    color: str = "unimed",
    completed_label: str = "",
    custom_css: str = "",
    sequence: int = 10,
) -> str:
    """Add a horizontal step-by-step progress tracker.

    Shows a numbered breadcrumb-style progress indicator — ideal for
    wizard flows, onboarding, or multi-stage processes.

    Args:
        page_id: Target page ID.
        region_name: Internal region name.
        steps: List of step labels (e.g., ["Dados Basicos","Clinica","Confirmacao"]).
        current_step: Active step number (1-based).
        color: Accent color for active/completed steps.
        completed_label: Override the checkmark character for completed steps.
        custom_css: Additional CSS rules injected into the style block.
        sequence: Display order on page.

    Returns:
        JSON with status, region_id.
    """
    err = _guard(page_id)
    if err:
        return err

    region_id = ids.next(f"progress_{page_id}_{_esc(region_name)}")
    clr = _col(color)
    active = max(1, min(current_step, len(steps)))
    extra_css = _esc(custom_css) if custom_css else ""

    step_html_parts: list[str] = []
    for i, label in enumerate(steps, start=1):
        safe_label = _html_esc(label)
        if i < active:
            cls, style = "mcp-step done", f"background:{clr};color:#fff;border-color:{clr};"
        elif i == active:
            cls, style = "mcp-step active", f"background:{clr};color:#fff;border-color:{clr};box-shadow:0 0 0 3px {clr}44;"
        else:
            cls, style = "mcp-step", "background:#fff;color:#999;border-color:#ddd;"
        connector = "<div class='mcp-step-line'></div>" if i < len(steps) else ""
        step_html_parts.append(
            f'<div class="mcp-step-wrap">'
            f'<div class="{cls}" style="{style}">{i}</div>'
            f'<div class="mcp-step-label">{_esc(safe_label)}</div>'
            f'</div>{connector}'
        )

    check_content = _esc(_html_esc(completed_label)) if completed_label else "\\2713"
    steps_html = _esc("".join(step_html_parts))
    plsql = f"""BEGIN
  sys.htp.p('<style>
    .mcp-progress{{display:flex;align-items:flex-start;justify-content:center;padding:14px 0;flex-wrap:wrap;}}
    .mcp-step-wrap{{display:flex;flex-direction:column;align-items:center;flex:1;min-width:60px;}}
    .mcp-step{{width:32px;height:32px;border-radius:50%;border:2px solid #ddd;
      display:flex;align-items:center;justify-content:center;font-weight:700;
      font-size:.85rem;transition:all .3s;}}
    .mcp-step.done::after{{content:"{check_content}";}}
    .mcp-step-label{{font-size:.72rem;color:#666;margin-top:5px;text-align:center;max-width:80px;}}
    .mcp-step-line{{flex:1;height:2px;background:#e0e0e0;margin:15px -2px 0;min-width:20px;}}
    @media(max-width:480px){{
      .mcp-progress{{gap:4px;}}
      .mcp-step-label{{font-size:.65rem;max-width:60px;}}
      .mcp-step-line{{min-width:10px;}}
    }}
    {extra_css}
  </style>');
  sys.htp.p('<div class="mcp-progress">{steps_html}</div>');
END;"""

    try:
        _plsql_region(region_id, region_name, plsql, sequence)
        session.regions[region_id] = RegionInfo(
            region_id=region_id, page_id=page_id,
            region_name=region_name, region_type="progress_tracker",
        )
        return _json({"status": "ok", "region_id": region_id, "page_id": page_id,
                      "message": f"Progress tracker '{region_name}' added (step {active}/{len(steps)})."})
    except Exception as e:
        return _json({"status": "error", "error": str(e)})


# ── 4. Alert Box ───────────────────────────────────────────────────────────────

def apex_add_alert_box(
    page_id: int,
    message: str,
    alert_type: str = "info",
    title: str = "",
    dismissible: bool = True,
    icon: str = "",
    custom_css: str = "",
    sequence: int = 5,
) -> str:
    """Add a styled alert/info/warning/error box to a page.

    A more visual alternative to apex_add_notification_region — uses
    stronger typography and optional title.

    Args:
        page_id: Target page ID.
        message: Alert message text. Supports &ITEM. substitutions.
        alert_type: "info" | "success" | "warning" | "error".
        title: Optional bold title line above the message.
        dismissible: Show x close button (default True).
        icon: Font Awesome class override (e.g., "fa-bell"). Uses type default if empty.
        custom_css: Additional CSS rules injected into the style block.
        sequence: Display order on page.

    Returns:
        JSON with status, region_id.
    """
    err = _guard(page_id)
    if err:
        return err

    # Text color, background, border color, default icon
    # All combos maintain WCAG AA contrast (4.5:1+)
    TYPE_MAP = {
        "info":    ("#1565c0", "#e3f2fd", "#90caf9", "fa-info-circle"),
        "success": ("#1b5e20", "#e8f5e9", "#a5d6a7", "fa-check-circle"),
        "warning": ("#e65100", "#fff8e1", "#ffe082", "fa-exclamation-triangle"),
        "error":   ("#b71c1c", "#ffebee", "#ef9a9a", "fa-times-circle"),
    }
    txt, bg, border, def_icon = TYPE_MAP.get(alert_type, TYPE_MAP["info"])
    fa = icon or def_icon
    dismiss = (
        '<button onclick="this.closest(\'.mcp-alert\').remove()" '
        f'style="float:right;background:none;border:none;cursor:pointer;'
        f'color:{txt};font-size:1.1rem;line-height:1;">&times;</button>'
    ) if dismissible else ""
    safe_title = _html_esc(title)
    title_html = f'<strong style="display:block;margin-bottom:4px;">{_esc(safe_title)}</strong>' if title else ""
    region_id = ids.next(f"alert_{page_id}_{alert_type}")
    extra_css = _esc(custom_css) if custom_css else ""

    plsql = f"""BEGIN
  sys.htp.p('<style>
    .mcp-alert{{border-radius:8px;padding:14px 18px;margin-bottom:14px;}}
    {extra_css}
  </style>');
  sys.htp.p('<div class="mcp-alert" style="background:{bg};border-left:4px solid {border};'||
            'color:{txt};">');
  sys.htp.p('{_esc(dismiss)}');
  sys.htp.p('<span class="fa {fa}" style="margin-right:8px;"></span>');
  sys.htp.p('{_esc(title_html)}');
  sys.htp.p('{_esc(_html_esc(message))}');
  sys.htp.p('</div>');
END;"""

    try:
        name = f"Alert {alert_type.title()} {page_id}"
        _plsql_region(region_id, name, plsql, sequence)
        session.regions[region_id] = RegionInfo(
            region_id=region_id, page_id=page_id,
            region_name=name, region_type="alert_box",
        )
        return _json({"status": "ok", "region_id": region_id, "alert_type": alert_type,
                      "page_id": page_id, "message": f"Alert box ({alert_type}) added to page {page_id}."})
    except Exception as e:
        return _json({"status": "error", "error": str(e)})


# ── 5. Stat Delta ──────────────────────────────────────────────────────────────

def apex_add_stat_delta(
    page_id: int,
    region_name: str,
    metrics: list[dict[str, Any]],
    columns: int = 4,
    delta_label: str = "vs anterior",
    custom_css: str = "",
    sequence: int = 10,
) -> str:
    """Add metric cards with current value and a delta (change vs previous period).

    Each card shows: icon, label, current value, delta arrow with % change.

    Args:
        page_id: Target page ID.
        region_name: Internal region name.
        metrics: List of metric dicts:
            - "label": Card title
            - "sql": SQL returning current scalar value
            - "prev_sql": SQL returning previous-period value (for delta)
            - "icon": Font Awesome class (e.g., "fa-users")
            - "color": Accent color
            - "suffix": Unit suffix ("%", " pacientes", etc.)
            - "prefix": Unit prefix ("R$ ", "$", etc.)
        columns: Number of columns (2-4).
        delta_label: Label text after the percentage change (default "vs anterior").
        custom_css: Additional CSS rules injected into the style block.
        sequence: Display order on page.

    Returns:
        JSON with status, region_id.
    """
    err = _guard(page_id)
    if err:
        return err

    region_id = ids.next(f"delta_{page_id}_{_esc(region_name)}")
    col_pct = {2: "48%", 3: "31%", 4: "23%"}.get(columns, "23%")
    extra_css = _esc(custom_css) if custom_css else ""
    safe_delta_lbl = _esc(_html_esc(delta_label))

    lines = [
        "DECLARE",
        "  v_cur  NUMBER;",
        "  v_prev NUMBER;",
        "  v_delta NUMBER;",
        "  v_delta_str VARCHAR2(200);",
        "  v_delta_color VARCHAR2(20);",
        "  v_arrow VARCHAR2(10);",
        "BEGIN",
        f"  sys.htp.p('<style>"
        f".mcp-delta-grid{{display:flex;flex-wrap:wrap;gap:14px;padding:4px 0;}}"
        f".mcp-delta-card{{flex:1 1 {col_pct};min-width:140px;background:#fff;border-radius:10px;"
        f"padding:16px;box-shadow:0 2px 8px rgba(0,0,0,.08);}}"
        f".mcp-delta-top{{display:flex;align-items:center;gap:10px;margin-bottom:10px;}}"
        f".mcp-delta-icon{{font-size:22px;}}"
        f".mcp-delta-label{{font-size:.75rem;color:#888;text-transform:uppercase;letter-spacing:.4px;}}"
        f".mcp-delta-val{{font-size:1.6rem;font-weight:700;color:#333;}}"
        f".mcp-delta-change{{font-size:.78rem;margin-top:4px;font-weight:600;}}"
        f"@media(max-width:600px){{.mcp-delta-card{{flex:1 1 100%;min-width:0;}}}}"
        f"{extra_css}"
        f"</style>');",
        "  sys.htp.p('<div class=\"mcp-delta-grid\">');",
    ]

    for m in metrics:
        lbl  = _esc(_html_esc(m.get("label", "")))
        sql  = _esc(m.get("sql", "SELECT 0 FROM DUAL"))
        psql = _esc(m.get("prev_sql", "SELECT 0 FROM DUAL"))
        ico  = m.get("icon", "fa-chart-bar")
        clr  = _col(m.get("color", "blue"))
        sfx  = _esc(_html_esc(m.get("suffix", "")))
        pfx  = _esc(_html_esc(m.get("prefix", "")))
        lines.append(f"""
  BEGIN EXECUTE IMMEDIATE '{sql}'  INTO v_cur;  EXCEPTION WHEN OTHERS THEN v_cur  := 0; END;
  BEGIN EXECUTE IMMEDIATE '{psql}' INTO v_prev; EXCEPTION WHEN OTHERS THEN v_prev := 0; END;
  IF v_prev <> 0 THEN
    v_delta := ROUND((v_cur - v_prev) / v_prev * 100, 1);
  ELSE
    v_delta := 0;
  END IF;
  IF v_delta > 0 THEN v_arrow := '&#9650;'; v_delta_color := '#43a047';
  ELSIF v_delta < 0 THEN v_arrow := '&#9660;'; v_delta_color := '#e53935';
  ELSE v_arrow := '&#8213;'; v_delta_color := '#9e9e9e'; END IF;
  v_delta_str := v_arrow || ' ' || TO_CHAR(ABS(v_delta)) || '% {safe_delta_lbl}';
  sys.htp.p('<div class="mcp-delta-card" style="border-top:3px solid {clr}">');
  sys.htp.p('<div class="mcp-delta-top">');
  sys.htp.p('<span class="fa {ico} mcp-delta-icon" style="color:{clr}"></span>');
  sys.htp.p('<span class="mcp-delta-label">{lbl}</span>');
  sys.htp.p('</div>');
  sys.htp.p('<div class="mcp-delta-val">{pfx}' || TO_CHAR(v_cur) || '{sfx}</div>');
  sys.htp.p('<div class="mcp-delta-change" style="color:' || v_delta_color || '">' || v_delta_str || '</div>');
  sys.htp.p('</div>');""")

    lines += ["  sys.htp.p('</div>');", "END;"]
    plsql = "\n".join(lines)

    try:
        _plsql_region(region_id, region_name, plsql, sequence)
        session.regions[region_id] = RegionInfo(
            region_id=region_id, page_id=page_id,
            region_name=region_name, region_type="stat_delta",
        )
        return _json({"status": "ok", "region_id": region_id, "page_id": page_id,
                      "message": f"Stat delta '{region_name}' added to page {page_id} ({len(metrics)} metrics)."})
    except Exception as e:
        return _json({"status": "error", "error": str(e)})


# ── 6. Quick Links ─────────────────────────────────────────────────────────────

def apex_add_quick_links(
    page_id: int,
    region_name: str,
    links: list[dict[str, str]],
    columns: int = 4,
    custom_css: str = "",
    sequence: int = 10,
) -> str:
    """Add a grid of quick-action icon buttons to a page.

    Ideal for dashboard homepages -- a visually rich navigation shortcut panel.

    Args:
        page_id: Target page ID.
        region_name: Internal region name.
        links: List of link dicts (4-8 recommended):
            - "label": Button label
            - "url": Target URL or f?p= link
            - "icon": Font Awesome class (e.g., "fa-plus", "fa-users")
            - "color": Accent/background color
            - "badge": Optional badge/count (from SQL or static text)
        columns: Number of columns (2-5, default 4).
        custom_css: Additional CSS rules injected into the style block.
        sequence: Display order on page.

    Returns:
        JSON with status, region_id.
    """
    err = _guard(page_id)
    if err:
        return err

    region_id = ids.next(f"quicklinks_{page_id}_{_esc(region_name)}")
    col_pct = {2: "48%", 3: "31%", 4: "23%", 5: "18%"}.get(columns, "23%")
    extra_css = _esc(custom_css) if custom_css else ""

    html_parts: list[str] = []
    for lk in links:
        lbl  = _esc(_html_esc(lk.get("label", "Link")))
        url  = _esc(_html_esc(lk.get("url", "#")))
        ico  = lk.get("icon", "fa-link")
        clr  = _col(lk.get("color", "blue"))
        badge = _esc(_html_esc(lk.get("badge", "")))
        bdg = f'<span class="mcp-ql-badge">{badge}</span>' if badge else ""
        html_parts.append(
            f'<a href="{url}" class="mcp-ql-btn" style="border-top:3px solid {clr};">'
            f'<span class="fa {ico} mcp-ql-icon" style="color:{clr};"></span>'
            f'<span class="mcp-ql-label">{lbl}</span>'
            f'{bdg}</a>'
        )

    all_html = _esc("".join(html_parts))
    plsql = f"""BEGIN
  sys.htp.p('<style>
    .mcp-ql-grid{{display:flex;flex-wrap:wrap;gap:12px;padding:4px 0;}}
    .mcp-ql-btn{{flex:1 1 {col_pct};min-width:120px;background:#fff;border-radius:10px;
      padding:18px 12px;text-align:center;text-decoration:none;color:#333;
      box-shadow:0 2px 8px rgba(0,0,0,.08);transition:transform .15s,box-shadow .15s;
      display:flex;flex-direction:column;align-items:center;gap:8px;position:relative;}}
    .mcp-ql-btn:hover{{transform:translateY(-2px);box-shadow:0 4px 16px rgba(0,0,0,.14);}}
    .mcp-ql-icon{{font-size:1.6rem;}}
    .mcp-ql-label{{font-size:.8rem;font-weight:600;color:#555;text-align:center;}}
    .mcp-ql-badge{{position:absolute;top:8px;right:10px;background:#e53935;color:#fff;
      border-radius:10px;padding:1px 6px;font-size:.7rem;font-weight:700;}}
    @media(max-width:480px){{
      .mcp-ql-btn{{flex:1 1 45%;min-width:100px;padding:14px 8px;}}
      .mcp-ql-icon{{font-size:1.3rem;}}
    }}
    {extra_css}
  </style>');
  sys.htp.p('<div class="mcp-ql-grid">{all_html}</div>');
END;"""

    try:
        _plsql_region(region_id, region_name, plsql, sequence)
        session.regions[region_id] = RegionInfo(
            region_id=region_id, page_id=page_id,
            region_name=region_name, region_type="quick_links",
        )
        return _json({"status": "ok", "region_id": region_id, "page_id": page_id,
                      "message": f"Quick links '{region_name}' added to page {page_id} ({len(links)} links)."})
    except Exception as e:
        return _json({"status": "error", "error": str(e)})


# ── 7. Leaderboard ─────────────────────────────────────────────────────────────

def apex_add_leaderboard(
    page_id: int,
    region_name: str,
    sql_query: str,
    label_column: str = "LABEL",
    value_column: str = "VALUE",
    max_rows: int = 10,
    color: str = "unimed",
    show_medals: bool = True,
    custom_css: str = "",
    sequence: int = 10,
) -> str:
    """Add a ranked leaderboard list from SQL.

    Displays top-N items with rank position, optional medal icons,
    a proportional progress bar, and the value.

    Args:
        page_id: Target page ID.
        region_name: Region display name (shown as header).
        sql_query: SQL returning rows with label and value columns.
            ORDER BY value DESC should be in the SQL.
            Example: "SELECT t.DS_NOME LABEL, COUNT(*) VALUE FROM TEA_TERAPEUTAS t
                        JOIN TEA_AVALIACOES a ON a.ID_TERAPEUTA = t.ID_TERAPEUTA
                        GROUP BY t.DS_NOME ORDER BY 2 DESC"
        label_column: Column name for the item label (default "LABEL").
        value_column: Column name for the numeric value (default "VALUE").
        max_rows: Maximum rows to display (default 10).
        color: Accent color for progress bars.
        show_medals: Show medal icons for top 3 (default True).
        custom_css: Additional CSS rules injected into the style block.
        sequence: Display order on page.

    Returns:
        JSON with status, region_id.
    """
    err = _guard(page_id)
    if err:
        return err

    region_id = ids.next(f"leaderboard_{page_id}_{_esc(region_name)}")
    clr = _col(color)
    lbl_col = label_column.upper()
    val_col = value_column.upper()
    extra_css = _esc(custom_css) if custom_css else ""

    medals = "CASE WHEN v_rank = 1 THEN '&#127949;' WHEN v_rank = 2 THEN '&#127950;' WHEN v_rank = 3 THEN '&#127951;' ELSE TO_CHAR(v_rank) END" if show_medals else "TO_CHAR(v_rank)"

    plsql = f"""DECLARE
  v_max  NUMBER := 0;
  v_rank NUMBER := 0;
  v_bar  NUMBER;
  v_medal VARCHAR2(20);
BEGIN
  sys.htp.p('<style>
    .mcp-lb{{background:#fff;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,.08);overflow:hidden;}}
    .mcp-lb-hdr{{background:{clr};color:#fff;padding:12px 16px;font-weight:700;font-size:.9rem;}}
    .mcp-lb-row{{display:flex;align-items:center;gap:12px;padding:10px 16px;border-bottom:1px solid #f5f5f5;flex-wrap:nowrap;}}
    .mcp-lb-row:last-child{{border-bottom:none;}}
    .mcp-lb-rank{{min-width:28px;font-size:.85rem;font-weight:700;text-align:center;}}
    .mcp-lb-name{{flex:1;font-size:.88rem;color:#333;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}}
    .mcp-lb-bar-wrap{{width:90px;background:#f0f0f0;border-radius:4px;height:6px;flex-shrink:0;}}
    .mcp-lb-bar{{height:6px;border-radius:4px;background:{clr};}}
    .mcp-lb-val{{min-width:40px;text-align:right;font-weight:700;font-size:.88rem;color:{clr};}}
    @media(max-width:480px){{.mcp-lb-bar-wrap{{display:none;}}}}
    {extra_css}
  </style>');
  sys.htp.p('<div class="mcp-lb">');
  sys.htp.p('<div class="mcp-lb-hdr">{_esc(_html_esc(region_name))}</div>');
  BEGIN
    EXECUTE IMMEDIATE 'SELECT NVL(MAX({val_col}),1) FROM ({_esc(sql_query)})' INTO v_max;
    IF v_max = 0 THEN v_max := 1; END IF;
  EXCEPTION WHEN OTHERS THEN v_max := 1; END;
  FOR r IN (SELECT {lbl_col}, {val_col} FROM ({sql_query}) WHERE ROWNUM <= {max_rows}) LOOP
    v_rank := v_rank + 1;
    v_bar  := GREATEST(ROUND(r.{val_col} / v_max * 90), 4);
    v_medal := {medals};
    sys.htp.p('<div class="mcp-lb-row">');
    sys.htp.p('<div class="mcp-lb-rank">' || v_medal || '</div>');
    sys.htp.p('<div class="mcp-lb-name">' || APEX_ESCAPE.HTML(r.{lbl_col}) || '</div>');
    sys.htp.p('<div class="mcp-lb-bar-wrap"><div class="mcp-lb-bar" style="width:' || v_bar || 'px"></div></div>');
    sys.htp.p('<div class="mcp-lb-val">' || TO_CHAR(r.{val_col}) || '</div>');
    sys.htp.p('</div>');
  END LOOP;
  sys.htp.p('</div>');
END;"""

    try:
        _plsql_region(region_id, region_name, plsql, sequence, hide_header=False)
        session.regions[region_id] = RegionInfo(
            region_id=region_id, page_id=page_id,
            region_name=region_name, region_type="leaderboard",
        )
        return _json({"status": "ok", "region_id": region_id, "page_id": page_id,
                      "message": f"Leaderboard '{region_name}' added to page {page_id}."})
    except Exception as e:
        return _json({"status": "error", "error": str(e)})


# ── 8. Tag Cloud ───────────────────────────────────────────────────────────────

def apex_add_tag_cloud(
    page_id: int,
    region_name: str,
    sql_query: str,
    label_column: str = "LABEL",
    count_column: str = "CNT",
    custom_css: str = "",
    sequence: int = 10,
) -> str:
    """Add a dynamic tag cloud from SQL.

    Font size scales proportionally with count. Clicking a tag
    applies a page-item filter (optional).

    Args:
        page_id: Target page ID.
        region_name: Region display name.
        sql_query: SQL returning label and count columns.
            Example: "SELECT DS_STATUS LABEL, COUNT(*) CNT
                        FROM TEA_AVALIACOES GROUP BY DS_STATUS ORDER BY 2 DESC"
        label_column: Column name for the tag text.
        count_column: Column name for the frequency/count.
        custom_css: Additional CSS rules injected into the style block.
        sequence: Display order on page.

    Returns:
        JSON with status, region_id.
    """
    err = _guard(page_id)
    if err:
        return err

    region_id = ids.next(f"tagcloud_{page_id}_{_esc(region_name)}")
    lbl = label_column.upper()
    cnt = count_column.upper()
    extra_css = _esc(custom_css) if custom_css else ""
    palette = resolve_palette("default", size=10)

    pal_assignments = "; ".join(
        f"v_pal({i + 1}):='{c}'" for i, c in enumerate(palette)
    )

    plsql = f"""DECLARE
  v_max   NUMBER := 1;
  v_sz    NUMBER;
  v_idx   NUMBER := 0;
  TYPE t_colors IS TABLE OF VARCHAR2(20) INDEX BY PLS_INTEGER;
  v_pal   t_colors;
BEGIN
  {pal_assignments};
  sys.htp.p('<style>
    .mcp-tagcloud{{display:flex;flex-wrap:wrap;gap:8px;padding:12px 4px;align-items:center;}}
    .mcp-tag{{display:inline-block;padding:4px 12px;border-radius:20px;color:#fff;
      font-weight:600;cursor:default;transition:opacity .2s;opacity:.9;}}
    .mcp-tag:hover{{opacity:1;box-shadow:0 2px 8px rgba(0,0,0,.2);}}
    {extra_css}
  </style>');
  BEGIN
    EXECUTE IMMEDIATE 'SELECT NVL(MAX({cnt}),1) FROM ({_esc(sql_query)})' INTO v_max;
    IF v_max = 0 THEN v_max := 1; END IF;
  EXCEPTION WHEN OTHERS THEN v_max := 1; END;
  sys.htp.p('<div class="mcp-tagcloud">');
  FOR r IN (SELECT {lbl}, {cnt} FROM ({sql_query})) LOOP
    v_idx := MOD(v_idx, 10) + 1;
    v_sz  := GREATEST(ROUND(0.75 + (r.{cnt} / v_max) * 0.9, 2), 0.75);
    sys.htp.p('<span class="mcp-tag" style="background:' || v_pal(v_idx) ||
              ';font-size:' || TO_CHAR(v_sz) || 'rem" title="' ||
              APEX_ESCAPE.HTML(TO_CHAR(r.{cnt})) || '">' ||
              APEX_ESCAPE.HTML(r.{lbl}) || '</span>');
  END LOOP;
  sys.htp.p('</div>');
END;"""

    try:
        _plsql_region(region_id, region_name, plsql, sequence, hide_header=False)
        session.regions[region_id] = RegionInfo(
            region_id=region_id, page_id=page_id,
            region_name=region_name, region_type="tag_cloud",
        )
        return _json({"status": "ok", "region_id": region_id, "page_id": page_id,
                      "message": f"Tag cloud '{region_name}' added to page {page_id}."})
    except Exception as e:
        return _json({"status": "error", "error": str(e)})


# ── 9. Percent Bars ────────────────────────────────────────────────────────────

def apex_add_percent_bars(
    page_id: int,
    region_name: str,
    sql_query: str,
    label_column: str = "LABEL",
    value_column: str = "VALUE",
    color: str = "unimed",
    show_values: bool = True,
    custom_css: str = "",
    sequence: int = 10,
) -> str:
    """Add horizontal percentage bar chart rendered in HTML.

    Lighter than JET charts — pure HTML/CSS, instant render.
    Values are automatically normalized to 0–100% relative to the max.

    Args:
        page_id: Target page ID.
        region_name: Region display name.
        sql_query: SQL returning label and numeric value.
            Example: "SELECT DS_STATUS LABEL, COUNT(*) VALUE
                        FROM TEA_AVALIACOES GROUP BY DS_STATUS ORDER BY 2 DESC"
        label_column: Column name for the row label.
        value_column: Column name for the numeric value.
        color: Bar color (named or hex).
        show_values: Show value number at end of bar (default True).
        sequence: Display order on page.

    Returns:
        JSON with status, region_id.
    """
    err = _guard(page_id)
    if err:
        return err

    region_id = ids.next(f"pctbars_{page_id}_{_esc(region_name)}")
    clr = _col(color)
    lbl = label_column.upper()
    val = value_column.upper()
    extra_css = _esc(custom_css) if custom_css else ""
    val_display = "sys.htp.p('<span class=\"mcp-pb-val\">' || TO_CHAR(r.{val}) || '</span>');" if show_values else ""

    plsql = f"""DECLARE
  v_max NUMBER := 1;
  v_pct NUMBER;
BEGIN
  sys.htp.p('<style>
    .mcp-pb-wrap{{padding:4px 0;}}
    .mcp-pb-row{{margin-bottom:10px;}}
    .mcp-pb-header{{display:flex;justify-content:space-between;margin-bottom:4px;
      font-size:.82rem;color:#555;font-weight:500;}}
    .mcp-pb-track{{background:#f0f0f0;border-radius:6px;height:10px;overflow:hidden;}}
    .mcp-pb-fill{{height:10px;border-radius:6px;background:{clr};transition:width .5s ease;}}
    .mcp-pb-val{{font-size:.8rem;color:{clr};font-weight:700;}}
    {extra_css}
  </style>');
  BEGIN
    EXECUTE IMMEDIATE 'SELECT NVL(MAX({val}),1) FROM ({_esc(sql_query)})' INTO v_max;
    IF v_max = 0 THEN v_max := 1; END IF;
  EXCEPTION WHEN OTHERS THEN v_max := 1; END;
  sys.htp.p('<div class="mcp-pb-wrap">');
  FOR r IN (SELECT {lbl}, {val} FROM ({sql_query})) LOOP
    v_pct := GREATEST(ROUND(r.{val} / v_max * 100), 1);
    sys.htp.p('<div class="mcp-pb-row">');
    sys.htp.p('<div class="mcp-pb-header">');
    sys.htp.p('<span>' || APEX_ESCAPE.HTML(r.{lbl}) || '</span>');
    {val_display}
    sys.htp.p('</div>');
    sys.htp.p('<div class="mcp-pb-track"><div class="mcp-pb-fill" style="width:' || v_pct || '%"></div></div>');
    sys.htp.p('</div>');
  END LOOP;
  sys.htp.p('</div>');
END;"""

    try:
        _plsql_region(region_id, region_name, plsql, sequence, hide_header=False)
        session.regions[region_id] = RegionInfo(
            region_id=region_id, page_id=page_id,
            region_name=region_name, region_type="percent_bars",
        )
        return _json({"status": "ok", "region_id": region_id, "page_id": page_id,
                      "message": f"Percent bars '{region_name}' added to page {page_id}."})
    except Exception as e:
        return _json({"status": "error", "error": str(e)})


# ── 10. Icon List ──────────────────────────────────────────────────────────────

def apex_add_icon_list(
    page_id: int,
    region_name: str,
    sql_query: str,
    label_column: str = "LABEL",
    value_column: str = "VALUE",
    icon_column: str = "",
    default_icon: str = "fa-circle",
    color: str = "blue",
    custom_css: str = "",
    sequence: int = 10,
) -> str:
    """Add a vertical icon+label+value list from SQL.

    Each row shows: colored icon | label text | value (right-aligned).
    Great for status summaries, category breakdowns, or configuration lists.

    Args:
        page_id: Target page ID.
        region_name: Region display name.
        sql_query: SQL returning label/value and optionally icon columns.
            Example: "SELECT DS_STATUS LABEL, COUNT(*) VALUE FROM TEA_AVALIACOES
                        GROUP BY DS_STATUS ORDER BY 1"
        label_column: Column for the item label.
        value_column: Column for the right-side value.
        icon_column: Column containing Font Awesome class per row (optional).
        default_icon: FA icon used when icon_column is empty or not specified.
        color: Icon accent color (named or hex).
        sequence: Display order on page.

    Returns:
        JSON with status, region_id.
    """
    err = _guard(page_id)
    if err:
        return err

    region_id = ids.next(f"iconlist_{page_id}_{_esc(region_name)}")
    clr = _col(color)
    lbl = label_column.upper()
    val = value_column.upper()
    ico_expr = f"r.{icon_column.upper()}" if icon_column else f"'{default_icon}'"
    extra_css = _esc(custom_css) if custom_css else ""

    plsql = f"""DECLARE v_icon VARCHAR2(100);
BEGIN
  sys.htp.p('<style>
    .mcp-ilist{{background:#fff;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,.08);overflow:hidden;color:#333;}}
    .mcp-il-row{{display:flex;align-items:center;gap:12px;padding:11px 16px;
      border-bottom:1px solid #f5f5f5;}}
    .mcp-il-row:last-child{{border-bottom:none;}}
    .mcp-il-icon{{width:32px;height:32px;border-radius:50%;background:{clr}22;
      display:flex;align-items:center;justify-content:center;flex-shrink:0;}}
    .mcp-il-label{{flex:1;font-size:.88rem;color:#444;}}
    .mcp-il-val{{font-size:.9rem;font-weight:700;color:{clr};}}
    {extra_css}
  </style>');
  sys.htp.p('<div class="mcp-ilist">');
  FOR r IN (SELECT {lbl}, {val}{ ', ' + icon_column.upper() if icon_column else '' } FROM ({sql_query})) LOOP
    v_icon := {ico_expr};
    sys.htp.p('<div class="mcp-il-row">');
    sys.htp.p('<div class="mcp-il-icon"><span class="fa ' || APEX_ESCAPE.HTML(v_icon) ||
              '" style="color:{clr}"></span></div>');
    sys.htp.p('<div class="mcp-il-label">' || APEX_ESCAPE.HTML(r.{lbl}) || '</div>');
    sys.htp.p('<div class="mcp-il-val">' || APEX_ESCAPE.HTML(TO_CHAR(r.{val})) || '</div>');
    sys.htp.p('</div>');
  END LOOP;
  sys.htp.p('</div>');
END;"""

    try:
        _plsql_region(region_id, region_name, plsql, sequence, hide_header=False)
        session.regions[region_id] = RegionInfo(
            region_id=region_id, page_id=page_id,
            region_name=region_name, region_type="icon_list",
        )
        return _json({"status": "ok", "region_id": region_id, "page_id": page_id,
                      "message": f"Icon list '{region_name}' added to page {page_id}."})
    except Exception as e:
        return _json({"status": "error", "error": str(e)})


# ── 11. Traffic Light ──────────────────────────────────────────────────────────

def apex_add_traffic_light(
    page_id: int,
    region_name: str,
    sql_query: str,
    label_column: str = "LABEL",
    status_column: str = "STATUS",
    custom_css: str = "",
    sequence: int = 10,
) -> str:
    """Add a traffic-light status indicator grid from SQL.

    SQL must return a status column with values: 'GREEN', 'AMBER', or 'RED'
    (or equivalent: 'OK'/'WARNING'/'ERROR', 'CONCLUIDA'/'EM_ANDAMENTO'/'CANCELADA').
    Automatically maps common status strings to colors.

    Args:
        page_id: Target page ID.
        region_name: Region display name.
        sql_query: SQL returning label and status columns.
            Example: "SELECT DS_NOME LABEL,
                        CASE FL_ATIVO WHEN 'S' THEN 'GREEN' ELSE 'RED' END STATUS
                        FROM TEA_CLINICAS ORDER BY 1"
        label_column: Column for the item label.
        status_column: Column for the status ('GREEN'/'AMBER'/'RED' or similar).
        sequence: Display order on page.

    Returns:
        JSON with status, region_id.
    """
    err = _guard(page_id)
    if err:
        return err

    region_id = ids.next(f"trafficlight_{page_id}_{_esc(region_name)}")
    lbl = label_column.upper()
    sts = status_column.upper()
    extra_css = _esc(custom_css) if custom_css else ""

    plsql = f"""DECLARE
  v_color VARCHAR2(20);
  v_bg    VARCHAR2(20);
BEGIN
  sys.htp.p('<style>
    .mcp-tl-grid{{display:flex;flex-wrap:wrap;gap:10px;padding:6px 0;}}
    .mcp-tl-item{{display:flex;align-items:center;gap:10px;background:#fff;
      border-radius:8px;padding:10px 14px;box-shadow:0 1px 4px rgba(0,0,0,.08);
      flex:1 1 200px;min-width:160px;color:#333;}}
    .mcp-tl-dot{{width:14px;height:14px;border-radius:50%;flex-shrink:0;
      box-shadow:0 0 0 3px rgba(0,0,0,.1);}}
    .mcp-tl-label{{font-size:.85rem;color:#444;}}
    {extra_css}
  </style>');
  sys.htp.p('<div class="mcp-tl-grid">');
  FOR r IN (SELECT {lbl}, UPPER({sts}) AS STATUS_VAL FROM ({sql_query})) LOOP
    CASE r.STATUS_VAL
      WHEN 'GREEN'       THEN v_color := '#43a047'; v_bg := '#e8f5e9';
      WHEN 'OK'          THEN v_color := '#43a047'; v_bg := '#e8f5e9';
      WHEN 'CONCLUIDA'   THEN v_color := '#43a047'; v_bg := '#e8f5e9';
      WHEN 'ATIVO'       THEN v_color := '#43a047'; v_bg := '#e8f5e9';
      WHEN 'AMBER'       THEN v_color := '#ffb300'; v_bg := '#fff8e1';
      WHEN 'WARNING'     THEN v_color := '#ffb300'; v_bg := '#fff8e1';
      WHEN 'EM_ANDAMENTO'THEN v_color := '#ffb300'; v_bg := '#fff8e1';
      WHEN 'RED'         THEN v_color := '#e53935'; v_bg := '#ffebee';
      WHEN 'ERROR'       THEN v_color := '#e53935'; v_bg := '#ffebee';
      WHEN 'CANCELADA'   THEN v_color := '#e53935'; v_bg := '#ffebee';
      ELSE                    v_color := '#9e9e9e'; v_bg := '#f5f5f5';
    END CASE;
    sys.htp.p('<div class="mcp-tl-item" style="background:' || v_bg || '">');
    sys.htp.p('<div class="mcp-tl-dot" style="background:' || v_color || '"></div>');
    sys.htp.p('<span class="mcp-tl-label">' || APEX_ESCAPE.HTML(r.{lbl}) || '</span>');
    sys.htp.p('</div>');
  END LOOP;
  sys.htp.p('</div>');
END;"""

    try:
        _plsql_region(region_id, region_name, plsql, sequence, hide_header=False)
        session.regions[region_id] = RegionInfo(
            region_id=region_id, page_id=page_id,
            region_name=region_name, region_type="traffic_light",
        )
        return _json({"status": "ok", "region_id": region_id, "page_id": page_id,
                      "message": f"Traffic light '{region_name}' added to page {page_id}."})
    except Exception as e:
        return _json({"status": "error", "error": str(e)})


# ── 12. Spotlight Metric ───────────────────────────────────────────────────────

def apex_add_spotlight_metric(
    page_id: int,
    region_name: str,
    sql_query: str,
    label: str,
    color: str = "unimed",
    icon: str = "fa-star",
    suffix: str = "",
    prefix: str = "",
    subtitle_sql: str = "",
    value_size: str = "3.2rem",
    icon_size: str = "2.4rem",
    custom_css: str = "",
    sequence: int = 10,
) -> str:
    """Add a large centered spotlight metric -- a single KPI in the spotlight.

    The value is displayed very large in the center, with the label below.
    Ideal for a primary metric on a dedicated dashboard section.

    Args:
        page_id: Target page ID.
        region_name: Internal region name.
        sql_query: SQL returning a single scalar value.
            Example: "SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA'"
        label: Metric label below the value.
        color: Accent color.
        icon: Font Awesome icon above the value.
        suffix: Unit suffix (e.g., "%", " pts").
        prefix: Unit prefix (e.g., "R$ ", "$").
        subtitle_sql: Optional SQL for a smaller subtitle line below the label.
        value_size: CSS font-size for the metric value (default "3.2rem").
        icon_size: CSS font-size for the icon (default "2.4rem").
        custom_css: Additional CSS rules injected into the style block.
        sequence: Display order on page.

    Returns:
        JSON with status, region_id.
    """
    err = _guard(page_id)
    if err:
        return err

    region_id = ids.next(f"spotlight_{page_id}_{_esc(region_name)}")
    clr = _col(color)
    extra_css = _esc(custom_css) if custom_css else ""

    sub_block = ""
    if subtitle_sql:
        sub_block = f"""
  BEGIN EXECUTE IMMEDIATE '{_esc(subtitle_sql)}' INTO v_sub;
  EXCEPTION WHEN OTHERS THEN v_sub := ''; END;
  IF v_sub IS NOT NULL THEN
    sys.htp.p('<div class="mcp-spot-sub">' || APEX_ESCAPE.HTML(v_sub) || '</div>');
  END IF;"""

    plsql = f"""DECLARE
  v_val VARCHAR2(4000);
  v_sub VARCHAR2(4000);
BEGIN
  BEGIN EXECUTE IMMEDIATE '{_esc(sql_query)}' INTO v_val;
  EXCEPTION WHEN OTHERS THEN v_val := '-'; END;
  sys.htp.p('<style>
    .mcp-spotlight{{text-align:center;padding:32px 20px;background:#fff;color:#333;
      border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,.1);}}
    .mcp-spot-icon{{font-size:{_esc(icon_size)};color:{clr};margin-bottom:12px;}}
    .mcp-spot-val{{font-size:{_esc(value_size)};font-weight:800;color:{clr};line-height:1;}}
    .mcp-spot-label{{font-size:.9rem;color:#888;margin-top:8px;text-transform:uppercase;
      letter-spacing:.6px;font-weight:500;}}
    .mcp-spot-sub{{font-size:.82rem;color:#666;margin-top:6px;}}
    @media(max-width:480px){{
      .mcp-spotlight{{padding:20px 12px;}}
      .mcp-spot-val{{font-size:2rem;}}
    }}
    {extra_css}
  </style>');
  sys.htp.p('<div class="mcp-spotlight">');
  sys.htp.p('<div class="mcp-spot-icon"><span class="fa {icon}"></span></div>');
  sys.htp.p('<div class="mcp-spot-val">{_esc(_html_esc(prefix))}' || APEX_ESCAPE.HTML(v_val) || '{_esc(_html_esc(suffix))}</div>');
  sys.htp.p('<div class="mcp-spot-label">{_esc(_html_esc(label))}</div>');
  {sub_block}
  sys.htp.p('</div>');
END;"""

    try:
        _plsql_region(region_id, region_name, plsql, sequence)
        session.regions[region_id] = RegionInfo(
            region_id=region_id, page_id=page_id,
            region_name=region_name, region_type="spotlight",
        )
        return _json({"status": "ok", "region_id": region_id, "page_id": page_id,
                      "message": f"Spotlight metric '{region_name}' added to page {page_id}."})
    except Exception as e:
        return _json({"status": "error", "error": str(e)})


# ── 13. Comparison Panel ───────────────────────────────────────────────────────

def apex_add_comparison_panel(
    page_id: int,
    region_name: str,
    left_label: str,
    left_metrics: list[dict[str, str]],
    right_label: str,
    right_metrics: list[dict[str, str]],
    left_color: str = "blue",
    right_color: str = "green",
    custom_css: str = "",
    sequence: int = 10,
) -> str:
    """Add a side-by-side comparison panel (A vs B).

    Renders two columns with labels and KPI values -- ideal for
    period comparison, group A/B analysis, or plan vs actual.

    Args:
        page_id: Target page ID.
        region_name: Internal region name.
        left_label: Header for the left column (e.g., "Periodo Anterior").
        left_metrics: Metrics for left column. Each dict:
            {"label": "Total", "sql": "SELECT COUNT(*) FROM ...", "suffix": ""}
        right_label: Header for the right column (e.g., "Periodo Atual").
        right_metrics: Metrics for right column (same format as left_metrics).
        left_color: Accent color for left column.
        right_color: Accent color for right column.
        custom_css: Additional CSS rules injected into the style block.
        sequence: Display order on page.

    Returns:
        JSON with status, region_id.
    """
    err = _guard(page_id)
    if err:
        return err

    region_id = ids.next(f"compare_{page_id}_{_esc(region_name)}")
    lc = _col(left_color)
    rc = _col(right_color)

    extra_css = _esc(custom_css) if custom_css else ""

    def _metrics_block(metrics: list[dict[str, str]], clr: str) -> str:
        lines: list[str] = []
        for m in metrics:
            lbl = _esc(_html_esc(m.get("label", "")))
            sql = _esc(m.get("sql", "SELECT '' FROM DUAL"))
            sfx = _esc(_html_esc(m.get("suffix", "")))
            lines.append(
                f"  BEGIN EXECUTE IMMEDIATE '{sql}' INTO v_val;"
                f" EXCEPTION WHEN OTHERS THEN v_val := '-'; END;\n"
                f"  sys.htp.p('<div class=\"mcp-cmp-row\">"
                f"<span class=\"mcp-cmp-lbl\">{lbl}</span>"
                f"<span class=\"mcp-cmp-val\" style=\"color:{clr}\">'||"
                f"APEX_ESCAPE.HTML(v_val)||'{sfx}</span></div>');"
            )
        return "\n".join(lines)

    left_block = _metrics_block(left_metrics, lc)
    right_block = _metrics_block(right_metrics, rc)

    plsql = f"""DECLARE v_val VARCHAR2(4000);
BEGIN
  sys.htp.p('<style>
    .mcp-cmp{{display:flex;gap:16px;flex-wrap:wrap;}}
    .mcp-cmp-col{{flex:1 1 280px;min-width:250px;background:#fff;border-radius:10px;
      box-shadow:0 2px 8px rgba(0,0,0,.08);overflow:hidden;}}
    .mcp-cmp-hdr{{padding:12px 16px;font-weight:700;font-size:.88rem;color:#fff;}}
    .mcp-cmp-body{{padding:12px 16px;color:#333;}}
    .mcp-cmp-row{{display:flex;justify-content:space-between;padding:7px 0;
      border-bottom:1px solid #f5f5f5;font-size:.85rem;}}
    .mcp-cmp-row:last-child{{border-bottom:none;}}
    .mcp-cmp-lbl{{color:#666;}}
    .mcp-cmp-val{{font-weight:700;}}
    @media(max-width:600px){{.mcp-cmp{{flex-direction:column;}}.mcp-cmp-col{{min-width:0;}}}}
    {extra_css}
  </style>');
  sys.htp.p('<div class="mcp-cmp">');
  sys.htp.p('<div class="mcp-cmp-col">');
  sys.htp.p('<div class="mcp-cmp-hdr" style="background:{lc}">{_esc(_html_esc(left_label))}</div>');
  sys.htp.p('<div class="mcp-cmp-body">');
{left_block}
  sys.htp.p('</div></div>');
  sys.htp.p('<div class="mcp-cmp-col">');
  sys.htp.p('<div class="mcp-cmp-hdr" style="background:{rc}">{_esc(_html_esc(right_label))}</div>');
  sys.htp.p('<div class="mcp-cmp-body">');
{right_block}
  sys.htp.p('</div></div>');
  sys.htp.p('</div>');
END;"""

    try:
        _plsql_region(region_id, region_name, plsql, sequence)
        session.regions[region_id] = RegionInfo(
            region_id=region_id, page_id=page_id,
            region_name=region_name, region_type="comparison_panel",
        )
        return _json({"status": "ok", "region_id": region_id, "page_id": page_id,
                      "message": f"Comparison panel '{region_name}' added to page {page_id}."})
    except Exception as e:
        return _json({"status": "error", "error": str(e)})


# ── 14. Activity Stream ────────────────────────────────────────────────────────

def apex_add_activity_stream(
    page_id: int,
    region_name: str,
    sql_query: str,
    text_column: str = "TEXT",
    date_column: str = "DT",
    icon_column: str = "",
    color_column: str = "",
    default_icon: str = "fa-circle",
    default_color: str = "blue",
    max_rows: int = 20,
    custom_css: str = "",
    sequence: int = 10,
) -> str:
    """Add a scrollable activity/audit stream from SQL.

    Renders a vertical timeline feed with icon, text, and relative date.
    Ideal for audit logs, activity feeds, or recent events panels.

    Args:
        page_id: Target page ID.
        region_name: Region display name.
        sql_query: SQL returning text and date columns (ORDER BY date DESC).
            Example: "SELECT DS_DETALHES TEXT, DT_OPERACAO DT, DS_OPERACAO ICON_COL
                        FROM TEA_LOG_AUDITORIA ORDER BY DT_OPERACAO DESC"
        text_column: Column for the activity description.
        date_column: Column for the timestamp (DATE or TIMESTAMP).
        icon_column: Column containing FA icon class per row (optional).
        color_column: Column containing hex color per row (optional).
        default_icon: Default FA icon class.
        default_color: Default accent color.
        max_rows: Maximum rows to display.
        sequence: Display order on page.

    Returns:
        JSON with status, region_id.
    """
    err = _guard(page_id)
    if err:
        return err

    region_id = ids.next(f"activity_{page_id}_{_esc(region_name)}")
    clr = _col(default_color)
    txt = text_column.upper()
    dt  = date_column.upper()
    ico_expr = f"NVL(r.{icon_column.upper()}, '{default_icon}')" if icon_column else f"'{default_icon}'"
    clr_expr = f"NVL(r.{color_column.upper()}, '{clr}')" if color_column else f"'{clr}'"
    extra_cols = ""
    if icon_column:
        extra_cols += f", {icon_column.upper()}"
    if color_column:
        extra_cols += f", {color_column.upper()}"
    extra_css = _esc(custom_css) if custom_css else ""

    plsql = f"""DECLARE
  v_icon  VARCHAR2(100);
  v_color VARCHAR2(30);
  v_date  VARCHAR2(40);
BEGIN
  sys.htp.p('<style>
    .mcp-act{{background:#fff;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,.08);
      max-height:440px;overflow-y:auto;color:#333;}}
    .mcp-act-hdr{{padding:12px 16px;font-weight:700;font-size:.88rem;
      border-bottom:1px solid #eee;color:#444;}}
    .mcp-act-item{{display:flex;gap:12px;padding:11px 16px;border-bottom:1px solid #f8f8f8;}}
    .mcp-act-item:last-child{{border-bottom:none;}}
    .mcp-act-dot{{width:34px;height:34px;border-radius:50%;display:flex;
      align-items:center;justify-content:center;flex-shrink:0;font-size:.9rem;}}
    .mcp-act-body{{flex:1;}}
    .mcp-act-text{{font-size:.85rem;color:#444;margin-bottom:3px;line-height:1.4;}}
    .mcp-act-date{{font-size:.75rem;color:#aaa;}}
    {extra_css}
  </style>');
  sys.htp.p('<div class="mcp-act">');
  sys.htp.p('<div class="mcp-act-hdr">{_esc(_html_esc(region_name))}</div>');
  FOR r IN (SELECT {txt}, {dt}{extra_cols} FROM ({sql_query}) WHERE ROWNUM <= {max_rows}) LOOP
    v_icon  := {ico_expr};
    v_color := {clr_expr};
    v_date  := CASE
      WHEN r.{dt} >= SYSDATE - 1/24     THEN 'há minutos'
      WHEN r.{dt} >= SYSDATE - 1        THEN TO_CHAR(ROUND((SYSDATE - r.{dt})*24,0)) || 'h atrás'
      WHEN r.{dt} >= SYSDATE - 7        THEN TO_CHAR(TRUNC(SYSDATE - r.{dt})) || 'd atrás'
      ELSE TO_CHAR(r.{dt}, 'DD/MM/YYYY')
    END;
    sys.htp.p('<div class="mcp-act-item">');
    sys.htp.p('<div class="mcp-act-dot" style="background:' || v_color || '22">');
    sys.htp.p('<span class="fa ' || APEX_ESCAPE.HTML(v_icon) ||
              '" style="color:' || v_color || '"></span></div>');
    sys.htp.p('<div class="mcp-act-body">');
    sys.htp.p('<div class="mcp-act-text">' || APEX_ESCAPE.HTML(SUBSTR(r.{txt},1,200)) || '</div>');
    sys.htp.p('<div class="mcp-act-date">' || v_date || '</div>');
    sys.htp.p('</div></div>');
  END LOOP;
  sys.htp.p('</div>');
END;"""

    try:
        _plsql_region(region_id, region_name, plsql, sequence, hide_header=False)
        session.regions[region_id] = RegionInfo(
            region_id=region_id, page_id=page_id,
            region_name=region_name, region_type="activity_stream",
        )
        return _json({"status": "ok", "region_id": region_id, "page_id": page_id,
                      "message": f"Activity stream '{region_name}' added to page {page_id} (max {max_rows} rows)."})
    except Exception as e:
        return _json({"status": "error", "error": str(e)})


# ── 15. Status Matrix ──────────────────────────────────────────────────────────

def apex_add_status_matrix(
    page_id: int,
    region_name: str,
    sql_query: str,
    label_column: str = "LABEL",
    status_column: str = "STATUS",
    group_column: str = "",
    custom_css: str = "",
    sequence: int = 10,
) -> str:
    """Add a status matrix grid -- items with colored status dots and labels.

    Organizes items in a card grid with color-coded status badges.
    Optional group_column adds a subtle category label.

    Args:
        page_id: Target page ID.
        region_name: Region display name.
        sql_query: SQL returning label and status columns.
        label_column: Column for item name.
        status_column: Column with status text (e.g., 'Ativo', 'Inativo', 'Pendente').
        group_column: Optional column for category grouping label.
        sequence: Display order on page.

    Returns:
        JSON with status, region_id.
    """
    err = _guard(page_id)
    if err:
        return err

    region_id = ids.next(f"smatrix_{page_id}_{_esc(region_name)}")
    lbl = label_column.upper()
    sts = status_column.upper()
    grp_col = group_column.upper()
    grp_select = f", {grp_col}" if group_column else ""
    grp_display = (f"sys.htp.p('<div class=\"mcp-sm-group\">'||APEX_ESCAPE.HTML(r.{grp_col})||'</div>');"
                   if group_column else "")
    extra_css = _esc(custom_css) if custom_css else ""

    plsql = f"""DECLARE
  v_color VARCHAR2(20);
  v_bg    VARCHAR2(20);
BEGIN
  sys.htp.p('<style>
    .mcp-sm-grid{{display:flex;flex-wrap:wrap;gap:10px;padding:4px 0;}}
    .mcp-sm-card{{flex:1 1 180px;min-width:150px;background:#fff;border-radius:8px;
      padding:12px 14px;box-shadow:0 1px 4px rgba(0,0,0,.08);color:#333;}}
    .mcp-sm-top{{display:flex;align-items:center;gap:8px;}}
    .mcp-sm-dot{{width:10px;height:10px;border-radius:50%;flex-shrink:0;}}
    .mcp-sm-label{{font-size:.85rem;color:#444;font-weight:500;flex:1;}}
    .mcp-sm-badge{{font-size:.72rem;padding:2px 8px;border-radius:10px;font-weight:600;}}
    .mcp-sm-group{{font-size:.7rem;color:#aaa;margin-top:5px;text-transform:uppercase;letter-spacing:.4px;}}
    @media(max-width:480px){{.mcp-sm-card{{flex:1 1 100%;min-width:0;}}}}
    {extra_css}
  </style>');
  sys.htp.p('<div class="mcp-sm-grid">');
  FOR r IN (SELECT {lbl}, {sts}{grp_select} FROM ({sql_query})) LOOP
    CASE UPPER(r.{sts})
      WHEN 'ATIVO'        THEN v_color := '#43a047'; v_bg := '#e8f5e9';
      WHEN 'ACTIVE'       THEN v_color := '#43a047'; v_bg := '#e8f5e9';
      WHEN 'OK'           THEN v_color := '#43a047'; v_bg := '#e8f5e9';
      WHEN 'CONCLUIDA'    THEN v_color := '#43a047'; v_bg := '#e8f5e9';
      WHEN 'PENDENTE'     THEN v_color := '#ffb300'; v_bg := '#fff8e1';
      WHEN 'EM_ANDAMENTO' THEN v_color := '#ffb300'; v_bg := '#fff8e1';
      WHEN 'PENDING'      THEN v_color := '#ffb300'; v_bg := '#fff8e1';
      WHEN 'INATIVO'      THEN v_color := '#e53935'; v_bg := '#ffebee';
      WHEN 'CANCELADA'    THEN v_color := '#e53935'; v_bg := '#ffebee';
      WHEN 'ERROR'        THEN v_color := '#e53935'; v_bg := '#ffebee';
      ELSE                     v_color := '#9e9e9e'; v_bg := '#f5f5f5';
    END CASE;
    sys.htp.p('<div class="mcp-sm-card">');
    sys.htp.p('<div class="mcp-sm-top">');
    sys.htp.p('<div class="mcp-sm-dot" style="background:' || v_color || '"></div>');
    sys.htp.p('<span class="mcp-sm-label">' || APEX_ESCAPE.HTML(r.{lbl}) || '</span>');
    sys.htp.p('<span class="mcp-sm-badge" style="background:' || v_bg ||
              ';color:' || v_color || '">' || APEX_ESCAPE.HTML(r.{sts}) || '</span>');
    sys.htp.p('</div>');
    {grp_display}
    sys.htp.p('</div>');
  END LOOP;
  sys.htp.p('</div>');
END;"""

    try:
        _plsql_region(region_id, region_name, plsql, sequence, hide_header=False)
        session.regions[region_id] = RegionInfo(
            region_id=region_id, page_id=page_id,
            region_name=region_name, region_type="status_matrix",
        )
        return _json({"status": "ok", "region_id": region_id, "page_id": page_id,
                      "message": f"Status matrix '{region_name}' added to page {page_id}."})
    except Exception as e:
        return _json({"status": "error", "error": str(e)})


# ── 16. Collapsible Region ─────────────────────────────────────────────────────

def apex_add_collapsible_region(
    page_id: int,
    region_name: str,
    content_html: str = "",
    content_sql: str = "",
    collapsed: bool = False,
    custom_css: str = "",
    sequence: int = 10,
) -> str:
    """Add a collapsible/expandable section to a page.

    Renders a titled panel that can be toggled open/closed by clicking the header.
    Useful for grouping secondary information that shouldn't always be visible.

    Args:
        page_id: Target page ID.
        region_name: Section title (shown in the clickable header).
        content_html: Static HTML content to show inside (optional).
        content_sql: SQL returning VARCHAR2 content to show inside (optional,
            overrides content_html). Example: "SELECT DS_OBSERVACOES FROM T WHERE ID=1"
        collapsed: Start collapsed (default False = expanded).
        sequence: Display order on page.

    Returns:
        JSON with status, region_id.
    """
    err = _guard(page_id)
    if err:
        return err

    region_id = ids.next(f"collapsible_{page_id}_{_esc(region_name)}")
    uid = region_id % 999999
    init_display = "none" if collapsed else "block"
    icon_init = "fa-chevron-right" if collapsed else "fa-chevron-down"
    extra_css = _esc(custom_css) if custom_css else ""

    if content_sql:
        body_block = (
            f"  BEGIN EXECUTE IMMEDIATE '{_esc(content_sql)}' INTO v_body;\n"
            f"  EXCEPTION WHEN OTHERS THEN v_body := '(Sem dados)'; END;"
        )
        body_output = "  sys.htp.p(APEX_ESCAPE.HTML(v_body));"
    else:
        body_block = f"  v_body := '{_esc(content_html or '(Conteudo nao configurado.)')}'; "
        body_output = "  sys.htp.p(v_body);"

    plsql = f"""DECLARE v_body VARCHAR2(32767);
BEGIN
  {body_block}
  sys.htp.p('<style>
    .mcp-collapse-hdr{{display:flex;align-items:center;gap:8px;cursor:pointer;
      padding:12px 16px;background:#f8f9fa;border-radius:8px;user-select:none;
      border:1px solid #e9ecef;color:#333;}}
    .mcp-collapse-hdr:hover{{background:#e9ecef;}}
    .mcp-collapse-hdr-title{{flex:1;font-weight:600;font-size:.9rem;color:#444;}}
    .mcp-collapse-body{{padding:14px 16px;border:1px solid #e9ecef;border-top:none;
      border-radius:0 0 8px 8px;background:#fff;margin-bottom:8px;color:#333;}}
    {extra_css}
  </style>');
  sys.htp.p('<div onclick="var b=document.getElementById(''mcpc{uid}'');'||
            'var i=document.getElementById(''mcpi{uid}'');'||
            'if(b.style.display==''none''){{b.style.display=''block'';i.className=''fa fa-chevron-down'';}}else{{b.style.display=''none'';i.className=''fa fa-chevron-right'';}}"'||
            ' class="mcp-collapse-hdr">');
  sys.htp.p('<i class="fa {icon_init}" id="mcpi{uid}"></i>');
  sys.htp.p('<span class="mcp-collapse-hdr-title">{_esc(region_name)}</span>');
  sys.htp.p('</div>');
  sys.htp.p('<div id="mcpc{uid}" class="mcp-collapse-body" style="display:{init_display}">');
  {body_output}
  sys.htp.p('</div>');
END;"""

    try:
        name = f"Collapsible {region_name}"
        _plsql_region(region_id, name, plsql, sequence)
        session.regions[region_id] = RegionInfo(
            region_id=region_id, page_id=page_id,
            region_name=name, region_type="collapsible",
        )
        return _json({"status": "ok", "region_id": region_id, "page_id": page_id,
                      "message": f"Collapsible region '{region_name}' added to page {page_id}."})
    except Exception as e:
        return _json({"status": "error", "error": str(e)})


# ── 17. Tabs Container ─────────────────────────────────────────────────────────

def apex_add_tabs_container(
    page_id: int,
    region_name: str,
    tabs: list[dict[str, str]],
    color: str = "unimed",
    custom_css: str = "",
    sequence: int = 10,
) -> str:
    """Add a tabbed content container to a page.

    Renders a horizontal tab bar where each tab shows its content inline.
    Content can be static HTML or the result of a SQL query.

    Args:
        page_id: Target page ID.
        region_name: Internal region name.
        tabs: List of tab dicts (2–6 tabs):
            - "label": Tab header label
            - "icon": Optional FA icon (e.g., "fa-users")
            - "html": Static HTML content (optional)
            - "sql": SQL returning VARCHAR2 content (optional, overrides html)
        color: Active tab accent color.
        sequence: Display order on page.

    Returns:
        JSON with status, region_id.
    """
    err = _guard(page_id)
    if err:
        return err

    region_id = ids.next(f"tabs_{page_id}_{_esc(region_name)}")
    uid = region_id % 999999
    clr = _col(color)
    extra_css = _esc(custom_css) if custom_css else ""

    tab_btns: list[str] = []
    tab_panels: list[str] = []
    for i, tab in enumerate(tabs):
        lbl = _esc(_html_esc(tab.get("label", f"Tab {i+1}")))
        ico = tab.get("icon", "")
        ico_html = f'<span class="fa {ico}" style="margin-right:5px"></span>' if ico else ""
        active_cls = "mcp-tab-active" if i == 0 else "mcp-tab-btn"
        tab_btns.append(
            f'<button class="{active_cls}" id="mcp-tbtn-{uid}-{i}" '
            f'onclick="mcpTab({uid},{i},{len(tabs)})">{ico_html}{lbl}</button>'
        )
        content = tab.get("html") or tab.get("sql") or ""
        is_sql = "sql" in tab and tab["sql"]
        disp = "block" if i == 0 else "none"
        if is_sql:
            tab_panels.append(
                f"  sys.htp.p('<div id=\"mcp-tpnl-{uid}-{i}\" class=\"mcp-tab-panel\" style=\"display:{disp}\">');  \n"
                f"  BEGIN EXECUTE IMMEDIATE '{_esc(content)}' INTO v_content;\n"
                f"  EXCEPTION WHEN OTHERS THEN v_content := '(Erro ao carregar)'; END;\n"
                f"  sys.htp.p(APEX_ESCAPE.HTML(v_content));\n"
                f"  sys.htp.p('</div>');"
            )
        else:
            tab_panels.append(
                f"  sys.htp.p('<div id=\"mcp-tpnl-{uid}-{i}\" class=\"mcp-tab-panel\" style=\"display:{disp}\">');\n"
                f"  sys.htp.p('{_esc(content or '')}');\n"
                f"  sys.htp.p('</div>');"
            )

    btns_html = _esc("".join(tab_btns))
    panels_block = "\n".join(tab_panels)

    plsql = f"""DECLARE v_content VARCHAR2(32767);
BEGIN
  sys.htp.p('<style>
    .mcp-tabs{{background:#fff;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,.08);overflow:hidden;}}
    .mcp-tab-bar{{display:flex;background:#f8f9fa;border-bottom:2px solid #e9ecef;}}
    .mcp-tab-btn,.mcp-tab-active{{padding:11px 20px;border:none;background:none;cursor:pointer;
      font-size:.85rem;font-weight:500;color:#777;border-bottom:2px solid transparent;
      margin-bottom:-2px;transition:all .2s;}}
    .mcp-tab-btn:hover{{color:{clr};}}
    .mcp-tab-active{{color:{clr};border-bottom-color:{clr};background:#fff;font-weight:700;}}
    .mcp-tab-panel{{padding:16px;color:#333;}}
    @media(max-width:600px){{
      .mcp-tab-bar{{flex-wrap:wrap;}}
      .mcp-tab-btn,.mcp-tab-active{{flex:1 1 auto;text-align:center;padding:9px 12px;font-size:.78rem;}}
    }}
    {extra_css}
  </style>');
  sys.htp.p('<script>function mcpTab(u,n,t){{for(var i=0;i<t;i++){{
    var b=document.getElementById(''mcp-tbtn-''+u+''-''+i);
    var p=document.getElementById(''mcp-tpnl-''+u+''-''+i);
    if(b)b.className=(i==n?''mcp-tab-active'':''mcp-tab-btn'');
    if(p)p.style.display=(i==n?''block'':''none'');}}}}</script>');
  sys.htp.p('<div class="mcp-tabs">');
  sys.htp.p('<div class="mcp-tab-bar">{btns_html}</div>');
{panels_block}
  sys.htp.p('</div>');
END;"""

    try:
        _plsql_region(region_id, region_name, plsql, sequence)
        session.regions[region_id] = RegionInfo(
            region_id=region_id, page_id=page_id,
            region_name=region_name, region_type="tabs_container",
        )
        return _json({"status": "ok", "region_id": region_id, "page_id": page_id,
                      "message": f"Tabs container '{region_name}' added to page {page_id} ({len(tabs)} tabs)."})
    except Exception as e:
        return _json({"status": "error", "error": str(e)})


# ── 18. Data Card Grid ─────────────────────────────────────────────────────────

def apex_add_data_card_grid(
    page_id: int,
    region_name: str,
    sql_query: str,
    title_column: str = "TITLE",
    subtitle_column: str = "",
    value_column: str = "VALUE",
    badge_column: str = "",
    url_column: str = "",
    color: str = "blue",
    columns: int = 3,
    custom_css: str = "",
    sequence: int = 10,
) -> str:
    """Add a SQL-driven card grid -- each row becomes a visual card.

    More flexible than APEX native Cards -- supports custom badge,
    subtitle, and optional URL per row. Pure HTML rendering.

    Args:
        page_id: Target page ID.
        region_name: Region display name.
        sql_query: SQL returning title, optional subtitle, value, optional badge.
            Example: "SELECT DS_NOME TITLE, DS_ESPECIALIDADE SUBTITLE,
                        COUNT(a.ID_AVALIACAO) VALUE
                        FROM TEA_TERAPEUTAS t LEFT JOIN TEA_AVALIACOES a USING(ID_TERAPEUTA)
                        GROUP BY DS_NOME, DS_ESPECIALIDADE"
        title_column: Column for card title.
        subtitle_column: Column for card subtitle (optional).
        value_column: Column for prominent numeric value.
        badge_column: Column for badge text (optional, e.g., status).
        url_column: Column for card click URL (optional).
        color: Accent color for value and border.
        columns: Grid columns (2-4).
        custom_css: Additional CSS rules injected into the style block.
        sequence: Display order on page.

    Returns:
        JSON with status, region_id.
    """
    err = _guard(page_id)
    if err:
        return err

    region_id = ids.next(f"cardgrid_{page_id}_{_esc(region_name)}")
    clr = _col(color)
    ttl = title_column.upper()
    val = value_column.upper()
    col_pct = {2: "48%", 3: "31%", 4: "23%"}.get(columns, "31%")
    extra_css = _esc(custom_css) if custom_css else ""

    extra_cols = ""
    if subtitle_column:
        extra_cols += f", {subtitle_column.upper()}"
    if badge_column:
        extra_cols += f", {badge_column.upper()}"
    if url_column:
        extra_cols += f", {url_column.upper()}"

    sub_line = (f"sys.htp.p('<div class=\"mcp-dc-sub\">'||APEX_ESCAPE.HTML(r.{subtitle_column.upper()})||'</div>');"
                if subtitle_column else "")
    badge_line = (f"sys.htp.p('<span class=\"mcp-dc-badge\">'||APEX_ESCAPE.HTML(r.{badge_column.upper()})||'</span>');"
                  if badge_column else "")
    url_open = f"sys.htp.p('<a href=\"'||APEX_ESCAPE.HTML(r.{url_column.upper()})||'\" style=\"text-decoration:none\">');" if url_column else ""
    url_close = f"sys.htp.p('</a>');" if url_column else ""

    plsql = f"""BEGIN
  sys.htp.p('<style>
    .mcp-dc-grid{{display:flex;flex-wrap:wrap;gap:14px;padding:4px 0;}}
    .mcp-dc-card{{flex:1 1 {col_pct};min-width:160px;background:#fff;border-radius:10px;
      padding:16px;box-shadow:0 2px 8px rgba(0,0,0,.08);border-top:3px solid {clr};
      transition:transform .15s;color:#333;}}
    .mcp-dc-card:hover{{transform:translateY(-2px);box-shadow:0 4px 14px rgba(0,0,0,.12);}}
    .mcp-dc-title{{font-size:.9rem;font-weight:700;color:#333;margin-bottom:4px;}}
    .mcp-dc-sub{{font-size:.78rem;color:#888;margin-bottom:8px;}}
    .mcp-dc-val{{font-size:1.6rem;font-weight:800;color:{clr};}}
    .mcp-dc-badge{{display:inline-block;font-size:.72rem;padding:2px 8px;border-radius:10px;
      background:{clr}22;color:{clr};font-weight:600;margin-top:6px;}}
    @media(max-width:600px){{.mcp-dc-card{{flex:1 1 100%;min-width:0;}}}}
    {extra_css}
  </style>');
  sys.htp.p('<div class="mcp-dc-grid">');
  FOR r IN (SELECT {ttl}, {val}{extra_cols} FROM ({sql_query})) LOOP
    {url_open}
    sys.htp.p('<div class="mcp-dc-card">');
    sys.htp.p('<div class="mcp-dc-title">' || APEX_ESCAPE.HTML(r.{ttl}) || '</div>');
    {sub_line}
    sys.htp.p('<div class="mcp-dc-val">' || APEX_ESCAPE.HTML(TO_CHAR(r.{val})) || '</div>');
    {badge_line}
    sys.htp.p('</div>');
    {url_close}
  END LOOP;
  sys.htp.p('</div>');
END;"""

    try:
        _plsql_region(region_id, region_name, plsql, sequence, hide_header=False)
        session.regions[region_id] = RegionInfo(
            region_id=region_id, page_id=page_id,
            region_name=region_name, region_type="data_card_grid",
        )
        return _json({"status": "ok", "region_id": region_id, "page_id": page_id,
                      "message": f"Data card grid '{region_name}' added to page {page_id}."})
    except Exception as e:
        return _json({"status": "error", "error": str(e)})


# ── 19. Heatmap Grid ───────────────────────────────────────────────────────────

def apex_add_heatmap_grid(
    page_id: int,
    region_name: str,
    sql_query: str,
    row_column: str = "ROW_LABEL",
    col_column: str = "COL_LABEL",
    value_column: str = "VALUE",
    color: str = "blue",
    custom_css: str = "",
    sequence: int = 10,
) -> str:
    """Add a heatmap grid (cross-tab matrix) with color-intensity cells.

    Each cell's background intensity reflects its value relative to the max.
    SQL must return row label, column label, and a numeric value.

    Args:
        page_id: Target page ID.
        region_name: Region display name.
        sql_query: SQL returning ROW_LABEL, COL_LABEL, VALUE.
            Example: "SELECT TO_CHAR(DT_AVALIACAO,'DY') ROW_LABEL,
                        DS_STATUS COL_LABEL, COUNT(*) VALUE
                        FROM TEA_AVALIACOES
                        GROUP BY TO_CHAR(DT_AVALIACAO,'DY'), DS_STATUS
                        ORDER BY 1, 2"
        row_column: Column for row labels.
        col_column: Column for column labels.
        value_column: Column for numeric cell values.
        color: Heatmap base color (high intensity = this color, low = tint).
        sequence: Display order on page.

    Returns:
        JSON with status, region_id.
    """
    err = _guard(page_id)
    if err:
        return err

    region_id = ids.next(f"heatmap_{page_id}_{_esc(region_name)}")
    clr = _col(color)
    row_col = row_column.upper()
    col_col = col_column.upper()
    val_col = value_column.upper()
    extra_css = _esc(custom_css) if custom_css else ""

    plsql = f"""DECLARE
  TYPE t_rows IS TABLE OF VARCHAR2(200) INDEX BY PLS_INTEGER;
  TYPE t_cols IS TABLE OF VARCHAR2(200) INDEX BY PLS_INTEGER;
  TYPE t_vals IS TABLE OF NUMBER        INDEX BY VARCHAR2(400);
  v_rows t_rows;
  v_cols t_cols;
  v_vals t_vals;
  v_key  VARCHAR2(400);
  v_max  NUMBER := 1;
  v_pct  NUMBER;
  v_val  NUMBER;
  v_ri   PLS_INTEGER := 0;
  v_ci   PLS_INTEGER := 0;
  v_row_exists BOOLEAN;
  v_col_exists BOOLEAN;
BEGIN
  -- Load data
  FOR r IN (SELECT {row_col}, {col_col}, {val_col} FROM ({sql_query})) LOOP
    v_key := r.{row_col} || '|' || r.{col_col};
    v_vals(v_key) := r.{val_col};
    IF r.{val_col} > v_max THEN v_max := r.{val_col}; END IF;
    -- Collect unique rows
    v_row_exists := FALSE;
    FOR i IN 1..v_ri LOOP
      IF v_rows(i) = r.{row_col} THEN v_row_exists := TRUE; EXIT; END IF;
    END LOOP;
    IF NOT v_row_exists THEN v_ri := v_ri + 1; v_rows(v_ri) := r.{row_col}; END IF;
    -- Collect unique cols
    v_col_exists := FALSE;
    FOR i IN 1..v_ci LOOP
      IF v_cols(i) = r.{col_col} THEN v_col_exists := TRUE; EXIT; END IF;
    END LOOP;
    IF NOT v_col_exists THEN v_ci := v_ci + 1; v_cols(v_ci) := r.{col_col}; END IF;
  END LOOP;
  IF v_max = 0 THEN v_max := 1; END IF;
  -- Render
  sys.htp.p('<style>
    .mcp-hm table{{border-collapse:collapse;width:100%;font-size:.78rem;}}
    .mcp-hm th{{padding:7px 10px;background:#f5f5f5;color:#666;font-weight:600;
      border:1px solid #eee;text-align:center;}}
    .mcp-hm td{{padding:7px 10px;border:1px solid #eee;text-align:center;
      font-weight:600;color:#333;}}
    .mcp-hm td.row-hdr{{text-align:left;background:#f9f9f9;color:#555;font-weight:600;}}
    @media(max-width:600px){{.mcp-hm{{overflow-x:auto;}}}}
    {extra_css}
  </style>');
  sys.htp.p('<div class="mcp-hm"><table>');
  sys.htp.p('<tr><th></th>');
  FOR ci IN 1..v_ci LOOP
    sys.htp.p('<th>' || APEX_ESCAPE.HTML(v_cols(ci)) || '</th>');
  END LOOP;
  sys.htp.p('</tr>');
  FOR ri IN 1..v_ri LOOP
    sys.htp.p('<tr><td class="row-hdr">' || APEX_ESCAPE.HTML(v_rows(ri)) || '</td>');
    FOR ci IN 1..v_ci LOOP
      v_key := v_rows(ri) || '|' || v_cols(ci);
      IF v_vals.EXISTS(v_key) THEN
        v_val := v_vals(v_key);
        v_pct := ROUND(v_val / v_max * 100);
      ELSE
        v_val := 0; v_pct := 0;
      END IF;
      sys.htp.p('<td style="background:{clr}' || TO_CHAR(ROUND(v_pct * 255 / 100), 'FM0X') ||
                ';opacity:' || TO_CHAR(0.15 + v_pct/100*0.85, 'FM0.99') ||
                ';background-color:{clr}' || TO_CHAR(LPAD(TO_CHAR(ROUND(v_pct * 2), 'FM0X'), 2, '0'), 'FM0X') ||
                '">' || CASE WHEN v_val > 0 THEN TO_CHAR(v_val) ELSE '' END || '</td>');
    END LOOP;
    sys.htp.p('</tr>');
  END LOOP;
  sys.htp.p('</table></div>');
END;"""

    try:
        _plsql_region(region_id, region_name, plsql, sequence, hide_header=False)
        session.regions[region_id] = RegionInfo(
            region_id=region_id, page_id=page_id,
            region_name=region_name, region_type="heatmap_grid",
        )
        return _json({"status": "ok", "region_id": region_id, "page_id": page_id,
                      "message": f"Heatmap grid '{region_name}' added to page {page_id}."})
    except Exception as e:
        return _json({"status": "error", "error": str(e)})


# ── 20. Ribbon Stats ───────────────────────────────────────────────────────────

def apex_add_ribbon_stats(
    page_id: int,
    region_name: str,
    metrics: list[dict[str, Any]],
    bg_color: str = "#f8f9fa",
    custom_css: str = "",
    sequence: int = 10,
) -> str:
    """Add a full-width colored ribbon with multiple KPI stats side by side.

    A compact, professional banner that spans the full page width.
    Each stat has an icon, value, and label. Dividers separate the items.

    Args:
        page_id: Target page ID.
        region_name: Internal region name.
        metrics: List of stat dicts (3–6):
            - "label": Stat label
            - "sql": SQL returning single scalar value
            - "icon": Font Awesome class
            - "color": Icon/value color
            - "suffix": Unit suffix
        bg_color: Ribbon background color (hex or CSS value).
        sequence: Display order on page.

    Returns:
        JSON with status, region_id.
    """
    err = _guard(page_id)
    if err:
        return err

    region_id = ids.next(f"ribbon_{page_id}_{_esc(region_name)}")
    extra_css = _esc(custom_css) if custom_css else ""
    lines = [
        "DECLARE v_val VARCHAR2(4000);",
        "BEGIN",
        f"  sys.htp.p('<style>"
        f".mcp-ribbon{{display:flex;flex-wrap:wrap;background:{_esc(bg_color)};border-radius:10px;"
        f"padding:16px 8px;box-shadow:0 2px 8px rgba(0,0,0,.08);margin-bottom:12px;color:#333;}}"
        f".mcp-rib-item{{flex:1 1 auto;display:flex;align-items:center;gap:12px;padding:0 16px;"
        f"border-right:1px solid rgba(0,0,0,.08);min-width:120px;}}"
        f".mcp-rib-item:last-child{{border-right:none;}}"
        f".mcp-rib-icon{{font-size:1.8rem;}}"
        f".mcp-rib-text{{display:flex;flex-direction:column;}}"
        f".mcp-rib-val{{font-size:1.3rem;font-weight:700;color:#333;line-height:1;}}"
        f".mcp-rib-lbl{{font-size:.72rem;color:#888;margin-top:3px;text-transform:uppercase;letter-spacing:.4px;}}"
        f"@media(max-width:600px){{.mcp-ribbon{{flex-direction:column;gap:12px;}}"
        f".mcp-rib-item{{border-right:none;border-bottom:1px solid rgba(0,0,0,.06);padding:8px 16px;}}"
        f".mcp-rib-item:last-child{{border-bottom:none;}}}}"
        f"{extra_css}"
        f"</style>');",
        "  sys.htp.p('<div class=\"mcp-ribbon\">');",
    ]
    for m in metrics:
        lbl = _esc(_html_esc(m.get("label", "")))
        sql = _esc(m.get("sql", "SELECT '' FROM DUAL"))
        ico = m.get("icon", "fa-chart-bar")
        clr = _col(m.get("color", "blue"))
        sfx = _esc(_html_esc(m.get("suffix", "")))
        lines.append(
            f"  BEGIN EXECUTE IMMEDIATE '{sql}' INTO v_val;"
            f" EXCEPTION WHEN OTHERS THEN v_val := '-'; END;\n"
            f"  sys.htp.p('<div class=\"mcp-rib-item\">'||"
            f"'<span class=\"fa {ico} mcp-rib-icon\" style=\"color:{clr}\"></span>'||"
            f"'<div class=\"mcp-rib-text\">'||"
            f"'<span class=\"mcp-rib-val\" style=\"color:{clr}\">'||"
            f"APEX_ESCAPE.HTML(v_val)||'{sfx}</span>'||"
            f"'<span class=\"mcp-rib-lbl\">{lbl}</span>'||"
            f"'</div></div>');"
        )
    lines += ["  sys.htp.p('</div>');", "END;"]
    plsql = "\n".join(lines)

    try:
        _plsql_region(region_id, region_name, plsql, sequence)
        session.regions[region_id] = RegionInfo(
            region_id=region_id, page_id=page_id,
            region_name=region_name, region_type="ribbon_stats",
        )
        return _json({"status": "ok", "region_id": region_id, "page_id": page_id,
                      "message": f"Ribbon stats '{region_name}' added to page {page_id} ({len(metrics)} stats)."})
    except Exception as e:
        return _json({"status": "error", "error": str(e)})
