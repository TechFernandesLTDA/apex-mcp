"""Build App 209 — Relatórios Clínicos TEA."""
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
    apex_add_animated_counter, apex_add_pareto_chart, apex_add_stacked_chart,
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
    print("  App 209 — Relatórios Clínicos TEA")
    print("  Evolução · Instrumentos · Dimensões · Clínicas · Histórico")
    print("═" * 60)

    # ──────────────────────────────────────────
    section(1, "Conexão Oracle ADB")
    if not ok("apex_connect", apex_connect()): return

    # ──────────────────────────────────────────
    section(2, "Criar aplicação 209")
    if not ok("apex_create_app", apex_create_app(
        app_id=209, app_name="Relatórios Clínicos TEA",
        app_alias="relatorios-tea", login_page=100, home_page=1,
        language="pt-br", date_format="DD/MM/YYYY",
    )): return
    if not ok("apex_generate_login(100)", apex_generate_login(100)): return

    # ──────────────────────────────────────────
    section(3, "Painel de Relatórios — página 1")
    if not ok("apex_add_page(1)", apex_add_page(1, "Painel de Relatórios", "blank")): return

    ok("hero_banner", apex_add_hero_banner(
        page_id=1,
        title="Relatórios Clínicos TEA",
        subtitle="Evolução longitudinal de scores, comparativos e análise por dimensão ICHOM",
        bg_color="purple", sequence=5,
    ))
    ok("metric_cards: indicadores", apex_add_metric_cards(
        page_id=1, region_name="Indicadores Clínicos",
        metrics=[
            {"label": "Beneficiários Ativos",  "sql": "SELECT COUNT(*) FROM TEA_BENEFICIARIOS WHERE FL_ATIVO='S'",                          "color": "purple", "icon": "fa-users"},
            {"label": "Avaliações Concluídas", "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA'",                    "color": "green",  "icon": "fa-check-circle"},
            {"label": "Score Médio (%)",        "sql": "SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0",         "color": "blue",   "icon": "fa-bar-chart"},
            {"label": "Instrumentos Ativos",   "sql": "SELECT COUNT(*) FROM TEA_PROVAS WHERE FL_ATIVO='S'",                                 "color": "orange", "icon": "fa-list-alt"},
        ],
        style="gradient", sequence=10,
    ))
    ok("stat_delta: variação mensal", apex_add_stat_delta(
        page_id=1, region_name="Variação Mensal", sequence=20, columns=4,
        metrics=[
            {"label": "Beneficiários Ativos",  "icon": "fa-users",        "color": "purple",
             "sql": "SELECT COUNT(*) FROM TEA_BENEFICIARIOS WHERE FL_ATIVO='S'",
             "prev_sql": "SELECT COUNT(*) FROM TEA_BENEFICIARIOS WHERE FL_ATIVO='S' AND DT_CRIACAO < TRUNC(SYSDATE,'MM')"},
            {"label": "Avaliações Concluídas", "icon": "fa-check-circle", "color": "green",
             "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA'",
             "prev_sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA' AND DT_AVALIACAO < TRUNC(SYSDATE,'MM')"},
            {"label": "Score Médio (%)",        "icon": "fa-bar-chart",    "color": "blue", "suffix": "%",
             "sql": "SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0",
             "prev_sql": "SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0 AND DT_AVALIACAO < TRUNC(SYSDATE,'MM')"},
            {"label": "Em Andamento",          "icon": "fa-spinner",      "color": "orange",
             "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='EM_ANDAMENTO'",
             "prev_sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='EM_ANDAMENTO' AND DT_AVALIACAO < TRUNC(SYSDATE,'MM')"},
        ],
    ))
    ok("animated_counter: avaliações", apex_add_animated_counter(
        page_id=1, region_name="Total de Avaliações",
        sql_query="SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA'",
        label="Avaliações Clínicas Concluídas",
        color="purple", icon="fa-stethoscope", sequence=30,
    ))
    ok("ribbon_stats: resumo clínico", apex_add_ribbon_stats(
        page_id=1, region_name="Resumo Clínico",
        metrics=[
            {"label": "Clínicas",    "sql": "SELECT COUNT(*) FROM TEA_CLINICAS WHERE FL_ATIVO='S'",   "icon": "fa-hospital-o",  "color": "teal"},
            {"label": "Terapeutas",  "sql": "SELECT COUNT(*) FROM TEA_TERAPEUTAS WHERE FL_ATIVO='S'", "icon": "fa-user-md",     "color": "purple"},
            {"label": "Avaliações",  "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES",                    "icon": "fa-clipboard",   "color": "blue"},
            {"label": "Dimensões",   "sql": "SELECT COUNT(DISTINCT ID_DIMENSAO) FROM TEA_AVALIACAO_DIMENSOES", "icon": "fa-th",  "color": "orange"},
        ],
        sequence=40,
    ))

    # ──────────────────────────────────────────
    section(4, "Evolução por Paciente — página 10")
    if not ok("apex_add_page(10)", apex_add_page(10, "Evolução por Paciente", "blank")): return

    if not ok("region: VW_TEA_EVOLUCAO_BENEFICIARIO IR",
        apex_add_region(10, "Evolução dos Beneficiários", "report",
            source_sql="""SELECT BENEFICIARIO,
       NR_BENEFICIO,
       CLINICA,
       PROVA         AS INSTRUMENTO,
       NR_COLETA,
       TO_CHAR(DT_AVALIACAO,'DD/MM/YYYY') AS DT_AVALIACAO,
       SCORE_PCT,
       SCORE_ANTERIOR,
       VARIACAO
  FROM VW_TEA_EVOLUCAO_BENEFICIARIO
 ORDER BY BENEFICIARIO, PROVA, NR_COLETA DESC""")): return

    ok("spotlight: score médio geral", apex_add_spotlight_metric(
        page_id=10, region_name="Score Médio das Avaliações Concluídas",
        sql_query="SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA' AND NR_PCT_TOTAL>0",
        label="Score Médio Geral — Avaliações Concluídas",
        color="purple", icon="fa-line-chart", suffix="%", sequence=20,
    ))
    ok("area_chart: evolução score por mês", apex_add_area_chart(
        page_id=10, region_name="Evolução do Score Médio por Mês",
        series_list=[
            {"name": "Score Médio (%)",
             "sql": "SELECT TO_CHAR(DT_AVALIACAO,'MM/YYYY') AS L, ROUND(AVG(NR_PCT_TOTAL),1) AS V FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA' AND NR_PCT_TOTAL>0 GROUP BY TO_CHAR(DT_AVALIACAO,'MM/YYYY') ORDER BY MIN(DT_AVALIACAO)",
             "label_col": "L", "value_col": "V", "color": "#9C27B0"},
            {"name": "Máximo (%)",
             "sql": "SELECT TO_CHAR(DT_AVALIACAO,'MM/YYYY') AS L, MAX(NR_PCT_TOTAL) AS V FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA' AND NR_PCT_TOTAL>0 GROUP BY TO_CHAR(DT_AVALIACAO,'MM/YYYY') ORDER BY MIN(DT_AVALIACAO)",
             "label_col": "L", "value_col": "V", "color": "#43A047"},
        ],
        height=300, stacked=False,
        y_axis_title="Score (%)", x_axis_title="Mês/Ano",
        sequence=30,
    ))
    ok("comparison_panel: 1ª coleta vs última", apex_add_comparison_panel(
        page_id=10, region_name="Comparativo de Evolução: 1ª vs Última Coleta",
        left_label="1ª Coleta",
        left_metrics=[
            {"label": "Score Médio",  "sql": "SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM VW_TEA_EVOLUCAO_BENEFICIARIO WHERE NR_COLETA=1 AND SCORE_PCT>0"},
            {"label": "Avaliações",   "sql": "SELECT COUNT(*) FROM VW_TEA_EVOLUCAO_BENEFICIARIO WHERE NR_COLETA=1"},
            {"label": "Pacientes",    "sql": "SELECT COUNT(DISTINCT ID_BENEFICIARIO) FROM VW_TEA_EVOLUCAO_BENEFICIARIO WHERE NR_COLETA=1"},
            {"label": "Clínicas",     "sql": "SELECT COUNT(DISTINCT CLINICA) FROM VW_TEA_EVOLUCAO_BENEFICIARIO WHERE NR_COLETA=1"},
        ],
        right_label="Última Coleta",
        right_metrics=[
            {"label": "Score Médio",  "sql": "SELECT ROUND(AVG(v.SCORE_PCT),1) FROM VW_TEA_EVOLUCAO_BENEFICIARIO v JOIN (SELECT ID_BENEFICIARIO, ID_PROVA, MAX(NR_COLETA) AS MAX_C FROM TEA_AVALIACOES GROUP BY ID_BENEFICIARIO, ID_PROVA) m ON v.ID_BENEFICIARIO=m.ID_BENEFICIARIO AND v.NR_COLETA=m.MAX_C WHERE v.SCORE_PCT>0"},
            {"label": "Avaliações",   "sql": "SELECT COUNT(*) FROM VW_TEA_EVOLUCAO_BENEFICIARIO v JOIN (SELECT ID_BENEFICIARIO, ID_PROVA, MAX(NR_COLETA) AS MAX_C FROM TEA_AVALIACOES GROUP BY ID_BENEFICIARIO, ID_PROVA) m ON v.ID_BENEFICIARIO=m.ID_BENEFICIARIO AND v.NR_COLETA=m.MAX_C"},
            {"label": "Pacientes",    "sql": "SELECT COUNT(DISTINCT ID_BENEFICIARIO) FROM VW_TEA_EVOLUCAO_BENEFICIARIO"},
            {"label": "Com Melhora",  "sql": "SELECT COUNT(*) FROM VW_TEA_EVOLUCAO_BENEFICIARIO WHERE VARIACAO > 0"},
        ],
        left_color="blue", right_color="green", sequence=40,
    ))
    ok("heatmap_grid: beneficiário x instrumento", apex_add_heatmap_grid(
        page_id=10, region_name="Score por Beneficiário e Instrumento",
        sql_query=(
            "SELECT BENEFICIARIO AS ROW_LABEL, PROVA AS COL_LABEL, "
            "ROUND(AVG(SCORE_PCT),0) AS VALUE "
            "FROM VW_TEA_EVOLUCAO_BENEFICIARIO "
            "WHERE SCORE_PCT > 0 "
            "GROUP BY BENEFICIARIO, PROVA "
            "ORDER BY BENEFICIARIO, PROVA"
        ),
        row_column="ROW_LABEL", col_column="COL_LABEL", value_column="VALUE",
        color="purple", sequence=50,
    ))

    # ──────────────────────────────────────────
    section(5, "Comparativo por Instrumento — página 20")
    if not ok("apex_add_page(20)", apex_add_page(20, "Comparativo por Instrumento", "blank")): return

    ok("kpi_row: score médio por instrumento", apex_add_kpi_row(
        page_id=20, region_name="Score Médio por Instrumento",
        metrics=[
            {"label": "VINELAND", "sql": "SELECT ROUND(AVG(a.NR_PCT_TOTAL),1)||'%' FROM TEA_AVALIACOES a JOIN TEA_PROVAS p ON p.ID_PROVA=a.ID_PROVA WHERE p.DS_NOME LIKE '%VINELAND%' AND a.NR_PCT_TOTAL>0", "color": "blue"},
            {"label": "CBCL",     "sql": "SELECT ROUND(AVG(a.NR_PCT_TOTAL),1)||'%' FROM TEA_AVALIACOES a JOIN TEA_PROVAS p ON p.ID_PROVA=a.ID_PROVA WHERE p.DS_NOME LIKE '%CBCL%'     AND a.NR_PCT_TOTAL>0", "color": "orange"},
            {"label": "CFQL2",    "sql": "SELECT ROUND(AVG(a.NR_PCT_TOTAL),1)||'%' FROM TEA_AVALIACOES a JOIN TEA_PROVAS p ON p.ID_PROVA=a.ID_PROVA WHERE p.DS_NOME LIKE '%CFQL%'    AND a.NR_PCT_TOTAL>0", "color": "green"},
            {"label": "RBS-R",    "sql": "SELECT ROUND(AVG(a.NR_PCT_TOTAL),1)||'%' FROM TEA_AVALIACOES a JOIN TEA_PROVAS p ON p.ID_PROVA=a.ID_PROVA WHERE p.DS_NOME LIKE '%RBS%'    AND a.NR_PCT_TOTAL>0", "color": "purple"},
        ],
        sequence=5,
    ))
    ok("stacked_chart: avaliações por instrumento/mês", apex_add_stacked_chart(
        page_id=20, region_name="Avaliações por Instrumento e Mês",
        series_list=[
            {"name": "VINELAND",
             "sql": "SELECT TO_CHAR(a.DT_AVALIACAO,'MM/YYYY') AS LABEL, COUNT(*) AS VALUE FROM TEA_AVALIACOES a JOIN TEA_PROVAS p ON p.ID_PROVA=a.ID_PROVA WHERE p.DS_NOME LIKE '%VINELAND%' GROUP BY TO_CHAR(a.DT_AVALIACAO,'MM/YYYY') ORDER BY MIN(a.DT_AVALIACAO)",
             "color": "#1E88E5"},
            {"name": "CBCL",
             "sql": "SELECT TO_CHAR(a.DT_AVALIACAO,'MM/YYYY') AS LABEL, COUNT(*) AS VALUE FROM TEA_AVALIACOES a JOIN TEA_PROVAS p ON p.ID_PROVA=a.ID_PROVA WHERE p.DS_NOME LIKE '%CBCL%'     GROUP BY TO_CHAR(a.DT_AVALIACAO,'MM/YYYY') ORDER BY MIN(a.DT_AVALIACAO)",
             "color": "#FF9800"},
            {"name": "CFQL2",
             "sql": "SELECT TO_CHAR(a.DT_AVALIACAO,'MM/YYYY') AS LABEL, COUNT(*) AS VALUE FROM TEA_AVALIACOES a JOIN TEA_PROVAS p ON p.ID_PROVA=a.ID_PROVA WHERE p.DS_NOME LIKE '%CFQL%'    GROUP BY TO_CHAR(a.DT_AVALIACAO,'MM/YYYY') ORDER BY MIN(a.DT_AVALIACAO)",
             "color": "#43A047"},
            {"name": "RBS-R",
             "sql": "SELECT TO_CHAR(a.DT_AVALIACAO,'MM/YYYY') AS LABEL, COUNT(*) AS VALUE FROM TEA_AVALIACOES a JOIN TEA_PROVAS p ON p.ID_PROVA=a.ID_PROVA WHERE p.DS_NOME LIKE '%RBS%'    GROUP BY TO_CHAR(a.DT_AVALIACAO,'MM/YYYY') ORDER BY MIN(a.DT_AVALIACAO)",
             "color": "#9C27B0"},
        ],
        chart_type="bar", height=320,
        y_axis_title="Avaliações", x_axis_title="Mês/Ano",
        sequence=10,
    ))
    ok("pareto: instrumentos por volume", apex_add_pareto_chart(
        page_id=20, region_name="Pareto — Volume por Instrumento",
        sql_query=(
            "SELECT p.DS_NOME AS LABEL, COUNT(a.ID_AVALIACAO) AS VALUE "
            "FROM TEA_PROVAS p LEFT JOIN TEA_AVALIACOES a ON a.ID_PROVA = p.ID_PROVA "
            "WHERE p.FL_ATIVO='S' GROUP BY p.DS_NOME ORDER BY 2 DESC"
        ),
        bar_name="Avaliações", line_name="Acumulado %", height=320, sequence=20,
    ))
    ok("gradient_donut: proporção instrumentos", apex_add_gradient_donut(
        page_id=20, region_name="Proporção de Uso por Instrumento",
        sql_query=(
            "SELECT p.DS_NOME AS LABEL, COUNT(a.ID_AVALIACAO) AS VALUE "
            "FROM TEA_PROVAS p JOIN TEA_AVALIACOES a ON a.ID_PROVA = p.ID_PROVA "
            "WHERE p.FL_ATIVO='S' GROUP BY p.DS_NOME ORDER BY 2 DESC"
        ),
        label_column="LABEL", value_column="VALUE",
        center_label_text="Instrumentos",
        series_name="Avaliações", height=300, sequence=30,
    ))
    ok("percent_bars: score médio por instrumento", apex_add_percent_bars(
        page_id=20, region_name="Score Médio por Instrumento (%)",
        sql_query=(
            "SELECT p.DS_NOME AS LABEL, ROUND(AVG(a.NR_PCT_TOTAL),1) AS VALUE "
            "FROM TEA_PROVAS p JOIN TEA_AVALIACOES a ON a.ID_PROVA = p.ID_PROVA "
            "WHERE p.FL_ATIVO='S' AND a.NR_PCT_TOTAL > 0 "
            "GROUP BY p.DS_NOME ORDER BY 2 DESC"
        ),
        color="orange", sequence=40,
    ))

    # ──────────────────────────────────────────
    section(6, "Score por Dimensão — página 30")
    if not ok("apex_add_page(30)", apex_add_page(30, "Score por Dimensão", "blank")): return

    if not ok("region: VW_TEA_SCORE_DIMENSAO IR",
        apex_add_region(30, "Scores por Dimensão Clínica", "report",
            source_sql="""SELECT BENEFICIARIO,
       DIMENSAO,
       NR_ORDEM,
       NR_SCORE,
       NR_SCORE_MAX,
       NR_PERCENTUAL  AS PCT,
       NR_COLETA,
       TO_CHAR(DT_AVALIACAO,'DD/MM/YYYY') AS DT_AVALIACAO
  FROM VW_TEA_SCORE_DIMENSAO
 ORDER BY BENEFICIARIO, NR_ORDEM, NR_COLETA DESC""")): return

    ok("spotlight: melhor dimensão", apex_add_spotlight_metric(
        page_id=30, region_name="Score Médio por Dimensão",
        sql_query="SELECT ROUND(AVG(NR_PERCENTUAL),1) FROM VW_TEA_SCORE_DIMENSAO WHERE NR_PERCENTUAL > 0",
        label="Score Médio Geral por Dimensão",
        color="teal", icon="fa-th", suffix="%", sequence=20,
    ))
    ok("leaderboard: dimensões por score", apex_add_leaderboard(
        page_id=30, region_name="Ranking de Dimensões por Score Médio",
        sql_query=(
            "SELECT DIMENSAO AS LABEL, ROUND(AVG(NR_PERCENTUAL),1) AS VALUE "
            "FROM VW_TEA_SCORE_DIMENSAO WHERE NR_PERCENTUAL > 0 "
            "GROUP BY DIMENSAO ORDER BY 2 DESC FETCH FIRST 10 ROWS ONLY"
        ),
        color="teal", max_rows=10, sequence=30,
    ))
    ok("percent_bars: percentual por dimensão", apex_add_percent_bars(
        page_id=30, region_name="Percentual Médio por Dimensão",
        sql_query=(
            "SELECT DIMENSAO AS LABEL, ROUND(AVG(NR_PERCENTUAL),1) AS VALUE "
            "FROM VW_TEA_SCORE_DIMENSAO WHERE NR_PERCENTUAL > 0 "
            "GROUP BY DIMENSAO ORDER BY 2 DESC"
        ),
        color="teal", sequence=40,
    ))
    ok("combo_chart: score vs score_max por dimensão", apex_add_combo_chart(
        page_id=30, region_name="Score Obtido vs Máximo por Dimensão",
        bar_sql=(
            "SELECT DIMENSAO AS L, ROUND(AVG(NR_SCORE),1) AS V "
            "FROM VW_TEA_SCORE_DIMENSAO GROUP BY DIMENSAO ORDER BY AVG(NR_SCORE) DESC"
        ),
        line_sql=(
            "SELECT DIMENSAO AS L, ROUND(AVG(NR_SCORE_MAX),1) AS V "
            "FROM VW_TEA_SCORE_DIMENSAO GROUP BY DIMENSAO ORDER BY AVG(NR_SCORE_MAX) DESC"
        ),
        bar_name="Score Obtido", line_name="Score Máximo",
        bar_label_col="L", bar_value_col="V",
        line_label_col="L", line_value_col="V",
        height=320, y_axis_title="Pontos", y2_axis_title="Máximo",
        sequence=50,
    ))

    # ──────────────────────────────────────────
    section(7, "Análise por Clínica — página 40")
    if not ok("apex_add_page(40)", apex_add_page(40, "Análise por Clínica", "blank")): return

    if not ok("region: VW_TEA_RESUMO_CLINICA IR",
        apex_add_region(40, "Resumo por Clínica", "report",
            source_sql="""SELECT CLINICA,
       QTD_BENEFICIARIOS,
       QTD_AVALIACOES,
       MEDIA_SCORE_PCT         AS SCORE_MEDIO_PCT,
       TO_CHAR(ULTIMA_AVALIACAO,'DD/MM/YYYY') AS ULTIMA_AVALIACAO
  FROM VW_TEA_RESUMO_CLINICA
 ORDER BY QTD_AVALIACOES DESC""")): return

    ok("leaderboard: clínicas por avaliações", apex_add_leaderboard(
        page_id=40, region_name="Ranking de Clínicas por Avaliações",
        sql_query="SELECT CLINICA AS LABEL, QTD_AVALIACOES AS VALUE FROM VW_TEA_RESUMO_CLINICA ORDER BY 2 DESC",
        color="indigo", max_rows=10, sequence=20,
    ))
    ok("comparison_panel: melhor clínica vs média", apex_add_comparison_panel(
        page_id=40, region_name="Top Clínica vs Média Geral",
        left_label="Melhor Clínica (Score)",
        left_metrics=[
            {"label": "Score Médio",   "sql": "SELECT ROUND(MAX(MEDIA_SCORE_PCT),1) FROM VW_TEA_RESUMO_CLINICA"},
            {"label": "Avaliações",    "sql": "SELECT QTD_AVALIACOES FROM VW_TEA_RESUMO_CLINICA WHERE MEDIA_SCORE_PCT = (SELECT MAX(MEDIA_SCORE_PCT) FROM VW_TEA_RESUMO_CLINICA) AND ROWNUM=1"},
            {"label": "Beneficiários", "sql": "SELECT QTD_BENEFICIARIOS FROM VW_TEA_RESUMO_CLINICA WHERE MEDIA_SCORE_PCT = (SELECT MAX(MEDIA_SCORE_PCT) FROM VW_TEA_RESUMO_CLINICA) AND ROWNUM=1"},
            {"label": "Terapeutas",    "sql": "SELECT COUNT(*) FROM TEA_TERAPEUTAS t JOIN TEA_CLINICAS c ON c.ID_CLINICA=t.ID_CLINICA WHERE c.DS_NOME=(SELECT CLINICA FROM VW_TEA_RESUMO_CLINICA WHERE MEDIA_SCORE_PCT=(SELECT MAX(MEDIA_SCORE_PCT) FROM VW_TEA_RESUMO_CLINICA) AND ROWNUM=1) AND t.FL_ATIVO='S'"},
        ],
        right_label="Média Geral",
        right_metrics=[
            {"label": "Score Médio",   "sql": "SELECT ROUND(AVG(MEDIA_SCORE_PCT),1) FROM VW_TEA_RESUMO_CLINICA WHERE MEDIA_SCORE_PCT IS NOT NULL"},
            {"label": "Avaliações",    "sql": "SELECT ROUND(AVG(QTD_AVALIACOES),0) FROM VW_TEA_RESUMO_CLINICA"},
            {"label": "Beneficiários", "sql": "SELECT ROUND(AVG(QTD_BENEFICIARIOS),0) FROM VW_TEA_RESUMO_CLINICA"},
            {"label": "Terapeutas",    "sql": "SELECT ROUND(COUNT(*)/NULLIF((SELECT COUNT(*) FROM TEA_CLINICAS WHERE FL_ATIVO='S'),0),1) FROM TEA_TERAPEUTAS WHERE FL_ATIVO='S'"},
        ],
        left_color="green", right_color="blue", sequence=30,
    ))
    ok("stacked_chart: avaliações por clínica e status", apex_add_stacked_chart(
        page_id=40, region_name="Avaliações por Clínica e Status",
        series_list=[
            {"name": "Concluída",
             "sql": "SELECT c.DS_NOME AS LABEL, COUNT(*) AS VALUE FROM TEA_AVALIACOES a JOIN TEA_BENEFICIARIOS b ON b.ID_BENEFICIARIO=a.ID_BENEFICIARIO JOIN TEA_CLINICAS c ON c.ID_CLINICA=b.ID_CLINICA WHERE a.DS_STATUS='CONCLUIDA' GROUP BY c.DS_NOME ORDER BY 2 DESC",
             "color": "#43A047"},
            {"name": "Em Andamento",
             "sql": "SELECT c.DS_NOME AS LABEL, COUNT(*) AS VALUE FROM TEA_AVALIACOES a JOIN TEA_BENEFICIARIOS b ON b.ID_BENEFICIARIO=a.ID_BENEFICIARIO JOIN TEA_CLINICAS c ON c.ID_CLINICA=b.ID_CLINICA WHERE a.DS_STATUS='EM_ANDAMENTO' GROUP BY c.DS_NOME ORDER BY 2 DESC",
             "color": "#FF9800"},
            {"name": "Rascunho",
             "sql": "SELECT c.DS_NOME AS LABEL, COUNT(*) AS VALUE FROM TEA_AVALIACOES a JOIN TEA_BENEFICIARIOS b ON b.ID_BENEFICIARIO=a.ID_BENEFICIARIO JOIN TEA_CLINICAS c ON c.ID_CLINICA=b.ID_CLINICA WHERE a.DS_STATUS='RASCUNHO' GROUP BY c.DS_NOME ORDER BY 2 DESC",
             "color": "#1E88E5"},
        ],
        chart_type="bar", height=320,
        y_axis_title="Avaliações", x_axis_title="Clínica",
        sequence=40,
    ))
    ok("heatmap_grid: clínica x instrumento", apex_add_heatmap_grid(
        page_id=40, region_name="Score Médio por Clínica e Instrumento",
        sql_query=(
            "SELECT c.DS_NOME AS ROW_LABEL, p.DS_NOME AS COL_LABEL, "
            "ROUND(AVG(a.NR_PCT_TOTAL),0) AS VALUE "
            "FROM TEA_AVALIACOES a "
            "JOIN TEA_BENEFICIARIOS b ON b.ID_BENEFICIARIO = a.ID_BENEFICIARIO "
            "JOIN TEA_CLINICAS c      ON c.ID_CLINICA = b.ID_CLINICA "
            "JOIN TEA_PROVAS p        ON p.ID_PROVA = a.ID_PROVA "
            "WHERE a.NR_PCT_TOTAL > 0 AND a.DS_STATUS='CONCLUIDA' "
            "GROUP BY c.DS_NOME, p.DS_NOME "
            "ORDER BY c.DS_NOME, p.DS_NOME"
        ),
        row_column="ROW_LABEL", col_column="COL_LABEL", value_column="VALUE",
        color="indigo", sequence=50,
    ))

    # ──────────────────────────────────────────
    section(8, "Histórico Completo — página 50")
    if not ok("apex_add_page(50)", apex_add_page(50, "Histórico Completo", "blank")): return

    if not ok("region: Histórico IR",
        apex_add_region(50, "Histórico de Avaliações", "report",
            source_sql="""SELECT a.ID_AVALIACAO,
       b.DS_NOME        AS PACIENTE,
       b.NR_BENEFICIO,
       c.DS_NOME        AS CLINICA,
       p.DS_NOME        AS INSTRUMENTO,
       t.DS_NOME        AS TERAPEUTA,
       a.NR_COLETA,
       TO_CHAR(a.DT_AVALIACAO,'DD/MM/YYYY') AS DATA_AVALIACAO,
       a.DS_STATUS,
       a.NR_PCT_TOTAL   AS SCORE_PCT
  FROM TEA_AVALIACOES a
  JOIN TEA_BENEFICIARIOS b ON b.ID_BENEFICIARIO = a.ID_BENEFICIARIO
  JOIN TEA_CLINICAS c      ON c.ID_CLINICA = b.ID_CLINICA
  JOIN TEA_PROVAS p        ON p.ID_PROVA   = a.ID_PROVA
  JOIN TEA_TERAPEUTAS t    ON t.ID_TERAPEUTA = a.ID_TERAPEUTA
 ORDER BY a.DT_AVALIACAO DESC""")): return

    ok("animated_counter: total histórico", apex_add_animated_counter(
        page_id=50, region_name="Total de Registros no Histórico",
        sql_query="SELECT COUNT(*) FROM TEA_AVALIACOES",
        label="Total de Avaliações no Sistema",
        color="indigo", icon="fa-history", sequence=20,
    ))
    ok("stat_delta: resumo geral", apex_add_stat_delta(
        page_id=50, region_name="Resumo Geral do Sistema", sequence=30, columns=4,
        metrics=[
            {"label": "Total Avaliações",      "icon": "fa-clipboard",    "color": "indigo",
             "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES",
             "prev_sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DT_AVALIACAO < TRUNC(SYSDATE,'MM')"},
            {"label": "Pacientes Avaliados",   "icon": "fa-users",        "color": "purple",
             "sql": "SELECT COUNT(DISTINCT ID_BENEFICIARIO) FROM TEA_AVALIACOES",
             "prev_sql": "SELECT COUNT(DISTINCT ID_BENEFICIARIO) FROM TEA_AVALIACOES WHERE DT_AVALIACAO < TRUNC(SYSDATE,'MM')"},
            {"label": "Score Médio (%)",        "icon": "fa-bar-chart",    "color": "blue", "suffix": "%",
             "sql": "SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0",
             "prev_sql": "SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0 AND DT_AVALIACAO < TRUNC(SYSDATE,'MM')"},
            {"label": "Terapeutas Ativos",     "icon": "fa-user-md",      "color": "teal",
             "sql": "SELECT COUNT(DISTINCT ID_TERAPEUTA) FROM TEA_AVALIACOES WHERE DT_AVALIACAO >= ADD_MONTHS(SYSDATE,-3)",
             "prev_sql": "SELECT COUNT(DISTINCT ID_TERAPEUTA) FROM TEA_AVALIACOES WHERE DT_AVALIACAO >= ADD_MONTHS(SYSDATE,-6) AND DT_AVALIACAO < ADD_MONTHS(SYSDATE,-3)"},
        ],
    ))
    ok("activity_stream: timeline avaliações", apex_add_activity_stream(
        page_id=50, region_name="Timeline de Avaliações",
        sql_query=(
            "SELECT b.DS_NOME||' — '||p.DS_NOME||' — '||c.DS_NOME||' ('||a.DS_STATUS||')' AS TEXT, "
            "a.DT_AVALIACAO AS DT "
            "FROM TEA_AVALIACOES a "
            "JOIN TEA_BENEFICIARIOS b ON b.ID_BENEFICIARIO = a.ID_BENEFICIARIO "
            "JOIN TEA_PROVAS p ON p.ID_PROVA = a.ID_PROVA "
            "JOIN TEA_CLINICAS c ON c.ID_CLINICA = b.ID_CLINICA "
            "ORDER BY a.DT_AVALIACAO DESC FETCH FIRST 25 ROWS ONLY"
        ),
        text_column="TEXT", date_column="DT",
        default_icon="fa-stethoscope", default_color="indigo",
        max_rows=25, sequence=40,
    ))
    ok("traffic_light: integridade clínica", apex_add_traffic_light(
        page_id=50, region_name="Integridade dos Dados Clínicos",
        sql_query=(
            "SELECT 'Avaliações Concluídas' AS LABEL, "
            "CASE WHEN COUNT(*) >= 50 THEN 'GREEN' WHEN COUNT(*) >= 20 THEN 'YELLOW' ELSE 'RED' END AS STATUS "
            "FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA' "
            "UNION ALL "
            "SELECT 'Pacientes com Avaliação', "
            "CASE WHEN COUNT(DISTINCT a.ID_BENEFICIARIO)*100/NULLIF(COUNT(DISTINCT b.ID_BENEFICIARIO),0) >= 70 THEN 'GREEN' "
            "     WHEN COUNT(DISTINCT a.ID_BENEFICIARIO)*100/NULLIF(COUNT(DISTINCT b.ID_BENEFICIARIO),0) >= 40 THEN 'YELLOW' ELSE 'RED' END "
            "FROM TEA_BENEFICIARIOS b LEFT JOIN TEA_AVALIACOES a ON a.ID_BENEFICIARIO=b.ID_BENEFICIARIO WHERE b.FL_ATIVO='S' "
            "UNION ALL "
            "SELECT 'Scores Calculados', "
            "CASE WHEN COUNT(*) >= 50 THEN 'GREEN' WHEN COUNT(*) >= 20 THEN 'YELLOW' ELSE 'RED' END "
            "FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL > 0 "
            "UNION ALL "
            "SELECT 'Scores por Dimensão', "
            "CASE WHEN COUNT(*) >= 100 THEN 'GREEN' WHEN COUNT(*) >= 30 THEN 'YELLOW' ELSE 'RED' END "
            "FROM TEA_AVALIACAO_DIMENSOES"
        ),
        label_column="LABEL", status_column="STATUS", sequence=50,
    ))

    # ──────────────────────────────────────────
    section(9, "Navegação")
    if not ok("nav: Painel",       apex_add_nav_item("Painel Clínico",       1,  10, "fa-home")): return
    if not ok("nav: Evolução",     apex_add_nav_item("Evolução Pacientes",   10, 20, "fa-line-chart")): return
    if not ok("nav: Instrumentos", apex_add_nav_item("Por Instrumento",      20, 30, "fa-list-alt")): return
    if not ok("nav: Dimensões",    apex_add_nav_item("Score por Dimensão",   30, 40, "fa-th")): return
    if not ok("nav: Clínicas",     apex_add_nav_item("Análise por Clínica",  40, 50, "fa-hospital-o")): return
    if not ok("nav: Histórico",    apex_add_nav_item("Histórico Completo",   50, 60, "fa-history")): return

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
        ("  1", "Painel de Relatórios  (hero + metric_cards + stat_delta + animated_counter + ribbon_stats)"),
        (" 10", "Evolução p/ Paciente  (IR VW_EVOLUCAO + spotlight + area_chart + comparison_panel + heatmap)"),
        (" 20", "Comparativo Instrumento (kpi_row + stacked_chart + pareto + gradient_donut + percent_bars)"),
        (" 30", "Score por Dimensão    (IR VW_SCORE_DIM + spotlight + leaderboard + percent_bars + combo_chart)"),
        (" 40", "Análise por Clínica   (IR VW_RESUMO + leaderboard + comparison_panel + stacked + heatmap)"),
        (" 50", "Histórico Completo    (IR completo + animated_counter + stat_delta + activity_stream + traffic_light)"),
    ]

    print(f"""
{'═'*60}
  App 209 — Relatórios Clínicos TEA
  Construído em {elapsed:.1f}s
  Páginas : {summary.get('pages')}
  Regiões : {summary.get('regions')}
  Itens   : {summary.get('items')}

  Páginas ({len(pages_detail)}):""")
    for pid, desc in pages_detail:
        print(f"    {pid}  {desc}")
    print(f"""
  URL: f?p=209
  Login: cnu.admin / Unimed@2024
{'═'*60}""")


if __name__ == "__main__":
    run()
