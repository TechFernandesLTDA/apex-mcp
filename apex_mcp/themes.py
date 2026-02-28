"""Tema Unimed — CSS completo extraído do app de produção APEX 24.2.13.

Baseado no theme CSS do app "Plataforma Desfecho TEA" (ID 108).
Aplica a paleta Unimed (#00995D) sobre o Universal Theme 42 Redwood Light.

Uso:
    from apex_mcp.themes import UNIMED_THEME_CSS
    apex_add_global_css(UNIMED_THEME_CSS)   # aplica em todas as páginas via Page 0
    # ou
    apex_add_page_css(page_id, UNIMED_THEME_CSS)   # aplica só em uma página
"""
from __future__ import annotations

# ── Paleta Unimed (referência rápida) ─────────────────────────────────────────
UNIMED_PRIMARY   = "#00995D"
UNIMED_DARK      = "#006B3F"
UNIMED_LIGHT     = "#E8F5E9"
UNIMED_SUCCESS   = "#43A047"
UNIMED_WARNING   = "#FF9800"
UNIMED_DANGER    = "#E53935"
UNIMED_INFO      = "#1E88E5"
UNIMED_BG        = "#F5F7FA"
UNIMED_TEXT      = "#333333"
UNIMED_BORDER    = "#DEE2E6"

