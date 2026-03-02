"""App 206 — Centro IA — Hub de Inteligência Artificial (TEA).

Aplicativo Oracle APEX 24.2 completo com contexto de Inteligência Artificial,
integrando PKG_CLAUDE_API, PKG_TEA_AI, PKG_TEA_VECTOR e SELECT AI (DBMS_CLOUD_AI).

Páginas (9):
  100 → Login (customizado)
    1 → Dashboard IA (métricas de uso, gráficos, interações recentes)
   10 → Chat com Claude (interface chat interativa + quick prompts)
   20 → Análise Clínica IA (selecionar avaliação → análise detalhada por Claude)
   30 → Recomendações Terapêuticas (selecionar paciente → recomendações IA)
   40 → SQL Intelligence (linguagem natural → SQL via SELECT AI)
   50 → Base de Conhecimento RAG (busca vetorial + PKG_TEA_VECTOR)
   60 → Log de Interações IA (audit trail de todas as chamadas)
   70 → Configurações IA (API key, modelo, parâmetros)
"""
import os, sys, json, time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

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

from apex_mcp.tools.sql_tools       import apex_connect
from apex_mcp.tools.app_tools       import (
    apex_list_apps, apex_create_app, apex_finalize_app, apex_delete_app,
)
from apex_mcp.tools.page_tools      import apex_add_page
from apex_mcp.tools.component_tools import apex_add_region, apex_add_item, apex_add_process, apex_add_button, apex_add_dynamic_action
from apex_mcp.tools.shared_tools    import apex_add_app_item, apex_add_nav_item, apex_add_lov
from apex_mcp.tools.generator_tools import apex_generate_login
from apex_mcp.tools.advanced_tools  import (
    apex_add_global_css, apex_add_notification_region, apex_add_page_css,
    apex_validate_app,
)
from apex_mcp.tools.visual_tools    import (
    apex_add_metric_cards, apex_generate_analytics_page,
    apex_add_jet_chart, apex_add_gauge,
)
from apex_mcp.tools.js_tools        import apex_add_page_js
from apex_mcp.themes                import UNIMED_THEME_CSS

APP_ID   = 206
APP_NAME = "Centro IA — Plataforma TEA"

# =============================================================================
# CSS GLOBAL
# =============================================================================
APP_EXTRA_CSS = """
/* ── AI Hub — Chat Interface ────────────────────────────────────────────── */
#ai-chat-container{
  display:flex;flex-direction:column;height:580px;
  background:#fff;border-radius:12px;overflow:hidden;
  box-shadow:0 4px 24px rgba(0,0,0,.08)
}
#chat-header{
  background:linear-gradient(135deg,#00995D 0%,#006B3F 100%);
  color:#fff;padding:14px 20px;
  display:flex;align-items:center;gap:12px;flex-shrink:0
}
#chat-header .fa{font-size:1.4rem}
#chat-header strong{font-size:.95rem;font-weight:700}
.model-badge{
  background:rgba(255,255,255,.2);border-radius:12px;
  padding:3px 10px;font-size:11px;margin-left:auto;white-space:nowrap
}
#chat-history{
  flex:1;overflow-y:auto;padding:18px 20px;
  background:#F5F7FA;display:flex;flex-direction:column;gap:10px
}
.chat-message{display:flex;align-items:flex-start;gap:10px;animation:chatFadeIn .3s ease}
.chat-msg-user{flex-direction:row-reverse}
.chat-icon{
  width:34px;height:34px;border-radius:50%;display:flex;
  align-items:center;justify-content:center;
  font-size:14px;flex-shrink:0;background:#00995D;color:#fff;padding:9px
}
.chat-msg-user .chat-icon{background:#1E88E5}
.chat-msg-error .chat-icon{background:#E53935}
.chat-bubble{
  max-width:72%;padding:11px 15px;border-radius:18px;
  line-height:1.55;font-size:.875rem;
  background:#fff;box-shadow:0 2px 8px rgba(0,0,0,.06);word-break:break-word
}
.chat-msg-user .chat-bubble{
  background:#1E88E5;color:#fff;border-radius:18px 18px 4px 18px
}
.chat-msg-ai .chat-bubble{border-radius:18px 18px 18px 4px}
.chat-msg-error .chat-bubble{background:#ffebee;color:#c62828;border-radius:12px}
#typing-indicator{
  display:none;padding:6px 20px;gap:5px;align-items:center
}
.typing-dot{
  display:inline-block;width:8px;height:8px;
  background:#00995D;border-radius:50%;animation:typingBounce 1s infinite
}
.typing-dot:nth-child(2){animation-delay:.2s}
.typing-dot:nth-child(3){animation-delay:.4s}
#chat-input-area{
  padding:10px 16px 14px;background:#fff;border-top:1px solid #e8ecf0;flex-shrink:0
}
.quick-prompts{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px}
.quick-btn{
  background:#f0faf5;border:1px solid #00995D;color:#00995D;
  border-radius:20px;padding:5px 12px;font-size:11.5px;cursor:pointer;
  transition:all .2s;font-family:inherit;white-space:nowrap
}
.quick-btn:hover{background:#00995D;color:#fff}
#chat-send-row{display:flex;gap:8px;align-items:flex-end}
#chat-textarea{
  flex:1;border:1px solid #d1d9e0;border-radius:10px;
  padding:10px 14px;font-size:.875rem;font-family:inherit;
  resize:none;max-height:100px;min-height:40px;
  transition:border-color .2s;line-height:1.4
}
#chat-textarea:focus{outline:none;border-color:#00995D;box-shadow:0 0 0 3px rgba(0,153,93,.12)}
#btn-send-chat{
  background:#00995D;color:#fff;border:none;border-radius:10px;
  padding:10px 18px;font-size:.875rem;font-weight:600;cursor:pointer;
  transition:background .2s;flex-shrink:0;white-space:nowrap
}
#btn-send-chat:hover{background:#006B3F}
@keyframes chatFadeIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
@keyframes typingBounce{0%,60%,100%{transform:translateY(0)}30%{transform:translateY(-8px)}}

/* ── SQL Intelligence ───────────────────────────────────────────────────── */
.sql-panel{background:#1e1e1e;border-radius:10px;padding:16px 18px;margin-top:4px}
.sql-panel pre{
  color:#d4d4d4;font-family:Consolas,'Courier New',monospace;
  font-size:.82rem;white-space:pre-wrap;word-break:break-all;margin:0;line-height:1.5
}
.sql-panel-header{
  display:flex;align-items:center;gap:8px;
  color:#00995D;font-size:.8rem;font-weight:600;margin-bottom:8px
}
.ai-result-box{
  background:#f8fbff;border:1px solid #d0e8ff;border-radius:10px;
  padding:16px 18px;font-size:.875rem;line-height:1.65;color:#1a2a3a;margin-top:8px
}
.ai-result-empty{
  text-align:center;padding:40px 20px;color:#8a9bb0;font-size:.875rem
}
.ai-result-empty .fa{font-size:2.5rem;display:block;margin-bottom:10px;color:#bdc8d8}

/* ── RAG Knowledge Base ─────────────────────────────────────────────────── */
.kb-card{
  background:#fff;border-radius:10px;padding:16px;margin-bottom:12px;
  box-shadow:0 2px 8px rgba(0,0,0,.06);border-left:4px solid #00995D;
  transition:box-shadow .2s
}
.kb-card:hover{box-shadow:0 4px 16px rgba(0,0,0,.1)}
.kb-card h4{margin:0 0 8px;font-size:.9rem;color:#00995D;font-weight:700}
.kb-card p{margin:0 0 8px;font-size:.85rem;color:#444;line-height:1.5}
.sim-badge{
  display:inline-block;background:#e8f5e9;color:#2e7d32;
  border-radius:12px;padding:2px 10px;font-size:.78rem;font-weight:600
}
.kb-empty{text-align:center;color:#8a9bb0;padding:40px 20px;font-size:.875rem}
.kb-empty .fa{font-size:2rem;color:#bdc8d8;display:block;margin-bottom:8px}

/* ── Analysis result ────────────────────────────────────────────────────── */
.analysis-card{
  background:#fff;border-radius:12px;padding:20px 22px;
  box-shadow:0 4px 16px rgba(0,0,0,.07);border-top:4px solid #00995D
}
.analysis-header{
  display:flex;align-items:center;gap:12px;margin-bottom:16px;
  padding-bottom:14px;border-bottom:1px solid #f0f0f0
}
.analysis-header .fa{font-size:1.6rem;color:#00995D}
.analysis-title{font-size:1rem;font-weight:700;color:#00995D}
.analysis-sub{font-size:.82rem;color:#777}
.analysis-body{font-size:.875rem;line-height:1.7;color:#2c3e50;white-space:pre-line}

/* ── IA Feature nav tiles (dashboard) ──────────────────────────────────── */
.ia-tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:14px}
.ia-tile{
  border-radius:12px;padding:20px 14px;text-align:center;cursor:pointer;
  text-decoration:none;display:block;transition:transform .2s,box-shadow .2s;color:#fff
}
.ia-tile:hover{transform:translateY(-4px);box-shadow:0 8px 24px rgba(0,0,0,.18);color:#fff}
.ia-tile .fa{font-size:2rem;display:block;margin-bottom:10px;opacity:.9}
.ia-tile-label{font-size:.82rem;font-weight:700;line-height:1.3}
.ia-tile-sub{font-size:.74rem;opacity:.8;margin-top:3px}
.tile-chat{background:linear-gradient(135deg,#00995D,#006B3F)}
.tile-analysis{background:linear-gradient(135deg,#1E88E5,#0d47a1)}
.tile-rec{background:linear-gradient(135deg,#43A047,#1b5e20)}
.tile-sql{background:linear-gradient(135deg,#FB8C00,#e65100)}
.tile-rag{background:linear-gradient(135deg,#8E24AA,#4a148c)}
.tile-log{background:linear-gradient(135deg,#00ACC1,#006064)}
.tile-config{background:linear-gradient(135deg,#546E7A,#263238)}

/* ── Page header banners ────────────────────────────────────────────────── */
.ia-page-header{
  display:flex;align-items:center;gap:14px;
  padding:14px 18px;border-radius:10px;margin-bottom:4px;color:#fff
}
.ia-page-header .fa{font-size:1.6rem;flex-shrink:0}
.ia-page-header-text strong{font-size:.95rem;font-weight:700;display:block}
.ia-page-header-text span{font-size:.82rem;opacity:.85}
.ia-header-chat{background:linear-gradient(135deg,#00995D,#006B3F)}
.ia-header-analysis{background:linear-gradient(135deg,#1E88E5,#0d47a1)}
.ia-header-rec{background:linear-gradient(135deg,#43A047,#1b5e20)}
.ia-header-sql{background:linear-gradient(135deg,#FB8C00,#e65100)}
.ia-header-rag{background:linear-gradient(135deg,#8E24AA,#4a148c)}
.ia-header-log{background:linear-gradient(135deg,#00ACC1,#006064)}
.ia-header-config{background:linear-gradient(135deg,#546E7A,#263238)}
""".strip()

