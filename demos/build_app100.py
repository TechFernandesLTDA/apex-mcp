"""Build App 100 — Plataforma Desfecho TEA (aplicação principal).

Páginas criadas:
  100  Login customizado (público)
    1  Dashboard — indicadores + JET charts
  10/11  Beneficiários (IR + Form)
  20/21  Clínicas (IR + Form) — ADM only
  30/31  Terapeutas (IR + Form) — ADM + CLINICA
   50  Nova Avaliação TEA (form + AJAX auto-save)
   60  Dashboard por Clínica (JET charts) — ADM + CLINICA
   61  Dashboard por Beneficiário (evolution charts)
   70  Configurações do Sistema — ADM only
  101  Gestão de Usuários — ADM only
  102  Chat Assistente IA (AJAX + inline chat UI)
"""
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

from apex_mcp.tools.sql_tools      import apex_connect
from apex_mcp.tools.app_tools      import apex_create_app, apex_finalize_app
from apex_mcp.tools.page_tools     import apex_add_page
from apex_mcp.tools.component_tools import apex_add_region, apex_add_item, apex_add_button, apex_add_process, apex_add_dynamic_action
from apex_mcp.tools.shared_tools   import apex_add_auth_scheme, apex_add_nav_item, apex_add_app_item, apex_add_app_process
from apex_mcp.tools.generator_tools import apex_generate_login, apex_generate_crud
from apex_mcp.tools.visual_tools   import apex_add_metric_cards, apex_add_jet_chart, apex_generate_analytics_page
from apex_mcp.tools.validation_tools import apex_add_item_validation
from apex_mcp.tools.js_tools       import apex_add_page_js, apex_generate_ajax_handler
from apex_mcp.tools.ui_tools       import apex_add_stat_delta, apex_add_leaderboard, apex_add_percent_bars, apex_add_ribbon_stats
from apex_mcp.tools.chart_tools    import apex_add_pareto_chart, apex_add_animated_counter


def ok(label, result_str):
    r = json.loads(result_str)
    if r.get("status") == "error":
        print(f"  ❌ {label}: {r['error']}")
        return False, r
    print(f"  ✓  {label}")
    return True, r


