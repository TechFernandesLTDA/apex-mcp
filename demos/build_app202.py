"""Build App 202 — Administração e Auditoria."""
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
from apex_mcp.tools.component_tools import apex_add_region, apex_add_dynamic_action
from apex_mcp.tools.shared_tools import apex_add_auth_scheme, apex_add_nav_item
from apex_mcp.tools.js_tools import apex_generate_ajax_handler

def ok(label, result_str):
    r = json.loads(result_str)
    if r.get("status") == "error":
        print(f"  ❌ {label}: {r['error']}")
        return False
    print(f"  ✓  {label}")
    return True

def run():
    print("\n══════════════════════════════════════")
    print("  APP 202 — Administração e Auditoria")
    print("══════════════════════════════════════")

    print("\n[1] Conectando...")
    if not ok("apex_connect", apex_connect()): return

    print("\n[2] Criando aplicação 202...")
    if not ok("apex_create_app", apex_create_app(
        app_id=202, app_name="Administração TEA",
        app_alias="admin-tea", login_page=101, home_page=1,
        language="pt-br", date_format="DD/MM/YYYY"
    )): return

    print("\n[3] Authorization scheme IS_ADMIN...")
    if not ok("apex_add_auth_scheme(IS_ADMIN)",
        apex_add_auth_scheme(
            scheme_name="IS_ADMIN",
            function_body=(
                "RETURN PKG_TEA_AVALIACAO.tem_perfil('ADM');"
            )
        )): return

    print("\n[4] Login page 101...")
    if not ok("apex_generate_login", apex_generate_login(101)): return

    print("\n[5] Dashboard ADM (page 1)...")
    if not ok("apex_add_page(1)", apex_add_page(1, "Dashboard ADM", "blank")): return
    if not ok("apex_generate_dashboard", apex_generate_dashboard(
        page_id=1,
        kpi_queries=[
            {"label": "Usuários Ativos",   "sql": "SELECT COUNT(*) FROM TEA_USUARIOS WHERE FL_ATIVO='S'",                          "icon": "fa-user",        "color": "blue"},
            {"label": "Eventos Auditoria", "sql": "SELECT COUNT(*) FROM TEA_LOG_AUDITORIA",                                        "icon": "fa-file-text-o", "color": "orange"},
            {"label": "Clínicas Ativas",   "sql": "SELECT COUNT(*) FROM TEA_CLINICAS WHERE FL_ATIVO='S'",                          "icon": "fa-hospital-o",  "color": "green"},
            {"label": "Config. Params",    "sql": "SELECT COUNT(*) FROM TEA_CONFIG",                                               "icon": "fa-cog",         "color": "red"},
        ]
    )): return

    print("\n[6] CRUD Usuários (pages 10-11)...")
    if not ok("apex_generate_crud(TEA_USUARIOS)", apex_generate_crud("TEA_USUARIOS", 10, 11)): return

    print("\n[7] Página Log de Auditoria (page 20)...")
    if not ok("apex_add_page(20)", apex_add_page(20, "Log de Auditoria", "blank")): return

    if not ok("region: Filtro tabela",
        apex_add_region(20, "Filtrar por Tabela", "static",
            source_sql="")): return

    if not ok("region: Log IR",
        apex_add_region(20, "Eventos de Auditoria", "report",
            source_sql="""SELECT DS_TABELA,
       DS_OPERACAO,
       ID_REGISTRO,
       DS_USUARIO,
       DS_DETALHES,
       TO_CHAR(DT_OPERACAO,'DD/MM/YYYY HH24:MI:SS') AS DT_OPERACAO
  FROM TEA_LOG_AUDITORIA
 ORDER BY DT_OPERACAO DESC""")): return

    print("\n[8] AJAX handler para filtrar log (page 20)...")
    r = apex_generate_ajax_handler(
        page_id=20,
        callback_name="FILTRAR_LOG",
        plsql_code="""DECLARE
  l_tabela VARCHAR2(100) := :P20_TABELA;
BEGIN
  apex_json.open_object;
  apex_json.write('status', 'ok');
  apex_json.open_array('rows');
  FOR r IN (
    SELECT DS_TABELA, DS_OPERACAO, DS_USUARIO,
           TO_CHAR(DT_OPERACAO,'DD/MM/YYYY HH24:MI:SS') AS DT
      FROM TEA_LOG_AUDITORIA
     WHERE (l_tabela IS NULL OR DS_TABELA = l_tabela)
     ORDER BY DT_OPERACAO DESC
     FETCH FIRST 50 ROWS ONLY
  ) LOOP
    apex_json.open_object;
    apex_json.write('tabela',     r.DS_TABELA);
    apex_json.write('operacao',   r.DS_OPERACAO);
    apex_json.write('usuario',    r.DS_USUARIO);
    apex_json.write('data',       r.DT);
    apex_json.close_object;
  END LOOP;
  apex_json.close_array;
  apex_json.close_object;
END;""",
        input_items=["P20_TABELA"],
        return_json=True,
        auto_add_js=True
    )
    rj = json.loads(r)
    if rj.get("status") == "error":
        print(f"  ❌ apex_generate_ajax_handler: {rj['error']}")
        return
    print(f"  ✓  apex_generate_ajax_handler (process_id={rj.get('process_id')})")

    print("\n[9] Dynamic action: filtrar ao mudar P20_TABELA...")
    if not ok("apex_add_dynamic_action",
        apex_add_dynamic_action(
            page_id=20,
            da_name="Filtrar Log ao Mudar Tabela",
            event="change",
            trigger_element="P20_TABELA",
            action_type="execute_javascript",
            javascript_code="callFiltrarLog();"
        )): return

    print("\n[10] Página Configurações (page 30)...")
    if not ok("apex_add_page(30)", apex_add_page(30, "Configurações", "blank")): return
    if not ok("region: Config KV",
        apex_add_region(30, "Parâmetros do Sistema", "report",
            source_sql="""SELECT DS_CHAVE AS PARAMETRO,
       DS_VALOR AS VALOR,
       TO_CHAR(DT_CRIACAO,'DD/MM/YYYY HH24:MI') AS DT_CRIACAO
  FROM TEA_CONFIG
 ORDER BY DS_CHAVE""")): return

    print("\n[11] Navegação...")
    if not ok("nav: Dashboard",     apex_add_nav_item("Dashboard",    1,  10, "fa-home")): return
    if not ok("nav: Usuários",      apex_add_nav_item("Usuários",     10, 20, "fa-users")): return
    if not ok("nav: Auditoria",     apex_add_nav_item("Auditoria",    20, 30, "fa-file-text-o")): return
    if not ok("nav: Configurações", apex_add_nav_item("Configurações",30, 40, "fa-cog")): return

    print("\n[12] Finalizando...")
    r = apex_finalize_app()
    rj = json.loads(r)
    if rj.get("status") == "error":
        print(f"  ❌ apex_finalize_app: {rj['error']}")
        return
    print(f"  ✓  apex_finalize_app → URL: {rj.get('apex_url')}")
    summary = rj.get("summary", {})
    print(f"\n  App 202 criado com sucesso!")
    print(f"  Páginas: {summary.get('pages')}  Regiões: {summary.get('regions')}  Itens: {summary.get('items')}")

if __name__ == "__main__":
    run()
