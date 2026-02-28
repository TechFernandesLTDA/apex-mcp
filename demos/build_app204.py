"""Build App 204 — TEA Backoffice (apex_generate_from_schema demo).

Demonstra o gerador de mais alto nível do MCP: uma chamada cria
dashboard + CRUDs + navegação para todas as tabelas do projeto TEA.

Tabelas incluídas (8 das 18 tabelas TEA — as que têm conteúdo e
fazem sentido como CRUD para um backoffice):

  Operacional   → TEA_BENEFICIARIOS, TEA_AVALIACOES, TEA_CLINICAS, TEA_TERAPEUTAS
  Instrumentos  → TEA_PROVAS, TEA_DIMENSOES
  Administração → TEA_USUARIOS, TEA_PERFIS

Tabelas excluídas intencionalmente:
  TEA_QUESTOES / TEA_OPCOES_RESPOSTA  — sem conteúdo (licenciado)
  TEA_AVALIACAO_ITENS / _DIMENSOES    — detalhes gerenciados pelos forms
  TEA_EMBEDDINGS / TEA_CONHECIMENTO   — dados vetoriais / RAG
  TEA_LOG_AUDITORIA                   — somente leitura
  TEA_CONFIG                          — gerenciado via página de configuração dedicada
"""
import os, json, sys, time

# ── Credenciais do ambiente TEA ──────────────────────────────────────────────
os.environ.update({
    "ORACLE_DB_USER":        "TEA_APP",
    "ORACLE_DB_PASS":        "TeaApp@2024#Unimed",
    "ORACLE_DSN":            "u5cvlivnjuodscai_tp",
    "ORACLE_WALLET_DIR":     r"C:\Projetos\Apex\wallet",
    "ORACLE_WALLET_PASSWORD": "apex1234",
    "APEX_WORKSPACE_ID":     "8822816515098715",
    "APEX_SCHEMA":           "TEA_APP",
    "APEX_WORKSPACE_NAME":   "TEA",
})

sys.path.insert(0, r"C:\Projetos\Apex\mcp-server")

from apex_mcp.tools.sql_tools      import apex_connect
from apex_mcp.tools.app_tools      import apex_create_app, apex_finalize_app
from apex_mcp.tools.generator_tools import apex_generate_login
from apex_mcp.tools.advanced_tools  import apex_generate_from_schema, apex_validate_app
from apex_mcp.tools.shared_tools    import apex_add_auth_scheme


# ── Helpers ───────────────────────────────────────────────────────────────────
def ok(label: str, result_str: str) -> tuple[bool, dict]:
    r = json.loads(result_str)
    if r.get("status") == "error":
        print(f"  ✗  {label}: {r['error']}")
        return False, r
    print(f"  ✓  {label}")
    return True, r


def section(title: str):
    print(f"\n{'─' * 54}")
    print(f"  {title}")
    print(f"{'─' * 54}")


# ── Tabelas e ícones TEA ──────────────────────────────────────────────────────
TABLES = [
    "TEA_BENEFICIARIOS",    # pacientes
    "TEA_AVALIACOES",       # cabeçalho das avaliações
    "TEA_CLINICAS",         # clínicas credenciadas
    "TEA_TERAPEUTAS",       # profissionais
    "TEA_PROVAS",           # instrumentos VINELAND, CBCL, CFQL2, RBS-R
    "TEA_DIMENSOES",        # dimensões de cada instrumento
    "TEA_USUARIOS",         # usuários do sistema
    "TEA_PERFIS",           # perfis ADM / CLINICA / TERAPEUTA
]

ICONS = {
    "TEA_BENEFICIARIOS": "fa-users",
    "TEA_AVALIACOES":    "fa-clipboard-check",
    "TEA_CLINICAS":      "fa-hospital-o",
    "TEA_TERAPEUTAS":    "fa-user-md",
    "TEA_PROVAS":        "fa-file-text-o",
    "TEA_DIMENSOES":     "fa-sliders",
    "TEA_USUARIOS":      "fa-lock",
    "TEA_PERFIS":        "fa-id-badge",
}

# Mapeamento de cores para o dashboard (um por tabela, ciclando)
PALETTE = ["#1E88E5", "#00995D", "#FF9800", "#8E24AA",
           "#00ACC1", "#E53935", "#6D4C41", "#546E7A"]

APP_ID   = 204
APP_NAME = "TEA Backoffice"


