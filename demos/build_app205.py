"""Plataforma TEA — App 205 Completo.

Cria do zero um app APEX 24.2 completo para a Plataforma de Desfecho TEA
com tema Unimed (#00995D), todas as telas e navegação estruturada.

Páginas geradas:
  100 → Login (customizado)
    1 → Dashboard (métricas KPI + 2 gráficos JET)
   10 → Beneficiários — lista (Interactive Report)
   11 → Beneficiário — formulário (Create/Edit)
   20 → Clínicas — lista (IR)
   21 → Clínica — formulário
   30 → Terapeutas — lista (IR)
   31 → Terapeuta — formulário
   50 → Nova Avaliação — Etapa 1 (dados gerais)
   51 → Nova Avaliação — Etapa 2 (Comunicação — 5 Likert)
   52 → Nova Avaliação — Etapa 3 (Socialização — 5 Likert)
   53 → Nova Avaliação — Etapa 4 (Habilidades — 5 Likert)
   54 → Score Final (círculo SVG animado + métricas + IR)
   60 → Histórico de Avaliações (IR completo)
"""
import os, sys, json, time, textwrap

# Force UTF-8 output on Windows (avoids cp1252 UnicodeEncodeError)
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

from apex_mcp.tools.sql_tools       import apex_connect
from apex_mcp.tools.app_tools       import (
    apex_list_apps, apex_create_app, apex_finalize_app, apex_delete_app,
)
from apex_mcp.tools.page_tools      import apex_add_page
from apex_mcp.tools.component_tools import apex_add_region, apex_add_item, apex_add_process
from apex_mcp.tools.shared_tools    import apex_add_app_item, apex_add_nav_item
from apex_mcp.tools.generator_tools import apex_generate_login, apex_generate_crud
from apex_mcp.tools.advanced_tools  import (
    apex_generate_wizard, apex_add_global_css, apex_generate_report_page,
)
from apex_mcp.tools.visual_tools    import (
    apex_add_metric_cards, apex_generate_analytics_page,
)
from apex_mcp.tools.js_tools        import apex_add_page_js
from apex_mcp.themes                import UNIMED_THEME_CSS

# ── Configuração ──────────────────────────────────────────────────────────────
APP_ID   = 205
APP_NAME = "Plataforma TEA — Desfecho Clínico"

# Escala Likert (SELECT_LIST → convertida em botões visuais via JS)
LIKERT = (
    "SELECT '0 - Nunca'         D,'0' R FROM DUAL UNION ALL "
    "SELECT '1 - Raramente'     D,'1' R FROM DUAL UNION ALL "
    "SELECT '2 - As vezes'      D,'2' R FROM DUAL UNION ALL "
    "SELECT '3 - Sempre'        D,'3' R FROM DUAL"
)

# =============================================================================
# CSS EXTRA (Likert buttons + Score hero + Wizard intro + Action bar)
# Complementa UNIMED_THEME_CSS aplicado globalmente
# =============================================================================
APP_EXTRA_CSS = """
/* ── Wizard intro banner ───────────────────────────────────────────────── */
.tea-wizard-header{
  display:flex;align-items:center;gap:16px;
  background:linear-gradient(135deg,#00995D,#006B3F);
  padding:16px 20px;border-radius:10px;color:#fff;margin-bottom:14px;
  box-shadow:0 3px 12px rgba(0,107,63,.3)
}
.tea-wizard-header .fa{font-size:2.2rem;flex-shrink:0;opacity:.9}
.tea-wizard-header-title{font-size:1rem;font-weight:700;margin-bottom:3px}
.tea-wizard-header-sub{font-size:.82rem;opacity:.85;line-height:1.4}

/* ── Wizard Likert step intro ───────────────────────────────────────────── */
.tea-step-intro{
  background:linear-gradient(90deg,#f0faf5,#fff);
  border-left:4px solid #00995D;border-radius:8px;
  padding:12px 16px;margin-bottom:14px;
  display:flex;align-items:center;gap:12px
}
.tea-step-intro .fa{color:#00995D;font-size:1.6rem}
.tea-step-intro-title{font-weight:700;color:#006B3F;font-size:.95rem;margin-bottom:2px}
.tea-step-intro-sub{font-size:.82rem;color:#666}

/* ── Likert buttons ─────────────────────────────────────────────────────── */
.tea-hidden-select{display:none!important}
.tea-likert-group{display:flex;gap:8px;flex-wrap:wrap;margin:6px 0 4px}
.tea-likert-btn{
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  min-width:76px;padding:10px 6px;
  border:2px solid #dde3e9;border-radius:10px;
  background:#fff;cursor:pointer;
  transition:all .2s ease;font-family:inherit
}
.tea-likert-btn:hover{
  border-width:3px;transform:translateY(-2px);
  box-shadow:0 4px 14px rgba(0,0,0,.15)
}
.tea-likert-btn.is-active{
  color:#fff!important;border-width:2px;
  box-shadow:0 4px 16px rgba(0,0,0,.25);transform:translateY(-2px)
}
.tea-likert-score{font-size:22px;font-weight:800;margin-bottom:4px}
.tea-likert-label{font-size:11px;font-weight:600;text-align:center;white-space:nowrap}

/* ── Score page ─────────────────────────────────────────────────────────── */
.tea-score-hero{
  display:flex;align-items:center;gap:48px;flex-wrap:wrap;
  padding:36px 32px;
  background:linear-gradient(135deg,#f0faf5 0%,#fff 60%);
  border-radius:16px;border-left:5px solid #00995D;
  box-shadow:0 4px 20px rgba(0,0,0,.07)
}
.tea-score-circle-wrap{position:relative;width:160px;height:160px;flex-shrink:0}
.tea-score-svg{width:160px;height:160px}
.tea-score-arc{transition:stroke-dasharray 1.6s cubic-bezier(.4,0,.2,1)}
.tea-score-center{
  position:absolute;top:50%;left:50%;
  transform:translate(-50%,-50%);text-align:center;pointer-events:none
}
.tea-score-number{display:block;font-size:42px;font-weight:800;color:#1a1a2e;line-height:1}
.tea-score-max{display:block;font-size:13px;color:#888;margin-top:4px}
.tea-score-info{flex:1;min-width:200px}
.tea-score-name{font-size:22px;font-weight:700;color:#1a1a2e;margin:0 0 8px;line-height:1.3}
.tea-score-pct{font-size:52px;font-weight:800;line-height:1;margin:0 0 14px}
.tea-score-badge{
  display:inline-block;padding:6px 22px;border-radius:20px;
  color:#fff;font-weight:700;font-size:14px;letter-spacing:.5px;margin-bottom:14px
}
.tea-score-hint{font-size:13px;color:#888;margin:10px 0 0}
.tea-score-empty{padding:60px 40px;text-align:center;color:#888;font-size:16px}
.tea-score-empty i{display:block;margin-bottom:16px;color:#1E88E5;font-size:52px}

/* ── Score action buttons ───────────────────────────────────────────────── */
.tea-score-actions{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:20px;align-items:center}
.tea-score-actions .t-Button{text-decoration:none}
""".strip()

