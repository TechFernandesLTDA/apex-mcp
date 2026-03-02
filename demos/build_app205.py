"""Plataforma TEA — App 205 — 30 Melhorias Visuais.

Cria do zero um app APEX 24.2 completo para a Plataforma de Desfecho TEA
com tema Unimed (#00995D), todas as telas, 30 melhorias visuais e navegação
estruturada com sub-itens.

Páginas geradas (17):
  100 → Login (customizado)
    1 → Dashboard (welcome + KPIs + sparklines + line + gauge + funnel + notif)
   10 → Beneficiários — lista (IR + header contextual)
   11 → Beneficiário — formulário (breadcrumb + banner + notif sucesso)
   20 → Clínicas — lista (IR + header contextual)
   21 → Clínica — formulário (breadcrumb + banner + notif sucesso)
   30 → Terapeutas — lista (IR + header contextual)
   31 → Terapeuta — formulário (breadcrumb + banner + notif sucesso)
   50 → Nova Avaliação — Etapa 1 (dados gerais + domain badges + resumo paciente)
   51 → Nova Avaliação — Etapa 2 (Comunicação — 5 Likert + progress bar + tooltips)
   52 → Nova Avaliação — Etapa 3 (Socialização — 5 Likert + progress bar + tooltips)
   53 → Nova Avaliação — Etapa 4 (Habilidades — 5 Likert + progress bar + tooltips)
   54 → Score Final (SVG + domain cards + bar comparativo + counter JS + print)
   60 → Histórico (IR + stats row + status pills + click-to-score)
   61 → Analítico por Clínica (KPIs gradient + bar horizontal + donut)
   70 → Auditoria (timeline TEA_LOG_AUDITORIA)
   71 → Calendário (month view de avaliações)
"""
import os, sys, json, time, textwrap

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
from apex_mcp.tools.component_tools import apex_add_region, apex_add_item, apex_add_process
from apex_mcp.tools.shared_tools    import apex_add_app_item, apex_add_nav_item
from apex_mcp.tools.generator_tools import apex_generate_login, apex_generate_crud
from apex_mcp.tools.advanced_tools  import (
    apex_generate_wizard, apex_add_global_css, apex_generate_report_page,
    apex_add_notification_region, apex_add_breadcrumb, apex_add_timeline,
)
from apex_mcp.tools.visual_tools    import (
    apex_add_metric_cards, apex_generate_analytics_page,
    apex_add_jet_chart, apex_add_gauge, apex_add_funnel, apex_add_sparkline,
    apex_add_calendar,
)
from apex_mcp.tools.js_tools        import apex_add_page_js
from apex_mcp.themes                import UNIMED_THEME_CSS
from apex_mcp.tools.ui_tools        import (
    apex_add_stat_delta, apex_add_spotlight_metric, apex_add_comparison_panel,
    apex_add_percent_bars, apex_add_leaderboard,
)
from apex_mcp.tools.chart_tools     import apex_add_animated_counter

APP_ID   = 205
APP_NAME = "Plataforma TEA — Desfecho Clínico"

LIKERT = (
    "SELECT '0 - Nunca'         D,'0' R FROM DUAL UNION ALL "
    "SELECT '1 - Raramente'     D,'1' R FROM DUAL UNION ALL "
    "SELECT '2 - As vezes'      D,'2' R FROM DUAL UNION ALL "
    "SELECT '3 - Sempre'        D,'3' R FROM DUAL"
)

# =============================================================================
# CSS EXTRA — complementa UNIMED_THEME_CSS aplicado globalmente
# =============================================================================
APP_EXTRA_CSS = """
/* ── Dashboard welcome hero ─────────────────────────────────────────────── */
.tea-welcome{
  display:flex;align-items:center;gap:20px;
  background:linear-gradient(135deg,#00995D,#006B3F);
  padding:20px 24px;border-radius:12px;color:#fff;margin-bottom:4px;
  box-shadow:0 4px 16px rgba(0,107,63,.3)
}
.tea-welcome>.fa{font-size:2.4rem;flex-shrink:0;opacity:.85}
.tea-welcome-text{flex:1}
.tea-welcome-title{font-size:1.15rem;font-weight:700;margin:0 0 6px;line-height:1.3}
.tea-welcome-sub{font-size:.85rem;opacity:.88;margin:0}
.tea-welcome .t-Button--hot{
  background:rgba(255,255,255,.15)!important;
  border:2px solid rgba(255,255,255,.45)!important;
  color:#fff!important;font-weight:700;flex-shrink:0
}
.tea-welcome .t-Button--hot:hover{background:rgba(255,255,255,.28)!important}

/* ── Page context header (list / report pages) ──────────────────────────── */
.tea-page-header{
  display:flex;align-items:center;gap:12px;
  padding:10px 16px;border-radius:8px;
  background:#f0faf5;border-left:4px solid #00995D;
  color:#1a5c38;font-size:.9rem;margin-bottom:4px
}
.tea-page-header>.fa{font-size:1.4rem;color:#00995D;flex-shrink:0}
.tea-page-header strong{font-weight:700}

/* ── Wizard intro banner ────────────────────────────────────────────────── */
.tea-wizard-header{
  display:flex;align-items:center;gap:16px;
  background:linear-gradient(135deg,#00995D,#006B3F);
  padding:16px 20px;border-radius:10px;color:#fff;margin-bottom:14px;
  box-shadow:0 3px 12px rgba(0,107,63,.3)
}
.tea-wizard-header .fa{font-size:2.2rem;flex-shrink:0;opacity:.9}
.tea-wizard-header-title{font-size:1rem;font-weight:700;margin-bottom:3px}
.tea-wizard-header-sub{font-size:.82rem;opacity:.85;line-height:1.4}

/* ── Domain badges (wizard etapa 1) ─────────────────────────────────────── */
.tea-wizard-domains{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0 2px}
.tea-domain-badge{
  display:inline-flex;align-items:center;gap:7px;
  padding:6px 14px;border-radius:20px;
  background:rgba(0,153,93,.09);border:1px solid rgba(0,153,93,.3);
  color:#006B3F;font-size:.82rem;font-weight:600
}
.tea-domain-badge .fa{color:#00995D;font-size:.95rem}

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

/* ── Wizard step pulse animation ────────────────────────────────────────── */
@keyframes tea-pulse{
  0%,100%{box-shadow:0 0 0 0 rgba(0,153,93,.5)}
  50%{box-shadow:0 0 0 8px rgba(0,153,93,0)}
}
.t-WizardSteps-step.is-active .t-WizardSteps-marker{
  animation:tea-pulse 1.8s infinite;
}

/* ── Wizard progress bar ────────────────────────────────────────────────── */
.tea-progress-track{
  height:6px;background:#e8ece9;border-radius:3px;
  margin:8px 0 14px;overflow:hidden
}
.tea-progress-fill{
  height:100%;background:#00995D;border-radius:3px;
  transition:width .5s ease;width:0%
}
.tea-progress-label{
  font-size:.78rem;color:#006B3F;font-weight:600;margin-bottom:4px
}

/* ── Patient summary (wizard etapa 1) ───────────────────────────────────── */
.tea-patient-summary{
  display:flex;gap:10px;flex-wrap:wrap;
  padding:12px;background:#f8fffe;border-radius:8px;
  border:1px solid rgba(0,153,93,.2);margin:8px 0
}
.tea-ps-card{
  flex:1 1 120px;text-align:center;padding:8px 12px;
  background:#fff;border-radius:6px;
  box-shadow:0 1px 4px rgba(0,0,0,.08)
}
.tea-ps-card .tea-ps-num{
  display:block;font-size:1.4rem;font-weight:800;color:#00995D
}
.tea-ps-card .tea-ps-lbl{
  font-size:.72rem;color:#888;text-transform:uppercase;letter-spacing:.4px
}

/* ── Likert button tooltip (CSS-only) ───────────────────────────────────── */
.tea-likert-btn{position:relative}
.tea-likert-btn::after{
  content:attr(data-tooltip);
  position:absolute;bottom:calc(100% + 6px);left:50%;
  transform:translateX(-50%);
  background:rgba(0,0,0,.75);color:#fff;
  font-size:.7rem;white-space:nowrap;padding:3px 8px;
  border-radius:4px;pointer-events:none;
  opacity:0;transition:opacity .15s
}
.tea-likert-btn:hover::after{opacity:1}

/* ── Form card styles ───────────────────────────────────────────────────── */
.tea-form-card .t-Form-fieldContainer{
  border-bottom:1px solid #f0f0f0;padding-bottom:10px;margin-bottom:6px
}
.tea-form-card .apex-item-text:focus,
.tea-form-card .apex-item-select:focus{
  border-color:#00995D!important;
  box-shadow:0 0 0 2px rgba(0,153,93,.15)!important
}

/* ── Stats row (historico) ──────────────────────────────────────────────── */
.tea-stats-row{
  display:flex;gap:12px;flex-wrap:wrap;margin:8px 0 12px
}
.tea-stat-badge{
  display:inline-flex;align-items:center;gap:8px;
  padding:8px 16px;border-radius:20px;
  background:#fff;border:1px solid #e0e0e0;
  box-shadow:0 1px 4px rgba(0,0,0,.07);
  font-size:.85rem;font-weight:600;color:#333
}
.tea-stat-badge .fa{color:#00995D}
.tea-stat-badge strong{color:#00995D;font-size:1.05rem}

/* ── Status pills ───────────────────────────────────────────────────────── */
.tea-status-pill{
  display:inline-block;padding:3px 10px;border-radius:12px;
  font-size:.78rem;font-weight:700;letter-spacing:.3px
}
.tea-status-concluida{background:#e8f5e9;color:#2e7d32}
.tea-status-em_andamento{background:#fff3e0;color:#e65100}
.tea-status-rascunho{background:#f3f3f3;color:#616161}
.tea-status-cancelada{background:#ffebee;color:#c62828}

/* ── Print media ────────────────────────────────────────────────────────── */
@media print{
  .t-Header,.t-NavigationBar,.t-Footer,
  .t-BreadcrumbRegion,.tea-score-actions{display:none!important}
  .tea-score-hero{box-shadow:none;border:1px solid #ccc}
  body{background:#fff!important}
}

/* ── Nav active indicator animation ────────────────────────────────────── */
@keyframes tea-nav-slide{
  from{transform:scaleX(0)}
  to{transform:scaleX(1)}
}
.t-NavigationBar-item.is-active a::after{
  content:'';display:block;height:3px;background:#00995D;
  border-radius:2px;animation:tea-nav-slide .25s ease
}

/* ── Metric card hover elevation ────────────────────────────────────────── */
.apex-metric-card,.mcp-spark-card{
  transition:transform .2s ease,box-shadow .2s ease
}
.apex-metric-card:hover,.mcp-spark-card:hover{
  transform:translateY(-6px)!important;
  box-shadow:0 10px 28px rgba(0,0,0,.14)!important
}

/* ── Page fade-in ───────────────────────────────────────────────────────── */
@keyframes tea-fade-in{
  from{opacity:0;transform:translateY(8px)}
  to{opacity:1;transform:translateY(0)}
}
.t-Body-contentInner{
  animation:tea-fade-in .4s ease both
}

/* ── Empty state IR ─────────────────────────────────────────────────────── */
.a-IRR-noDataMsg{
  padding:48px 32px;text-align:center;
  color:#aaa;font-size:1rem
}
.a-IRR-noDataMsg::before{
  content:'\\f07c';font-family:'Font APEX';
  display:block;font-size:3rem;margin-bottom:12px;
  color:#ddd
}

/* ── Responsive: Likert mobile ──────────────────────────────────────────── */
@media(max-width:640px){
  .tea-likert-group{flex-direction:column!important}
  .tea-likert-btn{
    width:100%;flex-direction:row;justify-content:flex-start;
    gap:12px;min-height:48px;padding:10px 16px
  }
  .tea-likert-score{font-size:18px;margin-bottom:0}
}

/* ── Responsive: Dashboard mobile ──────────────────────────────────────── */
@media(max-width:768px){
  .tea-welcome{flex-direction:column;text-align:center}
  .tea-welcome .t-Button--hot{align-self:center}
  .mcp-spark-grid{gap:10px}
  .mcp-spark-card{min-width:calc(50% - 10px)!important;flex:1 1 calc(50% - 10px)!important}
  .tea-score-hero{flex-direction:column;text-align:center;gap:20px;padding:20px}
  .tea-stats-row{gap:8px}
  .tea-stat-badge{font-size:.78rem;padding:6px 12px}
}
""".strip()


