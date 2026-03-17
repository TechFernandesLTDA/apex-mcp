"""Custom exception classes for apex-mcp.

Using domain-specific exceptions instead of bare ``Exception`` makes error
handling more precise and allows callers to distinguish between connection
issues, session state problems, and validation errors.
"""
from __future__ import annotations


class ApexMCPError(Exception):
    """Base exception for all apex-mcp errors."""


class NotConnectedError(ApexMCPError):
    """Raised when a tool requires an active database connection."""

    def __init__(self, msg: str = "Not connected. Call apex_connect() first.") -> None:
        super().__init__(msg)


class NoSessionError(ApexMCPError):
    """Raised when a tool requires an active import session."""

    def __init__(self, msg: str = "No import session active. Call apex_create_app() first.") -> None:
        super().__init__(msg)


class PageNotFoundError(ApexMCPError):
    """Raised when a referenced page does not exist in the current session."""

    def __init__(self, page_id: int) -> None:
        super().__init__(f"Page {page_id} not found in current session. Call apex_add_page() first.")
        self.page_id = page_id


class RegionNotFoundError(ApexMCPError):
    """Raised when a referenced region does not exist on a page."""

    def __init__(self, page_id: int, region_name: str) -> None:
        super().__init__(
            f"Region '{region_name}' not found on page {page_id}. "
            "Create it first with apex_add_region()."
        )
        self.page_id = page_id
        self.region_name = region_name
