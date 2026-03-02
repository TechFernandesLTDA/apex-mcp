"""Build App 207 — Dashboard Executivo TEA.

Painel executivo de alto nível para gestão da Plataforma Desfecho TEA.
Utiliza extensivamente os 30 novos visuais (ui_tools + chart_tools).

Páginas (8):
  100 → Login (customizado)
    1 → Painel Executivo  (hero banner + metric cards + stacked chart + stat delta + animated counter)
   10 → KPIs Estratégicos (spotlight metric + comparison panel + kpi row + percent bars)
   20 → Comparativo de Período (comparison panel + combo chart + stat delta)
   30 → Mapa de Calor     (heatmap grid + status matrix + data card grid)
   40 → Tendências        (area chart stacked + line chart + ribbon stats)
   50 → Scorecard Clínicas(leaderboard + percent bars + bar horizontal chart)
"""
import os, json, sys, time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

os.environ.update({
    "ORACLE_DB_USER":         "TEA_APP",
    "ORACLE_DB_PASS":         "TeaApp@2024#Unimed",
    "ORACLE_DSN":             "u5cvlivnjuodscai_tp",
    "ORACLE_WALLET_DIR":      r"C:\Projetos\Apex\wallet",
    "ORACLE_WALLET_PASSWORD": "apex1234",
    "APEX_WORKSPACE_ID":      "8822816515098715",
    "APEX_SCHEMA":            "TEA_APP",
    "APEX_WORKSPACE_NAME":    "TEA",
})

sys.path.insert(0, r"C:\Projetos\Apex\mcp-server")

from apex_mcp.tools.sql_tools       import apex_connect
from apex_mcp.tools.app_tools       import apex_create_app, apex_finalize_app
from apex_mcp.tools.page_tools      import apex_add_page
from apex_mcp.tools.generator_tools import apex_generate_login
from apex_mcp.tools.visual_tools    import apex_add_metric_cards, apex_add_jet_chart
from apex_mcp.tools.shared_tools    import apex_add_nav_item
from apex_mcp.tools.ui_tools        import (
    apex_add_hero_banner, apex_add_kpi_row, apex_add_stat_delta,
    apex_add_ribbon_stats, apex_add_spotlight_metric, apex_add_comparison_panel,
    apex_add_percent_bars, apex_add_leaderboard, apex_add_heatmap_grid,
    apex_add_status_matrix, apex_add_data_card_grid,
)
from apex_mcp.tools.chart_tools     import (
    apex_add_stacked_chart, apex_add_combo_chart, apex_add_area_chart,
    apex_add_animated_counter, apex_add_pareto_chart,
)

APP_ID   = 207
APP_NAME = "Dashboard Executivo TEA"


def ok(label: str, result_str: str) -> tuple[bool, dict]:
    r = json.loads(result_str)
    if r.get("status") == "error":
        print(f"  ❌ {label}: {r['error']}")
        return False, r
    print(f"  ✓  {label}")
    return True, r


def section(title: str):
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")