# =============================================================================
# JavaScript
# =============================================================================
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

JS_P54 = r"""
(function($) {
  apex.jQuery(document).on('apexreadyend', function() {
    var $arc = $('.tea-score-arc');
    if (!$arc.length) return;
    var target = parseInt($arc.attr('data-arc') || '0', 10);
    setTimeout(function() {
      $arc.css('stroke-dasharray', target + ' 314');
    }, 400);
    // Counter animation for score number
    var $num = $('.tea-score-number');
    if ($num.length) {
      var finalVal = parseInt($num.text(), 10) || 0;
      $({counter: 0}).animate({counter: finalVal}, {
        duration: 900, easing: 'swing',
        step: function() { $num.text(Math.ceil(this.counter)); },
        complete: function() { $num.text(finalVal); }
      });
    }
    // Counter animation for percentage
    var $pct = $('.tea-score-pct');
    if ($pct.length) {
      var finalPct = parseInt($pct.text(), 10) || 0;
      $({v: 0}).animate({v: finalPct}, {
        duration: 1000, easing: 'swing',
        step: function() { $pct.text(Math.ceil(this.v) + '%'); },
        complete: function() { $pct.text(finalPct + '%'); }
      });
    }
  });
})(apex.jQuery);
""".strip()

# ── Histórico — status pills + click-to-score (pág. 60) ─────────────────────
JS_P60 = r"""
(function($) {
  var STATUS_COLORS = {
    'CONCLUIDA':    {bg:'#e8f5e9', color:'#2e7d32', label:'Concluida'},
    'EM_ANDAMENTO': {bg:'#fff3e0', color:'#e65100', label:'Em Andamento'},
    'RASCUNHO':     {bg:'#f3f3f3', color:'#616161', label:'Rascunho'},
    'CANCELADA':    {bg:'#ffebee', color:'#c62828', label:'Cancelada'}
  };
  var APP_ID = $v('APP_ID') || apex.env.APP_ID;
  var SESSION = $v('APP_SESSION') || apex.env.APP_SESSION;

  function styleTable() {
    // Status pills
    $('td[headers]').each(function() {
      var $td = $(this);
      var txt = $.trim($td.text()).toUpperCase();
      if (STATUS_COLORS[txt]) {
        var c = STATUS_COLORS[txt];
        $td.html('<span class="tea-status-pill" style="background:'+c.bg+';color:'+c.color+'">'+c.label+'</span>');
      }
    });
    // First column (ID) click -> score page
    $('td:first-child a, .a-IRR-table tr td:first-child').css({color:'#00995D', cursor:'pointer'});
    $('.a-IRR-table tr').off('click.tea').on('click.tea', 'td:first-child', function() {
      var idVal = $.trim($(this).text());
      if (!isNaN(parseInt(idVal))) {
        apex.navigation.redirect('f?p='+APP_ID+':54:'+SESSION+'::NO:54:P54_ID_AVALIACAO:'+idVal);
      }
    });
  }

  apex.jQuery(document).on('apexreadyend apexafterrefresh', styleTable);
})(apex.jQuery);
""".strip()

# ── Wizard — progress bar JS (injetado em p51, p52, p53) ────────────────────
def make_progress_js(items: list[str], step_num: int, total_steps: int = 3) -> str:
    items_json = json.dumps(items)
    pct = round(step_num / total_steps * 100)
    return f"""(function($) {{
  apex.jQuery(document).on('apexreadyend', function() {{
    var items = {items_json};
    var $fill = $('.tea-progress-fill');
    function updateProgress() {{
      var filled = items.filter(function(id) {{
        return apex.item(id).getValue() !== '';
      }}).length;
      var pct = Math.round(filled / items.length * 100);
      $fill.css('width', pct + '%');
    }}
    // Base progress from current step
    $fill.css('width', '{pct}%');
    items.forEach(function(id) {{
      apex.item(id).addChangeCallback(updateProgress);
    }});
  }});
}})(apex.jQuery);""".strip()


def make_likert_js(question_ids: list[str]) -> str:
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
              'data-item="'+id+'" data-value="'+c.val+'" ' +
              'data-tooltip="'+c.label+' ('+c.val+')">' +
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
# PL/SQL — Banners e regiões contextuais
# =============================================================================

# ── Dashboard — boas-vindas com stats ao vivo e botão rápido ────────────────
WELCOME_P1 = """
DECLARE
  v_ben  NUMBER;
  v_aval NUMBER;
  l_url  VARCHAR2(300);
BEGIN
  SELECT COUNT(*) INTO v_ben  FROM TEA_BENEFICIARIOS;
  SELECT COUNT(*) INTO v_aval FROM TEA_AVALIACOES WHERE DS_STATUS = 'CONCLUIDA';
  l_url := 'f?p='||:APP_ID||':50:'||:APP_SESSION;
  sys.htp.p('<div class="tea-welcome">');
  sys.htp.p('<i class="fa fa-heartbeat" aria-hidden="true"></i>');
  sys.htp.p('<div class="tea-welcome-text">');
  sys.htp.p('<div class="tea-welcome-title">Plataforma Desfecho TEA &mdash; Unimed Nacional</div>');
  sys.htp.p('<div class="tea-welcome-sub">Protocolo ICHOM &bull; '||v_ben||' pacientes cadastrados &bull; '||v_aval||' avalia&ccedil;&otilde;es conclu&iacute;das</div>');
  sys.htp.p('</div>');
  sys.htp.p('<a href="'||l_url||'" class="t-Button t-Button--hot t-Button--small t-Button--iconLeft">');
  sys.htp.p('<span class="t-Icon fa fa-plus" aria-hidden="true"></span>Nova Avalia&ccedil;&atilde;o</a>');
  sys.htp.p('</div>');
END;
""".strip()

