"""Demo — apex_generate_rest_endpoints com tabelas do projeto TEA.

Expõe as principais tabelas operacionais do TEA como APIs REST via ORDS,
criando automaticamente os 5 endpoints padrão (GET list, POST, GET item, PUT, DELETE)
para cada tabela.

Base URL resultante (Oracle ADB):
  https://u5cvlivnjuodscai-u5cvlivnjuodscai.adb.sa-saopaulo-1.oraclecloudapps.com
  /ords/tea_app/{modulo}/

Tabelas incluídas (5):
  Módulo beneficiarios  → TEA_BENEFICIARIOS  (pacientes)
  Módulo avaliacoes     → TEA_AVALIACOES     (cabeçalho de avaliações)
  Módulo clinicas       → TEA_CLINICAS       (clínicas credenciadas)
  Módulo terapeutas     → TEA_TERAPEUTAS     (profissionais)
  Módulo provas         → TEA_PROVAS         (instrumentos ICHOM)
"""
import os, sys, json, time

# ── Credenciais TEA ───────────────────────────────────────────────────────────
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

from apex_mcp.tools.sql_tools   import apex_connect
from apex_mcp.tools.devops_tools import apex_generate_rest_endpoints
from apex_mcp.db import db

# ── Tabelas e configuração ────────────────────────────────────────────────────
ENDPOINTS = [
    {"table": "TEA_BENEFICIARIOS", "path": "beneficiarios", "auth": True},
    {"table": "TEA_AVALIACOES",    "path": "avaliacoes",    "auth": True},
    {"table": "TEA_CLINICAS",      "path": "clinicas",      "auth": False},   # referência pública
    {"table": "TEA_TERAPEUTAS",    "path": "terapeutas",    "auth": False},   # referência pública
    {"table": "TEA_PROVAS",        "path": "provas",        "auth": False},   # instrumentos públicos
]

BASE_URL = (
    "https://u5cvlivnjuodscai-u5cvlivnjuodscai"
    ".adb.sa-saopaulo-1.oraclecloudapps.com/ords/tea_app"
)

METHOD_PAD = {"GET": "GET   ", "POST": "POST  ", "PUT": "PUT   ", "DELETE": "DELETE"}

# ── Helpers ───────────────────────────────────────────────────────────────────
def ok(label: str, result_str: str) -> tuple[bool, dict]:
    r = json.loads(result_str)
    if r.get("status") == "error":
        print(f"  ✗  {label}: {r['error']}")
        return False, r
    print(f"  ✓  {label}")
    return True, r


def verify_module(module_name: str) -> int | None:
    """Verifica se o módulo ORDS foi criado. Retorna ID ou None."""
    try:
        rows = db.execute(
            "SELECT id FROM user_ords_modules WHERE name = :n",
            {"n": module_name},
        )
        return rows[0]["ID"] if rows else None
    except Exception:
        return None


# ── Main ──────────────────────────────────────────────────────────────────────
def run():
    t0 = time.perf_counter()
    print("\n" + "═" * 60)
    print("  apex_generate_rest_endpoints — TEA REST API")
    print(f"  {len(ENDPOINTS)} tabelas → {len(ENDPOINTS) * 5} endpoints ORDS")
    print("═" * 60)

    # ── 1. Conexão ────────────────────────────────────────────────────────────
    print("\n[1] Conectando ao Oracle ADB...")
    flag, _ = ok("apex_connect", apex_connect())
    if not flag:
        return

    # ── 2. Gerar endpoints ────────────────────────────────────────────────────
    print("\n[2] Gerando módulos ORDS...\n")
    all_results = []

    for cfg in ENDPOINTS:
        table = cfg["table"]
        path  = cfg["path"]
        auth  = cfg["auth"]

        t_start = time.perf_counter()
        flag, r = ok(
            f"apex_generate_rest_endpoints({table})",
            apex_generate_rest_endpoints(
                table_name=table,
                base_path=path,
                require_auth=auth,
            ),
        )
        elapsed = time.perf_counter() - t_start

        if flag:
            r["_elapsed"] = elapsed
            all_results.append(r)

    # ── 3. Verificar no banco ─────────────────────────────────────────────────
    print("\n[3] Verificando módulos ORDS no banco...\n")
    for r in all_results:
        mod_id = verify_module(r["module_name"])
        r["_verified"] = mod_id is not None
        status = f"ID={mod_id}" if mod_id else "NÃO encontrado"
        symbol = "✓" if mod_id else "✗"
        print(f"  {symbol}  {r['module_name']:20s}  {status}")

    # ── 4. Resumo de endpoints ────────────────────────────────────────────────
    print("\n[4] Endpoints criados:")
    print()

    for r in all_results:
        table  = r["table_name"]
        pk     = r["pk_column"]
        auth   = "🔒 autenticado" if r["require_auth"] else "🌐 público"
        elapsed = r["_elapsed"]
        verified = "✓" if r["_verified"] else "?"

        print(f"  {verified} {table} (PK: {pk}) — {auth} — {elapsed:.2f}s")
        for ep in r["endpoints"]:
            meth = METHOD_PAD.get(ep["method"], ep["method"].ljust(6))
            url  = f"{BASE_URL}{ep['path']}"
            print(f"      {meth}  {url}")
        print()

    # ── 5. Exemplos de chamada ────────────────────────────────────────────────
    if all_results:
        r0 = all_results[0]  # beneficiarios
        base = f"{BASE_URL}/{r0['module_name']}"
        pk   = r0["pk_column"].lower()
        print("[5] Exemplos de chamada (curl):")
        print()
        print(f"  # Listar beneficiários:")
        print(f'  curl -X GET "{base}/" \\')
        print(f'       -H "Authorization: Bearer <token>"')
        print()
        print(f"  # Buscar por PK:")
        print(f'  curl -X GET "{base}/42" \\')
        print(f'       -H "Authorization: Bearer <token>"')
        print()
        if len(all_results) > 2:
            r_pub = all_results[2]  # clinicas (público)
            print(f"  # Listar clínicas (público):")
            print(f'  curl -X GET "{BASE_URL}/{r_pub["module_name"]}/"')
            print()

    # ── 6. Estatísticas finais ────────────────────────────────────────────────
    total  = time.perf_counter() - t0
    ok_cnt = sum(1 for r in all_results if r.get("_verified"))
    ep_cnt = len(all_results) * 5

    print("═" * 60)
    print(f"  Módulos criados : {len(all_results)}/{len(ENDPOINTS)}")
    print(f"  Verificados     : {ok_cnt}/{len(all_results)}")
    print(f"  Endpoints total : {ep_cnt}")
    print(f"  Tempo total     : {total:.1f}s")
    print("═" * 60 + "\n")


if __name__ == "__main__":
    run()
