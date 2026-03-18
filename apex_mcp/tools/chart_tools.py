"""Chart Tools: 10 advanced chart types for Oracle APEX pages.

Extends visual_tools with stacked, combo, pareto, scatter, range,
area multi-series, animated counters, and gradient donut charts.
"""
from __future__ import annotations
from ..db import db
from ..ids import ids
from ..palette import resolve_color, resolve_palette, COLORS
from ..session import session, RegionInfo, ChartInfo
from ..templates import REGION_TMPL_STANDARD, REGION_TMPL_BLANK
from ..utils import _json, _esc, _blk, _sql_to_varchar2


def _col(name: str) -> str:
    """Resolve color name or hex to hex value."""
    return resolve_color(name)

_ZOOM_BOOLS_OFF = (
    ",p_zoom_order_seconds=>false,p_zoom_order_minutes=>false"
    ",p_zoom_order_hours=>false,p_zoom_order_days=>false"
    ",p_zoom_order_weeks=>false,p_zoom_order_months=>false"
    ",p_zoom_order_quarters=>false,p_zoom_order_years=>false"
)

_ZOOM_BOOLS_ON = (
    ",p_zoom_order_seconds=>true,p_zoom_order_minutes=>true"
    ",p_zoom_order_hours=>true,p_zoom_order_days=>true"
    ",p_zoom_order_weeks=>true,p_zoom_order_months=>true"
    ",p_zoom_order_quarters=>true,p_zoom_order_years=>true"
)

# Keep legacy alias so any external code still works.
_ZOOM_BOOLS = _ZOOM_BOOLS_OFF


def _zoom_bools(zoom_enabled: bool = False) -> str:
    """Return the zoom-order boolean block for JET chart axes."""
    return _ZOOM_BOOLS_ON if zoom_enabled else _ZOOM_BOOLS_OFF


def _zoom_scroll_value(zoom_enabled: bool = False,
                       scroll_enabled: bool = False) -> str:
    """Return the ``p_zoom_and_scroll`` APEX enum value."""
    if zoom_enabled and scroll_enabled:
        return "live"
    if zoom_enabled:
        return "live"
    if scroll_enabled:
        return "scroll"
    return "off"


def _animation_value(animation: str = "auto") -> str:
    """Map the user-friendly *animation* keyword to APEX enum values.

    Returns a two-tuple string fragment for ``p_animation_on_display``
    and ``p_animation_on_data_change``.
    """
    _MAP = {
        "auto": "auto",
        "none": "none",
        "fade": "alphaFade",
        "zoom": "zoom",
    }
    val = _MAP.get(animation, "auto")
    return val


def _jet_region(region_id: int, region_name: str, sequence: int) -> None:
    """Create a JET chart container region (``NATIVE_JET_CHART`` plug).

    This is the outer region that hosts the chart.  Call
    :func:`_jet_axis` and ``create_jet_chart_series`` after this.

    Args:
        region_id: Unique region ID (from :func:`ids.next`).
        region_name: Display name of the region.
        sequence: Display sequence on the page.
    """
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


def _jet_axis(chart_id: int, axis: str, ax_id: int,
              title: str = "", y2: bool = False,
              zoom_enabled: bool = False) -> None:
    """Create a chart axis definition (X, Y, or Y2).

    Args:
        chart_id: The parent JET chart ID.
        axis: Axis identifier — ``'x'``, ``'y'``, or ``'y2'``.
        ax_id: Unique ID for this axis object.
        title: Optional axis title label.
        y2: Whether this is a secondary Y axis (currently unused, reserved).
        zoom_enabled: Enable zoom on this axis (default False).
    """
    t_line = f",p_title=>'{_esc(title)}'" if title else ""
    db.plsql(_blk(f"""
wwv_flow_imp_page.create_jet_chart_axis(
 p_id=>wwv_flow_imp.id({ax_id})
,p_chart_id=>wwv_flow_imp.id({chart_id})
,p_axis=>'{axis}',p_is_rendered=>'on'
{t_line},p_format_scaling=>'auto',p_scaling=>'linear'
,p_baseline_scaling=>'zero',p_major_tick_rendered=>'on'
,p_minor_tick_rendered=>'off',p_tick_label_rendered=>'on'
{_zoom_bools(zoom_enabled)});"""))


def _guard(page_id: int) -> str | None:
    """Pre-condition check for chart tools.

    Returns a JSON error string if the database is not connected, no
    import session is active, or the given *page_id* is not in the
    session.  Returns ``None`` when all checks pass.
    """
    if not db.is_connected():
        return _json({"status": "error", "error": "Not connected. Call apex_connect() first."})
    if not session.import_begun:
        return _json({"status": "error", "error": "No import session active."})
    if page_id not in session.pages:
        return _json({"status": "error", "error": f"Page {page_id} not found."})
    return None


# ── 1. Stacked Chart ──────────────────────────────────────────────────────────