# ── CSS completo do tema ───────────────────────────────────────────────────────
UNIMED_THEME_CSS: str = """
/* =============================================================================
   TEMA UNIMED — Oracle APEX 24.2 / Universal Theme 42 / Redwood Light
   Plataforma Desfecho TEA — paleta #00995D (Unimed Nacional)
   ============================================================================= */

/* 1. VARIÁVEIS CSS (Theme Roller Override) */
:root {
    --ut-palette-primary:          #00995D;
    --ut-palette-primary-contrast: #FFFFFF;
    --ut-palette-primary-shade:    #006B3F;
    --ut-palette-success:          #43A047;
    --ut-palette-warning:          #FF9800;
    --ut-palette-danger:           #E53935;
    --ut-palette-info:             #1E88E5;
    --ut-body-background-color:    #F5F7FA;
    --ut-region-background-color:  #FFFFFF;
    --ut-body-text-color:          #333333;
    --ut-heading-text-color:       #222222;
    --ut-component-border-color:   #DEE2E6;
    --ut-component-border-radius:  8px;
    --ut-shadow:       0 2px 8px rgba(0,0,0,0.08);
    --ut-shadow-lg:    0 4px 16px rgba(0,0,0,0.12);
}

/* 2. CABEÇALHO (Top Bar) */
.t-Header-branding {
    background: linear-gradient(135deg, #00995D, #006B3F) !important;
    box-shadow: 0 2px 12px rgba(0,107,63,0.3);
}
.t-Header-logo-link { color: #FFFFFF !important; font-weight: 700; }
.t-Header-nav-list .t-Header-nav-item .t-Header-nav-link {
    color: rgba(255,255,255,0.85) !important;
    border-radius: 6px; transition: all 0.2s;
}
.t-Header-nav-list .t-Header-nav-item .t-Header-nav-link:hover,
.t-Header-nav-list .t-Header-nav-item.is-active .t-Header-nav-link {
    background: rgba(255,255,255,0.2) !important; color: #FFFFFF !important;
}

/* 3. SIDEBAR / NAVEGAÇÃO */
.t-Body-nav {
    background-color: #FFFFFF !important;
    border-right: 1px solid #DEE2E6 !important;
    scrollbar-width: thin !important;
    scrollbar-color: #A5D6A7 transparent !important;
}
.t-Body-nav::-webkit-scrollbar { width: 6px !important; }
.t-Body-nav::-webkit-scrollbar-thumb {
    background: #A5D6A7 !important; border-radius: 10px;
}
.t-Body-nav::-webkit-scrollbar-thumb:hover { background: #66BB6A !important; }

.t-TreeNav,
.t-TreeNav .a-TreeView-node,
.t-TreeNav .a-TreeView-row,
.t-TreeNav .a-TreeView-content {
    background-color: transparent !important;
    background-image: none !important;
    box-shadow: none !important; border-radius: 0 !important;
}
.t-TreeNav .a-TreeView-content,
.t-TreeNav .a-TreeView-row { border-left: 3px solid transparent !important; transition: all 0.15s; }
.t-TreeNav .a-TreeView-label, .t-TreeNav .fa { color: #666666 !important; }
.t-TreeNav .a-TreeView-node:hover > .a-TreeView-content,
.t-TreeNav .a-TreeView-node:hover > .a-TreeView-row,
.t-TreeNav .is-selected > .a-TreeView-content,
.t-TreeNav .is-selected > .a-TreeView-row { background-color: #E8F5E9 !important; }
.t-TreeNav .a-TreeView-node.is-current > .a-TreeView-content,
.t-TreeNav .a-TreeView-node.is-current > .a-TreeView-row {
    background-color: #E8F5E9 !important; border-left: 3px solid #00995D !important;
}
.t-TreeNav .a-TreeView-node.is-current > .a-TreeView-content .a-TreeView-label,
.t-TreeNav .a-TreeView-node.is-current > .a-TreeView-row .a-TreeView-label,
.t-TreeNav .a-TreeView-node.is-current > .a-TreeView-content .fa,
.t-TreeNav .a-TreeView-node.is-current > .a-TreeView-row .fa {
    color: #00995D !important; font-weight: 600 !important;
}

/* 4. BOTÕES */
.t-Button--hot,
.t-Button.t-Button--hot:not(.t-Button--simple) {
    background-color: #00995D !important; border-color: #00995D !important;
    color: #FFFFFF !important; border-radius: 6px; font-weight: 600; transition: all 0.2s;
}
.t-Button--hot:hover,
.t-Button.t-Button--hot:not(.t-Button--simple):hover {
    background-color: #006B3F !important; border-color: #006B3F !important;
    box-shadow: 0 2px 8px rgba(0,153,93,0.4);
}
.t-Button:not(.t-Button--hot):not(.t-Button--simple):not(.t-Button--danger) {
    border-radius: 6px; transition: all 0.2s;
}
.t-Button--danger { background-color: #E53935 !important; border-color: #E53935 !important; }

/* 5. REGIÕES */
.t-Region {
    border-radius: 8px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
    border: none !important;
}
.t-Region-header { border-bottom: 1px solid #DEE2E6; }
.t-Region-title { color: #333333; font-weight: 600; font-size: 16px; }
.t-Region--accent1 .t-Region-header { background-color: #00995D; }
.t-Region--accent1 .t-Region-title { color: #FFFFFF; }

/* 6. INTERACTIVE REPORT */
.a-IRR-table th,
.a-IG .a-GV-header .a-GV-headerLabel {
    background-color: #00995D !important; color: #FFFFFF !important;
    font-weight: 600; font-size: 13px; text-transform: uppercase; letter-spacing: 0.3px;
}
.a-IRR-table th a, .a-IRR-headerLink { color: #FFFFFF !important; }
.a-IRR-table th .a-IRR-headerIcon,
.a-IRR-table th .a-IRR-headerAction,
.a-IRR-table th .a-Icon,
.a-IG-header .a-Icon {
    color: #FFFFFF !important; fill: #FFFFFF !important;
    filter: brightness(0) invert(1) !important;
}
.a-IRR-table tr:hover td,
.a-IG .a-GV-row:hover .a-GV-cell { background-color: #E8F5E9 !important; }
.a-IRR-table tr:nth-child(even) td { background-color: #FAFAFA !important; }
.a-IRR-table a { color: #00995D; font-weight: 500; }
.a-IRR-table a:hover { color: #006B3F; }

/* 7. FORMULÁRIOS */
.apex-item-text,
.apex-item-select,
.apex-item-textarea,
input.text_field,
select.selectlist,
textarea.textarea {
    border: 2px solid #DEE2E6 !important;
    border-radius: 6px !important;
    padding: 10px 14px !important;
    font-size: 14px;
    transition: border-color 0.2s, box-shadow 0.2s;
}
.apex-item-text:focus,
.apex-item-select:focus,
.apex-item-textarea:focus,
input.text_field:focus,
select.selectlist:focus,
textarea.textarea:focus {
    border-color: #00995D !important;
    box-shadow: 0 0 0 3px rgba(0,153,93,0.1) !important;
    outline: none;
}
.t-Form-label { font-weight: 600 !important; color: #333333 !important; font-size: 13px !important; }
.t-Form-fieldContainer.is-required .t-Form-label::after { content: " *"; color: #E53935; font-weight: 700; }
.t-Form-fieldContainer.has-error .apex-item-text,
.t-Form-fieldContainer.has-error .apex-item-select {
    border-color: #E53935 !important;
    box-shadow: 0 0 0 3px rgba(229,57,53,0.1) !important;
}

/* 8. WIZARD */
.t-WizardSteps-step.is-active .t-WizardSteps-marker {
    background-color: #00995D !important; color: #FFFFFF !important;
    box-shadow: 0 2px 8px rgba(0,153,93,0.4);
}
.t-WizardSteps-step.is-complete .t-WizardSteps-marker { background-color: #43A047 !important; color: #FFFFFF !important; }
.t-WizardSteps-step.is-active .t-WizardSteps-label { color: #00995D !important; font-weight: 700; }
.t-WizardSteps-step.is-complete .t-WizardSteps-label { color: #43A047; }
.t-Wizard-footer .t-Button--hot { background-color: #00995D !important; border-color: #00995D !important; }
.t-Wizard-footer .t-Button--hot:hover { background-color: #006B3F !important; border-color: #006B3F !important; }

/* 9. CARDS */
.t-Cards .t-Card {
    border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    border-left: 4px solid #00995D; transition: all 0.2s;
}
.t-Cards .t-Card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.12); transform: translateY(-2px); }
.t-Cards .t-Card-titleWrap .t-Card-title { color: #333333; font-weight: 700; }

/* 10. CHARTS (Oracle JET) */
.oj-chart {
    --oj-chart-series-color-ramp: #00995D #43A047 #66BB6A #A5D6A7 #006B3F
                                   #1E88E5 #42A5F5 #FF9800 #FFB74D #E53935;
}

/* 11. ALERTAS */
.t-Alert--success { background-color: #E8F5E9 !important; border-left: 4px solid #43A047 !important; }
.t-Alert--warning { background-color: #FFF3E0 !important; border-left: 4px solid #FF9800 !important; }
.t-Alert--danger  { background-color: #FFEBEE !important; border-left: 4px solid #E53935 !important; }

/* 12. BREADCRUMB */
.t-Breadcrumb-item a { color: #00995D !important; }
.t-Breadcrumb-item a:hover { color: #006B3F !important; }

/* 13. BADGES DE STATUS */
.u-color-ok       { background-color: #E8F5E9 !important; color: #2E7D32 !important;
                    padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
.u-color-pendente { background-color: #FFF3E0 !important; color: #E65100 !important;
                    padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
.u-color-erro     { background-color: #FFEBEE !important; color: #C62828 !important;
                    padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }

/* 14. LOGIN PAGE */
.t-Login-container {
    background: linear-gradient(135deg, #00995D 0%, #006B3F 100%) !important;
}
.t-Login .t-Button--hot { background-color: #006B3F !important; width: 100%; padding: 14px; font-size: 16px; }

/* 15. MENU DROPDOWN */
.a-Menu-item.is-focused > .a-Menu-inner,
.a-Menu-content .a-Menu-item:hover > .a-Menu-inner {
    background-color: #00995D !important; color: #FFFFFF !important;
}

/* 16. FILTROS IRR — remover azul padrão */
.a-IRR-controls .a-IRR-controlsIcon,
.a-IRR-controls .a-Icon.icon-irr-search,
.a-IRR-controlsIcon.icon-irr-search {
    background-color: #00995D !important; color: #FFFFFF !important; border: none !important;
}
.a-IRR-controlsCheckbox:checked + .a-IRR-controlsLabel::before,
.a-IRR-controlsCheckbox:checked + .a-IRR-controlsCheckboxLabel::before {
    background-color: #00995D !important; border-color: #006B3F !important;
}
#apex_search:focus, .a-IRR-searchField:focus {
    border-color: #00995D !important; box-shadow: 0 0 0 1px #00995D !important;
}

/* 17. ACESSIBILIDADE */
*:focus-visible { outline: 3px solid #00995D !important; outline-offset: 2px; }

/* 18. RESPONSIVIDADE */
@media (max-width: 992px) {
    .t-Button--hot { padding: 14px 20px !important; font-size: 16px !important; }
    .apex-item-text, .apex-item-select { padding: 12px 16px !important; font-size: 16px !important; }
    input[type="radio"], input[type="checkbox"] { width: 22px !important; height: 22px !important; }
}
""".strip()
