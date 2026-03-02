"""Build App 208 — Portal do Terapeuta TEA."""
import os, json, sys, time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

os.environ.update({
    "ORACLE_DB_USER": "TEA_APP", "ORACLE_DB_PASS": "TeaApp@2024#Unimed",
    "ORACLE_DSN": "u5cvlivnjuodscai_tp",
    "ORACLE_WALLET_DIR": r"C:\Projetos\Apex\wallet",
    "ORACLE_WALLET_PASSWORD": "apex1234",
    "APEX_WORKSPACE_ID": "8822816515098715",
    "APEX_SCHEMA": "TEA_APP", "APEX_WORKSPACE_NAME": "TEA",
})

sys.path.insert(0, r"C:\Projetos\Apex\mcp-server")

from apex_mcp.tools.sql_tools    import apex_connect
from apex_mcp.tools.app_tools    import apex_create_app, apex_finalize_app
from apex_mcp.tools.page_tools   import apex_add_page
from apex_mcp.tools.generator_tools import apex_generate_login
from apex_mcp.tools.component_tools import apex_add_region
from apex_mcp.tools.shared_tools import apex_add_nav_item
from apex_mcp.tools.visual_tools import apex_add_jet_chart, apex_add_metric_cards
from apex_mcp.tools.ui_tools import (
    apex_add_hero_banner, apex_add_kpi_row, apex_add_stat_delta,
    apex_add_ribbon_stats, apex_add_spotlight_metric, apex_add_comparison_panel,
    apex_add_activity_stream, apex_add_percent_bars, apex_add_leaderboard,
    apex_add_heatmap_grid, apex_add_data_card_grid, apex_add_traffic_light,
)
from apex_mcp.tools.chart_tools import (
    apex_add_animated_counter, apex_add_pareto_chart,
    apex_add_area_chart, apex_add_combo_chart, apex_add_gradient_donut,
)


def ok(label, result_str):
    r = json.loads(result_str)
    if r.get("status") == "error":
        print(f"  ❌ {label}: {r['error']}")
        return False
    print(f"  ✓  {label}")
    return True


SEP = "─" * 60

def section(n, title):
    print(f"\n{SEP}\n  [{n}] {title}\n{SEP}")