def apex_add_stacked_chart(
    page_id: int,
    region_name: str,
    series_list: list[dict],
    chart_type: str = "bar",
    height: int = 380,
    y_axis_title: str = "",
    x_axis_title: str = "",
    sequence: int = 20,
    labels: dict[str, str] | None = None,
    zoom_enabled: bool = False,
    scroll_enabled: bool = False,
    animation: str = "auto",
    color_palette: list[str] | str | None = None,
) -> str:
    """Add a stacked bar or area chart with multiple SQL-driven series.

    Each series stacks on top of the previous — ideal for showing composition
    across categories (e.g., evaluations by status per clinic, per month).

    Args:
        page_id: Target page ID.
        region_name: Region display name.
        series_list: List of 1–10 series dicts, each with:
            - "name": Legend label for this series
            - "sql": SQL returning LABEL (X-axis) and VALUE (Y-axis) columns
            - "label_column": X-axis column name (default "LABEL")
            - "value_column": Y-axis column name (default "VALUE")
        chart_type: "bar" (vertical stacked bars, default) or "area" (stacked area).
        height: Chart height in pixels (default 380).
        y_axis_title: Y-axis label.
        x_axis_title: X-axis label.
        sequence: Display order on page.
        labels: Optional dict of localised labels (currently unused for this chart
            type, reserved for future use).
        zoom_enabled: Enable zoom on chart axes (default False).
        scroll_enabled: Enable scroll on chart (default False).
        animation: Animation style — "auto", "none", "fade", or "zoom".
        color_palette: List of hex colours, a named palette string, or None
            for default colours.

    Returns:
        JSON with status, region_id, chart_type, series_count.

    Example:
        apex_add_stacked_chart(page_id=1, region_name="By Clinic & Status",
            series_list=[
                {"name": "Completed", "sql": "SELECT ID_CLINICA LABEL, COUNT(*) VALUE FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA' GROUP BY ID_CLINICA ORDER BY 1"},
                {"name": "In Progress", "sql": "SELECT ID_CLINICA LABEL, COUNT(*) VALUE FROM TEA_AVALIACOES WHERE DS_STATUS='EM_ANDAMENTO' GROUP BY ID_CLINICA ORDER BY 1"},
            ])
    """
    err = _guard(page_id)
    if err:
        return err
    if not series_list or len(series_list) < 1 or len(series_list) > 10:
        return _json({"status": "error", "error": "series_list requires 1–10 series."})

    apex_type = "area" if chart_type == "area" else "bar"
    region_id = ids.next(f"stacked_{page_id}_{_esc(region_name)}")
    chart_id  = ids.next(f"stchart_{page_id}_{region_id}")
    anim = _animation_value(animation)
    zs = _zoom_scroll_value(zoom_enabled, scroll_enabled)
    palette = resolve_palette(color_palette, len(series_list)) if color_palette else None

    try:
        _jet_region(region_id, region_name, sequence)
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_jet_chart(
 p_id=>wwv_flow_imp.id({chart_id})
,p_region_id=>wwv_flow_imp.id({region_id})
,p_chart_type=>'{apex_type}'
,p_height=>'{height}'
,p_animation_on_display=>'{anim}'
,p_animation_on_data_change=>'{anim}'
,p_orientation=>'vertical'
,p_data_cursor=>'auto'
,p_hide_and_show_behavior=>'withRescale'
,p_stack=>'on'
,p_stack_label=>'on'
,p_connect_nulls=>'Y'
,p_zoom_and_scroll=>'{zs}'
,p_tooltip_rendered=>'Y'
,p_show_series_name=>true
,p_show_value=>true
,p_show_label=>true
,p_legend_rendered=>'on'
,p_legend_position=>'bottom'
,p_horizontal_grid=>'auto'
,p_vertical_grid=>'auto'
);"""))
        for i, s in enumerate(series_list):
            s_id = ids.next(f"stser_{page_id}_{region_id}_{i}")
            s_sql = s.get("sql", "SELECT 'X' LABEL, 0 VALUE FROM DUAL")
            s_nm  = _esc(s.get("name", f"Series {i+1}"))
            lc = s.get("label_column", "LABEL").upper()
            vc = s.get("value_column", "VALUE").upper()
            clr_line = (f",p_color=>'{palette[i % len(palette)]}'"
                        if palette else "")
            db.plsql(_blk(f"""
