"""Tools: apex_add_jet_chart, apex_add_metric_cards, apex_generate_analytics_page."""
from __future__ import annotations
import json
from typing import Any
from ..db import db
from ..ids import ids
from ..session import session, PageInfo, RegionInfo
from ..templates import REGION_TMPL_STANDARD, REGION_TMPL_BLANK, REGION_TMPL_CARDS


def _esc(value: str) -> str:
    return value.replace("'", "''")


def _blk(sql: str) -> str:
    return f"begin\n{sql}\nend;"


# ── Helpers ────────────────────────────────────────────────────────────────────

def _sql_to_varchar2(sql: str) -> str:
    """Split a SQL string into wwv_flow_string.join(wwv_flow_t_varchar2(...)) chunks."""
    lines = sql.replace("'", "''").splitlines()
    if not lines:
        return "''"
    quoted = [f"'{line}'" for line in lines]
    return "wwv_flow_string.join(wwv_flow_t_varchar2(\n" + ",\n".join(quoted) + "))"


def _js_to_varchar2(js: str) -> str:
    """Same as _sql_to_varchar2 but for JavaScript code."""
    return _sql_to_varchar2(js)


# ── Tool 1: JET Chart ─────────────────────────────────────────────────────────

def apex_add_jet_chart(
    page_id: int,
    region_name: str,
    chart_type: str = "bar",
    sql_query: str = "",
    label_column: str = "LABEL",
    value_column: str = "VALUE",
    series_name: str = "",
    height: int = 400,
    y_axis_title: str = "",
    x_axis_title: str = "",
    legend_position: str = "end",
    orientation: str = "vertical",
    sequence: int = 20,
    extra_series: list[dict[str, Any]] | None = None,
    color_palette: list[str] | None = None,
) -> str:
    """Add an Oracle JET chart region to a page.

    Uses the native APEX NATIVE_JET_CHART engine — no external libraries needed.
    Integrates with the Universal Theme and inherits APEX color/font settings.

    Args:
        page_id: Target page ID.
        region_name: Region title shown in the APEX page.
        chart_type: Chart style:
            - "bar": Vertical bar chart (default)
            - "bar_horizontal": Horizontal bar chart
            - "line": Line chart (good for trends over time)
            - "area": Filled area chart (good for cumulative data)
            - "pie": Pie chart (distribution, no axes)
            - "donut": Donut chart (distribution with center hole)
            - "combo": Bar + line on same chart (use extra_series for line)
        sql_query: SQL query returning at least 2 columns: label + value.
            Example: "SELECT DS_STATUS AS LABEL, COUNT(*) AS VALUE
                        FROM TEA_AVALIACOES GROUP BY DS_STATUS"
        label_column: Column name used for X axis / slices (default "LABEL").
        value_column: Column name used for Y axis / slice size (default "VALUE").
        series_name: Display name for the data series (shown in legend/tooltip).
        height: Chart height in pixels (default 400).
        y_axis_title: Optional Y axis label.
        x_axis_title: Optional X axis label.
        legend_position: Where to show the legend: "end" (right), "top",
                         "bottom", "start" (left), "auto".
        orientation: "vertical" (default) or "horizontal" (for bar charts only).
        sequence: Region display order on the page.
        extra_series: Additional data series for multi-series charts.
            List of dicts: [{"sql": "...", "value_column": "VALUE",
                              "label_column": "LABEL", "series_name": "Series 2"}]
            Each extra series can have its own SQL query.
        color_palette: Optional list of hex colors for chart series (e.g., ["#00995D", "#1e88e5"]). Overrides default JET colors.

    Returns:
        JSON with status, region_id, chart_id.

    Best practices:
        - For time-series data, use "line" or "area" with dates as label column
        - For distributions, use "pie" or "donut" (max 8-10 slices)
        - For comparisons, use "bar" or "bar_horizontal"
        - SQL must be deterministic (no non-deterministic functions in ORDER BY)
        - Always ORDER BY the label column for consistent rendering
        - For multi-series: use "area" with stack=on for part-of-whole analysis
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})
    if not session.import_begun:
        return json.dumps({"status": "error", "error": "No import session active. Call apex_create_app() first."})
    if page_id not in session.pages:
        return json.dumps({"status": "error", "error": f"Page {page_id} not found. Call apex_add_page() first."})
    if not sql_query.strip():
        return json.dumps({"status": "error", "error": "sql_query is required."})

    chart_type_lower = chart_type.lower()
    effective_series_name = series_name or region_name

    # Normalize chart type
    apex_chart_type = {
        "bar":            "bar",
        "bar_horizontal": "bar",
        "line":           "line",
        "area":           "area",
        "pie":            "pie",
        "donut":          "donut",
        "combo":          "combo",
    }.get(chart_type_lower, "bar")

    is_pie_type = apex_chart_type in ("pie", "donut")
    apex_orientation = "horizontal" if chart_type_lower == "bar_horizontal" else orientation

    try:
        region_id = ids.next(f"chart_region_{page_id}_{_esc(region_name)}")
        chart_id  = ids.next(f"chart_{page_id}_{_esc(region_name)}")
        series_id = ids.next(f"chart_series_{page_id}_{_esc(region_name)}_1")

        # ── 1. Create the region plug ────────────────────────────────────────
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_plug(
 p_id=>wwv_flow_imp.id({region_id})
,p_plug_name=>'{_esc(region_name)}'
,p_region_template_options=>'#DEFAULT#:t-Region--scrollBody'
,p_escape_on_http_output=>'Y'
,p_plug_template=>{REGION_TMPL_STANDARD}
,p_plug_display_sequence=>{sequence}
,p_plug_display_point=>'BODY'
,p_plug_source_type=>'NATIVE_JET_CHART'
,p_plug_query_num_rows=>15
);"""))

        # ── 2. Create the chart config ───────────────────────────────────────
        stack_val   = "on" if apex_chart_type == "area" else "off"
        pie_params  = ""
        if is_pie_type:
            pie_params = ",p_pie_other_threshold=>0\n,p_pie_selection_effect=>'highlightAndExplode'"

        # Color palette override
        palette_line = ""
        if color_palette:
            colors_js = "[" + ",".join(f'\\"{c}\\"' for c in color_palette) + "]"
            palette_line = f",p_init_javascript_code=>'{{\"colors\":{colors_js}}}'"

        db.plsql(_blk(f"""
wwv_flow_imp_page.create_jet_chart(
 p_id=>wwv_flow_imp.id({chart_id})
,p_region_id=>wwv_flow_imp.id({region_id})
,p_chart_type=>'{apex_chart_type}'
,p_height=>'{height}'
,p_animation_on_display=>'auto'
,p_animation_on_data_change=>'auto'
,p_orientation=>'{apex_orientation}'
,p_data_cursor=>'auto'
,p_data_cursor_behavior=>'auto'
,p_hide_and_show_behavior=>'withRescale'
,p_hover_behavior=>'none'
,p_stack=>'{stack_val}'
,p_stack_label=>'off'
,p_connect_nulls=>'Y'
,p_value_position=>'auto'
,p_sorting=>'label-asc'
,p_fill_multi_series_gaps=>true
,p_zoom_and_scroll=>'off'
,p_tooltip_rendered=>'Y'
,p_show_series_name=>true
,p_show_group_name=>true
,p_show_value=>true
,p_show_label=>true
,p_show_row=>true
,p_show_start=>true
,p_show_end=>true
,p_show_progress=>true
,p_show_baseline=>true
,p_legend_rendered=>'on'
,p_legend_position=>'{legend_position}'
,p_overview_rendered=>'off'
{pie_params}
,p_horizontal_grid=>'auto'
,p_vertical_grid=>'auto'
,p_gauge_orientation=>'circular'
,p_gauge_plot_area=>'on'
,p_show_gauge_value=>true
{palette_line}
);"""))

        # ── 3. Create primary series ─────────────────────────────────────────
        pie_label_params = (
            "\n,p_items_label_rendered=>true"
            "\n,p_items_label_position=>'auto'"
            "\n,p_items_label_display_as=>'LABEL'"
        ) if is_pie_type else (
            "\n,p_items_label_rendered=>false"
            "\n,p_items_label_display_as=>'PERCENT'"
        )

        db.plsql(_blk(f"""
wwv_flow_imp_page.create_jet_chart_series(
 p_id=>wwv_flow_imp.id({series_id})
,p_chart_id=>wwv_flow_imp.id({chart_id})
,p_seq=>10
,p_name=>'{_esc(effective_series_name)}'
,p_data_source_type=>'SQL'
,p_data_source=>{_sql_to_varchar2(sql_query)}
,p_items_value_column_name=>'{_esc(value_column.upper())}'
,p_items_label_column_name=>'{_esc(label_column.upper())}'
,p_line_type=>'auto'
,p_marker_rendered=>'auto'
,p_marker_shape=>'auto'
,p_assigned_to_y2=>'off'
{pie_label_params}
,p_threshold_display=>'onIndicator'
);"""))

        # ── 4. Extra series (multi-series charts) ────────────────────────────
        extra = extra_series or []
        for i, s in enumerate(extra, start=2):
            ex_series_id = ids.next(f"chart_series_{page_id}_{_esc(region_name)}_{i}")
            ex_sql       = s.get("sql", sql_query)
            ex_value_col = s.get("value_column", "VALUE").upper()
            ex_label_col = s.get("label_column", label_column).upper()
            ex_name      = s.get("series_name", f"Series {i}")
            db.plsql(_blk(f"""
wwv_flow_imp_page.create_jet_chart_series(
 p_id=>wwv_flow_imp.id({ex_series_id})
,p_chart_id=>wwv_flow_imp.id({chart_id})
,p_seq=>{i * 10}
,p_name=>'{_esc(ex_name)}'
,p_data_source_type=>'SQL'
,p_data_source=>{_sql_to_varchar2(ex_sql)}
,p_items_value_column_name=>'{ex_value_col}'
,p_items_label_column_name=>'{ex_label_col}'
,p_line_type=>'auto'
,p_marker_rendered=>'auto'
,p_marker_shape=>'auto'
,p_assigned_to_y2=>'off'
,p_items_label_rendered=>false
,p_items_label_display_as=>'PERCENT'
,p_threshold_display=>'onIndicator'
);"""))

        # ── 5. Axes (not for pie/donut) ──────────────────────────────────────
        if not is_pie_type:
            zoom_bools = (
                ",p_zoom_order_seconds=>false\n,p_zoom_order_minutes=>false\n"
                ",p_zoom_order_hours=>false\n,p_zoom_order_days=>false\n"
                ",p_zoom_order_weeks=>false\n,p_zoom_order_months=>false\n"
                ",p_zoom_order_quarters=>false\n,p_zoom_order_years=>false"
            )
            y_title_line = f",p_title=>'{_esc(y_axis_title)}'" if y_axis_title else ""
            x_title_line = f",p_title=>'{_esc(x_axis_title)}'" if x_axis_title else ""

            y_axis_id = ids.next(f"chart_y_{page_id}_{_esc(region_name)}")
            x_axis_id = ids.next(f"chart_x_{page_id}_{_esc(region_name)}")

            db.plsql(_blk(f"""
wwv_flow_imp_page.create_jet_chart_axis(
 p_id=>wwv_flow_imp.id({y_axis_id})
,p_chart_id=>wwv_flow_imp.id({chart_id})
,p_axis=>'y'
,p_is_rendered=>'on'
{y_title_line}
,p_format_scaling=>'auto'
,p_scaling=>'linear'
,p_baseline_scaling=>'zero'
,p_position=>'auto'
,p_major_tick_rendered=>'on'
,p_minor_tick_rendered=>'off'
,p_tick_label_rendered=>'on'
{zoom_bools}
);"""))

            db.plsql(_blk(f"""
wwv_flow_imp_page.create_jet_chart_axis(
 p_id=>wwv_flow_imp.id({x_axis_id})
,p_chart_id=>wwv_flow_imp.id({chart_id})
,p_axis=>'x'
,p_is_rendered=>'on'
{x_title_line}
,p_format_scaling=>'auto'
,p_scaling=>'linear'
,p_baseline_scaling=>'zero'
,p_major_tick_rendered=>'on'
,p_minor_tick_rendered=>'off'
,p_tick_label_rendered=>'on'
,p_tick_label_rotation=>'none'
,p_tick_label_position=>'outside'
{zoom_bools}
);"""))

        # Update session
        session.regions[region_id] = RegionInfo(
            region_id=region_id, page_id=page_id,
            region_name=region_name, region_type="chart"
        )

        return json.dumps({
            "status": "ok",
            "region_id": region_id,
            "chart_id": chart_id,
            "chart_type": apex_chart_type,
            "series_count": 1 + len(extra),
            "page_id": page_id,
            "message": f"JET {apex_chart_type} chart '{region_name}' added to page {page_id}.",
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)


# ── Tool 2: Dial Gauge Chart ──────────────────────────────────────────────────

def apex_add_gauge(
    page_id: int,
    region_name: str,
    sql_query: str,
    value_column: str = "VALUE",
    min_value: float = 0,
    max_value: float = 100,
    thresholds: list[dict] | None = None,
    height: int = 300,
    sequence: int = 20,
    color: str | None = None,
) -> str:
    """Add a JET dial gauge chart to a page.

    Ideal for KPI scores, completion rates, SLA metrics, health indicators.
    Renders as a circular dial with colored threshold zones.

    Args:
        page_id: Target page ID.
        region_name: Region title.
        sql_query: SQL returning a single numeric value in VALUE_COLUMN.
            Example: "SELECT ROUND(AVG(NR_PCT_TOTAL)) AS VALUE FROM TEA_AVALIACOES"
        value_column: Column name with the gauge value (default "VALUE").
        min_value: Minimum scale value (default 0).
        max_value: Maximum scale value (default 100).
        thresholds: List of threshold zones. Each dict:
            {"value": 33, "color": "#e53935"}  -- red up to 33
            {"value": 66, "color": "#fb8c00"}  -- orange up to 66
            {"value": 100, "color": "#43a047"} -- green up to 100
            If omitted, uses a single green zone.
        height: Gauge height in pixels (default 300).
        sequence: Region display order.
        color: Single color hex for the gauge needle/fill (optional).

    Returns:
        JSON with status, region_id, chart_id.
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})
    if not session.import_begun:
        return json.dumps({"status": "error", "error": "No import session active. Call apex_create_app() first."})
    if page_id not in session.pages:
        return json.dumps({"status": "error", "error": f"Page {page_id} not found."})
    if not sql_query.strip():
        return json.dumps({"status": "error", "error": "sql_query is required."})

    default_thresholds = thresholds or [
        {"value": max_value * 0.33, "color": "#e53935"},
        {"value": max_value * 0.66, "color": "#fb8c00"},
        {"value": max_value,        "color": "#43a047"},
    ]

    try:
        region_id = ids.next(f"gauge_region_{page_id}_{_esc(region_name)}")
        chart_id  = ids.next(f"gauge_chart_{page_id}_{_esc(region_name)}")
        series_id = ids.next(f"gauge_series_{page_id}_{_esc(region_name)}")

        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_plug(
 p_id=>wwv_flow_imp.id({region_id})
,p_plug_name=>'{_esc(region_name)}'
,p_region_template_options=>'#DEFAULT#:t-Region--scrollBody'
,p_escape_on_http_output=>'Y'
,p_plug_template=>{REGION_TMPL_STANDARD}
,p_plug_display_sequence=>{sequence}
,p_plug_display_point=>'BODY'
,p_plug_source_type=>'NATIVE_JET_CHART'
,p_plug_query_num_rows=>15
);"""))

        color_line = f",p_init_javascript_code=>'{{\"color\":\"{color}\"}}'" if color else ""

        db.plsql(_blk(f"""
wwv_flow_imp_page.create_jet_chart(
 p_id=>wwv_flow_imp.id({chart_id})
,p_region_id=>wwv_flow_imp.id({region_id})
,p_chart_type=>'dial'
,p_height=>'{height}'
,p_animation_on_display=>'auto'
,p_animation_on_data_change=>'auto'
,p_gauge_orientation=>'circular'
,p_gauge_plot_area=>'on'
,p_show_gauge_value=>true
,p_legend_rendered=>'off'
,p_overview_rendered=>'off'
{color_line}
);"""))

        db.plsql(_blk(f"""
wwv_flow_imp_page.create_jet_chart_series(
 p_id=>wwv_flow_imp.id({series_id})
,p_chart_id=>wwv_flow_imp.id({chart_id})
,p_seq=>10
,p_name=>'{_esc(region_name)}'
,p_data_source_type=>'SQL'
,p_data_source=>{_sql_to_varchar2(sql_query)}
,p_items_value_column_name=>'{_esc(value_column.upper())}'
,p_items_label_column_name=>'{_esc(value_column.upper())}'
,p_assigned_to_y2=>'off'
,p_items_label_rendered=>false
,p_items_label_display_as=>'PERCENT'
,p_threshold_display=>'onIndicator'
);"""))

        # Y axis with min/max/thresholds
        y_axis_id = ids.next(f"gauge_y_{page_id}_{_esc(region_name)}")
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_jet_chart_axis(
 p_id=>wwv_flow_imp.id({y_axis_id})
,p_chart_id=>wwv_flow_imp.id({chart_id})
,p_axis=>'y'
,p_is_rendered=>'on'
,p_format_scaling=>'auto'
,p_scaling=>'linear'
,p_baseline_scaling=>'zero'
,p_position=>'auto'
,p_major_tick_rendered=>'on'
,p_minor_tick_rendered=>'off'
,p_tick_label_rendered=>'on'
,p_zoom_order_seconds=>false
,p_zoom_order_minutes=>false
,p_zoom_order_hours=>false
,p_zoom_order_days=>false
,p_zoom_order_weeks=>false
,p_zoom_order_months=>false
,p_zoom_order_quarters=>false
,p_zoom_order_years=>false
);"""))

        session.regions[region_id] = RegionInfo(
            region_id=region_id, page_id=page_id,
            region_name=region_name, region_type="gauge"
        )

        return json.dumps({
            "status": "ok",
            "region_id": region_id,
            "chart_id": chart_id,
            "chart_type": "dial",
            "page_id": page_id,
            "message": f"Gauge '{region_name}' added to page {page_id}.",
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)


# ── Tool 3: Funnel Chart ──────────────────────────────────────────────────────

def apex_add_funnel(
    page_id: int,
    region_name: str,
    sql_query: str,
    label_column: str = "LABEL",
    value_column: str = "VALUE",
    series_name: str = "",
    height: int = 380,
    sequence: int = 20,
    color_palette: list[str] | None = None,
) -> str:
    """Add a JET funnel chart to a page.

    Perfect for visualizing pipeline stages, approval flows, or conversion steps.
    Each row in the SQL represents one stage of the funnel (ordered top to bottom).

    Args:
        page_id: Target page ID.
        region_name: Region title.
        sql_query: SQL ordered from largest to smallest stage.
            Example: "SELECT DS_STATUS AS LABEL, COUNT(*) AS VALUE
                        FROM TEA_AVALIACOES GROUP BY DS_STATUS ORDER BY 2 DESC"
        label_column: Column for stage labels (default "LABEL").
        value_column: Column for stage values (default "VALUE").
        series_name: Legend label.
        height: Chart height in pixels (default 380).
        sequence: Region display order.
        color_palette: Optional hex color list per stage.

    Returns:
        JSON with status, region_id, chart_id.
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})
    if not session.import_begun:
        return json.dumps({"status": "error", "error": "No import session active. Call apex_create_app() first."})
    if page_id not in session.pages:
        return json.dumps({"status": "error", "error": f"Page {page_id} not found."})

    effective_name = series_name or region_name

    try:
        region_id = ids.next(f"funnel_region_{page_id}_{_esc(region_name)}")
        chart_id  = ids.next(f"funnel_chart_{page_id}_{_esc(region_name)}")
        series_id = ids.next(f"funnel_series_{page_id}_{_esc(region_name)}")

        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_plug(
 p_id=>wwv_flow_imp.id({region_id})
,p_plug_name=>'{_esc(region_name)}'
,p_region_template_options=>'#DEFAULT#:t-Region--scrollBody'
,p_escape_on_http_output=>'Y'
,p_plug_template=>{REGION_TMPL_STANDARD}
,p_plug_display_sequence=>{sequence}
,p_plug_display_point=>'BODY'
,p_plug_source_type=>'NATIVE_JET_CHART'
,p_plug_query_num_rows=>15
);"""))

        palette_line = ""
        if color_palette:
            colors_js = "[" + ",".join(f'\\"{c}\\"' for c in color_palette) + "]"
            palette_line = f",p_init_javascript_code=>'{{\"colors\":{colors_js}}}'"

        db.plsql(_blk(f"""