def run():
    t0 = time.time()
    print("\n" + "═" * 60)
    print("  App 208 — Portal do Terapeuta TEA")
    print("  Agenda · Pacientes · Avaliações · Evolução · Desempenho")
    print("═" * 60)

    # ──────────────────────────────────────────
    section(1, "Conexão Oracle ADB")
    if not ok("apex_connect", apex_connect()): return

    # ──────────────────────────────────────────
    section(2, "Criar aplicação 208")
    if not ok("apex_create_app", apex_create_app(
        app_id=208, app_name="Portal do Terapeuta TEA",
        app_alias="terapeuta-tea", login_page=100, home_page=1,
        language="pt-br", date_format="DD/MM/YYYY",
    )): return
    if not ok("apex_generate_login(100)", apex_generate_login(100)): return

    # ──────────────────────────────────────────
    section(3, "Minha Agenda — página 1")
    if not ok("apex_add_page(1)", apex_add_page(1, "Minha Agenda", "blank")): return

    ok("hero_banner", apex_add_hero_banner(
        page_id=1,
        title="Portal do Terapeuta",
        subtitle="Acompanhe seus pacientes, avaliações e evolução clínica",
        bg_color="green", sequence=5,
    ))
    ok("metric_cards: indicadores", apex_add_metric_cards(
        page_id=1, region_name="Indicadores do Terapeuta",
        metrics=[
            {"label": "Pacientes Ativos",      "sql": "SELECT COUNT(*) FROM TEA_BENEFICIARIOS WHERE FL_ATIVO='S'",                   "color": "green",  "icon": "fa-users"},
            {"label": "Avaliações Concluídas", "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA'",             "color": "blue",   "icon": "fa-check-circle"},
            {"label": "Em Andamento",          "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='EM_ANDAMENTO'",         "color": "orange", "icon": "fa-spinner"},
            {"label": "Score Médio (%)",        "sql": "SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0", "color": "purple", "icon": "fa-bar-chart"},
        ],
        style="gradient", sequence=10,
    ))
    ok("stat_delta: variação mensal", apex_add_stat_delta(
        page_id=1, region_name="Variação Mensal", sequence=20, columns=4,
        metrics=[
            {"label": "Pacientes Ativos",      "icon": "fa-users",        "color": "green",
             "sql": "SELECT COUNT(*) FROM TEA_BENEFICIARIOS WHERE FL_ATIVO='S'",
             "prev_sql": "SELECT COUNT(*) FROM TEA_BENEFICIARIOS WHERE FL_ATIVO='S' AND DT_CRIACAO < TRUNC(SYSDATE,'MM')"},
            {"label": "Avaliações Concluídas", "icon": "fa-check-circle", "color": "blue",
             "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA'",
             "prev_sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA' AND DT_AVALIACAO < TRUNC(SYSDATE,'MM')"},
            {"label": "Em Andamento",          "icon": "fa-spinner",      "color": "orange",
             "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='EM_ANDAMENTO'",
             "prev_sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='EM_ANDAMENTO' AND DT_AVALIACAO < TRUNC(SYSDATE,'MM')"},
            {"label": "Score Médio (%)",        "icon": "fa-bar-chart",    "color": "purple", "suffix": "%",
             "sql": "SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0",
             "prev_sql": "SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0 AND DT_AVALIACAO < TRUNC(SYSDATE,'MM')"},
        ],
    ))
    ok("animated_counter: total avaliações", apex_add_animated_counter(
        page_id=1, region_name="Total Avaliações",
        sql_query="SELECT COUNT(*) FROM TEA_AVALIACOES",
        label="Total de Avaliações Realizadas",
        color="green", icon="fa-clipboard", sequence=30,
    ))
    ok("activity_stream: avaliações recentes", apex_add_activity_stream(
        page_id=1, region_name="Avaliações Recentes",
        sql_query=(
            "SELECT t.DS_NOME||' — '||b.DS_NOME||' ('||a.DS_STATUS||')' AS TEXT, "
            "a.DT_AVALIACAO AS DT "
            "FROM TEA_AVALIACOES a "
            "JOIN TEA_TERAPEUTAS t ON t.ID_TERAPEUTA = a.ID_TERAPEUTA "
            "JOIN TEA_BENEFICIARIOS b ON b.ID_BENEFICIARIO = a.ID_BENEFICIARIO "
            "ORDER BY a.DT_AVALIACAO DESC FETCH FIRST 15 ROWS ONLY"
        ),
        text_column="TEXT", date_column="DT",
        default_icon="fa-stethoscope", default_color="green",
        max_rows=15, sequence=40,
    ))
    ok("ribbon_stats: resumo sistema", apex_add_ribbon_stats(
        page_id=1, region_name="Resumo do Sistema",
        metrics=[
            {"label": "Terapeutas",   "sql": "SELECT COUNT(*) FROM TEA_TERAPEUTAS WHERE FL_ATIVO='S'",    "icon": "fa-user-md",    "color": "green"},
            {"label": "Clínicas",     "sql": "SELECT COUNT(*) FROM TEA_CLINICAS WHERE FL_ATIVO='S'",      "icon": "fa-hospital-o", "color": "teal"},
            {"label": "Instrumentos", "sql": "SELECT COUNT(*) FROM TEA_PROVAS WHERE FL_ATIVO='S'",        "icon": "fa-list-alt",   "color": "orange"},
            {"label": "Beneficiários","sql": "SELECT COUNT(*) FROM TEA_BENEFICIARIOS WHERE FL_ATIVO='S'", "icon": "fa-users",      "color": "blue"},
        ],
        sequence=50,
    ))

    # ──────────────────────────────────────────
    section(4, "Meus Pacientes — página 10")
    if not ok("apex_add_page(10)", apex_add_page(10, "Meus Pacientes", "blank")): return

    if not ok("region: Beneficiários IR",
        apex_add_region(10, "Beneficiários Atendidos", "report",
            source_sql="""SELECT b.ID_BENEFICIARIO,
       b.DS_NOME,
       b.NR_BENEFICIO,
       b.FL_ATIVO,
       COUNT(a.ID_AVALIACAO)            AS NR_AVALIACOES,
       TO_CHAR(MAX(a.DT_AVALIACAO),'DD/MM/YYYY') AS DT_ULTIMA_AVALIACAO,
       ROUND(AVG(a.NR_PCT_TOTAL),1)     AS NR_SCORE_MEDIO
  FROM TEA_BENEFICIARIOS b
  LEFT JOIN TEA_AVALIACOES a ON a.ID_BENEFICIARIO = b.ID_BENEFICIARIO
 GROUP BY b.ID_BENEFICIARIO, b.DS_NOME, b.NR_BENEFICIO, b.FL_ATIVO
 ORDER BY NR_AVALIACOES DESC""")): return

    ok("leaderboard: top pacientes", apex_add_leaderboard(
        page_id=10, region_name="Top Pacientes por Avaliações",
        sql_query=(
            "SELECT b.DS_NOME AS LABEL, COUNT(a.ID_AVALIACAO) AS VALUE "
            "FROM TEA_BENEFICIARIOS b "
            "LEFT JOIN TEA_AVALIACOES a ON a.ID_BENEFICIARIO = b.ID_BENEFICIARIO "
            "GROUP BY b.DS_NOME ORDER BY 2 DESC FETCH FIRST 10 ROWS ONLY"
        ),
        color="green", max_rows=10, sequence=20,
    ))
    ok("percent_bars: status pacientes", apex_add_percent_bars(
        page_id=10, region_name="Pacientes por Status",
        sql_query=(
            "SELECT CASE FL_ATIVO WHEN 'S' THEN 'Ativo' ELSE 'Inativo' END AS LABEL, "
            "COUNT(*) AS VALUE FROM TEA_BENEFICIARIOS GROUP BY FL_ATIVO ORDER BY 2 DESC"
        ),
        color="green", sequence=30,
    ))
    ok("data_card_grid: cards pacientes", apex_add_data_card_grid(
        page_id=10, region_name="Visão em Cards dos Pacientes",
        sql_query=(
            "SELECT b.DS_NOME AS TITLE, b.NR_BENEFICIO AS SUBTITLE, "
            "COUNT(a.ID_AVALIACAO) AS VALUE, "
            "CASE b.FL_ATIVO WHEN 'S' THEN 'Ativo' ELSE 'Inativo' END AS BADGE "
            "FROM TEA_BENEFICIARIOS b "
            "LEFT JOIN TEA_AVALIACOES a ON a.ID_BENEFICIARIO = b.ID_BENEFICIARIO "
            "GROUP BY b.DS_NOME, b.NR_BENEFICIO, b.FL_ATIVO "
            "ORDER BY VALUE DESC FETCH FIRST 9 ROWS ONLY"
        ),
        title_column="TITLE", subtitle_column="SUBTITLE",
        value_column="VALUE", badge_column="BADGE",
        color="green", columns=3, sequence=40,
    ))

    # ──────────────────────────────────────────
    section(5, "Minhas Avaliações — página 20")
    if not ok("apex_add_page(20)", apex_add_page(20, "Minhas Avaliações", "blank")): return

    if not ok("region: Avaliações IR",
        apex_add_region(20, "Registro de Avaliações", "report",
            source_sql="""SELECT a.ID_AVALIACAO,
       b.DS_NOME        AS PACIENTE,
       p.DS_NOME        AS INSTRUMENTO,
       t.DS_NOME        AS TERAPEUTA,
       TO_CHAR(a.DT_AVALIACAO,'DD/MM/YYYY') AS DATA_AVALIACAO,
       a.DS_STATUS,
       a.NR_PCT_TOTAL   AS PCT
  FROM TEA_AVALIACOES a
  JOIN TEA_BENEFICIARIOS b ON b.ID_BENEFICIARIO = a.ID_BENEFICIARIO
  JOIN TEA_PROVAS p        ON p.ID_PROVA        = a.ID_PROVA
  JOIN TEA_TERAPEUTAS t    ON t.ID_TERAPEUTA    = a.ID_TERAPEUTA
 ORDER BY a.DT_AVALIACAO DESC""")): return

    ok("animated_counter: concluídas", apex_add_animated_counter(
        page_id=20, region_name="Avaliações Concluídas",
        sql_query="SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA'",
        label="Avaliações Concluídas no Sistema",
        color="blue", icon="fa-check-circle", sequence=20,
    ))
    ok("percent_bars: status avaliações", apex_add_percent_bars(
        page_id=20, region_name="Distribuição por Status",
        sql_query="SELECT DS_STATUS AS LABEL, COUNT(*) AS VALUE FROM TEA_AVALIACOES GROUP BY DS_STATUS ORDER BY 2 DESC",
        color="blue", sequence=30,
    ))
    ok("activity_stream: feed avaliações", apex_add_activity_stream(
        page_id=20, region_name="Feed de Avaliações",
        sql_query=(
            "SELECT b.DS_NOME||' — '||p.DS_NOME||' ('||a.DS_STATUS||')' AS TEXT, "
            "a.DT_AVALIACAO AS DT "
            "FROM TEA_AVALIACOES a "
            "JOIN TEA_BENEFICIARIOS b ON b.ID_BENEFICIARIO = a.ID_BENEFICIARIO "
            "JOIN TEA_PROVAS p ON p.ID_PROVA = a.ID_PROVA "
            "ORDER BY a.DT_AVALIACAO DESC FETCH FIRST 20 ROWS ONLY"
        ),
        text_column="TEXT", date_column="DT",
        default_icon="fa-clipboard", default_color="blue",
        max_rows=20, sequence=40,
    ))

    # ──────────────────────────────────────────
    section(6, "Evolução dos Pacientes — página 30")
    if not ok("apex_add_page(30)", apex_add_page(30, "Evolução dos Pacientes", "blank")): return

    ok("spotlight: score médio geral", apex_add_spotlight_metric(
        page_id=30, region_name="Score Médio Global",
        sql_query="SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0",
        label="Score Médio Global dos Pacientes",
        color="purple", icon="fa-line-chart", suffix="%", sequence=5,
    ))
    ok("area_chart: evolução por status/mês", apex_add_area_chart(
        page_id=30, region_name="Evolução Mensal por Status",
        series_list=[
            {"name": "Concluída",    "sql": "SELECT TO_CHAR(DT_AVALIACAO,'MM/YYYY') AS L, COUNT(*) AS V FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA'    GROUP BY TO_CHAR(DT_AVALIACAO,'MM/YYYY') ORDER BY MIN(DT_AVALIACAO)", "label_col": "L", "value_col": "V", "color": "#43A047"},
            {"name": "Em Andamento", "sql": "SELECT TO_CHAR(DT_AVALIACAO,'MM/YYYY') AS L, COUNT(*) AS V FROM TEA_AVALIACOES WHERE DS_STATUS='EM_ANDAMENTO' GROUP BY TO_CHAR(DT_AVALIACAO,'MM/YYYY') ORDER BY MIN(DT_AVALIACAO)", "label_col": "L", "value_col": "V", "color": "#FF9800"},
            {"name": "Rascunho",     "sql": "SELECT TO_CHAR(DT_AVALIACAO,'MM/YYYY') AS L, COUNT(*) AS V FROM TEA_AVALIACOES WHERE DS_STATUS='RASCUNHO'     GROUP BY TO_CHAR(DT_AVALIACAO,'MM/YYYY') ORDER BY MIN(DT_AVALIACAO)", "label_col": "L", "value_col": "V", "color": "#1E88E5"},
        ],
        height=320, stacked=True,
        y_axis_title="Avaliações", x_axis_title="Mês/Ano",
        sequence=10,
    ))
    ok("combo_chart: avaliações + score por mês", apex_add_combo_chart(
        page_id=30, region_name="Avaliações e Score Médio por Mês",
        bar_sql=(
            "SELECT TO_CHAR(DT_AVALIACAO,'MM/YYYY') AS L, COUNT(*) AS V "
            "FROM TEA_AVALIACOES GROUP BY TO_CHAR(DT_AVALIACAO,'MM/YYYY') "
            "ORDER BY MIN(DT_AVALIACAO)"
        ),
        line_sql=(
            "SELECT TO_CHAR(DT_AVALIACAO,'MM/YYYY') AS L, ROUND(AVG(NR_PCT_TOTAL),1) AS V "
            "FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0 "
            "GROUP BY TO_CHAR(DT_AVALIACAO,'MM/YYYY') ORDER BY MIN(DT_AVALIACAO)"
        ),
        bar_name="Avaliações", line_name="Score Médio (%)",
        bar_label_col="L", bar_value_col="V",
        line_label_col="L", line_value_col="V",
        height=320, y_axis_title="Avaliações", y2_axis_title="Score (%)",
        sequence=20,
    ))
    ok("comparison_panel: este mês vs anterior", apex_add_comparison_panel(
        page_id=30, region_name="Comparativo Mensal",
        left_label="Este Mês",
        left_metrics=[
            {"label": "Avaliações",  "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DT_AVALIACAO >= TRUNC(SYSDATE,'MM')"},
            {"label": "Concluídas",  "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA' AND DT_AVALIACAO >= TRUNC(SYSDATE,'MM')"},
            {"label": "Score Médio", "sql": "SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0 AND DT_AVALIACAO >= TRUNC(SYSDATE,'MM')"},
            {"label": "Em Andamento","sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='EM_ANDAMENTO' AND DT_AVALIACAO >= TRUNC(SYSDATE,'MM')"},
        ],
        right_label="Mês Anterior",
        right_metrics=[
            {"label": "Avaliações",  "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DT_AVALIACAO >= ADD_MONTHS(TRUNC(SYSDATE,'MM'),-1) AND DT_AVALIACAO < TRUNC(SYSDATE,'MM')"},
            {"label": "Concluídas",  "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA' AND DT_AVALIACAO >= ADD_MONTHS(TRUNC(SYSDATE,'MM'),-1) AND DT_AVALIACAO < TRUNC(SYSDATE,'MM')"},
            {"label": "Score Médio", "sql": "SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0 AND DT_AVALIACAO >= ADD_MONTHS(TRUNC(SYSDATE,'MM'),-1) AND DT_AVALIACAO < TRUNC(SYSDATE,'MM')"},
            {"label": "Em Andamento","sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='EM_ANDAMENTO' AND DT_AVALIACAO >= ADD_MONTHS(TRUNC(SYSDATE,'MM'),-1) AND DT_AVALIACAO < TRUNC(SYSDATE,'MM')"},
        ],
        left_color="blue", right_color="green", sequence=30,
    ))
    ok("heatmap_grid: paciente x instrumento", apex_add_heatmap_grid(
        page_id=30, region_name="Score por Paciente e Instrumento",
        sql_query=(
            "SELECT b.DS_NOME AS ROW_LABEL, p.DS_NOME AS COL_LABEL, "
            "ROUND(AVG(a.NR_PCT_TOTAL),0) AS VALUE "
            "FROM TEA_AVALIACOES a "
            "JOIN TEA_BENEFICIARIOS b ON b.ID_BENEFICIARIO = a.ID_BENEFICIARIO "
            "JOIN TEA_PROVAS p ON p.ID_PROVA = a.ID_PROVA "
            "WHERE a.NR_PCT_TOTAL > 0 "
            "GROUP BY b.DS_NOME, p.DS_NOME "
            "ORDER BY b.DS_NOME, p.DS_NOME"
        ),
        row_column="ROW_LABEL", col_column="COL_LABEL", value_column="VALUE",
        color="purple", sequence=40,
    ))

    # ──────────────────────────────────────────
    section(7, "Por Instrumento — página 40")
    if not ok("apex_add_page(40)", apex_add_page(40, "Por Instrumento", "blank")): return

    ok("kpi_row: 4 instrumentos", apex_add_kpi_row(
        page_id=40, region_name="Avaliações por Instrumento",
        metrics=[
            {"label": "VINELAND", "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES a JOIN TEA_PROVAS p ON p.ID_PROVA=a.ID_PROVA WHERE p.DS_NOME LIKE '%VINELAND%'", "color": "blue"},
            {"label": "CBCL",     "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES a JOIN TEA_PROVAS p ON p.ID_PROVA=a.ID_PROVA WHERE p.DS_NOME LIKE '%CBCL%'",     "color": "orange"},
            {"label": "CFQL2",    "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES a JOIN TEA_PROVAS p ON p.ID_PROVA=a.ID_PROVA WHERE p.DS_NOME LIKE '%CFQL%'",    "color": "green"},
            {"label": "RBS-R",    "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES a JOIN TEA_PROVAS p ON p.ID_PROVA=a.ID_PROVA WHERE p.DS_NOME LIKE '%RBS%'",    "color": "purple"},
        ],
        sequence=5,
    ))
    ok("pareto: avaliações por instrumento", apex_add_pareto_chart(
        page_id=40, region_name="Pareto — Avaliações por Instrumento",
        sql_query=(
            "SELECT p.DS_NOME AS LABEL, COUNT(a.ID_AVALIACAO) AS VALUE "
            "FROM TEA_PROVAS p LEFT JOIN TEA_AVALIACOES a ON a.ID_PROVA = p.ID_PROVA "
            "WHERE p.FL_ATIVO='S' GROUP BY p.DS_NOME ORDER BY 2 DESC"
        ),
        bar_name="Avaliações", line_name="Acumulado %", height=340, sequence=10,
    ))
    ok("percent_bars: distribuição instrumento", apex_add_percent_bars(
        page_id=40, region_name="Distribuição por Instrumento",
        sql_query=(
            "SELECT p.DS_NOME AS LABEL, COUNT(a.ID_AVALIACAO) AS VALUE "
            "FROM TEA_PROVAS p JOIN TEA_AVALIACOES a ON a.ID_PROVA = p.ID_PROVA "
            "WHERE p.FL_ATIVO='S' GROUP BY p.DS_NOME ORDER BY 2 DESC"
        ),
        color="orange", sequence=20,
    ))
    ok("gradient_donut: proporção instrumentos", apex_add_gradient_donut(
        page_id=40, region_name="Proporção por Instrumento",
        sql_query=(
            "SELECT p.DS_NOME AS LABEL, COUNT(a.ID_AVALIACAO) AS VALUE "
            "FROM TEA_PROVAS p JOIN TEA_AVALIACOES a ON a.ID_PROVA = p.ID_PROVA "
            "WHERE p.FL_ATIVO='S' GROUP BY p.DS_NOME ORDER BY 2 DESC"
        ),
        label_column="LABEL", value_column="VALUE",
        series_name="Instrumentos", height=300, sequence=30,
    ))
    ok("data_card_grid: detalhes por instrumento", apex_add_data_card_grid(
        page_id=40, region_name="Detalhes por Instrumento",
        sql_query=(
            "SELECT p.DS_NOME AS TITLE, "
            "'Avaliações: '||COUNT(a.ID_AVALIACAO) AS SUBTITLE, "
            "ROUND(AVG(a.NR_PCT_TOTAL),1) AS VALUE, "
            "CASE WHEN COUNT(a.ID_AVALIACAO)>0 THEN 'Ativo' ELSE 'Sem dados' END AS BADGE "
            "FROM TEA_PROVAS p LEFT JOIN TEA_AVALIACOES a ON a.ID_PROVA = p.ID_PROVA "
            "WHERE p.FL_ATIVO='S' GROUP BY p.DS_NOME ORDER BY VALUE DESC NULLS LAST"
        ),
        title_column="TITLE", subtitle_column="SUBTITLE",
        value_column="VALUE", badge_column="BADGE",
        color="orange", columns=2, sequence=40,
    ))

    # ──────────────────────────────────────────
    section(8, "Meu Desempenho — página 50")
    if not ok("apex_add_page(50)", apex_add_page(50, "Meu Desempenho", "blank")): return

    ok("spotlight: score médio terapeutas", apex_add_spotlight_metric(
        page_id=50, region_name="Score Médio Geral dos Terapeutas",
        sql_query="SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0",
        label="Score Médio de Todas as Avaliações",
        color="teal", icon="fa-trophy", suffix="%", sequence=5,
    ))
    ok("stat_delta: desempenho mensal", apex_add_stat_delta(
        page_id=50, region_name="Desempenho Mensal dos Terapeutas",
        sequence=10, columns=4,
        metrics=[
            {"label": "Avaliações (Mês)",   "icon": "fa-clipboard",    "color": "blue",
             "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DT_AVALIACAO >= TRUNC(SYSDATE,'MM')",
             "prev_sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DT_AVALIACAO >= ADD_MONTHS(TRUNC(SYSDATE,'MM'),-1) AND DT_AVALIACAO < TRUNC(SYSDATE,'MM')"},
            {"label": "Concluídas (Mês)",   "icon": "fa-check-circle", "color": "green",
             "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA' AND DT_AVALIACAO >= TRUNC(SYSDATE,'MM')",
             "prev_sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA' AND DT_AVALIACAO >= ADD_MONTHS(TRUNC(SYSDATE,'MM'),-1) AND DT_AVALIACAO < TRUNC(SYSDATE,'MM')"},
            {"label": "Score Médio (%)",    "icon": "fa-bar-chart",    "color": "purple", "suffix": "%",
             "sql": "SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0 AND DT_AVALIACAO >= TRUNC(SYSDATE,'MM')",
             "prev_sql": "SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0 AND DT_AVALIACAO >= ADD_MONTHS(TRUNC(SYSDATE,'MM'),-1) AND DT_AVALIACAO < TRUNC(SYSDATE,'MM')"},
            {"label": "Terapeutas Ativos",  "icon": "fa-user-md",      "color": "teal",
             "sql": "SELECT COUNT(DISTINCT ID_TERAPEUTA) FROM TEA_AVALIACOES WHERE DT_AVALIACAO >= TRUNC(SYSDATE,'MM')",
             "prev_sql": "SELECT COUNT(DISTINCT ID_TERAPEUTA) FROM TEA_AVALIACOES WHERE DT_AVALIACAO >= ADD_MONTHS(TRUNC(SYSDATE,'MM'),-1) AND DT_AVALIACAO < TRUNC(SYSDATE,'MM')"},
        ],
    ))
    ok("leaderboard: ranking terapeutas", apex_add_leaderboard(
        page_id=50, region_name="Ranking de Terapeutas por Avaliações",
        sql_query=(
            "SELECT t.DS_NOME AS LABEL, COUNT(a.ID_AVALIACAO) AS VALUE "
            "FROM TEA_TERAPEUTAS t "
            "LEFT JOIN TEA_AVALIACOES a ON a.ID_TERAPEUTA = t.ID_TERAPEUTA "
            "WHERE t.FL_ATIVO='S' GROUP BY t.DS_NOME ORDER BY 2 DESC FETCH FIRST 10 ROWS ONLY"
        ),
        color="teal", max_rows=10, sequence=20,
    ))
    ok("comparison_panel: este mês vs anterior p50", apex_add_comparison_panel(
        page_id=50, region_name="Comparativo Mensal de Terapeutas",
        left_label="Este Mês",
        left_metrics=[
            {"label": "Avaliações",    "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DT_AVALIACAO >= TRUNC(SYSDATE,'MM')"},
            {"label": "Concluídas",    "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA' AND DT_AVALIACAO >= TRUNC(SYSDATE,'MM')"},
            {"label": "Score Médio",   "sql": "SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0 AND DT_AVALIACAO >= TRUNC(SYSDATE,'MM')"},
            {"label": "Terapeutas",    "sql": "SELECT COUNT(DISTINCT ID_TERAPEUTA) FROM TEA_AVALIACOES WHERE DT_AVALIACAO >= TRUNC(SYSDATE,'MM')"},
        ],
        right_label="Mês Anterior",
        right_metrics=[
            {"label": "Avaliações",    "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DT_AVALIACAO >= ADD_MONTHS(TRUNC(SYSDATE,'MM'),-1) AND DT_AVALIACAO < TRUNC(SYSDATE,'MM')"},
            {"label": "Concluídas",    "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA' AND DT_AVALIACAO >= ADD_MONTHS(TRUNC(SYSDATE,'MM'),-1) AND DT_AVALIACAO < TRUNC(SYSDATE,'MM')"},
            {"label": "Score Médio",   "sql": "SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0 AND DT_AVALIACAO >= ADD_MONTHS(TRUNC(SYSDATE,'MM'),-1) AND DT_AVALIACAO < TRUNC(SYSDATE,'MM')"},
            {"label": "Terapeutas",    "sql": "SELECT COUNT(DISTINCT ID_TERAPEUTA) FROM TEA_AVALIACOES WHERE DT_AVALIACAO >= ADD_MONTHS(TRUNC(SYSDATE,'MM'),-1) AND DT_AVALIACAO < TRUNC(SYSDATE,'MM')"},
        ],
        left_color="teal", right_color="blue", sequence=30,
    ))
    ok("percent_bars: avaliações por terapeuta", apex_add_percent_bars(
        page_id=50, region_name="Distribuição de Avaliações por Terapeuta",
        sql_query=(
            "SELECT t.DS_NOME AS LABEL, COUNT(a.ID_AVALIACAO) AS VALUE "
            "FROM TEA_TERAPEUTAS t "
            "JOIN TEA_AVALIACOES a ON a.ID_TERAPEUTA = t.ID_TERAPEUTA "
            "WHERE t.FL_ATIVO='S' GROUP BY t.DS_NOME ORDER BY 2 DESC FETCH FIRST 10 ROWS ONLY"
        ),
        color="teal", sequence=40,
    ))
    ok("traffic_light: status operacional", apex_add_traffic_light(
        page_id=50, region_name="Status Operacional",
        sql_query=(
            "SELECT 'Avaliações Pendentes' AS LABEL, "
            "CASE WHEN COUNT(*) = 0 THEN 'GREEN' WHEN COUNT(*) <= 5 THEN 'YELLOW' ELSE 'RED' END AS STATUS "
            "FROM TEA_AVALIACOES WHERE DS_STATUS='EM_ANDAMENTO' "
            "UNION ALL "
            "SELECT 'Terapeutas Ativos', "
            "CASE WHEN COUNT(*) >= 10 THEN 'GREEN' WHEN COUNT(*) >= 5 THEN 'YELLOW' ELSE 'RED' END "
            "FROM TEA_TERAPEUTAS WHERE FL_ATIVO='S' "
            "UNION ALL "
            "SELECT 'Pacientes Ativos', "
            "CASE WHEN COUNT(*) >= 20 THEN 'GREEN' WHEN COUNT(*) >= 10 THEN 'YELLOW' ELSE 'RED' END "
            "FROM TEA_BENEFICIARIOS WHERE FL_ATIVO='S' "
            "UNION ALL "
            "SELECT 'Instrumentos Disponíveis', "
            "CASE WHEN COUNT(*) >= 4 THEN 'GREEN' WHEN COUNT(*) >= 2 THEN 'YELLOW' ELSE 'RED' END "
            "FROM TEA_PROVAS WHERE FL_ATIVO='S'"
        ),
        label_column="LABEL", status_column="STATUS", sequence=50,
    ))

    # ──────────────────────────────────────────
    section(9, "Navegação")
    if not ok("nav: Minha Agenda",    apex_add_nav_item("Minha Agenda",    1,  10, "fa-calendar")): return
    if not ok("nav: Meus Pacientes",  apex_add_nav_item("Meus Pacientes",  10, 20, "fa-users")): return
    if not ok("nav: Avaliações",      apex_add_nav_item("Avaliações",      20, 30, "fa-clipboard")): return
    if not ok("nav: Evolução",        apex_add_nav_item("Evolução",        30, 40, "fa-line-chart")): return
    if not ok("nav: Por Instrumento", apex_add_nav_item("Por Instrumento", 40, 50, "fa-list-alt")): return
    if not ok("nav: Meu Desempenho",  apex_add_nav_item("Meu Desempenho",  50, 60, "fa-trophy")): return

    # ──────────────────────────────────────────
    section(10, "Finalizar")
    r = apex_finalize_app()
    rj = json.loads(r)
    if rj.get("status") == "error":
        print(f"  ❌ apex_finalize_app: {rj['error']}")
        return

    elapsed = time.time() - t0
    summary = rj.get("summary", {})
    print(f"  ✓  apex_finalize_app")

    pages_detail = [
        ("100", "Login"),
        ("  1", "Minha Agenda      (hero + metric_cards + stat_delta + animated_counter + activity_stream)"),
        (" 10", "Meus Pacientes    (IR + leaderboard + percent_bars + data_card_grid)"),
        (" 20", "Minhas Avaliações (IR + animated_counter + percent_bars + activity_stream)"),
        (" 30", "Evolução          (spotlight + area_chart + combo_chart + comparison_panel + heatmap_grid)"),
        (" 40", "Por Instrumento   (kpi_row + pareto + percent_bars + gradient_donut + data_card_grid)"),
        (" 50", "Meu Desempenho    (spotlight + stat_delta + leaderboard + comparison_panel + traffic_light)"),
    ]

    print(f"""
{'═'*60}
  App 208 — Portal do Terapeuta TEA
  Construído em {elapsed:.1f}s
  Páginas : {summary.get('pages')}
  Regiões : {summary.get('regions')}
  Itens   : {summary.get('items')}

  Páginas ({len(pages_detail)}):""")
    for pid, desc in pages_detail:
        print(f"    {pid}  {desc}")
    print(f"""
  URL: f?p=208
  Login: cnu.admin / Unimed@2024
{'═'*60}""")


if __name__ == "__main__":
    run()