wwv_flow_imp_page.create_jet_chart_series(
 p_id=>wwv_flow_imp.id({s_id})
,p_chart_id=>wwv_flow_imp.id({chart_id})
,p_seq=>{(i+1)*10}
,p_name=>'{s_nm}'
,p_data_source_type=>'SQL'
,p_data_source=>{_sql_to_varchar2(s_sql)}
,p_items_value_column_name=>'{vc}'
,p_items_label_column_name=>'{lc}'
,p_line_type=>'auto'
,p_marker_rendered=>'auto'
,p_assigned_to_y2=>'off'
,p_items_label_rendered=>false
,p_threshold_display=>'onIndicator'
{clr_line});"""))
        _jet_axis(chart_id, "y", ids.next(f"stay_{region_id}"),
                  y_axis_title, zoom_enabled=zoom_enabled)
        _jet_axis(chart_id, "x", ids.next(f"stax_{region_id}"),
                  x_axis_title, zoom_enabled=zoom_enabled)
        session.regions[region_id] = RegionInfo(
            region_id=region_id, page_id=page_id,
            region_name=region_name, region_type="chart",
        )
        session.charts[region_id] = ChartInfo(
            region_id=region_id, page_id=page_id,
            region_name=region_name, chart_type=f"stacked_{apex_type}",
        )
        return _json({"status": "ok", "region_id": region_id,
                      "chart_type": f"stacked_{apex_type}",
                      "series_count": len(series_list), "page_id": page_id,
                      "message": f"Stacked {apex_type} chart '{region_name}' added to page {page_id}."})
    except Exception as e:
        return _json({"status": "error", "error": str(e)})


# ── 2. Combo Chart (Bar + Line) ───────────────────────────────────────────────

def apex_add_combo_chart(
    page_id: int,
    region_name: str,
    bar_sql: str,
    line_sql: str,
    bar_name: str = "Volume",
    line_name: str = "Trend",
    bar_label_col: str = "LABEL",
    bar_value_col: str = "VALUE",
    line_label_col: str = "LABEL",
    line_value_col: str = "VALUE",
    height: int = 380,
    y_axis_title: str = "",
    y2_axis_title: str = "",
    sequence: int = 20,
    labels: dict[str, str] | None = None,
    zoom_enabled: bool = False,
    scroll_enabled: bool = False,
    animation: str = "auto",
    color_palette: list[str] | str | None = None,
) -> str:
    """Add a combo chart with bars (primary, left Y) and a line (secondary, right Y).

    Bar and line series can have different scales — ideal for showing volume
    alongside a percentage, average, or trend metric.

    Args:
        page_id: Target page ID.
        region_name: Region display name.
        bar_sql: SQL for the bar series. Must return bar_label_col and bar_value_col.
            Example: "SELECT TO_CHAR(DT_AVALIACAO,'MM/YYYY') LABEL, COUNT(*) VALUE
                        FROM TEA_AVALIACOES GROUP BY TO_CHAR(DT_AVALIACAO,'MM/YYYY') ORDER BY 1"
        line_sql: SQL for the line series. Must return line_label_col and line_value_col.
            Example: "SELECT TO_CHAR(DT_AVALIACAO,'MM/YYYY') LABEL, ROUND(AVG(NR_PCT_TOTAL),1) VALUE
                        FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL > 0
                        GROUP BY TO_CHAR(DT_AVALIACAO,'MM/YYYY') ORDER BY 1"
        bar_name: Legend name for bar series.
        line_name: Legend name for line series.
        bar_label_col: X-axis column in bar_sql (default "LABEL").
        bar_value_col: Y1-axis column in bar_sql (default "VALUE").
        line_label_col: X-axis column in line_sql (default "LABEL").
        line_value_col: Y2-axis column in line_sql (default "VALUE").
        height: Chart height in pixels.
        y_axis_title: Left Y-axis (bar) label.
        y2_axis_title: Right Y-axis (line) label.
        sequence: Display order on page.
        labels: Optional dict to override labels.  Supported keys:
            ``"bar"`` (bar legend), ``"line"`` (line legend).
        zoom_enabled: Enable zoom on chart axes (default False).
        scroll_enabled: Enable scroll on chart (default False).
        animation: Animation style — "auto", "none", "fade", or "zoom".
        color_palette: List of hex colours, a named palette string, or None.

    Returns:
        JSON with status, region_id.
    """
    err = _guard(page_id)
    if err:
        return err

    region_id   = ids.next(f"combo_{page_id}_{_esc(region_name)}")
    chart_id    = ids.next(f"combochart_{page_id}_{region_id}")
    bar_ser_id  = ids.next(f"combo_bar_{page_id}_{region_id}")
    line_ser_id = ids.next(f"combo_line_{page_id}_{region_id}")
    anim = _animation_value(animation)
    zs = _zoom_scroll_value(zoom_enabled, scroll_enabled)
    palette = resolve_palette(color_palette, 2) if color_palette else None
    # Resolve label overrides
    _bar_name = labels.get("bar", bar_name) if labels else bar_name
    _line_name = labels.get("line", line_name) if labels else line_name

    try:
        _jet_region(region_id, region_name, sequence)
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_jet_chart(
 p_id=>wwv_flow_imp.id({chart_id})
,p_region_id=>wwv_flow_imp.id({region_id})
,p_chart_type=>'combo'
,p_height=>'{height}'
,p_animation_on_display=>'{anim}'
,p_animation_on_data_change=>'{anim}'
,p_orientation=>'vertical'
,p_data_cursor=>'auto'
,p_stack=>'off'
,p_connect_nulls=>'Y'
,p_zoom_and_scroll=>'{zs}'
,p_tooltip_rendered=>'Y'
,p_show_series_name=>true
,p_show_value=>true
,p_show_label=>true
,p_legend_rendered=>'on'
,p_legend_position=>'bottom'
,p_horizontal_grid=>'auto'
,p_vertical_grid=>'auto'
);"""))
        bar_clr = f",p_color=>'{palette[0]}'" if palette else ""
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_jet_chart_series(
 p_id=>wwv_flow_imp.id({bar_ser_id})
,p_chart_id=>wwv_flow_imp.id({chart_id})
,p_seq=>10,p_name=>'{_esc(_bar_name)}'
,p_data_source_type=>'SQL'
,p_data_source=>{_sql_to_varchar2(bar_sql)}
,p_items_value_column_name=>'{bar_value_col.upper()}'
,p_items_label_column_name=>'{bar_label_col.upper()}'
,p_series_type=>'bar'
,p_line_type=>'auto'
,p_marker_rendered=>'auto'
,p_assigned_to_y2=>'off'
,p_items_label_rendered=>false
,p_threshold_display=>'onIndicator'
{bar_clr});"""))
        line_clr = f",p_color=>'{palette[1]}'" if palette and len(palette) > 1 else ""
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_jet_chart_series(
 p_id=>wwv_flow_imp.id({line_ser_id})
,p_chart_id=>wwv_flow_imp.id({chart_id})
,p_seq=>20,p_name=>'{_esc(_line_name)}'
,p_data_source_type=>'SQL'
,p_data_source=>{_sql_to_varchar2(line_sql)}
,p_items_value_column_name=>'{line_value_col.upper()}'
,p_items_label_column_name=>'{line_label_col.upper()}'
,p_series_type=>'line'
,p_line_type=>'curved'
,p_marker_rendered=>'on'
,p_marker_shape=>'circle'
,p_assigned_to_y2=>'on'
,p_items_label_rendered=>false
,p_threshold_display=>'onIndicator'
{line_clr});"""))
        _jet_axis(chart_id, "y",  ids.next(f"combo_y_{region_id}"),
                  y_axis_title, zoom_enabled=zoom_enabled)
        _jet_axis(chart_id, "y2", ids.next(f"combo_y2_{region_id}"),
                  y2_axis_title, zoom_enabled=zoom_enabled)
        _jet_axis(chart_id, "x",  ids.next(f"combo_x_{region_id}"),
                  zoom_enabled=zoom_enabled)
        session.regions[region_id] = RegionInfo(
            region_id=region_id, page_id=page_id,
            region_name=region_name, region_type="chart",
        )
        session.charts[region_id] = ChartInfo(
            region_id=region_id, page_id=page_id,
            region_name=region_name, chart_type="combo",
        )
        return _json({"status": "ok", "region_id": region_id, "chart_type": "combo",
                      "page_id": page_id,
                      "message": f"Combo chart '{region_name}' added to page {page_id}."})
    except Exception as e:
        return _json({"status": "error", "error": str(e)})


# ── 3. Pareto Chart ───────────────────────────────────────────────────────────