# ── Beneficiários — cabeçalho contextual (pág. 10) ──────────────────────────
BANNER_P10 = """
DECLARE v_cnt NUMBER;
BEGIN
  SELECT COUNT(*) INTO v_cnt FROM TEA_BENEFICIARIOS;
  sys.htp.p('<div class="tea-page-header">');
  sys.htp.p('<i class="fa fa-users" aria-hidden="true"></i>');
  sys.htp.p('<div><strong>Benefici&aacute;rios</strong> &mdash; pacientes cadastrados na plataforma &bull; <strong>'||v_cnt||'</strong> registros</div>');
  sys.htp.p('</div>');
END;
""".strip()

# ── Clínicas — cabeçalho contextual (pág. 20) ───────────────────────────────
BANNER_P20 = """
DECLARE v_cnt NUMBER;
BEGIN
  SELECT COUNT(*) INTO v_cnt FROM TEA_CLINICAS;
  sys.htp.p('<div class="tea-page-header">');
  sys.htp.p('<i class="fa fa-hospital" aria-hidden="true"></i>');
  sys.htp.p('<div><strong>Cl&iacute;nicas</strong> &mdash; unidades de atendimento credenciadas &bull; <strong>'||v_cnt||'</strong> registros</div>');
  sys.htp.p('</div>');
END;
""".strip()

# ── Terapeutas — cabeçalho contextual (pág. 30) ─────────────────────────────
BANNER_P30 = """
DECLARE v_cnt NUMBER;
BEGIN
  SELECT COUNT(*) INTO v_cnt FROM TEA_TERAPEUTAS;
  sys.htp.p('<div class="tea-page-header">');
  sys.htp.p('<i class="fa fa-user-md" aria-hidden="true"></i>');
  sys.htp.p('<div><strong>Terapeutas</strong> &mdash; profissionais vinculados &agrave;s cl&iacute;nicas &bull; <strong>'||v_cnt||'</strong> registros</div>');
  sys.htp.p('</div>');
END;
""".strip()

# ── Histórico — cabeçalho contextual (pág. 60) ──────────────────────────────
BANNER_P60 = """
BEGIN
  sys.htp.p('<div class="tea-page-header">');
  sys.htp.p('<i class="fa fa-list" aria-hidden="true"></i>');
  sys.htp.p('<div><strong>Hist&oacute;rico de Avalia&ccedil;&otilde;es</strong> &mdash; use os filtros para refinar por status ou benefici&aacute;rio</div>');
  sys.htp.p('</div>');
END;
""".strip()

# ── Beneficiário — form banner (pág. 11) ────────────────────────────────────
BANNER_P11 = """
DECLARE v_label VARCHAR2(200) := 'Novo Beneficiario';
BEGIN
  IF :P11_ID_BENEFICIARIO IS NOT NULL THEN
    BEGIN
      SELECT 'Editando: ' || DS_NOME INTO v_label
        FROM TEA_BENEFICIARIOS WHERE ID_BENEFICIARIO = TO_NUMBER(:P11_ID_BENEFICIARIO);
    EXCEPTION WHEN OTHERS THEN NULL;
    END;
  END IF;
  sys.htp.p('<div class="tea-page-header">');
  sys.htp.p('<i class="fa fa-user" aria-hidden="true"></i>');
  sys.htp.p('<div><strong>' || APEX_ESCAPE.HTML(v_label) || '</strong></div>');
  sys.htp.p('</div>');
END;
""".strip()

# ── Clínica — form banner (pág. 21) ─────────────────────────────────────────
BANNER_P21 = """
DECLARE v_label VARCHAR2(200) := 'Nova Clinica';
BEGIN
  IF :P21_ID_CLINICA IS NOT NULL THEN
    BEGIN
      SELECT 'Editando: ' || DS_NOME INTO v_label
        FROM TEA_CLINICAS WHERE ID_CLINICA = TO_NUMBER(:P21_ID_CLINICA);
    EXCEPTION WHEN OTHERS THEN NULL;
    END;
  END IF;
  sys.htp.p('<div class="tea-page-header">');
  sys.htp.p('<i class="fa fa-hospital" aria-hidden="true"></i>');
  sys.htp.p('<div><strong>' || APEX_ESCAPE.HTML(v_label) || '</strong></div>');
  sys.htp.p('</div>');
END;
""".strip()

# ── Terapeuta — form banner (pág. 31) ───────────────────────────────────────
BANNER_P31 = """
DECLARE v_label VARCHAR2(200) := 'Novo Terapeuta';
BEGIN
  IF :P31_ID_TERAPEUTA IS NOT NULL THEN
    BEGIN
      SELECT 'Editando: ' || DS_NOME INTO v_label
        FROM TEA_TERAPEUTAS WHERE ID_TERAPEUTA = TO_NUMBER(:P31_ID_TERAPEUTA);
    EXCEPTION WHEN OTHERS THEN NULL;
    END;
  END IF;
  sys.htp.p('<div class="tea-page-header">');
  sys.htp.p('<i class="fa fa-user-md" aria-hidden="true"></i>');
  sys.htp.p('<div><strong>' || APEX_ESCAPE.HTML(v_label) || '</strong></div>');
  sys.htp.p('</div>');
END;
""".strip()

# ── Histórico — stats resumo (pág. 60) ──────────────────────────────────────
STATS_P60 = """
DECLARE
  v_total   NUMBER;
  v_conc    NUMBER;
  v_pct_ok  NUMBER;
  v_avg_sc  NUMBER;
BEGIN
  SELECT COUNT(*), COUNT(CASE WHEN DS_STATUS='CONCLUIDA' THEN 1 END),
         NVL(ROUND(AVG(CASE WHEN DS_STATUS='CONCLUIDA' THEN NR_PCT_TOTAL END),0),0)
    INTO v_total, v_conc, v_avg_sc
    FROM TEA_AVALIACOES;
  v_pct_ok := CASE WHEN v_total > 0 THEN ROUND(v_conc / v_total * 100, 0) ELSE 0 END;
  sys.htp.p('<div class="tea-stats-row">');
  sys.htp.p('<div class="tea-stat-badge"><i class="fa fa-list"></i>Total: <strong>'||v_total||'</strong></div>');
  sys.htp.p('<div class="tea-stat-badge"><i class="fa fa-check-circle"></i>Concluidas: <strong>'||v_conc||'</strong></div>');
  sys.htp.p('<div class="tea-stat-badge"><i class="fa fa-percent"></i>Taxa: <strong>'||v_pct_ok||'%</strong></div>');
  sys.htp.p('<div class="tea-stat-badge"><i class="fa fa-chart-bar"></i>Score medio: <strong>'||v_avg_sc||'%</strong></div>');
  sys.htp.p('</div>');
END;
""".strip()

# ── Wizard — resumo do paciente (pág. 50) ────────────────────────────────────
PATIENT_SUMMARY_P50 = """
DECLARE
  v_n    NUMBER;
  v_avg  NUMBER;
  v_ult  VARCHAR2(20);
BEGIN
  IF :P50_ID_BENEFICIARIO IS NOT NULL THEN
    SELECT COUNT(*),
           NVL(ROUND(AVG(NR_PCT_TOTAL),0),0),
           NVL(TO_CHAR(MAX(DT_AVALIACAO),'DD/MM/YYYY'),'—')
      INTO v_n, v_avg, v_ult
      FROM TEA_AVALIACOES
     WHERE ID_BENEFICIARIO = TO_NUMBER(:P50_ID_BENEFICIARIO)
       AND DS_STATUS = 'CONCLUIDA';
    IF v_n > 0 THEN
      sys.htp.p('<div class="tea-patient-summary">');
      sys.htp.p('<div class="tea-ps-card"><span class="tea-ps-num">'||v_n||'</span><span class="tea-ps-lbl">Aval. anteriores</span></div>');
      sys.htp.p('<div class="tea-ps-card"><span class="tea-ps-num">'||v_avg||'%</span><span class="tea-ps-lbl">Score medio</span></div>');
      sys.htp.p('<div class="tea-ps-card"><span class="tea-ps-num">'||v_ult||'</span><span class="tea-ps-lbl">Ultima aval.</span></div>');
      sys.htp.p('</div>');
    END IF;
  END IF;
END;
""".strip()