# =============================================================================
# JavaScript
# =============================================================================

# Página 50 — preenche data padrão = hoje
JS_P50 = r"""
(function($) {
  apex.jQuery(document).on('apexreadyend', function() {
    if (!apex.item('P50_DT_AVALIACAO').getValue()) {
      var d = new Date();
      var dd = String(d.getDate()).padStart(2,'0');
      var mm = String(d.getMonth()+1).padStart(2,'0');
      apex.item('P50_DT_AVALIACAO').setValue(dd+'/'+mm+'/'+d.getFullYear());
    }
  });
})(apex.jQuery);
""".strip()

# Página 54 — anima arco SVG
JS_P54 = r"""
(function($) {
  apex.jQuery(document).on('apexreadyend', function() {
    var $arc = $('.tea-score-arc');
    if (!$arc.length) return;
    var target = parseInt($arc.attr('data-arc') || '0', 10);
    setTimeout(function() {
      $arc.css('stroke-dasharray', target + ' 314');
    }, 400);
  });
})(apex.jQuery);
""".strip()


def make_likert_js(question_ids: list[str]) -> str:
    """Gera JS que converte SELECT_LIST em grupos de botões Likert visuais."""
    items_json = json.dumps(question_ids)
    return textwrap.dedent(f"""
    (function($) {{
      var cfg = [
        {{val:'0', label:'Nunca',     color:'#E53935'}},
        {{val:'1', label:'Raramente', color:'#FF9800'}},
        {{val:'2', label:'As vezes',  color:'#1E88E5'}},
        {{val:'3', label:'Sempre',    color:'#00995D'}}
      ];
      var items = {items_json};

      function activateBtn(id, val) {{
        var c = cfg[parseInt(val,10)] || {{}};
        var $g = $('#grp_'+id);
        $g.find('.tea-likert-btn')
          .removeClass('is-active')
          .css({{background:'#fff','border-color':'#dde3e9',color:''}});
        $g.find('.tea-likert-btn[data-value="'+val+'"]')
          .addClass('is-active')
          .css({{background:c.color||'','border-color':c.color||'',color:'#fff'}});
      }}

      function buildLikert() {{
        items.forEach(function(id) {{
          var $sel = $('#'+id);
          if (!$sel.length) return;
          $sel.addClass('tea-hidden-select');
          var html = '<div class="tea-likert-group" id="grp_'+id+'">';
          cfg.forEach(function(c) {{
            html +=
              '<button type="button" class="tea-likert-btn" ' +
              'data-item="'+id+'" data-value="'+c.val+'">' +
              '<span class="tea-likert-score" style="color:'+c.color+'">'+c.val+'</span>' +
              '<span class="tea-likert-label">'+c.label+'</span>' +
              '</button>';
          }});
          html += '</div>';
          $sel.after(html);
          var cur = apex.item(id).getValue();
          if (cur !== '') activateBtn(id, cur);
        }});

        $(document).off('click.likert').on('click.likert', '.tea-likert-btn', function() {{
          var id  = $(this).data('item').toString();
          var val = $(this).data('value').toString();
          apex.item(id).setValue(val);
          activateBtn(id, val);
        }});
      }}

      apex.jQuery(document).on('apexreadyend', buildLikert);
    }})(apex.jQuery);
    """).strip()


# =============================================================================
# PL/SQL
# =============================================================================

