"""Build App 200 — Painel de Clínicas e Terapeutas."""
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
    print("  APP 200 — Painel de Clínicas TEA")
    print("══════════════════════════════════════")

    print("\n[1] Conectando...")
    if not ok("apex_connect", apex_connect()): return

    print("\n[2] Criando aplicação 200...")
    if not ok("apex_create_app", apex_create_app(
        app_id=200, app_name="Painel Clínicas TEA",
        app_alias="clinicas-tea", login_page=101, home_page=1,
        language="pt-br", date_format="DD/MM/YYYY"
    )): return

    print("\n[3] Login page 101...")
    if not ok("apex_generate_login", apex_generate_login(101)): return

    print("\n[4] Dashboard (page 1)...")
    if not ok("apex_add_page(1)", apex_add_page(1, "Dashboard", "blank")): return
    if not ok("apex_generate_dashboard", apex_generate_dashboard(
        page_id=1,
        kpi_queries=[
            {"label": "Clínicas",       "sql": "SELECT COUNT(*) FROM TEA_CLINICAS WHERE FL_ATIVO='S'",      "icon": "fa-hospital-o",  "color": "blue"},
            {"label": "Terapeutas",     "sql": "SELECT COUNT(*) FROM TEA_TERAPEUTAS WHERE FL_ATIVO='S'",    "icon": "fa-user-md",     "color": "green"},
            {"label": "Beneficiários",  "sql": "SELECT COUNT(*) FROM TEA_BENEFICIARIOS WHERE FL_ATIVO='S'", "icon": "fa-users",       "color": "orange"},
            {"label": "Avaliações",     "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES",                       "icon": "fa-clipboard",   "color": "red"},
        ]
    )): return

    print("\n[5] CRUD Clínicas (pages 10-11)...")
    r = apex_generate_crud("TEA_CLINICAS", 10, 11)
    if not ok("apex_generate_crud(TEA_CLINICAS)", r): return

    print("\n[6] CRUD Terapeutas (pages 20-21)...")
    r = apex_generate_crud("TEA_TERAPEUTAS", 20, 21)
    if not ok("apex_generate_crud(TEA_TERAPEUTAS)", r): return

    print("\n[7] Navegação...")
    if not ok("nav: Dashboard",   apex_add_nav_item("Dashboard",  1,  10, "fa-home")): return
    if not ok("nav: Clínicas",    apex_add_nav_item("Clínicas",   10, 20, "fa-hospital-o")): return
    if not ok("nav: Terapeutas",  apex_add_nav_item("Terapeutas", 20, 30, "fa-user-md")): return

    print("\n[8] Finalizando...")
    r = apex_finalize_app()
    rj = json.loads(r)
    if rj.get("status") == "error":
        print(f"  ❌ apex_finalize_app: {rj['error']}")
        return
    print(f"  ✓  apex_finalize_app → URL: {rj.get('apex_url')}")
    summary = rj.get("summary", {})
    print(f"\n  App 200 criado com sucesso!")
    print(f"  Páginas: {summary.get('pages')}  Regiões: {summary.get('regions')}  Itens: {summary.get('items')}")

if __name__ == "__main__":
    run()