wwv_flow_imp_page.create_jet_chart(
 p_id=>wwv_flow_imp.id({chart_id})
,p_region_id=>wwv_flow_imp.id({region_id})
,p_chart_type=>'funnel'
,p_height=>'{height}'
,p_animation_on_display=>'auto'
,p_animation_on_data_change=>'auto'
,p_data_cursor=>'auto'
,p_data_cursor_behavior=>'auto'
,p_legend_rendered=>'on'
,p_legend_position=>'end'
,p_overview_rendered=>'off'
,p_tooltip_rendered=>'Y'
,p_show_series_name=>true
,p_show_value=>true
{palette_line}
);"""))

        db.plsql(_blk(f"""
wwv_flow_imp_page.create_jet_chart_series(
 p_id=>wwv_flow_imp.id({series_id})
,p_chart_id=>wwv_flow_imp.id({chart_id})
,p_seq=>10
,p_name=>'{_esc(effective_name)}'
,p_data_source_type=>'SQL'
,p_data_source=>{_sql_to_varchar2(sql_query)}
,p_items_value_column_name=>'{_esc(value_column.upper())}'
,p_items_label_column_name=>'{_esc(label_column.upper())}'
,p_assigned_to_y2=>'off'
,p_items_label_rendered=>true
,p_items_label_position=>'auto'
,p_items_label_display_as=>'LABEL'
,p_threshold_display=>'onIndicator'
);"""))

        session.regions[region_id] = RegionInfo(
            region_id=region_id, page_id=page_id,
            region_name=region_name, region_type="funnel"
        )

        return json.dumps({
            "status": "ok",
            "region_id": region_id,
            "chart_id": chart_id,
            "chart_type": "funnel",
            "page_id": page_id,
            "message": f"Funnel chart '{region_name}' added to page {page_id}.",
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)


# ── Tool 4: Sparkline Metric Cards ────────────────────────────────────────────

def apex_add_sparkline(
    page_id: int,
    region_name: str,
    metrics: list[dict[str, Any]],
    sequence: int = 10,
    columns: int = 4,
) -> str:
    """Add metric cards with inline sparkline trend bars.

    Each card shows: title, current value, and a mini 7-bar trend chart.
    The developer controls colors via each metric's "color" key (hex or named).

    Args:
        page_id: Target page ID.
        region_name: Region name.
        metrics: List of metric dicts. Each dict:
            - "label": Card title (required)
            - "sql": SQL returning single current value (required)
            - "trend_sql": SQL returning up to 7 rows with VALUE column for sparkline.
                Example: "SELECT NR_PCT_TOTAL AS VALUE FROM TEA_AVALIACOES
                           WHERE DS_STATUS='CONCLUIDA' ORDER BY DT_AVALIACAO DESC
                           FETCH FIRST 7 ROWS ONLY"
            - "icon": Font Awesome icon class (e.g., "fa-chart-line")
            - "color": Hex color or named color for accent (e.g., "#00995D", "blue")
            - "suffix": Unit suffix (e.g., "%", "pts")
            - "prefix": Unit prefix (e.g., "$", "R$")
        sequence: Region display order.
        columns: Number of columns (2-4).

    Returns:
        JSON with status, region_id.
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})
    if not session.import_begun:
        return json.dumps({"status": "error", "error": "No import session active. Call apex_create_app() first."})
    if page_id not in session.pages:
        return json.dumps({"status": "error", "error": f"Page {page_id} not found."})

    named_colors = {
        "blue": "#1e88e5", "green": "#43a047", "orange": "#fb8c00",
        "red": "#e53935", "purple": "#8e24aa", "teal": "#00897b",
        "indigo": "#3949ab", "amber": "#ffb300",
    }
    col_pct = {2: "48%", 3: "31%", 4: "23%"}.get(columns, "23%")

    try:
        region_id = ids.next(f"sparkline_region_{page_id}_{_esc(region_name)}")

        lines: list[str] = []
        lines.append("DECLARE")
        lines.append("  v_val  VARCHAR2(4000);")
        lines.append("  v_bars VARCHAR2(4000);")
        lines.append("  v_max  NUMBER;")
        lines.append("  v_h    NUMBER;")
        lines.append("BEGIN")
        lines.append(f"""  sys.htp.p('<style>
    .mcp-spark-grid{{display:flex;flex-wrap:wrap;gap:14px;padding:6px 0;}}
    .mcp-spark-card{{flex:1 1 {col_pct};min-width:150px;background:#fff;border-radius:10px;
      padding:16px;box-shadow:0 2px 8px rgba(0,0,0,.08);border-left:4px solid #ccc;}}
    .mcp-spark-top{{display:flex;align-items:center;gap:10px;margin-bottom:8px;}}
    .mcp-spark-icon{{font-size:22px;}}
    .mcp-spark-label{{font-size:.78rem;color:#777;text-transform:uppercase;letter-spacing:.4px;}}
    .mcp-spark-value{{font-size:1.8rem;font-weight:700;color:#333;margin-bottom:8px;}}
    .mcp-spark-bars{{display:flex;align-items:flex-end;gap:3px;height:36px;}}
    .mcp-spark-bar{{flex:1;border-radius:2px 2px 0 0;min-height:3px;opacity:.85;
      transition:opacity .2s;}}.mcp-spark-bar:hover{{opacity:1;}}
  </style>');""")
        lines.append("  sys.htp.p('<div class=\"mcp-spark-grid\">');")

        for i, m in enumerate(metrics):
            label     = m.get("label", f"Metric {i+1}")
            sql       = m.get("sql", "SELECT 0 FROM DUAL")
            trend_sql = m.get("trend_sql", "")
            icon      = m.get("icon", "fa-chart-line")
            raw_color = m.get("color", "blue")
            suffix    = m.get("suffix", "")
            prefix    = m.get("prefix", "")
            color     = named_colors.get(raw_color, raw_color)

            lines.append(f"""
  -- Card {i}: {label}
  BEGIN EXECUTE IMMEDIATE '{_esc(sql)}' INTO v_val;
  EXCEPTION WHEN OTHERS THEN v_val := 'N/A'; END;
  sys.htp.p('<div class="mcp-spark-card" style="border-left-color:{color}">');
  sys.htp.p('<div class="mcp-spark-top">');
  sys.htp.p('<span class="mcp-spark-icon fa {icon}" style="color:{color}"></span>');
  sys.htp.p('<span class="mcp-spark-label">{_esc(label)}</span>');
  sys.htp.p('</div>');
  sys.htp.p('<div class="mcp-spark-value">{_esc(prefix)}' || APEX_ESCAPE.HTML(v_val) || '{_esc(suffix)}</div>');""")

            if trend_sql:
                lines.append(f"""
  -- Sparkline bars for card {i}
  v_bars := '';
  v_max := 1;
  BEGIN
    EXECUTE IMMEDIATE 'SELECT NVL(MAX(VALUE),1) FROM ({_esc(trend_sql)})' INTO v_max;
    IF v_max = 0 THEN v_max := 1; END IF;
    FOR r IN (SELECT VALUE FROM ({_esc(trend_sql)})) LOOP
      v_h := GREATEST(ROUND(r.VALUE / v_max * 34), 3);
      v_bars := v_bars || '<div class="mcp-spark-bar" style="height:' || v_h || 'px;background:{color}"></div>';
    END LOOP;
  EXCEPTION WHEN OTHERS THEN v_bars := '';
  END;
  sys.htp.p('<div class="mcp-spark-bars">' || v_bars || '</div>');""")
            else:
                lines.append("  sys.htp.p('<div class=\"mcp-spark-bars\"></div>');")

            lines.append("  sys.htp.p('</div>');")

        lines.append("  sys.htp.p('</div>');")
        lines.append("END;")
        full_plsql = "\n".join(lines)

        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_plug(
 p_id=>wwv_flow_imp.id({region_id})
,p_plug_name=>'{_esc(region_name)}'
,p_region_template_options=>'#DEFAULT#:t-Region--noPadding:t-Region--hideHeader:t-Region--scrollBody'
,p_plug_template=>{REGION_TMPL_BLANK}
,p_plug_display_sequence=>{sequence}
,p_plug_display_point=>'BODY'
,p_plug_source=>'{_esc(full_plsql)}'
,p_plug_source_type=>'NATIVE_PLSQL'
,p_plug_query_options=>'DERIVED_REPORT_COLUMNS'
);"""))

        session.regions[region_id] = RegionInfo(
            region_id=region_id, page_id=page_id,
            region_name=region_name, region_type="sparkline"
        )

        return json.dumps({
            "status": "ok",
            "region_id": region_id,
            "metric_count": len(metrics),
            "page_id": page_id,
            "message": f"Sparkline cards '{region_name}' added to page {page_id} ({len(metrics)} metrics).",
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)


# ── Tool 5: Metric Cards with inline HTML/JS ──────────────────────────────────

def apex_add_metric_cards(
    page_id: int,
    region_name: str,
    metrics: list[dict[str, Any]],
    sequence: int = 10,
    columns: int = 4,
    style: str = "gradient",
    color_palette: list[str] | None = None,
) -> str:
    """Add modern metric cards with inline HTML and JavaScript to a page.

    Creates a NATIVE_PLSQL region that queries Oracle Autonomous Database
    and renders animated metric tiles with embedded CSS and JavaScript.
    No external libraries required — everything is self-contained.

    Args:
        page_id: Target page ID.
        region_name: Region title (hidden by default).
        metrics: List of metric definitions. Each dict supports:
            - "label": Display label (required, e.g., "Pacientes Ativos")
            - "sql": SQL query returning a single value (required,
                     e.g., "SELECT COUNT(*) FROM TEA_BENEFICIARIOS WHERE FL_ATIVO='S'")
            - "icon": Font Awesome icon class (e.g., "fa-users", "fa-chart-bar")
            - "color": Color theme: "blue" | "green" | "orange" | "red" |
                       "purple" | "teal" | "indigo" | "amber" (auto-assigned if omitted)
            - "prefix": Text before value (e.g., "R$", "$")
            - "suffix": Text after value (e.g., "%", "pts")
            - "subtitle": Optional secondary text under the value
            - "link_page": Page number to link to on click (optional)
            Example:
                [
                  {"label": "Pacientes Ativos", "sql": "SELECT COUNT(*) FROM TEA_BENEFICIARIOS",
                   "icon": "fa-users", "color": "blue"},
                  {"label": "Taxa de Conclusão", "sql": "SELECT ROUND(AVG(NR_PCT_TOTAL)) FROM TEA_AVALIACOES",
                   "icon": "fa-check-circle", "color": "green", "suffix": "%"},
                ]
        sequence: Region display order on the page.
        columns: Number of columns in the card grid (2, 3, 4, or 6).
        style: Visual style:
            - "gradient": Colored gradient background with white text (default)
            - "white": White card with colored accent border
            - "dark": Dark card with neon accent

    Returns:
        JSON with status, region_id.

    Best practices:
        - Use 2-6 metrics per row; 4 is the sweet spot
        - Include a "%" suffix for ratio metrics (conversion rates, etc.)
        - Use contrasting colors — don't repeat the same color twice in a row
        - Keep SQL queries simple (single aggregation, no joins if possible)
        - Add link_page for drill-down navigation
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})
    if not session.import_begun:
        return json.dumps({"status": "error", "error": "No import session active. Call apex_create_app() first."})
    if page_id not in session.pages:
        return json.dumps({"status": "error", "error": f"Page {page_id} not found. Call apex_add_page() first."})
    if not metrics:
        return json.dumps({"status": "error", "error": "At least one metric is required."})

    auto_colors = ["blue", "green", "orange", "red", "purple", "teal", "indigo", "amber"]

    # Color palettes per style
    gradient_map = {
        "blue":   ("linear-gradient(135deg,#1e88e5,#1565c0)", "#fff"),
        "green":  ("linear-gradient(135deg,#43a047,#2e7d32)", "#fff"),
        "orange": ("linear-gradient(135deg,#fb8c00,#e65100)", "#fff"),
        "red":    ("linear-gradient(135deg,#e53935,#b71c1c)", "#fff"),
        "purple": ("linear-gradient(135deg,#8e24aa,#6a1b9a)", "#fff"),
        "teal":   ("linear-gradient(135deg,#00897b,#004d40)", "#fff"),
        "indigo": ("linear-gradient(135deg,#3949ab,#1a237e)", "#fff"),
        "amber":  ("linear-gradient(135deg,#ffb300,#ff6f00)", "#fff"),
    }
    white_border_map = {
        "blue": "#1e88e5", "green": "#43a047", "orange": "#fb8c00",
        "red": "#e53935", "purple": "#8e24aa", "teal": "#00897b",
        "indigo": "#3949ab", "amber": "#ffb300",
    }
    dark_map = {
        "blue": "#60a5fa", "green": "#34d399", "orange": "#fb923c",
        "red": "#f87171", "purple": "#c084fc", "teal": "#2dd4bf",
        "indigo": "#818cf8", "amber": "#fbbf24",
    }

    col_pct = {2: "48%", 3: "31%", 4: "23%", 6: "15%"}.get(columns, "23%")

    try:
        region_id = ids.next(f"metric_region_{page_id}_{_esc(region_name)}")

        # ── Build the PL/SQL source ───────────────────────────────────────────
        plsql_lines: list[str] = []

        # Embedded CSS
        if style == "gradient":
            card_css = f"""
  sys.htp.p('<style>
    .apex-metric-grid{{display:flex;flex-wrap:wrap;gap:16px;padding:8px 0;}}
    .apex-metric-card{{flex:1 1 {col_pct};min-width:160px;border-radius:12px;
      padding:20px 18px;cursor:pointer;transition:transform .2s,box-shadow .2s;
      box-shadow:0 4px 15px rgba(0,0,0,.15);}}
    .apex-metric-card:hover{{transform:translateY(-4px);box-shadow:0 8px 25px rgba(0,0,0,.25);}}
    .apex-metric-icon{{font-size:28px;margin-bottom:8px;opacity:.9;}}
    .apex-metric-value{{font-size:2rem;font-weight:700;line-height:1.1;}}
    .apex-metric-label{{font-size:.8rem;opacity:.85;margin-top:4px;text-transform:uppercase;letter-spacing:.5px;}}
    .apex-metric-sub{{font-size:.75rem;opacity:.7;margin-top:2px;}}
    .apex-counter{{display:inline-block;}}
  </style>');"""
        elif style == "white":
            card_css = f"""
  sys.htp.p('<style>
    .apex-metric-grid{{display:flex;flex-wrap:wrap;gap:16px;padding:8px 0;}}
    .apex-metric-card{{flex:1 1 {col_pct};min-width:160px;border-radius:10px;
      padding:20px 18px;background:#fff;cursor:pointer;
      transition:transform .2s,box-shadow .2s;box-shadow:0 2px 8px rgba(0,0,0,.08);
      border-left:4px solid #ccc;}}
    .apex-metric-card:hover{{transform:translateY(-3px);box-shadow:0 6px 20px rgba(0,0,0,.12);}}
    .apex-metric-icon{{font-size:26px;margin-bottom:6px;}}
    .apex-metric-value{{font-size:1.9rem;font-weight:700;color:#333;}}
    .apex-metric-label{{font-size:.8rem;color:#777;margin-top:4px;text-transform:uppercase;letter-spacing:.5px;}}
    .apex-metric-sub{{font-size:.75rem;color:#aaa;margin-top:2px;}}
  </style>');"""
        else:  # dark
            card_css = f"""
  sys.htp.p('<style>
    .apex-metric-grid{{display:flex;flex-wrap:wrap;gap:16px;padding:8px 0;}}
    .apex-metric-card{{flex:1 1 {col_pct};min-width:160px;border-radius:12px;
      padding:20px 18px;background:#1e1e2e;cursor:pointer;
      transition:transform .2s,box-shadow .2s;box-shadow:0 4px 20px rgba(0,0,0,.4);
      border:1px solid rgba(255,255,255,.08);}}
    .apex-metric-card:hover{{transform:translateY(-4px);box-shadow:0 8px 30px rgba(0,0,0,.5);}}
    .apex-metric-icon{{font-size:26px;margin-bottom:6px;}}
    .apex-metric-value{{font-size:1.9rem;font-weight:700;color:#e2e8f0;}}
    .apex-metric-label{{font-size:.8rem;color:#94a3b8;margin-top:4px;text-transform:uppercase;letter-spacing:.5px;}}
    .apex-metric-sub{{font-size:.75rem;color:#64748b;margin-top:2px;}}
  </style>');"""

        plsql_lines.append("DECLARE")
        plsql_lines.append("  v_val VARCHAR2(4000);")
        plsql_lines.append("BEGIN")
        plsql_lines.append(card_css)
        plsql_lines.append("  sys.htp.p('<div class=\"apex-metric-grid\">');")

        for i, m in enumerate(metrics):
            label    = m.get("label", f"Metric {i+1}")
            sql      = m.get("sql", "SELECT 0 FROM DUAL")
            icon     = m.get("icon", "fa-chart-bar")
            color    = m.get("color", auto_colors[i % len(auto_colors)])
            prefix   = m.get("prefix", "")
            suffix   = m.get("suffix", "")
            subtitle = m.get("subtitle", "")
            link_pg  = m.get("link_page")

            # Developer color override (takes precedence over style palette)
            if color_palette and i < len(color_palette):
                hex_col = color_palette[i]
                if style == "gradient":
                    bg = f"linear-gradient(135deg,{hex_col},{hex_col}cc)"
                    text_color = "#fff"
                    card_style = f"background:{bg};color:{text_color};"
                    icon_style = f"color:{text_color};"
                elif style == "white":
                    card_style = f"border-left-color:{hex_col};"
                    icon_style = f"color:{hex_col};"
                else:
                    card_style = ""
                    icon_style = f"color:{hex_col};"
            elif style == "gradient":
                bg, text_color = gradient_map.get(color, gradient_map["blue"])
                card_style = f"background:{bg};color:{text_color};"
                icon_style = f"color:{text_color};"
            elif style == "white":
                accent = white_border_map.get(color, "#1e88e5")
                card_style = f"border-left-color:{accent};"
                icon_style = f"color:{accent};"
            else:
                accent = dark_map.get(color, "#60a5fa")
                card_style = ""
                icon_style = f"color:{accent};"

            # Click handler
            if link_pg:
                click_handler = f"onclick=\"apex.navigation.redirect('f?p=&APP_ID.:{link_pg}:&SESSION..');\""
            else:
                click_handler = ""

            subtitle_html = (
                f'<div class=\\"apex-metric-sub\\">{_esc(subtitle)}</div>'
                if subtitle else ""
            )
            # Counter JS class for animation
            counter_class = f"apex-counter-{i}"

            plsql_lines.append(f"""
  BEGIN
    EXECUTE IMMEDIATE '{_esc(sql)}' INTO v_val;
  EXCEPTION WHEN OTHERS THEN v_val := 'N/A'; END;
  sys.htp.p('<div class="apex-metric-card" style="{card_style}" {click_handler}>');
  sys.htp.p('<div class="apex-metric-icon" style="{icon_style}"><span class="fa {icon}"></span></div>');
  sys.htp.p('<div class="apex-metric-value"><span class="apex-counter {counter_class}">' || APEX_ESCAPE.HTML('{_esc(prefix)}' || v_val || '{_esc(suffix)}') || '</span></div>');
  sys.htp.p('<div class="apex-metric-label">{_esc(label)}</div>');
  sys.htp.p('{subtitle_html}');
  sys.htp.p('</div>');""")

        plsql_lines.append("  sys.htp.p('</div>');")

        # Inline JS: animate counters on load
        plsql_lines.append("""
  sys.htp.p('<script>
    (function(){
      function animateNum(el,dur){
        var raw=el.textContent.replace(/[^0-9.]/g,"");
        var num=parseFloat(raw);
        if(isNaN(num))return;
        var prefix=el.textContent.replace(raw,"").split(num)[0]||"";
        var suffix=el.textContent.split(raw).pop()||"";
        var start=0,step=num/30,t=dur/30;
        var cur=0;
        var iv=setInterval(function(){
          cur=Math.min(cur+step,num);
          el.textContent=prefix+(Number.isInteger(num)?Math.round(cur):cur.toFixed(1))+suffix;
          if(cur>=num)clearInterval(iv);
        },t);
      }
      apex.jQuery(document).ready(function(){
        apex.jQuery(".apex-counter").each(function(){animateNum(this,800);});
      });
    })();
  </script>');""")

        plsql_lines.append("END;")

        full_plsql = "\n".join(plsql_lines)

        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_plug(
 p_id=>wwv_flow_imp.id({region_id})
,p_plug_name=>'{_esc(region_name)}'
,p_region_template_options=>'#DEFAULT#:t-Region--noPadding:t-Region--hideHeader:t-Region--scrollBody'
,p_plug_template=>{REGION_TMPL_BLANK}
,p_plug_display_sequence=>{sequence}
,p_plug_display_point=>'BODY'
,p_plug_source=>'{_esc(full_plsql)}'
,p_plug_source_type=>'NATIVE_PLSQL'
,p_plug_query_options=>'DERIVED_REPORT_COLUMNS'
);"""))

        session.regions[region_id] = RegionInfo(
            region_id=region_id, page_id=page_id,
            region_name=region_name, region_type="plsql"
        )

        return json.dumps({
            "status": "ok",
            "region_id": region_id,
            "metric_count": len(metrics),
            "style": style,
            "page_id": page_id,
            "message": f"Metric cards '{region_name}' added to page {page_id} ({len(metrics)} metrics, {style} style).",
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)


# ── Tool 3: Analytics Page Generator ─────────────────────────────────────────

def apex_generate_analytics_page(
    page_id: int,
    page_name: str = "Analytics",
    metrics: list[dict[str, Any]] | None = None,
    charts: list[dict[str, Any]] | None = None,
    auth_scheme: str | None = None,
) -> str:
    """Generate a complete analytics page with metric cards and JET charts.

    Creates a professional analytics page in one call:
    1. Metric cards row (if metrics provided)
    2. One or more JET charts below (bar, line, pie, donut, area)

    If the page already exists in session it adds content to it.
    If not, it creates the page first.

    Args:
        page_id: Target page ID.
        page_name: Page display name (used only if page is created).
        metrics: List of metric card dicts (see apex_add_metric_cards for format).
            Example:
                [{"label": "Total", "sql": "SELECT COUNT(*) FROM MY_TABLE",
                  "icon": "fa-database", "color": "blue"}]
        charts: List of chart dicts. Each supports the same args as apex_add_jet_chart:
            - "region_name": Chart title (required)
            - "chart_type": "bar" | "line" | "area" | "pie" | "donut" (default "bar")
            - "sql_query": SQL for data (required)
            - "label_column": Label column name (default "LABEL")
            - "value_column": Value column name (default "VALUE")
            - "series_name": Legend label
            - "height": Chart height px (default 400)
            - "y_axis_title": Y axis label
            - "x_axis_title": X axis label
            - "extra_series": Additional series (for multi-series charts)
            Example:
                [
                  {"region_name": "Avaliações por Status", "chart_type": "pie",
                   "sql_query": "SELECT DS_STATUS LABEL, COUNT(*) VALUE FROM TEA_AVALIACOES GROUP BY DS_STATUS"},
                  {"region_name": "Evolução Mensal", "chart_type": "line",
                   "sql_query": "SELECT TO_CHAR(DT_AVALIACAO,'MM/YYYY') LABEL, COUNT(*) VALUE FROM TEA_AVALIACOES GROUP BY TO_CHAR(DT_AVALIACAO,'MM/YYYY') ORDER BY 1",
                   "series_name": "Avaliações"},
                ]
        auth_scheme: Authorization scheme name to restrict access (optional).

    Returns:
        JSON with status, page_id, regions created, charts created.

    Best practices:
        - Put 4 metrics on the first row (most important KPIs)
        - Use a pie/donut chart for distributions (status, category breakdown)
        - Use a bar or line chart for time-series trends
        - Put charts side by side by assigning alternating sequences (10, 20)
    """
    if not db.is_connected():
        return json.dumps({"status": "error", "error": "Not connected. Call apex_connect() first."})
    if not session.import_begun:
        return json.dumps({"status": "error", "error": "No import session active. Call apex_create_app() first."})

    log: list[str] = []
    created_regions = 0
    chart_count     = 0

    try:
        # Create page if it doesn't exist yet
        if page_id not in session.pages:
            from .page_tools import apex_add_page
            pr = json.loads(apex_add_page(page_id, page_name, "blank", auth_scheme=auth_scheme))
            if pr.get("status") == "error":
                return json.dumps(pr)
            log.append(f"Created page {page_id} '{page_name}'")
        else:
            log.append(f"Page {page_id} already exists — adding content")

        seq = 10

        # Metric cards
        if metrics:
            mr = json.loads(apex_add_metric_cards(
                page_id=page_id,
                region_name="KPIs",
                metrics=metrics,
                sequence=seq,
            ))
            if mr.get("status") == "error":
                return json.dumps(mr)
            created_regions += 1
            seq += 10
            log.append(f"Added {len(metrics)} metric cards")

        # Charts
        for ch in (charts or []):
            cr = json.loads(apex_add_jet_chart(
                page_id=page_id,
                region_name=ch.get("region_name", f"Chart {chart_count + 1}"),
                chart_type=ch.get("chart_type", "bar"),
                sql_query=ch.get("sql_query", "SELECT 'N/A' LABEL, 0 VALUE FROM DUAL"),
                label_column=ch.get("label_column", "LABEL"),
                value_column=ch.get("value_column", "VALUE"),
                series_name=ch.get("series_name", ""),
                height=ch.get("height", 400),
                y_axis_title=ch.get("y_axis_title", ""),
                x_axis_title=ch.get("x_axis_title", ""),
                legend_position=ch.get("legend_position", "end"),
                sequence=seq,
                extra_series=ch.get("extra_series"),
            ))
            if cr.get("status") == "error":
                log.append(f"Chart '{ch.get('region_name')}' error: {cr['error']}")
            else:
                chart_count += 1
                created_regions += 1
                seq += 10
                log.append(f"Added {ch.get('chart_type','bar')} chart '{ch.get('region_name')}'")

        return json.dumps({
            "status": "ok",
            "page_id": page_id,
            "page_name": page_name,
            "regions_created": created_regions,
            "charts_created": chart_count,
            "log": log,
            "message": f"Analytics page {page_id} built: {len(metrics or [])} metrics, {chart_count} charts.",
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False, indent=2)