# Banner intro do wizard (pág. 50)
INTRO_P50 = """
BEGIN
  sys.htp.p('<div class="tea-wizard-header">');
  sys.htp.p('<i class="fa fa-clipboard-check" aria-hidden="true"></i>');
  sys.htp.p('<div>');
  sys.htp.p('<div class="tea-wizard-header-title">Avalia&ccedil;&atilde;o TEA &mdash; Protocolo ICHOM</div>');
  sys.htp.p('<div class="tea-wizard-header-sub">Instrumento padronizado ICHOM para acompanhamento do desfecho cl&iacute;nico. Preencha os dados e avance pelas 4 etapas.</div>');
  sys.htp.p('</div></div>');
END;
""".strip()

# Banner intro etapa 2 — Comunicação
INTRO_P51 = """
BEGIN
  sys.htp.p('<div class="tea-step-intro">');
  sys.htp.p('<i class="fa fa-comments" aria-hidden="true"></i>');
  sys.htp.p('<div><div class="tea-step-intro-title">Dom&iacute;nio: Comunica&ccedil;&atilde;o</div>');
  sys.htp.p('<div class="tea-step-intro-sub">Avalie a frequ&ecirc;ncia dos comportamentos comunicativos nos &uacute;ltimos 30 dias.</div></div>');
  sys.htp.p('</div>');
END;
""".strip()

# Banner intro etapa 3 — Socialização
INTRO_P52 = """
BEGIN
  sys.htp.p('<div class="tea-step-intro">');
  sys.htp.p('<i class="fa fa-users" aria-hidden="true"></i>');
  sys.htp.p('<div><div class="tea-step-intro-title">Dom&iacute;nio: Socializa&ccedil;&atilde;o</div>');
  sys.htp.p('<div class="tea-step-intro-sub">Avalie a intera&ccedil;&atilde;o social e o relacionamento com outras pessoas.</div></div>');
  sys.htp.p('</div>');
END;
""".strip()

# Banner intro etapa 4 — Habilidades
INTRO_P53 = """
BEGIN
  sys.htp.p('<div class="tea-step-intro">');
  sys.htp.p('<i class="fa fa-star" aria-hidden="true"></i>');
  sys.htp.p('<div><div class="tea-step-intro-title">Dom&iacute;nio: Habilidades da Vida Di&aacute;ria</div>');
  sys.htp.p('<div class="tea-step-intro-sub">Avalie a autonomia e independ&ecirc;ncia nas atividades cotidianas.</div></div>');
  sys.htp.p('</div>');
END;
""".strip()

# Botões de ação da página de score (pág. 54)
ACTIONS_P54 = """
DECLARE
  l_nova VARCHAR2(300);
  l_hist VARCHAR2(300);
BEGIN
  l_nova := 'f?p=' || :APP_ID || ':50:' || :APP_SESSION || '::NO::';
  l_hist := 'f?p=' || :APP_ID || ':60:' || :APP_SESSION || '::NO::';
  sys.htp.p('<div class="tea-score-actions">');
  sys.htp.p('<a href="' || l_nova || '" class="t-Button t-Button--hot t-Button--iconLeft">');
  sys.htp.p('<span class="t-Icon fa fa-plus" aria-hidden="true"></span>Nova Avalia&ccedil;&atilde;o</a>');
  sys.htp.p('<a href="' || l_hist || '" class="t-Button t-Button--iconLeft">');
  sys.htp.p('<span class="t-Icon fa fa-list" aria-hidden="true"></span>Hist&oacute;rico</a>');
  sys.htp.p('</div>');
END;
""".strip()

# Círculo de score animado (pág. 54)
SCORE_PLSQL = """
DECLARE
  v_score  NUMBER;
  v_pct    NUMBER;
  v_nome   VARCHAR2(200);
  v_nivel  VARCHAR2(60);
  v_color  VARCHAR2(20);
  v_arc    NUMBER;
BEGIN
  IF :P54_ID_AVALIACAO IS NULL OR :P54_ID_AVALIACAO = '' THEN
    sys.htp.p('<div class="tea-score-empty"><i class="fa fa-chart-bar"></i>');
    sys.htp.p('<p>Conclua uma avalia&ccedil;&atilde;o para ver o resultado aqui.</p></div>');
    RETURN;
  END IF;

  BEGIN
    SELECT a.NR_SCORE_TOTAL, a.NR_PCT_TOTAL, b.DS_NOME
      INTO v_score, v_pct, v_nome
      FROM TEA_AVALIACOES a
      JOIN TEA_BENEFICIARIOS b ON b.ID_BENEFICIARIO = a.ID_BENEFICIARIO
     WHERE a.ID_AVALIACAO = TO_NUMBER(:P54_ID_AVALIACAO);
  EXCEPTION
    WHEN NO_DATA_FOUND THEN
      sys.htp.p('<p>Avalia&ccedil;&atilde;o n&atilde;o encontrada.</p>');
      RETURN;
  END;

  v_nivel := CASE
    WHEN v_pct >= 75 THEN 'Alto Desenvolvimento'
    WHEN v_pct >= 50 THEN 'M&eacute;dio Desenvolvimento'
    ELSE                   'Baixo Desenvolvimento'
  END;
  v_color := CASE
    WHEN v_pct >= 75 THEN '#00995D'
    WHEN v_pct >= 50 THEN '#FF9800'
    ELSE                   '#E53935'
  END;
  v_arc := ROUND(v_pct / 100 * 314, 0);

  sys.htp.p(
    '<div class="tea-score-hero">' ||
    '<div class="tea-score-circle-wrap">' ||
    '<svg viewBox="0 0 120 120" class="tea-score-svg">' ||
    '<circle cx="60" cy="60" r="50" fill="none" stroke="#eee" stroke-width="10"/>' ||
    '<circle cx="60" cy="60" r="50" fill="none" stroke-width="10"' ||
    ' stroke-linecap="round" stroke="' || v_color || '"' ||
    ' stroke-dasharray="0 314" data-arc="' || TO_CHAR(v_arc) || '"' ||
    ' class="tea-score-arc"/></svg>' ||
    '<div class="tea-score-center">' ||
    '<span class="tea-score-number">' || TO_CHAR(v_score) || '</span>' ||
    '<span class="tea-score-max">/ 45 pts</span>' ||
    '</div></div>' ||
    '<div class="tea-score-info">' ||
    '<h2 class="tea-score-name">' || APEX_ESCAPE.HTML(v_nome) || '</h2>' ||
    '<div class="tea-score-pct" style="color:' || v_color || '">' ||
    TO_CHAR(ROUND(v_pct,0)) || '%</div>' ||
    '<span class="tea-score-badge" style="background:' || v_color || '">' ||
    v_nivel || '</span>' ||
    '<p class="tea-score-hint">' ||
    '15 quest&otilde;es &mdash; m&aacute;ximo 45 pontos (ICHOM TEA)' ||
    '</p></div></div>'
  );
END;
""".strip()

