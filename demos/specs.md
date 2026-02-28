# apex-mcp Demo Apps — Especificações e Critérios de Sucesso

Três aplicações reais criadas com as tools do apex-mcp sobre o schema TEA_APP.
Cada app demonstra um conjunto diferente de tools e padrões.

---

## App 200 — Painel de Clínicas e Terapeutas

**Objetivo:** CRUD completo de clínicas e terapeutas com dashboard de KPIs.
Demonstra: fluxo completo de criação, generators, navegação estruturada.

### Páginas
| ID  | Nome           | Tipo      | Tool principal           |
|-----|----------------|-----------|--------------------------|
| 101 | Login          | login     | apex_generate_login      |
| 1   | Dashboard      | blank     | apex_generate_dashboard  |
| 10  | Clínicas       | report    | apex_generate_crud       |
| 11  | Clínica (Form) | form      | apex_generate_crud       |
| 20  | Terapeutas     | report    | apex_generate_crud       |
| 21  | Terapeuta(Form)| form      | apex_generate_crud       |

### Tools Usadas
```
apex_create_app(200, "Painel Clínicas TEA")
apex_generate_login(101)
apex_add_page(1, "Dashboard", "blank")
apex_generate_dashboard(1, kpi_queries=[clinicas, terapeutas, beneficiarios, avaliacoes])
apex_generate_crud("TEA_CLINICAS", 10, 11)
apex_generate_crud("TEA_TERAPEUTAS", 20, 21)
apex_add_nav_item("Dashboard", 1, 10, "fa-home")
apex_add_nav_item("Clínicas", 10, 20, "fa-hospital-o")
apex_add_nav_item("Terapeutas", 20, 30, "fa-user-md")
apex_finalize_app()
```

### Critérios de Sucesso
- [ ] `apex_create_app` retorna `status: ok`
- [ ] Login page 101 gerada sem erro
- [ ] Dashboard com 4 KPIs (clínicas, terapeutas, beneficiários, avaliações)
- [ ] IR de TEA_CLINICAS mostra 6 clínicas
- [ ] Form de TEA_CLINICAS abre, edita e salva
- [ ] IR de TEA_TERAPEUTAS mostra 15 terapeutas
- [ ] Nav menu com 3 itens funcionais
- [ ] `apex_finalize_app` retorna `status: ok` com apex_url

---

## App 201 — Registro de Pacientes

**Objetivo:** Gestão de beneficiários com validações, computações e relatório de avaliações.
Demonstra: validações de campo, computações automáticas, regiões manuais com SQL customizado.

### Páginas
| ID  | Nome                | Tipo   | Tool principal                |
|-----|---------------------|--------|-------------------------------|
| 101 | Login               | login  | apex_generate_login           |
| 1   | Dashboard Pacientes | blank  | apex_generate_dashboard       |
| 10  | Beneficiários       | report | apex_generate_crud            |
| 11  | Beneficiário (Form) | form   | apex_generate_crud            |
| 20  | Avaliações          | blank  | apex_add_page + apex_add_region |

### Tools Usadas
```
apex_create_app(201, "Registro de Pacientes TEA")
apex_generate_login(101)
apex_add_page(1, "Dashboard Pacientes", "blank")
apex_generate_dashboard(1, kpi_queries=[beneficiarios ativos, avaliacoes concluidas, media score])
apex_generate_crud("TEA_BENEFICIARIOS", 10, 11)
apex_add_item_validation(11, "NR_BENEFICIO", "Número Obrigatório", "not_null", trigger_button="SAVE")
apex_add_item_validation(11, "DS_NOME", "Nome Obrigatório", "not_null", trigger_button="SAVE")
apex_add_item_validation(11, "NR_BENEFICIO", "Formato xxx.xxx.xxx-x", "regex",
    validation_expression="^[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]$", trigger_button="SAVE")
apex_add_item_computation(11, "DT_CRIACAO", "static_value", "SYSDATE", "BEFORE_HEADER")
apex_add_page(20, "Avaliações", "blank")
apex_add_region(20, "Avaliações por Beneficiário", "report",
    source_sql="SELECT a.ID_AVALIACAO, b.DS_NOME, p.DS_NOME AS PROVA,
                       a.DT_AVALIACAO, a.DS_STATUS, a.NR_PCT_TOTAL
                  FROM TEA_AVALIACOES a
                  JOIN TEA_BENEFICIARIOS b ON b.ID_BENEFICIARIO = a.ID_BENEFICIARIO
                  JOIN TEA_PROVAS p ON p.ID_PROVA = a.ID_PROVA
                 ORDER BY a.DT_AVALIACAO DESC")
apex_add_nav_item("Dashboard", 1, 10, "fa-home")
apex_add_nav_item("Pacientes", 10, 20, "fa-users")
apex_add_nav_item("Avaliações", 20, 30, "fa-clipboard")
apex_finalize_app()
```

