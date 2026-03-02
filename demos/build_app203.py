"""Build App 203 — Painel Analytics TEA (visuais modernos com JET charts + metric cards)."""
import os, json, sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

os.environ.update({
    "ORACLE_DB_USER": "TEA_APP", "ORACLE_DB_PASS": "TeaApp@2024#Unimed",
    "ORACLE_DSN": "u5cvlivnjuodscai_tp",
    "ORACLE_WALLET_DIR": r"C:\Projetos\Apex\wallet",
    "ORACLE_WALLET_PASSWORD": "apex1234",
    "APEX_WORKSPACE_ID": "8822816515098715",
    "APEX_SCHEMA": "TEA_APP", "APEX_WORKSPACE_NAME": "TEA",
})

sys.path.insert(0, r"C:\Projetos\Apex\mcp-server")

from apex_mcp.tools.sql_tools import apex_connect
from apex_mcp.tools.app_tools import apex_create_app, apex_finalize_app
from apex_mcp.tools.page_tools import apex_add_page
from apex_mcp.tools.generator_tools import apex_generate_login
from apex_mcp.tools.visual_tools import apex_add_jet_chart, apex_add_metric_cards, apex_generate_analytics_page
from apex_mcp.tools.shared_tools import apex_add_nav_item


def ok(label, result_str):
    r = json.loads(result_str)
    if r.get("status") == "error":
        print(f"  ❌ {label}: {r['error']}")
        return False, r
    print(f"  ✓  {label}")
    return True, r