# =============================================================================
# PL/SQL PARA REGIÕES HTML (banners)
# =============================================================================
def ia_banner(icon: str, title: str, subtitle: str, css_class: str) -> str:
    return f"""BEGIN
  sys.htp.p('<div class="ia-page-header {css_class}">');
  sys.htp.p('<i class="fa {icon}" aria-hidden="true"></i>');
  sys.htp.p('<div class="ia-page-header-text">');
  sys.htp.p('<strong>{title}</strong>');
  sys.htp.p('<span>{subtitle}</span>');
  sys.htp.p('</div></div>');
END;""".strip()


# =============================================================================
# PL/SQL PARA REGIÕES ESTÁTICAS (render direto)
# =============================================================================
DASHBOARD_TILES = """
DECLARE
  l_app VARCHAR2(10) := TO_CHAR(:APP_ID);
  l_ses VARCHAR2(100) := :APP_SESSION;
BEGIN
  sys.htp.p('<div class="ia-tiles">');
  sys.htp.p('<a class="ia-tile tile-chat" href="f?p='||l_app||':10:'||l_ses||'">');
  sys.htp.p('<i class="fa fa-comments"></i>');
  sys.htp.p('<div class="ia-tile-label">Chat com Claude</div>');
  sys.htp.p('<div class="ia-tile-sub">Assistente IA</div></a>');

  sys.htp.p('<a class="ia-tile tile-analysis" href="f?p='||l_app||':20:'||l_ses||'">');
  sys.htp.p('<i class="fa fa-stethoscope"></i>');
  sys.htp.p('<div class="ia-tile-label">Analise Clinica</div>');
  sys.htp.p('<div class="ia-tile-sub">IA por avaliacao</div></a>');

  sys.htp.p('<a class="ia-tile tile-rec" href="f?p='||l_app||':30:'||l_ses||'">');
  sys.htp.p('<i class="fa fa-lightbulb-o"></i>');
  sys.htp.p('<div class="ia-tile-label">Recomendacoes</div>');
  sys.htp.p('<div class="ia-tile-sub">Terapia por paciente</div></a>');

  sys.htp.p('<a class="ia-tile tile-sql" href="f?p='||l_app||':40:'||l_ses||'">');
  sys.htp.p('<i class="fa fa-database"></i>');
  sys.htp.p('<div class="ia-tile-label">SQL Intelligence</div>');
  sys.htp.p('<div class="ia-tile-sub">NL para SQL</div></a>');

  sys.htp.p('<a class="ia-tile tile-rag" href="f?p='||l_app||':50:'||l_ses||'">');
  sys.htp.p('<i class="fa fa-search"></i>');
  sys.htp.p('<div class="ia-tile-label">Base Conhecimento</div>');
  sys.htp.p('<div class="ia-tile-sub">Busca RAG vetorial</div></a>');

  sys.htp.p('<a class="ia-tile tile-log" href="f?p='||l_app||':60:'||l_ses||'">');
  sys.htp.p('<i class="fa fa-history"></i>');
  sys.htp.p('<div class="ia-tile-label">Log de Interacoes</div>');
  sys.htp.p('<div class="ia-tile-sub">Audit trail IA</div></a>');

  sys.htp.p('<a class="ia-tile tile-config" href="f?p='||l_app||':70:'||l_ses||'">');
  sys.htp.p('<i class="fa fa-cog"></i>');
  sys.htp.p('<div class="ia-tile-label">Configuracoes</div>');
  sys.htp.p('<div class="ia-tile-sub">API &amp; modelos</div></a>');
  sys.htp.p('</div>');
END;""".strip()

CHAT_HTML = """
BEGIN
  sys.htp.p('<div id="ai-chat-container">');

  -- Header
  sys.htp.p('<div id="chat-header">');
  sys.htp.p('<i class="fa fa-robot" aria-hidden="true"></i>');
  sys.htp.p('<strong>Assistente Claude</strong>');
  sys.htp.p('<span class="model-badge" id="chat-model-badge">claude-sonnet-4-6</span>');
  sys.htp.p('</div>');

  -- Chat history (with welcome message)
  sys.htp.p('<div id="chat-history">');
  sys.htp.p('<div class="chat-message chat-msg-ai">');
  sys.htp.p('<span class="chat-icon fa fa-robot"></span>');
  sys.htp.p('<div class="chat-bubble">');
  sys.htp.p('Ol&aacute;! Sou o <strong>Assistente Claude</strong> da Plataforma TEA.');
  sys.htp.p('<br>Posso ajudar com:<br>');
  sys.htp.p('&bull; An&aacute;lise de avalia&ccedil;&otilde;es e scores<br>');
  sys.htp.p('&bull; Interpreta&ccedil;&atilde;o de instrumentos (VINELAND, CBCL, RBS-R)<br>');
  sys.htp.p('&bull; Boas pr&aacute;ticas cl&iacute;nicas para TEA<br>');
  sys.htp.p('&bull; Qualquer d&uacute;vida sobre a plataforma');
  sys.htp.p('</div></div>');
  sys.htp.p('</div>'); -- chat-history

  -- Typing indicator
  sys.htp.p('<div id="typing-indicator">');
  sys.htp.p('<span class="typing-dot"></span>');
  sys.htp.p('<span class="typing-dot"></span>');
  sys.htp.p('<span class="typing-dot"></span>');
  sys.htp.p('</div>');

  -- Input area
  sys.htp.p('<div id="chat-input-area">');
  sys.htp.p('<div class="quick-prompts">');
  sys.htp.p('<button class="quick-btn" onclick="iaQuickPrompt(''Resumir padroes clinicos dos pacientes TEA desta semana'')">&#128202; Padroes</button>');
  sys.htp.p('<button class="quick-btn" onclick="iaQuickPrompt(''Quais as melhores praticas para avaliacao VINELAND 3?'')">&#128203; VINELAND</button>');
  sys.htp.p('<button class="quick-btn" onclick="iaQuickPrompt(''Como interpretar scores baixos em Comunicacao?'')">&#128172; Scores</button>');
  sys.htp.p('<button class="quick-btn" onclick="iaQuickPrompt(''Diferenca entre CBCL e RBS-R para TEA'')">&#9883; Instrumentos</button>');
  sys.htp.p('</div>');
  sys.htp.p('<div id="chat-send-row">');
  sys.htp.p('<textarea id="chat-textarea" rows="2" placeholder="Digite sua mensagem... (Enter para enviar, Shift+Enter para nova linha)"></textarea>');
  sys.htp.p('<button id="btn-send-chat" onclick="iaSendChatMessage()"><i class="fa fa-send"></i> Enviar</button>');
  sys.htp.p('</div>');
  sys.htp.p('</div>'); -- input-area

  sys.htp.p('</div>'); -- ai-chat-container
END;""".strip()

