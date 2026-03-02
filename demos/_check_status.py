"""Quick status check and app list."""
import os, sys, json
sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault('ORACLE_DB_USER', 'TEA_APP')
os.environ.setdefault('ORACLE_DB_PASS', 'TeaApp@2024#Unimed')
os.environ.setdefault('ORACLE_DSN', 'u5cvlivnjuodscai_tp')
os.environ.setdefault('ORACLE_WALLET_DIR', r'C:\Projetos\Apex\wallet')
os.environ.setdefault('ORACLE_WALLET_PASSWORD', 'apex1234')
os.environ.setdefault('APEX_WORKSPACE_ID', '8822816515098715')
os.environ.setdefault('APEX_SCHEMA', 'TEA_APP')
os.environ.setdefault('APEX_WORKSPACE_NAME', 'TEA')

from apex_mcp.tools.sql_tools import apex_connect, apex_status
from apex_mcp.tools.app_tools import apex_list_apps

print("=== CONNECT ===")
print(json.dumps(apex_connect(), indent=2))
print("\n=== STATUS ===")
print(json.dumps(apex_status(), indent=2))
print("\n=== APPS ===")
print(json.dumps(apex_list_apps(), indent=2))
