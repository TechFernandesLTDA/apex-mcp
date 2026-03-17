"""Tests for apex_mcp.exceptions — custom exception classes.

Run: pytest tests/test_exceptions.py -v
"""
from __future__ import annotations

import pytest


class TestApexMCPError:
    def test_is_exception_subclass(self):
        from apex_mcp.exceptions import ApexMCPError

        assert issubclass(ApexMCPError, Exception)

    def test_can_be_raised_and_caught(self):
        from apex_mcp.exceptions import ApexMCPError

        with pytest.raises(ApexMCPError):
            raise ApexMCPError("test error")


class TestNotConnectedError:
    def test_default_message(self):
        from apex_mcp.exceptions import NotConnectedError

        err = NotConnectedError()
        assert "connect" in str(err).lower()

    def test_custom_message(self):
        from apex_mcp.exceptions import NotConnectedError

        err = NotConnectedError("Custom msg")
        assert str(err) == "Custom msg"

    def test_inherits_from_base(self):
        from apex_mcp.exceptions import ApexMCPError, NotConnectedError

        assert issubclass(NotConnectedError, ApexMCPError)


class TestNoSessionError:
    def test_default_message(self):
        from apex_mcp.exceptions import NoSessionError

        err = NoSessionError()
        assert "session" in str(err).lower()

    def test_inherits_from_base(self):
        from apex_mcp.exceptions import ApexMCPError, NoSessionError

        assert issubclass(NoSessionError, ApexMCPError)


class TestPageNotFoundError:
    def test_message_contains_page_id(self):
        from apex_mcp.exceptions import PageNotFoundError

        err = PageNotFoundError(42)
        assert "42" in str(err)
        assert err.page_id == 42

    def test_inherits_from_base(self):
        from apex_mcp.exceptions import ApexMCPError, PageNotFoundError

        assert issubclass(PageNotFoundError, ApexMCPError)


class TestRegionNotFoundError:
    def test_message_contains_region_and_page(self):
        from apex_mcp.exceptions import RegionNotFoundError

        err = RegionNotFoundError(10, "My Region")
        assert "My Region" in str(err)
        assert "10" in str(err)
        assert err.page_id == 10
        assert err.region_name == "My Region"

    def test_inherits_from_base(self):
        from apex_mcp.exceptions import ApexMCPError, RegionNotFoundError

        assert issubclass(RegionNotFoundError, ApexMCPError)