# ── Main ──────────────────────────────────────────────────────────────────────
def run():
    t0 = time.perf_counter()
    print("\n" + "═" * 54)
    print(f"  App {APP_ID} — {APP_NAME}")
    print(f"  apex_generate_from_schema — {len(TABLES)} tabelas TEA")
    print("═" * 54)

    # ── 1. Conexão ────────────────────────────────────────────────────────────
    section("1/4  Conexão com Oracle ADB")
    if not ok("apex_connect", apex_connect())[0]:
        return

    # ── 2. Criar aplicação ────────────────────────────────────────────────────
    section("2/4  Criar aplicação")
    flag, _ = ok("apex_create_app", apex_create_app(
        app_id=APP_ID,
        app_name=APP_NAME,
        app_alias="tea-backoffice",
        login_page=101,
        home_page=1,
        language="pt-br",
        date_format="DD/MM/YYYY",
        theme_style="REDWOOD_LIGHT",
    ))
    if not flag:
        return

    # Login page
    ok("apex_generate_login(101)", apex_generate_login(101))

    # Auth schemes usados nos CRUDs de admin
    ok("auth IS_ADM",       apex_add_auth_scheme("IS_ADM",
        "SELECT 1 FROM TEA_USUARIOS WHERE DS_LOGIN = :APP_USER AND ID_PERFIL = "
        "(SELECT ID_PERFIL FROM TEA_PERFIS WHERE DS_PERFIL = 'ADM')"))
    ok("auth IS_CLINICA",   apex_add_auth_scheme("IS_CLINICA",
        "SELECT 1 FROM TEA_USUARIOS WHERE DS_LOGIN = :APP_USER AND ID_PERFIL = "
        "(SELECT ID_PERFIL FROM TEA_PERFIS WHERE DS_PERFIL = 'CLINICA')"))
    ok("auth IS_TERAPEUTA", apex_add_auth_scheme("IS_TERAPEUTA",
        "SELECT 1 FROM TEA_USUARIOS WHERE DS_LOGIN = :APP_USER AND ID_PERFIL = "
        "(SELECT ID_PERFIL FROM TEA_PERFIS WHERE DS_PERFIL = 'TERAPEUTA')"))

    # ── 3. apex_generate_from_schema ─────────────────────────────────────────
    section("3/4  apex_generate_from_schema")
    print(f"  Tabelas: {', '.join(t.replace('TEA_','') for t in TABLES)}")
    print()

    t_gen = time.perf_counter()
    flag, result = ok(
        "apex_generate_from_schema",
        apex_generate_from_schema(
            tables=TABLES,
            start_page_id=10,          # CRUDs: 10/11, 12/13, 14/15 ...
            include_dashboard=True,    # página 1 com KPI cards automáticos
            nav_icon_map=ICONS,
        ),
    )
    elapsed_gen = time.perf_counter() - t_gen

    if flag:
        print()
        print(f"  Tabelas processadas : {len(result.get('tables', []))}")
        print(f"  Páginas criadas     : {result.get('total_pages', 0)}  "
              f"({result.get('pages_created', [])})")
        print(f"  Itens criados       : {result.get('total_items', 0)}")
        print(f"  Tempo geração       : {elapsed_gen:.1f}s")
        print()
        for line in result.get("log", []):
            print(f"    · {line}")
    else:
        return

    # ── 4. Finalizar + validar ────────────────────────────────────────────────
    section("4/4  Finalizar e validar")
    ok("apex_finalize_app", apex_finalize_app())

    _, val = ok("apex_validate_app", apex_validate_app(APP_ID))
    if val.get("status") == "ok":
        score   = val.get("score", "?")
        issues  = val.get("issues", [])
        warns   = val.get("warnings", [])
        summary = val.get("summary", {})
        print(f"\n  Score de qualidade : {score}/100")
        print(f"  Páginas            : {summary.get('pages', '?')}")
        print(f"  Regiões            : {summary.get('regions', '?')}")
        print(f"  Itens              : {summary.get('items', '?')}")
        print(f"  Botões             : {summary.get('buttons', '?')}")
        print(f"  Processos          : {summary.get('processes', '?')}")
        if issues:
            print(f"\n  Erros ({len(issues)}):")
            for i in issues[:5]:
                print(f"    ✗  {i}")
        if warns:
            print(f"\n  Avisos ({len(warns)}):")
            for w in warns[:5]:
                print(f"    ⚠  {w}")
        if not issues and not warns:
            print("\n  Nenhum problema encontrado.")

    # ── Resumo ────────────────────────────────────────────────────────────────
    total = time.perf_counter() - t0
    print("\n" + "═" * 54)
    print(f"  App {APP_ID} criado em {total:.1f}s")
    print(f"  Login: f?p={APP_ID}:101")
    print("═" * 54 + "\n")


if __name__ == "__main__":
    run()
