"""Import session state tracking."""
from __future__ import annotations
import threading
from dataclasses import dataclass, field
from typing import Optional


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

    _lock: threading.RLock = field(
        default_factory=threading.RLock, init=False, repr=False, compare=False
    )

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
            "page_list": [
                {"page_id": p.page_id, "name": p.page_name, "type": p.page_type}
                for p in self.pages.values()
            ],
        }


# Module-level singleton
session = ImportSession()
