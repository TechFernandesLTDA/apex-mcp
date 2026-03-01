"""Import session state tracking."""
from __future__ import annotations
import logging
import threading
from dataclasses import dataclass, field
from typing import Optional

_log = logging.getLogger("apex_mcp.session")


@dataclass
class PageInfo:
    page_id: int
    page_name: str
    page_type: str  # blank, report, form, login, dashboard


@dataclass
class RegionInfo:
    region_id: int
    page_id: int
    region_name: str
    region_type: str


@dataclass
class ItemInfo:
    item_id: int
    page_id: int
    item_name: str
    item_type: str


@dataclass
class LovInfo:
    lov_id: int
    lov_name: str


@dataclass
class AuthSchemeInfo:
    scheme_id: int
    scheme_name: str


@dataclass
class DynamicActionInfo:
    da_id: int
    page_id: int
    da_name: str
    event: str


@dataclass
class ChartInfo:
    region_id: int
    page_id: int
    region_name: str
    chart_type: str  # bar, line, pie, gauge, funnel, calendar, etc.


@dataclass
class ProcessInfo:
    process_id: int
    page_id: int
    process_name: str
    process_type: str
    exec_point: str


@dataclass
class BranchInfo:
    branch_id: int
    page_id: int
    branch_name: str


@dataclass
class ImportSession:
    """Tracks state of the current APEX app import session."""

    app_id: Optional[int] = None
    app_name: Optional[str] = None
    workspace_id: Optional[int] = None
    import_begun: bool = False
    import_ended: bool = False

    pages: dict[int, PageInfo] = field(default_factory=dict)
    regions: dict[int, RegionInfo] = field(default_factory=dict)
    items: dict[str, ItemInfo] = field(default_factory=dict)  # key: item_name
    lovs: dict[str, LovInfo] = field(default_factory=dict)    # key: lov_name
    auth_schemes: dict[str, AuthSchemeInfo] = field(default_factory=dict)
    nav_items: list[dict] = field(default_factory=list)
    app_items: list[str] = field(default_factory=list)
    app_processes: list[str] = field(default_factory=list)
    buttons: dict[str, int] = field(default_factory=dict)  # key: "{page_id}:{button_name}"
    dynamic_actions: dict[int, DynamicActionInfo] = field(default_factory=dict)  # key: da_id
    charts: dict[int, ChartInfo] = field(default_factory=dict)                   # key: region_id
    processes: dict[int, ProcessInfo] = field(default_factory=dict)              # key: process_id
    branches: dict[int, BranchInfo] = field(default_factory=dict)               # key: branch_id

    _lock: threading.RLock = field(
        default_factory=threading.RLock, init=False, repr=False, compare=False
    )
    # Rollback tracking: list of (component_type, component_id) for rollback
    _created_components: list = field(default_factory=list, init=False, repr=False, compare=False)

    def track_component(self, component_type: str, component_id: int) -> None:
        """Track a created component for potential rollback."""
        with self._lock:
            _log.debug("Tracking component %s id=%s", component_type, component_id)
            self._created_components.append((component_type, component_id))

    def pop_rollback_log(self) -> list:
        """Return and clear the component tracking log."""
        with self._lock:
            log = list(self._created_components)
            self._created_components.clear()
            return log

    def reset(self) -> None:
        with self._lock:
            self.app_id = None
            self.app_name = None
            self.workspace_id = None
            self.import_begun = False
            self.import_ended = False
            self.pages.clear()
            self.regions.clear()
            self.items.clear()
            self.lovs.clear()
            self.auth_schemes.clear()
            self.nav_items.clear()
            self.app_items.clear()
            self.app_processes.clear()
            self.buttons.clear()
            self.dynamic_actions.clear()
            self.charts.clear()
            self.processes.clear()
            self.branches.clear()
            self._created_components.clear()
            _log.info("Session reset (app_id=%s)", self.app_id)

    def summary(self) -> dict:
        return {
            "app_id": self.app_id,
            "app_name": self.app_name,
            "import_begun": self.import_begun,
            "import_ended": self.import_ended,
            "pages": len(self.pages),
            "regions": len(self.regions),
            "items": len(self.items),
            "lovs": len(self.lovs),
            "auth_schemes": len(self.auth_schemes),
            "nav_items": len(self.nav_items),
            "app_items": len(self.app_items),
            "app_processes": len(self.app_processes),
            "dynamic_actions": len(self.dynamic_actions),
            "charts": len(self.charts),
            "processes": len(self.processes),
            "branches": len(self.branches),
            "tracked_components": len(self._created_components),
            "page_list": [
                {"page_id": p.page_id, "name": p.page_name, "type": p.page_type}
                for p in self.pages.values()
            ],
        }


# Module-level singleton
session = ImportSession()

# Public exports — importable via:
#   from apex_mcp.session import session, DynamicActionInfo, ChartInfo, ProcessInfo, BranchInfo
__all__ = [
    "session",
    "ImportSession",
    "PageInfo",
    "RegionInfo",
    "ItemInfo",
    "LovInfo",
    "AuthSchemeInfo",
    "DynamicActionInfo",
    "ChartInfo",
    "ProcessInfo",
    "BranchInfo",
]
