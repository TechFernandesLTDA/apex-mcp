"""Build App 201 — Registro de Pacientes."""
import os, json, sys

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