# Processo de salvamento da avaliação (pág. 53 — botão FINALIZAR)
SAVE_PLSQL = textwrap.dedent("""
DECLARE
  v_id     NUMBER;
  v_com    NUMBER;
  v_soc    NUMBER;
  v_hab    NUMBER;
  v_score  NUMBER;
  v_pct    NUMBER;
  v_coleta NUMBER;
BEGIN
  -- Comunicação (pág. 51, máx 15 pts)
  v_com :=
    NVL(TO_NUMBER(:P51_COM_Q1),0) + NVL(TO_NUMBER(:P51_COM_Q2),0) +
    NVL(TO_NUMBER(:P51_COM_Q3),0) + NVL(TO_NUMBER(:P51_COM_Q4),0) +
    NVL(TO_NUMBER(:P51_COM_Q5),0);

  -- Socialização (pág. 52, máx 15 pts)
  v_soc :=
    NVL(TO_NUMBER(:P52_SOC_Q1),0) + NVL(TO_NUMBER(:P52_SOC_Q2),0) +
    NVL(TO_NUMBER(:P52_SOC_Q3),0) + NVL(TO_NUMBER(:P52_SOC_Q4),0) +
    NVL(TO_NUMBER(:P52_SOC_Q5),0);

  -- Habilidades (pág. 53, máx 15 pts)
  v_hab :=
    NVL(TO_NUMBER(:P53_HAB_Q1),0) + NVL(TO_NUMBER(:P53_HAB_Q2),0) +
    NVL(TO_NUMBER(:P53_HAB_Q3),0) + NVL(TO_NUMBER(:P53_HAB_Q4),0) +
    NVL(TO_NUMBER(:P53_HAB_Q5),0);

  v_score := v_com + v_soc + v_hab;
  v_pct   := ROUND(v_score / 45 * 100, 1);

  SELECT NVL(MAX(NR_COLETA), 0) + 1
    INTO v_coleta
    FROM TEA_AVALIACOES
   WHERE ID_BENEFICIARIO = TO_NUMBER(:P50_ID_BENEFICIARIO);

  INSERT INTO TEA_AVALIACOES (
    ID_BENEFICIARIO, ID_PROVA, ID_TERAPEUTA, ID_CLINICA,
    NR_COLETA, DT_AVALIACAO, DS_STATUS,
    NR_SCORE_TOTAL, NR_PCT_TOTAL, FL_TERMO_ACEITO, DT_FINALIZACAO
  ) VALUES (
    TO_NUMBER(:P50_ID_BENEFICIARIO),
    TO_NUMBER(:P50_ID_PROVA),
    TO_NUMBER(:P50_ID_TERAPEUTA),
    (SELECT ID_CLINICA FROM TEA_TERAPEUTAS
      WHERE ID_TERAPEUTA = TO_NUMBER(:P50_ID_TERAPEUTA)),
    v_coleta,
    NVL(TO_DATE(:P50_DT_AVALIACAO, 'DD/MM/YYYY'), SYSDATE),
    'CONCLUIDA',
    v_score, v_pct,
    NVL(:P50_FL_TERMO, 'N'),
    SYSTIMESTAMP
  ) RETURNING ID_AVALIACAO INTO v_id;

  :AI_AVALIACAO_ID := TO_CHAR(v_id);

  APEX_UTIL.REDIRECT_URL(
    APEX_UTIL.PREPARE_URL(
      'f?p=' || :APP_ID || ':54:' || :APP_SESSION ||
      '::NO:54:P54_ID_AVALIACAO:' || v_id
    )
  );
END;
""").strip()