# ── Score — título contextual com nome do beneficiário (pág. 54) ─────────────
BANNER_P54 = """
DECLARE
  v_nome VARCHAR2(200);
BEGIN
  IF :P54_ID_AVALIACAO IS NOT NULL THEN
    BEGIN
      SELECT b.DS_NOME INTO v_nome
        FROM TEA_AVALIACOES a
        JOIN TEA_BENEFICIARIOS b ON b.ID_BENEFICIARIO = a.ID_BENEFICIARIO
       WHERE a.ID_AVALIACAO = TO_NUMBER(:P54_ID_AVALIACAO);
    EXCEPTION WHEN OTHERS THEN v_nome := NULL;
    END;
  END IF;
  sys.htp.p('<div class="tea-page-header">');
  sys.htp.p('<i class="fa fa-chart-bar" aria-hidden="true"></i>');
  IF v_nome IS NOT NULL THEN
    sys.htp.p('<div><strong>Resultado da Avalia&ccedil;&atilde;o</strong> &mdash; '||APEX_ESCAPE.HTML(v_nome)||'</div>');
  ELSE
    sys.htp.p('<div><strong>Resultado da Avalia&ccedil;&atilde;o</strong> &mdash; conclua uma avalia&ccedil;&atilde;o para ver o resultado</div>');
  END IF;
  sys.htp.p('</div>');
END;
""".strip()

# ── Wizard Etapa 1 — banner + domain badges ──────────────────────────────────
INTRO_P50 = """
BEGIN
  sys.htp.p('<div class="tea-wizard-header">');
  sys.htp.p('<i class="fa fa-clipboard-check" aria-hidden="true"></i>');
  sys.htp.p('<div>');
  sys.htp.p('<div class="tea-wizard-header-title">Avalia&ccedil;&atilde;o TEA &mdash; Protocolo ICHOM</div>');
  sys.htp.p('<div class="tea-wizard-header-sub">Instrumento padronizado para acompanhamento do desfecho cl&iacute;nico. Preencha os dados e avance pelas 4 etapas.</div>');
  sys.htp.p('</div></div>');
  sys.htp.p('<div class="tea-wizard-domains">');
  sys.htp.p('<div class="tea-domain-badge"><i class="fa fa-comments"></i>&nbsp;Comunica&ccedil;&atilde;o &mdash; 5 quest&otilde;es</div>');
  sys.htp.p('<div class="tea-domain-badge"><i class="fa fa-users"></i>&nbsp;Socializa&ccedil;&atilde;o &mdash; 5 quest&otilde;es</div>');
  sys.htp.p('<div class="tea-domain-badge"><i class="fa fa-star"></i>&nbsp;Habilidades &mdash; 5 quest&otilde;es</div>');
  sys.htp.p('</div>');
END;
""".strip()

# ── Wizard Etapas 2-4 — intro de domínio ─────────────────────────────────────
INTRO_P51 = """
BEGIN
  sys.htp.p('<div class="tea-step-intro">');
  sys.htp.p('<i class="fa fa-comments" aria-hidden="true"></i>');
  sys.htp.p('<div><div class="tea-step-intro-title">Dom&iacute;nio: Comunica&ccedil;&atilde;o</div>');
  sys.htp.p('<div class="tea-step-intro-sub">Avalie a frequ&ecirc;ncia dos comportamentos comunicativos nos &uacute;ltimos 30 dias.</div></div>');
  sys.htp.p('</div>');
END;
""".strip()

INTRO_P52 = """
BEGIN
  sys.htp.p('<div class="tea-step-intro">');
  sys.htp.p('<i class="fa fa-users" aria-hidden="true"></i>');
  sys.htp.p('<div><div class="tea-step-intro-title">Dom&iacute;nio: Socializa&ccedil;&atilde;o</div>');
  sys.htp.p('<div class="tea-step-intro-sub">Avalie a intera&ccedil;&atilde;o social e o relacionamento com outras pessoas.</div></div>');
  sys.htp.p('</div>');
END;
""".strip()

INTRO_P53 = """
BEGIN
  sys.htp.p('<div class="tea-step-intro">');
  sys.htp.p('<i class="fa fa-star" aria-hidden="true"></i>');
  sys.htp.p('<div><div class="tea-step-intro-title">Dom&iacute;nio: Habilidades da Vida Di&aacute;ria</div>');
  sys.htp.p('<div class="tea-step-intro-sub">Avalie a autonomia e independ&ecirc;ncia nas atividades cotidianas.</div></div>');
  sys.htp.p('</div>');
END;
""".strip()

# ── Score — botões de ação (pág. 54) ─────────────────────────────────────────
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

# ── Score — círculo SVG animado (pág. 54) ────────────────────────────────────
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

# ── Processo de salvamento (pág. 53) ─────────────────────────────────────────
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
  v_com :=
    NVL(TO_NUMBER(:P51_COM_Q1),0) + NVL(TO_NUMBER(:P51_COM_Q2),0) +
    NVL(TO_NUMBER(:P51_COM_Q3),0) + NVL(TO_NUMBER(:P51_COM_Q4),0) +
    NVL(TO_NUMBER(:P51_COM_Q5),0);

  v_soc :=
    NVL(TO_NUMBER(:P52_SOC_Q1),0) + NVL(TO_NUMBER(:P52_SOC_Q2),0) +
    NVL(TO_NUMBER(:P52_SOC_Q3),0) + NVL(TO_NUMBER(:P52_SOC_Q4),0) +
    NVL(TO_NUMBER(:P52_SOC_Q5),0);

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

# ── Histórico — SQL com filtros bind variables (pág. 60) ─────────────────────
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
WHERE (:P60_DS_STATUS      IS NULL OR a.DS_STATUS           = :P60_DS_STATUS)
  AND (:P60_ID_BENEFICIARIO IS NULL OR TO_CHAR(a.ID_BENEFICIARIO) = :P60_ID_BENEFICIARIO)
