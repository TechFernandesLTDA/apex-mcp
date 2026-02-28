# TEA Backoffice (App 204)

**Alias**: TEA-BACKOFFICE | **Pages**: 18 | **Schema**: TEA_APP | **Last updated**: 

## Pages

### Page 1: Dashboard
**Auth**: — | **Mode**: Normal

#### Regions

| Region | Type | Source |
|--------|------|--------|
| Record Counts | PL/SQL | DECLARE   v_val VARCHAR2(4000); BEGIN    sys.htp.p('<style>     .apex-metric-grid{display:flex;flex-wrap:wrap;gap:16px;padding:8px 0;}     .apex-metric-card{flex:1 1 23%;min-width:160px;border-radius: |

---

### Page 10: Tea Beneficiarios
**Auth**: — | **Mode**: Normal

#### Regions

| Region | Type | Source |
|--------|------|--------|
| Tea Beneficiarios | Interactive Report | SELECT ID_BENEFICIARIO, NR_BENEFICIO, DS_NOME, DT_NASCIMENTO, NR_IDADE, ID_NIVEL, ID_CLINICA, ID_TERAPEUTA, ID_PERIODO, DS_RESPONSAVEL, FL_ATIVO, DT_CRIACAO, DT_ATUALIZACAO FROM TEA_BENEFICIARIOS |

---

### Page 11: Edit Tea Beneficiarios
**Auth**: — | **Mode**: Normal

#### Regions

| Region | Type | Source |
|--------|------|--------|
| Edit Tea Beneficiarios | Form |  |
| Buttons | Static Content |  |

#### Items

| Item | Type |
|------|------|
| P11_ID_BENEFICIARIO | Hidden |
| P11_NR_BENEFICIO | Number Field |
| P11_DS_NOME | Text Field |
| P11_DT_NASCIMENTO |  |
| P11_NR_IDADE | Number Field |
| P11_ID_NIVEL | Select List |
| P11_ID_CLINICA | Select List |
| P11_ID_TERAPEUTA | Select List |
| P11_ID_PERIODO | Select List |
| P11_DS_RESPONSAVEL | Text Field |
| P11_FL_ATIVO | Switch |

---

### Page 12: Tea Avaliacoes
**Auth**: — | **Mode**: Normal

#### Regions

| Region | Type | Source |
|--------|------|--------|
| Tea Avaliacoes | Interactive Report | SELECT ID_AVALIACAO, ID_BENEFICIARIO, ID_PROVA, ID_TERAPEUTA, ID_CLINICA, NR_COLETA, DT_AVALIACAO, DS_STATUS, NR_SCORE_TOTAL, NR_PCT_TOTAL, FL_TERMO_ACEITO, NR_ETAPA_ATUAL, DS_OBSERVACOES, DT_CRIACAO, |

---

### Page 13: Edit Tea Avaliacoes
**Auth**: — | **Mode**: Normal

#### Regions

| Region | Type | Source |
|--------|------|--------|
| Edit Tea Avaliacoes | Form |  |
| Buttons | Static Content |  |

#### Items

| Item | Type |
|------|------|
| P13_ID_AVALIACAO | Hidden |
| P13_ID_BENEFICIARIO | Select List |
| P13_ID_PROVA | Select List |
| P13_ID_TERAPEUTA | Select List |
| P13_ID_CLINICA | Select List |
| P13_NR_COLETA | Number Field |
| P13_DT_AVALIACAO |  |
| P13_DS_STATUS | Text Field |
| P13_NR_SCORE_TOTAL | Number Field |
| P13_NR_PCT_TOTAL | Number Field |
| P13_FL_TERMO_ACEITO | Switch |
| P13_NR_ETAPA_ATUAL | Number Field |
| P13_DS_OBSERVACOES | Textarea |
| P13_DT_FINALIZACAO |  |

---

### Page 14: Tea Clinicas
**Auth**: — | **Mode**: Normal

#### Regions

| Region | Type | Source |
|--------|------|--------|
| Tea Clinicas | Interactive Report | SELECT ID_CLINICA, DS_NOME, NR_CNPJ, DS_ENDERECO, DS_CIDADE, DS_UF, DS_TELEFONE, DS_EMAIL, ID_USUARIO, FL_ATIVO, DT_CRIACAO, DT_ATUALIZACAO FROM TEA_CLINICAS |

---

### Page 15: Edit Tea Clinicas
**Auth**: — | **Mode**: Normal

#### Regions

| Region | Type | Source |
|--------|------|--------|
| Edit Tea Clinicas | Form |  |
| Buttons | Static Content |  |

#### Items

| Item | Type |
|------|------|
| P15_ID_CLINICA | Hidden |
| P15_DS_NOME | Text Field |
| P15_NR_CNPJ | Number Field |
| P15_DS_ENDERECO | Text Field |
| P15_DS_CIDADE | Text Field |
| P15_DS_UF | Text Field |
| P15_DS_TELEFONE | Text Field |
| P15_DS_EMAIL | Text Field |
| P15_ID_USUARIO | Select List |
| P15_FL_ATIVO | Switch |

---

### Page 16: Tea Terapeutas
**Auth**: — | **Mode**: Normal

#### Regions

| Region | Type | Source |
|--------|------|--------|
| Tea Terapeutas | Interactive Report | SELECT ID_TERAPEUTA, DS_NOME, NR_REGISTRO, DS_ESPECIALIDADE, ID_CLINICA, ID_TERAPIA, ID_USUARIO, FL_ATIVO, DT_CRIACAO, DT_ATUALIZACAO FROM TEA_TERAPEUTAS |

---

### Page 17: Edit Tea Terapeutas
**Auth**: — | **Mode**: Normal

#### Regions

| Region | Type | Source |
|--------|------|--------|
| Edit Tea Terapeutas | Form |  |
| Buttons | Static Content |  |

#### Items

| Item | Type |
|------|------|
| P17_ID_TERAPEUTA | Hidden |
| P17_DS_NOME | Text Field |
| P17_NR_REGISTRO | Number Field |
| P17_DS_ESPECIALIDADE | Text Field |
| P17_ID_CLINICA | Select List |
| P17_ID_TERAPIA | Select List |
| P17_ID_USUARIO | Select List |
| P17_FL_ATIVO | Switch |

---

### Page 18: Tea Provas
**Auth**: — | **Mode**: Normal

#### Regions

| Region | Type | Source |
|--------|------|--------|
| Tea Provas | Interactive Report | SELECT ID_PROVA, DS_NOME, DS_DESCRICAO, DS_VERSAO, NR_ORDEM, FL_ATIVO, DT_CRIACAO, DT_ATUALIZACAO FROM TEA_PROVAS |

---

### Page 19: Edit Tea Provas
**Auth**: — | **Mode**: Normal

#### Regions

| Region | Type | Source |
|--------|------|--------|
| Edit Tea Provas | Form |  |
| Buttons | Static Content |  |

#### Items

| Item | Type |
|------|------|
| P19_ID_PROVA | Hidden |
| P19_DS_NOME | Text Field |
| P19_DS_DESCRICAO | Textarea |
| P19_DS_VERSAO | Text Field |
| P19_NR_ORDEM | Number Field |
| P19_FL_ATIVO | Switch |

---

### Page 20: Tea Dimensoes
**Auth**: — | **Mode**: Normal

#### Regions

| Region | Type | Source |
|--------|------|--------|
| Tea Dimensoes | Interactive Report | SELECT ID_DIMENSAO, ID_PROVA, DS_NOME, DS_DESCRICAO, NR_ORDEM, FL_ATIVO, DT_CRIACAO FROM TEA_DIMENSOES |

---

### Page 21: Edit Tea Dimensoes
**Auth**: — | **Mode**: Normal

#### Regions

| Region | Type | Source |
|--------|------|--------|
| Edit Tea Dimensoes | Form |  |
| Buttons | Static Content |  |

#### Items

| Item | Type |
|------|------|
| P21_ID_DIMENSAO | Hidden |
| P21_ID_PROVA | Select List |
| P21_DS_NOME | Text Field |
| P21_DS_DESCRICAO | Textarea |
| P21_NR_ORDEM | Number Field |
| P21_FL_ATIVO | Switch |

---

### Page 22: Tea Usuarios
**Auth**: — | **Mode**: Normal

#### Regions

| Region | Type | Source |
|--------|------|--------|
| Tea Usuarios | Interactive Report | SELECT ID_USUARIO, DS_LOGIN, DS_EMAIL, DS_NOME, DS_SENHA_HASH, DS_SALT, ID_PERFIL, FL_ATIVO, FL_PRIMEIRO_ACESSO, DT_ULTIMO_LOGIN, DT_CRIACAO, DT_ATUALIZACAO FROM TEA_USUARIOS |

---

### Page 23: Edit Tea Usuarios
**Auth**: — | **Mode**: Normal

#### Regions

| Region | Type | Source |
|--------|------|--------|
| Edit Tea Usuarios | Form |  |
| Buttons | Static Content |  |

#### Items

| Item | Type |
|------|------|
| P23_ID_USUARIO | Hidden |
| P23_DS_LOGIN | Text Field |
| P23_DS_EMAIL | Text Field |
| P23_DS_NOME | Text Field |
| P23_DS_SENHA_HASH | Text Field |
| P23_DS_SALT | Text Field |
| P23_ID_PERFIL | Select List |
| P23_FL_ATIVO | Switch |
| P23_FL_PRIMEIRO_ACESSO | Switch |
| P23_DT_ULTIMO_LOGIN |  |

---

### Page 24: Tea Perfis
**Auth**: — | **Mode**: Normal

#### Regions

| Region | Type | Source |
|--------|------|--------|
| Tea Perfis | Interactive Report | SELECT ID_PERFIL, DS_PERFIL, DS_DESCRICAO FROM TEA_PERFIS |

---

### Page 25: Edit Tea Perfis
**Auth**: — | **Mode**: Normal

#### Regions

| Region | Type | Source |
|--------|------|--------|
| Edit Tea Perfis | Form |  |
| Buttons | Static Content |  |

#### Items

| Item | Type |
|------|------|
| P25_ID_PERFIL | Hidden |
| P25_DS_PERFIL | Text Field |
| P25_DS_DESCRICAO | Text Field |

---

### Page 101: Login
**Auth**: — | **Mode**: Normal

#### Regions

| Region | Type | Source |
|--------|------|--------|
| TEA Backoffice | Static Content |  |

#### Items

| Item | Type |
|------|------|
| P101_USERNAME | Text Field |
| P101_PASSWORD | Password |

---

## Shared LOVs (9)

| LOV Name | Type |
|----------|------|
| LOV_ID_BENEFICIARIO | Dynamic |
| LOV_ID_CLINICA | Dynamic |
| LOV_ID_NIVEL | Dynamic |
| LOV_ID_PERFIL | Dynamic |
| LOV_ID_PERIODO | Dynamic |
| LOV_ID_PROVA | Dynamic |
| LOV_ID_TERAPEUTA | Dynamic |
| LOV_ID_TERAPIA | Dynamic |
| LOV_ID_USUARIO | Dynamic |

## Auth Schemes (3)

| Scheme | Type |
|--------|------|
| IS_ADM | PL/SQL Function Returning Boolean |
| IS_CLINICA | PL/SQL Function Returning Boolean |
| IS_TERAPEUTA | PL/SQL Function Returning Boolean |