### Critérios de Sucesso
- [ ] `apex_create_app` retorna `status: ok`
- [ ] 40 beneficiários visíveis no IR com busca funcional
- [ ] Validação de NR_BENEFICIO (obrigatório) dispara no submit
- [ ] Validação de formato regex (xxx.xxx.xxx-x) funciona
- [ ] Computation de DT_CRIACAO preenche automaticamente
- [ ] IR de Avaliações mostra 120 registros com join nas 3 tabelas
- [ ] `apex_finalize_app` retorna `status: ok`

---

## App 202 — Administração e Auditoria

**Objetivo:** Painel administrativo com gestão de usuários, log de auditoria e AJAX handler.
Demonstra: auth schemes, dynamic actions, AJAX + JavaScript, múltiplas regiões por página.

### Páginas
| ID  | Nome           | Tipo   | Tool principal                      |
|-----|----------------|--------|-------------------------------------|
| 101 | Login          | login  | apex_generate_login                 |
| 1   | Dashboard ADM  | blank  | apex_generate_dashboard             |
| 10  | Usuários       | report | apex_generate_crud                  |
| 11  | Usuário (Form) | form   | apex_generate_crud                  |
| 20  | Log Auditoria  | blank  | apex_add_page + apex_add_region     |
| 30  | Configurações  | blank  | apex_add_page + apex_add_region (KV)|

### Tools Usadas
```
apex_create_app(202, "Administração TEA")
apex_add_auth_scheme("IS_ADMIN", "custom", "EXISTS(SELECT 1 FROM TEA_USUARIOS WHERE DS_LOGIN = :APP_USER AND ID_PERFIL=1 AND FL_ATIVO='S')")
apex_generate_login(101)
apex_add_page(1, "Dashboard ADM", "blank")
apex_generate_dashboard(1, kpi_queries=[usuarios ativos, logins hoje, erros auditoria])
apex_generate_crud("TEA_USUARIOS", 10, 11)
apex_add_page(20, "Log de Auditoria", "blank")
apex_add_region(20, "Auditoria", "report",
    source_sql="SELECT DS_TABELA, DS_OPERACAO, ID_REGISTRO,
                       DS_USUARIO, DS_DETALHES, DT_OPERACAO
                  FROM TEA_LOG_AUDITORIA
                 ORDER BY DT_OPERACAO DESC")
apex_add_page(30, "Configurações", "blank")
apex_add_region(30, "Parâmetros", "report",
    source_sql="SELECT DS_CHAVE, DS_VALOR, DT_CRIACAO FROM TEA_CONFIG ORDER BY DS_CHAVE")
apex_generate_ajax_handler(20, "FILTRAR_LOG",
    "SELECT DS_TABELA, DS_OPERACAO, ID_REGISTRO, DS_USUARIO, DS_DETALHES, DT_OPERACAO
       FROM TEA_LOG_AUDITORIA WHERE (:P20_TABELA IS NULL OR DS_TABELA = :P20_TABELA)
      ORDER BY DT_OPERACAO DESC",
    input_items=["P20_TABELA"])
apex_add_dynamic_action(20, "Filtrar Log", "change", "P20_TABELA",
    action_type="execute_javascript",
    javascript_code="callFiltrarLog();")
apex_add_nav_item("Dashboard", 1, 10, "fa-home")
apex_add_nav_item("Usuários", 10, 20, "fa-users")
apex_add_nav_item("Auditoria", 20, 30, "fa-file-text-o")
apex_add_nav_item("Configurações", 30, 40, "fa-cog")
apex_finalize_app()
```

### Critérios de Sucesso
- [ ] `apex_create_app` retorna `status: ok`
- [ ] Authorization scheme IS_ADMIN criada
- [ ] 13 usuários no IR de TEA_USUARIOS
- [ ] Log de auditoria mostra 120 entradas ordenadas por data desc
- [ ] AJAX handler FILTRAR_LOG criado (process_id no retorno)
- [ ] Dynamic action dispara callFiltrarLog() no change do P20_TABELA
- [ ] Página de Configurações mostra chave/valor do TEA_CONFIG
- [ ] `apex_finalize_app` retorna `status: ok`

---

## Resumo de Tools por App

| Tool                      | App 200 | App 201 | App 202 |
|---------------------------|:-------:|:-------:|:-------:|
| apex_create_app           | ✓       | ✓       | ✓       |
| apex_generate_login       | ✓       | ✓       | ✓       |
| apex_add_page             | ✓       | ✓       | ✓       |
| apex_generate_dashboard   | ✓       | ✓       | ✓       |
| apex_generate_crud        | ✓ (x2)  | ✓       | ✓       |
| apex_add_region           |         | ✓       | ✓ (x2)  |
| apex_add_item_validation  |         | ✓ (x3)  |         |
| apex_add_item_computation |         | ✓       |         |
| apex_add_auth_scheme      |         |         | ✓       |
| apex_generate_ajax_handler|         |         | ✓       |
| apex_add_dynamic_action   |         |         | ✓       |
| apex_add_nav_item         | ✓ (x3)  | ✓ (x3)  | ✓ (x4)  |
| apex_finalize_app         | ✓       | ✓       | ✓       |
