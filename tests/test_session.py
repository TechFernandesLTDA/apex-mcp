"""Tests for apex_mcp.session — ImportSession state tracking.

Run: pytest tests/test_session.py -v
"""
from __future__ import annotations

import logging


class TestImportSessionReset:
    def test_reset_clears_all_state(self):
        from apex_mcp.session import ImportSession, PageInfo

        s = ImportSession()
        s.app_id = 200
        s.app_name = "Test"
        s.import_begun = True
        s.pages[1] = PageInfo(page_id=1, page_name="Home", page_type="blank")
        s.reset()

        assert s.app_id is None
        assert s.app_name is None
        assert s.import_begun is False
        assert len(s.pages) == 0

    def test_reset_logs_old_app_id(self, caplog):
        from apex_mcp.session import ImportSession

        s = ImportSession()
        s.app_id = 42

        with caplog.at_level(logging.INFO, logger="apex_mcp.session"):
            s.reset()

        assert any("42" in r.message for r in caplog.records)


class TestImportSessionSummary:
    def test_summary_structure(self):
        from apex_mcp.session import ImportSession

        s = ImportSession()
        summary = s.summary()
        assert "app_id" in summary
        assert "pages" in summary
        assert "regions" in summary
        assert "items" in summary
        assert "page_list" in summary

    def test_summary_counts_components(self):
        from apex_mcp.session import ImportSession, PageInfo, RegionInfo

        s = ImportSession()
        s.pages[1] = PageInfo(page_id=1, page_name="Home", page_type="blank")
        s.pages[2] = PageInfo(page_id=2, page_name="List", page_type="report")
        s.regions[100] = RegionInfo(region_id=100, page_id=1, region_name="R1", region_type="ir")

        summary = s.summary()
        assert summary["pages"] == 2
        assert summary["regions"] == 1
        assert len(summary["page_list"]) == 2


class TestImportSessionTrackComponent:
    def test_track_component_adds_to_list(self):
        from apex_mcp.session import ImportSession

        s = ImportSession()
        s.track_component("region", 100)
        s.track_component("item", 200)
        assert len(s._created_components) == 2

    def test_pop_rollback_log_returns_and_clears(self):
        from apex_mcp.session import ImportSession

        s = ImportSession()
        s.track_component("region", 100)
        s.track_component("item", 200)

        log = s.pop_rollback_log()
        assert len(log) == 2
        assert ("region", 100) in log
        assert len(s._created_components) == 0

    def test_pop_rollback_log_when_empty(self):
        from apex_mcp.session import ImportSession

        s = ImportSession()
        log = s.pop_rollback_log()
        assert log == []


class TestModuleSingleton:
    def test_singleton_is_importable(self):
        from apex_mcp.session import session

        assert session is not None
        assert hasattr(session, "app_id")


class TestDataclasses:
    def test_page_info_fields(self):
        from apex_mcp.session import PageInfo

        p = PageInfo(page_id=1, page_name="Home", page_type="blank")
        assert p.page_id == 1
        assert p.page_name == "Home"
        assert p.page_type == "blank"

    def test_region_info_fields(self):
        from apex_mcp.session import RegionInfo

        r = RegionInfo(region_id=100, page_id=1, region_name="R1", region_type="ir")
        assert r.region_id == 100

    def test_item_info_fields(self):
        from apex_mcp.session import ItemInfo

        i = ItemInfo(item_id=200, page_id=1, item_name="P1_NAME", item_type="text")
        assert i.item_name == "P1_NAME"

    def test_lov_info_fields(self):
        from apex_mcp.session import LovInfo

        lov = LovInfo(lov_id=300, lov_name="DEPARTMENTS")
        assert lov.lov_name == "DEPARTMENTS"

    def test_chart_info_fields(self):
        from apex_mcp.session import ChartInfo

        c = ChartInfo(region_id=400, page_id=1, region_name="C1", chart_type="bar")
        assert c.chart_type == "bar"

    def test_process_info_fields(self):
        from apex_mcp.session import ProcessInfo

        p = ProcessInfo(process_id=500, page_id=1, process_name="Save",
                       process_type="DML", exec_point="AFTER_SUBMIT")
        assert p.exec_point == "AFTER_SUBMIT"

    def test_branch_info_fields(self):
        from apex_mcp.session import BranchInfo

        b = BranchInfo(branch_id=600, page_id=1, branch_name="Go Home")
        assert b.branch_name == "Go Home"

    def test_dynamic_action_info_fields(self):
        from apex_mcp.session import DynamicActionInfo

        da = DynamicActionInfo(da_id=700, page_id=1, da_name="OnClick", event="click")
        assert da.event == "click"

    def test_auth_scheme_info_fields(self):
        from apex_mcp.session import AuthSchemeInfo

        a = AuthSchemeInfo(scheme_id=800, scheme_name="IS_ADMIN")
        assert a.scheme_name == "IS_ADMIN"