def run():
    print("\n" + "═"*60)
    print("  APP 100 — Plataforma Desfecho TEA (Unimed Nacional)")
    print("═"*60)

    # ── 1. Conexão ────────────────────────────────────────────────────────────
    print("\n[1] Conectando...")
    if not ok("apex_connect", apex_connect())[0]: return

    # ── 2. Criar Aplicação ────────────────────────────────────────────────────
    print("\n[2] Criando aplicação 100...")
    if not ok("apex_create_app", apex_create_app(
        app_id=100,
        app_name="Desfecho TEA — Unimed Nacional",
        app_alias="tea-desfecho",
        login_page=100,
        home_page=1,
        language="pt-br",
        date_format="DD/MM/YYYY",
    ))[0]: return

    # ── 3. Authorization Schemes ──────────────────────────────────────────────
    print("\n[3] Authorization schemes...")

    # IS_ADM: apenas perfil ADM
    if not ok("auth: IS_ADM", apex_add_auth_scheme(
        scheme_name="IS_ADM",
        function_body="""DECLARE l_count NUMBER;
BEGIN
  SELECT COUNT(*) INTO l_count
    FROM TEA_USUARIOS u
    JOIN TEA_PERFIS p ON p.ID_PERFIL = u.ID_PERFIL
   WHERE UPPER(u.DS_LOGIN) = UPPER(:APP_USER)
     AND p.DS_PERFIL = 'ADM'
     AND u.FL_ATIVO = 'S';
  RETURN l_count > 0;
END;""",
        error_message="Acesso restrito a administradores.",
    ))[0]: return

    # IS_CLINICA: ADM ou CLINICA
    if not ok("auth: IS_CLINICA", apex_add_auth_scheme(
        scheme_name="IS_CLINICA",
        function_body="""DECLARE l_count NUMBER;
BEGIN
  SELECT COUNT(*) INTO l_count
    FROM TEA_USUARIOS u
    JOIN TEA_PERFIS p ON p.ID_PERFIL = u.ID_PERFIL
   WHERE UPPER(u.DS_LOGIN) = UPPER(:APP_USER)
     AND p.DS_PERFIL IN ('ADM','CLINICA')
     AND u.FL_ATIVO = 'S';
  RETURN l_count > 0;
END;""",
        error_message="Acesso restrito a gestores de clínica.",
    ))[0]: return

    # IS_TERAPEUTA: todos os perfis autenticados
    if not ok("auth: IS_TERAPEUTA", apex_add_auth_scheme(
        scheme_name="IS_TERAPEUTA",
        function_body="""DECLARE l_count NUMBER;
BEGIN
  SELECT COUNT(*) INTO l_count
    FROM TEA_USUARIOS u
   WHERE UPPER(u.DS_LOGIN) = UPPER(:APP_USER)
     AND u.FL_ATIVO = 'S';
  RETURN l_count > 0;
END;""",
        error_message="Acesso negado.",
    ))[0]: return

    # ── 4. Login (page 100) ───────────────────────────────────────────────────
    print("\n[4] Login page 100...")
    if not ok("apex_generate_login(100)", apex_generate_login(
        page_id=100,
        app_name="Desfecho TEA",
    ))[0]: return

    # ── 5. Dashboard — page 1 ─────────────────────────────────────────────────
    print("\n[5] Dashboard — page 1...")
    if not ok("apex_add_page(1)", apex_add_page(1, "Dashboard", "blank"))[0]: return

    if not ok("metric_cards: KPIs principais", apex_add_metric_cards(
        page_id=1,
        region_name="Indicadores Principais",
        sequence=10,
        columns=4,
        style="gradient",
        metrics=[
            {"label": "Beneficiários Ativos",    "sql": "SELECT COUNT(*) FROM TEA_BENEFICIARIOS WHERE FL_ATIVO='S'",                    "icon": "fa-users",        "color": "blue",   "link_page": 10},
            {"label": "Avaliações Concluídas",    "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA'",              "icon": "fa-check-circle", "color": "green",  "link_page": 10},
            {"label": "Em Andamento",             "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='EM_ANDAMENTO'",           "icon": "fa-spinner",      "color": "orange"},
            {"label": "Média Score (%)",          "sql": "SELECT ROUND(AVG(NR_PCT_TOTAL),1) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL > 0", "icon": "fa-bar-chart",    "color": "purple", "suffix": "%"},
        ],
    ))[0]: return

    if not ok("metric_cards: operacional", apex_add_metric_cards(
        page_id=1,
        region_name="Indicadores Operacionais",
        sequence=15,
        columns=4,
        style="white",
        metrics=[
            {"label": "Clínicas Ativas",     "sql": "SELECT COUNT(*) FROM TEA_CLINICAS WHERE FL_ATIVO='S'",          "icon": "fa-hospital-o",  "color": "teal"},
            {"label": "Terapeutas Ativos",   "sql": "SELECT COUNT(*) FROM TEA_TERAPEUTAS WHERE FL_ATIVO='S'",         "icon": "fa-user-md",     "color": "indigo"},
            {"label": "Instrumentos",        "sql": "SELECT COUNT(*) FROM TEA_PROVAS WHERE FL_ATIVO='S'",             "icon": "fa-list-alt",    "color": "orange"},
            {"label": "Usuários do Sistema", "sql": "SELECT COUNT(*) FROM TEA_USUARIOS WHERE FL_ATIVO='S'",           "icon": "fa-user-circle", "color": "blue"},
        ],
    ))[0]: return

    if not ok("chart: avaliações por status (bar)", apex_add_jet_chart(
        page_id=1,
        region_name="Avaliações por Status",
        chart_type="bar",
        sql_query="SELECT DS_STATUS AS LABEL, COUNT(*) AS VALUE FROM TEA_AVALIACOES GROUP BY DS_STATUS ORDER BY 2 DESC",
        series_name="Quantidade",
        height=320,
        y_axis_title="Qtd",
        sequence=20,
    ))[0]: return

    if not ok("chart: distribuição por clínica (pie)", apex_add_jet_chart(
        page_id=1,
        region_name="Avaliações por Clínica",
        chart_type="pie",
        sql_query=(
            "SELECT c.DS_NOME AS LABEL, COUNT(a.ID_AVALIACAO) AS VALUE "
            "FROM TEA_CLINICAS c "
            "LEFT JOIN TEA_AVALIACOES a ON a.ID_CLINICA = c.ID_CLINICA "
            "WHERE c.FL_ATIVO='S' GROUP BY c.DS_NOME ORDER BY 2 DESC "
            "FETCH FIRST 8 ROWS ONLY"
        ),
        series_name="Avaliações",
        height=320,
        legend_position="end",
        sequence=30,
    ))[0]: return

    # Stat delta — variação vs. mês anterior
    ok("stat_delta: variação mensal", apex_add_stat_delta(
        page_id=1,
        region_name="Variação Mensal",
        sequence=40,
        columns=4,
        metrics=[
            {
                "label": "Beneficiários", "icon": "fa-users", "color": "blue",
                "sql": "SELECT COUNT(*) FROM TEA_BENEFICIARIOS WHERE FL_ATIVO='S'",
                "prev_sql": "SELECT COUNT(*) FROM TEA_BENEFICIARIOS WHERE FL_ATIVO='S' AND DT_CRIACAO < TRUNC(SYSDATE,'MM')",
            },
            {
                "label": "Avaliações Concluídas", "icon": "fa-check-circle", "color": "green",
                "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA'",
                "prev_sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA' AND DT_AVALIACAO < TRUNC(SYSDATE,'MM')",
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
    ))

    # Ribbon stats — resumo compacto
    ok("ribbon_stats: resumo sistema", apex_add_ribbon_stats(
        page_id=1,
        region_name="Resumo do Sistema",
        sequence=50,
        metrics=[
            {"label": "Avaliações",   "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES",                                  "icon": "fa-clipboard",    "color": "blue"},
            {"label": "Concluídas",   "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA'",       "icon": "fa-check-circle", "color": "green"},
            {"label": "Em Andamento", "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='EM_ANDAMENTO'",    "icon": "fa-spinner",      "color": "orange"},
            {"label": "Clínicas",     "sql": "SELECT COUNT(*) FROM TEA_CLINICAS WHERE FL_ATIVO='S'",                  "icon": "fa-hospital-o",   "color": "teal"},
            {"label": "Terapeutas",   "sql": "SELECT COUNT(*) FROM TEA_TERAPEUTAS WHERE FL_ATIVO='S'",                "icon": "fa-user-md",      "color": "indigo"},
        ],
    ))

    # ── 6. Beneficiários — pages 10/11 ────────────────────────────────────────
    print("\n[6] CRUD Beneficiários — pages 10/11...")
    if not ok("apex_generate_crud(TEA_BENEFICIARIOS)", apex_generate_crud(
        "TEA_BENEFICIARIOS", 10, 11,
    ))[0]: return

    # Validações no form de beneficiários
    ok("val: NR_BENEFICIO obrigatório", apex_add_item_validation(
        11, "NR_BENEFICIO", "Número de Benefício Obrigatório", "not_null"))
    ok("val: DS_NOME obrigatório", apex_add_item_validation(
        11, "DS_NOME", "Nome do Beneficiário Obrigatório", "not_null"))
    ok("val: NR_BENEFICIO formato", apex_add_item_validation(
        11, "NR_BENEFICIO", "Formato do Benefício Inválido",
        "regex",
        validation_expression=r"^[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]$",
        error_message="Use o formato: 000.000.000-0"))

    # ── 7. Clínicas — pages 20/21 (IS_ADM) ────────────────────────────────────
    print("\n[7] CRUD Clínicas — pages 20/21 (IS_ADM)...")
    if not ok("apex_generate_crud(TEA_CLINICAS)", apex_generate_crud(
        "TEA_CLINICAS", 20, 21, auth_scheme="IS_ADM",
    ))[0]: return

    # ── 8. Terapeutas — pages 30/31 (IS_CLINICA) ──────────────────────────────
    print("\n[8] CRUD Terapeutas — pages 30/31 (IS_CLINICA)...")
    if not ok("apex_generate_crud(TEA_TERAPEUTAS)", apex_generate_crud(
        "TEA_TERAPEUTAS", 30, 31, auth_scheme="IS_CLINICA",
    ))[0]: return

    # ── 9. Nova Avaliação — page 50 ───────────────────────────────────────────
    print("\n[9] Nova Avaliação — page 50...")
    if not ok("apex_add_page(50)", apex_add_page(50, "Nova Avaliação TEA", "blank"))[0]: return

    ok("region: cabeçalho avaliação", apex_add_region(
        50, "Dados da Avaliação", "form",
        source_sql=(
            "SELECT ID_AVALIACAO, ID_BENEFICIARIO, ID_PROVA, ID_TERAPEUTA, "
            "DT_AVALIACAO, DS_STATUS, DS_OBSERVACOES "
            "FROM TEA_AVALIACOES WHERE ID_AVALIACAO = :P50_ID_AVALIACAO"
        ),
        sequence=10,
    ))

    # Items do form
    ok("item: P50_ID_AVALIACAO (hidden)", apex_add_item(
        50, "Dados da Avaliação", "P50_ID_AVALIACAO", "hidden"))
    ok("item: P50_ID_BENEFICIARIO (select)", apex_add_item(
        50, "Dados da Avaliação", "P50_ID_BENEFICIARIO", "select",
        label="Beneficiário",
        lov_name="SELECT DS_NOME d, ID_BENEFICIARIO r FROM TEA_BENEFICIARIOS WHERE FL_ATIVO='S' ORDER BY DS_NOME",
        is_required=True))
    ok("item: P50_ID_PROVA (select)", apex_add_item(
        50, "Dados da Avaliação", "P50_ID_PROVA", "select",
        label="Instrumento (Prova)",
        lov_name="SELECT DS_NOME d, ID_PROVA r FROM TEA_PROVAS WHERE FL_ATIVO='S' ORDER BY NR_ORDEM",
        is_required=True))
    ok("item: P50_DT_AVALIACAO (date)", apex_add_item(
        50, "Dados da Avaliação", "P50_DT_AVALIACAO", "date",
        label="Data da Avaliação", is_required=True))
    ok("item: P50_DS_OBSERVACOES (textarea)", apex_add_item(
        50, "Dados da Avaliação", "P50_DS_OBSERVACOES", "textarea",
        label="Observações"))

    ok("btn: Iniciar Avaliação", apex_add_button(
        50, "Dados da Avaliação", "INICIAR",
        label="Iniciar Avaliação", action="submit",
        hot=True, position="BELOW_BOX",
    ))
    ok("btn: Cancelar", apex_add_button(
        50, "Dados da Avaliação", "CANCELAR",
        label="Cancelar", action="redirect",
        url="f?p=&APP_ID.:10:&SESSION..",
        position="BELOW_BOX",
    ))

    # Process: criar avaliação no banco
    ok("process: CRIAR_AVALIACAO", apex_add_process(
        page_id=50,
        process_name="Criar Avaliação",
        process_type="plsql",
        source="""DECLARE
  l_id TEA_AVALIACOES.ID_AVALIACAO%TYPE;
BEGIN
  INSERT INTO TEA_AVALIACOES (
    ID_BENEFICIARIO, ID_PROVA, ID_TERAPEUTA, ID_CLINICA,
    DT_AVALIACAO, DS_STATUS, NR_COLETA, FL_TERMO_ACEITO
  )
  SELECT
    :P50_ID_BENEFICIARIO,
    :P50_ID_PROVA,
    t.ID_TERAPEUTA,
    t.ID_CLINICA,
    TO_DATE(:P50_DT_AVALIACAO,'DD/MM/YYYY'),
    'RASCUNHO',
    NVL((SELECT MAX(NR_COLETA)+1 FROM TEA_AVALIACOES WHERE ID_BENEFICIARIO=:P50_ID_BENEFICIARIO),1),
    'N'
  FROM TEA_TERAPEUTAS t
  JOIN TEA_USUARIOS u ON u.ID_USUARIO = t.ID_USUARIO
  WHERE UPPER(u.DS_LOGIN) = UPPER(:APP_USER)
  FETCH FIRST 1 ROW ONLY;
  l_id := TEA_AVALIACAO_SEQ.CURRVAL;
  :P50_ID_AVALIACAO := l_id;
  APEX_APPLICATION.G_PRINT_SUCCESS_MESSAGE := 'Avaliação criada! ID: '||l_id;
END;""",
        condition_button="INICIAR",
        sequence=10,
    ))

    # Validações page 50
    ok("val: beneficiário obrigatório", apex_add_item_validation(
        50, "ID_BENEFICIARIO", "Beneficiário Obrigatório", "not_null"))
    ok("val: instrumento obrigatório", apex_add_item_validation(
        50, "ID_PROVA", "Instrumento Obrigatório", "not_null"))
    ok("val: data obrigatória", apex_add_item_validation(
        50, "DT_AVALIACAO", "Data da Avaliação Obrigatória", "not_null"))

    # AJAX auto-save para respostas
    ok("ajax: SALVAR_RESPOSTA", apex_generate_ajax_handler(
        page_id=50,
        callback_name="SALVAR_RESPOSTA",
        plsql_code="""DECLARE
  l_id_avaliacao  NUMBER := TO_NUMBER(:P50_ID_AVALIACAO);
  l_id_questao    NUMBER := TO_NUMBER(apex_application.g_x01);
  l_nr_resposta   NUMBER := TO_NUMBER(apex_application.g_x02);
BEGIN
  MERGE INTO TEA_AVALIACAO_ITENS tgt
  USING (SELECT l_id_avaliacao AS ID_AVALIACAO, l_id_questao AS ID_QUESTAO FROM DUAL) src
  ON (tgt.ID_AVALIACAO = src.ID_AVALIACAO AND tgt.ID_QUESTAO = src.ID_QUESTAO)
  WHEN MATCHED THEN
    UPDATE SET NR_RESPOSTA = l_nr_resposta, DT_ATUALIZACAO = SYSTIMESTAMP
  WHEN NOT MATCHED THEN
    INSERT (ID_AVALIACAO, ID_QUESTAO, NR_RESPOSTA, DT_CRIACAO)
    VALUES (l_id_avaliacao, l_id_questao, l_nr_resposta, SYSTIMESTAMP);
  apex_json.open_object;
  apex_json.write('status','ok');
  apex_json.write('saved', l_id_questao);
  apex_json.close_object;
END;""",
        input_items=["P50_ID_AVALIACAO"],
        return_json=True,
        auto_add_js=True,
    ))

    # ── 10. Dashboard por Clínica — page 60 ───────────────────────────────────
    print("\n[10] Dashboard por Clínica — page 60 (IS_CLINICA)...")
    ok_flag, _ = ok("apex_generate_analytics_page(60)", apex_generate_analytics_page(
        page_id=60,
        page_name="Dashboard por Clínica",
        auth_scheme="IS_CLINICA",
        metrics=[
            {"label": "Clínicas",          "sql": "SELECT COUNT(*) FROM TEA_CLINICAS WHERE FL_ATIVO='S'",            "icon": "fa-hospital-o", "color": "teal"},
            {"label": "Terapeutas",        "sql": "SELECT COUNT(*) FROM TEA_TERAPEUTAS WHERE FL_ATIVO='S'",           "icon": "fa-user-md",    "color": "blue"},
            {"label": "Beneficiários",     "sql": "SELECT COUNT(*) FROM TEA_BENEFICIARIOS WHERE FL_ATIVO='S'",        "icon": "fa-users",      "color": "green"},
            {"label": "Avaliações/Clínica","sql": "SELECT ROUND(AVG(cnt)) FROM (SELECT ID_CLINICA, COUNT(*) cnt FROM TEA_AVALIACOES GROUP BY ID_CLINICA)", "icon": "fa-bar-chart", "color": "orange"},
        ],
        charts=[
            {
                "region_name": "Avaliações por Clínica",
                "chart_type": "bar",
                "sql_query": (
                    "SELECT c.DS_NOME AS LABEL, COUNT(a.ID_AVALIACAO) AS VALUE "
                    "FROM TEA_CLINICAS c "
                    "LEFT JOIN TEA_AVALIACOES a ON a.ID_CLINICA = c.ID_CLINICA "
                    "WHERE c.FL_ATIVO='S' GROUP BY c.DS_NOME ORDER BY 2 DESC"
                ),
                "series_name": "Avaliações",
                "height": 380,
                "y_axis_title": "Quantidade",
            },
            {
                "region_name": "Score Médio por Clínica (%)",
                "chart_type": "bar_horizontal",
                "sql_query": (
                    "SELECT c.DS_NOME AS LABEL, ROUND(AVG(a.NR_PCT_TOTAL),1) AS VALUE "
                    "FROM TEA_CLINICAS c "
                    "JOIN TEA_AVALIACOES a ON a.ID_CLINICA = c.ID_CLINICA "
                    "WHERE a.NR_PCT_TOTAL > 0 GROUP BY c.DS_NOME ORDER BY 2 DESC"
                ),
                "series_name": "Score Médio (%)",
                "height": 380,
                "x_axis_title": "Score Médio (%)",
            },
        ],
    ))

    # Leaderboard — top clínicas por avaliações
    ok("leaderboard: top clínicas", apex_add_leaderboard(
        page_id=60,
        region_name="Ranking de Clínicas",
        sql_query=(
            "SELECT c.DS_NOME AS LABEL, COUNT(a.ID_AVALIACAO) AS VALUE "
            "FROM TEA_CLINICAS c "
            "LEFT JOIN TEA_AVALIACOES a ON a.ID_CLINICA = c.ID_CLINICA "
            "WHERE c.FL_ATIVO='S' GROUP BY c.DS_NOME ORDER BY 2 DESC"
        ),
        color="unimed",
        max_rows=8,
        sequence=40,
    ))

    # Percent bars — distribuição por status
    ok("percent_bars: status das avaliações", apex_add_percent_bars(
        page_id=60,
        region_name="Distribuição por Status",
        sql_query="SELECT DS_STATUS AS LABEL, COUNT(*) AS VALUE FROM TEA_AVALIACOES GROUP BY DS_STATUS ORDER BY 2 DESC",
        color="blue",
        sequence=50,
    ))

    # ── 11. Dashboard por Beneficiário — page 61 ──────────────────────────────
    print("\n[11] Dashboard por Beneficiário — page 61...")
    if not ok("apex_add_page(61)", apex_add_page(61, "Evolução do Beneficiário", "blank"))[0]: return

    ok("metric_cards: resumo beneficiário", apex_add_metric_cards(
        page_id=61,
        region_name="Resumo",
        sequence=10,
        columns=3,
        style="white",
        metrics=[
            {"label": "Total Avaliações",   "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES",         "icon": "fa-clipboard",    "color": "blue"},
            {"label": "Concluídas",         "sql": "SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA'", "icon": "fa-check", "color": "green"},
            {"label": "Score Máximo (%)",   "sql": "SELECT NVL(MAX(NR_PCT_TOTAL),0) FROM TEA_AVALIACOES WHERE NR_PCT_TOTAL>0", "icon": "fa-trophy", "color": "amber", "suffix": "%"},
        ],
    ))

    ok("chart: evolução scores (line)", apex_add_jet_chart(
        page_id=61,
        region_name="Evolução de Scores",
        chart_type="line",
        sql_query=(
            "SELECT TO_CHAR(DT_AVALIACAO,'DD/MM/YYYY') AS LABEL, "
            "NVL(NR_PCT_TOTAL,0) AS VALUE "
            "FROM TEA_AVALIACOES "
            "WHERE DS_STATUS='CONCLUIDA' "
            "ORDER BY DT_AVALIACAO"
        ),
        series_name="Score (%)",
        height=380,
        y_axis_title="Score (%)",
        x_axis_title="Data",
        sequence=20,
    ))

    ok("chart: avaliações por instrumento (donut)", apex_add_jet_chart(
        page_id=61,
        region_name="Por Instrumento",
        chart_type="donut",
        sql_query=(
            "SELECT p.DS_NOME AS LABEL, COUNT(a.ID_AVALIACAO) AS VALUE "
            "FROM TEA_PROVAS p "
            "LEFT JOIN TEA_AVALIACOES a ON a.ID_PROVA = p.ID_PROVA "
            "WHERE p.FL_ATIVO='S' GROUP BY p.DS_NOME"
        ),
        series_name="Avaliações",
        height=380,
        sequence=30,
    ))

    # Animated counter — total de avaliações concluídas
    ok("animated_counter: concluídas", apex_add_animated_counter(
        page_id=61,
        region_name="Total Concluídas",
        sql_query="SELECT COUNT(*) FROM TEA_AVALIACOES WHERE DS_STATUS='CONCLUIDA'",
        label="Avaliações Concluídas no Sistema",
        color="green",
        icon="fa-check-circle",
        sequence=40,
    ))

    # Pareto chart — avaliações por instrumento (análise 80/20)
    ok("pareto: avaliações por instrumento", apex_add_pareto_chart(
        page_id=61,
        region_name="Pareto — Avaliações por Instrumento",
        sql_query=(
            "SELECT p.DS_NOME AS LABEL, COUNT(a.ID_AVALIACAO) AS VALUE "
            "FROM TEA_PROVAS p "
            "LEFT JOIN TEA_AVALIACOES a ON a.ID_PROVA = p.ID_PROVA "
            "WHERE p.FL_ATIVO='S' GROUP BY p.DS_NOME ORDER BY 2 DESC"
        ),
        bar_name="Avaliações",
        line_name="Acumulado %",
        height=380,
        sequence=50,
    ))

    # ── 12. Configurações — page 70 ───────────────────────────────────────────
    print("\n[12] Configurações — page 70 (IS_ADM)...")
    if not ok("apex_add_page(70)", apex_add_page(70, "Configurações do Sistema", "blank", auth_scheme="IS_ADM"))[0]: return

    ok("region: parâmetros", apex_add_region(
        70, "Parâmetros do Sistema", "report",
        source_sql=(
            "SELECT DS_CHAVE AS \"Parâmetro\", "
            "DS_VALOR AS \"Valor\", "
            "TO_CHAR(DT_CRIACAO,'DD/MM/YYYY HH24:MI') AS \"Criado em\" "
            "FROM TEA_CONFIG ORDER BY DS_CHAVE"
        ),
        sequence=10,
    ))

    ok("region: provas (instrumentos)", apex_add_region(
        70, "Instrumentos Clínicos", "report",
        source_sql=(
            "SELECT DS_NOME AS \"Instrumento\", DS_VERSAO AS \"Versão\", "
            "DS_DESCRICAO AS \"Descrição\", "
            "DECODE(FL_ATIVO,'S','Ativo','Inativo') AS \"Status\" "
            "FROM TEA_PROVAS ORDER BY NR_ORDEM"
        ),
        sequence=20,
    ))

    # ── 13. Gestão de Usuários — page 101 ────────────────────────────────────
    print("\n[13] Gestão de Usuários — page 101 (IS_ADM)...")
    if not ok("apex_generate_crud(TEA_USUARIOS)", apex_generate_crud(
        "TEA_USUARIOS", 101, 102, auth_scheme="IS_ADM",
    ))[0]: return

    # ── 14. Chat IA — page 110 ────────────────────────────────────────────────
    print("\n[14] Chat Assistente IA — page 110...")
    if not ok("apex_add_page(110)", apex_add_page(110, "Assistente IA TEA", "blank"))[0]: return

    # Região do chat com HTML inline
    chat_html = """DECLARE
BEGIN
  sys.htp.p('<style>
    .tea-chat-wrap{display:flex;flex-direction:column;height:520px;border-radius:12px;
      overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.12);}
    .tea-chat-msgs{flex:1;overflow-y:auto;padding:20px;background:#f8fafc;display:flex;flex-direction:column;gap:12px;}
    .tea-msg{max-width:80%;padding:12px 16px;border-radius:12px;font-size:.92rem;line-height:1.5;}
    .tea-msg.user{align-self:flex-end;background:#00995D;color:#fff;border-bottom-right-radius:3px;}
    .tea-msg.bot{align-self:flex-start;background:#fff;color:#333;border:1px solid #e2e8f0;border-bottom-left-radius:3px;box-shadow:0 1px 4px rgba(0,0,0,.06);}
    .tea-msg.bot .tea-msg-lbl{font-size:.72rem;color:#00995D;font-weight:600;margin-bottom:4px;}
    .tea-chat-input{display:flex;gap:8px;padding:14px 16px;background:#fff;border-top:1px solid #e2e8f0;}
    .tea-chat-input textarea{flex:1;border:1px solid #e2e8f0;border-radius:8px;padding:10px 14px;
      font-size:.9rem;resize:none;outline:none;transition:border-color .2s;}
    .tea-chat-input textarea:focus{border-color:#00995D;}
    .tea-chat-input button{background:#00995D;color:#fff;border:none;border-radius:8px;
      padding:10px 20px;cursor:pointer;font-weight:600;transition:background .2s;}
    .tea-chat-input button:hover{background:#006B3F;}
    .tea-chat-input button:disabled{background:#94a3b8;cursor:not-allowed;}
    .tea-typing{color:#94a3b8;font-style:italic;font-size:.85rem;}
  </style>');
  sys.htp.p('<div class="tea-chat-wrap">');
  sys.htp.p('<div id="teaChatMsgs" class="tea-chat-msgs">');
  sys.htp.p('<div class="tea-msg bot"><div class="tea-msg-lbl">Assistente TEA</div>');
  sys.htp.p('Olá! Sou o assistente clínico da Plataforma Desfecho TEA. Posso responder perguntas sobre os pacientes, avaliações e instrumentos clínicos. Como posso ajudar?</div>');
  sys.htp.p('</div>');
  sys.htp.p('<div class="tea-chat-input">');
  sys.htp.p('<textarea id="teaChatQ" rows="2" placeholder="Digite sua pergunta sobre pacientes, avaliações ou instrumentos..."></textarea>');
  sys.htp.p('<button id="teaChatSend" onclick="teaChat()">Enviar</button>');
  sys.htp.p('</div>');
  sys.htp.p('</div>');
END;"""

    ok("region: chat UI", apex_add_region(
        110, "Assistente IA TEA", "plsql",
        source_sql=chat_html,
        sequence=10,
    ))

    # AJAX: perguntas ao Claude via PKG_CLAUDE_API
    ok("ajax: CHAT_IA", apex_generate_ajax_handler(
        page_id=110,
        callback_name="CHAT_IA",
        plsql_code="""DECLARE
  l_pergunta  VARCHAR2(4000) := apex_application.g_x01;
  l_resposta  VARCHAR2(32767);
BEGIN
  -- Tenta PKG_CLAUDE_API (requer contexto APEX com APEX_WEB_SERVICE)
  BEGIN
    l_resposta := PKG_CLAUDE_API.chat(
      p_mensagem => l_pergunta,
      p_sistema  => 'Você é o assistente clínico da Plataforma Desfecho TEA da Unimed Nacional. ' ||
                    'Responda em português. Foco em TEA, instrumentos VINELAND/CBCL/CFQL2/RBS-R, ' ||
                    'avaliações e suporte clínico. Seja conciso e profissional.'
    );
  EXCEPTION
    WHEN OTHERS THEN
      -- Fallback: resposta genérica
      l_resposta := 'Serviço de IA temporariamente indisponível. Por favor, tente novamente em alguns instantes. (' || SQLERRM || ')';
  END;
  apex_json.open_object;
  apex_json.write('status',   'ok');
  apex_json.write('resposta', l_resposta);
  apex_json.close_object;
END;""",
        input_items=[],
        return_json=True,
        auto_add_js=False,  # JS customizado abaixo
    ))

    # JS customizado do chat
    ok("page_js: chat controller", apex_add_page_js(
        page_id=110,
        javascript_code="""function teaChat() {
  var q = document.getElementById('teaChatQ').value.trim();
  if (!q) return;
  var msgs = document.getElementById('teaChatMsgs');
  var btn  = document.getElementById('teaChatSend');

  // Adiciona mensagem do usuário
  msgs.innerHTML += '<div class="tea-msg user">' + apex.util.escapeHTML(q) + '</div>';
  msgs.innerHTML += '<div class="tea-msg bot tea-typing" id="teaTyping">Digitando...</div>';
  msgs.scrollTop = msgs.scrollHeight;

  document.getElementById('teaChatQ').value = '';
  btn.disabled = true;

  apex.server.process('CHAT_IA', {}, {
    dataType: 'json',
    data: { x01: q },
    success: function(data) {
      document.getElementById('teaTyping').remove();
      if (data.status === 'ok') {
        msgs.innerHTML += '<div class="tea-msg bot"><div class="tea-msg-lbl">Assistente TEA</div>' +
          apex.util.escapeHTML(data.resposta).replace(/\\n/g,'<br>') + '</div>';
      } else {
        msgs.innerHTML += '<div class="tea-msg bot" style="color:#e53935">Erro: ' + apex.util.escapeHTML(data.error||'desconhecido') + '</div>';
      }
      msgs.scrollTop = msgs.scrollHeight;
      btn.disabled = false;
    },
    error: function() {
      document.getElementById('teaTyping').remove();
      msgs.innerHTML += '<div class="tea-msg bot" style="color:#e53935">Falha na conexão com o assistente.</div>';
      btn.disabled = false;
    }
  });
}
// Enviar com Enter (Shift+Enter = nova linha)
document.addEventListener('DOMContentLoaded', function() {
  var ta = document.getElementById('teaChatQ');
  if (ta) ta.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); teaChat(); }
  });
});""",
    ))

    # ── 15. App Items de Sessão ────────────────────────────────────────────────
    print("\n[15] App items de sessão...")
    ok("app_item: AI_ID_CLINICA",   apex_add_app_item("AI_ID_CLINICA"))
    ok("app_item: AI_ID_TERAPEUTA", apex_add_app_item("AI_ID_TERAPEUTA"))
    ok("app_item: AI_PERFIL",       apex_add_app_item("AI_PERFIL"))

    # App process: carregar perfil do usuário logado em todos os itens de sessão
    ok("app_process: CARREGAR_PERFIL_USUARIO", apex_add_app_process(
        process_name="Carregar Perfil do Usuário",
        plsql_body="""DECLARE
  l_id_clinica   NUMBER;
  l_id_terapeuta NUMBER;
  l_perfil       VARCHAR2(50);
BEGIN
  SELECT p.DS_PERFIL INTO l_perfil
    FROM TEA_USUARIOS u JOIN TEA_PERFIS p ON p.ID_PERFIL = u.ID_PERFIL
   WHERE UPPER(u.DS_LOGIN) = UPPER(:APP_USER) AND u.FL_ATIVO='S'
   FETCH FIRST 1 ROW ONLY;

  :AI_PERFIL := l_perfil;

  BEGIN
    SELECT t.ID_CLINICA, t.ID_TERAPEUTA INTO l_id_clinica, l_id_terapeuta
      FROM TEA_TERAPEUTAS t JOIN TEA_USUARIOS u ON u.ID_USUARIO = t.ID_USUARIO
     WHERE UPPER(u.DS_LOGIN) = UPPER(:APP_USER) AND u.FL_ATIVO='S'
     FETCH FIRST 1 ROW ONLY;
    :AI_ID_CLINICA   := l_id_clinica;
    :AI_ID_TERAPEUTA := l_id_terapeuta;
  EXCEPTION WHEN NO_DATA_FOUND THEN NULL;
  END;
EXCEPTION WHEN NO_DATA_FOUND THEN NULL;
END;""",
        point="AFTER_LOGIN",
    ))

    # ── 16. Navegação ─────────────────────────────────────────────────────────
    print("\n[16] Navegação...")
    ok("nav: Dashboard",      apex_add_nav_item("Dashboard",      1,   10, "fa-home"))
    ok("nav: Beneficiários",  apex_add_nav_item("Beneficiários",  10,  20, "fa-users"))
    ok("nav: Nova Avaliação", apex_add_nav_item("Nova Avaliação", 50,  30, "fa-plus-circle"))
    ok("nav: Clínicas",       apex_add_nav_item("Clínicas",       20,  40, "fa-hospital-o"))
    ok("nav: Terapeutas",     apex_add_nav_item("Terapeutas",     30,  50, "fa-user-md"))
    ok("nav: Dash Clínica",   apex_add_nav_item("Por Clínica",    60,  60, "fa-bar-chart"))
    ok("nav: Dash Paciente",  apex_add_nav_item("Por Paciente",   61,  70, "fa-line-chart"))
    ok("nav: Configurações",  apex_add_nav_item("Configurações",  70,  80, "fa-cog"))
    ok("nav: Usuários",       apex_add_nav_item("Usuários",       101, 90, "fa-user-circle"))
    ok("nav: Chat IA",        apex_add_nav_item("Assistente IA",  110, 100,"fa-comments"))

    # ── 17. Finalizar ─────────────────────────────────────────────────────────
    print("\n[17] Finalizando...")
    r = apex_finalize_app()
    rj = json.loads(r)
    if rj.get("status") == "error":
        print(f"  ❌ apex_finalize_app: {rj['error']}")
        return

    print(f"  ✓  apex_finalize_app")
    summary = rj.get("summary", {})
    print(f"\n{'═'*60}")
    print(f"  APP 100 — Desfecho TEA CRIADO COM SUCESSO!")
    print(f"  URL:      f?p=100")
    print(f"  Páginas:  {summary.get('pages')}")
    print(f"  Regiões:  {summary.get('regions')}")
    print(f"  Itens:    {summary.get('items')}")
    print(f"{'═'*60}")
    print(f"\n  Login: https://<seu-apex>/ords/f?p=100")
    print(f"  Usuário teste: cnu.admin / Unimed@2024")


if __name__ == "__main__":
    run()