def run():
    print("\n══════════════════════════════════════════════════")
    print("  APP 203 — Painel Analytics TEA (visuais modernos)")
    print("══════════════════════════════════════════════════")

    print("\n[1] Conectando...")
    if not ok("apex_connect", apex_connect())[0]: return

    print("\n[2] Criando aplicação 203...")
    ok_flag, _ = ok("apex_create_app", apex_create_app(
        app_id=203, app_name="Analytics TEA",
        app_alias="analytics-tea", login_page=101, home_page=1,
        language="pt-br", date_format="DD/MM/YYYY"
    ))
    if not ok_flag: return

    print("\n[3] Login page 101...")
    if not ok("apex_generate_login", apex_generate_login(101))[0]: return

    # ─── Página 1: Overview com Metric Cards (gradient) + JET Charts ──────────
    print("\n[4] Página 1 — Overview com metric cards gradiente...")
    if not ok("apex_add_page(1)", apex_add_page(1, "Overview", "blank"))[0]: return

    ok_flag, _ = ok("apex_add_metric_cards(gradient)", apex_add_metric_cards(
        page_id=1,
        region_name="Indicadores TEA",
        sequence=10,
        columns=4,
        style="gradient",
        metrics=[
            {
                "label": "Beneficiários Ativos",
                "sql": "SELECT COUNT(*) FROM TEA_BENEFICIARIOS WHERE FL_ATIVO='S'",
                "icon": "fa-users",
                "color": "blue",
            },
            {
                "label": "Avaliações Concluídas",
                "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA'",
                "icon": "fa-check-circle",
                "color": "green",
            },
            {
                "label": "Em Andamento",
                "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='EM_ANDAMENTO'",
                "icon": "fa-spinner",
                "color": "orange",
            },
            {
                "label": "Média Score (%)",
                "sql": "SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL > 0",
                "icon": "fa-bar-chart",
                "color": "purple",
                "suffix": "%",
            },
        ],
    ))
    if not ok_flag: return

    # JET Bar chart: Avaliações por Status
    ok_flag, _ = ok("apex_add_jet_chart(bar: status)", apex_add_jet_chart(
        page_id=1,
        region_name="Avaliações por Status",
        chart_type="bar",
        sql_query=(
            "SELECT DS_STATUS AS LABEL, COUNT(*) AS VALUE "
            "FROM TEA_AVALIACOES "
            "GROUP BY DS_STATUS ORDER BY 1"
        ),
        label_column="LABEL",
        value_column="VALUE",
        series_name="Qtd. Avaliações",
        height=350,
        y_axis_title="Quantidade",
        x_axis_title="Status",
        sequence=20,
    ))
    if not ok_flag: return

    # JET Pie chart: Distribuição por Clínica
    ok_flag, _ = ok("apex_add_jet_chart(pie: clínicas)", apex_add_jet_chart(
        page_id=1,
        region_name="Distribuição por Clínica",
        chart_type="pie",
        sql_query=(
            "SELECT c.DS_NOME AS LABEL, COUNT(a.ID_AVALIACAO) AS VALUE "
            "FROM TEA_CLINICAS c "
            "LEFT JOIN TEA_TERAPEUTAS t ON t.ID_CLINICA = c.ID_CLINICA "
            "LEFT JOIN TEA_AVALIACOES a ON a.ID_TERAPEUTA = t.ID_TERAPEUTA "
            "GROUP BY c.DS_NOME ORDER BY 2 DESC "
            "FETCH FIRST 6 ROWS ONLY"
        ),
        label_column="LABEL",
        value_column="VALUE",
        series_name="Avaliações",
        height=350,
        legend_position="end",
        sequence=30,
    ))
    if not ok_flag: return

    # ─── Página 2: Tendências com Line/Area Charts ─────────────────────────────
    print("\n[5] Página 2 — Tendências com line/area charts...")
    if not ok("apex_add_page(2)", apex_add_page(2, "Tendências", "blank"))[0]: return

    ok_flag, _ = ok("apex_add_metric_cards(white)", apex_add_metric_cards(
        page_id=2,
        region_name="KPIs Tendências",
        sequence=10,
        columns=4,
        style="white",
        metrics=[
            {
                "label": "Clínicas Ativas",
                "sql": "SELECT COUNT(*) FROM TEA_CLINICAS WHERE FL_ATIVO='S'",
                "icon": "fa-hospital-o",
                "color": "teal",
            },
            {
                "label": "Terapeutas",
                "sql": "SELECT COUNT(*) FROM TEA_TERAPEUTAS WHERE FL_ATIVO='S'",
                "icon": "fa-user-md",
                "color": "indigo",
            },
            {
                "label": "Total Avaliações",
                "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES",
                "icon": "fa-clipboard",
                "color": "orange",
            },
            {
                "label": "Score Máximo (%)",
                "sql": "SELECT MAX(NR_PCT_TOTAL) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL > 0",
                "icon": "fa-trophy",
                "color": "amber",
                "suffix": "%",
            },
        ],
    ))
    if not ok_flag: return

    # Line chart: avaliações por terapeuta (top 8)
    ok_flag, _ = ok("apex_add_jet_chart(bar_horizontal: terapeutas)", apex_add_jet_chart(
        page_id=2,
        region_name="Top Terapeutas por Avaliações",
        chart_type="bar_horizontal",
        sql_query=(
            "SELECT t.DS_NOME AS LABEL, COUNT(a.ID_AVALIACAO) AS VALUE "
            "FROM TEA_TERAPEUTAS t "
            "LEFT JOIN TEA_AVALIACOES a ON a.ID_TERAPEUTA = t.ID_TERAPEUTA "
            "GROUP BY t.DS_NOME ORDER BY 2 DESC "
            "FETCH FIRST 8 ROWS ONLY"
        ),
        label_column="LABEL",
        value_column="VALUE",
        series_name="Avaliações",
        height=380,
        x_axis_title="Quantidade",
        sequence=20,
    ))
    if not ok_flag: return

    # Donut chart: beneficiários por faixa etária
    ok_flag, _ = ok("apex_add_jet_chart(donut: faixa etária)", apex_add_jet_chart(
        page_id=2,
        region_name="Beneficiários por Faixa Etária",
        chart_type="donut",
        sql_query=(
            "SELECT "
            "  CASE "
            "    WHEN MONTHS_BETWEEN(SYSDATE, DT_NASCIMENTO)/12 < 6  THEN '0-5 anos' "
            "    WHEN MONTHS_BETWEEN(SYSDATE, DT_NASCIMENTO)/12 < 12 THEN '6-11 anos' "
            "    WHEN MONTHS_BETWEEN(SYSDATE, DT_NASCIMENTO)/12 < 18 THEN '12-17 anos' "
            "    ELSE '18+ anos' "
            "  END AS LABEL, "
            "  COUNT(*) AS VALUE "
            "FROM TEA_BENEFICIARIOS "
            "WHERE FL_ATIVO='S' "
            "GROUP BY "
            "  CASE "
            "    WHEN MONTHS_BETWEEN(SYSDATE, DT_NASCIMENTO)/12 < 6  THEN '0-5 anos' "
            "    WHEN MONTHS_BETWEEN(SYSDATE, DT_NASCIMENTO)/12 < 12 THEN '6-11 anos' "
            "    WHEN MONTHS_BETWEEN(SYSDATE, DT_NASCIMENTO)/12 < 18 THEN '12-17 anos' "
            "    ELSE '18+ anos' "
            "  END "
            "ORDER BY 1"
        ),
        label_column="LABEL",
        value_column="VALUE",
        series_name="Beneficiários",
        height=350,
        sequence=30,
    ))
    if not ok_flag: return

    # ─── Página 3: Analytics gerada pelo apex_generate_analytics_page ─────────
    print("\n[6] Página 3 — Analytics completa (apex_generate_analytics_page)...")
    ok_flag, _ = ok("apex_generate_analytics_page", apex_generate_analytics_page(
        page_id=3,
        page_name="Analytics Completa",
        metrics=[
            {
                "label": "Avaliações Rascunho",
                "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='RASCUNHO'",
                "icon": "fa-pencil",
                "color": "indigo",
            },
            {
                "label": "Canceladas",
                "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CANCELADA'",
                "icon": "fa-times-circle",
                "color": "red",
            },
            {
                "label": "Instrumentos",
                "sql": "SELECT COUNT(*) FROM TEA_PROVAS",
                "icon": "fa-list-alt",
                "color": "teal",
            },
            {
                "label": "Usuários Ativos",
                "sql": "SELECT COUNT(*) FROM TEA_USUARIOS WHERE FL_ATIVO='S'",
                "icon": "fa-user-circle",
                "color": "blue",
            },
        ],
        charts=[
            {
                "region_name": "Avaliações por Prova (Instrumento)",
                "chart_type": "bar",
                "sql_query": (
                    "SELECT p.DS_NOME AS LABEL, COUNT(a.ID_AVALIACAO) AS VALUE "
                    "FROM TEA_PROVAS p "
                    "LEFT JOIN TEA_AVALIACOES a ON a.ID_PROVA = p.ID_PROVA "
                    "GROUP BY p.DS_NOME ORDER BY 2 DESC"
                ),
                "series_name": "Avaliações",
                "height": 380,
                "y_axis_title": "Quantidade",
            },
            {
                "region_name": "Status das Avaliações",
                "chart_type": "donut",
                "sql_query": (
                    "SELECT DS_STATUS AS LABEL, COUNT(*) AS VALUE "
                    "FROM TEA_AVALIACOES GROUP BY DS_STATUS ORDER BY 1"
                ),
                "series_name": "Avaliações",
                "height": 380,
                "legend_position": "end",
            },
        ],
    ))
    if not ok_flag: return

    # ─── Navegação ─────────────────────────────────────────────────────────────
    print("\n[7] Navegação...")
    if not ok("nav: Overview",    apex_add_nav_item("Overview",    1, 10, "fa-home"))[0]: return
    if not ok("nav: Tendências",  apex_add_nav_item("Tendências",  2, 20, "fa-line-chart"))[0]: return
    if not ok("nav: Analytics",   apex_add_nav_item("Analytics",   3, 30, "fa-pie-chart"))[0]: return

    # ─── Finalizar ─────────────────────────────────────────────────────────────
    print("\n[8] Finalizando...")
    r = apex_finalize_app()
    rj = json.loads(r)
    if rj.get("status") == "error":
        print(f"  ❌ apex_finalize_app: {rj['error']}")
        return
    print(f"  ✓  apex_finalize_app → URL: {rj.get('apex_url')}")
    summary = rj.get("summary", {})
    print(f"\n  App 203 criado com sucesso!")
    print(f"  Páginas: {summary.get('pages')}  Regiões: {summary.get('regions')}  Itens: {summary.get('items')}")
    print("\n  Visuais criados:")
    print("  • Página 1: 4 metric cards (gradient) + bar chart + pie chart")
    print("  • Página 2: 4 metric cards (white) + bar horizontal + donut chart")
    print("  • Página 3: 4 metric cards (auto) + bar chart + donut chart (via generate_analytics_page)")


if __name__ == "__main__":
    run()
