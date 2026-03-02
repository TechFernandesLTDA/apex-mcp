"""Check current apps and PKG status before building."""
import os, sys, json
sys.path.insert(0, r"C:\Projetos\Apex\mcp-server")
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

os.environ.update({
    "ORACLE_DB_USER": "TEA_APP", "ORACLE_DB_PASS": "TeaApp@2024#Unimed",
    "ORACLE_DSN": "u5cvlivnjuodscai_tp",
    "ORACLE_WALLET_DIR": r"C:\Projetos\Apex\wallet",
    "ORACLE_WALLET_PASSWORD": "apex1234",
    "APEX_WORKSPACE_ID": "8822816515098715",
    "APEX_SCHEMA": "TEA_APP", "APEX_WORKSPACE_NAME": "TEA",
})

from apex_mcp.tools.sql_tools import apex_connect, apex_run_sql
from apex_mcp.tools.app_tools import apex_list_apps

def parse(r):
    if isinstance(r, str): return json.loads(r)
    return r

r = parse(apex_connect()); print("CONNECT:", r.get("status"), r.get("message","")[:80])

# Apps
apps = parse(apex_list_apps())
print("\nAPPS:")
for a in (apps.get("data") or []):
    print(f"  App {str(a.get('APPLICATION_ID','?')):>5} — {a.get('APPLICATION_NAME','?')}")

# Check packages
pkgs = parse(apex_run_sql("""
SELECT object_name, status
FROM all_objects
WHERE object_type = 'PACKAGE'
  AND object_name IN ('PKG_CLAUDE_API','PKG_TEA_AI','PKG_TEA_VECTOR')
ORDER BY object_name
"""))
print("\nPACKAGES:")
for row in (pkgs.get("rows") or []):
    print(f"  {row.get('OBJECT_NAME','?'):20} {row.get('STATUS','?')}")

# Check tables
tabs = parse(apex_run_sql("""
SELECT table_name
FROM all_tables
WHERE table_name IN ('TEA_LOG_AUDITORIA','TEA_CONFIG','TEA_CONHECIMENTO','TEA_EMBEDDINGS','TEA_BENEFICIARIOS','TEA_AVALIACOES')
ORDER BY table_name
"""))
print("\nTABLES:")
for row in (tabs.get("rows") or []):
    print(f"  {row.get('TABLE_NAME','?')}")

# Check SELECT AI profile
prof = parse(apex_run_sql("SELECT profile_name FROM user_cloud_ai_profiles"))
print("\nSELECT AI PROFILES:")
for row in (prof.get("rows") or []):
    print(f"  {row.get('PROFILE_NAME','?')}")

# Check TEA_CONFIG for AI keys (correct column names: DS_CHAVE / DS_VALOR)
cfg = parse(apex_run_sql("SELECT DS_CHAVE, SUBSTR(DS_VALOR,1,40) AS VAL FROM tea_config ORDER BY DS_CHAVE"))
print("\nTEA_CONFIG:")
for row in (cfg.get("rows") or []):
    print(f"  {row.get('DS_CHAVE','?'):30} = {row.get('VAL','?')}")

# Log IA summary
log = parse(apex_run_sql("""
SELECT DS_OPERACAO, COUNT(*) AS TOTAL
FROM tea_log_auditoria
WHERE DS_OPERACAO IN ('CHAT_IA','ANALISE_IA','RECOMEND_IA','SELECT_AI','RAG_BUSCA')
GROUP BY DS_OPERACAO ORDER BY DS_OPERACAO
"""))
print("\nLOG IA (interações fictícias):")
for row in (log.get("rows") or []):
    print(f"  {row.get('DS_OPERACAO','?'):20} {row.get('TOTAL','?')}")

# TEA_CONHECIMENTO count
kb = parse(apex_run_sql("SELECT COUNT(*) AS TOTAL, COUNT(DISTINCT DS_CATEGORIA) AS CATS FROM tea_conhecimento WHERE FL_ATIVO='S'"))
print("\nTEA_CONHECIMENTO:")
for row in (kb.get("rows") or []):
    print(f"  {row.get('TOTAL','?')} artigos em {row.get('CATS','?')} categorias")