SQL_INTEL_HTML = """
BEGIN
  sys.htp.p('<div id="sql-result-container" style="display:none">');
  sys.htp.p('<div class="sql-panel">');
  sys.htp.p('<div class="sql-panel-header"><i class="fa fa-code"></i> SQL Gerado por IA</div>');
  sys.htp.p('<pre id="sql-generated-text"></pre>');
  sys.htp.p('</div>');
  sys.htp.p('<div class="ai-result-box" id="sql-narrative-text" style="margin-top:8px"></div>');
  sys.htp.p('</div>');
  sys.htp.p('<div class="ai-result-empty" id="sql-empty-state">');
  sys.htp.p('<i class="fa fa-database"></i>');
  sys.htp.p('<p>Digite uma pergunta em portugu&ecirc;s e clique em <strong>Executar</strong>.<br>');
  sys.htp.p('O SELECT AI ir&aacute; gerar o SQL e apresentar a resposta em linguagem natural.</p>');
  sys.htp.p('<p style="font-size:.8rem;color:#aaa">Exemplos:<br>');
  sys.htp.p('"Quantos benefici&aacute;rios existem por cl&iacute;nica?"<br>');
  sys.htp.p('"Qual o score m&eacute;dio das avalia&ccedil;&otilde;es do mes passado?"<br>');
  sys.htp.p('"Listar os 5 terapeutas com mais avalia&ccedil;&otilde;es"</p>');
  sys.htp.p('</div>');
END;""".strip()

KB_HTML = """
BEGIN
  sys.htp.p('<div id="kb-resultados">');
  sys.htp.p('<div class="kb-empty">');
  sys.htp.p('<i class="fa fa-search"></i>');
  sys.htp.p('<p>Digite um termo de busca para pesquisar na base de conhecimento TEA.<br>');
  sys.htp.p('A busca utiliza similaridade vetorial (PKG_TEA_VECTOR) quando disponivel.</p>');
  sys.htp.p('</div>');
  sys.htp.p('</div>');
END;""".strip()

ANALYSIS_HTML = """
BEGIN
  sys.htp.p('<div id="analysis-result">');
  sys.htp.p('<div class="ai-result-empty">');
  sys.htp.p('<i class="fa fa-stethoscope"></i>');
  sys.htp.p('<p>Selecione uma avalia&ccedil;&atilde;o e clique em <strong>Analisar com IA</strong>.<br>');
  sys.htp.p('O Claude ir&aacute; interpretar os scores e sugerir observa&ccedil;&otilde;es cl&iacute;nicas.</p>');
  sys.htp.p('</div>');
  sys.htp.p('</div>');
END;""".strip()

REC_HTML = """
BEGIN
  sys.htp.p('<div id="rec-result">');
  sys.htp.p('<div class="ai-result-empty">');
  sys.htp.p('<i class="fa fa-lightbulb-o"></i>');
  sys.htp.p('<p>Selecione um benefici&aacute;rio e clique em <strong>Gerar Recomenda&ccedil;&otilde;es</strong>.<br>');
  sys.htp.p('O Claude ir&aacute; sugerir abordagens terap&ecirc;uticas baseadas no hist&oacute;rico de avalia&ccedil;&otilde;es.</p>');
  sys.htp.p('</div>');
  sys.htp.p('</div>');
END;""".strip()

CONFIG_PLSQL = """
DECLARE
  v_key   VARCHAR2(200);
  v_val   VARCHAR2(4000);
BEGIN
  sys.htp.p('<div class="t-Form-fieldContainer">');
  BEGIN
    SELECT valor INTO v_val FROM tea_config WHERE chave = 'ANTHROPIC_API_KEY';
    sys.htp.p('<div class="t-Form-labelContainer"><label class="t-Form-label">Anthropic API Key</label></div>');
    sys.htp.p('<div class="t-Form-inputContainer">');
    sys.htp.p('<input type="text" class="text_field apex-item-text" value="****'||SUBSTR(v_val,-4)||'" readonly style="width:100%;max-width:400px">');
    sys.htp.p('</div>');
  EXCEPTION WHEN NO_DATA_FOUND THEN
    sys.htp.p('<p style="color:#c0392b">ANTHROPIC_API_KEY nao configurada em TEA_CONFIG.</p>');
  END;
  sys.htp.p('</div>');

  sys.htp.p('<div class="t-Form-fieldContainer" style="margin-top:16px">');
  BEGIN
    SELECT valor INTO v_val FROM tea_config WHERE chave = 'AI_MODEL';
    sys.htp.p('<div class="t-Form-labelContainer"><label class="t-Form-label">Modelo Ativo</label></div>');
    sys.htp.p('<div class="t-Form-inputContainer">');
    sys.htp.p('<input type="text" class="text_field apex-item-text" value="'||APEX_ESCAPE.HTML(v_val)||'" readonly style="width:100%;max-width:400px">');
    sys.htp.p('</div>');
  EXCEPTION WHEN NO_DATA_FOUND THEN
    sys.htp.p('<p style="color:#999;font-size:.85rem">AI_MODEL nao definido (padrao: claude-sonnet-4-6)</p>');
  END;
  sys.htp.p('</div>');

  sys.htp.p('<div style="margin-top:20px;padding:14px;background:#f0faf5;border-radius:8px;border-left:4px solid #00995D">');
  sys.htp.p('<strong style="color:#006B3F">Pacotes PL/SQL Ativos:</strong><br>');
  FOR pkg IN (SELECT object_name, status FROM user_objects WHERE object_type=chr(80)||chr(65)||chr(67)||chr(75)||chr(65)||chr(71)||chr(69) AND object_name LIKE chr(80)||chr(75)||chr(71)||chr(95)||chr(37) ORDER BY object_name) LOOP
    sys.htp.p('<span style="display:inline-block;margin:3px 6px 3px 0;padding:2px 10px;border-radius:10px;font-size:.8rem;background:'||CASE pkg.status WHEN 'VALID' THEN '#e8f5e9' ELSE '#ffebee' END||';color:'||CASE pkg.status WHEN 'VALID' THEN '#2e7d32' ELSE '#c62828' END||'">'||APEX_ESCAPE.HTML(pkg.object_name)||' &mdash; '||pkg.status||'</span>');
  END LOOP;
  sys.htp.p('</div>');

  sys.htp.p('<div style="margin-top:14px;padding:14px;background:#f8fbff;border-radius:8px;border-left:4px solid #1E88E5">');
  sys.htp.p('<strong style="color:#0d47a1">SELECT AI Profile:</strong><br>');
  BEGIN
    SELECT profile_name INTO v_key FROM user_cloud_ai_profiles WHERE rownum=1;
    sys.htp.p('<span style="color:#1E88E5;font-weight:600">'||APEX_ESCAPE.HTML(v_key)||'</span> <span style="color:#27ae60;font-size:.82rem">&#10003; Ativo</span>');
  EXCEPTION WHEN NO_DATA_FOUND THEN
    sys.htp.p('<span style="color:#c0392b">Nenhum profile configurado.</span>');
  END;
  sys.htp.p('</div>');
END;""".strip()

# =============================================================================
# AJAX PL/SQL PROCESSES
# =============================================================================
AJAX_CHAT = """
DECLARE
  l_mensagem  VARCHAR2(4000) := APEX_APPLICATION.G_X01;
  l_modelo    VARCHAR2(100)  := APEX_APPLICATION.G_X02;
  l_resposta  CLOB;
  l_contexto  VARCHAR2(4000) := 'Voce e um assistente clinico especializado em Transtorno do Espectro Autista (TEA). Responda sempre em portugues, de forma clara e profissional. Contexto: Plataforma Desfecho TEA - Unimed Nacional, padrão ICHOM.';
BEGIN
  IF l_mensagem IS NULL OR LENGTH(TRIM(l_mensagem)) = 0 THEN
    APEX_JSON.OPEN_OBJECT;
    APEX_JSON.WRITE('status','error');
    APEX_JSON.WRITE('mensagem','Mensagem vazia.');
    APEX_JSON.CLOSE_OBJECT;
    RETURN;
  END IF;

  -- Motor 1: PKG_CLAUDE_API.CHAT
  BEGIN
    l_resposta := PKG_CLAUDE_API.CHAT(
      p_mensagem  => l_mensagem,
      p_contexto  => l_contexto
    );
  EXCEPTION WHEN OTHERS THEN
    -- Motor 2: PKG_TEA_AI fallback
    BEGIN
      EXECUTE IMMEDIATE
        'BEGIN :r := PKG_TEA_AI.CHAT(p_mensagem=>:m, p_contexto=>:c); END;'
        USING OUT l_resposta, IN l_mensagem, IN l_contexto;
    EXCEPTION WHEN OTHERS THEN
      -- Motor 3: SELECT AI fallback
      BEGIN
        l_resposta := DBMS_CLOUD_AI.GENERATE(
          prompt       => l_mensagem,
          profile_name => 'TEA_AI_PROFILE',
          action       => 'chat'
        );
      EXCEPTION WHEN OTHERS THEN
        l_resposta := '[Erro ao acessar IA: ' || SQLERRM || ']';
      END;
    END;
  END;

  -- Log da interacao
  BEGIN
    INSERT INTO TEA_LOG_AUDITORIA (DS_ACAO, DS_DETALHES, DS_USUARIO, DT_LOG)
    VALUES ('CHAT_IA', SUBSTR('P:'||l_mensagem||' R:'||SUBSTR(l_resposta,1,100),1,4000),
            :APP_USER, SYSTIMESTAMP);
    COMMIT;
  EXCEPTION WHEN OTHERS THEN NULL; END;

  APEX_JSON.OPEN_OBJECT;
  APEX_JSON.WRITE('status','success');
  APEX_JSON.WRITE('resposta', l_resposta);
  APEX_JSON.CLOSE_OBJECT;
EXCEPTION WHEN OTHERS THEN
  APEX_JSON.OPEN_OBJECT;
  APEX_JSON.WRITE('status','error');
  APEX_JSON.WRITE('mensagem', 'Erro interno: '||SQLERRM);
  APEX_JSON.CLOSE_OBJECT;
END;""".strip()