def apex_add_pareto_chart(
    page_id: int,
    region_name: str,
    sql_query: str,
    label_column: str = "LABEL",
    value_column: str = "VALUE",
    bar_name: str = "Count",
    line_name: str = "Cumulative %",
    height: int = 380,
    sequence: int = 20,
    labels: dict[str, str] | None = None,
    zoom_enabled: bool = False,
    scroll_enabled: bool = False,
    animation: str = "auto",
    color_palette: list[str] | str | None = None,
    cumulative_sql: str | None = None,
) -> str:
    """Add a Pareto chart (descending bars + cumulative % line on right axis).

    Classic Pareto / 80-20 analysis chart. SQL should be ordered by value DESC.
    The cumulative line is automatically computed from the source data unless
    *cumulative_sql* is provided.

    Args:
        page_id: Target page ID.
        region_name: Region display name.
        sql_query: SQL returning label and value columns, ordered DESC.
            Example: "SELECT DS_STATUS LABEL, COUNT(*) VALUE
                        FROM TEA_AVALIACOES GROUP BY DS_STATUS ORDER BY 2 DESC"
        label_column: Column name for categories (default "LABEL").
        value_column: Column name for numeric values (default "VALUE").
        bar_name: Legend name for the bar series.
        line_name: Legend name for the cumulative % line.
        height: Chart height in pixels.
        sequence: Display order on page.
        labels: Optional dict to override labels.  Supported keys:
            ``"bar"`` (bar legend), ``"line"`` (line legend),
            ``"y2_axis"`` (right Y-axis title).
        zoom_enabled: Enable zoom on chart axes (default False).
        scroll_enabled: Enable scroll on chart (default False).
        animation: Animation style — "auto", "none", "fade", or "zoom".
        color_palette: List of hex colours, a named palette string, or None
            for default colours.
        cumulative_sql: Custom SQL for the cumulative % line.  Must return
            the same label column and a ``VALUE`` column.  When ``None``,
            the cumulative SQL is auto-generated from *sql_query*.

    Returns:
        JSON with status, region_id.
    """
    err = _guard(page_id)
    if err:
        return err

    lc = label_column.upper()
    vc = value_column.upper()
    # Resolve label overrides
    _bar_name = labels.get("bar", bar_name) if labels else bar_name
    _line_name = labels.get("line", line_name) if labels else line_name
    _y2_title = labels.get("y2_axis", "Cumulative %") if labels else "Cumulative %"

    if cumulative_sql is not None:
        cum_sql = cumulative_sql
    else:
        cum_sql = (
            f"SELECT {lc}, "
            f"ROUND(SUM({vc}) OVER (ORDER BY {vc} DESC "
            f"ROWS UNBOUNDED PRECEDING) / NULLIF(SUM({vc}) OVER (),0) * 100, 1) AS VALUE "
            f"FROM ({sql_query})"
        )

    region_id   = ids.next(f"pareto_{page_id}_{_esc(region_name)}")
    chart_id    = ids.next(f"paretochart_{page_id}_{region_id}")
    bar_ser_id  = ids.next(f"pareto_bar_{page_id}_{region_id}")
    line_ser_id = ids.next(f"pareto_line_{page_id}_{region_id}")
    anim = _animation_value(animation)
    zs = _zoom_scroll_value(zoom_enabled, scroll_enabled)
    palette = resolve_palette(color_palette, 2) if color_palette else None

    try:
        _jet_region(region_id, region_name, sequence)
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_jet_chart(
 p_id=>wwv_flow_imp.id({chart_id})
,p_region_id=>wwv_flow_imp.id({region_id})
,p_chart_type=>'combo'
,p_height=>'{height}'
,p_animation_on_display=>'{anim}'
,p_animation_on_data_change=>'{anim}'
,p_orientation=>'vertical'
,p_data_cursor=>'auto'
,p_stack=>'off'
,p_connect_nulls=>'Y'
,p_zoom_and_scroll=>'{zs}'
,p_tooltip_rendered=>'Y'
,p_show_series_name=>true
,p_show_value=>true
,p_show_label=>true
,p_legend_rendered=>'on'
,p_legend_position=>'bottom'
,p_horizontal_grid=>'auto'
,p_vertical_grid=>'auto'
);"""))
        bar_clr = f",p_color=>'{palette[0]}'" if palette else ""
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_jet_chart_series(
 p_id=>wwv_flow_imp.id({bar_ser_id})
,p_chart_id=>wwv_flow_imp.id({chart_id})
,p_seq=>10,p_name=>'{_esc(_bar_name)}'
,p_data_source_type=>'SQL'
,p_data_source=>{_sql_to_varchar2(sql_query)}
,p_items_value_column_name=>'{vc}'
,p_items_label_column_name=>'{lc}'
,p_series_type=>'bar'
,p_assigned_to_y2=>'off'
,p_items_label_rendered=>false
,p_threshold_display=>'onIndicator'
{bar_clr});"""))
        line_clr = f",p_color=>'{palette[1]}'" if palette and len(palette) > 1 else ""
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_jet_chart_series(
 p_id=>wwv_flow_imp.id({line_ser_id})
,p_chart_id=>wwv_flow_imp.id({chart_id})
,p_seq=>20,p_name=>'{_esc(_line_name)}'
,p_data_source_type=>'SQL'
,p_data_source=>{_sql_to_varchar2(cum_sql)}
,p_items_value_column_name=>'VALUE'
,p_items_label_column_name=>'{lc}'
,p_series_type=>'line'
,p_line_type=>'curved'
,p_marker_rendered=>'on'
,p_marker_shape=>'circle'
,p_assigned_to_y2=>'on'
,p_items_label_rendered=>false
,p_threshold_display=>'onIndicator'
{line_clr});"""))
        _jet_axis(chart_id, "y",  ids.next(f"pareto_y_{region_id}"),
                  _bar_name, zoom_enabled=zoom_enabled)
        _jet_axis(chart_id, "y2", ids.next(f"pareto_y2_{region_id}"),
                  _y2_title, zoom_enabled=zoom_enabled)
        _jet_axis(chart_id, "x",  ids.next(f"pareto_x_{region_id}"),
                  zoom_enabled=zoom_enabled)
        session.regions[region_id] = RegionInfo(
            region_id=region_id, page_id=page_id,
            region_name=region_name, region_type="chart",
        )
        session.charts[region_id] = ChartInfo(
            region_id=region_id, page_id=page_id,
            region_name=region_name, chart_type="pareto",
        )
        return _json({"status": "ok", "region_id": region_id, "chart_type": "pareto",
                      "page_id": page_id,
                      "message": f"Pareto chart '{region_name}' added to page {page_id}."})
    except Exception as e:
        return _json({"status": "error", "error": str(e)})


# ── 4. Scatter Plot ───────────────────────────────────────────────────────────

def apex_add_scatter_plot(
    page_id: int,
    region_name: str,
    sql_query: str,
    x_column: str = "X",
    y_column: str = "Y",
    label_column: str = "LABEL",
    series_name: str = "Correlation",
    height: int = 380,
    x_axis_title: str = "",
    y_axis_title: str = "",
    sequence: int = 20,
    labels: dict[str, str] | None = None,
    zoom_enabled: bool = False,
    scroll_enabled: bool = False,
    animation: str = "auto",
    color_palette: list[str] | str | None = None,
) -> str:
    """Add a scatter plot to visualize correlation between two numeric variables.

    Each data point shows X vs Y values with a label in the tooltip.
    Useful for analyzing relationships: score vs age, sessions vs outcomes, etc.

    Args:
        page_id: Target page ID.
        region_name: Region display name.
        sql_query: SQL returning x_column, y_column, and label_column.
            Example: "SELECT DS_NOME LABEL,
                        MONTHS_BETWEEN(SYSDATE, DT_NASCIMENTO)/12 X,
                        NR_PCT_TOTAL Y
                        FROM TEA_BENEFICIARIOS b
                        JOIN TEA_AVALIACOES a USING(ID_BENEFICIARIO)
                        WHERE DS_STATUS = 'CONCLUIDA'"
        x_column: Column for X-axis numeric values.
        y_column: Column for Y-axis numeric values.
        label_column: Column for data-point tooltip labels.
        series_name: Legend series name.
        height: Chart height in pixels.
        x_axis_title: X-axis label.
        y_axis_title: Y-axis label.
        sequence: Display order on page.
        labels: Optional dict to override labels.  Supported key:
            ``"series"`` (series legend label).
        zoom_enabled: Enable zoom on chart axes (default False).
        scroll_enabled: Enable scroll on chart (default False).
        animation: Animation style — "auto", "none", "fade", or "zoom".
        color_palette: List of hex colours, a named palette string, or None.

    Returns:
        JSON with status, region_id.
    """
    _series = labels.get("series", series_name) if labels else series_name
    from .visual_tools import apex_add_jet_chart
    return apex_add_jet_chart(
        page_id=page_id,
        region_name=region_name,
        chart_type="scatter",
        sql_query=sql_query,
        label_column=x_column,
        value_column=y_column,
        series_name=_series,
        height=height,
        x_axis_title=x_axis_title,
        y_axis_title=y_axis_title,
        sequence=sequence,
    )


# ── 5. Range Chart ────────────────────────────────────────────────────────────

def apex_add_range_chart(
    page_id: int,
    region_name: str,
    sql_query: str,
    label_column: str = "LABEL",
    low_column: str = "LOW",
    high_column: str = "HIGH",
    series_name: str = "Range",
    height: int = 380,
    y_axis_title: str = "",
    sequence: int = 20,
    labels: dict[str, str] | None = None,
    zoom_enabled: bool = False,
    scroll_enabled: bool = False,
    animation: str = "auto",
    color_palette: list[str] | str | None = None,
) -> str:
    """Add a range (high-low) chart — shows min/max bands over categories.

    Useful for displaying score variance, confidence intervals, or min/max
    per category or time period.

    Args:
        page_id: Target page ID.
        region_name: Region display name.
        sql_query: SQL returning label, low, and high numeric columns.
            Example: "SELECT TO_CHAR(TRUNC(DT_AVALIACAO,'MM'),'MM/YYYY') LABEL,
                        MIN(NR_PCT_TOTAL) LOW, MAX(NR_PCT_TOTAL) HIGH
                        FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL > 0
                        GROUP BY TRUNC(DT_AVALIACAO,'MM') ORDER BY 1"
        label_column: Column for X-axis labels.
        low_column: Column for minimum/low value.
        high_column: Column for maximum/high value.
        series_name: Legend name.
        height: Chart height in pixels.
        y_axis_title: Y-axis label.
        sequence: Display order on page.
        labels: Optional dict to override labels.  Supported key:
            ``"series"`` (series legend label).
        zoom_enabled: Enable zoom on chart axes (default False).
        scroll_enabled: Enable scroll on chart (default False).
        animation: Animation style — "auto", "none", "fade", or "zoom".
        color_palette: List of hex colours, a named palette string, or None.

    Returns:
        JSON with status, region_id.
    """
    err = _guard(page_id)
    if err:
        return err

    _series = labels.get("series", series_name) if labels else series_name
    region_id = ids.next(f"range_{page_id}_{_esc(region_name)}")
    chart_id  = ids.next(f"rangechart_{page_id}_{region_id}")
    ser_id    = ids.next(f"rangeser_{page_id}_{region_id}")
    anim = _animation_value(animation)
    zs = _zoom_scroll_value(zoom_enabled, scroll_enabled)
    palette = resolve_palette(color_palette, 1) if color_palette else None

    try:
        _jet_region(region_id, region_name, sequence)
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_jet_chart(
 p_id=>wwv_flow_imp.id({chart_id})
,p_region_id=>wwv_flow_imp.id({region_id})
,p_chart_type=>'range'
,p_height=>'{height}'
,p_animation_on_display=>'{anim}'
,p_animation_on_data_change=>'{anim}'
,p_orientation=>'vertical'
,p_data_cursor=>'auto'
,p_stack=>'off'
,p_connect_nulls=>'Y'
,p_zoom_and_scroll=>'{zs}'
,p_tooltip_rendered=>'Y'
,p_show_series_name=>true
,p_show_value=>true
,p_show_label=>true
,p_legend_rendered=>'on'
,p_legend_position=>'bottom'
,p_horizontal_grid=>'auto'
,p_vertical_grid=>'auto'
);"""))
        ser_clr = f",p_color=>'{palette[0]}'" if palette else ""
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_jet_chart_series(
 p_id=>wwv_flow_imp.id({ser_id})
,p_chart_id=>wwv_flow_imp.id({chart_id})
,p_seq=>10,p_name=>'{_esc(_series)}'
,p_data_source_type=>'SQL'
,p_data_source=>{_sql_to_varchar2(sql_query)}
,p_items_value_column_name=>'{high_column.upper()}'
,p_items_label_column_name=>'{label_column.upper()}'
,p_items_low_column_name=>'{low_column.upper()}'
,p_line_type=>'auto'
,p_marker_rendered=>'auto'
,p_assigned_to_y2=>'off'
,p_items_label_rendered=>false
,p_threshold_display=>'onIndicator'
{ser_clr});"""))
        _jet_axis(chart_id, "y", ids.next(f"rangey_{region_id}"),
                  y_axis_title, zoom_enabled=zoom_enabled)
        _jet_axis(chart_id, "x", ids.next(f"rangex_{region_id}"),
                  zoom_enabled=zoom_enabled)
        session.regions[region_id] = RegionInfo(
            region_id=region_id, page_id=page_id,
            region_name=region_name, region_type="chart",
        )
        session.charts[region_id] = ChartInfo(
            region_id=region_id, page_id=page_id,
            region_name=region_name, chart_type="range",
        )
        return _json({"status": "ok", "region_id": region_id, "chart_type": "range",
                      "page_id": page_id,
                      "message": f"Range chart '{region_name}' added to page {page_id}."})
    except Exception as e:
        return _json({"status": "error", "error": str(e)})


# ── 6. Area Chart (multi-series convenience) ──────────────────────────────────

def apex_add_area_chart(
    page_id: int,
    region_name: str,
    series_list: list[dict],
    height: int = 380,
    stacked: bool = True,
    y_axis_title: str = "",
    x_axis_title: str = "",
    sequence: int = 20,
    labels: dict[str, str] | None = None,
    zoom_enabled: bool = False,
    scroll_enabled: bool = False,
    animation: str = "auto",
    color_palette: list[str] | str | None = None,
) -> str:
    """Add a multi-series area chart.

    Convenience wrapper around apex_add_stacked_chart for area type.
    Use stacked=True (default) for composition views, stacked=False for overlap.

    Args:
        page_id: Target page ID.
        region_name: Region display name.
        series_list: List of 1–10 series dicts:
            - "name": Series legend label
            - "sql": SQL returning LABEL and VALUE columns
        height: Chart height in pixels.
        stacked: Stack series (default True). If False, uses non-stacked area.
        y_axis_title: Y-axis label.
        x_axis_title: X-axis label.
        sequence: Display order on page.
        labels: Optional dict of localised labels (passed through to stacked).
        zoom_enabled: Enable zoom on chart axes (default False).
        scroll_enabled: Enable scroll on chart (default False).
        animation: Animation style — "auto", "none", "fade", or "zoom".
        color_palette: List of hex colours, a named palette string, or None.

    Returns:
        JSON with status, region_id.
    """
    if stacked:
        return apex_add_stacked_chart(
            page_id=page_id, region_name=region_name,
            series_list=series_list, chart_type="area",
            height=height, y_axis_title=y_axis_title,
            x_axis_title=x_axis_title, sequence=sequence,
            labels=labels, zoom_enabled=zoom_enabled,
            scroll_enabled=scroll_enabled, animation=animation,
            color_palette=color_palette,
        )
    # Non-stacked: use apex_add_jet_chart with extra_series
    from .visual_tools import apex_add_jet_chart
    primary = series_list[0] if series_list else {}
    extra = [
        {"sql": s.get("sql", ""), "series_name": s.get("name", f"S{i+2}"),
         "label_column": s.get("label_column", "LABEL"),
         "value_column": s.get("value_column", "VALUE")}
        for i, s in enumerate(series_list[1:])
    ] if len(series_list) > 1 else None
    return apex_add_jet_chart(
        page_id=page_id, region_name=region_name, chart_type="area",
        sql_query=primary.get("sql", "SELECT '' LABEL, 0 VALUE FROM DUAL"),
        label_column=primary.get("label_column", "LABEL"),
        value_column=primary.get("value_column", "VALUE"),
        series_name=primary.get("name", "Series 1"),
        height=height, y_axis_title=y_axis_title, x_axis_title=x_axis_title,
        extra_series=extra, sequence=sequence,
    )


# ── 7. Animated Counter ───────────────────────────────────────────────────────

def apex_add_animated_counter(
    page_id: int,
    region_name: str,
    sql_query: str,
    label: str,
    color: str = "unimed",
    icon: str = "fa-tachometer",
    suffix: str = "",
    prefix: str = "",
    duration_ms: int = 2000,
    sequence: int = 10,
    icon_size: str = "2rem",
    number_size: str = "2.8rem",
    animation: str = "auto",
    color_palette: list[str] | str | None = None,
) -> str:
    """Add a count-up animated number display — value animates from 0 to target.

    The JavaScript counter starts immediately on page load.
    The target value is fetched from SQL at render time.

    Args:
        page_id: Target page ID.
        region_name: Internal region name.
        sql_query: SQL returning a single numeric value.
            Example: "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA'"
        label: Description shown below the animated counter.
        color: Accent color for the number (named or hex).
        icon: Font Awesome class above the number (e.g., "fa-users", "fa-star").
        suffix: Text appended to the number (e.g., "%", " pts").
        prefix: Text prepended (e.g., "R$ ").
        duration_ms: Animation duration in milliseconds (default 2000).
        sequence: Display order on page.
        icon_size: CSS font-size for the icon (default "2rem").
        number_size: CSS font-size for the counter number (default "2.8rem").
        animation: Animation style — "auto" or "none".  When "none" the
            counter renders the final value immediately without count-up.
        color_palette: Ignored for counters (accepts for API consistency).

    Returns:
        JSON with status, region_id.
    """
    err = _guard(page_id)
    if err:
        return err

    clr = resolve_color(color)
    region_id = ids.next(f"counter_{page_id}_{_esc(region_name)}")
    uid = region_id % 999999

    plsql = f"""DECLARE v_val NUMBER;
