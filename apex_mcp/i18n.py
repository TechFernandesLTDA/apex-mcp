"""Internationalization support for apex-mcp generated applications.

Provides translatable labels used in generated APEX components.
The active locale can be set via APEX_MCP_LOCALE env var or at runtime.
"""
from __future__ import annotations

import os

# ── Label dictionaries ────────────────────────────────────────────────────────
_LABELS: dict[str, dict[str, str]] = {
    "en": {
        "logout": "Logout",
        "login": "Sign In",
        "username": "Username",
        "password": "Password",
        "submit": "Submit",
        "save": "Save",
        "cancel": "Cancel",
        "delete": "Delete",
        "create": "Create",
        "edit": "Edit",
        "search": "Search",
        "filter": "Filter",
        "filters": "Filters",
        "apply": "Apply",
        "reset": "Reset",
        "close": "Close",
        "yes": "Yes",
        "no": "No",
        "back": "Back",
        "next": "Next",
        "finish": "Finish",
        "loading": "Loading...",
        "no_data": "No data found.",
        "confirm_delete": "Are you sure you want to delete this record?",
        "record_saved": "Record saved successfully.",
        "record_deleted": "Record deleted.",
        "error_required": "#LABEL# is required.",
        "error_invalid": "#LABEL# is not valid.",
        "max_rows_warning": "The maximum row count for this report has been reached.",
        "dashboard": "Dashboard",
        "home": "Home",
        "reports": "Reports",
        "settings": "Settings",
        "total": "Total",
        "average": "Average",
        "count": "Count",
        "trend": "Trend",
        "quantity": "Quantity",
        "cumulative_pct": "Cumulative %",
        "download_formats": "CSV:HTML:XLSX:PDF",
        "system_unavailable": "System temporarily unavailable.",
        # Audit column names (for generator exclusion)
        "audit_columns": "CREATED_ON,UPDATED_ON,CREATED_BY,UPDATED_BY,CREATED_AT,UPDATED_AT",
    },
    "pt-br": {
        "logout": "Sair",
        "login": "Entrar",
        "username": "Usuário",
        "password": "Senha",
        "submit": "Enviar",
        "save": "Salvar",
        "cancel": "Cancelar",
        "delete": "Excluir",
        "create": "Criar",
        "edit": "Editar",
        "search": "Pesquisar",
        "filter": "Filtro",
        "filters": "Filtros",
        "apply": "Aplicar",
        "reset": "Limpar",
        "close": "Fechar",
        "yes": "Sim",
        "no": "Não",
        "back": "Voltar",
        "next": "Próximo",
        "finish": "Finalizar",
        "loading": "Carregando...",
        "no_data": "Nenhum registro encontrado.",
        "confirm_delete": "Tem certeza que deseja excluir este registro?",
        "record_saved": "Registro salvo com sucesso.",
        "record_deleted": "Registro excluído.",
        "error_required": "#LABEL# é obrigatório.",
        "error_invalid": "#LABEL# não é válido.",
        "max_rows_warning": "O número máximo de linhas para este relatório foi atingido.",
        "dashboard": "Painel",
        "home": "Início",
        "reports": "Relatórios",
        "settings": "Configurações",
        "total": "Total",
        "average": "Média",
        "count": "Quantidade",
        "trend": "Tendência",
        "quantity": "Quantidade",
        "cumulative_pct": "Acumulado %",
        "download_formats": "CSV:HTML:XLSX:PDF",
        "system_unavailable": "Sistema temporariamente indisponível.",
        "audit_columns": "CREATED_ON,UPDATED_ON,CREATED_BY,UPDATED_BY,CREATED_AT,UPDATED_AT,DT_CRIACAO,DT_ATUALIZACAO,DS_CRIADO_POR,DS_ATUALIZADO_POR",
    },
    "es": {
        "logout": "Salir",
        "login": "Iniciar sesión",
        "username": "Usuario",
        "password": "Contraseña",
        "submit": "Enviar",
        "save": "Guardar",
        "cancel": "Cancelar",
        "delete": "Eliminar",
        "create": "Crear",
        "edit": "Editar",
        "search": "Buscar",
        "filter": "Filtro",
        "filters": "Filtros",
        "apply": "Aplicar",
        "reset": "Limpiar",
        "close": "Cerrar",
        "yes": "Sí",
        "no": "No",
        "back": "Atrás",
        "next": "Siguiente",
        "finish": "Finalizar",
        "loading": "Cargando...",
        "no_data": "No se encontraron registros.",
        "confirm_delete": "¿Está seguro de que desea eliminar este registro?",
        "record_saved": "Registro guardado exitosamente.",
        "record_deleted": "Registro eliminado.",
        "error_required": "#LABEL# es obligatorio.",
        "error_invalid": "#LABEL# no es válido.",
        "max_rows_warning": "Se alcanzó el número máximo de filas para este informe.",
        "dashboard": "Panel",
        "home": "Inicio",
        "reports": "Informes",
        "settings": "Configuración",
        "total": "Total",
        "average": "Promedio",
        "count": "Cantidad",
        "trend": "Tendencia",
        "quantity": "Cantidad",
        "cumulative_pct": "Acumulado %",
        "download_formats": "CSV:HTML:XLSX:PDF",
        "system_unavailable": "Sistema temporalmente no disponible.",
        "audit_columns": "CREATED_ON,UPDATED_ON,CREATED_BY,UPDATED_BY,CREATED_AT,UPDATED_AT",
    },
}

# ── Active locale ─────────────────────────────────────────────────────────────
_locale: str = os.environ.get("APEX_MCP_LOCALE", "en").lower()


def set_locale(locale: str) -> None:
    """Set the active locale for generated UI labels."""
    global _locale
    _locale = locale.lower()


def get_locale() -> str:
    """Return the current active locale."""
    return _locale


def t(key: str, locale: str | None = None) -> str:
    """Translate a label key to the active (or specified) locale.

    Falls back to English if key not found in active locale.
    """
    loc = (locale or _locale).lower()
    labels = _LABELS.get(loc, _LABELS["en"])
    return labels.get(key, _LABELS["en"].get(key, key))


def audit_columns(locale: str | None = None) -> set[str]:
    """Return the set of audit column names to exclude from forms."""
    raw = t("audit_columns", locale)
    return {c.strip().upper() for c in raw.split(",") if c.strip()}