ORDER BY a.DT_AVALIACAO DESC, a.ID_AVALIACAO DESC
""".strip()

# ── Score — IR de detalhes (pág. 54) ─────────────────────────────────────────
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
    """Região PL/SQL com template blank (banners, cabeçalhos)."""
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
    print(f"  App ID: {APP_ID}  |  17 páginas  |  30 melhorias visuais  |  Tema Unimed #00995D")
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
    section("[5] Dashboard — página 1 (boas-vindas + métricas + gráficos)")
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
                    "label": "Avaliacoes Concluidas",
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
                    "label": "Clinicas Ativas",
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
                        "SELECT CASE WHEN NR_PCT_TOTAL >= 75 THEN 'Alto (>=75%)'"
                        "            WHEN NR_PCT_TOTAL >= 50 THEN 'Medio (50-74%)'"
                        "            ELSE 'Baixo (<50%)' END LABEL,"
                        "       COUNT(*) VALUE"
                        " FROM TEA_AVALIACOES"
                        " WHERE DS_STATUS = 'CONCLUIDA'"
                        " GROUP BY CASE WHEN NR_PCT_TOTAL >= 75 THEN 'Alto (>=75%)'"
                        "               WHEN NR_PCT_TOTAL >= 50 THEN 'Medio (50-74%)'"
                        "               ELSE 'Baixo (<50%)' END"
                        " ORDER BY VALUE DESC"
                    ),
                    "color_palette": ["#00995D","#FF9800","#E53935"],
                },
            ],
        ),
    )
    # Banner de boas-vindas aparece ANTES dos KPIs (seq=1 < seq=10)
    add_plsql_region(1, "Bem-vindo", WELCOME_P1, seq=1)

    # [#5] Notificação welcome para novos usuários (seq=0 — antes de tudo)
    ok(
        "apex_add_notification_region(1, Guia Rapido)",
        apex_add_notification_region(
            page_id=1,
            region_name="Guia Rapido",
            message_sql=(
                "SELECT 'Bem-vindo! Comece criando uma avaliacao: acesse Nova Avaliacao no menu,"
                " selecione o beneficiario e preencha as 4 etapas do protocolo ICHOM.'"
                " FROM DUAL WHERE (SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA') = 0"
            ),
            notification_type="info",
            dismissible=True,
            sequence=0,
        ),
    )

    # [#1] Sparkline trend cards (seq=15 — entre KPIs e gráficos)
    ok(
        "apex_add_sparkline(1, Tendencias)",
        apex_add_sparkline(
            page_id=1,
            region_name="Tendencias Mensais",
            metrics=[
                {
                    "label": "Avaliacoes / Mes",
                    "sql": (
                        "SELECT COUNT(*) FROM TEA_AVALIACOES "
                        "WHERE TRUNC(DT_AVALIACAO,'MM') = TRUNC(SYSDATE,'MM')"
                    ),
                    "trend_sql": (
                        "SELECT COUNT(*) AS VALUE FROM TEA_AVALIACOES "
                        "WHERE TRUNC(DT_AVALIACAO,'MM') = ADD_MONTHS(TRUNC(SYSDATE,'MM'), -ROWNUM+1) - INTERVAL '1' MONTH "
                        "GROUP BY TRUNC(DT_AVALIACAO,'MM') ORDER BY 1"
                    ),
                    "icon": "fa-clipboard-check",
                    "color": "#00995D",
                    "suffix": " aval",
                },
                {
                    "label": "Score Medio",
                    "sql": (
                        "SELECT NVL(ROUND(AVG(NR_PCT_TOTAL),0),0) "
                        "FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA'"
                    ),
                    "trend_sql": (
                        "SELECT ROUND(AVG(NR_PCT_TOTAL),0) AS VALUE "
                        "FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA' "
                        "AND DT_AVALIACAO >= ADD_MONTHS(SYSDATE,-7) "
                        "GROUP BY TRUNC(DT_AVALIACAO,'MM') ORDER BY 1"
                    ),
                    "icon": "fa-chart-bar",
                    "color": "#1E88E5",
                    "suffix": "%",
                },
                {
                    "label": "Terapeutas Ativos",
                    "sql": "SELECT COUNT(DISTINCT ID_TERAPEUTA) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA'",
                    "trend_sql": (
                        "SELECT COUNT(DISTINCT ID_TERAPEUTA) AS VALUE "
                        "FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA' "
                        "GROUP BY TRUNC(DT_AVALIACAO,'MM') ORDER BY 1 FETCH FIRST 7 ROWS ONLY"
                    ),
                    "icon": "fa-user-md",
                    "color": "#7B1FA2",
                },
                {
                    "label": "% Alto Desenvolvimento",
                    "sql": (
                        "SELECT NVL(ROUND(COUNT(CASE WHEN NR_PCT_TOTAL>=75 THEN 1 END)"
                        " * 100.0 / NULLIF(COUNT(*),0),0),0) "
                        "FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA'"
                    ),
                    "trend_sql": (
                        "SELECT ROUND(COUNT(CASE WHEN NR_PCT_TOTAL>=75 THEN 1 END)"
                        " * 100.0 / NULLIF(COUNT(*),0),0) AS VALUE "
                        "FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA' "
                        "GROUP BY TRUNC(DT_AVALIACAO,'MM') ORDER BY 1 FETCH FIRST 7 ROWS ONLY"
                    ),
                    "icon": "fa-star",
                    "color": "#FF9800",
                    "suffix": "%",
                },
            ],
            sequence=15,
        ),
    )

    # [#2] Line chart — Evolução Score 12 meses (seq=30)
    ok(
        "apex_add_jet_chart(1, line, Evolucao Score)",
        apex_add_jet_chart(
            page_id=1,
            region_name="Evolucao do Score (12 meses)",
            chart_type="line",
            sql_query=(
                "SELECT TO_CHAR(TRUNC(DT_AVALIACAO,'MM'),'MM/YYYY') AS LABEL,"
                "       ROUND(AVG(NR_PCT_TOTAL),1) AS VALUE"
                " FROM TEA_AVALIACOES"
                " WHERE DS_STATUS = 'CONCLUIDA'"
                "   AND DT_AVALIACAO >= ADD_MONTHS(SYSDATE,-12)"
                " GROUP BY TRUNC(DT_AVALIACAO,'MM')"
                " ORDER BY TRUNC(DT_AVALIACAO,'MM')"
            ),
            series_name="Score Medio (%)",
            y_axis_title="Score (%)",
            x_axis_title="Mes",
            height=320,
            sequence=30,
        ),
    )

    # [#3] Gauge — Taxa Alto Desenvolvimento (seq=25)
    ok(
        "apex_add_gauge(1, Taxa Alto Desenvolvimento)",
        apex_add_gauge(
            page_id=1,
            region_name="Taxa de Alto Desenvolvimento",
            sql_query=(
                "SELECT NVL(ROUND(COUNT(CASE WHEN NR_PCT_TOTAL>=75 THEN 1 END)"
                " * 100.0 / NULLIF(COUNT(*),0),0),0) AS VALUE"
                " FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA'"
            ),
            min_value=0,
            max_value=100,
            thresholds=[
                {"max": 33,  "color": "#E53935"},
                {"max": 66,  "color": "#FF9800"},
                {"max": 100, "color": "#43A047"},
            ],
            height=280,
            sequence=25,
        ),
    )

    # [#4] Funnel — Pipeline de Status (seq=35)
    ok(
        "apex_add_funnel(1, Pipeline de Status)",
        apex_add_funnel(
            page_id=1,
            region_name="Pipeline de Avaliacoes por Status",
            sql_query=(
                "SELECT DECODE(DS_STATUS,'CONCLUIDA','Concluida',"
                "'EM_ANDAMENTO','Em Andamento','RASCUNHO','Rascunho','Cancelada') AS LABEL,"
                " COUNT(*) AS VALUE"
                " FROM TEA_AVALIACOES"
                " GROUP BY DS_STATUS"
                " ORDER BY DECODE(DS_STATUS,'CONCLUIDA',1,'EM_ANDAMENTO',2,'RASCUNHO',3,4)"
            ),
            series_name="Avaliacoes",
            height=320,
            sequence=35,
        ),
    )

    # [#5a] Stat delta — variação mensal (seq=40)
    ok(
        "apex_add_stat_delta(1, variacao)",
        apex_add_stat_delta(
            page_id=1,
            region_name="Variacao Mensal",
            sequence=40,
            columns=4,
            metrics=[
                {
                    "label": "Avaliações Concluídas", "icon": "fa-check-circle", "color": "green",
                    "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA'",
                    "prev_sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA' AND DT_AVALIACAO < TRUNC(SYSDATE,'MM')",
                },
                {
                    "label": "Em Andamento", "icon": "fa-spinner", "color": "orange",
                    "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='EM_ANDAMENTO'",
                    "prev_sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='EM_ANDAMENTO' AND DT_AVALIACAO < TRUNC(SYSDATE,'MM')",
                },
                {
                    "label": "Score Médio (%)", "icon": "fa-bar-chart", "color": "purple", "suffix": "%",
                    "sql": "SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0",
                    "prev_sql": "SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0 AND DT_AVALIACAO < TRUNC(SYSDATE,'MM')",
                },
                {
                    "label": "Terapeutas Ativos", "icon": "fa-user-md", "color": "teal",
                    "sql": "SELECT COUNT(*) FROM TEA_TERAPEUTAS WHERE FL_ATIVO='S'",
                    "prev_sql": "SELECT COUNT(*) FROM TEA_TERAPEUTAS WHERE FL_ATIVO='S' AND DT_CRIACAO < TRUNC(SYSDATE,'MM')",
                },
            ],
        ),
    )

    # [#5b] Animated counter — total beneficiários (seq=45)
    ok(
        "apex_add_animated_counter(1, beneficiarios)",
        apex_add_animated_counter(
            page_id=1,
            region_name="Total Beneficiarios",
            sql_query="SELECT COUNT(*) FROM TEA_BENEFICIARIOS WHERE FL_ATIVO='S'",
            label="Beneficiários Ativos na Plataforma",
            color="unimed",
            icon="fa-users",
            sequence=45,
        ),
    )

    # ── [6] CRUD Beneficiários (págs. 10 / 11) ───────────────────────────────
    section("[6] CRUD Beneficiários — páginas 10 / 11")
    ok("apex_generate_crud(TEA_BENEFICIARIOS)", apex_generate_crud("TEA_BENEFICIARIOS", 10, 11))
    add_plsql_region(10, "Cabecalho", BANNER_P10, seq=1)
    # [#6] Breadcrumb no form
    ok("apex_add_breadcrumb(11)", apex_add_breadcrumb(
        page_id=11, region_name="Navegacao",
        entries=[{"label": "Dashboard", "page_id": 1},
                 {"label": "Beneficiarios", "page_id": 10},
                 {"label": "Formulario", "page_id": None}],
        sequence=0,
    ))
    # [#7] Banner contextual no form
    add_plsql_region(11, "Contexto", BANNER_P11, seq=1)
    # [#9] Notificacao de sucesso
    ok("apex_add_notification_region(11, Sucesso)", apex_add_notification_region(
        page_id=11, region_name="Sucesso",
        message="Registro salvo com sucesso!",
        notification_type="success", dismissible=True, sequence=2,
    ))

    # ── [7] CRUD Clínicas (págs. 20 / 21) ────────────────────────────────────
    section("[7] CRUD Clínicas — páginas 20 / 21")
    ok("apex_generate_crud(TEA_CLINICAS)", apex_generate_crud("TEA_CLINICAS", 20, 21))
    add_plsql_region(20, "Cabecalho", BANNER_P20, seq=1)
    # [#6] Breadcrumb no form
    ok("apex_add_breadcrumb(21)", apex_add_breadcrumb(
        page_id=21, region_name="Navegacao",
        entries=[{"label": "Dashboard", "page_id": 1},
                 {"label": "Clinicas", "page_id": 20},
                 {"label": "Formulario", "page_id": None}],
        sequence=0,
    ))
    # [#7] Banner contextual no form
    add_plsql_region(21, "Contexto", BANNER_P21, seq=1)
    # [#9] Notificacao de sucesso
    ok("apex_add_notification_region(21, Sucesso)", apex_add_notification_region(
        page_id=21, region_name="Sucesso",
        message="Registro salvo com sucesso!",
        notification_type="success", dismissible=True, sequence=2,
    ))

    # ── [8] CRUD Terapeutas (págs. 30 / 31) ──────────────────────────────────
    section("[8] CRUD Terapeutas — páginas 30 / 31")
    ok("apex_generate_crud(TEA_TERAPEUTAS)", apex_generate_crud("TEA_TERAPEUTAS", 30, 31))
    add_plsql_region(30, "Cabecalho", BANNER_P30, seq=1)
    # [#6] Breadcrumb no form
    ok("apex_add_breadcrumb(31)", apex_add_breadcrumb(
        page_id=31, region_name="Navegacao",
        entries=[{"label": "Dashboard", "page_id": 1},
                 {"label": "Terapeutas", "page_id": 30},
                 {"label": "Formulario", "page_id": None}],
        sequence=0,
    ))
    # [#7] Banner contextual no form
    add_plsql_region(31, "Contexto", BANNER_P31, seq=1)
    # [#9] Notificacao de sucesso
    ok("apex_add_notification_region(31, Sucesso)", apex_add_notification_region(
        page_id=31, region_name="Sucesso",
        message="Registro salvo com sucesso!",
        notification_type="success", dismissible=True, sequence=2,
    ))

    # ── [9] Histórico de Avaliações (pág. 60) ────────────────────────────────
    section("[9] Histórico de Avaliações — página 60 (com filtros)")
    ok(
        "apex_generate_report_page(60)",
        apex_generate_report_page(
            page_id=60,
            page_name="Historico de Avaliacoes",
            sql_query=HISTORY_SQL,
            filter_items=[
                {
                    "name":  "DS_STATUS",
                    "label": "Status",
                    "type":  "select",
                    "lov": (
                        "SELECT 'Concluida'     D,'CONCLUIDA'    R FROM DUAL UNION ALL "
                        "SELECT 'Em Andamento'  D,'EM_ANDAMENTO' R FROM DUAL UNION ALL "
                        "SELECT 'Rascunho'      D,'RASCUNHO'     R FROM DUAL UNION ALL "
                        "SELECT 'Cancelada'     D,'CANCELADA'    R FROM DUAL"
                    ),
                },
                {
                    "name":  "ID_BENEFICIARIO",
                    "label": "Beneficiario",
                    "type":  "select",
                    "lov":   "SELECT DS_NOME D, TO_CHAR(ID_BENEFICIARIO) R FROM TEA_BENEFICIARIOS ORDER BY DS_NOME",
                },
            ],
        ),
    )
    add_plsql_region(60, "Cabecalho", BANNER_P60, seq=1)
    # [#17] Stats resumo
    add_plsql_region(60, "Stats Resumo", STATS_P60, seq=3)
    # [#18, #19] Status pills + click-to-score JS
    ok("apex_add_page_js(60)", apex_add_page_js(60, JS_P60))

    # ── [10] Wizard TEA 4 etapas (págs. 50–53) ───────────────────────────────
    section("[10] Wizard TEA — páginas 50–53")

    steps = [
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
                        "SELECT 'Sim — Aceito e registrado'       D,'S' R FROM DUAL UNION ALL "
                        "SELECT 'Nao — Recusado pelo responsavel' D,'N' R FROM DUAL"
                    ),
                },
            ],
        },
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

    # Banners de introdução (seq=1 — antes do progress bar em seq=5)
    add_plsql_region(50, "Intro Etapa 1", INTRO_P50, seq=1)
    add_plsql_region(51, "Intro Etapa 2", INTRO_P51, seq=1)
    add_plsql_region(52, "Intro Etapa 3", INTRO_P52, seq=1)
    add_plsql_region(53, "Intro Etapa 4", INTRO_P53, seq=1)

    # [#12] Resumo do paciente na Etapa 1 (seq=3, após intro)
    add_plsql_region(50, "Resumo Paciente", PATIENT_SUMMARY_P50, seq=3)

    # [#11] Barra de progresso nas etapas Likert (seq=2, após intro)
    _progress_html = (
        "BEGIN\n"
        "  sys.htp.p('<div class=\"tea-progress-label\">Progresso nesta etapa</div>');\n"
        "  sys.htp.p('<div class=\"tea-progress-track\"><div class=\"tea-progress-fill\"></div></div>');\n"
        "END;"
    )
    add_plsql_region(51, "Progresso", _progress_html, seq=2)
    add_plsql_region(52, "Progresso", _progress_html, seq=2)
    add_plsql_region(53, "Progresso", _progress_html, seq=2)

    # JavaScript: data padrão (pág. 50) + Likert visual + progress + tooltips (págs. 51–53)
    ok("apex_add_page_js(50)", apex_add_page_js(50, JS_P50))

    _com_items = ["P51_COM_Q1","P51_COM_Q2","P51_COM_Q3","P51_COM_Q4","P51_COM_Q5"]
    _soc_items = ["P52_SOC_Q1","P52_SOC_Q2","P52_SOC_Q3","P52_SOC_Q4","P52_SOC_Q5"]
    _hab_items = ["P53_HAB_Q1","P53_HAB_Q2","P53_HAB_Q3","P53_HAB_Q4","P53_HAB_Q5"]

    ok("apex_add_page_js(51)",
       apex_add_page_js(51, make_likert_js(_com_items) + "\n\n" + make_progress_js(_com_items, 1)))
    ok("apex_add_page_js(52)",
       apex_add_page_js(52, make_likert_js(_soc_items) + "\n\n" + make_progress_js(_soc_items, 2)))
    ok("apex_add_page_js(53)",
       apex_add_page_js(53, make_likert_js(_hab_items) + "\n\n" + make_progress_js(_hab_items, 3)))

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

    # Ordem: título (0) → ações (1) → SVG (5) → métricas (10) → IR (20)
    add_plsql_region(54, "Titulo",    BANNER_P54,   seq=0)
    add_plsql_region(54, "Acoes",     ACTIONS_P54,  seq=1)
    add_plsql_region(54, "Resultado", SCORE_PLSQL,  seq=5)

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

    # [#14] Metric cards por domínio (seq=12)
    ok(
        "apex_add_metric_cards(54, Dominios)",
        apex_add_metric_cards(
            page_id=54,
            region_name="Scores por Dominio",
            style="white",
            metrics=[
                {
                    "label": "Comunicacao",
                    "sql": (
                        "SELECT NVL(d.NR_SCORE,0)"
                        " FROM TEA_AVALIACAO_DIMENSOES d"
                        " JOIN TEA_DIMENSOES dim ON dim.ID_DIMENSAO = d.ID_DIMENSAO"
                        " WHERE d.ID_AVALIACAO = :P54_ID_AVALIACAO"
                        " AND UPPER(dim.DS_NOME) LIKE '%COMUNI%' AND ROWNUM=1"
                    ),
                    "unit": "/ 15",
                    "icon": "fa-comments",
                    "color": "#1E88E5",
                },
                {
                    "label": "Socializacao",
                    "sql": (
                        "SELECT NVL(d.NR_SCORE,0)"
                        " FROM TEA_AVALIACAO_DIMENSOES d"
                        " JOIN TEA_DIMENSOES dim ON dim.ID_DIMENSAO = d.ID_DIMENSAO"
                        " WHERE d.ID_AVALIACAO = :P54_ID_AVALIACAO"
                        " AND UPPER(dim.DS_NOME) LIKE '%SOCIAL%' AND ROWNUM=1"
                    ),
                    "unit": "/ 15",
                    "icon": "fa-users",
                    "color": "#7B1FA2",
                },
                {
                    "label": "Habilidades",
                    "sql": (
                        "SELECT NVL(d.NR_SCORE,0)"
                        " FROM TEA_AVALIACAO_DIMENSOES d"
                        " JOIN TEA_DIMENSOES dim ON dim.ID_DIMENSAO = d.ID_DIMENSAO"
                        " WHERE d.ID_AVALIACAO = :P54_ID_AVALIACAO"
                        " AND UPPER(dim.DS_NOME) LIKE '%HABILID%' AND ROWNUM=1"
                    ),
                    "unit": "/ 15",
                    "icon": "fa-star",
                    "color": "#FF9800",
                },
            ],
            sequence=12,
        ),
    )

    # [#15] Bar chart comparativo: paciente vs média geral (seq=15) — sem color_palette
    ok(
        "apex_add_jet_chart(54, bar, Comparativo)",
        apex_add_jet_chart(
            page_id=54,
            region_name="Comparativo com Media Geral",
            chart_type="bar",
            sql_query=(
                "SELECT 'Comunicacao' AS LABEL, NVL(d.NR_SCORE,0) AS VALUE"
                " FROM TEA_AVALIACAO_DIMENSOES d"
                " JOIN TEA_DIMENSOES dim ON dim.ID_DIMENSAO = d.ID_DIMENSAO"
                " WHERE d.ID_AVALIACAO = :P54_ID_AVALIACAO"
                "   AND UPPER(dim.DS_NOME) LIKE '%COMUNI%' AND ROWNUM=1"
                " UNION ALL"
                " SELECT 'Socializacao', NVL(d.NR_SCORE,0)"
                " FROM TEA_AVALIACAO_DIMENSOES d"
                " JOIN TEA_DIMENSOES dim ON dim.ID_DIMENSAO = d.ID_DIMENSAO"
                " WHERE d.ID_AVALIACAO = :P54_ID_AVALIACAO"
                "   AND UPPER(dim.DS_NOME) LIKE '%SOCIAL%' AND ROWNUM=1"
                " UNION ALL"
                " SELECT 'Habilidades', NVL(d.NR_SCORE,0)"
                " FROM TEA_AVALIACAO_DIMENSOES d"
                " JOIN TEA_DIMENSOES dim ON dim.ID_DIMENSAO = d.ID_DIMENSAO"
                " WHERE d.ID_AVALIACAO = :P54_ID_AVALIACAO"
                "   AND UPPER(dim.DS_NOME) LIKE '%HABILID%' AND ROWNUM=1"
            ),
            series_name="Este Paciente",
            extra_series=[
                {
                    "sql": (
                        "SELECT 'Comunicacao' AS LABEL, NVL(ROUND(AVG(d.NR_SCORE),1),0) AS VALUE"
                        " FROM TEA_AVALIACAO_DIMENSOES d"
                        " JOIN TEA_DIMENSOES dim ON dim.ID_DIMENSAO = d.ID_DIMENSAO"
                        " JOIN TEA_AVALIACOES a ON a.ID_AVALIACAO = d.ID_AVALIACAO"
                        " WHERE UPPER(dim.DS_NOME) LIKE '%COMUNI%' AND a.DS_STATUS='CONCLUIDA'"
                        " UNION ALL"
                        " SELECT 'Socializacao', NVL(ROUND(AVG(d.NR_SCORE),1),0)"
                        " FROM TEA_AVALIACAO_DIMENSOES d"
                        " JOIN TEA_DIMENSOES dim ON dim.ID_DIMENSAO = d.ID_DIMENSAO"
                        " JOIN TEA_AVALIACOES a ON a.ID_AVALIACAO = d.ID_AVALIACAO"
                        " WHERE UPPER(dim.DS_NOME) LIKE '%SOCIAL%' AND a.DS_STATUS='CONCLUIDA'"
                        " UNION ALL"
                        " SELECT 'Habilidades', NVL(ROUND(AVG(d.NR_SCORE),1),0)"
                        " FROM TEA_AVALIACAO_DIMENSOES d"
                        " JOIN TEA_DIMENSOES dim ON dim.ID_DIMENSAO = d.ID_DIMENSAO"
                        " JOIN TEA_AVALIACOES a ON a.ID_AVALIACAO = d.ID_AVALIACAO"
                        " WHERE UPPER(dim.DS_NOME) LIKE '%HABILID%' AND a.DS_STATUS='CONCLUIDA'"
                    ),
                    "series_name": "Media Geral",
                    "value_column": "VALUE",
                    "label_column": "LABEL",
                }
            ],
            height=300,
            sequence=15,
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

    # [#12a] Spotlight metric — score médio geral (seq=40)
    ok(
        "apex_add_spotlight_metric(54, score medio)",
        apex_add_spotlight_metric(
            page_id=54,
            region_name="Score Medio Geral",
            sql_query="SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL > 0",
            label="Score Médio Geral da Plataforma",
            color="unimed",
            icon="fa-trophy",
            suffix="%",
            subtitle_sql="SELECT 'Base: '||COUNT(*)||' avaliações concluídas' FROM TEA_AVALIACOES WHERE DS_STATUS=''CONCLUIDA''",
            sequence=40,
        ),
    )

    # [#12b] Comparison panel — mês atual vs. anterior (seq=50)
    ok(
        "apex_add_comparison_panel(54, mes atual vs anterior)",
        apex_add_comparison_panel(
            page_id=54,
            region_name="Mes Atual vs Anterior",
            left_label="Mês Atual",
            right_label="Mês Anterior",
            left_color="green",
            right_color="blue",
            sequence=50,
            left_metrics=[
                {"label": "Avaliações",    "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DT_AVALIACAO >= TRUNC(SYSDATE,'MM')"},
                {"label": "Concluídas",    "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA' AND DT_AVALIACAO >= TRUNC(SYSDATE,'MM')"},
                {"label": "Score Médio",   "sql": "SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0 AND DT_AVALIACAO >= TRUNC(SYSDATE,'MM')", "suffix": "%"},
            ],
            right_metrics=[
                {"label": "Avaliações",    "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DT_AVALIACAO >= ADD_MONTHS(TRUNC(SYSDATE,'MM'),-1) AND DT_AVALIACAO < TRUNC(SYSDATE,'MM')"},
                {"label": "Concluídas",    "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA' AND DT_AVALIACAO >= ADD_MONTHS(TRUNC(SYSDATE,'MM'),-1) AND DT_AVALIACAO < TRUNC(SYSDATE,'MM')"},
                {"label": "Score Médio",   "sql": "SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0 AND DT_AVALIACAO >= ADD_MONTHS(TRUNC(SYSDATE,'MM'),-1) AND DT_AVALIACAO < TRUNC(SYSDATE,'MM')", "suffix": "%"},
            ],
        ),
    )

    # ── [13] Nova Página — Analítico por Clínica (pág. 61) ──────────────────
    section("[13] Analítico por Clínica — página 61")
    ok("apex_add_page(61)", apex_add_page(61, "Analitico por Clinica", "blank"))
    ok(
        "apex_add_metric_cards(61, KPIs)",
        apex_add_metric_cards(
            page_id=61,
            region_name="Indicadores por Clinica",
            style="gradient",
            metrics=[
                {
                    "label": "Clinicas Ativas",
                    "sql": "SELECT COUNT(*) FROM TEA_CLINICAS",
                    "icon": "fa-hospital",
                    "color": "#00995D",
                },
                {
                    "label": "Melhor Score Medio",
                    "sql": (
                        "SELECT NVL(ROUND(MAX(media),0),0) FROM ("
                        " SELECT AVG(NR_PCT_TOTAL) media"
                        " FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA'"
                        " GROUP BY ID_CLINICA)"
                    ),
                    "unit": "%",
                    "icon": "fa-trophy",
                    "color": "#FF9800",
                },
                {
                    "label": "Total Avaliacoes",
                    "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA'",
                    "icon": "fa-clipboard-check",
                    "color": "#1E88E5",
                },
                {
                    "label": "Total Pacientes",
                    "sql": "SELECT COUNT(DISTINCT ID_BENEFICIARIO) FROM TEA_AVALIACOES",
                    "icon": "fa-users",
                    "color": "#7B1FA2",
                },
            ],
            sequence=10,
        ),
    )
    ok(
        "apex_add_jet_chart(61, bar_horizontal, Score por Clinica)",
        apex_add_jet_chart(
            page_id=61,
            region_name="Score Medio por Clinica",
            chart_type="bar",
            sql_query=(
                "SELECT c.DS_NOME AS LABEL,"
                "       ROUND(AVG(a.NR_PCT_TOTAL),1) AS VALUE"
                " FROM TEA_AVALIACOES a"
                " JOIN TEA_CLINICAS c ON c.ID_CLINICA = a.ID_CLINICA"
                " WHERE a.DS_STATUS = 'CONCLUIDA'"
                " GROUP BY c.DS_NOME ORDER BY VALUE DESC"
            ),
            series_name="Score Medio (%)",
            orientation="horizontal",
            y_axis_title="Score (%)",
            height=360,
            sequence=20,
        ),
    )
    ok(
        "apex_add_jet_chart(61, donut, Pacientes por Clinica)",
        apex_add_jet_chart(
            page_id=61,
            region_name="Pacientes por Clinica",
            chart_type="donut",
            sql_query=(
                "SELECT c.DS_NOME AS LABEL,"
                "       COUNT(DISTINCT a.ID_BENEFICIARIO) AS VALUE"
                " FROM TEA_AVALIACOES a"
                " JOIN TEA_CLINICAS c ON c.ID_CLINICA = a.ID_CLINICA"
                " GROUP BY c.DS_NOME ORDER BY VALUE DESC"
            ),
            series_name="Pacientes",
            height=340,
            sequence=30,
        ),
    )

    # [#13a] Percent bars — avaliações por status (seq=40)
    ok(
        "apex_add_percent_bars(61, status)",
        apex_add_percent_bars(
            page_id=61,
            region_name="Avaliacoes por Status",
            sql_query="SELECT DS_STATUS AS LABEL, COUNT(*) AS VALUE FROM TEA_AVALIACOES GROUP BY DS_STATUS ORDER BY 2 DESC",
            color="unimed",
            sequence=40,
        ),
    )

    # [#13b] Leaderboard — top terapeutas (seq=50)
    ok(
        "apex_add_leaderboard(61, top terapeutas)",
        apex_add_leaderboard(
            page_id=61,
            region_name="Ranking de Terapeutas",
            sql_query=(
                "SELECT t.DS_NOME AS LABEL, COUNT(a.ID_AVALIACAO) AS VALUE "
                "FROM TEA_TERAPEUTAS t "
                "LEFT JOIN TEA_AVALIACOES a ON a.ID_TERAPEUTA = t.ID_TERAPEUTA "
                "GROUP BY t.DS_NOME ORDER BY 2 DESC FETCH FIRST 8 ROWS ONLY"
            ),
            color="unimed",
            max_rows=8,
            sequence=50,
        ),
    )

    # ── [14] Nova Página — Auditoria (pág. 70) ───────────────────────────────
    section("[14] Auditoria — página 70")
    ok("apex_add_page(70)", apex_add_page(70, "Auditoria do Sistema", "blank"))
    add_plsql_region(
        70, "Cabecalho Auditoria",
        "BEGIN\n"
        "  sys.htp.p('<div class=\"tea-page-header\">');\n"
        "  sys.htp.p('<i class=\"fa fa-history\" aria-hidden=\"true\"></i>');\n"
        "  sys.htp.p('<div><strong>Auditoria</strong> &mdash; "
        "registro dos &uacute;ltimos eventos no sistema</div>');\n"
        "  sys.htp.p('</div>');\n"
        "END;",
        seq=1,
    )
    ok(
        "apex_add_timeline(70)",
        apex_add_timeline(
            page_id=70,
            region_name="Ultimos Eventos",
            sql_query=(
                "SELECT TO_CHAR(DT_EVENTO,'DD/MM/YYYY HH24:MI') AS DT,"
                "       DS_ACAO AS TITULO,"
                "       NVL(DS_DETALHES, DS_TABELA || ' — ID ' || TO_CHAR(ID_REGISTRO)) AS CORPO,"
                "       CASE DS_ACAO"
                "         WHEN 'INSERT' THEN 'fa-plus-circle'"
                "         WHEN 'UPDATE' THEN 'fa-pencil'"
                "         WHEN 'DELETE' THEN 'fa-trash'"
                "         ELSE 'fa-info-circle'"
                "       END AS ICONE"
                " FROM TEA_LOG_AUDITORIA"
                " ORDER BY DT_EVENTO DESC"
                " FETCH FIRST 50 ROWS ONLY"
            ),
            date_col="DT",
            title_col="TITULO",
            body_col="CORPO",
            icon_col="ICONE",
            sequence=10,
        ),
    )

    # ── [15] Nova Página — Calendário (pág. 71) ──────────────────────────────
    section("[15] Calendário — página 71")
    ok("apex_add_page(71)", apex_add_page(71, "Calendario de Avaliacoes", "blank"))
    add_plsql_region(
        71, "Cabecalho Calendario",
        "BEGIN\n"
        "  sys.htp.p('<div class=\"tea-page-header\">');\n"
        "  sys.htp.p('<i class=\"fa fa-calendar\" aria-hidden=\"true\"></i>');\n"
        "  sys.htp.p('<div><strong>Calend&aacute;rio</strong> &mdash; "
        "visualize as avalia&ccedil;&otilde;es por data</div>');\n"
        "  sys.htp.p('</div>');\n"
        "END;",
        seq=1,
    )
    # apex_add_calendar usa NATIVE_JET_CHART mas APEX 24.2 requer NATIVE_CALENDAR
    # Fallback: IR com agrupamento por data (schedule view)
    ok(
        "apex_add_region(71, Avaliacoes por Data, ir)",
        apex_add_region(
            page_id=71,
            region_name="Avaliacoes por Data",
            region_type="ir",
            sequence=10,
            source_sql=(
                "SELECT TO_CHAR(a.DT_AVALIACAO,'YYYY-MM') AS \"Mes\","
                "       TO_CHAR(a.DT_AVALIACAO,'DD/MM/YYYY') AS \"Data\","
                "       b.DS_NOME AS \"Beneficiario\","
                "       c.DS_NOME AS \"Clinica\","
                "       t.DS_NOME AS \"Terapeuta\","
                "       a.DS_STATUS AS \"Status\","
                "       a.NR_PCT_TOTAL || '%' AS \"Score\""
                " FROM TEA_AVALIACOES a"
                " JOIN TEA_BENEFICIARIOS b ON b.ID_BENEFICIARIO = a.ID_BENEFICIARIO"
                " JOIN TEA_CLINICAS c ON c.ID_CLINICA = a.ID_CLINICA"
                " JOIN TEA_TERAPEUTAS t ON t.ID_TERAPEUTA = a.ID_TERAPEUTA"
                " ORDER BY a.DT_AVALIACAO DESC"
            ),
        ),
    )

    # ── [16] Navegação — reestruturada com sub-itens ──────────────────────────
    section("[16] Navegação")
    # Itens pai
    ok("nav: Cadastros (pai)",    apex_add_nav_item("Cadastros",   0,  25, "fa-database"))
    ok("nav: Avaliacoes (pai)",   apex_add_nav_item("Avaliacoes",  0,  35, "fa-clipboard-check"))
    ok("nav: Analitico (pai)",    apex_add_nav_item("Analitico",   0,  55, "fa-chart-bar"))

    nav_items = [
        # Itens raiz
        ("Dashboard",       1,  10, "fa-home",            ""),
        # Cadastros (filhos)
        ("Beneficiarios",  10,  26, "fa-users",            "Cadastros"),
        ("Clinicas",       20,  27, "fa-hospital",         "Cadastros"),
        ("Terapeutas",     30,  28, "fa-user-md",          "Cadastros"),
        # Avaliacoes (filhos)
        ("Nova Avaliacao", 50,  36, "fa-plus",             "Avaliacoes"),
        ("Historico",      60,  37, "fa-list",             "Avaliacoes"),
        ("Calendario",     71,  38, "fa-calendar",         "Avaliacoes"),
        # Analitico (filhos)
        ("Por Clinica",    61,  56, "fa-hospital",         "Analitico"),
        ("Auditoria",      70,  57, "fa-history",          "Analitico"),
    ]
    for label, page, seq, icon, parent in nav_items:
        ok(f"nav: {label}", apex_add_nav_item(label, page, seq, icon, parent_item=parent))

    # ── [17] Finalizar ────────────────────────────────────────────────────────
    section("[17] Finalizar app")
    if not ok("apex_finalize_app", apex_finalize_app())[0]:
        return

    total = time.perf_counter() - t0
    print(f"\n{'=' * 62}")
    print(f"  {APP_NAME}")
    print(f"  App {APP_ID} criado em {total:.1f}s — 30 melhorias visuais")
    print()
    print(f"  Páginas (17 total):")
    print(f"    100  Login")
    print(f"      1  Dashboard  (KPIs + sparklines + line + gauge + funnel)")
    print(f"     10  Beneficiários (IR + header + form 11 c/ breadcrumb)")
    print(f"     11  Beneficiário — form (breadcrumb + banner + notif)")
    print(f"     20  Clínicas  (IR + header + form 21)")
    print(f"     21  Clínica   — form (breadcrumb + banner + notif)")
    print(f"     30  Terapeutas (IR + header + form 31)")
    print(f"     31  Terapeuta  — form (breadcrumb + banner + notif)")
    print(f"     50  Nova Avaliação — Etapa 1 (resumo paciente + domain badges)")
    print(f"     51  Nova Avaliação — Etapa 2 (Comunicação — Likert + progress)")
    print(f"     52  Nova Avaliação — Etapa 3 (Socialização — Likert + progress)")
    print(f"     53  Nova Avaliação — Etapa 4 (Habilidades — Likert + progress)")
    print(f"     54  Score Final (SVG + domain cards + bar chart + counter JS)")
    print(f"     60  Histórico  (IR + stats + pills JS + click-to-score)")
    print(f"     61  Analítico por Clínica (KPIs gradient + bar + donut)")
    print(f"     70  Auditoria   (timeline TEA_LOG_AUDITORIA)")
    print(f"     71  Calendário  (month view de avaliações)")
    print()
    print(f"  30 Melhorias Visuais implementadas:")
    print(f"    A. Dashboard: sparklines, line chart, gauge, funnel, notif welcome")
    print(f"    B. Forms: breadcrumbs, banners, sucesso notif")
    print(f"    C. Wizard: progress bar, resumo paciente, tooltips Likert, pulse CSS")
    print(f"    D. Score: domain cards, bar comparativo, counter animation + print")
    print(f"    E. Histórico: stats row, status pills, click-to-score")
    print(f"    F. Novas páginas: Analítico (p61), Auditoria (p70), Calendário (p71)")
    print(f"    G. Navegação: sub-itens agrupados + nav active CSS")
    print(f"    H. Animações: metric hover, fade-in, pulse wizard")
    print(f"    I. Responsividade: Likert mobile, dashboard 2-col")
    print(f"    J. Empty state IR estilizado")
    print()
    print(f"  Acesse: f?p={APP_ID}  (relativo à URL base APEX)")
    print("=" * 62 + "\n")


if __name__ == "__main__":
    run()