AJAX_ANALYSIS = """
DECLARE
  l_id_aval   NUMBER := TO_NUMBER(APEX_APPLICATION.G_X01);
  l_resultado CLOB;
  l_benefic   VARCHAR2(200);
  l_prova     VARCHAR2(200);
  l_score     NUMBER;
  l_pct       NUMBER;
BEGIN
  IF l_id_aval IS NULL THEN
    APEX_JSON.OPEN_OBJECT;
    APEX_JSON.WRITE('status','error');
    APEX_JSON.WRITE('mensagem','Selecione uma avaliacao.');
    APEX_JSON.CLOSE_OBJECT;
    RETURN;
  END IF;

  -- Buscar dados da avaliacao
  BEGIN
    SELECT b.DS_NOME, p.DS_NOME, a.NR_SCORE_TOTAL, a.NR_PCT_TOTAL
      INTO l_benefic, l_prova, l_score, l_pct
      FROM TEA_AVALIACOES a
      JOIN TEA_BENEFICIARIOS b ON b.ID_BENEFICIARIO = a.ID_BENEFICIARIO
      JOIN TEA_PROVAS p ON p.ID_PROVA = a.ID_PROVA
     WHERE a.ID_AVALIACAO = l_id_aval;
  EXCEPTION WHEN NO_DATA_FOUND THEN
    APEX_JSON.OPEN_OBJECT;
    APEX_JSON.WRITE('status','error');
    APEX_JSON.WRITE('mensagem','Avaliacao nao encontrada.');
    APEX_JSON.CLOSE_OBJECT;
    RETURN;
  END;

  -- Tentar PKG_CLAUDE_API
  BEGIN
    l_resultado := PKG_CLAUDE_API.ANALISAR_AVALIACAO(p_id_avaliacao => l_id_aval);
  EXCEPTION WHEN OTHERS THEN
    -- Fallback: gerar analise com contexto
    DECLARE l_prompt VARCHAR2(4000);
    BEGIN
      l_prompt := 'Analise clinica TEA: Paciente '||l_benefic||', instrumento '||l_prova||', score '||l_score||' ('||ROUND(l_pct)||'%). Forneca interpretacao clinica detalhada dos resultados, areas de atencao e sugestoes de intervencao.';
      BEGIN
        l_resultado := DBMS_CLOUD_AI.GENERATE(prompt=>l_prompt, profile_name=>'TEA_AI_PROFILE', action=>'narrate');
      EXCEPTION WHEN OTHERS THEN
        l_resultado := 'Erro ao gerar analise: '||SQLERRM;
      END;
    END;
  END;

  BEGIN
    INSERT INTO TEA_LOG_AUDITORIA(DS_ACAO,DS_DETALHES,DS_USUARIO,DT_LOG)
    VALUES('ANALISE_IA','Avaliacao ID:'||l_id_aval||' Paciente:'||l_benefic,:APP_USER,SYSTIMESTAMP);
    COMMIT;
  EXCEPTION WHEN OTHERS THEN NULL; END;

  APEX_JSON.OPEN_OBJECT;
  APEX_JSON.WRITE('status','success');
  APEX_JSON.WRITE('resultado', l_resultado);
  APEX_JSON.WRITE('beneficiario', l_benefic);
  APEX_JSON.WRITE('instrumento', l_prova);
  APEX_JSON.WRITE('score', l_score);
  APEX_JSON.WRITE('percentual', ROUND(l_pct));
  APEX_JSON.CLOSE_OBJECT;
EXCEPTION WHEN OTHERS THEN
  APEX_JSON.OPEN_OBJECT;
  APEX_JSON.WRITE('status','error');
  APEX_JSON.WRITE('mensagem','Erro: '||SQLERRM);
  APEX_JSON.CLOSE_OBJECT;
END;""".strip()

AJAX_RECOMMENDATIONS = """
DECLARE
  l_id_ben    NUMBER := TO_NUMBER(APEX_APPLICATION.G_X01);
  l_resultado CLOB;
  l_nome      VARCHAR2(200);
BEGIN
  IF l_id_ben IS NULL THEN
    APEX_JSON.OPEN_OBJECT;
    APEX_JSON.WRITE('status','error');
    APEX_JSON.WRITE('mensagem','Selecione um beneficiario.');
    APEX_JSON.CLOSE_OBJECT;
    RETURN;
  END IF;

  SELECT DS_NOME INTO l_nome FROM TEA_BENEFICIARIOS WHERE ID_BENEFICIARIO = l_id_ben;

  -- Motor 1
  BEGIN
    l_resultado := PKG_CLAUDE_API.RECOMENDAR_TERAPIA(p_id_beneficiario => l_id_ben);
  EXCEPTION WHEN OTHERS THEN
    DECLARE l_prompt VARCHAR2(4000); v_ult_score NUMBER; v_cnt NUMBER;
    BEGIN
      SELECT COUNT(*), NVL(MAX(NR_PCT_TOTAL),0)
        INTO v_cnt, v_ult_score
        FROM TEA_AVALIACOES WHERE ID_BENEFICIARIO = l_id_ben;
      l_prompt := 'Paciente TEA: '||l_nome||'. Total de '||v_cnt||' avaliacoes. Ultimo percentual: '||ROUND(v_ult_score)||'%. Gere recomendacoes terapeuticas personalizadas e plano de intervencao.';
      BEGIN
        l_resultado := DBMS_CLOUD_AI.GENERATE(prompt=>l_prompt, profile_name=>'TEA_AI_PROFILE', action=>'narrate');
      EXCEPTION WHEN OTHERS THEN
        l_resultado := 'Erro ao gerar recomendacoes: '||SQLERRM;
      END;
    END;
  END;

  BEGIN
    INSERT INTO TEA_LOG_AUDITORIA(DS_ACAO,DS_DETALHES,DS_USUARIO,DT_LOG)
    VALUES('RECOMEND_IA','Beneficiario ID:'||l_id_ben||' Nome:'||l_nome,:APP_USER,SYSTIMESTAMP);
    COMMIT;
  EXCEPTION WHEN OTHERS THEN NULL; END;

  APEX_JSON.OPEN_OBJECT;
  APEX_JSON.WRITE('status','success');
  APEX_JSON.WRITE('resultado', l_resultado);
  APEX_JSON.WRITE('beneficiario', l_nome);
  APEX_JSON.CLOSE_OBJECT;
EXCEPTION WHEN OTHERS THEN
  APEX_JSON.OPEN_OBJECT;
  APEX_JSON.WRITE('status','error');
  APEX_JSON.WRITE('mensagem','Erro: '||SQLERRM);
  APEX_JSON.CLOSE_OBJECT;
END;""".strip()

AJAX_SELECT_AI = """
DECLARE
  l_pergunta  VARCHAR2(4000) := APEX_APPLICATION.G_X01;
  l_sql_gerado CLOB;
  l_narrativa  CLOB;
BEGIN
  IF l_pergunta IS NULL THEN
    APEX_JSON.OPEN_OBJECT;
    APEX_JSON.WRITE('status','error');
    APEX_JSON.WRITE('mensagem','Digite uma pergunta.');
    APEX_JSON.CLOSE_OBJECT;
    RETURN;
  END IF;

  -- Gerar SQL
  BEGIN
    l_sql_gerado := DBMS_CLOUD_AI.GENERATE(
      prompt       => l_pergunta,
      profile_name => 'TEA_AI_PROFILE',
      action       => 'showsql'
    );
  EXCEPTION WHEN OTHERS THEN
    l_sql_gerado := '-- Nao foi possivel gerar SQL: '||SQLERRM;
  END;

  -- Gerar narrativa
  BEGIN
    l_narrativa := DBMS_CLOUD_AI.GENERATE(
      prompt       => l_pergunta,
      profile_name => 'TEA_AI_PROFILE',
      action       => 'narrate'
    );
  EXCEPTION WHEN OTHERS THEN
    l_narrativa := 'Erro ao gerar resposta: '||SQLERRM;
  END;

  BEGIN
    INSERT INTO TEA_LOG_AUDITORIA(DS_ACAO,DS_DETALHES,DS_USUARIO,DT_LOG)
    VALUES('SELECT_AI',SUBSTR(l_pergunta,1,4000),:APP_USER,SYSTIMESTAMP);
    COMMIT;
  EXCEPTION WHEN OTHERS THEN NULL; END;

  APEX_JSON.OPEN_OBJECT;
  APEX_JSON.WRITE('status','success');
  APEX_JSON.WRITE('sql_gerado', l_sql_gerado);
  APEX_JSON.WRITE('narrativa', l_narrativa);
  APEX_JSON.CLOSE_OBJECT;
EXCEPTION WHEN OTHERS THEN
  APEX_JSON.OPEN_OBJECT;
  APEX_JSON.WRITE('status','error');
  APEX_JSON.WRITE('mensagem','Erro: '||SQLERRM);
  APEX_JSON.CLOSE_OBJECT;
END;""".strip()

