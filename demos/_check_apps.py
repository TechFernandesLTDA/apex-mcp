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
    print(f"  App {str(a.get('application_id','?')):>5} — {a.get('application_name','?')}")

# Check packages
q = """
SELECT object_name, status
FROM all_objects
WHERE object_type = 'PACKAGE'
  AND object_name IN ('PKG_CLAUDE_API','PKG_TEA_AI','PKG_TEA_VECTOR')
ORDER BY object_name
"""
pkgs = parse(apex_run_sql(q))
print("\nPACKAGES:")
for row in (pkgs.get("data") or []):
    print(f"  {row.get('OBJECT_NAME','?'):20} {row.get('STATUS','?')}")

# Check tables
q2 = """
SELECT table_name
FROM all_tables
WHERE table_name IN ('TEA_LOG_AUDITORIA','TEA_CONFIG','TEA_CONHECIMENTO','TEA_EMBEDDINGS','TEA_BENEFICIARIOS','TEA_AVALIACOES')
ORDER BY table_name
"""
tabs = parse(apex_run_sql(q2))
print("\nTABLES:")
for row in (tabs.get("data") or []):
    print(f"  {row.get('TABLE_NAME','?')}")

# Check SELECT AI profile
q3 = "SELECT profile_name FROM user_cloud_ai_profiles"
prof = parse(apex_run_sql(q3))
print("\nSELECT AI PROFILES:")
for row in (prof.get("data") or []):
    print(f"  {row.get('PROFILE_NAME','?')}")

# Check TEA_CONFIG for AI keys
q4 = "SELECT chave, SUBSTR(valor,1,40) val FROM tea_config"
cfg = parse(apex_run_sql(q4))
print("\nTEA_CONFIG:")
for row in (cfg.get("data") or []):
    print(f"  {row.get('CHAVE','?'):30} = {row.get('VAL','?')}")
