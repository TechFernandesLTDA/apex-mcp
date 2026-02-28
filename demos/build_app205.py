"""Demo — Formulário TEA de Avaliação em 4 Etapas (App 205).

Cria um wizard interativo com 4 etapas de avaliação ICHOM, totalizando
scores por domínio e salvando a avaliação na tabela TEA_AVALIACOES.

Fluxo:
  Página 101 → Login
  Página 50  → Etapa 1: Dados da Avaliação (beneficiário, instrumento, terapeuta)
  Página 51  → Etapa 2: Comunicação       (5 questões Likert 0-3)
  Página 52  → Etapa 3: Socialização      (5 questões Likert 0-3)
  Página 53  → Etapa 4: Habilidades       (5 questões Likert 0-3) → FINALIZAR
  Página 54  → Score Final                (métricas + detalhes da avaliação salva)

Score: 15 questões × max 3 pontos = máximo 45 pontos.
"""
import os, sys, json, time, textwrap

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

from apex_mcp.tools.sql_tools        import apex_connect
from apex_mcp.tools.app_tools        import (
    apex_list_apps, apex_create_app, apex_finalize_app, apex_delete_app,
)
from apex_mcp.tools.page_tools       import apex_add_page
from apex_mcp.tools.component_tools  import apex_add_region, apex_add_item, apex_add_process
from apex_mcp.tools.shared_tools     import apex_add_app_item, apex_add_nav_item
from apex_mcp.tools.generator_tools  import apex_generate_login
from apex_mcp.tools.advanced_tools   import apex_generate_wizard
from apex_mcp.tools.visual_tools     import apex_add_metric_cards

# ── Configuração ──────────────────────────────────────────────────────────────
APP_ID   = 205
APP_NAME = "TEA — Avaliação Interativa"

# Escala Likert: 0=Nunca … 3=Sempre (máx 3 × 15 questões = 45 pts)
LIKERT = (
    "SELECT '0 — Nunca'         D,'0' R FROM DUAL UNION ALL "
    "SELECT '1 — Raramente'     D,'1' R FROM DUAL UNION ALL "
    "SELECT '2 — Às vezes'      D,'2' R FROM DUAL UNION ALL "
    "SELECT '3 — Sempre'        D,'3' R FROM DUAL"
)

# ── Helpers ───────────────────────────────────────────────────────────────────
def ok(label: str, result_str: str) -> tuple[bool, dict]:
    r = json.loads(result_str)
    if r.get("status") == "error":
        print(f"  ✗  {label}: {r['error']}")
        return False, r
    print(f"  ✓  {label}")
    return True, r


def section(title: str) -> None:
    print(f"\n{'─' * 56}")
    print(f"  {title}")
    print(f"{'─' * 56}")


# ── PL/SQL do processo de salvamento (roda no APEX quando usuário clica FINALIZAR)
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
  -- Domínio Comunicação (página 51, máx 15 pts)
  v_com :=
    NVL(TO_NUMBER(:P51_COM_Q1),0) + NVL(TO_NUMBER(:P51_COM_Q2),0) +
    NVL(TO_NUMBER(:P51_COM_Q3),0) + NVL(TO_NUMBER(:P51_COM_Q4),0) +
    NVL(TO_NUMBER(:P51_COM_Q5),0);

  -- Domínio Socialização (página 52, máx 15 pts)
  v_soc :=
    NVL(TO_NUMBER(:P52_SOC_Q1),0) + NVL(TO_NUMBER(:P52_SOC_Q2),0) +
    NVL(TO_NUMBER(:P52_SOC_Q3),0) + NVL(TO_NUMBER(:P52_SOC_Q4),0) +
    NVL(TO_NUMBER(:P52_SOC_Q5),0);

  -- Domínio Habilidades da Vida Diária (página 53, máx 15 pts)
  v_hab :=
    NVL(TO_NUMBER(:P53_HAB_Q1),0) + NVL(TO_NUMBER(:P53_HAB_Q2),0) +
    NVL(TO_NUMBER(:P53_HAB_Q3),0) + NVL(TO_NUMBER(:P53_HAB_Q4),0) +
    NVL(TO_NUMBER(:P53_HAB_Q5),0);

  v_score := v_com + v_soc + v_hab;                 -- máx 45
  v_pct   := ROUND(v_score / 45 * 100, 1);

  -- Número sequencial de coleta para o beneficiário
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

  -- Guardar ID da avaliação criada para a página de score
  :AI_AVALIACAO_ID := TO_CHAR(v_id);

  -- Redirecionar para página 54 (Score Final) passando o ID via URL
  APEX_UTIL.REDIRECT_URL(
    APEX_UTIL.PREPARE_URL(
      'f?p=' || :APP_ID || ':54:' || :APP_SESSION ||
      '::NO:54:P54_ID_AVALIACAO:' || v_id
    )
  );