AJAX_RAG = """
DECLARE
  l_query    VARCHAR2(4000) := APEX_APPLICATION.G_X01;
  l_resultado CLOB;
  TYPE t_rec IS RECORD (titulo VARCHAR2(400), conteudo VARCHAR2(2000));
  TYPE t_tab IS TABLE OF t_rec;
  l_rows     t_tab;
BEGIN
  IF l_query IS NULL THEN
    APEX_JSON.OPEN_OBJECT;
    APEX_JSON.WRITE('status','error');
    APEX_JSON.WRITE('mensagem','Digite um termo de busca.');
    APEX_JSON.CLOSE_OBJECT;
    RETURN;
  END IF;

  -- Tentar PKG_TEA_VECTOR (busca vetorial)
  BEGIN
    EXECUTE IMMEDIATE
      'BEGIN :r := PKG_TEA_VECTOR.BUSCAR_SIMILAR(p_query=>:q, p_limit=>5); END;'
      USING OUT l_resultado, IN l_query;
  EXCEPTION WHEN OTHERS THEN
    -- Fallback: busca textual em TEA_CONHECIMENTO
    l_resultado := NULL;
  END;

  IF l_resultado IS NULL THEN
    BEGIN
      SELECT JSON_ARRAYAGG(
        JSON_OBJECT('titulo' VALUE SUBSTR(DS_TITULO,1,200), 'conteudo' VALUE SUBSTR(DS_CONTEUDO,1,500), 'score' VALUE 0.75)
        RETURNING CLOB
      )
      INTO l_resultado
      FROM (
        SELECT DS_TITULO, DS_CONTEUDO
          FROM TEA_CONHECIMENTO
         WHERE UPPER(DS_CONTEUDO||' '||DS_TITULO) LIKE '%'||UPPER(l_query)||'%'
         FETCH FIRST 5 ROWS ONLY
      );
    EXCEPTION WHEN OTHERS THEN
      l_resultado := '[]';
    END;
  END IF;

  BEGIN
    INSERT INTO TEA_LOG_AUDITORIA(DS_ACAO,DS_DETALHES,DS_USUARIO,DT_LOG)
    VALUES('RAG_BUSCA',SUBSTR(l_query,1,4000),:APP_USER,SYSTIMESTAMP);
    COMMIT;
  EXCEPTION WHEN OTHERS THEN NULL; END;

  APEX_JSON.OPEN_OBJECT;
  APEX_JSON.WRITE('status','success');
  APEX_JSON.WRITE_RAW('resultados', NVL(l_resultado,'[]'));
  APEX_JSON.CLOSE_OBJECT;
EXCEPTION WHEN OTHERS THEN
  APEX_JSON.OPEN_OBJECT;
  APEX_JSON.WRITE('status','error');
  APEX_JSON.WRITE('mensagem','Erro: '||SQLERRM);
  APEX_JSON.CLOSE_OBJECT;
END;""".strip()

# =============================================================================
# JavaScript — Chat
# =============================================================================
JS_CHAT = r"""
(function() {
  'use strict';

  window.iaSendChatMessage = function() {
    var ta = document.getElementById('chat-textarea');
    if (!ta) return;
    var msg = ta.value.trim();
    if (!msg) return;
    iaAppendMessage('user', msg.replace(/\n/g,'<br>'));
    ta.value = '';
    ta.style.height = 'auto';
    document.getElementById('typing-indicator').style.display = 'flex';

    apex.server.process('PROCESSAR_CHAT', { x01: msg }, {
      dataType: 'json',
      success: function(d) {
        document.getElementById('typing-indicator').style.display = 'none';
        if (d && d.status === 'success') {
          iaAppendMessage('assistant', iaFormat(d.resposta || ''));
        } else {
          iaAppendMessage('error', (d && d.mensagem) || 'Erro ao processar.');
        }
      },
      error: function() {
        document.getElementById('typing-indicator').style.display = 'none';
        iaAppendMessage('error', 'Erro de comunicacao com o servidor IA.');
      }
    });
  };

  window.iaQuickPrompt = function(text) {
    var ta = document.getElementById('chat-textarea');
    if (ta) { ta.value = text; iaSendChatMessage(); }
  };

  function iaAppendMessage(type, html) {
    var history = document.getElementById('chat-history');
    if (!history) return;
    var cssMap = {user:'chat-msg-user', assistant:'chat-msg-ai', error:'chat-msg-error'};
    var iconMap = {user:'fa-user', assistant:'fa-robot', error:'fa-warning'};
    var div = document.createElement('div');
    div.className = 'chat-message ' + (cssMap[type] || 'chat-msg-ai');
    var icon = document.createElement('span');
    icon.className = 'chat-icon fa ' + (iconMap[type] || 'fa-robot');
    var bubble = document.createElement('div');
    bubble.className = 'chat-bubble';
    bubble.innerHTML = html;
    div.appendChild(icon);
    div.appendChild(bubble);
    history.appendChild(div);
    history.scrollTop = history.scrollHeight;
  }

  function iaFormat(text) {
    return apex.util.escapeHTML(text)
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n\n+/g, '</p><p style="margin:8px 0 0">')
      .replace(/\n/g, '<br>');
  }

  // Auto-resize textarea
  apex.jQuery(document).on('input', '#chat-textarea', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
  });

  // Enter to send, Shift+Enter for newline
  apex.jQuery(document).on('keydown', '#chat-textarea', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      iaSendChatMessage();
    }
  });
})();
""".strip()

JS_SQL = r"""
(function() {
  'use strict';

  window.iaExecutarSQL = function() {
    var inp = document.getElementById('P40_PERGUNTA');
    if (!inp || !inp.value.trim()) return;
    var btn = document.getElementById('btn-exec-sql');
    if (btn) { btn.disabled = true; btn.textContent = 'Processando...'; }

    apex.server.process('EXECUTAR_SELECT_AI', { x01: inp.value.trim() }, {
      dataType: 'json',
      success: function(d) {
        if (btn) { btn.disabled = false; btn.textContent = 'Executar'; }
        if (d && d.status === 'success') {
          var sqlEl = document.getElementById('sql-generated-text');
          var narEl = document.getElementById('sql-narrative-text');
          var emp   = document.getElementById('sql-empty-state');
          var cont  = document.getElementById('sql-result-container');
          if (sqlEl) sqlEl.textContent = d.sql_gerado || '-- Sem SQL gerado';
          if (narEl) narEl.innerHTML = apex.util.escapeHTML(d.narrativa || '').replace(/\n/g,'<br>');
          if (emp)  emp.style.display  = 'none';
          if (cont) cont.style.display = 'block';
        } else {
          apex.message.showErrors([{type:'error', location:'inline', message:(d && d.mensagem)||'Erro ao executar.'}]);
        }
      },
      error: function() {
        if (btn) { btn.disabled = false; btn.textContent = 'Executar'; }
        apex.message.showErrors([{type:'error', location:'inline', message:'Erro de comunicacao.'}]);
      }
    });
  };

  apex.jQuery(document).on('keydown', '#P40_PERGUNTA', function(e) {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) iaExecutarSQL();
  });
})();
""".strip()