# SQL do histórico de avaliações (pág. 60)
HISTORY_SQL = """
SELECT
  a.ID_AVALIACAO                                     AS "ID",
  b.DS_NOME                                          AS "Beneficiario",
  b.NR_BENEFICIO                                     AS "Nr Beneficio",
  c.DS_NOME                                          AS "Clinica",
  t.DS_NOME                                          AS "Terapeuta",
  p.DS_NOME || ' v' || p.DS_VERSAO                  AS "Instrumento",
  TO_CHAR(a.DT_AVALIACAO, 'DD/MM/YYYY')             AS "Data",
  a.NR_COLETA                                        AS "Coleta",
  a.NR_SCORE_TOTAL || ' / 45'                        AS "Score",
  TO_CHAR(ROUND(a.NR_PCT_TOTAL,0)) || '%'            AS "Percentual",
  CASE
    WHEN a.NR_PCT_TOTAL >= 75 THEN 'Alto'
    WHEN a.NR_PCT_TOTAL >= 50 THEN 'Medio'
    ELSE 'Baixo'
  END                                                AS "Nivel",
  a.DS_STATUS                                        AS "Status"
FROM TEA_AVALIACOES a
JOIN TEA_BENEFICIARIOS b ON b.ID_BENEFICIARIO = a.ID_BENEFICIARIO
JOIN TEA_TERAPEUTAS    t ON t.ID_TERAPEUTA    = a.ID_TERAPEUTA
JOIN TEA_CLINICAS      c ON c.ID_CLINICA      = a.ID_CLINICA
JOIN TEA_PROVAS        p ON p.ID_PROVA        = a.ID_PROVA
ORDER BY a.DT_AVALIACAO DESC, a.ID_AVALIACAO DESC
""".strip()

# SQL do detalhe de avaliação (IR na pág. 54)
RESULT_SQL = """
SELECT
  b.DS_NOME                                          AS "Beneficiario",
  b.NR_BENEFICIO                                     AS "Nr Beneficio",
  p.DS_NOME || ' v' || p.DS_VERSAO                  AS "Instrumento",
  t.DS_NOME                                          AS "Terapeuta",
  c.DS_NOME                                          AS "Clinica",
  TO_CHAR(a.DT_AVALIACAO, 'DD/MM/YYYY')             AS "Data",
  a.NR_COLETA                                        AS "Nr Coleta",
  a.NR_SCORE_TOTAL || ' / 45'                        AS "Score Total",
  TO_CHAR(ROUND(a.NR_PCT_TOTAL,0)) || '%'            AS "Percentual",
  CASE
    WHEN a.NR_PCT_TOTAL >= 75 THEN 'Alto (>=75%)'
    WHEN a.NR_PCT_TOTAL >= 50 THEN 'Medio (50-74%)'
    ELSE 'Baixo (<50%)'
  END                                                AS "Nivel de Habilidade",
  a.DS_STATUS                                        AS "Status"
FROM TEA_AVALIACOES a
JOIN TEA_BENEFICIARIOS b ON b.ID_BENEFICIARIO = a.ID_BENEFICIARIO
JOIN TEA_PROVAS        p ON p.ID_PROVA        = a.ID_PROVA
JOIN TEA_TERAPEUTAS    t ON t.ID_TERAPEUTA    = a.ID_TERAPEUTA
JOIN TEA_CLINICAS      c ON c.ID_CLINICA      = a.ID_CLINICA
WHERE a.ID_AVALIACAO = :P54_ID_AVALIACAO
""".strip()


# =============================================================================
# Helpers
# =============================================================================
def ok(label: str, result_str: str) -> tuple[bool, dict]:
    r = json.loads(result_str)
    if r.get("status") == "error":
        print(f"  x  {label}: {r['error']}")
        return False, r
    print(f"  ok {label}")
    return True, r


def section(title: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'-' * 60}")


def add_plsql_region(page_id: int, name: str, plsql: str, seq: int) -> None:
    """Atalho para adicionar região PL/SQL sem template (banner/botões)."""
    ok(
        f"apex_add_region({page_id}, {name}, plsql)",
        apex_add_region(
            page_id=page_id,
            region_name=name,
            region_type="plsql",
            sequence=seq,
            source_sql=plsql,
            template="0",
        ),
    )