def run():
    t0 = time.perf_counter()
    print("\n" + "═"*60)
    print(f"  App {APP_ID} — {APP_NAME}")
    print(f"  KPIs Executivos · Comparativos · Heatmap · Tendências")
    print("═"*60)

    # ── [1] Conexão ───────────────────────────────────────────────────────────
    section("[1] Conexão Oracle ADB")
    if not ok("apex_connect", apex_connect())[0]: return

    # ── [2] Criar app ─────────────────────────────────────────────────────────
    section("[2] Criar aplicação 207")
    if not ok("apex_create_app", apex_create_app(
        app_id=APP_ID,
        app_name=APP_NAME,
        app_alias="exec-tea",
        login_page=100,
        home_page=1,
        language="pt-br",
        date_format="DD/MM/YYYY",
    ))[0]: return

    ok("apex_generate_login(100)", apex_generate_login(100))

    # ── [3] Página 1 — Painel Executivo ───────────────────────────────────────
    section("[3] Painel Executivo — página 1")
    if not ok("apex_add_page(1)", apex_add_page(1, "Painel Executivo", "blank"))[0]: return

    # Hero banner com 4 KPIs inline
    ok("hero_banner", apex_add_hero_banner(
        page_id=1,
        title="Dashboard Executivo — Plataforma TEA",
        subtitle="Visão estratégica em tempo real · Unimed Nacional · " +
                 "Padrão ICHOM · VINELAND · CBCL · CFQL2 · RBS-R",
        bg_color="unimed",
        stats=[
            {"label": "Beneficiários Ativos", "sql": "SELECT COUNT(*) FROM TEA_BENEFICIARIOS WHERE FL_ATIVO='S'"},
            {"label": "Avaliações",           "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES"},
            {"label": "Score Médio (%)",       "sql": "SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0", "suffix": "%"},
            {"label": "Clínicas Ativas",       "sql": "SELECT COUNT(*) FROM TEA_CLINICAS WHERE FL_ATIVO='S'"},
        ],
        button_label="Ver KPIs",
        button_url="f?p=&APP_ID.:10:&SESSION..",
        sequence=5,
    ))

    # Metric cards principais (gradient)
    ok("metric_cards: principais", apex_add_metric_cards(
        page_id=1,
        region_name="Indicadores Executivos",
        sequence=10,
        columns=4,
        style="gradient",
        metrics=[
            {"label": "Beneficiários Ativos",    "sql": "SELECT COUNT(*) FROM TEA_BENEFICIARIOS WHERE FL_ATIVO='S'",                    "icon": "fa-users",        "color": "blue",   "link_page": 50},
            {"label": "Avaliações Concluídas",   "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA'",              "icon": "fa-check-circle", "color": "green"},
            {"label": "Taxa Conclusão (%)",      "sql": "SELECT ROUND(COUNT(CASE WHEN DS_STATUS='CONCLUIDA' THEN 1 END)*100.0/NULLIF(COUNT(*),0),1) FROM TEA_AVALIACOES", "icon": "fa-pie-chart", "color": "teal", "suffix": "%"},
            {"label": "Score Médio Geral (%)",   "sql": "SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0",   "icon": "fa-trophy",       "color": "amber",  "suffix": "%"},
        ],
    ))

    # Stat delta — variação mensal
    ok("stat_delta: variação", apex_add_stat_delta(
        page_id=1,
        region_name="Variação vs. Mês Anterior",
        sequence=20,
        columns=4,
        metrics=[
            {"label": "Novas Avaliações",  "icon": "fa-clipboard",    "color": "blue",
             "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DT_AVALIACAO >= TRUNC(SYSDATE,'MM')",
             "prev_sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DT_AVALIACAO >= ADD_MONTHS(TRUNC(SYSDATE,'MM'),-1) AND DT_AVALIACAO < TRUNC(SYSDATE,'MM')"},
            {"label": "Concluídas Mês",    "icon": "fa-check-circle", "color": "green",
             "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA' AND DT_AVALIACAO >= TRUNC(SYSDATE,'MM')",
             "prev_sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA' AND DT_AVALIACAO >= ADD_MONTHS(TRUNC(SYSDATE,'MM'),-1) AND DT_AVALIACAO < TRUNC(SYSDATE,'MM')"},
            {"label": "Novos Pacientes",   "icon": "fa-user-plus",    "color": "purple",
             "sql": "SELECT COUNT(*) FROM TEA_BENEFICIARIOS WHERE DT_CRIACAO >= TRUNC(SYSDATE,'MM')",
             "prev_sql": "SELECT COUNT(*) FROM TEA_BENEFICIARIOS WHERE DT_CRIACAO >= ADD_MONTHS(TRUNC(SYSDATE,'MM'),-1) AND DT_CRIACAO < TRUNC(SYSDATE,'MM')"},
            {"label": "Score Médio Mês",   "icon": "fa-bar-chart",    "color": "teal", "suffix": "%",
             "sql": "SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0 AND DT_AVALIACAO >= TRUNC(SYSDATE,'MM')",
             "prev_sql": "SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0 AND DT_AVALIACAO >= ADD_MONTHS(TRUNC(SYSDATE,'MM'),-1) AND DT_AVALIACAO < TRUNC(SYSDATE,'MM')"},
        ],
    ))

    # Stacked chart — avaliações por clínica e status
    ok("stacked_chart: avaliações por clínica", apex_add_stacked_chart(
        page_id=1,
        region_name="Avaliações por Clínica e Status",
        chart_type="bar",
        height=380,
        y_axis_title="Qtd. Avaliações",
        x_axis_title="Clínica",
        sequence=30,
        series_list=[
            {
                "name": "Concluída",
                "sql": (
                    "SELECT c.DS_NOME AS LABEL, COUNT(*) AS VALUE "
                    "FROM TEA_CLINICAS c LEFT JOIN TEA_AVALIACOES a "
                    "ON a.ID_CLINICA=c.ID_CLINICA AND a.DS_STATUS='CONCLUIDA' "
                    "WHERE c.FL_ATIVO='S' GROUP BY c.DS_NOME ORDER BY c.DS_NOME"
                ),
            },
            {
                "name": "Em Andamento",
                "sql": (
                    "SELECT c.DS_NOME AS LABEL, COUNT(*) AS VALUE "
                    "FROM TEA_CLINICAS c LEFT JOIN TEA_AVALIACOES a "
                    "ON a.ID_CLINICA=c.ID_CLINICA AND a.DS_STATUS='EM_ANDAMENTO' "
                    "WHERE c.FL_ATIVO='S' GROUP BY c.DS_NOME ORDER BY c.DS_NOME"
                ),
            },
            {
                "name": "Rascunho",
                "sql": (
                    "SELECT c.DS_NOME AS LABEL, COUNT(*) AS VALUE "
                    "FROM TEA_CLINICAS c LEFT JOIN TEA_AVALIACOES a "
                    "ON a.ID_CLINICA=c.ID_CLINICA AND a.DS_STATUS='RASCUNHO' "
                    "WHERE c.FL_ATIVO='S' GROUP BY c.DS_NOME ORDER BY c.DS_NOME"
                ),
            },
        ],
    ))

    # Animated counter + ribbon_stats
    ok("animated_counter: total avaliações", apex_add_animated_counter(
        page_id=1,
        region_name="Total de Avaliações",
        sql_query="SELECT COUNT(*) FROM TEA_AVALIACOES",
        label="Total de Avaliações Registradas na Plataforma",
        color="unimed",
        icon="fa-clipboard",
        sequence=40,
    ))

    ok("ribbon_stats: resumo executivo", apex_add_ribbon_stats(
        page_id=1,
        region_name="Resumo Executivo",
        sequence=50,
        metrics=[
            {"label": "Terapeutas",   "sql": "SELECT COUNT(*) FROM TEA_TERAPEUTAS WHERE FL_ATIVO='S'",      "icon": "fa-user-md",    "color": "blue"},
            {"label": "Instrumentos", "sql": "SELECT COUNT(*) FROM TEA_PROVAS WHERE FL_ATIVO='S'",          "icon": "fa-list-alt",   "color": "orange"},
            {"label": "Dimensões",    "sql": "SELECT COUNT(*) FROM TEA_DIMENSOES",                          "icon": "fa-sliders",    "color": "purple"},
            {"label": "Em Andamento", "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='EM_ANDAMENTO'", "icon": "fa-spinner", "color": "teal"},
            {"label": "Canceladas",   "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CANCELADA'",    "icon": "fa-times",   "color": "red"},
        ],
    ))

    # ── [4] Página 10 — KPIs Estratégicos ────────────────────────────────────
    section("[4] KPIs Estratégicos — página 10")
    if not ok("apex_add_page(10)", apex_add_page(10, "KPIs Estratégicos", "blank"))[0]: return

    ok("spotlight: score médio", apex_add_spotlight_metric(
        page_id=10,
        region_name="Score Médio Geral",
        sql_query="SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL > 0",
        label="Score Médio Geral da Plataforma",
        color="unimed",
        icon="fa-trophy",
        suffix="%",
        subtitle_sql="SELECT 'Baseado em '||COUNT(*)||' avaliações concluídas' FROM TEA_AVALIACOES WHERE DS_STATUS=''CONCLUIDA''",
        sequence=10,
    ))

    ok("comparison_panel: mês atual vs anterior", apex_add_comparison_panel(
        page_id=10,
        region_name="Mês Atual vs. Mês Anterior",
        left_label="Mês Atual",
        right_label="Mês Anterior",
        left_color="green",
        right_color="blue",
        sequence=20,
        left_metrics=[
            {"label": "Avaliações",   "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DT_AVALIACAO >= TRUNC(SYSDATE,'MM')"},
            {"label": "Concluídas",   "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA' AND DT_AVALIACAO >= TRUNC(SYSDATE,'MM')"},
            {"label": "Score Médio",  "sql": "SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0 AND DT_AVALIACAO >= TRUNC(SYSDATE,'MM')", "suffix": "%"},
            {"label": "Novos Pacientes", "sql": "SELECT COUNT(*) FROM TEA_BENEFICIARIOS WHERE DT_CRIACAO >= TRUNC(SYSDATE,'MM')"},
        ],
        right_metrics=[
            {"label": "Avaliações",   "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DT_AVALIACAO >= ADD_MONTHS(TRUNC(SYSDATE,'MM'),-1) AND DT_AVALIACAO < TRUNC(SYSDATE,'MM')"},
            {"label": "Concluídas",   "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA' AND DT_AVALIACAO >= ADD_MONTHS(TRUNC(SYSDATE,'MM'),-1) AND DT_AVALIACAO < TRUNC(SYSDATE,'MM')"},
            {"label": "Score Médio",  "sql": "SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0 AND DT_AVALIACAO >= ADD_MONTHS(TRUNC(SYSDATE,'MM'),-1) AND DT_AVALIACAO < TRUNC(SYSDATE,'MM')", "suffix": "%"},
            {"label": "Novos Pacientes", "sql": "SELECT COUNT(*) FROM TEA_BENEFICIARIOS WHERE DT_CRIACAO >= ADD_MONTHS(TRUNC(SYSDATE,'MM'),-1) AND DT_CRIACAO < TRUNC(SYSDATE,'MM')"},
        ],
    ))

    ok("kpi_row: 6 KPIs compactos", apex_add_kpi_row(
        page_id=10,
        region_name="KPIs Rápidos",
        sequence=30,
        metrics=[
            {"label": "Taxa Conclusão",     "sql": "SELECT ROUND(COUNT(CASE WHEN DS_STATUS='CONCLUIDA' THEN 1 END)*100.0/NULLIF(COUNT(*),0),1) FROM TEA_AVALIACOES", "suffix": "%",        "color": "green"},
            {"label": "Taxa Andamento",     "sql": "SELECT ROUND(COUNT(CASE WHEN DS_STATUS='EM_ANDAMENTO' THEN 1 END)*100.0/NULLIF(COUNT(*),0),1) FROM TEA_AVALIACOES", "suffix": "%",     "color": "orange"},
            {"label": "Score Máximo",       "sql": "SELECT MAX(NR_PCT_TOTAL) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0",                           "suffix": "%",      "color": "purple"},
            {"label": "Score Mínimo",       "sql": "SELECT MIN(NR_PCT_TOTAL) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0",                           "suffix": "%",      "color": "red"},
            {"label": "Média Avaliações/Clínica","sql": "SELECT ROUND(COUNT(*)/NULLIF((SELECT COUNT(*) FROM TEA_CLINICAS WHERE FL_ATIVO='S'),0),1) FROM TEA_AVALIACOES", "color": "blue"},
            {"label": "Pacientes/Terapeuta","sql": "SELECT ROUND(COUNT(DISTINCT ID_BENEFICIARIO)/NULLIF((SELECT COUNT(*) FROM TEA_TERAPEUTAS WHERE FL_ATIVO='S'),0),1) FROM TEA_AVALIACOES", "color": "teal"},
        ],
    ))

    ok("percent_bars: status global", apex_add_percent_bars(
        page_id=10,
        region_name="Distribuição Global por Status",
        sql_query="SELECT DS_STATUS AS LABEL, COUNT(*) AS VALUE FROM TEA_AVALIACOES GROUP BY DS_STATUS ORDER BY 2 DESC",
        color="unimed",
        sequence=40,
    ))

    ok("pareto: instrumentos estratégicos", apex_add_pareto_chart(
        page_id=10,
        region_name="Pareto — Avaliações por Instrumento",
        sql_query=(
            "SELECT p.DS_NOME AS LABEL, COUNT(a.ID_AVALIACAO) AS VALUE "
            "FROM TEA_PROVAS p LEFT JOIN TEA_AVALIACOES a ON a.ID_PROVA=p.ID_PROVA "
            "WHERE p.FL_ATIVO='S' GROUP BY p.DS_NOME ORDER BY 2 DESC"
        ),
        bar_name="Volume",
        line_name="Acumulado %",
        height=360,
        sequence=50,
    ))

    # ── [5] Página 20 — Comparativo de Período ───────────────────────────────
    section("[5] Comparativo de Período — página 20")
    if not ok("apex_add_page(20)", apex_add_page(20, "Comparativo de Período", "blank"))[0]: return

    ok("combo_chart: avaliações + score médio", apex_add_combo_chart(
        page_id=20,
        region_name="Volume de Avaliações vs. Score Médio",
        bar_sql=(
            "SELECT TO_CHAR(DT_AVALIACAO,'MM/YYYY') AS LABEL, COUNT(*) AS VALUE "
            "FROM TEA_AVALIACOES "
            "GROUP BY TO_CHAR(DT_AVALIACAO,'MM/YYYY') "
            "ORDER BY MIN(DT_AVALIACAO)"
        ),
        line_sql=(
            "SELECT TO_CHAR(DT_AVALIACAO,'MM/YYYY') AS LABEL, "
            "ROUND(AVG(NR_PCT_TOTAL),1) AS VALUE "
            "FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL > 0 "
            "GROUP BY TO_CHAR(DT_AVALIACAO,'MM/YYYY') "
            "ORDER BY MIN(DT_AVALIACAO)"
        ),
        bar_name="Avaliações",
        line_name="Score Médio (%)",
        y_axis_title="Qtd. Avaliações",
        y2_axis_title="Score Médio (%)",
        height=400,
        sequence=10,
    ))

    ok("stat_delta: comparativo trimestral", apex_add_stat_delta(
        page_id=20,
        region_name="Trimestre Atual vs. Anterior",
        sequence=20,
        columns=4,
        metrics=[
            {"label": "Avaliações",    "icon": "fa-clipboard",    "color": "blue",
             "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DT_AVALIACAO >= ADD_MONTHS(TRUNC(SYSDATE,'Q'),0)",
             "prev_sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DT_AVALIACAO >= ADD_MONTHS(TRUNC(SYSDATE,'Q'),-3) AND DT_AVALIACAO < ADD_MONTHS(TRUNC(SYSDATE,'Q'),0)"},
            {"label": "Concluídas",    "icon": "fa-check-circle", "color": "green",
             "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA' AND DT_AVALIACAO >= ADD_MONTHS(TRUNC(SYSDATE,'Q'),0)",
             "prev_sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA' AND DT_AVALIACAO >= ADD_MONTHS(TRUNC(SYSDATE,'Q'),-3) AND DT_AVALIACAO < ADD_MONTHS(TRUNC(SYSDATE,'Q'),0)"},
            {"label": "Score Médio",   "icon": "fa-bar-chart",    "color": "purple", "suffix": "%",
             "sql": "SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0 AND DT_AVALIACAO >= ADD_MONTHS(TRUNC(SYSDATE,'Q'),0)",
             "prev_sql": "SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0 AND DT_AVALIACAO >= ADD_MONTHS(TRUNC(SYSDATE,'Q'),-3) AND DT_AVALIACAO < ADD_MONTHS(TRUNC(SYSDATE,'Q'),0)"},
            {"label": "Novos Pacientes","icon": "fa-user-plus",   "color": "teal",
             "sql": "SELECT COUNT(*) FROM TEA_BENEFICIARIOS WHERE DT_CRIACAO >= ADD_MONTHS(TRUNC(SYSDATE,'Q'),0)",
             "prev_sql": "SELECT COUNT(*) FROM TEA_BENEFICIARIOS WHERE DT_CRIACAO >= ADD_MONTHS(TRUNC(SYSDATE,'Q'),-3) AND DT_CRIACAO < ADD_MONTHS(TRUNC(SYSDATE,'Q'),0)"},
        ],
    ))

    ok("comparison_panel: top2 clínicas", apex_add_comparison_panel(
        page_id=20,
        region_name="Comparação — Top 2 Clínicas por Volume",
        left_label="Clínica #1",
        right_label="Clínica #2",
        left_color="unimed",
        right_color="blue",
        sequence=30,
        left_metrics=[
            {"label": "Clínica",         "sql": "SELECT DS_NOME FROM TEA_CLINICAS WHERE FL_ATIVO='S' AND ROWNUM=1 ORDER BY (SELECT COUNT(*) FROM TEA_AVALIACOES a WHERE a.ID_CLINICA=ID_CLINICA) DESC"},
            {"label": "Avaliações",      "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE ID_CLINICA=(SELECT ID_CLINICA FROM (SELECT ID_CLINICA, RANK() OVER (ORDER BY COUNT(*) DESC) RNK FROM TEA_AVALIACOES GROUP BY ID_CLINICA) WHERE RNK=1 AND ROWNUM=1)"},
            {"label": "Score Médio",     "sql": "SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0 AND ID_CLINICA=(SELECT ID_CLINICA FROM (SELECT ID_CLINICA, RANK() OVER (ORDER BY COUNT(*) DESC) RNK FROM TEA_AVALIACOES GROUP BY ID_CLINICA) WHERE RNK=1 AND ROWNUM=1)", "suffix": "%"},
        ],
        right_metrics=[
            {"label": "Clínica",         "sql": "SELECT DS_NOME FROM TEA_CLINICAS WHERE ID_CLINICA=(SELECT ID_CLINICA FROM (SELECT ID_CLINICA, RANK() OVER (ORDER BY COUNT(*) DESC) RNK FROM TEA_AVALIACOES GROUP BY ID_CLINICA) WHERE RNK=2 AND ROWNUM=1)"},
            {"label": "Avaliações",      "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE ID_CLINICA=(SELECT ID_CLINICA FROM (SELECT ID_CLINICA, RANK() OVER (ORDER BY COUNT(*) DESC) RNK FROM TEA_AVALIACOES GROUP BY ID_CLINICA) WHERE RNK=2 AND ROWNUM=1)"},
            {"label": "Score Médio",     "sql": "SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0 AND ID_CLINICA=(SELECT ID_CLINICA FROM (SELECT ID_CLINICA, RANK() OVER (ORDER BY COUNT(*) DESC) RNK FROM TEA_AVALIACOES GROUP BY ID_CLINICA) WHERE RNK=2 AND ROWNUM=1)", "suffix": "%"},
        ],
    ))

    # ── [6] Página 30 — Mapa de Calor ────────────────────────────────────────
    section("[6] Mapa de Calor — página 30")
    if not ok("apex_add_page(30)", apex_add_page(30, "Mapa de Calor", "blank"))[0]: return

    ok("heatmap_grid: clínica x status", apex_add_heatmap_grid(
        page_id=30,
        region_name="Heatmap — Avaliações por Clínica e Status",
        sql_query=(
            "SELECT c.DS_NOME AS ROW_LABEL, a.DS_STATUS AS COL_LABEL, COUNT(*) AS VALUE "
            "FROM TEA_CLINICAS c "
            "LEFT JOIN TEA_AVALIACOES a ON a.ID_CLINICA = c.ID_CLINICA "
            "WHERE c.FL_ATIVO='S' AND a.DS_STATUS IS NOT NULL "
            "GROUP BY c.DS_NOME, a.DS_STATUS "
            "ORDER BY 1, 2"
        ),
        row_column="ROW_LABEL",
        col_column="COL_LABEL",
        value_column="VALUE",
        color="unimed",
        sequence=10,
    ))

    ok("status_matrix: terapeutas", apex_add_status_matrix(
        page_id=30,
        region_name="Status dos Terapeutas",
        sql_query=(
            "SELECT t.DS_NOME AS LABEL, "
            "DECODE(t.FL_ATIVO,'S','Ativo','Inativo') AS STATUS, "
            "c.DS_NOME AS GROUP_LABEL "
            "FROM TEA_TERAPEUTAS t "
            "JOIN TEA_CLINICAS c ON c.ID_CLINICA = t.ID_CLINICA "
            "ORDER BY c.DS_NOME, t.DS_NOME"
        ),
        label_column="LABEL",
        status_column="STATUS",
        group_column="GROUP_LABEL",
        sequence=20,
    ))

    ok("data_card_grid: clínicas", apex_add_data_card_grid(
        page_id=30,
        region_name="Cards de Clínicas",
        sql_query=(
            "SELECT c.DS_NOME AS TITLE, "
            "c.DS_CIDADE AS SUBTITLE, "
            "COUNT(a.ID_AVALIACAO) AS VALUE, "
            "DECODE(c.FL_ATIVO,'S','Ativa','Inativa') AS BADGE "
            "FROM TEA_CLINICAS c "
            "LEFT JOIN TEA_AVALIACOES a ON a.ID_CLINICA = c.ID_CLINICA "
            "GROUP BY c.DS_NOME, c.DS_CIDADE, c.FL_ATIVO "
            "ORDER BY 3 DESC"
        ),
        title_column="TITLE",
        subtitle_column="SUBTITLE",
        value_column="VALUE",
        badge_column="BADGE",
        color="unimed",
        columns=3,
        sequence=30,
    ))

    # ── [7] Página 40 — Tendências e Projeção ────────────────────────────────
    section("[7] Tendências e Projeção — página 40")
    if not ok("apex_add_page(40)", apex_add_page(40, "Tendências e Projeção", "blank"))[0]: return

    ok("area_chart stacked: evolução por status", apex_add_area_chart(
        page_id=40,
        region_name="Evolução Mensal por Status",
        stacked=True,
        height=400,
        y_axis_title="Qtd. Avaliações",
        x_axis_title="Mês",
        sequence=10,
        series_list=[
            {
                "name": "Concluída",
                "sql": (
                    "SELECT TO_CHAR(DT_AVALIACAO,'MM/YYYY') AS LABEL, COUNT(*) AS VALUE "
                    "FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA' "
                    "GROUP BY TO_CHAR(DT_AVALIACAO,'MM/YYYY') ORDER BY MIN(DT_AVALIACAO)"
                ),
            },
            {
                "name": "Em Andamento",
                "sql": (
                    "SELECT TO_CHAR(DT_AVALIACAO,'MM/YYYY') AS LABEL, COUNT(*) AS VALUE "
                    "FROM TEA_AVALIACOES WHERE DS_STATUS='EM_ANDAMENTO' "
                    "GROUP BY TO_CHAR(DT_AVALIACAO,'MM/YYYY') ORDER BY MIN(DT_AVALIACAO)"
                ),
            },
            {
                "name": "Rascunho",
                "sql": (
                    "SELECT TO_CHAR(DT_AVALIACAO,'MM/YYYY') AS LABEL, COUNT(*) AS VALUE "
                    "FROM TEA_AVALIACOES WHERE DS_STATUS='RASCUNHO' "
                    "GROUP BY TO_CHAR(DT_AVALIACAO,'MM/YYYY') ORDER BY MIN(DT_AVALIACAO)"
                ),
            },
        ],
    ))

    ok("jet_chart line: score médio mensal", apex_add_jet_chart(
        page_id=40,
        region_name="Evolução do Score Médio Mensal",
        chart_type="line",
        sql_query=(
            "SELECT TO_CHAR(DT_AVALIACAO,'MM/YYYY') AS LABEL, "
            "ROUND(AVG(NR_PCT_TOTAL),1) AS VALUE "
            "FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL > 0 "
            "GROUP BY TO_CHAR(DT_AVALIACAO,'MM/YYYY') "
            "ORDER BY MIN(DT_AVALIACAO)"
        ),
        series_name="Score Médio (%)",
        height=360,
        y_axis_title="Score (%)",
        x_axis_title="Mês",
        sequence=20,
    ))

    ok("ribbon_stats: tendências resumo", apex_add_ribbon_stats(
        page_id=40,
        region_name="Resumo de Tendências",
        sequence=30,
        metrics=[
            {"label": "Total Avaliações",  "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES",                                   "icon": "fa-clipboard",    "color": "blue"},
            {"label": "Últimos 30 dias",   "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DT_AVALIACAO >= SYSDATE-30",   "icon": "fa-calendar",     "color": "teal"},
            {"label": "Score Máximo",      "sql": "SELECT MAX(NR_PCT_TOTAL) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0",      "icon": "fa-arrow-up",     "color": "green", "suffix": "%"},
            {"label": "Score Mínimo",      "sql": "SELECT MIN(NR_PCT_TOTAL) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0",      "icon": "fa-arrow-down",   "color": "orange","suffix": "%"},
            {"label": "Mês com + Aval.",   "sql": "SELECT TO_CHAR(DT_MES,'MM/YYYY') FROM (SELECT TRUNC(DT_AVALIACAO,'MM') DT_MES, COUNT(*) CNT FROM TEA_AVALIACOES GROUP BY TRUNC(DT_AVALIACAO,'MM') ORDER BY 2 DESC FETCH FIRST 1 ROW ONLY)", "icon": "fa-calendar-check-o", "color": "purple"},
        ],
    ))

    # ── [8] Página 50 — Scorecard Clínicas ───────────────────────────────────
    section("[8] Scorecard Clínicas — página 50")
    if not ok("apex_add_page(50)", apex_add_page(50, "Scorecard Clínicas", "blank"))[0]: return

    ok("metric_cards: scorecard KPIs", apex_add_metric_cards(
        page_id=50,
        region_name="KPIs de Clínicas",
        sequence=10,
        columns=4,
        style="white",
        metrics=[
            {"label": "Clínicas Ativas",        "sql": "SELECT COUNT(*) FROM TEA_CLINICAS WHERE FL_ATIVO='S'",                                          "icon": "fa-hospital-o", "color": "teal"},
            {"label": "Melhor Score Médio (%)",  "sql": "SELECT MAX(score) FROM (SELECT ROUND(AVG(a.NR_PCT_TOTAL),1) score FROM TEA_AVALIACOES a WHERE a.NR_PCT_TOTAL>0 GROUP BY a.ID_CLINICA)", "icon": "fa-trophy",    "color": "green", "suffix": "%"},
            {"label": "Maior Volume",            "sql": "SELECT MAX(cnt) FROM (SELECT COUNT(*) cnt FROM TEA_AVALIACOES GROUP BY ID_CLINICA)",            "icon": "fa-bar-chart",  "color": "blue"},
            {"label": "Terapeutas / Clínica",    "sql": "SELECT ROUND(AVG(cnt),1) FROM (SELECT COUNT(*) cnt FROM TEA_TERAPEUTAS WHERE FL_ATIVO='S' GROUP BY ID_CLINICA)", "icon": "fa-users",   "color": "purple"},
        ],
    ))

    ok("leaderboard: ranking clínicas", apex_add_leaderboard(
        page_id=50,
        region_name="Ranking de Clínicas por Volume",
        sql_query=(
            "SELECT c.DS_NOME AS LABEL, COUNT(a.ID_AVALIACAO) AS VALUE "
            "FROM TEA_CLINICAS c "
            "LEFT JOIN TEA_AVALIACOES a ON a.ID_CLINICA = c.ID_CLINICA "
            "WHERE c.FL_ATIVO='S' GROUP BY c.DS_NOME ORDER BY 2 DESC"
        ),
        color="unimed",
        max_rows=10,
        show_medals=True,
        sequence=20,
    ))

    ok("percent_bars: score médio por clínica", apex_add_percent_bars(
        page_id=50,
        region_name="Score Médio por Clínica (%)",
        sql_query=(
            "SELECT c.DS_NOME AS LABEL, ROUND(AVG(a.NR_PCT_TOTAL),1) AS VALUE "
            "FROM TEA_CLINICAS c "
            "JOIN TEA_AVALIACOES a ON a.ID_CLINICA = c.ID_CLINICA "
            "WHERE a.NR_PCT_TOTAL > 0 AND c.FL_ATIVO='S' "
            "GROUP BY c.DS_NOME ORDER BY 2 DESC"
        ),
        color="green",
        sequence=30,
    ))

    ok("jet_chart bar_horizontal: terapeutas por clínica", apex_add_jet_chart(
        page_id=50,
        region_name="Terapeutas por Clínica",
        chart_type="bar",
        orientation="horizontal",
        sql_query=(
            "SELECT c.DS_NOME AS LABEL, COUNT(t.ID_TERAPEUTA) AS VALUE "
            "FROM TEA_CLINICAS c "
            "LEFT JOIN TEA_TERAPEUTAS t ON t.ID_CLINICA = c.ID_CLINICA AND t.FL_ATIVO='S' "
            "WHERE c.FL_ATIVO='S' GROUP BY c.DS_NOME ORDER BY 2 DESC"
        ),
        series_name="Terapeutas",
        height=340,
        x_axis_title="Qtd. Terapeutas",
        sequence=40,
    ))

    ok("stat_delta: scorecard variação", apex_add_stat_delta(
        page_id=50,
        region_name="Variação por Clínica (Top 4)",
        sequence=50,
        columns=4,
        metrics=[
            {"label": "Volume Geral",      "icon": "fa-bar-chart",    "color": "blue",
             "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DT_AVALIACAO >= TRUNC(SYSDATE,'MM')",
             "prev_sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DT_AVALIACAO >= ADD_MONTHS(TRUNC(SYSDATE,'MM'),-1) AND DT_AVALIACAO < TRUNC(SYSDATE,'MM')"},
            {"label": "Clínicas c/ Aval.", "icon": "fa-hospital-o",   "color": "teal",
             "sql": "SELECT COUNT(DISTINCT ID_CLINICA) FROM TEA_AVALIACOES WHERE DT_AVALIACAO >= TRUNC(SYSDATE,'MM')",
             "prev_sql": "SELECT COUNT(DISTINCT ID_CLINICA) FROM TEA_AVALIACOES WHERE DT_AVALIACAO >= ADD_MONTHS(TRUNC(SYSDATE,'MM'),-1) AND DT_AVALIACAO < TRUNC(SYSDATE,'MM')"},
            {"label": "Score Médio Mês",   "icon": "fa-trophy",       "color": "green", "suffix": "%",
             "sql": "SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0 AND DT_AVALIACAO >= TRUNC(SYSDATE,'MM')",
             "prev_sql": "SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0 AND DT_AVALIACAO >= ADD_MONTHS(TRUNC(SYSDATE,'MM'),-1) AND DT_AVALIACAO < TRUNC(SYSDATE,'MM')"},
            {"label": "Taxa Conclusão",    "icon": "fa-check-circle", "color": "purple", "suffix": "%",
             "sql": "SELECT ROUND(COUNT(CASE WHEN DS_STATUS='CONCLUIDA' THEN 1 END)*100.0/NULLIF(COUNT(*),0),1) FROM TEA_AVALIACOES WHERE DT_AVALIACAO >= TRUNC(SYSDATE,'MM')",
             "prev_sql": "SELECT ROUND(COUNT(CASE WHEN DS_STATUS='CONCLUIDA' THEN 1 END)*100.0/NULLIF(COUNT(*),0),1) FROM TEA_AVALIACOES WHERE DT_AVALIACAO >= ADD_MONTHS(TRUNC(SYSDATE,'MM'),-1) AND DT_AVALIACAO < TRUNC(SYSDATE,'MM')"},
        ],
    ))

    # ── [9] Navegação ─────────────────────────────────────────────────────────
    section("[9] Navegação")
    nav_items = [
        ("Painel Executivo",   1,  "fa-tachometer",  10),
        ("KPIs Estratégicos",  10, "fa-star",         20),
        ("Comparativo",        20, "fa-exchange",     30),
        ("Mapa de Calor",      30, "fa-th",           40),
        ("Tendências",         40, "fa-line-chart",   50),
        ("Scorecard Clínicas", 50, "fa-hospital-o",  60),
    ]
    for name, pg, icon, seq in nav_items:
        ok(f"nav: {name}", apex_add_nav_item(
            item_name=name, target_page=pg, sequence=seq, icon=icon,
        ))

    # ── [10] Finalizar ────────────────────────────────────────────────────────
    section("[10] Finalizar")
    r = json.loads(apex_finalize_app())
    if r.get("status") == "error":
        print(f"  ❌ apex_finalize_app: {r['error']}")
        return
    print(f"  ✓  apex_finalize_app")

    summary = r.get("summary", {})
    elapsed = time.perf_counter() - t0

    print("\n" + "═"*60)
    print(f"  App {APP_ID} — {APP_NAME}")
    print(f"  Construído em {elapsed:.1f}s")
    print(f"  Páginas : {summary.get('pages')}")
    print(f"  Regiões : {summary.get('regions')}")
    print(f"  Itens   : {summary.get('items')}")
    print(f"\n  Páginas (7):")
    print(f"    100  Login")
    print(f"      1  Painel Executivo  (hero + metric cards + stacked chart + stat delta + animated counter)")
    print(f"     10  KPIs Estratégicos (spotlight + comparison + kpi row + percent bars + pareto)")
    print(f"     20  Comparativo       (combo chart + stat delta + comparison panel)")
    print(f"     30  Mapa de Calor     (heatmap + status matrix + data card grid)")
    print(f"     40  Tendências        (area chart stacked + line chart + ribbon stats)")
    print(f"     50  Scorecard Clínicas(leaderboard + percent bars + bar + stat delta)")
    print(f"\n  URL: f?p={APP_ID}")
    print(f"  Login: cnu.admin / Unimed@2024")
    print("═"*60)


if __name__ == "__main__":
    run()