JS_RAG = r"""
(function() {
  'use strict';

  window.iaBuscarKB = function() {
    var inp = document.getElementById('P50_BUSCA');
    if (!inp || !inp.value.trim()) return;
    var btn = document.getElementById('btn-buscar-kb');
    if (btn) { btn.disabled = true; btn.textContent = 'Buscando...'; }

    apex.server.process('BUSCAR_CONHECIMENTO', { x01: inp.value.trim() }, {
      dataType: 'json',
      success: function(d) {
        if (btn) { btn.disabled = false; btn.textContent = 'Buscar'; }
        var container = document.getElementById('kb-resultados');
        if (!container) return;
        container.innerHTML = '';
        if (d && d.status === 'success' && d.resultados && d.resultados.length) {
          d.resultados.forEach(function(item) {
            var score = item.score ? Math.round(item.score * 100) : null;
            container.innerHTML +=
              '<div class="kb-card">' +
              '<h4>' + apex.util.escapeHTML(item.titulo || 'Sem título') + '</h4>' +
              '<p>' + apex.util.escapeHTML((item.conteudo || '').substring(0, 400)) + (item.conteudo && item.conteudo.length > 400 ? '...' : '') + '</p>' +
              (score ? '<span class="sim-badge">Similaridade: ' + score + '%</span>' : '') +
              '</div>';
          });
        } else {
          container.innerHTML = '<div class="kb-empty"><i class="fa fa-search"></i><p>Nenhum resultado encontrado para "' + apex.util.escapeHTML(inp.value) + '".<br>Tente termos diferentes ou verifique a base de conhecimento (TEA_CONHECIMENTO).</p></div>';
        }
      },
      error: function() {
        if (btn) { btn.disabled = false; btn.textContent = 'Buscar'; }
      }
    });
  };

  apex.jQuery(document).on('keydown', '#P50_BUSCA', function(e) {
    if (e.key === 'Enter') iaBuscarKB();
  });
})();
""".strip()

JS_ANALYSIS = r"""
(function() {
  'use strict';

  window.iaAnalisarAvaliacao = function() {
    var sel = apex.item('P20_ID_AVALIACAO');
    if (!sel || !sel.getValue()) {
      apex.message.showErrors([{type:'error',location:'inline',message:'Selecione uma avaliacao.'}]);
      return;
    }
    var btn = document.getElementById('btn-analisar');
    if (btn) { btn.disabled = true; btn.textContent = 'Analisando com IA...'; }
    var res = document.getElementById('analysis-result');
    if (res) res.innerHTML = '<div style="text-align:center;padding:40px;color:#888"><i class="fa fa-spinner fa-spin fa-2x"></i><br><br>Claude esta analisando...</div>';

    apex.server.process('ANALISAR_AVALIACAO_IA', { x01: sel.getValue() }, {
      dataType: 'json',
      success: function(d) {
        if (btn) { btn.disabled = false; btn.textContent = 'Analisar com IA'; }
        if (!res) return;
        if (d && d.status === 'success') {
          res.innerHTML =
            '<div class="analysis-card">' +
            '<div class="analysis-header">' +
            '<i class="fa fa-stethoscope"></i>' +
            '<div><div class="analysis-title">Analise Clinica — ' + apex.util.escapeHTML(d.beneficiario||'') + '</div>' +
            '<div class="analysis-sub">' + apex.util.escapeHTML(d.instrumento||'') + ' &nbsp;|&nbsp; Score: ' + (d.score||'?') + ' &nbsp;|&nbsp; ' + (d.percentual||'?') + '%</div></div>' +
            '</div>' +
            '<div class="analysis-body">' + apex.util.escapeHTML(d.resultado||'').replace(/\n/g,'<br>') + '</div>' +
            '</div>';
        } else {
          res.innerHTML = '<div class="ai-result-empty"><i class="fa fa-warning"></i><p>' + apex.util.escapeHTML((d&&d.mensagem)||'Erro ao analisar.') + '</p></div>';
        }
      },
      error: function() {
        if (btn) { btn.disabled = false; btn.textContent = 'Analisar com IA'; }
        if (res) res.innerHTML = '<div class="ai-result-empty"><i class="fa fa-warning"></i><p>Erro de comunicacao.</p></div>';
      }
    });
  };

  window.iaGerarRecomendacoes = function() {
    var sel = apex.item('P30_ID_BENEFICIARIO');
    if (!sel || !sel.getValue()) {
      apex.message.showErrors([{type:'error',location:'inline',message:'Selecione um beneficiario.'}]);
      return;
    }
    var btn = document.getElementById('btn-recomendar');
    if (btn) { btn.disabled = true; btn.textContent = 'Gerando com IA...'; }
    var res = document.getElementById('rec-result');
    if (res) res.innerHTML = '<div style="text-align:center;padding:40px;color:#888"><i class="fa fa-spinner fa-spin fa-2x"></i><br><br>Claude esta gerando recomendacoes...</div>';

    apex.server.process('GERAR_RECOMENDACOES_IA', { x01: sel.getValue() }, {
      dataType: 'json',
      success: function(d) {
        if (btn) { btn.disabled = false; btn.textContent = 'Gerar Recomendacoes'; }
        if (!res) return;
        if (d && d.status === 'success') {
          res.innerHTML =
            '<div class="analysis-card">' +
            '<div class="analysis-header">' +
            '<i class="fa fa-lightbulb-o" style="color:#43A047"></i>' +
            '<div><div class="analysis-title" style="color:#43A047">Recomendacoes Terapeuticas</div>' +
            '<div class="analysis-sub">' + apex.util.escapeHTML(d.beneficiario||'') + '</div></div>' +
            '</div>' +
            '<div class="analysis-body">' + apex.util.escapeHTML(d.resultado||'').replace(/\n/g,'<br>') + '</div>' +
            '</div>';
        } else {
          res.innerHTML = '<div class="ai-result-empty"><i class="fa fa-warning"></i><p>' + apex.util.escapeHTML((d&&d.mensagem)||'Erro.') + '</p></div>';
        }
      },
      error: function() {
        if (btn) { btn.disabled = false; btn.textContent = 'Gerar Recomendacoes'; }
      }
    });
  };
})();
""".strip()

# =============================================================================
# Helpers
# =============================================================================
def ok(label: str, result_str: str) -> tuple[bool, dict]:
    try:
        r = json.loads(result_str)
    except Exception:
        r = {"status": "error", "error": str(result_str)[:120]}
    if r.get("status") == "error":
        print(f"  ✗  {label}: {r.get('error', r.get('mensagem','?'))}")
        return False, r
    print(f"  ✓  {label}")
    return True, r


def section(title: str) -> None:
    print(f"\n{'─' * 62}")
    print(f"  {title}")
    print(f"{'─' * 62}")


def plsql_region(page_id: int, name: str, plsql: str, seq: int) -> None:
    ok(f"region({page_id},{name})", apex_add_region(
        page_id=page_id, region_name=name, region_type="plsql",
        sequence=seq, source_sql=plsql, template="0",
    ))


def static_region(page_id: int, name: str, plsql: str, seq: int) -> None:
    plsql_region(page_id, name, plsql, seq)