# =============================================================================
# Main
# =============================================================================
def run():
    t0 = time.perf_counter()
    print("\n" + "=" * 62)
    print(f"  {APP_NAME}")
    print(f"  App ID: {APP_ID}  |  14 páginas  |  Tema Unimed #00995D")
    print("=" * 62)

    # ── [1] Conectar ──────────────────────────────────────────────────────────
    section("[1] Conexão")
    if not ok("apex_connect", apex_connect())[0]:
        return

    # ── [2] Limpar ────────────────────────────────────────────────────────────
    section("[2] Limpar workspace")
    apps = json.loads(apex_list_apps())
    if isinstance(apps, list) and any(a.get("APPLICATION_ID") == APP_ID for a in apps):
        ok(f"apex_delete_app({APP_ID})", apex_delete_app(APP_ID))
    else:
        print(f"  ->  App {APP_ID} não existe, criando do zero")

    # ── [3] Criar app + tema global ───────────────────────────────────────────
    section("[3] Criar app + Tema Unimed Global")
    if not ok(f"apex_create_app({APP_ID})", apex_create_app(APP_ID, APP_NAME, home_page=1))[0]:
        return
    ok("apex_add_global_css", apex_add_global_css(UNIMED_THEME_CSS + "\n\n" + APP_EXTRA_CSS))

    # ── [4] Login (pág. 100) ──────────────────────────────────────────────────
    section("[4] Login — página 100")
    ok("apex_generate_login(100)", apex_generate_login(100))

    # ── [5] Dashboard — pág. 1 ───────────────────────────────────────────────
    section("[5] Dashboard — página 1 (métricas + gráficos)")
    ok(
        "apex_generate_analytics_page(1)",
        apex_generate_analytics_page(
            page_id=1,
            page_name="Dashboard",
            metrics=[
                {
                    "label": "Beneficiarios",
                    "sql":   "SELECT COUNT(*) FROM TEA_BENEFICIARIOS",
                    "icon":  "fa-users",
                    "color": "#00995D",
                },
                {
                    "label": "Avaliacoes",
                    "sql":   "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS = 'CONCLUIDA'",
                    "icon":  "fa-clipboard-check",
                    "color": "#1E88E5",
                },
                {
                    "label": "Score Medio",
                    "sql":   "SELECT NVL(ROUND(AVG(NR_PCT_TOTAL),0),0) FROM TEA_AVALIACOES WHERE DS_STATUS = 'CONCLUIDA'",
                    "unit":  "%",
                    "icon":  "fa-chart-bar",
                    "color": "#FF9800",
                },
                {
                    "label": "Clinicas",
                    "sql":   "SELECT COUNT(*) FROM TEA_CLINICAS",
                    "icon":  "fa-hospital",
                    "color": "#7B1FA2",
                },
            ],
            charts=[
                {
                    "region_name": "Avaliacoes por Clinica",
                    "chart_type":  "bar",
                    "sql_query": (
                        "SELECT c.DS_NOME LABEL, COUNT(*) VALUE"
                        " FROM TEA_AVALIACOES a"
                        " JOIN TEA_CLINICAS c ON c.ID_CLINICA = a.ID_CLINICA"
                        " WHERE a.DS_STATUS = 'CONCLUIDA'"
                        " GROUP BY c.DS_NOME ORDER BY VALUE DESC"
                    ),
                    "color_palette": ["#00995D","#43A047","#66BB6A","#006B3F","#1E88E5","#7B1FA2"],
                },
                {
                    "region_name": "Nivel de Desenvolvimento",
                    "chart_type":  "donut",
                    "sql_query": (
                        "SELECT CASE WHEN NR_PCT_TOTAL >= 75 THEN 'Alto'"
                        "            WHEN NR_PCT_TOTAL >= 50 THEN 'Medio'"
                        "            ELSE 'Baixo' END LABEL,"
                        "       COUNT(*) VALUE"
                        " FROM TEA_AVALIACOES"
                        " WHERE DS_STATUS = 'CONCLUIDA'"
                        " GROUP BY CASE WHEN NR_PCT_TOTAL >= 75 THEN 'Alto'"
                        "               WHEN NR_PCT_TOTAL >= 50 THEN 'Medio'"
                        "               ELSE 'Baixo' END"
                        " ORDER BY VALUE DESC"
                    ),
                    "color_palette": ["#00995D","#FF9800","#E53935"],
                },
            ],
        ),
    )

    # ── [6] CRUD Beneficiários (págs. 10 / 11) ───────────────────────────────
    section("[6] CRUD Beneficiários — páginas 10 / 11")
    ok("apex_generate_crud(TEA_BENEFICIARIOS)", apex_generate_crud("TEA_BENEFICIARIOS", 10, 11))

    # ── [7] CRUD Clínicas (págs. 20 / 21) ────────────────────────────────────
    section("[7] CRUD Clínicas — páginas 20 / 21")
    ok("apex_generate_crud(TEA_CLINICAS)", apex_generate_crud("TEA_CLINICAS", 20, 21))

    # ── [8] CRUD Terapeutas (págs. 30 / 31) ──────────────────────────────────
    section("[8] CRUD Terapeutas — páginas 30 / 31")
    ok("apex_generate_crud(TEA_TERAPEUTAS)", apex_generate_crud("TEA_TERAPEUTAS", 30, 31))

    # ── [9] Histórico de Avaliações (pág. 60) ────────────────────────────────
    section("[9] Histórico de Avaliações — página 60")
    ok(
        "apex_generate_report_page(60)",
        apex_generate_report_page(
            page_id=60,
            page_name="Historico de Avaliacoes",
            sql_query=HISTORY_SQL,
        ),
    )

    # ── [10] Wizard TEA 4 etapas (págs. 50–53) ───────────────────────────────
    section("[10] Wizard TEA — páginas 50–53")

    steps = [
        # Etapa 1 — Dados
        {
            "title": "Etapa 1 — Dados da Avaliacao",
            "items": [
                {
                    "name": "ID_BENEFICIARIO", "label": "Beneficiario (Paciente)",
                    "type": "select", "required": True,
                    "lov": (
                        "SELECT DS_NOME || ' (' || NR_BENEFICIO || ')' D,"
                        "       ID_BENEFICIARIO R"
                        "  FROM TEA_BENEFICIARIOS ORDER BY DS_NOME"
                    ),
                },
                {
                    "name": "ID_PROVA", "label": "Instrumento de Avaliacao",
                    "type": "select", "required": True,
                    "lov": (
                        "SELECT DS_NOME || ' v' || DS_VERSAO D, ID_PROVA R"
                        "  FROM TEA_PROVAS WHERE FL_ATIVO = 'S' ORDER BY NR_ORDEM"
                    ),
                },
                {
                    "name": "ID_TERAPEUTA", "label": "Terapeuta Responsavel",
                    "type": "select", "required": True,
                    "lov": (
                        "SELECT t.DS_NOME || ' — ' || c.DS_NOME D, t.ID_TERAPEUTA R"
                        "  FROM TEA_TERAPEUTAS t JOIN TEA_CLINICAS c ON c.ID_CLINICA = t.ID_CLINICA"
                        " ORDER BY t.DS_NOME"
                    ),
                },
                {
                    "name": "DT_AVALIACAO", "label": "Data da Avaliacao",
                    "type": "date", "required": True,
                },
                {
                    "name": "FL_TERMO", "label": "Termo de Consentimento Informado",
                    "type": "select", "required": True,
                    "lov": (
                        "SELECT 'Sim — Aceito e registrado' D,'S' R FROM DUAL UNION ALL "
                        "SELECT 'Nao — Recusado pelo responsavel' D,'N' R FROM DUAL"
                    ),
                },
            ],
        },
        # Etapa 2 — Comunicação
        {
            "title": "Etapa 2 — Comunicacao",
            "items": [
                {"name": "COM_Q1", "label": "1. Usa palavras para expressar necessidades basicas",
                 "type": "select", "lov": LIKERT},
                {"name": "COM_Q2", "label": "2. Responde quando seu nome e chamado",
                 "type": "select", "lov": LIKERT},
                {"name": "COM_Q3", "label": "3. Mantem contato visual durante conversas",
                 "type": "select", "lov": LIKERT},
                {"name": "COM_Q4", "label": "4. Faz perguntas para obter informacoes",
                 "type": "select", "lov": LIKERT},
                {"name": "COM_Q5", "label": "5. Compreende instrucoes verbais simples",
                 "type": "select", "lov": LIKERT},
            ],
        },
        # Etapa 3 — Socialização
        {
            "title": "Etapa 3 — Socializacao",
            "items": [
                {"name": "SOC_Q1", "label": "1. Interage espontaneamente com outras criancas",
                 "type": "select", "lov": LIKERT},
                {"name": "SOC_Q2", "label": "2. Demonstra empatia por outras pessoas",
                 "type": "select", "lov": LIKERT},
                {"name": "SOC_Q3", "label": "3. Participa de atividades em grupo",
                 "type": "select", "lov": LIKERT},
                {"name": "SOC_Q4", "label": "4. Compartilha brinquedos e materiais",
                 "type": "select", "lov": LIKERT},
                {"name": "SOC_Q5", "label": "5. Reconhece e expressa emocoes basicas",
                 "type": "select", "lov": LIKERT},
            ],
        },
        # Etapa 4 — Habilidades
        {
            "title": "Etapa 4 — Habilidades da Vida Diaria",
            "items": [
                {"name": "HAB_Q1", "label": "1. Realiza higiene pessoal com autonomia",
                 "type": "select", "lov": LIKERT},
                {"name": "HAB_Q2", "label": "2. Se veste e despe sem assistencia",
                 "type": "select", "lov": LIKERT},
                {"name": "HAB_Q3", "label": "3. Come com utensilios de forma independente",
                 "type": "select", "lov": LIKERT},
                {"name": "HAB_Q4", "label": "4. Organiza seus pertences e ambiente",
                 "type": "select", "lov": LIKERT},
                {"name": "HAB_Q5", "label": "5. Segue rotinas diarias estabelecidas",
                 "type": "select", "lov": LIKERT},
            ],
        },
    ]

    flag, wiz = ok(
        "apex_generate_wizard(50–53)",
        apex_generate_wizard(
            start_page_id=50,
            steps=steps,
            wizard_title="Avaliacao TEA — Protocolo ICHOM",
            finish_redirect_page=54,
        ),
    )
    if not flag:
        return
    print(f"    Páginas : {wiz.get('pages')}  |  Itens : {len(wiz.get('items_created', []))}")

    # Banners de introdução em cada etapa
    add_plsql_region(50, "Intro Etapa 1", INTRO_P50, seq=1)
    add_plsql_region(51, "Intro Etapa 2", INTRO_P51, seq=1)
    add_plsql_region(52, "Intro Etapa 3", INTRO_P52, seq=1)
    add_plsql_region(53, "Intro Etapa 4", INTRO_P53, seq=1)

    # JS: data padrão (pág. 50) + Likert visual (págs. 51–53)
    ok("apex_add_page_js(50)", apex_add_page_js(50, JS_P50))
    ok("apex_add_page_js(51)",
       apex_add_page_js(51, make_likert_js(
           ["P51_COM_Q1","P51_COM_Q2","P51_COM_Q3","P51_COM_Q4","P51_COM_Q5"])))
    ok("apex_add_page_js(52)",
       apex_add_page_js(52, make_likert_js(
           ["P52_SOC_Q1","P52_SOC_Q2","P52_SOC_Q3","P52_SOC_Q4","P52_SOC_Q5"])))
    ok("apex_add_page_js(53)",
       apex_add_page_js(53, make_likert_js(
           ["P53_HAB_Q1","P53_HAB_Q2","P53_HAB_Q3","P53_HAB_Q4","P53_HAB_Q5"])))

    # Processo de salvamento (pág. 53 — botão FINALIZAR)
    ok(
        "apex_add_process(53, Salvar Avaliacao)",
        apex_add_process(
            page_id=53,
            process_name="Salvar Avaliacao TEA",
            process_type="plsql",
            sequence=5,
            source=SAVE_PLSQL,
            condition_button="NEXT",
            success_message="Avaliacao registrada com sucesso!",
            error_message="Erro ao salvar avaliacao. Verifique os dados.",
        ),
    )

    # ── [11] App Item — transporta ID entre páginas ───────────────────────────
    section("[11] App Item — AI_AVALIACAO_ID")
    ok("apex_add_app_item", apex_add_app_item(item_name="AI_AVALIACAO_ID"))

    # ── [12] Score Final — página 54 ─────────────────────────────────────────
    section("[12] Score Final — página 54")
    ok("apex_add_page(54)", apex_add_page(54, "Score da Avaliacao", "blank"))

    add_plsql_region(54, "Acoes",             ACTIONS_P54,  seq=1)
    add_plsql_region(54, "Resultado",          SCORE_PLSQL,  seq=5)

    ok(
        "apex_add_metric_cards(54)",
        apex_add_metric_cards(
            page_id=54,
            region_name="Detalhes Rapidos",
            style="gradient",
            metrics=[
                {
                    "label": "Score Total",
                    "sql":   "SELECT NR_SCORE_TOTAL FROM TEA_AVALIACOES WHERE ID_AVALIACAO = :P54_ID_AVALIACAO",
                    "unit":  "/ 45",
                    "icon":  "fa-star",
                    "color": "#00995D",
                },
                {
                    "label": "Percentual",
                    "sql":   "SELECT ROUND(NR_PCT_TOTAL,0) FROM TEA_AVALIACOES WHERE ID_AVALIACAO = :P54_ID_AVALIACAO",
                    "unit":  "%",
                    "icon":  "fa-percent",
                    "color": "#1E88E5",
                },
                {
                    "label": "Nivel",
                    "sql": (
                        "SELECT CASE"
                        "  WHEN NR_PCT_TOTAL >= 75 THEN 'Alto'"
                        "  WHEN NR_PCT_TOTAL >= 50 THEN 'Medio'"
                        "  ELSE 'Baixo' END"
                        " FROM TEA_AVALIACOES WHERE ID_AVALIACAO = :P54_ID_AVALIACAO"
                    ),
                    "icon":  "fa-chart-bar",
                    "color": "#FF9800",
                },
                {
                    "label": "Nr Coleta",
                    "sql":   "SELECT NR_COLETA FROM TEA_AVALIACOES WHERE ID_AVALIACAO = :P54_ID_AVALIACAO",
                    "icon":  "fa-list-ol",
                    "color": "#7B1FA2",
                },
            ],
            sequence=10,
        ),
    )

    ok(
        "apex_add_region(54, Detalhes, ir)",
        apex_add_region(
            page_id=54,
            region_name="Detalhes da Avaliacao",
            region_type="ir",
            sequence=20,
            source_sql=RESULT_SQL,
        ),
    )

    ok(
        "apex_add_item(54, P54_ID_AVALIACAO, hidden)",
        apex_add_item(
            page_id=54,
            region_name="Detalhes da Avaliacao",
            item_name="P54_ID_AVALIACAO",
            item_type="hidden",
            sequence=5,
        ),
    )

    ok("apex_add_page_js(54)", apex_add_page_js(54, JS_P54))

    # ── [13] Navegação ────────────────────────────────────────────────────────
    section("[13] Navegação")
    nav_items = [
        ("Dashboard",       1,  10, "fa-home"),
        ("Beneficiarios",  10,  20, "fa-users"),
        ("Nova Avaliacao", 50,  30, "fa-clipboard-check"),
        ("Historico",      60,  40, "fa-list"),
        ("Clinicas",       20,  50, "fa-hospital"),
        ("Terapeutas",     30,  60, "fa-user-md"),
    ]
    for label, page, seq, icon in nav_items:
        ok(f"nav: {label}", apex_add_nav_item(label, page, seq, icon))

    # ── [14] Finalizar ────────────────────────────────────────────────────────
    section("[14] Finalizar app")
    if not ok("apex_finalize_app", apex_finalize_app())[0]:
        return

    # ── Resumo ────────────────────────────────────────────────────────────────
    total = time.perf_counter() - t0
    print(f"\n{'=' * 62}")
    print(f"  {APP_NAME}")
    print(f"  App {APP_ID} criado em {total:.1f}s")
    print()
    print(f"  Páginas:")
    print(f"    100  Login")
    print(f"      1  Dashboard  (4 KPIs + bar chart + donut chart)")
    print(f"     10  Beneficiários (IR + form 11)")
    print(f"     20  Clínicas      (IR + form 21)")
    print(f"     30  Terapeutas    (IR + form 31)")
    print(f"     50  Nova Avaliação — Etapa 1 (dados)")
    print(f"     51  Nova Avaliação — Etapa 2 (Comunicação — Likert)")
    print(f"     52  Nova Avaliação — Etapa 3 (Socialização — Likert)")
    print(f"     53  Nova Avaliação — Etapa 4 (Habilidades — Likert)")
    print(f"     54  Score Final   (SVG animado + métricas + IR)")
    print(f"     60  Histórico de Avaliações (IR)")
    print()
    print(f"  UI:")
    print(f"    - UNIMED_THEME_CSS global (Página 0) — paleta #00995D")
    print(f"    - Banners de intro em todas as etapas do wizard")
    print(f"    - Botões Likert visuais (0=Red 1=Orange 2=Blue 3=Green)")
    print(f"    - Score animado SVG + botões Nova Avaliação / Histórico")
    print()
    print(f"  Acesse: f?p={APP_ID}  (relativo à URL base APEX)")
    print("=" * 62 + "\n")


if __name__ == "__main__":
    run()