END;
""").strip()

# SQL do relatório de resultado (página 54)
RESULT_SQL = """
SELECT
  b.DS_NOME                                        AS "Beneficiário",
  b.NR_BENEFICIO                                   AS "Nº Benefício",
  p.DS_NOME || ' v' || p.DS_VERSAO                AS "Instrumento",
  t.DS_NOME                                        AS "Terapeuta",
  TO_CHAR(a.DT_AVALIACAO, 'DD/MM/YYYY')           AS "Data",
  a.NR_COLETA                                      AS "Nº Coleta",
  a.NR_SCORE_TOTAL || ' / 45'                      AS "Score Total",
  TO_CHAR(a.NR_PCT_TOTAL, '990.0') || '%'         AS "Percentual",
  CASE
    WHEN a.NR_PCT_TOTAL >= 75 THEN 'Alto (≥75%)'
    WHEN a.NR_PCT_TOTAL >= 50 THEN 'Médio (50-74%)'
    ELSE 'Baixo (<50%)'
  END                                              AS "Nível de Habilidade",
  a.DS_STATUS                                      AS "Status"
FROM TEA_AVALIACOES a
JOIN TEA_BENEFICIARIOS b ON b.ID_BENEFICIARIO = a.ID_BENEFICIARIO
JOIN TEA_PROVAS        p ON p.ID_PROVA        = a.ID_PROVA
JOIN TEA_TERAPEUTAS    t ON t.ID_TERAPEUTA    = a.ID_TERAPEUTA
WHERE a.ID_AVALIACAO = :P54_ID_AVALIACAO
""".strip()


# ── Main ──────────────────────────────────────────────────────────────────────
def run():
    t0 = time.perf_counter()
    print("\n" + "═" * 60)
    print(f"  build_app205 — {APP_NAME}")
    print(f"  Wizard de avaliação TEA (4 etapas) + Score Final")
    print("═" * 60)

    # ── 1. Conectar ───────────────────────────────────────────────────────────
    section("[1] Conexão")
    if not ok("apex_connect", apex_connect())[0]:
        return

    # ── 2. Limpar app anterior (se existir) ───────────────────────────────────
    section("[2] Preparar workspace")
    apps_raw = apex_list_apps()
    apps = json.loads(apps_raw)
    if isinstance(apps, list) and any(a.get("APPLICATION_ID") == APP_ID for a in apps):
        ok(f"apex_delete_app({APP_ID})", apex_delete_app(APP_ID))
    else:
        print(f"  →  App {APP_ID} não existe — criando do zero")

    # ── 3. Criar app ──────────────────────────────────────────────────────────
    section("[3] Criar app")
    if not ok(f"apex_create_app({APP_ID})", apex_create_app(APP_ID, APP_NAME))[0]:
        return

    # ── 4. Login (página 101) ─────────────────────────────────────────────────
    section("[4] Página 101 — Login")
    ok("apex_generate_login(101)", apex_generate_login(101))

    # ── 5. Wizard 4 etapas (páginas 50-53) ───────────────────────────────────
    section("[5] Wizard — 4 etapas (páginas 50–53)")

    steps = [
        # ── Etapa 1: Dados da Avaliação ──────────────────────────────────────
        {
            "title": "Etapa 1 — Dados da Avaliação",
            "items": [
                {
                    "name":     "ID_BENEFICIARIO",
                    "label":    "Beneficiário (Paciente)",
                    "type":     "select",
                    "required": True,
                    "lov": (
                        "SELECT DS_NOME || ' (' || NR_BENEFICIO || ')' D,"
                        "       ID_BENEFICIARIO R"
                        "  FROM TEA_BENEFICIARIOS"
                        " ORDER BY DS_NOME"
                    ),
                },
                {
                    "name":     "ID_PROVA",
                    "label":    "Instrumento de Avaliação",
                    "type":     "select",
                    "required": True,
                    "lov": (
                        "SELECT DS_NOME || ' — ' || DS_VERSAO D,"
                        "       ID_PROVA R"
                        "  FROM TEA_PROVAS"
                        " WHERE FL_ATIVO = 'S'"
                        " ORDER BY NR_ORDEM"
                    ),
                },
                {
                    "name":     "ID_TERAPEUTA",
                    "label":    "Terapeuta Responsável",
                    "type":     "select",
                    "required": True,
                    "lov": (
                        "SELECT t.DS_NOME || ' — ' || c.DS_NOME D,"
                        "       t.ID_TERAPEUTA R"
                        "  FROM TEA_TERAPEUTAS t"
                        "  JOIN TEA_CLINICAS c ON c.ID_CLINICA = t.ID_CLINICA"
                        " ORDER BY t.DS_NOME"
                    ),
                },
                {
                    "name":     "DT_AVALIACAO",
                    "label":    "Data da Avaliação",
                    "type":     "date",
                    "required": True,
                },
                {
                    "name":     "FL_TERMO",
                    "label":    "Termo de Consentimento Informado",
                    "type":     "select",
                    "required": True,
                    "lov": (
                        "SELECT 'Sim — Aceito e registrado' D,'S' R FROM DUAL "
                        "UNION ALL "
                        "SELECT 'Não — Recusado pelo responsável' D,'N' R FROM DUAL"
                    ),
                },
            ],
        },

        # ── Etapa 2: Comunicação ──────────────────────────────────────────────
        {
            "title": "Etapa 2 — Comunicação",
            "items": [
                {"name": "COM_Q1", "label": "1. Usa palavras para expressar necessidades básicas",
                 "type": "select", "lov": LIKERT},
                {"name": "COM_Q2", "label": "2. Responde quando seu nome é chamado",
                 "type": "select", "lov": LIKERT},
                {"name": "COM_Q3", "label": "3. Mantém contato visual durante conversas",
                 "type": "select", "lov": LIKERT},
                {"name": "COM_Q4", "label": "4. Faz perguntas para obter informações",
                 "type": "select", "lov": LIKERT},
                {"name": "COM_Q5", "label": "5. Compreende instruções verbais simples",
                 "type": "select", "lov": LIKERT},
            ],
        },

        # ── Etapa 3: Socialização ─────────────────────────────────────────────
        {
            "title": "Etapa 3 — Socialização",
            "items": [
                {"name": "SOC_Q1", "label": "1. Interage espontaneamente com outras crianças",
                 "type": "select", "lov": LIKERT},
                {"name": "SOC_Q2", "label": "2. Demonstra empatia por outras pessoas",
                 "type": "select", "lov": LIKERT},
                {"name": "SOC_Q3", "label": "3. Participa de atividades em grupo",
                 "type": "select", "lov": LIKERT},
                {"name": "SOC_Q4", "label": "4. Compartilha brinquedos e materiais",
                 "type": "select", "lov": LIKERT},
                {"name": "SOC_Q5", "label": "5. Reconhece e expressa emoções básicas",
                 "type": "select", "lov": LIKERT},
            ],
        },

        # ── Etapa 4: Habilidades da Vida Diária ──────────────────────────────
        {
            "title": "Etapa 4 — Habilidades da Vida Diária",
            "items": [
                {"name": "HAB_Q1", "label": "1. Realiza higiene pessoal com autonomia",
                 "type": "select", "lov": LIKERT},
                {"name": "HAB_Q2", "label": "2. Se veste e despe sem assistência",
                 "type": "select", "lov": LIKERT},
                {"name": "HAB_Q3", "label": "3. Come com utensílios de forma independente",
                 "type": "select", "lov": LIKERT},
                {"name": "HAB_Q4", "label": "4. Organiza seus pertences e ambiente",
                 "type": "select", "lov": LIKERT},
                {"name": "HAB_Q5", "label": "5. Segue rotinas diárias estabelecidas",
                 "type": "select", "lov": LIKERT},
            ],
        },
    ]

    flag, wiz = ok(
        "apex_generate_wizard(pages 50–53)",
        apex_generate_wizard(
            start_page_id=50,
            steps=steps,
            wizard_title="Avaliação TEA — Protocolo ICHOM",
            finish_redirect_page=54,
        ),
    )
    if not flag:
        return

    print(f"    Páginas criadas : {wiz.get('pages')}")
    print(f"    Itens criados   : {len(wiz.get('items_created', []))}")

    # ── 6. Processo de salvamento na página 53 (FINALIZAR) ───────────────────
    section("[6] Processo Salvar Avaliação (página 53)")
    ok(
        "apex_add_process(53, Salvar Avaliação)",
        apex_add_process(
            page_id=53,
            process_name="Salvar Avaliação TEA",
            process_type="plsql",
            sequence=5,                    # antes do clear-cache do wizard (seq=10)
            source=SAVE_PLSQL,
            condition_button="NEXT",       # botão NEXT/FINALIZAR
            success_message="Avaliação salva com sucesso!",
            error_message="Erro ao salvar avaliação. Verifique os dados e tente novamente.",
        ),
    )

    # ── 7. App Item global para transportar o ID da avaliação ─────────────────
    section("[7] App Item — AI_AVALIACAO_ID")
    ok(
        "apex_add_app_item(AI_AVALIACAO_ID)",
        apex_add_app_item(item_name="AI_AVALIACAO_ID"),
    )

    # ── 8. Página 54 — Score Final ────────────────────────────────────────────
    section("[8] Página 54 — Score Final")
    ok("apex_add_page(54)", apex_add_page(54, "Score da Avaliação", "blank"))

    # Cartões de métricas do score
    ok(
        "apex_add_metric_cards(54)",
        apex_add_metric_cards(
            page_id=54,
            region_name="Resultado da Avaliação",
            style="gradient",
            metrics=[
                {
                    "label": "Score Total",
                    "sql":   "SELECT NR_SCORE_TOTAL FROM TEA_AVALIACOES WHERE ID_AVALIACAO = :P54_ID_AVALIACAO",
                    "unit":  "/ 45 pts",
                    "icon":  "fa-star",
                    "color": "#00995D",
                },
                {
                    "label": "Percentual Geral",
                    "sql":   "SELECT ROUND(NR_PCT_TOTAL,1) FROM TEA_AVALIACOES WHERE ID_AVALIACAO = :P54_ID_AVALIACAO",
                    "unit":  "%",
                    "icon":  "fa-percent",
                    "color": "#1E88E5",
                },
                {
                    "label": "Nível de Habilidade",
                    "sql": (
                        "SELECT CASE "
                        "  WHEN NR_PCT_TOTAL >= 75 THEN 'Alto' "
                        "  WHEN NR_PCT_TOTAL >= 50 THEN 'Médio' "
                        "  ELSE 'Baixo' "
                        "END FROM TEA_AVALIACOES WHERE ID_AVALIACAO = :P54_ID_AVALIACAO"
                    ),
                    "icon":  "fa-chart-bar",
                    "color": "#FF9800",
                },
                {
                    "label": "Nº Coleta",
                    "sql":   "SELECT NR_COLETA FROM TEA_AVALIACOES WHERE ID_AVALIACAO = :P54_ID_AVALIACAO",
                    "icon":  "fa-list-ol",
                    "color": "#7B1FA2",
                },
            ],
            sequence=10,
        ),
    )

    # Região de detalhes (Interactive Report)
    ok(
        "apex_add_region(54, Detalhes da Avaliação, ir)",
        apex_add_region(
            page_id=54,
            region_name="Detalhes da Avaliação",
            region_type="ir",
            sequence=20,
            source_sql=RESULT_SQL,
        ),
    )

    # Item hidden P54_ID_AVALIACAO (recebe o ID via URL)
    ok(
        "apex_add_item(54, P54_ID_AVALIACAO, hidden)",
        apex_add_item(
            page_id=54,
            region_name="Detalhes da Avaliação",
            item_name="P54_ID_AVALIACAO",
            item_type="hidden",
            sequence=5,
        ),
    )

    # ── 9. Navegação ──────────────────────────────────────────────────────────
    section("[9] Navegação")
    nav_items = [
        ("Nova Avaliação",       50,  10, "fa-clipboard-check"),
        ("Score da Avaliação",   54,  20, "fa-star"),
    ]
    for label, page, seq, icon in nav_items:
        ok(
            f"apex_add_nav_item({label})",
            apex_add_nav_item(label, page, seq, icon),
        )

    # ── 10. Finalizar ─────────────────────────────────────────────────────────
    section("[10] Finalizar app")
    if not ok("apex_finalize_app()", apex_finalize_app())[0]:
        return

    # ── Resumo ────────────────────────────────────────────────────────────────
    total = time.perf_counter() - t0
    print(f"\n{'═' * 60}")
    print(f"  App {APP_ID} — {APP_NAME}")
    print(f"  Criado em {total:.1f}s")
    print(f"")
    print(f"  Fluxo da avaliação:")
    print(f"    101  →  Login")
    print(f"     50  →  Etapa 1: Dados da Avaliação (beneficiário, instrumento, terapeuta)")
    print(f"     51  →  Etapa 2: Comunicação        (5 questões | máx 15 pts)")
    print(f"     52  →  Etapa 3: Socialização        (5 questões | máx 15 pts)")
    print(f"     53  →  Etapa 4: Habilidades         (5 questões | máx 15 pts) → FINALIZAR")
    print(f"     54  →  Score Final                  (métricas + detalhes salvo em TEA_AVALIACOES)")
    print(f"")
    print(f"  Score:  15 questões × 3 pts = máx 45 pontos")
    print(f"  Acesse: f?p={APP_ID}  (relativo à URL base do APEX)")
    print("═" * 60 + "\n")


if __name__ == "__main__":
    run()