# =============================================================================
# BUILD
# =============================================================================
def run():
    t0 = time.perf_counter()

    print("\n" + "=" * 62)
    print(f"  {APP_NAME}")
    print(f"  App ID: {APP_ID}  |  9 páginas  |  Hub de IA completo")
    print(f"  PKG_CLAUDE_API + PKG_TEA_AI + SELECT AI + RAG vetorial")
    print("=" * 62)

    # ── [1] Conectar ─────────────────────────────────────────────────────────
    section("[1] Conexão Oracle ADB")
    if not ok("apex_connect", apex_connect())[0]:
        return

    # ── [2] Limpar app anterior ──────────────────────────────────────────────
    section("[2] Limpar workspace")
    apps_raw = json.loads(apex_list_apps())
    existing_ids = {a.get("APPLICATION_ID") for a in (apps_raw.get("data") or [])}
    if APP_ID in existing_ids:
        ok(f"apex_delete_app({APP_ID})", apex_delete_app(APP_ID))
    else:
        print(f"  ->  App {APP_ID} não existe, criando do zero")

    # ── [3] Criar app + CSS global ────────────────────────────────────────────
    section("[3] Criar app + CSS global (Unimed + IA Hub)")
    if not ok(f"apex_create_app({APP_ID})", apex_create_app(APP_ID, APP_NAME, home_page=1))[0]:
        return
    ok("apex_add_global_css", apex_add_global_css(UNIMED_THEME_CSS + "\n\n" + APP_EXTRA_CSS))

    # ── [4] Login — pág. 100 ─────────────────────────────────────────────────
    section("[4] Login — página 100")
    ok("apex_generate_login(100)", apex_generate_login(100))

    # ── [5] LOVs compartilhadas ──────────────────────────────────────────────
    section("[5] LOVs — Avaliacoes e Beneficiarios")
    ok("lov_avaliacoes", apex_add_lov(
        lov_name="LOV_AVALIACOES_IA",
        lov_type="sql",
        sql_query="""SELECT b.DS_NOME || ' - ' || p.DS_NOME || ' - ' || TO_CHAR(a.DT_AVALIACAO,'DD/MM/YYYY') || ' - Score:'|| a.NR_SCORE_TOTAL D,
                            a.ID_AVALIACAO R
                       FROM TEA_AVALIACOES a
                       JOIN TEA_BENEFICIARIOS b ON b.ID_BENEFICIARIO = a.ID_BENEFICIARIO
                       JOIN TEA_PROVAS p ON p.ID_PROVA = a.ID_PROVA
                      WHERE a.DS_STATUS = 'CONCLUIDA'
                      ORDER BY a.DT_AVALIACAO DESC""",
    ))
    ok("lov_beneficiarios", apex_add_lov(
        lov_name="LOV_BENEFICIARIOS_IA",
        lov_type="sql",
        sql_query="""SELECT DS_NOME || ' (' || NR_BENEFICIO || ')' D, ID_BENEFICIARIO R
                       FROM TEA_BENEFICIARIOS ORDER BY DS_NOME""",
    ))

    # ── [6] Dashboard IA — pág. 1 ────────────────────────────────────────────
    section("[6] Dashboard IA — página 1")
    ok("apex_generate_analytics_page(1)", apex_generate_analytics_page(
        page_id=1,
        page_name="Dashboard IA",
        metrics=[
            {"label": "Interacoes IA",    "sql": "SELECT COUNT(*) FROM TEA_LOG_AUDITORIA WHERE DS_ACAO LIKE '%IA%'", "icon": "fa-robot",       "color": "#00995D"},
            {"label": "Chat Sessions",     "sql": "SELECT COUNT(*) FROM TEA_LOG_AUDITORIA WHERE DS_ACAO = 'CHAT_IA'", "icon": "fa-comments",    "color": "#1E88E5"},
            {"label": "Analises Clinicas", "sql": "SELECT COUNT(*) FROM TEA_LOG_AUDITORIA WHERE DS_ACAO = 'ANALISE_IA'", "icon": "fa-stethoscope","color": "#43A047"},
            {"label": "Docs na KB",        "sql": "SELECT COUNT(*) FROM TEA_CONHECIMENTO", "icon": "fa-book",        "color": "#8E24AA"},
        ],
        charts=[
            {
                "title": "Atividade IA - 30 dias",
                "type":  "bar",
                "sql":   """SELECT TO_CHAR(TRUNC(DT_LOG),'DD/MM') AS "Dia",
                                   COUNT(*) AS "Interacoes"
                              FROM TEA_LOG_AUDITORIA
                             WHERE DT_LOG >= SYSDATE - 30
                               AND DS_ACAO LIKE '%IA%'
                             GROUP BY TRUNC(DT_LOG)
                             ORDER BY TRUNC(DT_LOG)""",
            },
            {
                "title": "Tipos de Interacao",
                "type":  "donut",
                "sql":   """SELECT REPLACE(DS_ACAO,'_IA','') AS "Tipo",
                                   COUNT(*) AS "Qtd"
                              FROM TEA_LOG_AUDITORIA
                             WHERE DS_ACAO LIKE '%IA%'
                             GROUP BY DS_ACAO
                             ORDER BY COUNT(*) DESC""",
            },
        ],
    ))
    ok("tiles_dashboard", apex_add_region(
        page_id=1, region_name="Funcionalidades IA", region_type="plsql",
        sequence=50, source_sql=DASHBOARD_TILES, template="0",
    ))

    # ── [7] Chat com Claude — pág. 10 ─────────────────────────────────────────
    section("[7] Chat com Claude — página 10")
    ok("apex_add_page(10)", apex_add_page(page_id=10, page_name="Chat com Claude"))
    plsql_region(10, "Chat Header", ia_banner("fa-comments","Chat com Claude","Assistente IA especializado em TEA - powered by Claude Sonnet","ia-header-chat"), 5)
    ok("region_chat_html", apex_add_region(
        page_id=10, region_name="Assistente Claude", region_type="plsql",
        sequence=10, source_sql=CHAT_HTML, template="0",
    ))
    ok("process_chat(ON_DEMAND)", apex_add_process(
        page_id=10, process_name="PROCESSAR_CHAT",
        process_type="plsql", point="ON_DEMAND",
        source=AJAX_CHAT, sequence=10,
    ))
    ok("apex_add_page_js(10)", apex_add_page_js(10, JS_CHAT))

    # ── [8] Análise Clínica IA — pág. 20 ──────────────────────────────────────
    section("[8] Análise Clínica IA — página 20")
    ok("apex_add_page(20)", apex_add_page(page_id=20, page_name="Analise Clinica IA"))
    plsql_region(20, "Analysis Header", ia_banner("fa-stethoscope","Analise Clinica com IA","Selecione uma avaliacao para gerar interpretacao clinica detalhada","ia-header-analysis"), 5)
    ok("region_analysis_form", apex_add_region(
        page_id=20, region_name="Selecionar Avaliacao", region_type="static", sequence=10,
    ))
    ok("item_P20_ID_AVALIACAO", apex_add_item(
        page_id=20, region_name="Selecionar Avaliacao",
        item_name="P20_ID_AVALIACAO", item_type="select",
        label="Avaliacao TEA (Concluida)", sequence=10, lov_name="LOV_AVALIACOES_IA",
    ))
    ok("button_analisar", apex_add_button(
        page_id=20, region_name="Selecionar Avaliacao",
        button_name="ANALISAR_IA", label="Analisar com IA",
        action="da", hot=True, sequence=10,
    ))
    ok("da_analisar", apex_add_dynamic_action(
        page_id=20, da_name="DA Analisar IA", event="click",
        trigger_element="ANALISAR_IA",
        action_type="execute_javascript",
        javascript_code="iaAnalisarAvaliacao();",
        sequence=10,
    ))
    ok("region_analysis_result", apex_add_region(
        page_id=20, region_name="Resultado da Analise IA",
        region_type="plsql", sequence=20, source_sql=ANALYSIS_HTML, template="0",
    ))
    ok("process_analysis(ON_DEMAND)", apex_add_process(
        page_id=20, process_name="ANALISAR_AVALIACAO_IA",
        process_type="plsql", point="ON_DEMAND",
        source=AJAX_ANALYSIS, sequence=10,
    ))
    ok("apex_add_page_js(20)", apex_add_page_js(20, JS_ANALYSIS))

    # ── [9] Recomendações Terapêuticas — pág. 30 ──────────────────────────────
    section("[9] Recomendações Terapêuticas — página 30")
    ok("apex_add_page(30)", apex_add_page(page_id=30, page_name="Recomendacoes Terapeuticas"))
    plsql_region(30, "Rec Header", ia_banner("fa-lightbulb-o","Recomendacoes Terapeuticas","Gere planos de intervencao personalizados baseados no historico clinico","ia-header-rec"), 5)
    ok("region_rec_form", apex_add_region(
        page_id=30, region_name="Selecionar Paciente", region_type="static", sequence=10,
    ))
    ok("item_P30_ID_BENEFICIARIO", apex_add_item(
        page_id=30, region_name="Selecionar Paciente",
        item_name="P30_ID_BENEFICIARIO", item_type="select",
        label="Beneficiario", sequence=10, lov_name="LOV_BENEFICIARIOS_IA",
    ))
    ok("button_recomendar", apex_add_button(
        page_id=30, region_name="Selecionar Paciente",
        button_name="RECOMENDAR_IA", label="Gerar Recomendacoes",
        action="da", hot=True, sequence=10,
    ))
    ok("da_recomendar", apex_add_dynamic_action(
        page_id=30, da_name="DA Recomendar IA", event="click",
        trigger_element="RECOMENDAR_IA",
        action_type="execute_javascript",
        javascript_code="iaGerarRecomendacoes();",
        sequence=10,
    ))
    ok("region_rec_result", apex_add_region(
        page_id=30, region_name="Recomendacoes IA",
        region_type="plsql", sequence=20, source_sql=REC_HTML, template="0",
    ))
    ok("process_rec(ON_DEMAND)", apex_add_process(
        page_id=30, process_name="GERAR_RECOMENDACOES_IA",
        process_type="plsql", point="ON_DEMAND",
        source=AJAX_RECOMMENDATIONS, sequence=10,
    ))
    ok("apex_add_page_js(30)", apex_add_page_js(30, JS_ANALYSIS))

    # ── [10] SQL Intelligence — pág. 40 ───────────────────────────────────────
    section("[10] SQL Intelligence — página 40")
    ok("apex_add_page(40)", apex_add_page(page_id=40, page_name="SQL Intelligence"))
    plsql_region(40, "SQL Header", ia_banner("fa-database","SQL Intelligence","Faca perguntas em portugues e a IA gera o SQL automaticamente (SELECT AI)","ia-header-sql"), 5)
    ok("region_sql_input", apex_add_region(
        page_id=40, region_name="Sua Pergunta", region_type="static", sequence=10,
    ))
    ok("item_P40_PERGUNTA", apex_add_item(
        page_id=40, region_name="Sua Pergunta",
        item_name="P40_PERGUNTA", item_type="text",
        label="Pergunta em Linguagem Natural",
        sequence=10, placeholder="Ex: Quantos beneficiarios existem por clinica?",
    ))
    ok("button_exec_sql", apex_add_button(
        page_id=40, region_name="Sua Pergunta",
        button_name="EXEC_SQL", label="Executar",
        action="da", hot=True, sequence=10,
    ))
    ok("da_exec_sql", apex_add_dynamic_action(
        page_id=40, da_name="DA Exec SQL", event="click",
        trigger_element="EXEC_SQL",
        action_type="execute_javascript",
        javascript_code="iaExecutarSQL();",
        sequence=10,
    ))
    ok("region_sql_result", apex_add_region(
        page_id=40, region_name="Resultado SQL", region_type="plsql",
        sequence=20, source_sql=SQL_INTEL_HTML, template="0",
    ))
    ok("process_sql(ON_DEMAND)", apex_add_process(
        page_id=40, process_name="EXECUTAR_SELECT_AI",
        process_type="plsql", point="ON_DEMAND",
        source=AJAX_SELECT_AI, sequence=10,
    ))
    ok("apex_add_page_js(40)", apex_add_page_js(40, JS_SQL))

    # ── [11] Base de Conhecimento RAG — pág. 50 ───────────────────────────────
    section("[11] Base de Conhecimento RAG — página 50")
    ok("apex_add_page(50)", apex_add_page(page_id=50, page_name="Base de Conhecimento"))
    plsql_region(50, "KB Header", ia_banner("fa-search","Base de Conhecimento RAG","Busca vetorial com PKG_TEA_VECTOR - encontre informacoes relevantes sobre TEA","ia-header-rag"), 5)
    ok("region_kb_search", apex_add_region(
        page_id=50, region_name="Busca RAG", region_type="static", sequence=10,
    ))
    ok("item_P50_BUSCA", apex_add_item(
        page_id=50, region_name="Busca RAG",
        item_name="P50_BUSCA", item_type="text",
        label="Buscar na Base de Conhecimento",
        sequence=10, placeholder="Ex: instrumentos VINELAND, comportamento repetitivo, ABA...",
    ))
    ok("button_buscar_kb", apex_add_button(
        page_id=50, region_name="Busca RAG",
        button_name="BUSCAR_KB", label="Buscar",
        action="da", hot=True, sequence=10,
    ))
    ok("da_buscar_kb", apex_add_dynamic_action(
        page_id=50, da_name="DA Buscar KB", event="click",
        trigger_element="BUSCAR_KB",
        action_type="execute_javascript",
        javascript_code="iaBuscarKB();",
        sequence=10,
    ))
    ok("region_kb_results", apex_add_region(
        page_id=50, region_name="Resultados da Busca", region_type="plsql",
        sequence=20, source_sql=KB_HTML, template="0",
    ))
    ok("process_rag(ON_DEMAND)", apex_add_process(
        page_id=50, process_name="BUSCAR_CONHECIMENTO",
        process_type="plsql", point="ON_DEMAND",
        source=AJAX_RAG, sequence=10,
    ))
    ok("apex_add_page_js(50)", apex_add_page_js(50, JS_RAG))

    # ── [12] Log de Interações IA — pág. 60 ───────────────────────────────────
    section("[12] Log de Interações IA — página 60")
    ok("apex_add_page(60)", apex_add_page(page_id=60, page_name="Log de Interacoes IA"))
    plsql_region(60, "Log Header", ia_banner("fa-history","Log de Interacoes IA","Audit trail de todas as chamadas aos motores de inteligencia artificial","ia-header-log"), 5)
    ok("metric_cards_log", apex_add_metric_cards(
        page_id=60, region_name="Resumo de Uso IA",
        sequence=10, columns=4, style="gradient",
        metrics=[
            {"label": "Total Interacoes",  "sql": "SELECT COUNT(*) FROM TEA_LOG_AUDITORIA WHERE DS_ACAO LIKE '%IA%'", "icon": "fa-bolt",      "color": "#00995D"},
            {"label": "Chats",             "sql": "SELECT COUNT(*) FROM TEA_LOG_AUDITORIA WHERE DS_ACAO = 'CHAT_IA'", "icon": "fa-comments",  "color": "#1E88E5"},
            {"label": "SQL Intelligence",  "sql": "SELECT COUNT(*) FROM TEA_LOG_AUDITORIA WHERE DS_ACAO = 'SELECT_AI'","icon": "fa-database",  "color": "#FB8C00"},
            {"label": "Busca RAG",         "sql": "SELECT COUNT(*) FROM TEA_LOG_AUDITORIA WHERE DS_ACAO = 'RAG_BUSCA'","icon": "fa-search",    "color": "#8E24AA"},
        ],
    ))
    ok("region_log_ir", apex_add_region(
        page_id=60, region_name="Historico de Interacoes",
        region_type="ir", sequence=20,
        source_sql="""SELECT
  DS_ACAO                                  AS "Acao",
  DS_USUARIO                               AS "Usuario",
  TO_CHAR(DT_LOG,'DD/MM/YYYY HH24:MI:SS')  AS "Data/Hora",
  SUBSTR(DS_DETALHES, 1, 200)              AS "Detalhes"
FROM TEA_LOG_AUDITORIA
WHERE DS_ACAO IN ('CHAT_IA','ANALISE_IA','RECOMEND_IA','SELECT_AI','RAG_BUSCA')
   OR DS_ACAO LIKE '%IA%'
ORDER BY DT_LOG DESC""",
    ))

    # ── [13] Configurações IA — pág. 70 ───────────────────────────────────────
    section("[13] Configurações IA — página 70")
    ok("apex_add_page(70)", apex_add_page(page_id=70, page_name="Configuracoes IA"))
    plsql_region(70, "Config Header", ia_banner("fa-cog","Configuracoes IA","Status dos motores de IA, credenciais e parametros do sistema","ia-header-config"), 5)
    ok("region_config", apex_add_region(
        page_id=70, region_name="Status e Configuracoes",
        region_type="plsql", sequence=10, source_sql=CONFIG_PLSQL,
    ))
    ok("chart_ia_by_day", apex_add_jet_chart(
        page_id=70, region_name="Uso IA - Ultimos 7 dias",
        chart_type="bar", sequence=20,
        sql_query="""SELECT TO_CHAR(TRUNC(DT_LOG),'DD/MM') AS "Dia",
                      COUNT(*) AS "Interacoes"
                 FROM TEA_LOG_AUDITORIA
                WHERE DT_LOG >= SYSDATE - 7
                  AND (DS_ACAO LIKE '%IA%' OR DS_ACAO = 'SELECT_AI' OR DS_ACAO = 'RAG_BUSCA')
                GROUP BY TRUNC(DT_LOG)
                ORDER BY TRUNC(DT_LOG)""",
        label_column="Dia", value_column="Interacoes",
    ))

    # ── [14] Navegação — menu lateral ─────────────────────────────────────────
    section("[14] Navegação — menu lateral")
    nav_items = [
        ("Dashboard IA",       1,  "fa-tachometer", 10),
        ("Chat com Claude",    10, "fa-comments",   20),
        ("Analise Clinica",    20, "fa-stethoscope",30),
        ("Recomendacoes",      30, "fa-lightbulb-o",40),
        ("SQL Intelligence",   40, "fa-database",   50),
        ("Base Conhecimento",  50, "fa-search",     60),
        ("Log de Interacoes",  60, "fa-history",    70),
        ("Configuracoes IA",   70, "fa-cog",        80),
    ]
    for item_name, pg, icon, seq in nav_items:
        ok(f"nav({item_name})", apex_add_nav_item(
            item_name=item_name, target_page=pg, sequence=seq, icon=icon,
        ))

    # ── [15] Finalizar ────────────────────────────────────────────────────────
    section("[15] Finalizar app")
    ok("apex_finalize_app", apex_finalize_app())

    # ── [16] Validar ──────────────────────────────────────────────────────────
    section("[16] Validar app")
    ok("apex_validate_app", apex_validate_app(APP_ID))

    # ── Resumo ────────────────────────────────────────────────────────────────
    elapsed = time.perf_counter() - t0
    print(f"\n{'=' * 62}")
    print(f"  App {APP_ID} — {APP_NAME}")
    print(f"  Construido em {elapsed:.1f}s")
    print(f"\n  Paginas (9):")
    print(f"    100 -> Login")
    print(f"      1 -> Dashboard IA (metricas + graficos + tiles de features)")
    print(f"     10 -> Chat com Claude (chat interativo + quick prompts)")
    print(f"     20 -> Analise Clinica IA (PKG_CLAUDE_API.ANALISAR_AVALIACAO)")
    print(f"     30 -> Recomendacoes Terapeuticas (PKG_CLAUDE_API.RECOMENDAR_TERAPIA)")
    print(f"     40 -> SQL Intelligence (SELECT AI / DBMS_CLOUD_AI)")
    print(f"     50 -> Base de Conhecimento RAG (PKG_TEA_VECTOR)")
    print(f"     60 -> Log de Interacoes IA (audit trail)")
    print(f"     70 -> Configuracoes IA (status pkgs + chart)")
    print(f"\n  URL: https://u5cvlivnjuodscai-u5cvlivnjuodscai.adb.sa-saopaulo-1.oraclecloudapps.com/ords/r/tea/{APP_ID}")
    print(f"  Login: cnu.admin / Unimed@2024")
    print("=" * 62)


if __name__ == "__main__":
    run()
