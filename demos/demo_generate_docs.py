"""Demo — apex_generate_docs com App 204 (TEA Backoffice).

Gera documentação Markdown completa do app 204 automaticamente a partir
das views do dicionário de dados APEX, sem precisar abrir o browser.

Saída:
  - Console: estatísticas + preview das primeiras páginas
  - Arquivo: demos/app204_docs.md (Markdown completo pronto para uso)
"""
import os, sys, json, time, textwrap

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

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

from apex_mcp.tools.sql_tools    import apex_connect
from apex_mcp.tools.devops_tools import apex_generate_docs

APP_ID   = 204
OUT_FILE = os.path.join(os.path.dirname(__file__), "app204_docs.md")

# ── Helpers ───────────────────────────────────────────────────────────────────
def ok(label: str, result_str: str) -> tuple[bool, dict]:
    r = json.loads(result_str)
    if r.get("status") == "error":
        print(f"  ✗  {label}: {r['error']}")
        return False, r
    print(f"  ✓  {label}")
    return True, r


def preview_md(markdown: str, max_lines: int = 60) -> None:
    """Imprime as primeiras linhas do Markdown no console."""
    lines = markdown.splitlines()
    for line in lines[:max_lines]:
        print("  " + line)
    if len(lines) > max_lines:
        print(f"\n  ... ({len(lines) - max_lines} linhas adicionais no arquivo)")


# ── Main ──────────────────────────────────────────────────────────────────────
def run():
    t0 = time.perf_counter()
    print("\n" + "═" * 60)
    print(f"  apex_generate_docs — App {APP_ID} (TEA Backoffice)")
    print("═" * 60)

    # ── 1. Conexão ────────────────────────────────────────────────────────────
    print("\n[1] Conectando...")
    if not ok("apex_connect", apex_connect())[0]:
        return

    # ── 2. Gerar documentação ─────────────────────────────────────────────────
    print(f"\n[2] Gerando documentação do App {APP_ID}...")
    t_gen = time.perf_counter()
    flag, result = ok("apex_generate_docs", apex_generate_docs(APP_ID))
    elapsed = time.perf_counter() - t_gen

    if not flag:
        return

    stats    = result.get("stats", {})
    markdown = result.get("markdown", "")

    # ── 3. Estatísticas ───────────────────────────────────────────────────────
    print(f"\n[3] Estatísticas:")
    print(f"  Páginas       : {stats.get('pages', 0)}")
    print(f"  Regiões       : {stats.get('regions', 0)}")
    print(f"  Itens         : {stats.get('items', 0)}")
    print(f"  LOVs          : {stats.get('lovs', 0)}")
    print(f"  Auth Schemes  : {stats.get('auth_schemes', 0)}")
    print(f"  Linhas Markdown: {len(markdown.splitlines())}")
    print(f"  Tamanho       : {len(markdown):,} caracteres")
    print(f"  Tempo geração : {elapsed:.2f}s")

    # ── 4. Salvar arquivo ─────────────────────────────────────────────────────
    print(f"\n[4] Salvando em: {OUT_FILE}")
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(markdown)
    size_kb = os.path.getsize(OUT_FILE) / 1024
    print(f"  ✓  Arquivo salvo ({size_kb:.1f} KB)")

    # ── 5. Preview no console ─────────────────────────────────────────────────
    print(f"\n[5] Preview (primeiras 60 linhas):\n")
    print("  " + "─" * 56)
    preview_md(markdown, max_lines=60)
    print("  " + "─" * 56)

    # ── Resumo ────────────────────────────────────────────────────────────────
    total = time.perf_counter() - t0
    print(f"\n{'═' * 60}")
    print(f"  Documentação do App {APP_ID} gerada em {total:.1f}s")
    print(f"  Arquivo: {OUT_FILE}")
    print("═" * 60 + "\n")


if __name__ == "__main__":
    run()
