"""Build App 201 — Registro de Pacientes."""
import os, json, sys

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

from apex_mcp.tools.sql_tools import apex_connect
from apex_mcp.tools.app_tools import apex_create_app, apex_finalize_app
from apex_mcp.tools.page_tools import apex_add_page
from apex_mcp.tools.generator_tools import apex_generate_login, apex_generate_dashboard, apex_generate_crud
from apex_mcp.tools.component_tools import apex_add_region
from apex_mcp.tools.validation_tools import apex_add_item_validation, apex_add_item_computation
from apex_mcp.tools.shared_tools import apex_add_nav_item
from apex_mcp.tools.ui_tools    import apex_add_stat_delta, apex_add_ribbon_stats, apex_add_leaderboard, apex_add_percent_bars
from apex_mcp.tools.chart_tools import apex_add_animated_counter, apex_add_pareto_chart

def ok(label, result_str):
    r = json.loads(result_str)
    if r.get("status") == "error":
        print(f"  ❌ {label}: {r['error']}")
        return False
    print(f"  ✓  {label}")
    return True

def run():
    print("\n══════════════════════════════════════")
    print("  APP 201 — Registro de Pacientes")
    print("══════════════════════════════════════")

    print("\n[1] Conectando...")
    if not ok("apex_connect", apex_connect()): return

    print("\n[2] Criando aplicação 201...")
    if not ok("apex_create_app", apex_create_app(
        app_id=201, app_name="Registro de Pacientes TEA",
        app_alias="pacientes-tea", login_page=101, home_page=1,
        language="pt-br", date_format="DD/MM/YYYY"
    )): return

    print("\n[3] Login page 101...")
    if not ok("apex_generate_login", apex_generate_login(101)): return

    print("\n[4] Dashboard (page 1)...")
    if not ok("apex_add_page(1)", apex_add_page(1, "Dashboard Pacientes", "blank")): return
    if not ok("apex_generate_dashboard", apex_generate_dashboard(
        page_id=1,
        kpi_queries=[
            {"label": "Pacientes Ativos",      "sql": "SELECT COUNT(*) FROM TEA_BENEFICIARIOS WHERE FL_ATIVO='S'",                    "icon": "fa-users",      "color": "blue"},
            {"label": "Avaliações Concluídas", "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA'",              "icon": "fa-check-circle","color": "green"},
            {"label": "Em Andamento",          "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='EM_ANDAMENTO'",           "icon": "fa-spinner",    "color": "orange"},
            {"label": "Média Score (%)",       "sql": "SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL > 0", "icon": "fa-bar-chart",  "color": "red"},
        ]
    )): return

    ok("stat_delta: variação mensal", apex_add_stat_delta(
        page_id=1, region_name="Variacao Mensal", sequence=20, columns=4,
        metrics=[
            {"label": "Pacientes Ativos",      "icon": "fa-users",        "color": "blue",
             "sql": "SELECT COUNT(*) FROM TEA_BENEFICIARIOS WHERE FL_ATIVO='S'",
             "prev_sql": "SELECT COUNT(*) FROM TEA_BENEFICIARIOS WHERE FL_ATIVO='S' AND DT_CRIACAO < TRUNC(SYSDATE,'MM')"},
            {"label": "Avaliações Concluídas", "icon": "fa-check-circle", "color": "green",
             "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA'",
             "prev_sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA' AND DT_AVALIACAO < TRUNC(SYSDATE,'MM')"},
            {"label": "Score Médio (%)",       "icon": "fa-bar-chart",    "color": "purple", "suffix": "%",
             "sql": "SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0",
             "prev_sql": "SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0 AND DT_AVALIACAO < TRUNC(SYSDATE,'MM')"},
            {"label": "Em Andamento",          "icon": "fa-spinner",      "color": "orange",
             "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='EM_ANDAMENTO'",
             "prev_sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='EM_ANDAMENTO' AND DT_AVALIACAO < TRUNC(SYSDATE,'MM')"},
        ],
    ))
    ok("ribbon_stats: resumo", apex_add_ribbon_stats(
        page_id=1, region_name="Resumo do Sistema", sequence=30,
        metrics=[
            {"label": "Clínicas",    "sql": "SELECT COUNT(*) FROM TEA_CLINICAS WHERE FL_ATIVO='S'",     "icon": "fa-hospital-o",  "color": "teal"},
            {"label": "Terapeutas",  "sql": "SELECT COUNT(*) FROM TEA_TERAPEUTAS WHERE FL_ATIVO='S'",   "icon": "fa-user-md",     "color": "indigo"},
            {"label": "Instrumentos","sql": "SELECT COUNT(*) FROM TEA_PROVAS WHERE FL_ATIVO='S'",       "icon": "fa-list-alt",    "color": "orange"},
            {"label": "Usuários",    "sql": "SELECT COUNT(*) FROM TEA_USUARIOS WHERE FL_ATIVO='S'",     "icon": "fa-user-circle", "color": "blue"},
        ],
    ))

    print("\n[5] CRUD Beneficiários (pages 10-11)...")
    if not ok("apex_generate_crud(TEA_BENEFICIARIOS)", apex_generate_crud("TEA_BENEFICIARIOS", 10, 11)): return

    print("\n[6] Validações no form de beneficiários (page 11)...")
    if not ok("validation: NR_BENEFICIO not_null",
        apex_add_item_validation(11, "NR_BENEFICIO", "Número de Benefício Obrigatório",
            validation_type="not_null")): return

    if not ok("validation: DS_NOME not_null",
        apex_add_item_validation(11, "DS_NOME", "Nome Obrigatório",
            validation_type="not_null")): return

    if not ok("validation: NR_BENEFICIO regex",
        apex_add_item_validation(11, "NR_BENEFICIO", "Formato Inválido (ex: 000.000.000-0)",
            validation_type="regex",
            validation_expression=r"^[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]$",
            error_message="Formato inválido. Use: 000.000.000-0",
            sequence=20)): return

    print("\n[7] Computação: DT_CRIACAO auto-fill (page 11)...")
    if not ok("computation: DT_CRIACAO",
        apex_add_item_computation(11, "DT_CRIACAO",
            computation_type="plsql_expression",
            computation_expression="SYSDATE",
            computation_point="BEFORE_HEADER")): return

    print("\n[8] Página de Avaliações (page 20)...")
    if not ok("apex_add_page(20)", apex_add_page(20, "Avaliações", "blank")): return
    if not ok("region: Avaliações IR",
        apex_add_region(20, "Avaliações por Beneficiário", "report",
            source_sql="""SELECT a.ID_AVALIACAO,
       b.DS_NOME        AS PACIENTE,
       p.DS_NOME        AS PROVA,
       t.DS_NOME        AS TERAPEUTA,
       TO_CHAR(a.DT_AVALIACAO,'DD/MM/YYYY') AS DATA_AVALIACAO,
       a.DS_STATUS,
       a.NR_PCT_TOTAL   AS PCT
  FROM TEA_AVALIACOES a
  JOIN TEA_BENEFICIARIOS b ON b.ID_BENEFICIARIO = a.ID_BENEFICIARIO
  JOIN TEA_PROVAS p        ON p.ID_PROVA        = a.ID_PROVA
  JOIN TEA_TERAPEUTAS t    ON t.ID_TERAPEUTA    = a.ID_TERAPEUTA
 ORDER BY a.DT_AVALIACAO DESC""")): return

    ok("animated_counter: avaliações p20", apex_add_animated_counter(
        page_id=20, region_name="Total Avaliacoes",
        sql_query="SELECT COUNT(*) FROM TEA_AVALIACOES",
        label="Total de Avaliações no Sistema",
        color="unimed", icon="fa-clipboard", sequence=20,
    ))
    ok("leaderboard: top pacientes p20", apex_add_leaderboard(
        page_id=20, region_name="Top Pacientes por Avaliacoes",
        sql_query=(
            "SELECT b.DS_NOME AS LABEL, COUNT(a.ID_AVALIACAO) AS VALUE "
            "FROM TEA_BENEFICIARIOS b "
            "LEFT JOIN TEA_AVALIACOES a ON a.ID_BENEFICIARIO = b.ID_BENEFICIARIO "
            "GROUP BY b.DS_NOME ORDER BY 2 DESC FETCH FIRST 8 ROWS ONLY"
        ),
        color="unimed", max_rows=8, sequence=30,
    ))
    ok("percent_bars: status p20", apex_add_percent_bars(
        page_id=20, region_name="Distribuicao por Status",
        sql_query="SELECT DS_STATUS AS LABEL, COUNT(*) AS VALUE FROM TEA_AVALIACOES GROUP BY DS_STATUS ORDER BY 2 DESC",
        color="blue", sequence=40,
    ))
    ok("pareto: instrumentos p20", apex_add_pareto_chart(
        page_id=20, region_name="Pareto — Avaliacoes por Instrumento",
        sql_query=(
            "SELECT p.DS_NOME AS LABEL, COUNT(a.ID_AVALIACAO) AS VALUE "
            "FROM TEA_PROVAS p LEFT JOIN TEA_AVALIACOES a ON a.ID_PROVA = p.ID_PROVA "
            "WHERE p.FL_ATIVO='S' GROUP BY p.DS_NOME ORDER BY 2 DESC"
        ),
        bar_name="Avaliações", line_name="Acumulado %", height=360, sequence=50,
    ))

    print("\n[9] Navegação...")
    if not ok("nav: Dashboard", apex_add_nav_item("Dashboard", 1,  10, "fa-home")): return
    if not ok("nav: Pacientes", apex_add_nav_item("Pacientes", 10, 20, "fa-users")): return
    if not ok("nav: Avaliações",apex_add_nav_item("Avaliações",20, 30, "fa-clipboard")): return

    print("\n[10] Finalizando...")
    r = apex_finalize_app()
    rj = json.loads(r)
    if rj.get("status") == "error":
        print(f"  ❌ apex_finalize_app: {rj['error']}")
        return
    print(f"  ✓  apex_finalize_app → URL: {rj.get('apex_url')}")
    summary = rj.get("summary", {})
    print(f"\n  App 201 criado com sucesso!")
    print(f"  Páginas: {summary.get('pages')}  Regiões: {summary.get('regions')}  Itens: {summary.get('items')}")

if __name__ == "__main__":
    run()