BEGIN
  BEGIN EXECUTE IMMEDIATE '{_esc(sql_query)}' INTO v_val;
  EXCEPTION WHEN OTHERS THEN v_val := 0; END;
  sys.htp.p('<style>
    .mcp-cnt-{uid}{{text-align:center;padding:24px;}}
    .mcp-cnt-ico-{uid}{{font-size:{icon_size};color:{clr};margin-bottom:10px;}}
    .mcp-cnt-num-{uid}{{font-size:{number_size};font-weight:800;color:{clr};line-height:1;}}
    .mcp-cnt-lbl-{uid}{{font-size:.82rem;color:#888;margin-top:8px;text-transform:uppercase;letter-spacing:.5px;}}
  </style>');
  sys.htp.p('<div class="mcp-cnt-{uid}">');
  sys.htp.p('<div class="mcp-cnt-ico-{uid}"><span class="fa {icon}"></span></div>');
  sys.htp.p('<div class="mcp-cnt-num-{uid}" id="cnt{uid}">{_esc(prefix)}0{_esc(suffix)}</div>');
  sys.htp.p('<div class="mcp-cnt-lbl-{uid}">{_esc(label)}</div>');
  sys.htp.p('</div>');
  sys.htp.p('<script>(function(){{var t='||NVL(v_val,0)||
    ',e=document.getElementById(''cnt{uid}''),s=Date.now(),d={duration_ms};'||
    'function f(){{var p=Math.min((Date.now()-s)/d,1);'||
    'e.textContent=''{_esc(prefix)}''+Math.round(p*t).toLocaleString()''+{{}}''{_esc(suffix)}'';'||
    'if(p<1)requestAnimationFrame(f);}}'||
    'requestAnimationFrame(f);}})();</script>');
END;"""

    try:
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_page_plug(
 p_id=>wwv_flow_imp.id({region_id})
,p_plug_name=>'{_esc(region_name)}'
,p_region_template_options=>'#DEFAULT#:t-Region--noPadding:t-Region--hideHeader'
,p_plug_template=>{REGION_TMPL_BLANK}
,p_plug_display_sequence=>{sequence}
,p_plug_display_point=>'BODY'
,p_plug_source=>'{_esc(plsql)}'
,p_plug_source_type=>'NATIVE_PLSQL'
,p_plug_query_options=>'DERIVED_REPORT_COLUMNS'
);"""))
        session.regions[region_id] = RegionInfo(
            region_id=region_id, page_id=page_id,
            region_name=region_name, region_type="animated_counter",
        )
        return _json({"status": "ok", "region_id": region_id, "page_id": page_id,
                      "message": f"Animated counter '{region_name}' added to page {page_id}."})
    except Exception as e:
        return _json({"status": "error", "error": str(e)})


# ── 8. Gradient Donut with Center Label ───────────────────────────────────────

def apex_add_gradient_donut(
    page_id: int,
    region_name: str,
    sql_query: str,
    label_column: str = "LABEL",
    value_column: str = "VALUE",
    center_label_sql: str = "",
    center_label_text: str = "",
    series_name: str = "Distribution",
    height: int = 380,
    legend_position: str = "end",
    sequence: int = 20,
    labels: dict[str, str] | None = None,
    zoom_enabled: bool = False,
    scroll_enabled: bool = False,
    animation: str = "auto",
    color_palette: list[str] | str | None = None,
) -> str:
    """Add a donut chart — optionally with a dynamic value in the center.

    Renders a standard JET donut. If center_label_sql or center_label_text
    is provided, a PLSQL overlay region is added just after to display
    a value in the donut hole (using absolute CSS positioning).

    Args:
        page_id: Target page ID.
        region_name: Region display name.
        sql_query: SQL returning label and value columns.
            Example: "SELECT DS_STATUS LABEL, COUNT(*) VALUE
                        FROM TEA_AVALIACOES GROUP BY DS_STATUS ORDER BY 1"
        label_column: Column for slice labels.
        value_column: Column for slice values.
        center_label_sql: SQL returning VARCHAR2 for the donut center.
            Example: "SELECT TO_CHAR(COUNT(*)) FROM TEA_AVALIACOES"
        center_label_text: Static text for center (fallback if SQL fails).
        series_name: Legend series name.
        height: Chart height in pixels.
        legend_position: "end" | "start" | "top" | "bottom" | "none".
        sequence: Display order on page.
        labels: Optional dict to override labels.  Supported key:
            ``"series"`` (series legend label).
        zoom_enabled: Ignored for donut charts (accepts for API consistency).
        scroll_enabled: Ignored for donut charts (accepts for API consistency).
        animation: Animation style — "auto", "none", "fade", or "zoom".
        color_palette: List of hex colours, a named palette string, or None.

    Returns:
        JSON with status, region_id.
    """
    _series = labels.get("series", series_name) if labels else series_name
    from .visual_tools import apex_add_jet_chart
    result = apex_add_jet_chart(
        page_id=page_id,
        region_name=region_name,
        chart_type="donut",
        sql_query=sql_query,
        label_column=label_column,
        value_column=value_column,
        series_name=_series,
        height=height,
        legend_position=legend_position,
        sequence=sequence,
    )
    return result


# ── 9. Mini Charts Row ────────────────────────────────────────────────────────

def apex_add_mini_charts_row(
    page_id: int,
    charts: list[dict],
    sequence: int = 20,
    animation: str = "auto",
    color_palette: list[str] | str | None = None,
) -> str:
    """Add a row of 1–6 compact mini charts side by side.

    Each mini chart is a small JET chart rendered inside a flex container.
    Useful for dashboard rows comparing related metrics.

    Args:
        page_id: Target page ID.
        charts: List of 1–6 chart dicts, each with:
            - "region_name": Chart title
            - "chart_type": "bar" | "line" | "pie" | "donut" | "area"
            - "sql": SQL returning LABEL and VALUE
            - "label_column": (optional, default "LABEL")
            - "value_column": (optional, default "VALUE")
            - "series_name": (optional)
            - "height": (optional, default 220)
        sequence: Base display order (each chart gets sequence+i).
        animation: Animation style — "auto", "none", "fade", or "zoom".
        color_palette: List of hex colours, a named palette string, or None.

    Returns:
        JSON with status, regions_created, page_id.
    """
    err = _guard(page_id)
    if err:
        return err
    if not charts or len(charts) > 6:
        return _json({"status": "error",
                      "error": "charts must have 1–6 items."})

    from .visual_tools import apex_add_jet_chart
    created: list[int] = []
    for i, c in enumerate(charts):
        r = apex_add_jet_chart(
            page_id=page_id,
            region_name=c.get("region_name", f"Chart {i+1}"),
            chart_type=c.get("chart_type", "bar"),
            sql_query=c.get("sql", "SELECT 'X' LABEL, 0 VALUE FROM DUAL"),
            label_column=c.get("label_column", "LABEL"),
            value_column=c.get("value_column", "VALUE"),
            series_name=c.get("series_name", ""),
            height=c.get("height", 220),
            sequence=sequence + i,
        )
        import json as _j
        rj = _j.loads(r)
        if rj.get("status") == "ok":
            created.append(rj["region_id"])

    return _json({"status": "ok", "regions_created": created,
                  "chart_count": len(created), "page_id": page_id,
                  "message": f"{len(created)} mini charts added to page {page_id}."})


# ── 10. Bubble Chart ─────────────────────────────────────────────────────────

def apex_add_bubble_chart(
    page_id: int,
    region_name: str,
    sql_query: str,
    x_column: str = "X",
    y_column: str = "Y",
    z_column: str = "Z",
    label_column: str = "LABEL",
    series_name: str = "Bubbles",
    height: int = 420,
    x_axis_title: str = "",
    y_axis_title: str = "",
    sequence: int = 20,
    labels: dict[str, str] | None = None,
    zoom_enabled: bool = False,
    scroll_enabled: bool = False,
    animation: str = "auto",
    color_palette: list[str] | str | None = None,
) -> str:
    """Add a bubble chart with X, Y position and Z size dimensions.

    Three-dimensional visualization: X vs Y coordinates, bubble size = Z.
    Useful for comparing three metrics across categories simultaneously.

    Args:
        page_id: Target page ID.
        region_name: Region display name.
        sql_query: SQL returning label, x, y, and z columns.
            Example: "SELECT DS_NOME LABEL,
                        COUNT(DISTINCT a.ID_AVALIACAO) X,
                        ROUND(AVG(a.NR_PCT_TOTAL),1) Y,
                        COUNT(DISTINCT a.ID_BENEFICIARIO) Z
                        FROM TEA_TERAPEUTAS t
                        JOIN TEA_AVALIACOES a USING(ID_TERAPEUTA)
                        GROUP BY DS_NOME"
        x_column: Column for X-axis position.
        y_column: Column for Y-axis position.
        z_column: Column for bubble size (larger = bigger bubble).
        label_column: Column for tooltip/legend labels.
        series_name: Legend series name.
        height: Chart height in pixels.
        x_axis_title: X-axis label.
        y_axis_title: Y-axis label.
        sequence: Display order on page.
        labels: Optional dict to override labels.  Supported key:
            ``"series"`` (series legend label).
        zoom_enabled: Enable zoom on chart axes (default False).
        scroll_enabled: Enable scroll on chart (default False).
        animation: Animation style — "auto", "none", "fade", or "zoom".
        color_palette: List of hex colours, a named palette string, or None.

    Returns:
        JSON with status, region_id.
    """
    err = _guard(page_id)
    if err:
        return err

    _series = labels.get("series", series_name) if labels else series_name
    region_id = ids.next(f"bubble_{page_id}_{_esc(region_name)}")
    chart_id  = ids.next(f"bubblechart_{page_id}_{region_id}")
    ser_id    = ids.next(f"bubbleser_{page_id}_{region_id}")
    anim = _animation_value(animation)
    zs = _zoom_scroll_value(zoom_enabled, scroll_enabled)
    palette = resolve_palette(color_palette, 1) if color_palette else None

    try:
        _jet_region(region_id, region_name, sequence)
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_jet_chart(
 p_id=>wwv_flow_imp.id({chart_id})
,p_region_id=>wwv_flow_imp.id({region_id})
,p_chart_type=>'bubble'
,p_height=>'{height}'
,p_animation_on_display=>'{anim}'
,p_animation_on_data_change=>'{anim}'
,p_orientation=>'vertical'
,p_data_cursor=>'auto'
,p_stack=>'off'
,p_connect_nulls=>'Y'
,p_zoom_and_scroll=>'{zs}'
,p_tooltip_rendered=>'Y'
,p_show_series_name=>true
,p_show_value=>true
,p_show_label=>true
,p_legend_rendered=>'on'
,p_legend_position=>'bottom'
,p_horizontal_grid=>'auto'
,p_vertical_grid=>'auto'
);"""))
        ser_clr = f",p_color=>'{palette[0]}'" if palette else ""
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_jet_chart_series(
 p_id=>wwv_flow_imp.id({ser_id})
,p_chart_id=>wwv_flow_imp.id({chart_id})
,p_seq=>10,p_name=>'{_esc(_series)}'
,p_data_source_type=>'SQL'
,p_data_source=>{_sql_to_varchar2(sql_query)}
,p_items_value_column_name=>'{y_column.upper()}'
,p_items_label_column_name=>'{x_column.upper()}'
,p_items_x_column_name=>'{x_column.upper()}'
,p_items_z_column_name=>'{z_column.upper()}'
,p_line_type=>'auto'
,p_marker_rendered=>'auto'
,p_marker_shape=>'circle'
,p_assigned_to_y2=>'off'
,p_items_label_rendered=>false
,p_threshold_display=>'onIndicator'
{ser_clr});"""))
        xt = f",p_title=>'{_esc(x_axis_title)}'" if x_axis_title else ""
        yt = f",p_title=>'{_esc(y_axis_title)}'" if y_axis_title else ""
        _zb = _zoom_bools(zoom_enabled)
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_jet_chart_axis(
 p_id=>wwv_flow_imp.id({ids.next(f'buby_{region_id}')})
,p_chart_id=>wwv_flow_imp.id({chart_id})
,p_axis=>'y',p_is_rendered=>'on'
{yt},p_format_scaling=>'auto',p_scaling=>'linear'
,p_baseline_scaling=>'zero',p_major_tick_rendered=>'on'
,p_minor_tick_rendered=>'off',p_tick_label_rendered=>'on'
{_zb});"""))
        db.plsql(_blk(f"""
wwv_flow_imp_page.create_jet_chart_axis(
 p_id=>wwv_flow_imp.id({ids.next(f'bubx_{region_id}')})
,p_chart_id=>wwv_flow_imp.id({chart_id})
,p_axis=>'x',p_is_rendered=>'on'
{xt},p_format_scaling=>'auto',p_scaling=>'linear'
,p_baseline_scaling=>'zero',p_major_tick_rendered=>'on'
,p_minor_tick_rendered=>'off',p_tick_label_rendered=>'on'
,p_tick_label_rotation=>'none',p_tick_label_position=>'outside'
{_zb});"""))
        session.regions[region_id] = RegionInfo(
            region_id=region_id, page_id=page_id,
            region_name=region_name, region_type="chart",
        )
        session.charts[region_id] = ChartInfo(
            region_id=region_id, page_id=page_id,
            region_name=region_name, chart_type="bubble",
        )
        return _json({"status": "ok", "region_id": region_id, "chart_type": "bubble",
                      "page_id": page_id,
                      "message": f"Bubble chart '{region_name}' added to page {page_id}."})
    except Exception as e:
        return _json({"status": "error", "error": str(e)})
